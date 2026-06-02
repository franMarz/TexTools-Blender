import bpy
import bmesh

from . import utilities_color


gamma = 2.2


class op(bpy.types.Operator):
    bl_idname = "uv.textools_color_assign"
    bl_label = "Assign Color"
    bl_description = "Assign color to selected Objects or faces in Edit Mode"
    bl_options = {'UNDO'}

    index: bpy.props.IntProperty(description="Color Index", default=0)

    @classmethod
    def poll(cls, context):
        if bpy.context.area.ui_type != 'UV':
            return False
        if not bpy.context.active_object:
            return False
        if bpy.context.active_object not in bpy.context.selected_objects:
            return False
        if bpy.context.active_object.type != 'MESH':
            return False
        return True

    def execute(self, context):
        assign_color(self, context, self.index)
        return {'FINISHED'}



def assign_color(self, context, index):
    selected_obj = bpy.context.selected_objects.copy()

    previous_mode = 'OBJECT'
    if len(selected_obj) == 1:
        previous_mode = bpy.context.active_object.mode

    for obj in selected_obj:
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(state=True, view_layer=None)
        bpy.context.view_layer.objects.active = obj

        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(obj.data)

        if previous_mode == 'OBJECT':
            bpy.ops.mesh.select_all(action='SELECT')

        if bpy.context.scene.texToolsSettings.color_assign_mode == 'MATERIALS':
            for i in range(index + 1):
                if index >= len(obj.material_slots):
                    bpy.ops.object.material_slot_add()

            utilities_color.assign_slot(obj, index)
            obj.active_material_index = index
            bpy.ops.object.material_slot_assign()

        else:
            color = list(utilities_color.get_color(index).copy())
            color[0] = pow(color[0], 1 / gamma)
            color[1] = pow(color[1], 1 / gamma)
            color[2] = pow(color[2], 1 / gamma)
            rgba = (color[0], color[1], color[2], 1.0)

            utilities_color.ensure_color_layer(obj.data, utilities_color.COLOR_LAYER_NAME)

            # Refresh edit bmesh after creating/activating attribute so the layer is visible to bmesh.
            bm = bmesh.from_edit_mesh(obj.data)
            utilities_color.set_bmesh_face_colors(bm, utilities_color.COLOR_LAYER_NAME, rgba, only_selected=True)
            bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    for obj in selected_obj:
        obj.select_set(state=True, view_layer=None)
    bpy.ops.object.mode_set(mode=previous_mode)

    utilities_color.update_properties_tab()
    utilities_color.update_view_mode()


bpy.utils.register_class(op)
