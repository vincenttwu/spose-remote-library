"""Build review drafts only. Run inside a separate background Blender process.

Usage: blender --background --factory-startup --disable-autoexec --python this.py
Rebuilding an unapproved draft requires -- --replace-draft. Approved assets are refused.
"""
import bpy
import sys
import math
import json
import hashlib
from pathlib import Path
from mathutils import Vector, Quaternion
sys.path.insert(0,str(Path(__file__).resolve().parent))
from character_common import ROOT, bounds, evaluated_points, material, setup_stage, render, hide_helpers, write_json

PROFILE_DIR=ROOT/'body_profiles/BP001/v001'
PAIR_DIR=ROOT/'pairs/CPL01/v001'
profile=json.loads((PROFILE_DIR/'profile.json').read_text(encoding='utf-8'))
pair=json.loads((PAIR_DIR/'pair.json').read_text(encoding='utf-8'))
assert not profile['approved_at'] and not pair['approved_at'], 'Approved assets are immutable'
replace='--replace-draft' in sys.argv
for f in [PROFILE_DIR/'master.blend',PAIR_DIR/'template.blend']:
    assert replace or not f.exists(), 'Draft exists; use --replace-draft deliberately'
source=Path(profile['source_rig'])
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
assert hashlib.sha256(Path(profile['reference']['path']).read_bytes()).hexdigest()==profile['reference']['sha256']
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
bpy.context.scene.frame_set(1)
bpy.context.preferences.filepaths.save_version=0
body=bpy.data.objects['Adjustable Mannequin Rigify']
rig=bpy.data.objects['Rigify Rig']
menu=bpy.data.objects['Adjustable Mannequin Menu']
hide_helpers()
body.modifiers['Solidify'].show_render=False
sliders={'neck control':.055,'arms control':.115,'torso control':.055,
         'legs control':.040,'hips control':-.005,'head style':.285,
         'breasts control':0.,'breasts angle':0.,'belly control':0.,
         'muscle group control':0.,'guide lines control':0.}
for name,value in sliders.items():menu.pose.bones[name].location.x=value
menu.update_tag()

# A small additive torso-shape key preserves the original editable keys and rig rest bones.
basis=body.data.shape_keys.key_blocks['Basis']
taper=body.shape_key_add(name='BP001_TorsoTaper',from_mix=False)
knots=[(.90,1.0),(.99,.91),(1.08,.97),(1.20,1.10),(1.33,1.10)]
torso_groups={g.index for g in body.vertex_groups if g.name.startswith('DEF-spine')}
for index,v in enumerate(basis.data):
    co=v.co
    torso_weight=sum(g.weight for g in body.data.vertices[index].groups if g.group in torso_groups)
    if .90 < co.z < 1.33 and torso_weight>.8:
        for (za,fa),(zb,fb) in zip(knots,knots[1:]):
            if za<=co.z<=zb:
                f=fa+(fb-fa)*(co.z-za)/(zb-za)
                taper.data[index].co.x=co.x*f
                break
taper.value=1.0

neutral={}
for side,sign in [('L',1),('R',-1)]:
    shoulder=rig.pose.bones['shoulder.'+side]
    shoulder.location=shoulder.bone.matrix_local.to_3x3().inverted() @ Vector((.025*sign,0,0))
    rig.pose.bones['upper_arm_parent.'+side]['IK_FK']=1.0
    # A reproducible relaxed A stance, 20 degrees out from vertical.
    arm=rig.pose.bones['upper_arm_fk.'+side]
    axis=arm.bone.matrix_local.to_3x3().inverted() @ Vector((0,1,0))
    arm.rotation_quaternion=Quaternion(axis,math.radians(70)*sign)
    for name in ['shoulder.'+side,'upper_arm_fk.'+side]:
        b=rig.pose.bones[name]
        neutral[name]={'location':list(b.location),'quaternion':list(b.rotation_quaternion),'mode':b.rotation_mode}
rig.update_tag();body.data.update();bpy.context.view_layer.update()

root=bpy.data.objects.new('BP001_ROOT',None)
bpy.context.scene.collection.objects.link(root)
for obj in [rig,menu]:obj.parent=root
unscaled=bounds(body)
factor=1.85/unscaled['dimensions'][2]
root.scale=(factor,)*3
root.location.z=-bounds(body)['min'][2]
bpy.context.view_layer.update()
body.name='BP001_BODY';rig.name='BP001_RIG';menu.name='BP001_SHAPES'
body.data.name='BP001_MESH';rig.data.name='BP001_ARMATURE';menu.data.name='BP001_SLIDER_ARMATURE'
for obj in [root,body,rig,menu]:obj['library_profile']='BP001/v001'
rig.show_in_front=True
menu.hide_set(True);menu.hide_render=True
meta=bpy.data.objects.get('Metarig')
if meta:bpy.data.objects.remove(meta,do_unlink=True)
body.data.materials.clear()
body.data.materials.append(material('BP001_Clay',(.36,.43,.47)))
for mat in list(bpy.data.materials):
    if mat.name!='BP001_Clay':bpy.data.materials.remove(mat,do_unlink=True)
