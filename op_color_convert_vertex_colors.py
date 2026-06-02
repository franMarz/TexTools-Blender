import bpy
import bmesh

from . import utilities_color


gamma = 2.2


class op(bpy.types.Operator):
    bl_idname = "uv.textools_color_convert_to_vertex_colors"
    bl_label = "Pack Texture"
    bl_description = "Pack ID Colors into single texture and UVs"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if bpy.context.area.ui_type != 'UV':
            return False
        if not bpy.context.active_object:
            return False
        if bpy.context.active_object not in bpy.context.selected_objects:
            return False
        if len(bpy.context.selected_objects) != 1:
            return False
        if bpy.context.active_object.type != 'MESH':
            return False
        return True

    def execute(self, context):
        convert_vertex_colors(self, context)
        return {'FINISHED'}



def convert_vertex_colors(self, context):
    obj = bpy.context.active_object
    previous_mode = obj.mode

    # Ensure the target color attribute exists before entering edit mode.
    bpy.ops.object.mode_set(mode='OBJECT')
    utilities_color.ensure_color_layer(obj.data, utilities_color.COLOR_LAYER_NAME)

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)

    # Guarantee selection state is flushed before we start coloring.
    bm.faces.ensure_lookup_table()

    for i, slot in enumerate(obj.material_slots):
        if not slot.material:
            continue

        for face in bm.faces:
            face.select = (face.material_index == i)

        color = list(utilities_color.get_color(i).copy())
        color[0] = pow(color[0], 1 / gamma)
        color[1] = pow(color[1], 1 / gamma)
        color[2] = pow(color[2], 1 / gamma)
        rgba = (color[0], color[1], color[2], 1.0)

        utilities_color.set_bmesh_face_colors(
            bm,
            utilities_color.COLOR_LAYER_NAME,
            rgba,
            only_selected=True,
        )

    bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)

    bpy.ops.object.mode_set(mode='OBJECT')

    for area in bpy.context.screen.areas:
        if area.type == 'PROPERTIES':
            for space in area.spaces:
                if space.type == 'PROPERTIES':
                    space.context = 'DATA'

    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'SOLID'
                    try:
                        space.shading.color_type = 'ATTRIBUTE'
                    except Exception:
                        space.shading.color_type = 'VERTEX'

    if previous_mode != 'OBJECT':
        try:
            bpy.ops.object.mode_set(mode=previous_mode)
        except Exception:
            pass

    bpy.ops.ui.textools_popup('INVOKE_DEFAULT', message="Vertex colors assigned")


bpy.utils.register_class(op)
