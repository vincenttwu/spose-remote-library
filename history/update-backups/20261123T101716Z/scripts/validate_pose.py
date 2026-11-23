"""Blender-only contact proxy measurements. Not a physical solver or safety certificate."""
from math import dist

def _coords(bpy,actor,max_vertices=12000):
    obj=bpy.data.objects.get(f'CPL01_{actor}_BODY')
    if not obj or obj.type!='MESH':return []
    dg=bpy.context.evaluated_depsgraph_get();evaluated=obj.evaluated_get(dg)
    mesh=evaluated.to_mesh()
    try:
        step=max(1,len(mesh.vertices)//max_vertices)
        return [tuple(evaluated.matrix_world @ mesh.vertices[i].co) for i in range(0,len(mesh.vertices),step)]
    finally:evaluated.to_mesh_clear()

def measure_contact(bpy,config):
    from mathutils import Vector
    from mathutils.kdtree import KDTree
    out={'method':'sampled_evaluated_mesh_nearest_point_and_bone_head_proxies',
        'warning':'Candidate proximities only; no signed penetration depth, balance simulation or anatomical validity.'}
    a=_coords(bpy,'A');b=_coords(bpy,'B')
    if a and b:
        tree=KDTree(len(b))
        for i,p in enumerate(b):tree.insert(Vector(p),i)
        tree.balance()
        nearest=[]
        for p in a:
            _,_,distance=tree.find(Vector(p))
            nearest.append(distance)
        nearest.sort()
        out['mesh_sample']={'a_vertices':len(a),'b_vertices':len(b),'minimum_distance_m':round(nearest[0],6),
            'one_percentile_distance_m':round(nearest[int(.01*(len(nearest)-1))],6),
            'sample_pairs_under_1cm':sum(d<=.01 for d in nearest)}
    anchor_results=[]
    for anchor in config.get('anchors',[]):
        name=anchor.get('id','unnamed')
        try:
            ar=bpy.data.objects[f'CPL01_{anchor["actor"]}_RIG']
            tr=bpy.data.objects[f'CPL01_{anchor["target_actor"]}_RIG']
            pa=ar.pose.bones[anchor['bone']];pb=tr.pose.bones[anchor['target_bone']]
            point_a=ar.matrix_world @ pa.head;point_b=tr.matrix_world @ pb.head
            distance=(point_a-point_b).length
            tolerance=float(anchor.get('tolerance_m',.05))
            anchor_results.append({'id':name,'distance_m':round(distance,6),'tolerance_m':tolerance,
                'proxy_in_tolerance':distance<=tolerance,'method':'bone_head_to_bone_head'})
        except Exception as exc:
            anchor_results.append({'id':name,'error':str(exc)})
    out['anchors']=anchor_results
    return out
