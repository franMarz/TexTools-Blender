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
		if bpy.context.area.ui_type != 'UV':
			return False
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object.mode != 'EDIT':
			return False
		if not bpy.context.object.data.uv_layers:
			return False
		if bpy.context.scene.tool_settings.use_uv_select_sync:
			return False
		return True


	def execute(self, context):
		udim_tile, column, row = utilities_uv.get_UDIM_tile_coords(bpy.context.active_object)
		utilities_uv.multi_object_loop(centralize, context, udim_tile, column, row)
		return {'FINISHED'}



def centralize(context, udim_tile, column, row):
	selection_mode = bpy.context.scene.tool_settings.uv_select_mode
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()

	islands = utilities_uv.getSelectionIslands(bm, uv_layers)
	
	for island in islands:
		island_loops = {loop for face in island for loop in face.loops}
		boundary_loops = {loop for loop in island_loops if loop.link_loop_radial_next not in island_loops or loop.edge.is_boundary}
		bounds = utilities_uv.get_BBOX(boundary_loops, bm, uv_layers, are_loops=True)
		center = bounds['center']

		utilities_uv.move_island(island, round(-center.x + 0.5) + column, round(-center.y + 0.5) + row)

	# Workaround for selection not flushing properly from loops to EDGE Selection Mode, apparently since UV edge selection support was added to the UV space
	bpy.ops.uv.select_mode(type='VERTEX')
	bpy.context.scene.tool_settings.uv_select_mode = selection_mode


bpy.utils.register_class(op)
