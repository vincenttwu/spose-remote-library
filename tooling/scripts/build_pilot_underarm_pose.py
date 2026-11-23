"""Build the SRC002 V01 underarm-support pilot in a separate Blender process."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Matrix,Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from character_common import ROOT,render,evaluated_points,write_json

OUT=ROOT/'poses/UFDG-FWCH-V01/CPL01/v001/r001'
record=json.loads((OUT/'pose.json').read_text(encoding='utf-8'))
assert record['accepted_at'] is None
assert record['status'] not in ['accepted','excluded','blocked'], 'Do not rebuild a parked or accepted job'
if (OUT/'scene.blend').exists():
    assert '--replace-draft' in sys.argv, 'Use --replace-draft deliberately to replace this unaccepted draft'
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
    # Native palm-plane inspection identifies the thin axis near Z; map this frame
    # instead of assuming a bone-local axis is the palm normal.
    rest_y=bone.bone.matrix_local.to_3x3().col[1].normalized()
    sign=1 if name.endswith('.L') else -1
    # Thin-axis estimate from the source palm geometry, mirrored by side.
    rest_n=Vector((-.1322749*sign,-.3410520,-.9306916))
    rest_n=(rest_n-rest_y*rest_n.dot(rest_y)).normalized()
    desired_y=Vector(direction).normalized()
    desired_n=Vector(normal);desired_n=(desired_n-desired_y*desired_n.dot(desired_y)).normalized()
    rest_frame=Matrix((rest_y,rest_n,rest_y.cross(rest_n))).transposed()
    desired_frame=Matrix((desired_y,desired_n,desired_y.cross(desired_n))).transposed()
    matrix=(desired_frame @ rest_frame.transposed() @ bone.bone.matrix_local.to_3x3()).to_4x4()
    matrix.translation=rig.matrix_world.inverted() @ Vector(target)
    rig.pose.bones[name].matrix=matrix;update()

for actor,rig in rigs.items():
    # Rigify's property alone does not disable Blender IK stretch/compression.
    for bone in rig.pose.bones:
        for constraint in bone.constraints:
            if constraint.type=='IK':constraint.use_stretch=False
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
pose_torso('A',(0,.25,.62),92)
for actor in ['A','B']:
    rig=rigs[actor]
    for name,angle in [('neck',-35 if actor=='B' else -12),('head',-50 if actor=='B' else -12)]:
        b=rig.pose.bones[name]
        axis=b.bone.matrix_local.to_3x3().inverted() @ Vector((1,0,0))
        b.rotation_mode='QUATERNION'
        from mathutils import Quaternion
        b.rotation_quaternion=Quaternion(axis,math.radians(angle))
update()

for side,sign in [('L',1),('R',-1)]:
    point('B','foot_ik.'+side,(.14*sign,.18,.078),Matrix.Rotation(math.radians(135),4,'X'))
    point('B','thigh_ik_target.'+side,(.14*sign,-.8,.05))
    hand('B','hand_ik.'+side,(.23*sign,-.83,.035),(0,-1,0),(0,0,-1))
    point('B','upper_arm_ik_target.'+side,(.42*sign,-.65,.15))
    foot_rotation=Matrix.Rotation(math.radians(25*sign),4,'Z')
    point('A','foot_ik.'+side,(.36*sign,.43,.095),foot_rotation)
    point('A','thigh_ik_target.'+side,(.9*sign,-.05,.20))
    hand('A','hand_ik.'+side,(.245*sign,-.36,.185),(-sign,.05,-.35),(0,.4,.9))
    point('A','upper_arm_ik_target.'+side,(.85*sign,-.15,-.10))
update()

def region_points(actor,role,side=None):
    obj=bpy.data.objects[f'CPL01_{actor}_BODY']
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
    try:
        ids={i for face in mesh.polygons if obj.data.materials[face.material_index]['region']==role for i in face.vertices}
        points=[ev.matrix_world @ mesh.vertices[i].co for i in ids]
        return points if side is None else [v for v in points if (v.x>0)==(side=='L')]
    finally:ev.to_mesh_clear()

# Calibrate the front knee/shin support surface without changing leg lengths.
low,high=.18,.45
for iteration in range(14):
    height=(low+high)*.5
    pose_torso('B',(0,0,height),115)
    minimum=min(v.z for v in region_points('B','calves'))
    if minimum<.001:low=height
    else:high=height
front_pelvis_height=(low+high)*.5
pose_torso('B',(0,0,front_pelvis_height),115)

palm_targets={}
for side,sign in [('L',1),('R',-1)]:
    z=.035
    for iteration in range(3):
        min_z=min(v.z for v in region_points('B','hands',side))
        z+=.001-min_z
        hand('B','hand_ik.'+side,(.23*sign,-.83,z),(0,-1,0),(0,0,-1))
    palm_targets[side]=[.23*sign,-.83,z]

elbow_pole_choices={}
for side,sign in [('L',1),('R',-1)]:
    candidates=[]
    for height in [-.6,-.3,0.,.3,.6,1.0]:
        candidate=(.42*sign,-.65,height)
        point('B','upper_arm_ik_target.'+side,candidate)
        minimum=min(v.z for v in region_points('B','forearms',side))
        elbow_z=world_head('B','DEF-forearm.'+side).z
        score=max(0.,.002-minimum)*100+abs(elbow_z-.10)
        candidates.append((score,candidate,minimum))
    _,choice,minimum=min(candidates,key=lambda c:c[0])
    point('B','upper_arm_ik_target.'+side,choice)
    elbow_pole_choices[side]={'world_target_m':choice,'forearm_min_z_m':minimum}

head_bone=rigs['B'].pose.bones['head']
head_axis=head_bone.bone.matrix_local.to_3x3().inverted() @ Vector((1,0,0))
neck_bone=rigs['B'].pose.bones['neck']
neck_axis=neck_bone.bone.matrix_local.to_3x3().inverted() @ Vector((1,0,0))
head_candidates=[]
for neck_angle in [-25,-35,-45,-55]:
    neck_bone.rotation_quaternion=Quaternion(neck_axis,math.radians(neck_angle))
    for angle in [-5,-10,-20,-30,-40,-50,-60]:
        head_bone.rotation_quaternion=Quaternion(head_axis,math.radians(angle));update()
        minimum=min(v.z for v in region_points('B','head_neck'))
        if minimum>=.005:
            score=(abs(neck_angle+25)+abs(angle+15))/180
            head_candidates.append((score,neck_angle,angle,minimum))
assert head_candidates,'No head clearance candidate found'
_,neck_angle,head_angle,head_minimum=min(head_candidates,key=lambda item:item[0])
neck_bone.rotation_quaternion=Quaternion(neck_axis,math.radians(neck_angle))
head_bone.rotation_quaternion=Quaternion(head_axis,math.radians(head_angle));update()

measurements={}
for actor,rig in rigs.items():
    measurements[actor]={name:list(world_head(actor,name)) for name in ['torso','head','DEF-upper_arm.L','DEF-upper_arm.R',
        'DEF-forearm.L','DEF-forearm.R','DEF-hand.L','DEF-hand.R','DEF-thigh.L','DEF-thigh.R',
        'DEF-shin.L','DEF-shin.R','DEF-foot.L','DEF-foot.R']}
    pts=evaluated_points(bpy.data.objects[f'CPL01_{actor}_BODY'])
    measurements[actor]['mesh_min_z']=min(v.z for v in pts)
measurements['floor_region_min_z_m']={
    f'{actor}_{role}_{side}':min(v.z for v in region_points(actor,role,side))
    for actor,roles in [('A',['feet']),('B',['hands','calves','feet'])] for role in roles for side in ['L','R']}
measurements['front_palm_targets_world_m']=palm_targets
measurements['front_pelvis_height_m']=front_pelvis_height
measurements['elbow_pole_choices']=elbow_pole_choices
measurements['front_head_adjustment']={'head_local_angle_degrees':head_angle,'neck_local_angle_degrees':neck_angle,'head_neck_min_z_m':head_minimum}

target=Vector((0,-.22,.55))
for name,loc in [('CAM_Front',(0,-6,2.0)),('CAM_Side',(6,-.22,1.8)),('CAM_ThreeQuarter',(4,-6,3.0))]:
    camera=bpy.data.objects[name];camera.location=loc;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale=2.0
scene.render.resolution_x=1200;scene.render.resolution_y=1000
scene['library_asset']='UFDG-FWCH-V01/CPL01/v001/r001'
scene['review_status']='pilot_working_draft'
scene['source_id']='SRC002/v001';scene['appearance_mode']='regions'
scene.camera=bpy.data.objects['CAM_ThreeQuarter']
temp=OUT/'scene.pending.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(temp),check_existing=False)
temp.replace(OUT/'scene.blend')
for label,cam in [('front','CAM_Front'),('side','CAM_Side'),('three-quarter','CAM_ThreeQuarter')]:render(OUT/'previews'/f'{label}.png',cam)
write_json(OUT/'geometry-measurements.json',measurements)
print('PILOT_DRAFT_RENDERED',json.dumps(measurements))
