import bpy
import bmesh

class op(bpy.types.Operator):
    bl_idname = "uv.textools_select_concave_faces"
    bl_label = "Select concave"
    bl_description = "Select all concave faces"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not bpy.context.active_object:
            return False
        if bpy.context.active_object.type != 'MESH':
            return False
        if bpy.context.active_object.mode != 'EDIT':
            return False
        return True
    
    def execute(self, context):
        obj = bpy.context.edit_object
        me = obj.data

        bm = bmesh.from_edit_mesh(me)
        bm.faces.active = None

        for face in bm.faces:
            face.select_set(False)
            for loop in face.loops:
                if not loop.is_convex:
                    face.select_set(True)
                    break

        bmesh.update_edit_mesh(me)
        return {'FINISHED'}

bpy.utils.register_class(op)
