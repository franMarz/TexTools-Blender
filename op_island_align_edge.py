import bpy
import bmesh
import math

from . import utilities_uv
from . import settings



class op(bpy.types.Operator):
	bl_idname = "uv.textools_island_align_edge"
	bl_label = "Align Island by Edge"
	bl_description = "Align Islands by selected Edge"
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
		if bpy.context.scene.tool_settings.use_uv_select_sync:
			return False
		if not bpy.context.object.data.uv_layers:
			return False
		if bpy.context.scene.tool_settings.uv_select_mode != 'EDGE':
			return False
		return True


	def execute(self, context):
		utilities_uv.multi_object_loop(main, context)
		return {'FINISHED'}



def main(context):
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()

	#Store selection
	selected_faces_edge_loops = utilities_uv.selection_store(bm, uv_layers, return_selected_faces_edges=True)
	if not selected_faces_edge_loops:
		return

	# Collect island and edge pairs
	selected_faces_islands, selected_faces_loops = utilities_uv.getSelectionFacesIslands(bm, uv_layers, selected_faces_edge_loops)

	# Align each island to its edges
	for face in selected_faces_loops:
		align_island(selected_faces_loops[face][0][uv_layers].uv, selected_faces_loops[face][1][uv_layers].uv, selected_faces_islands[face])

	#Restore selection
	utilities_uv.selection_restore(bm, uv_layers)



def align_island(uv_vert0, uv_vert1, faces):
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()

	# Select faces
	bpy.ops.uv.select_all(action='DESELECT')
	for face in faces:
		for loop in face.loops:
			loop[uv_layers].select = True

	diff = uv_vert1 - uv_vert0
	current_angle = math.atan2(diff.x, diff.y)
	angle_to_rotate = round(current_angle / (math.pi/2)) * (math.pi/2) - current_angle

	# For some reason, bpy.ops.transform.rotate behaves differently based on the version of Blender.
	if settings.bversion == 2.83 or settings.bversion == 2.91:
		angle_to_rotate = -angle_to_rotate

	bpy.context.space_data.pivot_point = 'CURSOR'
	bpy.ops.uv.cursor_set(location=uv_vert0 + diff/2)

	bpy.ops.transform.rotate(value=angle_to_rotate, orient_axis='Z', constraint_axis=(False, False, False), orient_type='GLOBAL', mirror=False, use_proportional_edit=False)


bpy.utils.register_class(op)