for image in list(bpy.data.images):
    if image.source=='FILE':bpy.data.images.remove(image,do_unlink=True)
for poly in body.data.polygons:poly.use_smooth=True

def update():
    rig.update_tag();menu.update_tag();body.data.update();bpy.context.view_layer.update()

def difference(first,second):return max((a-b).length for a,b in zip(first,second))

tests=[]
for name,axis,amount in [('head','rotation',.08),('torso','location',.01),
                         ('upper_arm_fk.L','rotation',.08),('upper_arm_fk.R','rotation',.08),
                         ('foot_ik.L','location',.02),('foot_ik.R','location',.02)]:
    b=rig.pose.bones[name];saved=b.matrix_basis.copy();initial=evaluated_points(body)
    if axis=='rotation':b.rotation_quaternion=b.rotation_quaternion @ Quaternion((1,0,0),amount)
    else:b.location.z+=amount
    update();delta=difference(initial,evaluated_points(body))
    b.matrix_basis=saved;update()
    restored=difference(initial,evaluated_points(body))
    tests.append({'control':name,'max_mesh_displacement_m':delta,'restore_error_m':restored,'passed':delta>1e-5 and restored<1e-4})
    assert tests[-1]['passed'],str(tests[-1])
# Verify IK mode is functional separately; neutral arms stay in FK.
for side in ['L','R']:
    parent=rig.pose.bones['upper_arm_parent.'+side];old=parent['IK_FK']
    b=rig.pose.bones['hand_ik.'+side];saved=b.matrix_basis.copy()
    parent['IK_FK']=0.;update();initial=evaluated_points(body)
    b.location.z+=.025;update();delta=difference(initial,evaluated_points(body))
    b.matrix_basis=saved;parent['IK_FK']=old;update()
    tests.append({'control':b.name,'mode':'IK','max_mesh_displacement_m':delta,'passed':delta>1e-5})
    assert tests[-1]['passed']
initial_shape=body.data.shape_keys.key_blocks['Arm Size'].value
menu.pose.bones['arms control'].location.x+=.001;update()
changed_shape=body.data.shape_keys.key_blocks['Arm Size'].value
menu.pose.bones['arms control'].location.x=sliders['arms control'];update()
tests.append({'control':'arms control','shape_key':'Arm Size','passed':abs(changed_shape-initial_shape)>1e-5})
assert tests[-1]['passed']

ui_status={'tested':True,'registered':False,'error':None}
ui=bpy.data.texts.get('rig.004_ui.py')
if ui:
    try:
        scope={'__name__':'__rigify_ui__'}
        exec(compile(ui.as_string(),ui.name,'exec'),scope)
        ui_status['registered']=True
    except Exception as exc:ui_status['error']=repr(exc)

setup_stage()
scene=bpy.context.scene
scene['library_asset']='BP001/v001';scene['review_status']='pending_user_review'
scene['body_style']='articulated mannequin; reference-guided athletic proportions'
scene['neutral_stance']='relaxed A stance; preserve profile shoulder offsets'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_distance=3.2
            area.spaces.active.region_3d.view_location=(0,0,.95)
            area.spaces.active.region_3d.view_rotation=Quaternion((1,0,0),math.radians(90))
            area.spaces.active.shading.type='SOLID'
            area.spaces.active.overlay.show_floor=False

def save_blend(path, active_rig):
    assert Path(path).resolve().is_relative_to(ROOT.resolve())
    bpy.ops.object.select_all(action='DESELECT')
    active_rig.hide_set(False);active_rig.select_set(True)
    bpy.context.view_layer.objects.active=active_rig
    scene.camera=bpy.data.objects['CAM_Front']
    # The source contains orphaned texture materials with missing external paths.
    # Drafts use local clay materials; purge only unused datablocks before packing.
    if ui:ui.use_fake_user=True
    bpy.data.orphans_purge(do_recursive=True)
    bpy.ops.file.pack_all()
    temp=Path(path).with_name(Path(path).stem+'.pending.blend')
    bpy.ops.wm.save_as_mainfile(filepath=str(temp),check_existing=False)
    temp.replace(path)

