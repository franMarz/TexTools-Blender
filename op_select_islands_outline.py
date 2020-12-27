import bpy
import bmesh
import operator

from . import utilities_uv
from . import utilities_ui



class op(bpy.types.Operator):
	bl_idname = "uv.textools_select_islands_outline"
	bl_label = "Select Island outline"
	bl_description = "Select island edge bounds"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		if not bpy.context.active_object:
			return False
		
		#Only in Edit mode
		if bpy.context.active_object.mode != 'EDIT':
			return False
		
		if bpy.context.active_object.type != 'MESH':
			return False

		#Requires UV map
		if not bpy.context.object.data.uv_layers:
			return False

		# #requires UV_sync
		# if not bpy.context.scene.tool_settings.use_uv_select_sync:
		# 	return False

		return True
	

	def execute(self, context):
		utilities_uv.multi_object_loop(select_outline, self, context)
		return {'FINISHED'}


def select_outline(self, context):
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()

	sync = bpy.context.scene.tool_settings.use_uv_select_sync

	# Store previous edge seams
	edges_seam = [edge for edge in bm.edges if edge.seam]

	# Clear original seams
	for edge in edges_seam:
		edge.seam = False
	
	# Create seams from islands
	contextViewUV = utilities_ui.GetContextViewUV()
	if not contextViewUV:
		self.report({'ERROR_INVALID_INPUT'}, "This tool requires an available UV/Image view.")
		return {'CANCELLED'}
	bpy.ops.uv.seams_from_islands(contextViewUV)

	edges_seams_from_islands = [e for e in bm.edges if e.seam]
	if sync:
		edges_selected = [e for e in bm.edges if e.select]
	else:
		loops_seams_from_islands = [l for edge in edges_seams_from_islands for l in edge.link_loops]
		loops_selected = [loop for face in bm.faces for loop in face.loops if loop[uv_layers].select]
	
	# Clear false seams
	for edge in edges_seams_from_islands:
		edge.seam = False

	# Select bound edges from edges marked as seams and edge boundaries
	if sync:
		bpy.ops.mesh.select_all(action='DESELECT')
		bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
		for edge in edges_selected:
			if edge.is_boundary or edge in edges_seams_from_islands:
				edge.select = True
	else:
		bpy.ops.uv.select_all(action='DESELECT')
		bpy.context.scene.tool_settings.uv_select_mode = 'EDGE'
		for loop in loops_selected:
			if loop.link_loop_next in loops_selected:
				if loop in loops_seams_from_islands or loop.edge.is_boundary:
					loop[uv_layers].select = True
					loop.link_loop_next[uv_layers].select = True

	# Restore seam selection
	for edge in edges_seam:
		edge.seam = True


bpy.utils.register_class(op)
