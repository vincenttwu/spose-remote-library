"""Blender 5.2.2 V00 rig builder. Replaces flawed local-rotation-only Batch 001.

Reads declarative rig-targets.json via full remote library's own import pipeline.
No code is executed from incoming ZIPs. See docs/GEOMETRY-ENGINE-V2.md.
"""
import argparse,json,sys,traceback
from pathlib import Path
import bpy
SCRIPTS=Path(__file__).resolve().parent
sys.path.insert(0,str(SCRIPTS))
from rigify_floor_engine import RigifyFloorEngine
from render_previews import render_views
from validate_pose import measure_contact,validate_geometry

def read_json(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save_json(p,value):Path(p).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main(settings):
    cfg=read_json(settings);out=Path(cfg['output'])
    primary=Path(cfg['template_file']);fallback=Path(cfg['fallback_template'])
    template=primary if primary.is_file() else fallback
    if not template.is_file():raise FileNotFoundError('Shared CPL01 template missing')
    bpy.ops.wm.open_mainfile(filepath=str(template),use_scripts=False)
    bpy.context.preferences.filepaths.save_version=0
    controls=read_json(out/'inputs'/'rig-targets.json')
    contacts=read_json(out/'inputs'/'contacts.json')
    if controls.get('engine')!='rigify_floor_v2':
        raise ValueError('Legacy standing-risk package rejected: missing rigify_floor_v2 geometry contract')
    engine=RigifyFloorEngine(bpy);engine.initialize()
    ordered=controls['controls']
    # Root reset -> torso world placement -> foot & pole IK -> hand IK -> head/neck
    # relative contacts only after floor calibration, so hand placement follows
    # the actual constrained pose rather than a guessed hip location.
    for item in ordered:
        if item['space']!='POSE_RELATIVE_BONE_HEAD_HAND':engine.apply(item)
    calibration=engine.calibrate_floor(controls.get('floor_calibration',[]))
    pelvic_alignment=engine.align_pelvic_surfaces(controls.get('pelvic_alignment'))
    for item in ordered:
        if item['space']=='POSE_RELATIVE_BONE_HEAD_HAND':engine.apply(item)
    contact_result=measure_contact(bpy,contacts)
    checked=validate_geometry(engine,controls,calibration,contact_result)
    checked['diagnostics']['pelvic_alignment']=pelvic_alignment
    if pelvic_alignment.get('applied') and pelvic_alignment.get('closest_pelvis_distance_m',0)>.09:
        checked['issues'].append({'code':'PELVIC_SURFACE_GAP','detail':'Pelvis mesh gap remained above 9cm after bounded approach'})
        checked['hard_gate_pass']=False
    checks={'pair_objects_present':all(bpy.data.objects.get(f'CPL01_{a}_{kind}') for a in ('A','B') for kind in ('ROOT','RIG','BODY')),
            'rig_runtime_version':bpy.app.version_string,
            'engine':'rigify_floor_v2','applied_control_count':len(engine.applied),
            'floor_calibration':calibration,'posture_heights':engine.heights(),
            'geometry':checked['diagnostics'],'hard_gate_pass':checked['hard_gate_pass'],
            'approval':'NOT_REVIEWED'}
    # Render failed candidates so the operator can diagnose them visually; never
    # hide failures just because a nice looking image was produced.
    previews=render_views(bpy,out/'previews',cfg.get('render_config'))
    if cfg.get('save_blend'):
        bpy.ops.wm.save_as_mainfile(filepath=str(out/'scene.blend'),compress=True)
    save_json(out/'blender-result.json',{'rendered':True,'template':str(template),'checks':checks,
                                      'contact_checks':contact_result,
                                      'previews':sorted(previews),
                                      'issues':checked['issues']})

def cli():
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    p=argparse.ArgumentParser();p.add_argument('--settings',required=True)
    ns=p.parse_args(args)
    try:main(ns.settings)
    except Exception as exc:
        traceback.print_exc()
        try:save_json(Path(read_json(ns.settings)['output'])/'blender-result.json',{'rendered':False,'error':str(exc),'issues':[{'code':'BUILDER_EXCEPTION','detail':str(exc)}]})
        except Exception:pass
        raise
if __name__=='__main__':cli()
