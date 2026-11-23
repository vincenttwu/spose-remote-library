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

    def _hand_contact_patch(self, actor, side):
        """Select a wrist/palm patch adaptively, never mistake a finger tip for a palm.

        The VP001 material labels the whole hand. Some wrist handles are over
        10.5 cm from the deformed palm (notably DOWN/FCDN). The old fixed-radius
        probe silently failed there, or found a single tangential vertex.
        Adaptive patches report their localization radius and confidence.
        """
        all_hand=self.region_points(actor,'hands',side)
        wrist=self.head(actor,'hand_ik.'+side)
        defhand=self.head(actor,'DEF-hand.'+side)
        # Prefer the actual DEF hand joint (the control may be offset by Rigify).
        center=defhand if (defhand-wrist).length<.38 else wrist
        for radius in (.10,.14,.19,.25):
            patch=[p for p in all_hand if (p-center).length<radius]
            if len(patch)>=20:
                # Exclude the farthest quarter; fingertips dominate min-distance.
                patch=sorted(patch,key=lambda p:(p-center).length)
                return patch[:max(20,int(len(patch)*.75))],radius,'def-hand proximity'
        # A low-confidence fallback is measurable, never falsely "converged".
        if len(all_hand)<12:raise ValueError('Insufficient side-specific hand-region vertices')
        ranked=sorted(all_hand,key=lambda p:(p-center).length)
        return ranked[:max(12,int(len(ranked)*.35))],None,'fallback closest 35% of hand material'

    def _hip_contact_patch(self,actor,side):
        hip=self.head(actor,'hips')
        pts=[p for p in self.region_points(actor,'pelvis',side)
             if abs(p.z-hip.z)<.23 and abs(p.y-hip.y)<.30]
        if len(pts)<12:raise ValueError('Pelvis side material patch missing')
        pts.sort(key=lambda p:p.x,reverse=(side=='L'))
        return pts[:max(15,int(len(pts)*.34))]

    def _percentiles(self,values):
        if not values:return {}
        s=sorted(values)
        def q(f):return round(s[int(f*(len(s)-1))],6)
        return {'p10_m':q(.10),'p25_m':q(.25),'p50_m':q(.50),
                'p75_m':q(.75),'p90_m':q(.90),
                'within_15mm_fraction':round(sum(d<=.015 for d in s)/len(s),4),
                'within_30mm_fraction':round(sum(d<=.030 for d in s)/len(s),4),
                'min_m':round(s[0],6)}

    def palm_to_hip_surface(self,plan):
        """Aim the PALM PATCH centroid at lateral hip; assess area coverage.

        This is a bounded heuristic (not force/penetration). A near-zero nearest
        vertex is NOT success; p50 and area coverage reveal detached palms.
        """
        from mathutils.kdtree import KDTree
        if not plan:return {'enabled':False,'reason':'No palm surface plan'}
        actor=plan.get('actor','A');target=plan.get('target_actor','B')
        max_total=min(.25,max(.02,float(plan.get('max_translation_m',.16))))
        gap=float(plan.get('target_gap_m',.012))
        out={'enabled':True,'method':'v4_palm_patch_centroid_to_lateral_pelvis',
             'target_gap_m':gap,'sides':{},
             'warning':'Unsigned mesh distances; visual placement and penetration still require inspection.'}
        for side in ('L','R'):
            r={'side':side,'converged':False,'contact_target_valid':False,
               'translation_m':0.,'iteration_gap_m':[]}
            used=0.0
            try:
                for iteration in range(min(6,max(1,int(plan.get('iterations',5))))):
                    hp=self._hip_contact_patch(target,side)
                    palm,radius,patch_method=self._hand_contact_patch(actor,side)
                    r['hand_patch_radius_m']=radius
                    r['hand_patch_method']=patch_method
                    r['hand_mesh_vertices_sampled']=len(palm)
                    r['hip_mesh_vertices_sampled']=len(hp)
                    center=sum(palm,Vector((0,0,0)))/len(palm)
                    # Pick a short band of hip surface nearest the palm in Y/Z.
                    n=max(12,min(len(hp),int(.20*len(hp))))
                    site_subset=sorted(hp,key=lambda p:(p.y-center.y)**2+(p.z-center.z)**2)[:n]
                    site=sum(site_subset,Vector((0,0,0)))/len(site_subset)
                    outward=Vector((1,0,0)) if side=='L' else Vector((-1,0,0))
                    goal=site+outward*gap
                    delta=goal-center
                    dist=delta.length
                    r['iteration_gap_m'].append(round(dist,6))
                    r['contact_target_valid']=True
                    if dist<.008:break
                    step=min(.050,dist,max_total-used)
                    if step<.0001:break
                    handle='hand_ik.'+side
                    self.point(actor,handle,self.head(actor,handle)+delta.normalized()*step)
                    used+=step
                r['translation_m']=round(used,6)
                hp=self._hip_contact_patch(target,side)
                palm,radius,patch_method=self._hand_contact_patch(actor,side)
                tree=KDTree(len(hp))
                for i,v in enumerate(hp):tree.insert(v,i)
                tree.balance()
                data=self._percentiles([tree.find(v)[2] for v in palm])
                r['surface_distribution']=data
                r['palm_to_hip_surface_gap_m']=data['min_m']
                r['palm_patch_p25_distance_m']=data['p25_m']
                r['palm_patch_p50_distance_m']=data['p50_m']
                r['palm_patch_p75_distance_m']=data['p75_m']
                r['contact_coverage_30mm']=data['within_30mm_fraction']
                r['hand_patch_method']=patch_method
                r['hand_patch_radius_m']=radius
                r['converged']=bool(data['p50_m']<=.032 and data['within_30mm_fraction']>=.45 and radius is not None)
                r['confidence']='partial' if radius is None else 'region_approximation'
            except Exception as exc:
                r['reason']=f'{type(exc).__name__}: {exc}'
            out['sides'][side]=r
        return out

    def head_gaze(self, actor='B'):
        """Estimate head-forward direction from Rigify REST->POSE delta.

        Forward -Y is from RIG001. It is not an eye tracker; output explicitly
        identifies it as rig orientation proxy. X pitch is world elevation.
        """
        bone=self.bone(actor,'head')
        rig=self.rigs[actor]
        rest=bone.bone.matrix_local.to_3x3()
        posed=bone.matrix.to_3x3()
        v=(rig.matrix_world.to_3x3() @ posed @ rest.inverted() @ Vector((0,-1,0))).normalized()
        horiz=max(.0001,math.hypot(v.x,v.y))
        return {'vector_world':[round(x,6) for x in v],
                'elevation_deg':round(math.degrees(math.atan2(v.z,horiz)),3),
                'forward_dot_minus_y':round(-v.y,5),
                'method':'RIG001_forward_-Y_rest_to_pose_delta_estimate'}

    def aim_head(self, config):
        """Measure both signs of local X rotation, choose target head direction.

        No blind sign assumption: compare evaluated head control response while
        preserving the current style rotation (including FCDN side-roll).
        """
        if not config:return {'enabled':False}
        actor=config.get('actor','B')
        target=float(config.get('target_elevation_deg',10.))
        limit=min(75.,max(10.,float(config.get('max_delta_deg',65.))))
        axis=Vector((1,0,0))
        head=self.bone(actor,'head')
        head.rotation_mode='QUATERNION'
        prior=head.rotation_quaternion.copy()
        local_axis=head.bone.matrix_local.to_3x3().inverted() @ axis
        before=self.head_gaze(actor)
        candidates=[]
        for delta in (-limit,-limit*.75,-limit*.5,-limit*.25,0.,limit*.25,limit*.5,limit*.75,limit):
            head.rotation_quaternion=Quaternion(local_axis,math.radians(delta)) @ prior
            self.update()
            g=self.head_gaze(actor)
            # Additional penalty for looking backward rather than along -Y.
            score=abs(g['elevation_deg']-target) + max(0.,-g['forward_dot_minus_y'])*16. + abs(delta)*.015
            candidates.append((score,delta,g))
        best=min(candidates,key=lambda c:c[0])
        head.rotation_quaternion=Quaternion(local_axis,math.radians(best[1])) @ prior
        self.update()
        after=self.head_gaze(actor)
        return {'enabled':True,'actor':actor,'requested_elevation_deg':target,
                'sampled_delta_x_deg':round(best[1],3), 'before':before,'after':after,
                'candidate_count':len(candidates),'achieved':abs(after['elevation_deg']-target)<12.,
                'warning':'Rest-to-pose head proxy, not measured true eyeball or cheek direction'}

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
