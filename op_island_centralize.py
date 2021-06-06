import bpy
import bmesh

from . import utilities_uv



class op(bpy.types.Operator):
	bl_idname = "uv.textools_island_centralize"
	bl_label = "Centralize"
	bl_description = "Move selected islands the closest possible to the 0-1 UV area without changes in the textured object"
	bl_options = {'REGISTER', 'UNDO'}
	

	@classmethod
	def poll(cls, context):
		if not bpy.context.active_object:
			return False

		#Only in Edit mode
		if bpy.context.active_object.mode != 'EDIT':
			return False

		#Only in UV editor mode
		if bpy.context.area.type != 'IMAGE_EDITOR':
			return False
		
		#Requires UV map
		if not bpy.context.object.data.uv_layers:
			return False

		# Not in Synced mode
		if bpy.context.scene.tool_settings.use_uv_select_sync:
			return False

		return True


	def execute(self, context):
		utilities_uv.multi_object_loop(centralize, context)
		return {'FINISHED'}


def centralize(context):
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	islands = utilities_uv.getSelectionIslands()
	for island in islands:
		bounds = utilities_uv.get_island_BBOX(island)
		center = bounds['center']
		utilities_uv.move_island(island, round(-center.x + 0.5), round(-center.y + 0.5))


bpy.utils.register_class(op)
