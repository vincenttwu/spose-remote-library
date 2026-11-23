"""Shared Blender operations for BP001/CPL01; executed inside Blender Python."""
import bpy
from mathutils import Vector
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]

def evaluated_points(obj):
    bpy.context.view_layer.update()
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    try:
        return [evaluated.matrix_world @ v.co for v in mesh.vertices]
    finally:
        evaluated.to_mesh_clear()

def bounds(obj):
    points = evaluated_points(obj)
    lo = [min(p[i] for p in points) for i in range(3)]
    hi = [max(p[i] for p in points) for i in range(3)]
    return {'min':lo, 'max':hi, 'dimensions':[hi[i]-lo[i] for i in range(3)]}

def material(name, color):
    mat=bpy.data.materials.new(name)
    mat.diffuse_color=(*color,1)
    mat.use_nodes=True
    shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    shader.inputs['Base Color'].default_value=(*color,1)
    shader.inputs['Roughness'].default_value=.65
    return mat

def setup_stage():
    scene=bpy.context.scene
    scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1.0
    scene.render.engine='BLENDER_EEVEE'
    scene.render.resolution_x=800;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.film_transparent=False
    scene.world=bpy.data.worlds.new('Studio_World')
    scene.world.use_nodes=True
    bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND')
    bg.inputs['Color'].default_value=(.16,.18,.22,1);bg.inputs['Strength'].default_value=.5
    scene.view_settings.view_transform='AgX'
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.003))
    floor=bpy.context.object;floor.name='STUDIO_Floor';floor.data.materials.append(material('Studio_Floor',(.105,.12,.145)))
    for name,loc,energy,size in [('Key',(-3,-4,5),500,4),('Fill',(3,-2,3),350,3),('Rim',(1,3,4),650,3)]:
        ld=bpy.data.lights.new('STUDIO_'+name,'AREA');ld.energy=energy;ld.shape='DISK';ld.size=size
        light=bpy.data.objects.new(ld.name,ld);scene.collection.objects.link(light);light.location=loc
        light.rotation_euler=(Vector((0,0,.9))-light.location).to_track_quat('-Z','Y').to_euler()
    for name,loc in [('Front',(0,-6,.95)),('Side',(6,0,.95)),('ThreeQuarter',(4,-6,2.6))]:
        data=bpy.data.cameras.new('CAM_'+name);data.type='ORTHO';data.ortho_scale=2.15
        obj=bpy.data.objects.new(data.name,data);scene.collection.objects.link(obj);obj.location=loc
        obj.rotation_euler=(Vector((0,0,.925))-obj.location).to_track_quat('-Z','Y').to_euler()
    scene.camera=bpy.data.objects['CAM_Front']

def render(path, camera='CAM_Front'):
    scene=bpy.context.scene;scene.camera=bpy.data.objects[camera]
    scene.render.filepath=str(path)
    bpy.ops.render.render(write_still=True)

def hide_helpers():
    for col in bpy.data.collections:
        if col.name.startswith('WGTS_') or col.name=='Bone Shapes':
            col.hide_render=True
            for obj in col.objects:
                obj.hide_render=True
                if obj.name in bpy.context.view_layer.objects:obj.hide_set(True)
    meta=bpy.data.objects.get('Metarig')
    if meta:
        meta.hide_render=True
        if meta.name in bpy.context.view_layer.objects:meta.hide_set(True)

def write_json(path, value):
    Path(path).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
