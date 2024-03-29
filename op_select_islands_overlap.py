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
		return True


	def execute(self, context):
		bpy.ops.uv.select_overlap()
		bpy.ops.uv.select_linked()
		utilities_uv.multi_object_loop(deselect, self, context)
		return {'FINISHED'}



def deselect(self, context):
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()
	sync = bpy.context.scene.tool_settings.use_uv_select_sync
	if sync:
		selection_mode = tuple(bpy.context.scene.tool_settings.mesh_select_mode)

	islands = utilities_uv.get_selected_islands(bm, uv_layers)

	if len(islands) > 1:
		if sync:
			bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
			for face in islands[0]:
				face.select_set(False)
		else:
			for face in islands[0]:
				for loop in face.loops:
					loop[uv_layers].select = False

		utilities_uv.multi_object_loop_stop = True

	if sync:
		bpy.context.scene.tool_settings.mesh_select_mode = selection_mode
