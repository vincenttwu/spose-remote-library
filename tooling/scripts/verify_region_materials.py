"""Verify the saved VP001 appearance study and native slider behavior in Blender."""
import bpy,sys,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from character_common import ROOT,evaluated_points,write_json
study=ROOT/'pairs/CPL01/v001/studies/VP001-v001'
asset=study/'appearance-study.blend'
bpy.ops.wm.open_mainfile(filepath=str(asset),use_scripts=False)
results={}
for actor in ['A','B']:
    body=bpy.data.objects[f'CPL01_{actor}_BODY']
    menu=bpy.data.objects[f'CPL01_{actor}_SHAPES']
    other=bpy.data.objects[f'CPL01_{"B" if actor=="A" else "A"}_BODY']
    positions=evaluated_points(body)
    assert len(body.data.materials)==11
    assert len({p.material_index for p in body.data.polygons})==11
    for mat in body.data.materials:
        assert mat['actor']==actor and mat['visual_profile']=='VP001/v001'
        assert len(mat.node_tree.animation_data.drivers)==1
        d=mat.node_tree.animation_data.drivers[0]
        assert d.driver.variables[0].targets[0].id==menu
        assert d.is_valid
    factors=[]
    other_before=[m.node_tree.nodes['Region_Overlay'].inputs[0].default_value for m in other.data.materials]
    for value,expected in [(0.,0.),(.135,.5),(.27,1.)]:
        menu.pose.bones['muscle group control'].location.x=value
        menu.update_tag();bpy.context.view_layer.update()
        current=[m.node_tree.nodes['Region_Overlay'].inputs[0].default_value for m in body.data.materials]
        assert all(abs(f-expected)<1e-5 for f in current),(actor,value,current)
        assert other_before==[m.node_tree.nodes['Region_Overlay'].inputs[0].default_value for m in other.data.materials]
        assert max((a-b).length for a,b in zip(positions,evaluated_points(body)))<1e-7
        factors.append({'slider_x':value,'blend_factor':expected})
    results[actor]={'regions':11,'all_regions_assigned':True,'palette_targets_correct_actor':True,
        'independent_color_control':True,'geometry_unchanged':True,'slider_samples':factors}
report={'schema_version':1,'result':'technical_checks_passed_pending_palette_review','asset_sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),
    'blender_version':bpy.app.version_string,'actors':results,'main_pair_template_changed':False}
write_json(study/'appearance-validation.json',report)
print('APPEARANCE_VERIFICATION_PASSED',json.dumps(report))
