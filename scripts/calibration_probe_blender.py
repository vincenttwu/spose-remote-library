"""Blender-only, READ-ONLY SPOSE calibration measurement.

Run through collect_calibration.py, never by importing this into ordinary Python.
Loads local scenes into memory but never saves a .blend, edits source assets or
writes to tracking. Outputs bounded JSON geometry and rig-response observations.
"""
from __future__ import annotations
import argparse, datetime, hashlib, json, math, sys, traceback
from pathlib import Path
import bpy
from mathutils import Quaternion, Vector

sys.path.insert(0,str(Path(__file__).resolve().parent))
from rigify_floor_engine import RigifyFloorEngine


def digest(file):
    h=hashlib.sha256()
    with Path(file).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def xyz(v):return [round(float(x),6) for x in v]


def bounds(points):
    if not points:return {'count':0}
    lo=[min(p[i] for p in points) for i in range(3)]
    hi=[max(p[i] for p in points) for i in range(3)]
    center=[sum(p[i] for p in points)/len(points) for i in range(3)]
    return {'count':len(points),'min':xyz(lo),'max':xyz(hi),'centroid':xyz(center),
            'diagonal_m':round(math.sqrt(sum((hi[i]-lo[i])**2 for i in range(3))),6)}


def safe_prop(value):
    if type(value) in (float,int,str,bool) or value is None:return value
    if hasattr(value,'to_list'):return [safe_prop(x) for x in value.to_list()]
    if isinstance(value,(tuple,list)):return [safe_prop(x) for x in value]
    return str(value)[:120]


def control_inventory(engine):
    result={}
    for a in ('A','B'):
        rig=engine.rigs[a]
        bones=[]
        for pb in rig.pose.bones:
            try:
                item={'name':pb.name, 'parent':pb.parent.name if pb.parent else None,
                      'rest_head_m':xyz(rig.matrix_world @ pb.bone.head_local),
                      'rest_tail_m':xyz(rig.matrix_world @ pb.bone.tail_local),
                      'world_head_m':xyz(rig.matrix_world @ pb.head),
                      'world_tail_m':xyz(rig.matrix_world @ pb.tail),
                      'length_m':round(float(pb.bone.length),6),
                      'rotation_mode':pb.rotation_mode,
                      'constraints':[{'name':c.name,'type':c.type,'mute':bool(c.mute)} for c in pb.constraints],
                      'custom_properties':{str(k):safe_prop(pb[k]) for k in pb.keys() if not str(k).startswith('_')},
                      'lock_location':list(pb.lock_location),
                      'lock_rotation':list(pb.lock_rotation),
                      'lock_scale':list(pb.lock_scale)}
                bones.append(item)
            except Exception as ex:
                bones.append({'name':pb.name,'error':f'{type(ex).__name__}: {ex}'})
        result[a]={'rig_name':rig.name,'pose_bone_count':len(bones),'bones':bones}
    return result