master_box=bounds(body)
assert abs(master_box['dimensions'][2]-1.85)<1e-4
save_blend(PROFILE_DIR/'master.blend',rig)
for label,cam in [('front','CAM_Front'),('side','CAM_Side'),('three-quarter','CAM_ThreeQuarter')]:
    render(PROFILE_DIR/'previews'/f'{label}.png',cam)
profile.update(status='draft_pending_review',master_file_exists=True,master_height_measured_m=master_box['dimensions'][2],
    master_sha256=hashlib.sha256((PROFILE_DIR/'master.blend').read_bytes()).hexdigest(),
    rig_map='tooling/rig-maps/RIG001-v001.json',slider_values=sliders,
    measurements={'neutral_evaluated_bounds_m':master_box,'measurement_convention':'evaluated body mesh vertex Z extent; outline disabled; excludes widgets and stage'},
    source_rig_sha256=source_hash,blender_version=bpy.app.version_string,
    neutral_controls=neutral,extra_shape_keys={'BP001_TorsoTaper':1.0},
    geometry_style='Articulated source mannequin; approximate reference proportions, not a photoreal anatomy model.',
    calibration_notes=['Body-shape sliders and shoulder-control offsets are profile geometry settings; preserve them when resetting poses.',
        'Shoulder offsets are stored in neutral_controls, not baked into rig rest bones.',
        'Side/back geometry estimated from the provided front reference.'],
    control_tests=tests,rigify_ui_test=ui_status)
write_json(PROFILE_DIR/'profile.json',profile)

# Duplicate the entire actor group, including shape-key data, then remap every internal object reference.
originals=[root,rig,menu,body]
mapping={}
for obj in originals:
    clone=obj.copy()
    if obj.data:clone.data=obj.data.copy()
    bpy.context.scene.collection.objects.link(clone)
    mapping[obj]=clone

def remap_drivers(block):
    if block is None or not getattr(block,'animation_data',None):return
    for fc in block.animation_data.drivers:
        for var in fc.driver.variables:
            for target in var.targets:
                if target.id in mapping:target.id=mapping[target.id]

def remap_constraints(constraints):
    for c in constraints:
        for prop in ['target','pole_target','space_object']:
            target=getattr(c,prop,None)
            if target in mapping:setattr(c,prop,mapping[target])
        for target in getattr(c,'targets',[]):
            if target.target in mapping:target.target=mapping[target.target]

def remap_properties(block):
    for key in list(block.keys()):
        val=block[key]
        if isinstance(val,bpy.types.ID) and val in mapping:block[key]=mapping[val]
        elif hasattr(val,'keys'):remap_properties(val)

for original,clone in mapping.items():
    if original.parent in mapping:clone.parent=mapping[original.parent]
    remap_constraints(clone.constraints);remap_drivers(clone);remap_properties(clone)
    if clone.data:
        remap_drivers(clone.data)
        if getattr(clone.data,'shape_keys',None):remap_drivers(clone.data.shape_keys)
    if clone.type=='ARMATURE':
        for b in clone.pose.bones:remap_constraints(b.constraints);remap_properties(b)
    for mod in clone.modifiers:
        if hasattr(mod,'object') and mod.object in mapping:mod.object=mapping[mod.object]

root_b,rig_b,menu_b,body_b=[mapping[o] for o in originals]
for actor,group in [('A',originals),('B',[root_b,rig_b,menu_b,body_b])]:
    for obj,role in zip(group,['ROOT','RIG','SHAPES','BODY']):
        obj.name=f'CPL01_{actor}_{role}'
        obj['library_pair']='CPL01/v001';obj['actor_id']=actor
    group[0].location.x=-.50 if actor=='A' else .50
root_b.scale=tuple(v*(1.77/1.85) for v in root.scale)
root_b.location.z=0.;root_b.location.z=-bounds(body_b)['min'][2]
menu_b.hide_set(True);menu_b.hide_render=True
body.data.materials.clear();body.data.materials.append(material('CPL01_A_Clay',(.25,.40,.46)))
body_b.data.materials.clear();body_b.data.materials.append(material('CPL01_B_Clay',(.53,.37,.24)))
scene['library_asset']='CPL01/v001'
scene['actor_mapping']='A/B assigned by character identity; dataset mapping not yet selected'

