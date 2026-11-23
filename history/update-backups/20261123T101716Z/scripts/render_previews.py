"""Blender-only view rendering helpers for the remote importer."""
from pathlib import Path

def render_views(bpy,output,config=None):
    cfg=config or {}; out=Path(output);out.mkdir(parents=True,exist_ok=True)
    scene=bpy.context.scene
    resolution=cfg.get('resolution',[960,800])
    if not (isinstance(resolution,list) and len(resolution)==2 and all(isinstance(x,int) and 320<=x<=2400 for x in resolution)):
        raise ValueError('render resolution must be two integers between 320 and 2400')
    scene.render.resolution_x,scene.render.resolution_y=resolution
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    results={}
    cameras={'front':'CAM_Front','side':'CAM_Side','three-quarter':'CAM_ThreeQuarter'}
    for label,name in cameras.items():
        cam=bpy.data.objects.get(name)
        if not cam or cam.type!='CAMERA':raise ValueError(f'Missing scene camera: {name}')
        scene.camera=cam
        path=out/(label+'.png')
        scene.render.filepath=str(path)
        bpy.ops.render.render(write_still=True)
        if not path.is_file() or path.stat().st_size<100:raise RuntimeError(f'Failed to render {label}')
        results[label]=str(path)
    # Region QA is explicitly driven by the two mannequin appearance sliders.
    # Render it only if both independent controls exist in the supplied scene.
    controls=[]
    for actor in ('A','B'):
        shapes=bpy.data.objects.get(f'CPL01_{actor}_SHAPES')
        if not shapes or shapes.type!='ARMATURE' or 'muscle group control' not in shapes.pose.bones:
            break
        controls.append(shapes.pose.bones['muscle group control'])
    if len(controls)==2:
        saved=[p.location.x for p in controls]
        try:
            for ctrl in controls:ctrl.location.x=.27
            bpy.context.view_layer.update()
            scene.camera=bpy.data.objects['CAM_ThreeQuarter']
            qa=out/'qa-regions.png';scene.render.filepath=str(qa)
            bpy.ops.render.render(write_still=True)
            if qa.is_file() and qa.stat().st_size>100:results['qa-regions']=str(qa)
        finally:
            for ctrl,value in zip(controls,saved):ctrl.location.x=value
            bpy.context.view_layer.update()
    return results
