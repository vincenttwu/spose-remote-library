"""Reopen a pilot and verify source provenance, geometry preservation, and support proxies."""
import bpy,sys,json,hashlib,csv
import numpy as np
from pathlib import Path
from collections import Counter
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from character_common import ROOT,write_json
pose_id=sys.argv[sys.argv.index('--')+1]
out=ROOT/'poses'/pose_id/'CPL01/v001/r001'
record=json.loads((out/'pose.json').read_text(encoding='utf-8'))

def signature(body):
    h=hashlib.sha256()
    for key in body.data.shape_keys.key_blocks:
        coords=np.empty(len(key.data)*3,dtype=np.float32);key.data.foreach_get('co',coords)
        h.update(key.name.encode('utf-8'));h.update(coords.tobytes())
    loops=np.empty(len(body.data.loops),dtype=np.int32);body.data.loops.foreach_get('vertex_index',loops)
    h.update(loops.tobytes())
    return h.hexdigest()

def region_geometry(actor):
    obj=bpy.data.objects[f'CPL01_{actor}_BODY']
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
    try:
        verts=[ev.matrix_world @ vertex.co for vertex in mesh.vertices]
        faces=[tuple(poly.vertices) for poly in mesh.polygons]
        roles=[obj.data.materials[poly.material_index]['region'] for poly in mesh.polygons]
        regions={}
        for face,role in zip(faces,roles):
            for index in face:
                point=verts[index];side='L' if point.x>0 else 'R';name=role+'.'+side
                if name not in regions:regions[name]={'min_z':point.z,'max_z':point.z}
                else:
                    regions[name]['min_z']=min(regions[name]['min_z'],point.z)
                    regions[name]['max_z']=max(regions[name]['max_z'],point.z)
        return verts,faces,roles,regions
    finally:ev.to_mesh_clear()

template=ROOT/record['template_path']
assert hashlib.sha256(template.read_bytes()).hexdigest()==record['template_sha256']
bpy.ops.wm.open_mainfile(filepath=str(template),use_scripts=False)
source_signatures={actor:signature(bpy.data.objects[f'CPL01_{actor}_BODY']) for actor in ['A','B']}
root_scales={actor:tuple(bpy.data.objects[f'CPL01_{actor}_ROOT'].scale) for actor in ['A','B']}
def rest_signature(rig):
    return hashlib.sha256(json.dumps([(b.name,b.parent.name if b.parent else None,[list(row) for row in b.matrix_local]) for b in rig.data.bones],separators=(',',':')).encode()).hexdigest()
rest_signatures={actor:rest_signature(bpy.data.objects[f'CPL01_{actor}_RIG']) for actor in ['A','B']}
baseline_length_ratios={actor:{name:(bpy.data.objects[f'CPL01_{actor}_RIG'].pose.bones[name].tail-bpy.data.objects[f'CPL01_{actor}_RIG'].pose.bones[name].head).length/bpy.data.objects[f'CPL01_{actor}_RIG'].data.bones[name].length for name in ['ORG-upper_arm.L','ORG-forearm.L','ORG-thigh.L','ORG-shin.L']} for actor in ['A','B']}
print('BASELINE_LENGTH_RATIOS',json.dumps(baseline_length_ratios))
bpy.ops.wm.open_mainfile(filepath=str(out/'scene.blend'),use_scripts=False)
assert not list(bpy.data.libraries)
ui=bpy.data.texts.get('rig.004_ui.py')
if ui:exec(compile(ui.as_string(),ui.name,'exec'),{'__name__':'__rigify_ui__'})
geometry={};ratios={};region_bounds={}
for actor in ['A','B']:
    body=bpy.data.objects[f'CPL01_{actor}_BODY'];rig=bpy.data.objects[f'CPL01_{actor}_RIG']
    assert signature(body)==source_signatures[actor]
    assert tuple(bpy.data.objects[f'CPL01_{actor}_ROOT'].scale)==root_scales[actor]
    assert len(rig.pose.bones)==406
    assert rest_signature(rig)==rest_signatures[actor]
    assert len(body.data.materials)==11
    for mat in body.data.materials:
        assert mat['actor']==actor
        assert abs(mat.node_tree.nodes['Region_Overlay'].inputs[0].default_value-1)<1e-5
        for driver in mat.node_tree.animation_data.drivers:
            assert driver.is_valid
            assert driver.driver.variables[0].targets[0].id.name==f'CPL01_{actor}_SHAPES'
    for side in ['L','R']:
        assert rig.pose.bones['upper_arm_parent.'+side]['IK_Stretch']==0
        assert rig.pose.bones['thigh_parent.'+side]['IK_Stretch']==0
    ratios[actor]={}
    for bone_name in ['ORG-upper_arm.L','ORG-forearm.L','ORG-thigh.L','ORG-shin.L',
                      'ORG-upper_arm.R','ORG-forearm.R','ORG-thigh.R','ORG-shin.R']:
        bone=rig.pose.bones[bone_name]
        ratio=(bone.tail-bone.head).length/bone.bone.length
        ratios[actor][bone_name]=ratio
        print('POSE_LENGTH_RATIO',actor,bone_name,ratio)
        assert abs(ratio-1.)<.001,(actor,bone_name,ratio)
    geometry[actor]=region_geometry(actor)
    region_bounds[actor]=geometry[actor][3]

