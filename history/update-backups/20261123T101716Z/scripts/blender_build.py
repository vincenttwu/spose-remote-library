"""Blender-side data-only pose builder; designed for Blender 5.2.2 LTS.
No source ZIP scripts are loaded, no automatic anatomical pose solver is claimed.
"""
import argparse,json,math,sys,traceback
from pathlib import Path
import bpy
from mathutils import Vector

SCRIPTS=Path(__file__).resolve().parent
sys.path.insert(0,str(SCRIPTS))
from render_previews import render_views
from validate_pose import measure_contact

def read_json(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save_json(p,obj):Path(p).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

def apply_control(item):
    actor=item['actor'];space=item['space'];val=Vector(item['value'])
    if actor not in ('A','B'):raise ValueError('Unknown actor')
    if space.startswith('OBJECT_'):
        obj=bpy.data.objects.get(f'CPL01_{actor}_ROOT')
        if not obj:raise ValueError(f'Missing actor root for {actor}')
        if space=='OBJECT_WORLD_LOCATION_M':
            obj.matrix_world.translation=val
        elif space=='OBJECT_WORLD_ROTATION_DEG':
            obj.rotation_mode='XYZ'
            obj.rotation_euler=tuple(math.radians(v) for v in val)
        else:raise ValueError(f'Unsupported object control: {space}')
    else:
        rig=bpy.data.objects.get(f'CPL01_{actor}_RIG')
        if not rig or rig.type!='ARMATURE':raise ValueError(f'Missing actor armature {actor}')
        bone=rig.pose.bones.get(item['bone'])
        if bone is None:raise ValueError(f'Unknown pose bone: {actor}/{item["bone"]}')
        if space=='POSE_LOCAL_ROTATION_DEG':
            bone.rotation_mode='XYZ';bone.rotation_euler=tuple(math.radians(v) for v in val)
        elif space=='POSE_WORLD_HEAD_M':
            # Adapted from the existing pilot's measured control target approach.
            matrix=bone.matrix.copy();matrix.translation=rig.matrix_world.inverted() @ val
            bone.matrix=matrix
        else:raise ValueError(f'Unsupported pose control {space}')
    bpy.context.view_layer.update()

def main(settings_path):
    cfg=read_json(settings_path);out=Path(cfg['output'])
    template=Path(cfg['template_file'])
    if not template.exists():template=Path(cfg['fallback_template'])
    if not template.is_file():raise FileNotFoundError('Missing pair template')
    bpy.ops.wm.open_mainfile(filepath=str(template),use_scripts=False)
    bpy.context.preferences.filepaths.save_version=0
    payload=read_json(out/'inputs'/'rig-targets.json')
    contacts=read_json(out/'inputs'/'contacts.json')
    for item in payload['controls']:apply_control(item)
    checks={'pair_objects_present':all(bpy.data.objects.get(f'CPL01_{a}_{kind}') is not None for a in ('A','B') for kind in ('ROOT','RIG','BODY')),
       'applied_control_count':len(payload['controls']),'character_proportion_edits':'NONE_REQUESTED',
       'rig_runtime_version':bpy.app.version_string,'approval':'NOT_REVIEWED'}
    if not checks['pair_objects_present']:raise ValueError('Pair scene missing expected objects')
    contacts_result=measure_contact(bpy,contacts)
    previews=render_views(bpy,out/'previews',cfg.get('render_config'))
    if cfg.get('save_blend'):
        bpy.ops.wm.save_as_mainfile(filepath=str(out/'scene.blend'),compress=True)
    save_json(out/'blender-result.json',{'rendered':True,'template':str(template),'checks':checks,'contact_checks':contacts_result,
       'previews':sorted(previews),'issues':[]})

def cli():
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    pa=argparse.ArgumentParser();pa.add_argument('--settings',required=True)
    ns=pa.parse_args(args)
    try:main(ns.settings)
    except Exception as e:
        traceback.print_exc()
        try:save_json(Path(read_json(ns.settings)['output'])/'blender-result.json',{'rendered':False,'error':str(e)})
        except Exception:pass
        raise
if __name__=='__main__':cli()
