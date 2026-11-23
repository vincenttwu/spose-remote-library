"""Read-only inspection of source appearance controls; run in background Blender."""
import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=json.loads((ROOT/'body_profiles/BP001/v001/profile.json').read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=p['source_rig'],use_scripts=False)
result={'images':[{'name':i.name,'path':i.filepath,'packed':bool(i.packed_file),'size':list(i.size),
    'source':i.source} for i in bpy.data.images], 'node_groups':[],'material_slots':[]}
body=bpy.data.objects['Adjustable Mannequin Rigify']
result['material_slots']=[m.name for m in body.data.materials if m]
for block in list(bpy.data.materials)+list(bpy.data.node_groups):
    tree=block.node_tree if isinstance(block,bpy.types.Material) else block
    if not tree:continue
    nodes=[]
    for node in tree.nodes:
        if node.type in ['TEX_IMAGE','GROUP']:
            nodes.append({'name':node.name,'type':node.type,'image':node.image.name if node.type=='TEX_IMAGE' and node.image else None,
                'group':node.node_tree.name if node.type=='GROUP' and node.node_tree else None})
    drivers=[]
    if tree.animation_data:
        for fc in tree.animation_data.drivers:
            drivers.append({'path':fc.data_path,'expression':fc.driver.expression,
                'variables':[{'name':v.name,'targets':[{'id':t.id.name if t.id else None,'path':t.data_path} for t in v.targets]} for v in fc.driver.variables]})
    if nodes or drivers:result['node_groups'].append({'owner':block.name,'nodes':nodes,'drivers':drivers})
result['vertex_groups']=[g.name for g in body.vertex_groups]
(ROOT/'tooling/rig-maps/RIG001-source-materials-v001.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
