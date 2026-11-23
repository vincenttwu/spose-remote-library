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
    # Pass-03: spine/head styling follows trunk and knee support, with a bounded
    # floor recheck. Style controls are declarative; no executable pose code.
    for item in controls.get('styling_controls',[]):engine.apply(item)
    if controls.get('post_styling_calibration'):
        engine.calibrate_floor(controls['post_styling_calibration'])
    pelvic_alignment=engine.align_pelvic_surfaces(controls.get('pelvic_alignment'))
    for item in ordered:
        if item['space']=='POSE_RELATIVE_BONE_HEAD_HAND':engine.apply(item)
    # Real evaluated-mesh palm/hip measurements; no world-bone proxy as target.
    surface_contact=engine.palm_to_hip_surface(controls.get('palm_surface_contact'))
    head_side=engine.side_head_clearance('B',controls.get('head_side_floor',{}).get('side','L')) if controls.get('head_side_floor') else None
    contact_result=measure_contact(bpy,contacts)
    contact_result['palm_surface_contact']=surface_contact
    if head_side:contact_result['head_side_near_floor']=head_side
    checked=validate_geometry(engine,controls,calibration,contact_result)
    checked['diagnostics']['pelvic_alignment']=pelvic_alignment
    checked['diagnostics']['palm_surface_contact']=surface_contact
    if head_side:checked['diagnostics']['head_side_near_floor']=head_side
    if pelvic_alignment.get('applied') and pelvic_alignment.get('closest_pelvis_distance_m',0)>.09:
        checked['issues'].append({'code':'PELVIC_SURFACE_GAP','detail':'Pelvis mesh gap remained above 9cm after bounded approach'})
        checked['hard_gate_pass']=False
    # These are diagnostics only; contact, posture, and quality NEVER stop builds.
    for side,reading in surface_contact.get('sides',{}).items():
        gap=reading.get('palm_to_hip_surface_gap_m')
        if gap is None:checked['issues'].append({'code':'PALM_HIP_REGION_NOT_MEASURABLE','detail':f'{side}: {reading.get("reason")}'})
        elif gap>.025:checked['issues'].append({'code':'PALM_HIP_SURFACE_GAP','detail':f'{side}: surface gap {gap:.3f}m (>0.025m diagnostic) '})
    if head_side and head_side.get('z_m',0)>.055:
        checked['issues'].append({'code':'HEAD_SIDE_ABOVE_FLOOR','detail':f'head-side surface z={head_side["z_m"]:.3f}m'})
    checked['hard_gate_pass']=not checked['issues']  # legacy output field, NOT a gate
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
