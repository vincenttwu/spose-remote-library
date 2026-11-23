"""Blender geometry diagnostics only. No result blocks building or batch progression.
Proxies are not collision depth, physical stability, or human approval.
"""
import math
from mathutils import Vector


def measure_contact(bpy,config):
    from mathutils.kdtree import KDTree
    def coords(actor,max_verts=6000):
        obj=bpy.data.objects[f'CPL01_{actor}_BODY']
        ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
        try:
            step=max(1,len(mesh.vertices)//max_verts)
            return [ev.matrix_world @ mesh.vertices[i].co for i in range(0,len(mesh.vertices),step)]
        finally:ev.to_mesh_clear()
    a=coords('A');b=coords('B')
    out={'method':'sampled_evaluated_mesh_distance_and_bone_head_proxy',
         'warning':'Unsigned proximity does not establish penetration depth or correct contact.'}
    if a and b:
        tree=KDTree(len(b))
        for i,p in enumerate(b):tree.insert(p,i)
        tree.balance();distances=sorted(tree.find(p)[2] for p in a)
        out['mesh_sample']={'min_distance_m':round(distances[0],6),
                            'p01_distance_m':round(distances[int(.01*(len(distances)-1))],6),
                            'samples_under_1cm':sum(d<=.01 for d in distances)}
    anchors=[]
    for anchor in config.get('anchors',[]):
        try:
            lhs=bpy.data.objects[f'CPL01_{anchor["actor"]}_RIG']
            rhs=bpy.data.objects[f'CPL01_{anchor["target_actor"]}_RIG']
            pa=lhs.matrix_world @ lhs.pose.bones[anchor['bone']].head
            pb=rhs.matrix_world @ rhs.pose.bones[anchor['target_bone']].head
            d=(pa-pb).length;tol=float(anchor.get('tolerance_m',.05))
            anchors.append({'id':anchor.get('id'), 'distance_m':round(d,5),'tolerance_m':tol,'proxy_in_tolerance':d<=tol})
        except Exception as exc:anchors.append({'id':anchor.get('id'),'error':str(exc)})
    out['anchors']=anchors
    return out


def validate_geometry(engine,contract,calibration,contacts_result):
    issues=[];diagnostics={'supports':{},'postures':{},'body_min_z_m':{},'limits':{},'contact_proxies':contacts_result.get('anchors',[])}
    for item in contract['support_assertions']:
        actor=item['actor'];region=item['region'];side=item.get('side')
        key=f'{actor}/{region}/{side or "both"}'
        try:
            z=engine.min_z(actor,region,side)
            tol=float(item.get('tolerance_m',.025));target=float(item.get('target_z_m',.004))
            ok=abs(z-target)<=tol
            diagnostics['supports'][key]={'measured_z_m':round(z,5),'target_z_m':target,'tolerance_m':tol,'pass':ok}
            if not ok:issues.append({'code':'GROUND_SUPPORT_NOT_MET','detail':f'{key}: z={z:.4f} m (expected {target:.4f} ± {tol:.4f})'})
        except Exception as exc:
            issues.append({'code':'GROUND_SUPPORT_MEASURE_FAILED','detail':f'{key}: {exc}'})
    for actor in ('A','B'):
        pts=[]
        try:
            obj=engine.bodies[actor]
            ev=obj.evaluated_get(engine.bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
            try:
                step=max(1,len(mesh.vertices)//12000)
                pts=[(ev.matrix_world @ mesh.vertices[i].co).z for i in range(0,len(mesh.vertices),step)]
            finally:ev.to_mesh_clear()
            z=min(pts)
            diagnostics['body_min_z_m'][actor]=round(z,5)
            if z<-.022:issues.append({'code':'BELOW_FLOOR_PENETRATION','detail':f'{actor} sampled mesh below floor by {-z:.3f} m'})
        except Exception as exc:issues.append({'code':'MESH_GROUND_AUDIT_FAILED','detail':f'{actor}: {exc}'})
    for item in contract['posture_assertions']:
        actor=item['actor'];kind=item['kind'];results={'kind':kind,'legs':{}}
        hip_z=engine.head(actor,'hips').z
        head_z=engine.head(actor,'head').z
        results['hip_z_m']=round(hip_z,5)
        results['head_z_m']=round(head_z,5)
        # Optional silhouette-height guards are pose-specific: a lowered face-down
        # base MUST NOT inherit the tabletop limits used by DOGG-DOGG-V00.
        for field, actual, code, compare in (
            ('min_hip_z_m',hip_z,'PELVIS_TOO_LOW',lambda a,b:a<b),
            ('max_hip_z_m',hip_z,'PELVIS_TOO_HIGH',lambda a,b:a>b),
            ('min_head_z_m',head_z,'HEAD_TOO_LOW',lambda a,b:a<b),
        ):
            if field in item and compare(actual,float(item[field])):
                issues.append({'code':code,'detail':f'{actor}: {field}={float(item[field]):.3f}m, actual={actual:.3f}m'})
        if item.get('max_shoulder_to_hand_xy_m') is not None:
            threshold=float(item['max_shoulder_to_hand_xy_m'])
            results['shoulder_to_hand_xy_m']={}
            for side in ('L','R'):
                shoulder=engine.head(actor,'DEF-upper_arm.'+side)
                hand=engine.head(actor,'hand_ik.'+side)
                distance=math.hypot(shoulder.x-hand.x,shoulder.y-hand.y)
                results['shoulder_to_hand_xy_m'][side]=round(distance,5)
                if distance>threshold:
                    issues.append({'code':'PALM_TOO_FAR_FROM_SHOULDER',
                        'detail':f'{actor}/{side}: horizontal shoulder-to-palm distance {distance:.3f}m exceeds {threshold:.3f}m'})
        for side in ('L','R'):
            knee_z=engine.head(actor,'DEF-shin.'+side).z
            angle=engine.knee_angle_deg(actor,side)
            results['legs'][side]={'knee_z_m':round(knee_z,4),'angle_deg':round(angle,2) if angle else None}
            if kind in ('kneeling','quadruped','low_forearm_fold'):
                if knee_z>float(item.get('max_knee_joint_z_m',.23)):
                    issues.append({'code':'STANDING_INSTEAD_OF_KNEELING',
                                   'detail':f'{actor}/{side} knee joint z {knee_z:.3f}m while posture={kind}'})
                if angle is None or angle>float(item.get('max_knee_angle_deg',145)):
                    issues.append({'code':'KNEE_NOT_FLEXED','detail':f'{actor}/{side}: angle {angle}; expected flexed {kind}'})
                if 'min_knee_angle_deg' in item and (angle is None or angle<float(item['min_knee_angle_deg'])):
                    issues.append({'code':'KNEE_OVER_FOLDED','detail':f'{actor}/{side}: angle {angle}; required >= {item["min_knee_angle_deg"]} degrees'})
            if kind in ('standing','forward_fold_standing'):
                if knee_z<float(item.get('min_knee_joint_z_m',.18)):
                    issues.append({'code':'KNEE_HEIGHT_WRONG_FOR_STANDING','detail':f'{actor}/{side} knee joint z {knee_z:.3f}m'})
        if kind=='forward_fold_standing' and head_z>hip_z-float(item.get('min_head_drop_below_hip_m',.06)):
            issues.append({'code':'FORWARD_FOLD_NOT_ESTABLISHED','detail':f'{actor}: head {head_z:.3f}m hip {hip_z:.3f}m'})
        diagnostics['postures'][actor]=results
    # Optional cross-actor height continuity; surface proximity alone cannot
    # establish a coherent rear/front body alignment.
    relative=contract.get('relative_height_guard')
    if relative:
        a,b=relative['actors']
        delta=abs(engine.head(a,'hips').z-engine.head(b,'hips').z)
        limit=float(relative['max_hip_delta_m'])
        diagnostics['limits']['hip_delta_m']=round(delta,5)
        if delta>limit:
            issues.append({'code':'HIP_HEIGHT_MISMATCH','detail':f'{a}/{b} hip vertical delta {delta:.3f}m > {limit:.3f}m'})
    for anchor in contacts_result.get('anchors',[]):
        if 'error' in anchor:
            issues.append({'code':'CONTACT_ANCHOR_MISSING','detail':str(anchor['error'])})
        elif not anchor.get('proxy_in_tolerance'):
            issues.append({'code':'CONTACT_ANCHOR_TOO_FAR','detail':str(anchor.get('id'))+' exceeds diagnostic tolerance; inspect render'})
    diagnostics['calibration']=calibration
    return {'hard_gate_pass':not issues, 'geometry_reference_pass':not issues, 'issues':issues,'diagnostics':diagnostics}
