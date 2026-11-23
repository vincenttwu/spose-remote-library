"""Rigify mannequin positional and evaluated-mesh floor engine (Blender 5.2.2).

Migrated from the *working techniques*, not the unapproved poses, in:
  tooling/scripts/build_pilot_underarm_pose.py
  tooling/scripts/build_pilot_floor_pose.py

This is a candidate pose solver. It does not validate force, balance, anatomy, or
penetration. All supports/contact assertions are geometric checks; no approval.
"""
import math
from mathutils import Vector, Matrix, Quaternion


class RigifyFloorEngine:
    def __init__(self,bpy):
        self.bpy=bpy
        self.rigs={a:bpy.data.objects[f'CPL01_{a}_RIG'] for a in ('A','B')}
        self.roots={a:bpy.data.objects[f'CPL01_{a}_ROOT'] for a in ('A','B')}
        self.bodies={a:bpy.data.objects[f'CPL01_{a}_BODY'] for a in ('A','B')}
        self.applied=[]
        self.calibration=[]

    def update(self):
        for rig in self.rigs.values():rig.update_tag()
        self.bpy.context.view_layer.update()

    def bone(self,actor,name):return self.rigs[actor].pose.bones[name]
    def head(self,actor,name):
        rig=self.rigs[actor]
        return rig.matrix_world @ rig.pose.bones[name].head

    def initialize(self):
        for actor,rig in self.rigs.items():
            for bone in rig.pose.bones:
                for constraint in bone.constraints:
                    if constraint.type=='IK':constraint.use_stretch=False
            for side in ('L','R'):
                for part in ('upper_arm','thigh'):
                    parent=rig.pose.bones[f'{part}_parent.{side}']
                    parent['IK_FK']=0.0
                    parent['IK_Stretch']=0.0
                    parent['pole_vector']=True
        self.update()

    def point(self,actor,name,target,world_rotation=None):
        rig=self.rigs[actor];bone=self.bone(actor,name)
        matrix=bone.matrix.copy()
        if world_rotation is not None:
            matrix=world_rotation @ bone.bone.matrix_local.to_3x3().to_4x4()
        matrix.translation=rig.matrix_world.inverted() @ Vector(target)
        bone.matrix=matrix
        self.update()

    def palm(self,actor,name,target,direction,normal):
        """Historical palm-frame solution with side-dependent rest normals."""
        rig=self.rigs[actor];bone=self.bone(actor,name)
        rest_y=bone.bone.matrix_local.to_3x3().col[1].normalized()
        sign=1 if name.endswith('.L') else -1
        rest_n=Vector((-.1322749*sign,-.3410520,-.9306916))
        rest_n=rest_n-rest_y*rest_n.dot(rest_y)
        if rest_n.length<1e-5:raise ValueError('Degenerate native palm frame')
        rest_n.normalize()
        desired_y=Vector(direction).normalized()
        desired_n=Vector(normal)
        desired_n=desired_n-desired_y*desired_n.dot(desired_y)
        if desired_n.length<1e-5:raise ValueError('Degenerate desired palm frame')
        desired_n.normalize()
        rest_frame=Matrix((rest_y,rest_n,rest_y.cross(rest_n))).transposed()
        desired_frame=Matrix((desired_y,desired_n,desired_y.cross(desired_n))).transposed()
        # The palm frame is already an *absolute* pose matrix in rig space.
        # Do NOT pass it through point(..., world_rotation): point() multiplies
        # by the rest matrix for torso/foot rotations; doing so here would
        # apply the rest orientation twice and turn palms away from the target.
        matrix=(desired_frame @ rest_frame.transposed() @ bone.bone.matrix_local.to_3x3()).to_4x4()
        matrix.translation=rig.matrix_world.inverted() @ Vector(target)
        bone.matrix=matrix
        self.update()

    def apply(self,item):
        a=item['actor'];s=item['space'];v=item['value']
        if s=='OBJECT_WORLD_LOCATION_M':
            self.roots[a].location=Vector(v);self.update()
        elif s=='OBJECT_WORLD_ROTATION_DEG':
            self.roots[a].rotation_mode='XYZ'
            self.roots[a].rotation_euler=tuple(math.radians(x) for x in v)
            self.update()
        elif s=='POSE_WORLD_HEAD_M':self.point(a,item['bone'],v)
        elif s=='POSE_WORLD_HEAD_ROT_X_DEG':
            rot=Matrix.Rotation(math.radians(item.get('yaw_z_deg',0)),4,'Z') @ Matrix.Rotation(math.radians(item['pitch_x_deg']),4,'X')
            self.point(a,item['bone'],v,rot)
        elif s=='POSE_WORLD_HAND_FRAME':
            self.palm(a,item['bone'],v,item['direction_world'],item['normal_world'])
        elif s=='POSE_RELATIVE_BONE_HEAD_HAND':
            base=self.head(item['target_actor'],item['target_bone'])
            self.palm(a,item['bone'],base+Vector(v),item['direction_world'],item['normal_world'])
        elif s=='POSE_LOCAL_BONE_AXIS_ADD_DEG':
            bone=self.bone(a,item['bone'])
            axis={'X':Vector((1,0,0)),'Y':Vector((0,1,0)),'Z':Vector((0,0,1))}[item['axis']]
            axis=bone.bone.matrix_local.to_3x3().inverted() @ axis
            bone.rotation_mode='QUATERNION'
            bone.rotation_quaternion=Quaternion(axis,math.radians(item['angle_deg'])) @ bone.rotation_quaternion
            self.update()
        elif s=='POSE_LOCAL_REST_AXIS_ROT_X_DEG':
            bone=self.bone(a,item['bone'])
            axis=bone.bone.matrix_local.to_3x3().inverted() @ Vector((1,0,0))
            bone.rotation_mode='QUATERNION';bone.rotation_quaternion=Quaternion(axis,math.radians(item['angle_deg']))
            self.update()
        elif s=='POSE_LOCAL_ROTATION_DEG':
            bone=self.bone(a,item['bone']);bone.rotation_mode='XYZ'
            bone.rotation_euler=tuple(math.radians(x) for x in v);self.update()
        else:raise ValueError(f'Unsupported v2 pose space: {s}')
        self.applied.append({'actor':a,'bone':item.get('bone'), 'space':s})

    def region_points(self, actor, region, side=None):
        """Evaluated vertex samples by existing VP001 material region.

        head_side is an approximate side-of-head patch, not a proven cheek label.
        Forearms are narrowed to the appropriate DEF-forearm segment, avoiding
        elbow/upper-arm or contralateral vertices in the material region.
        """
        obj=self.bodies[actor]
        ev=obj.evaluated_get(self.bpy.context.evaluated_depsgraph_get())
        mesh=ev.to_mesh()
        try:
            label='head_neck' if region=='head_side' else region
            idset=set()
            for poly in mesh.polygons:
                mat=obj.material_slots[poly.material_index].material if poly.material_index < len(obj.material_slots) else None
                role=mat.get('region') if mat else None
                if region=='knees':
                    accept=role in ('calves','thighs')
                else:
                    accept=role==label
                if accept:idset.update(poly.vertices)
            pts=[ev.matrix_world @ mesh.vertices[i].co for i in idset]
            if region=='knees':
                knee_bones=[self.head(actor,'DEF-shin.'+s) for s in ('L','R') if side is None or s==side]
                pts=[p for p in pts if any((p-k).length<.135 for k in knee_bones)]
            elif region=='forearms':
                side_list=('L','R') if side is None else (side,)
                rig=self.rigs[actor]
                segments=[(rig.matrix_world @ self.bone(actor,'DEF-forearm.'+s).head,
                           rig.matrix_world @ self.bone(actor,'DEF-forearm.'+s).tail) for s in side_list]
                def near_segment(p,a,b):
                    v=b-a
                    t=max(0.,min(1.,(p-a).dot(v)/max(v.length_squared,1e-8)))
                    return (p-(a+t*v)).length < .15
                pts=[p for p in pts if any(near_segment(p,a,b) for a,b in segments)]
            elif region=='head_side':
                center=self.head(actor,'head')
                pts=[p for p in pts if (p-center).length<.22]
                if side:
                    pts=[p for p in pts if (p.x>=center.x)==(side=='L')]
            elif side:
                center=self.head(actor,'hips').x
                pts=[p for p in pts if (p.x>=center)==(side=='L')]
            if not pts:raise ValueError(f'No evaluated {region}/{side} mesh points for {actor}')
            return pts
        finally:
            ev.to_mesh_clear()

    def min_z(self,actor,region,side=None):
        return min(v.z for v in self.region_points(actor,region,side))

    def calibrate_floor(self,stages):
        """One stage translates a specified rig control along world Z (bounded).

        Knee stages must precede hand/foot stages. Each stage checks its actual
        evaluated material-region mesh, never IK handle Z. Supports can fail.
        """
        for st in stages:
            try:
                a=st['actor'];region=st['region'];side=st.get('side')
                bone=st['adjust_bone'];target=float(st.get('target_z_m',.004))
                max_step=float(st.get('max_total_shift_m',.22))
                before=self.min_z(a,region,side)
                applied=0.0
                for iteration in range(int(st.get('iterations',5))):
                    z=self.min_z(a,region,side)
                    delta=target-z
                    if abs(delta)<.0015:break
                    # Explicitly cap the accumulated motion to prevent catastrophic poses.
                    step=max(-.06,min(.06,delta))
                    step=max(-max_step-applied,min(max_step-applied,step))
                    if abs(step)<.00001:break
                    current=self.head(a,bone)
                    self.point(a,bone,current+Vector((0,0,step)))
                    applied+=step
                after=self.min_z(a,region,side)
                result={'actor':a,'region':region,'side':side,'adjust_bone':bone,
                        'before_z_m':round(before,6),'after_z_m':round(after,6),
                        'shift_m':round(applied,6),
                        'tolerance_m':st.get('tolerance_m',.018),
                        'in_tolerance':abs(after-target)<=float(st.get('tolerance_m',.018))}
                self.calibration.append(result)
            except Exception as exc:
                self.calibration.append({"actor":st.get("actor"),"region":st.get("region"),
                    "side":st.get("side"),"adjust_bone":st.get("adjust_bone"),
                    "error":f"{type(exc).__name__}: {exc}","in_tolerance":False,
                    "note":"Diagnostic stage unavailable; continue remaining supports and render"})
        return self.calibration

    def align_pelvic_surfaces(self,plan):
        """Bounded Y-only approach of rear actor to receiver's pelvis mesh.

        Proximity cannot distinguish surface penetration from proper contact.
        Refuses any backward-into-target directions; diagnostic only.
        """
        from mathutils.kdtree import KDTree
        if not plan:return {'applied':False,'reason':'No pelvic plan'}
        a=plan['actor'];b=plan['target_actor']
        target=float(plan.get('target_distance_m',.03))
        total_limit=float(plan.get('max_forward_shift_m',.16))
        used=0.0;measurements=[]
        for _ in range(int(plan.get('iterations',7))):
            av=self.region_points(a,'pelvis')
            bv=self.region_points(b,'pelvis')
            tree=KDTree(len(bv))
            for idx,v in enumerate(bv):tree.insert(v,idx)
            tree.balance()
            d=min(tree.find(v)[2] for v in av[::max(1,len(av)//2500)])
            measurements.append(round(d,6))
            if d <= target+.005:break
            current_a=self.head(a,'hips')
            current_b=self.head(b,'hips')
            if current_a.y<=current_b.y+.035:
                break # already too far forward; no arbitrary reversal
            step=min(.035,d-target,total_limit-used)
            if step<=.0001:break
            torso=self.head(a,'torso')
            self.point(a,'torso',torso+Vector((0,-step,0)))
            used+=step
        return {'applied':True,'actor':a,'target_actor':b,
                'distance_history_m':measurements,'rear_forward_shift_m':round(used,6),
                'closest_pelvis_distance_m':measurements[-1] if measurements else None,
                'target_distance_m':target,'diagnostic_only':True}

    def palm_to_hip_surface(self, plan):
        """Bounded per-side approach using evaluated palm and lateral-hip patches.

        Uses the VP001 `hands` and `pelvis` material regions. The wrist-near
        hand subpatch excludes distal fingers; the lateral pelvis band excludes
        thigh/leg hits. This is geometric proximity, not a physical grip or a
        signed penetration solver. Failure is returned as evidence, not raised.
        """
        from mathutils.kdtree import KDTree
        if not plan:return {'enabled':False,'reason':'No palm surface plan'}
        actor=plan.get('actor','A'); target=plan.get('target_actor','B')
        max_total=min(.28,max(.02,float(plan.get('max_translation_m',.19))))
        target_gap=float(plan.get('target_gap_m',.008))
        iterations=min(10,max(1,int(plan.get('iterations',6))))
        out={'enabled':True,'method':'VP001_evaluated_lateral_pelvis_to_wrist_near_palm',
             'target_gap_m':target_gap,'sides':{},
             'warning':'Unsigned surface proximity; no reliable penetration depth or force simulation.'}
        # Alternating both sides mitigates slight changes in the mesh when the
        # opposite IK moves. Never move torso or source meshes in this stage.
        for side in ('L','R'):
            result={'side':side,'contact_target_valid':False,'converged':False,'translation_m':0.,'gap_history_m':[]}
            used=0.
            try:
                for it in range(iterations):
                    hip_center=self.head(target,'hips')
                    hippts=[p for p in self.region_points(target,'pelvis',side)
                            if abs(p.z-hip_center.z)<.22 and abs(p.y-hip_center.y)<.28]
                    if len(hippts)<8:
                        raise ValueError('Insufficient side-specific hip mesh patch')
                    # Surface strip on lateral 25% of the selected hip region.
                    sorted_x=sorted(p.x for p in hippts)
                    cutoff=sorted_x[int(len(sorted_x)*(.75 if side=='L' else .25))]
                    lateral=[p for p in hippts if (p.x>=cutoff if side=='L' else p.x<=cutoff)]
                    if len(lateral)<5:raise ValueError('Lateral pelvis strip too small')
                    wrist=self.head(actor,'hand_ik.'+side)
                    palms=[p for p in self.region_points(actor,'hands',side) if (p-wrist).length<.105]
                    if len(palms)<5:
                        raise ValueError('Cannot localize wrist-near palm vertices; no unsafe whole-body fallback')
                    # Choose the side-hip surface closest to the current palm
                    # centroid in the Y/Z plane, then the palm vertex nearest it.
                    center=sum(palms,Vector((0,0,0)))/len(palms)
                    site=min(lateral,key=lambda p:(p.y-center.y)**2+(p.z-center.z)**2)
                    outward=Vector((1,0,0)) if side=='L' else Vector((-1,0,0))
                    site=site+outward*target_gap
                    nearest=min(palms,key=lambda p:(p-site).length)
                    delta=site-nearest
                    gap=(site-nearest).length
                    result['gap_history_m'].append(round(gap,6))
                    result['contact_target_valid']=True
                    if gap<=max(target_gap+.006,.015):
                        result['converged']=True;break
                    if used>=max_total-.0001:break
                    step=min(.055,gap-target_gap,max_total-used)
                    if step<=.0001:break
                    displacement=delta.normalized()*step
                    self.point(actor,'hand_ik.'+side,wrist+displacement)
                    used+=step
                result['translation_m']=round(used,6)
                # Post-IK evaluated geometry is the authoritative measurement.
                hp=[p for p in self.region_points(target,'pelvis',side)
                    if abs(p.z-self.head(target,'hips').z)<.22 and abs(p.y-self.head(target,'hips').y)<.28]
                xs=sorted(p.x for p in hp)
                cutoff=xs[int(len(xs)*(.75 if side=='L' else .25))]
                hp=[p for p in hp if (p.x>=cutoff if side=='L' else p.x<=cutoff)]
                wrist=self.head(actor,'hand_ik.'+side)
                ap=[p for p in self.region_points(actor,'hands',side) if (p-wrist).length<.105]
                if not hp or not ap:raise ValueError('Post-target surface patch missing')
                tree=KDTree(len(hp))
                for i,p in enumerate(hp):tree.insert(p,i)
                tree.balance()
                dists=sorted(tree.find(p)[2] for p in ap)
                result['palm_to_hip_surface_gap_m']=round(dists[0],6)
                result['palm_patch_p25_distance_m']=round(dists[int(.25*(len(dists)-1))],6)
                result['hand_mesh_vertices_sampled']=len(ap)
                result['hip_mesh_vertices_sampled']=len(hp)
                result['converged']=result['palm_to_hip_surface_gap_m']<=target_gap+.010
            except Exception as exc:
                result['reason']=f'{type(exc).__name__}: {exc}'
            out['sides'][side]=result
        return out

    def side_head_clearance(self,actor='B',side='L'):
        try:return {'actor':actor,'side':side,'z_m':round(self.min_z(actor,'head_side',side),6),
                    'method':'VP001_head_neck_material_side_patch_near_head_bone',
                    'anatomy_precision':'approximate_side_of_head_not_exact_cheek'}
        except Exception as exc:return {'actor':actor,'side':side,'error':str(exc)}

    def knee_angle_deg(self,actor,side):
        # Included angle at the knee; 180 is an almost straight leg.
        hip=self.head(actor,'DEF-thigh.'+side)
        knee=self.head(actor,'DEF-shin.'+side)
        ankle=self.head(actor,'DEF-foot.'+side)
        u=hip-knee;v=ankle-knee
        if min(u.length,v.length)<.001:return None
        return math.degrees(u.angle(v))

    def heights(self):
        return {a:{'hip_z_m':round(self.head(a,'hips').z,5),
                   'knee_L_z_m':round(self.head(a,'DEF-shin.L').z,5),
                   'knee_R_z_m':round(self.head(a,'DEF-shin.R').z,5),
                   'knee_L_angle_deg':round(self.knee_angle_deg(a,'L'),2) if self.knee_angle_deg(a,'L') is not None else None,
                   'knee_R_angle_deg':round(self.knee_angle_deg(a,'R'),2) if self.knee_angle_deg(a,'R') is not None else None,
                   'head_z_m':round(self.head(a,'head').z,5)} for a in ('A','B')}
