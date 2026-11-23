"""Run with Blender --background --factory-startup --disable-autoexec --python this_file."""
import bpy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
profile = json.loads((ROOT/'body_profiles/BP001/v001/profile.json').read_text(encoding='utf-8'))
source = Path(profile['source_rig'])
bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)

def driver_info(id_block):
    data = id_block.animation_data
    return [] if not data else [{'path': d.data_path, 'index': d.array_index, 'expression': d.driver.expression,
        'valid': d.is_valid, 'variables': [{'name': v.name, 'type': v.type, 'targets': [
            {'id': t.id.name if t.id else None, 'data_path': t.data_path,
             'bone_target': t.bone_target, 'transform_type': t.transform_type, 'transform_space': t.transform_space}
            for t in v.targets]} for v in d.driver.variables]} for d in data.drivers]

def safe_props(block):
    return {k: repr(block[k]) for k in block.keys() if k != '_RNA_UI'}

objects=[]
for obj in bpy.data.objects:
    item={'name':obj.name,'type':obj.type,'parent':obj.parent.name if obj.parent else None,
          'location':list(obj.location),'scale':list(obj.scale),'rotation':list(obj.rotation_euler),
          'dimensions':list(obj.dimensions),'hidden_render':obj.hide_render,
          'hidden_viewport':obj.hide_viewport,'hide_get':obj.hide_get(),
          'collections':[c.name for c in obj.users_collection], 'drivers':driver_info(obj),
          'props':safe_props(obj)}
    if obj.type=='MESH':
        item['vertices']=len(obj.data.vertices)
        item['modifiers']=[{'name':m.name,'type':m.type,'object':getattr(getattr(m,'object',None),'name',None),
            'show_viewport':m.show_viewport,'show_render':m.show_render} for m in obj.modifiers]
        if obj.data.shape_keys:
            item['shape_keys']=[{'name':k.name,'value':k.value,'min':k.slider_min,'max':k.slider_max} for k in obj.data.shape_keys.key_blocks]
            item['shape_drivers']=driver_info(obj.data.shape_keys)
    if obj.type=='ARMATURE':
        item['data_props']=safe_props(obj.data)
        item['bones']=[{'name':b.name,'parent':b.parent.name if b.parent else None,'rotation_mode':b.rotation_mode,
             'location':list(b.location),'rotation_euler':list(b.rotation_euler),'rotation_quaternion':list(b.rotation_quaternion),
             'scale':list(b.scale),'head':list(b.head),'tail':list(b.tail),
             'lock_location':list(b.lock_location),'lock_rotation':list(b.lock_rotation),
             'props':safe_props(b),'custom_shape':b.custom_shape.name if b.custom_shape else None,
             'constraints':[{'name':c.name,'type':c.type,'influence':c.influence,
                 'target':getattr(getattr(c,'target',None),'name',None),'subtarget':getattr(c,'subtarget',None),
                 'pole_target':getattr(getattr(c,'pole_target',None),'name',None),
                 'pole_subtarget':getattr(c,'pole_subtarget',None)} for c in b.constraints]} for b in obj.pose.bones]
    objects.append(item)
result={'schema_version':1,'status':'inspected_not_control_tested','blender_version':bpy.app.version_string,
        'source_path':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'scene':{'unit_scale':bpy.context.scene.unit_settings.scale_length,'engine':bpy.context.scene.render.engine,
            'frame':bpy.context.scene.frame_current},
        'collections':[{'name':c.name,'objects':[o.name for o in c.objects]} for c in bpy.data.collections],
        'texts':[{'name':t.name,'length':len(t.as_string()),'use_module':t.use_module} for t in bpy.data.texts],
        'objects':objects}
out=ROOT/'tooling/rig-maps/RIG001-inspection-v001.json'
out.write_text(json.dumps(result,indent=2),encoding='utf-8')
print('INSPECTION_SAVED',out)
print(json.dumps({'armatures':[{ 'name':i['name'],'bones':len(i['bones']),'props':i['props'],'data_props':i['data_props']} for i in objects if i['type']=='ARMATURE'],
    'meshes':[{ 'name':i['name'],'dimensions':i['dimensions'],'vertices':i['vertices'],'modifiers':i['modifiers'], 'keys':[k['name'] for k in i.get('shape_keys',[])]} for i in objects if i['type']=='MESH' and (i['vertices']>500 or i.get('shape_keys'))],
    'texts':result['texts']},indent=2))