support_checks={}
for actor,roles in [('A',['feet']),('B',['hands','calves'])]:
    for role in roles:
        for side in ['L','R']:
            z=region_bounds[actor][role+'.'+side]['min_z']
            support_checks[f'{actor}_{role}_{side}']={'min_surface_z_m':z,'tolerance_m':.005,'passed':abs(z)<=.005}
assert all(value['passed'] for value in support_checks.values()),support_checks
all_min=min(v.z for g in geometry.values() for v in g[0]);assert all_min>-.002
verts_a,faces_a,roles_a,_=geometry['A'];verts_b,faces_b,roles_b,_=geometry['B']
tree_a=BVHTree.FromPolygons(verts_a,faces_a,all_triangles=False)
tree_b=BVHTree.FromPolygons(verts_b,faces_b,all_triangles=False)
overlaps=tree_a.overlap(tree_b)
overlap_regions=Counter(roles_a[i]+' / '+roles_b[j] for i,j in overlaps)
source_cfg=json.loads((ROOT/'source/dataset.json').read_text(encoding='utf-8'))
catalog=ROOT/'source'/source_cfg['canonical_catalog']
assert hashlib.sha256(catalog.read_bytes()).hexdigest()==record['source_catalog_sha256']
with catalog.open(encoding='utf-8-sig',newline='') as f:row=next(row for row in csv.DictReader(f) if row['pose_id']==pose_id)
assert (out/'specification.txt').read_text(encoding='utf-8')==row['specification']
for name in ['front','side','three-quarter']:assert (out/'previews'/f'{name}.png').is_file()
report={'schema_version':1,'pose_id':pose_id,'pair_id':'CPL01','pair_version':'v001','revision':1,
    'result':'draft_technical_checks_passed_contact_review_pending','scene_sha256':hashlib.sha256((out/'scene.blend').read_bytes()).hexdigest(),
    'blender_version':bpy.app.version_string,'checks':{'blend_reopens':'passed','expected_rigs_present':'passed',
        'character_proportions_preserved':'passed','external_dependencies_resolved':'passed','previews_rendered':'passed',
        'visual_review':'agent_checked_draft_user_review_pending','output_checksums_recorded':'pending',
        'actor_palette_identity':'passed','appearance_does_not_change_geometry':'passed',
        'appearance_controls_independent':'material_targets_checked','region_qa_preview':'pending','appearance_metadata':'pending'},
    'support_region_checks':support_checks,'limb_length_ratios':ratios,'template_limb_length_ratios':baseline_length_ratios,
    'source_signature_matches':True,'source_catalog_hash_matches':True,
    'cross_actor_surface_overlap_candidates':dict(overlap_regions),
    'contact_validation':'review_required; BVH overlaps are surface candidates, not a penetration-depth or physics test',
    'region_bounds':region_bounds,
    'limitations':['Calf-region minimum surface height is a knee/shin floor-contact proxy, not a measured full contact patch.',
        'Upper-arm/rib contact fit and interpenetration need visual review.','No balance, load, physical safety, or dynamic simulation validation is asserted.'],
    'validated_at':None}
write_json(out/'validation.json',report)
print('PILOT_BASIC_CHECKS_PASSED',json.dumps({'supports':support_checks,'overlap_candidates':dict(overlap_regions)}))
