"""Read a saved pose and report body-region floor bounds and native palm planes."""
import bpy,sys,json
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from character_common import ROOT
scene=sys.argv[sys.argv.index('--')+1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/scene),use_scripts=False)
for actor in ['A','B']:
    body=bpy.data.objects[f'CPL01_{actor}_BODY'];rig=bpy.data.objects[f'CPL01_{actor}_RIG']
    names={g.index:g.name for g in body.vertex_groups}
    pts=[]
    for vertex in body.data.vertices:
        if sum(g.weight for g in vertex.groups if names[g.group].startswith(('DEF-hand.L','DEF-palm.')))>.7:
            pts.append(list(body.data.shape_keys.key_blocks['Basis'].data[vertex.index].co))
    points=np.asarray(pts);cov=np.cov(points.T);values,vectors=np.linalg.eigh(cov)
    print('NATIVE_PALM_PLANE',actor,values.tolist(),vectors[:,0].tolist())
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
    regions={}
    for poly in mesh.polygons:
        role=body.data.materials[poly.material_index]['region']
        for index in poly.vertices:
            point=ev.matrix_world @ mesh.vertices[index].co
            side='L' if point.x>0 else 'R'
            name=role+'.'+side
            if name not in regions:regions[name]={'min_z':point.z,'max_z':point.z}
            else:regions[name]['min_z']=min(regions[name]['min_z'],point.z);regions[name]['max_z']=max(regions[name]['max_z'],point.z)
    ev.to_mesh_clear()
    print('REGION_BOUNDS',actor,json.dumps(regions))
