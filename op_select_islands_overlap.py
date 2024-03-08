import bpy
import bmesh

from . import utilities_uv



class op(bpy.types.Operator):
	bl_idname = "uv.textools_select_islands_overlap"
	bl_label = "Select outline"
	bl_description = "Select all overlapping UV islands but one"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		if bpy.context.area.ui_type != 'UV':
			return False
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		if bpy.context.active_object.mode != 'EDIT':
			return False
		if not bpy.context.object.data.uv_layers:
			return False
		if bpy.context.scene.tool_settings.use_uv_select_sync:
			return False
		return True


	def execute(self, context):
		bpy.ops.uv.select_overlap()
		utilities_uv.multi_object_loop(deselect, self, context)
		bpy.ops.uv.select_linked()
		return {'FINISHED'}



def deselect(self, context):
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()

	islands = utilities_uv.getSelectionIslands(bm, uv_layers)
	if len(islands) > 1:
		for face in islands[0]:
			for loop in face.loops:
				loop[uv_layers].select = False
		utilities_uv.multi_object_loop_stop = True


bpy.utils.register_class(op)