# Cross-character references are checked structurally and by moving each actor in turn.
independence=[]
for moving_rig,moving_body,other_body in [(rig,body,body_b),(rig_b,body_b,body)]:
    before=evaluated_points(other_body);own=evaluated_points(moving_body)
    b=moving_rig.pose.bones['upper_arm_fk.L'];saved=b.matrix_basis.copy()
    b.rotation_quaternion=b.rotation_quaternion @ Quaternion((1,0,0),.12)
    moving_rig.update_tag();bpy.context.view_layer.update()
    other_delta=difference(before,evaluated_points(other_body));own_delta=difference(own,evaluated_points(moving_body))
    b.matrix_basis=saved;moving_rig.update_tag();bpy.context.view_layer.update()
    independence.append({'moving':moving_rig.name,'other_max_delta_m':other_delta,'own_max_delta_m':own_delta,
                         'passed':other_delta<1e-7 and own_delta>1e-5})
    assert independence[-1]['passed'],str(independence[-1])

actor_boxes=[bounds(o) for o in [body,body_b]]
for box,target in zip(actor_boxes,[1.85,1.77]):assert abs(box['dimensions'][2]-target)<1e-4
scene.render.resolution_x=1200;scene.render.resolution_y=1000
for name in ['CAM_Front','CAM_Side','CAM_ThreeQuarter']:bpy.data.objects[name].data.ortho_scale=2.8
# Side-view pairs are separated along the camera-right direction for readable review.
save_blend(PAIR_DIR/'template.blend',rig)
for label,cam in [('front','CAM_Front'),('three-quarter','CAM_ThreeQuarter')]:render(PAIR_DIR/'previews'/f'{label}.png',cam)
# Render each side independently, avoiding one character obscuring the other.
scene.render.resolution_x=800;scene.render.resolution_y=1000
bpy.data.objects['CAM_Side'].data.ortho_scale=2.15
for actor,visible,hidden in [('a',body,body_b),('b',body_b,body)]:
    hidden.hide_render=True
    render(PAIR_DIR/'previews'/f'side-{actor}.png','CAM_Side')
    hidden.hide_render=False
scene.render.resolution_x=1200;scene.render.resolution_y=1000
bpy.data.objects['CAM_Side'].data.ortho_scale=2.8
pair.update(status='draft_pending_review',template_file_exists=True,
    template_sha256=hashlib.sha256((PAIR_DIR/'template.blend').read_bytes()).hexdigest(),
    scaling_method='Common parent Empty uniform scale, preserving un-applied rig transforms; evaluated heights verified.',
    measurements={actor:{'height_m':box['dimensions'][2],'bounds_m':box} for actor,box in zip(['A','B'],actor_boxes)},
    objects={actor:{'root':group[0].name,'rig':group[1].name,'shape_controls':group[2].name,'body':group[3].name} for actor,group in [('A',originals),('B',[root_b,rig_b,menu_b,body_b])]},
    camera_settings={'type':'ORTHO','render_size':[1200,1000],'ortho_scale':2.8,'forward_axis':'-Y'},
    lighting_settings={'type':'three_area_lights','world_strength':.5},
    independence_tests=independence,blender_version=bpy.app.version_string,
    provisional=True,approved_at=None)
write_json(PAIR_DIR/'pair.json',pair)
write_json(ROOT/'tooling/rig-maps/RIG001-v001.json',{
    'schema_version':1,'rig_map_id':'RIG001','version':'v001','source_sha256':source_hash,
    'inspection':'RIG001-inspection-v001.json','blender_version':bpy.app.version_string,
    'forward_axis':'-Y','up_axis':'+Z','controls':{
        'root':'root','torso':'torso','hips':'hips','chest':'chest','head':'head','neck':'neck',
        'hand_ik':['hand_ik.L','hand_ik.R'],'arm_fk':['upper_arm_fk.L','upper_arm_fk.R'],
        'elbow_poles':['upper_arm_ik_target.L','upper_arm_ik_target.R'],
        'foot_ik':['foot_ik.L','foot_ik.R'],'knee_poles':['thigh_ik_target.L','thigh_ik_target.R'],
        'arm_mode_properties':['upper_arm_parent.L[IK_FK]','upper_arm_parent.R[IK_FK]'],
        'leg_mode_properties':['thigh_parent.L[IK_FK]','thigh_parent.R[IK_FK]']},
    'mode_semantics':{'IK_FK_0':'IK','IK_FK_1':'FK','neutral_arms':'FK','neutral_legs':'IK'},
    'tests':tests,'rigify_ui':ui_status,'limitations':['Basic control/deformation tests only; animation and every individual bone are not exhaustively tested.',
        'Preserve profile shoulder offsets and shape settings when resetting a pose.']})
assert hashlib.sha256(source.read_bytes()).hexdigest()==source_hash
print('CHARACTER_BUILD_COMPLETE',json.dumps({'heights_m':[b['dimensions'][2] for b in actor_boxes],
    'control_tests':len(tests),'independence':independence,'ui':ui_status}))