def region_inventory(engine):
    result={}
    for a in ('A','B'):
        obj=engine.bodies[a]
        ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh=ev.to_mesh()
        regions={}
        try:
            role_ids={}
            for poly in mesh.polygons:
                mat=obj.material_slots[poly.material_index].material if poly.material_index<len(obj.material_slots) else None
                role=mat.get('region','unknown') if mat else 'unassigned'
                role_ids.setdefault(str(role),set()).update(poly.vertices)
            for region,indices in sorted(role_ids.items()):
                coords=[ev.matrix_world @ mesh.vertices[i].co for i in indices]
                regions[region]=bounds(coords)
                # Bounded deterministic anatomical anchor samples: never export the full mesh.
                sample=sorted(indices)
                step=max(1,len(sample)//40)
                regions[region]['sample_world_points_m']=[xyz(ev.matrix_world @ mesh.vertices[i].co) for i in sample[::step][:40]]
            result[a]={'body_name':obj.name,'evaluated_vertex_count':len(mesh.vertices),
                       'evaluated_polygon_count':len(mesh.polygons),'regions':regions}
        finally:
            ev.to_mesh_clear()
    return result


def probe_control_response(engine):
    """Finite differences on neutral scene; always restore exact initial transforms."""
    output=[]
    for a in ('A','B'):
        for name in ('torso','hand_ik.L','hand_ik.R','foot_ik.L','foot_ik.R','head','neck','chest'):
            try:
                bone=engine.bone(a,name)
                base_matrix=bone.matrix.copy()
                base_quat=bone.rotation_quaternion.copy()
                base_mode=bone.rotation_mode
                def measure():
                    result={'head_gaze':engine.head_gaze(a)}
                    for label,bone_name in (('hip','hips'),('head','head'),('hand_L','DEF-hand.L'),('hand_R','DEF-hand.R')):
                        try:result[label+'_head_world_m']=xyz(engine.head(a,bone_name))
                        except Exception:pass
                    return result
                baseline=measure()
                tests=[]
                if name in ('head','neck','chest'):
                    bone.rotation_mode='QUATERNION'
                    source=bone.rotation_quaternion.copy()
                    axis=bone.bone.matrix_local.to_3x3().inverted() @ Vector((1,0,0))
                    for angle in (-15.,15.):
                        bone.rotation_quaternion=Quaternion(axis, math.radians(angle)) @ source
                        engine.update()
                        tests.append({'perturbation':{'local_x_deg':angle},'measurement':measure()})
                        bone.rotation_quaternion=source
                        engine.update()
                else:
                    for axis_name,vec in (('x',(.025,0.,0.)),('y',(0.,.025,0.)),('z',(0.,0.,.025))):
                        engine.point(a,name,engine.head(a,name)+Vector(vec))
                        tests.append({'perturbation':{'world_translation_m':vec,'axis':axis_name},'measurement':measure()})
                        bone.matrix=base_matrix
                        engine.update()
                output.append({'actor':a,'control':name,'baseline':baseline,'tests':tests})
            except Exception as ex:
                output.append({'actor':a,'control':name,'error':f'{type(ex).__name__}: {ex}'})
            finally:
                try:
                    bone.matrix=base_matrix
                    bone.rotation_mode=base_mode
                    if base_mode=='QUATERNION':bone.rotation_quaternion=base_quat
                    engine.update()
                except Exception:pass
    return output


def scene_metrics(engine):
    from mathutils.kdtree import KDTree
    out={'posture_heights':engine.heights(),
         'head_gaze':{a:engine.head_gaze(a) for a in ('A','B')},
         'support_surface_min_z_m':{},'hand_pelvis_patches':{},
         'head_side_floor_clearance':{s:engine.side_head_clearance('B',s) for s in ('L','R')}}
    for a in ('A','B'):
        out['support_surface_min_z_m'][a]={}
        for region in ('hands','feet','knees','forearms','head_side'):
            for side in ('L','R'):
                try:out['support_surface_min_z_m'][a][f'{region}.{side}']=round(engine.min_z(a,region,side),6)
                except Exception as ex:out['support_surface_min_z_m'][a][f'{region}.{side}']={'error':str(ex)}
    for side in ('L','R'):
        try:
            hp=engine._hip_contact_patch('B',side)
            palm,radius,method=engine._hand_contact_patch('A',side)
            tree=KDTree(len(hp))
            for i,p in enumerate(hp):tree.insert(p,i)
            tree.balance()
            stats=engine._percentiles([tree.find(p)[2] for p in palm])
            out['hand_pelvis_patches'][side]={'distance_distribution':stats,'hand_patch_localization_m':radius,
                                           'localization_method':method,'palm_vertices':len(palm),'hip_vertices':len(hp),
                                           'note':'Unsigned nearest-neighbor distances, not grip or penetration.'}
        except Exception as ex:out['hand_pelvis_patches'][side]={'error':f'{type(ex).__name__}: {ex}'}
    out['hip_delta_m']=round(abs(engine.head('A','hips').z-engine.head('B','hips').z),6)
    return out


def main():
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    pa=argparse.ArgumentParser()
    pa.add_argument('--mode', choices=['neutral','scene'],required=True)
    pa.add_argument('--scene',type=Path,required=True)
    pa.add_argument('--output',type=Path,required=True)
    pa.add_argument('--pose-id')
    pa.add_argument('--rig-map',type=Path)
    args=pa.parse_args(argv)
    # Isolate all destructive pose-control experimentation in a throwaway
    # Blender process. No save_mainfile, no changing the disk .blend.
    bpy.ops.wm.open_mainfile(filepath=str(args.scene),use_scripts=False)
    engine=RigifyFloorEngine(bpy)
    if args.mode=='neutral':engine.initialize()
    output={'schema_version':1,'kind':'spose_rig_calibration_probe','mode':args.mode,
            'pose_id':args.pose_id,'scene_source_sha256':digest(args.scene),
            'scene_basename':args.scene.name,
            'blender_version':bpy.app.version_string,
            'generated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'coordinate_convention':{'up':'+Z','rig_forward_reference':'-Y','units':'m'},
            'read_only':True,'measurement_confidence':'approximate_world_geometry_and_rig_proxies'}
    if args.rig_map and args.rig_map.is_file():output['rig_map_sha256']=digest(args.rig_map)
    if args.mode=='neutral':
        output['controls']=control_inventory(engine)
        output['body_regions']=region_inventory(engine)
        output['response_probes']=probe_control_response(engine)
    else:
        output['geometry']=scene_metrics(engine)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(output,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('SPOSE_CALIBRATION_COMPLETE '+str(args.output))


if __name__=='__main__':
    try:main()
    except Exception:
        traceback.print_exc()
        sys.exit(2)
