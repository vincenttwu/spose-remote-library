"""Create a separate appearance study; leave the character masters and pair template unchanged."""
import bpy,sys,json,hashlib
import argparse
from pathlib import Path
from collections import Counter,defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parent))
from character_common import ROOT,evaluated_points,render,write_json
visual=json.loads((ROOT/'visual_profiles/VP001/v001/visual.json').read_text(encoding='utf-8'))
pair_dir=ROOT/'pairs/CPL01/v001'
source=pair_dir/'template.blend'
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
study=pair_dir/'studies/VP001-v001';study.mkdir(parents=True,exist_ok=True)
assert '--replace-study' in sys.argv or not (study/'appearance-study.blend').exists(),'Study already exists; use --replace-study deliberately'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)

def linear(hexcode):
    vals=[int(hexcode[i:i+2],16)/255 for i in (1,3,5)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in vals)

def region(group):
    if group.startswith(('DEF-foot','DEF-toe')):return 'feet'
    if group.startswith(('DEF-hand','DEF-palm','DEF-f_','DEF-thumb')):return 'hands'
    if group.startswith('DEF-forearm'):return 'forearms'
    if group.startswith('DEF-upper_arm'):return 'upper_arms'
    if group.startswith('DEF-shoulder'):return 'shoulders'
    if group.startswith('DEF-thigh'):return 'thighs'
    if group.startswith('DEF-shin'):return 'calves'
    if group in ['DEF-spine.004','DEF-spine.005','DEF-spine.006']:return 'head_neck'
    if group.startswith('DEF-breast') or group in ['DEF-spine.002','DEF-spine.003','trapezius']:return 'chest_back'
    if group=='DEF-spine.001':return 'abdomen'
    if group=='DEF-spine' or group.startswith('DEF-pelvis'):return 'pelvis'
    return None

def create_material(actor,role,menu):
    palette=visual['actor_palettes'][actor]
    mat=bpy.data.materials.new(f'VP001_{actor}_{role}')
    mat.use_nodes=True
    mat.diffuse_color=(*linear(palette['regions'][role]),1)
    mat['visual_profile']='VP001/v001';mat['actor']=actor;mat['region']=role
    tree=mat.node_tree
    shader=next(n for n in tree.nodes if n.type=='BSDF_PRINCIPLED')
    shader.inputs['Roughness'].default_value=.72
    mix=tree.nodes.new('ShaderNodeMixRGB');mix.name='Region_Overlay';mix.blend_type='MIX'
    mix.inputs[1].default_value=(*linear(palette['base_srgb_hex']),1)
    mix.inputs[2].default_value=(*linear(palette['regions'][role]),1)
    fc=mix.inputs[0].driver_add('default_value')
    fc.driver.expression=visual['control']['factor_expression']
    var=fc.driver.variables.new();var.name='overlay';var.type='SINGLE_PROP'
    var.targets[0].id=menu
    var.targets[0].data_path='pose.bones["muscle group control"].location[0]'
    tree.links.new(mix.outputs['Color'],shader.inputs['Base Color'])
    return mat

stats={};assignments={};geometry_before={}
for actor in ['A','B']:
    body=bpy.data.objects[f'CPL01_{actor}_BODY'];menu=bpy.data.objects[f'CPL01_{actor}_SHAPES']
    geometry_before[actor]=evaluated_points(body)
    names={g.index:g.name for g in body.vertex_groups}
    roles=list(visual['actor_palettes'][actor]['regions'])
    body.data.materials.clear()
    for role in roles:body.data.materials.append(create_material(actor,role,menu))
    # Classify whole disconnected mannequin pieces to avoid jagged weight-boundary stripes.
    parents=list(range(len(body.data.vertices)))
    def find(i):
        while parents[i]!=i:
            parents[i]=parents[parents[i]];i=parents[i]
        return i
    for edge in body.data.edges:
        x,y=edge.vertices;parents[find(x)]=find(y)
    component_weights=defaultdict(lambda:defaultdict(float))
    component_vertices=defaultdict(list)
    for vertex in body.data.vertices:
        component=find(vertex.index);component_vertices[component].append(vertex.co)
        for g in vertex.groups:
            r=region(names[g.group])
            if r:component_weights[component][r]+=g.weight
    component_roles={c:max(w,key=w.get) for c,w in component_weights.items()}
    for c,points in component_vertices.items():
        if c not in component_roles:continue
        center=sum((v.z for v in points))/len(points)
        length=max(v.x for v in points)-min(v.x for v in points)
        if component_roles[c]=='upper_arms' and center>1.22 and length<.14:component_roles[c]='shoulders'
    regions=[]
    for poly in body.data.polygons:
        chosen=component_roles[find(poly.vertices[0])]
        poly.material_index=roles.index(chosen);regions.append(chosen)
    assignments[actor]=regions
    stats[actor]=dict(Counter(regions))
    body['visual_profile']='VP001/v001';body['palette_id']=visual['actor_palettes'][actor]['palette_id']
    menu.pose.bones['muscle group control'].location.x=.27
    menu.update_tag()
assert assignments['A']==assignments['B']
bpy.context.view_layer.update()
for actor in ['A','B']:
    after=evaluated_points(bpy.data.objects[f'CPL01_{actor}_BODY'])
    assert max((a-b).length for a,b in zip(geometry_before[actor],after))<1e-7

scene=bpy.context.scene;scene['visual_profile']='VP001/v001';scene['review_status']='appearance_proposal'
scene['appearance_mode']='regions';scene.camera=bpy.data.objects['CAM_Front']
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(study/'appearance-study.blend'),check_existing=False)
for label,cam in [('regions-front','CAM_Front'),('regions-three-quarter','CAM_ThreeQuarter')]:render(study/f'{label}.png',cam)
for actor in ['A','B']:
    menu=bpy.data.objects[f'CPL01_{actor}_SHAPES'];menu.pose.bones['muscle group control'].location.x=0.;menu.update_tag()
bpy.context.view_layer.update();render(study/'plain-front.png','CAM_Front')
write_json(study/'study.json',{'schema_version':1,'visual_profile':'VP001/v001','status':'proposed_pending_review',
    'source_template_sha256':source_hash,'geometry_unchanged':True,'same_region_map_both_actors':True,
    'polygon_counts':stats,'modes_rendered':['regions','plain'],'native_texture_used':False,
    'control':visual['control'],'limitations':['Broad deformation-based body regions, not an exact anatomical muscle segmentation.']})
assert hashlib.sha256(source.read_bytes()).hexdigest()==source_hash
print('APPEARANCE_STUDY_COMPLETE',json.dumps(stats))
