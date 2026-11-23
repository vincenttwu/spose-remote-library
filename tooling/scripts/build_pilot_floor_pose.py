"""Build the SRC002 first-entry nonsexual floor-support pilot in a separate Blender process."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Matrix,Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from character_common import ROOT,render,evaluated_points,write_json

OUT=ROOT/'poses/UFDG-FWCH-V00/CPL01/v001/r001'
record=json.loads((OUT/'pose.json').read_text(encoding='utf-8'))
assert record['accepted_at'] is None
bpy.ops.wm.open_mainfile(filepath=str(ROOT/record['template_path']),use_scripts=False)
bpy.context.preferences.filepaths.save_version=0
scene=bpy.context.scene
rigs={a:bpy.data.objects[f'CPL01_{a}_RIG'] for a in ['A','B']}
roots={a:bpy.data.objects[f'CPL01_{a}_ROOT'] for a in ['A','B']}
for root in roots.values():root.location.x=0.;root.location.y=0.

def update():
    for rig in rigs.values():rig.update_tag()
    bpy.context.view_layer.update()

def world_head(actor,name):
    rig=rigs[actor]
    return rig.matrix_world @ rig.pose.bones[name].head

def point(actor,name,target,rotation=None):
    rig=rigs[actor];bone=rig.pose.bones[name]
    matrix=bone.matrix.copy()
    if rotation is not None:
        # Root parents have uniform scale and no rotation.
        matrix=rotation @ bone.bone.matrix_local.to_3x3().to_4x4()
    matrix.translation=rig.matrix_world.inverted() @ Vector(target)
    bone.matrix=matrix
    update()

def pose_torso(actor,target,degrees):
    point(actor,'torso',target,Matrix.Rotation(math.radians(degrees),4,'X'))

def hand_frame(direction,normal):
    y=Vector(direction).normalized();z=Vector(normal).normalized()
    x=y.cross(z).normalized();z=x.cross(y).normalized()
    return Matrix((x,y,z)).transposed().to_4x4()

def hand(actor,name,target,direction,normal):
    rig=rigs[actor];bone=rig.pose.bones[name]
    # Native T-pose palm normals face anatomical forward (-Y); map this frame
    # instead of assuming a bone-local axis is the palm normal.
    rest_y=bone.bone.matrix_local.to_3x3().col[1].normalized()
    rest_n=Vector((0,-1,0));rest_n=(rest_n-rest_y*rest_n.dot(rest_y)).normalized()
    desired_y=Vector(direction).normalized()
    desired_n=Vector(normal);desired_n=(desired_n-desired_y*desired_n.dot(desired_y)).normalized()
    rest_frame=Matrix((rest_y,rest_n,rest_y.cross(rest_n))).transposed()
    desired_frame=Matrix((desired_y,desired_n,desired_y.cross(desired_n))).transposed()
    matrix=(desired_frame @ rest_frame.transposed() @ bone.bone.matrix_local.to_3x3()).to_4x4()
    matrix.translation=rig.matrix_world.inverted() @ Vector(target)
    rig.pose.bones[name].matrix=matrix;update()

for actor,rig in rigs.items():
    for side in ['L','R']:
        rig.pose.bones['upper_arm_parent.'+side]['IK_FK']=0.
        rig.pose.bones['upper_arm_parent.'+side]['IK_Stretch']=0.
        rig.pose.bones['upper_arm_parent.'+side]['pole_vector']=True
        rig.pose.bones['thigh_parent.'+side]['IK_FK']=0.
        rig.pose.bones['thigh_parent.'+side]['IK_Stretch']=0.
        rig.pose.bones['thigh_parent.'+side]['pole_vector']=True
update()

# Front floor reach and rear foot-supported squat. No pelvic contact is imposed.
pose_torso('B',(0,0,.47),115)
pose_torso('A',(0,.43,.51),75)
for actor in ['A','B']:
    rig=rigs[actor]
    for name,angle in [('neck',-12),('head',-28 if actor=='B' else -12)]:
        b=rig.pose.bones[name]
        axis=b.bone.matrix_local.to_3x3().inverted() @ Vector((1,0,0))
        b.rotation_mode='QUATERNION'
        from mathutils import Quaternion
        b.rotation_quaternion=Quaternion(axis,math.radians(angle))
update()

for side,sign in [('L',1),('R',-1)]:
    point('B','foot_ik.'+side,(.14*sign,.43,.078),Matrix.Rotation(math.radians(135),4,'X'))
    point('B','thigh_ik_target.'+side,(.14*sign,-.8,.05))
    hand('B','hand_ik.'+side,(.23*sign,-.78,.035),(0,-1,0),(0,0,-1))
    point('B','upper_arm_ik_target.'+side,(.42*sign,-.65,.15))
    foot_rotation=Matrix.Rotation(math.radians(25*sign),4,'Z')
    point('A','foot_ik.'+side,(.36*sign,.43,.095),foot_rotation)
    point('A','thigh_ik_target.'+side,(.9*sign,-.05,.20))
    hand('A','hand_ik.'+side,(.245*sign,-.36,.35),(0,-1,-.15),(-.65*sign,0,-.76))
    point('A','upper_arm_ik_target.'+side,(.58*sign,-.12,.38))
update()

measurements={}
for actor,rig in rigs.items():
    measurements[actor]={name:list(world_head(actor,name)) for name in ['torso','head','DEF-upper_arm.L','DEF-upper_arm.R',
        'DEF-forearm.L','DEF-forearm.R','DEF-hand.L','DEF-hand.R','DEF-thigh.L','DEF-thigh.R',
        'DEF-shin.L','DEF-shin.R','DEF-foot.L','DEF-foot.R']}
    pts=evaluated_points(bpy.data.objects[f'CPL01_{actor}_BODY'])
    measurements[actor]['mesh_min_z']=min(v.z for v in pts)

target=Vector((0,-.22,.55))
for name,loc in [('CAM_Front',(0,-6,2.0)),('CAM_Side',(6,-.22,1.8)),('CAM_ThreeQuarter',(4,-6,3.0))]:
    camera=bpy.data.objects[name];camera.location=loc;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale=2.0
scene.render.resolution_x=1200;scene.render.resolution_y=1000
scene['library_asset']='UFDG-FWCH-V00/CPL01/v001/r001'
scene['review_status']='pilot_working_draft'
scene['source_id']='SRC002/v001';scene['appearance_mode']='regions'
scene.camera=bpy.data.objects['CAM_ThreeQuarter']
temp=OUT/'scene.pending.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(temp),check_existing=False)
temp.replace(OUT/'scene.blend')
for label,cam in [('front','CAM_Front'),('side','CAM_Side'),('three-quarter','CAM_ThreeQuarter')]:render(OUT/'previews'/f'{label}.png',cam)
write_json(OUT/'working-measurements.json',measurements)
print('PILOT_DRAFT_RENDERED',json.dumps(measurements))
