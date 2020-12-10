import bpy
import bmesh
import operator
from mathutils import Vector
from collections import defaultdict
from math import pi

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
		utilities_uv.multi_object_loop(select_outline, context)
		return {'FINISHED'}


def select_outline(context):

	bm = bmesh.from_edit_mesh(bpy.context.active_object.data);
	uv_layers = bm.loops.layers.uv.verify();
	
	# Store previous edge seams
	edges_seam = [edge for edge in bm.edges if edge.seam]
	

	contextViewUV = utilities_ui.GetContextViewUV()
	if not contextViewUV:
		self.report({'ERROR_INVALID_INPUT'}, "This tool requires an available UV/Image view.")
		return

	# Create seams from islands
	bpy.ops.uv.seams_from_islands(contextViewUV)
	edges_seams_from_islands = [edge for edge in bm.edges if edge.seam]

	pre_sync = bpy.context.scene.tool_settings.use_uv_select_sync
	if bpy.context.scene.tool_settings.use_uv_select_sync:
		bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
		bpy.ops.uv.select_linked()
		bpy.context.scene.tool_settings.use_uv_select_sync = False
		bpy.ops.uv.select_all(action='SELECT')
	else:
		current_edit = tuple(bpy.context.tool_settings.mesh_select_mode)
		bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
		current_select = [f for f in bm.faces if f.select]

	islands = utilities_uv.getSelectionIslands()
	faces_islands = [face for island in islands for face in island]
	edges_islands = [edge for island in islands for face in island for edge in face.edges]
	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
	bpy.ops.mesh.select_all(action='DESELECT')

	
	# Clear seams
	for edge in edges_seams_from_islands:
		edge.seam = False

	if pre_sync:
		# Select seams from islands edges and edge boundaries
		for edge in edges_islands:
			if edge.is_boundary or edge in edges_seams_from_islands:
				edge.select = True
	else:
		for face in current_select:
			face.select = True
		bpy.context.tool_settings.mesh_select_mode = current_edit
		bpy.ops.uv.select_all(action='DESELECT')
		edges = []
		for edge in edges_islands:
			if edge.is_boundary or edge in edges_seams_from_islands:
				edges.extend([e for e in edge.verts[0].link_loops])
				edges.extend([e for e in edge.verts[1].link_loops])
				#edges.append(edge)
		
		bpy.context.scene.tool_settings.uv_select_mode = 'EDGE'
		for face in faces_islands:
			for loop in face.loops:
				if loop in edges:
					loop[uv_layers].select = True


	# Restore seam selection
	for edge in edges_seam:
		edge.seam = True

	bpy.context.scene.tool_settings.use_uv_select_sync = pre_sync

bpy.utils.register_class(op)
