"""Shared candidate previews with evaluated-geometry camera framing."""
from pathlib import Path
from mathutils import Vector


def render_views(bpy,output,config=None):
    cfg=config or {};out=Path(output);out.mkdir(parents=True,exist_ok=True)
    scene=bpy.context.scene
    resolution=cfg.get('resolution',[1100,900])
    if not (isinstance(resolution,list) and len(resolution)==2 and all(type(v) is int and 320<=v<=2400 for v in resolution)):
        raise ValueError('render resolution must be [int,int] between 320 and 2400')
    scene.render.resolution_x,scene.render.resolution_y=resolution
    scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
    # Fit around *both* evaluated bodies instead of assuming two standing people.
    world=[]
    for actor in ('A','B'):
        obj=bpy.data.objects[f'CPL01_{actor}_BODY']
        ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh=ev.to_mesh()
        try:
            step=max(1,len(mesh.vertices)//7000)
            world.extend(ev.matrix_world @ mesh.vertices[i].co for i in range(0,len(mesh.vertices),step))
        finally:ev.to_mesh_clear()
    lo=Vector(tuple(min(p[i] for p in world) for i in range(3)))
    hi=Vector(tuple(max(p[i] for p in world) for i in range(3)))
    center=(lo+hi)*.5;extent=hi-lo
    # Orthographic scale is primarily vertical. The wide frontal silhouette gets
    # extra horizontal room; this conservative setting may be tightened later.
    scale=max(1.7,extent.z*1.36,extent.x*1.35,extent.y*1.15)
    cameras={
        'front':('CAM_Front',Vector((0,-6,1.6))),
        'side':('CAM_Side',Vector((6,0,1.2))),
        'three-quarter':('CAM_ThreeQuarter',Vector((4,-6,2.2)))
    }
    results={}
    for label,(name,offset) in cameras.items():
        cam=bpy.data.objects.get(name)
        if cam is None or cam.type!='CAMERA':raise ValueError(f'Missing reference camera {name}')
        cam.location=center+offset
        cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
        cam.data.type='ORTHO';cam.data.ortho_scale=scale
        scene.camera=cam
        filepath=out/(label+'.png');scene.render.filepath=str(filepath)
        bpy.ops.render.render(write_still=True)
        if not filepath.is_file() or filepath.stat().st_size<100:raise RuntimeError('Render failed: '+label)
        results[label]=str(filepath)
    controls=[]
    for actor in ('A','B'):
        shapes=bpy.data.objects.get(f'CPL01_{actor}_SHAPES')
        if not shapes or shapes.type!='ARMATURE' or 'muscle group control' not in shapes.pose.bones:
            break
        controls.append(shapes.pose.bones['muscle group control'])
    if len(controls)==2:
        old=[p.location.x for p in controls]
        try:
            for p in controls:p.location.x=.27
            bpy.context.view_layer.update()
            scene.camera=bpy.data.objects['CAM_ThreeQuarter']
            path=out/'qa-regions.png';scene.render.filepath=str(path)
            bpy.ops.render.render(write_still=True)
            if path.is_file() and path.stat().st_size>100:results['qa-regions']=str(path)
        finally:
            for p,x in zip(controls,old):p.location.x=x
            bpy.context.view_layer.update()
    return results
