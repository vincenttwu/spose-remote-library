"""Reopen a saved draft in background Blender and verify geometry and rig isolation.

Use -- master or -- pair after Blender's --python argument.
"""
import bpy,sys,json,hashlib
from pathlib import Path
from mathutils import Quaternion
sys.path.insert(0,str(Path(__file__).resolve().parent))
from character_common import ROOT,bounds,evaluated_points,write_json
kind=sys.argv[sys.argv.index('--')+1]
assert kind in ['master','pair']
folder=ROOT/('body_profiles/BP001/v001' if kind=='master' else 'pairs/CPL01/v001')
asset=folder/('master.blend' if kind=='master' else 'template.blend')
bpy.ops.wm.open_mainfile(filepath=str(asset),use_scripts=False)
ui=bpy.data.texts.get('rig.004_ui.py')
ui_status={'present':ui is not None,'registered':False}
if ui:
    exec(compile(ui.as_string(),ui.name,'exec'),{'__name__':'__rigify_ui__'})
    ui_status['registered']=True
assert not list(bpy.data.libraries),'Linked external Blender data found'
missing=[i.filepath for i in bpy.data.images if i.source=='FILE' and not i.packed_file and not Path(bpy.path.abspath(i.filepath)).is_file()]
assert not missing,missing
prefixes=['BP001'] if kind=='master' else ['CPL01_A','CPL01_B']
targets=[1.85] if kind=='master' else [1.85,1.77]
measurements={}
for prefix,target in zip(prefixes,targets):
    body=bpy.data.objects[prefix+'_BODY'];rig=bpy.data.objects[prefix+'_RIG']
    assert len(rig.pose.bones)==406
    box=bounds(body);assert abs(box['dimensions'][2]-target)<1e-4
    assert abs(box['min'][2])<1e-4
    assert next(m for m in body.modifiers if m.type=='ARMATURE').object==rig
    shape_keys=body.data.shape_keys
    assert shape_keys and shape_keys.key_blocks['BP001_TorsoTaper'].value==1.0
    invalid=[d.data_path for block in [rig,shape_keys] if block.animation_data for d in block.animation_data.drivers if not d.is_valid]
    assert not invalid,invalid
    original=evaluated_points(body);b=rig.pose.bones['head'];saved=b.matrix_basis.copy()
    b.rotation_quaternion=b.rotation_quaternion @ Quaternion((1,0,0),.08)
    rig.update_tag();bpy.context.view_layer.update()
    delta=max((a-b).length for a,b in zip(original,evaluated_points(body)))
    b.matrix_basis=saved;rig.update_tag();bpy.context.view_layer.update()
    assert delta>1e-5
    measurements[prefix]={'bounds_m':box,'height_m':box['dimensions'][2],'bone_count':406,
        'head_control_displacement_m':delta,'invalid_drivers':invalid}

pair_tests={}
if kind=='pair':
    a=bpy.data.objects['CPL01_A_BODY'];b=bpy.data.objects['CPL01_B_BODY']
    ra=bpy.data.objects['CPL01_A_ROOT'];rb=bpy.data.objects['CPL01_B_ROOT']
    pa=[ra.matrix_world.inverted() @ v for v in evaluated_points(a)]
    pb=[rb.matrix_world.inverted() @ v for v in evaluated_points(b)]
    assert len(pa)==len(pb)
    error=max((v-w).length for v,w in zip(pa,pb))
    assert error<1e-5,error
    pair_tests['normalized_geometry_max_error']=error
    assert a.data!=b.data and a.data.shape_keys!=b.data.shape_keys
    pair_tests['independent_mesh_and_shape_keys']=True
    shape_results=[]
    for actor,own,other in [('A',a,b),('B',b,a)]:
        menu=bpy.data.objects[f'CPL01_{actor}_SHAPES']
        before=evaluated_points(other);before_own=evaluated_points(own)
        control=menu.pose.bones['arms control'];old=control.location.x
        control.location.x+=.002;menu.update_tag();bpy.context.view_layer.update()
        other_error=max((v-w).length for v,w in zip(before,evaluated_points(other)))
        own_delta=max((v-w).length for v,w in zip(before_own,evaluated_points(own)))
        control.location.x=old;menu.update_tag();bpy.context.view_layer.update()
        assert other_error<1e-7 and own_delta>1e-5,(actor,other_error,own_delta)
        shape_results.append({'actor':actor,'other_delta_m':other_error,'own_delta_m':own_delta,'passed':True})
    pair_tests['shape_slider_independence']=shape_results
    # Inspect all object-target references in each actor's drivers, modifiers, and constraints.
    for actor in ['A','B']:
        opposite='CPL01_'+('B' if actor=='A' else 'A')+'_'
        objects=[o for o in bpy.data.objects if o.name.startswith('CPL01_'+actor+'_')]
        for obj in objects:
            blocks=[obj,obj.data,getattr(obj.data,'shape_keys',None)]
            for block in blocks:
                if block is not None and getattr(block,'animation_data',None):
                    for driver in block.animation_data.drivers:
                        for var in driver.driver.variables:
                            for target in var.targets:
                                assert not target.id or not target.id.name.startswith(opposite),(obj.name,driver.data_path)
            constraints=list(obj.constraints)
            if obj.type=='ARMATURE':
                for bone in obj.pose.bones:constraints.extend(bone.constraints)
            for constraint in constraints:
                for prop in ['target','pole_target','space_object']:
                    target=getattr(constraint,prop,None)
                    assert not target or not target.name.startswith(opposite),(obj.name,constraint.name)
                for entry in getattr(constraint,'targets',[]):
                    assert not entry.target or not entry.target.name.startswith(opposite)
    pair_tests['no_cross_actor_driver_or_constraint_targets']=True

result={'schema_version':1,'result':'technical_checks_passed_pending_user_review',
    'asset':asset.name,'asset_sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),
    'blender_version':bpy.app.version_string,'reopened':True,'self_contained':True,
    'missing_files':missing,'ui':ui_status,'actors':measurements,'pair_tests':pair_tests,
    'visual_review':'pending_user_review','limitations':['Basic control and geometry checks; animation and all individual controls are not exhaustively validated.']}
write_json(folder/'validation.json',result)
print('CHARACTER_VERIFICATION_PASSED',json.dumps(result))
