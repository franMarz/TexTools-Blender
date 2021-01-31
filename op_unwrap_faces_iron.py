import bpy
import os
import bmesh
from mathutils import Vector
from collections import defaultdict
from math import pi

from . import utilities_uv
from . import utilities_ui

class op(bpy.types.Operator):
	"""UV Operator description"""
	bl_idname = "uv.textools_unwrap_faces_iron"
	bl_label = "Iron"
	bl_description = "Unwrap selected faces into a single UV island"
	bl_options = {'REGISTER', 'UNDO'}
	
	@classmethod
	def poll(cls, context):

		if not bpy.context.active_object:
			return False

		if bpy.context.active_object.type != 'MESH':
			return False

		#Only in Edit mode
		if bpy.context.active_object.mode != 'EDIT':
			return False

		# Need view Face mode
		if tuple(bpy.context.scene.tool_settings.mesh_select_mode)[2] == False:
			return False
		#Only in UV editor mode
		# if bpy.context.area.type != 'IMAGE_EDITOR':
		# 	return False

		#Requires UV map
		# if not bpy.context.object.data.uv_layers:
		# 	return False

		# if bpy.context.scene.tool_settings.uv_select_mode != 'FACE':
		#  	return False
		return True

	def execute(self, context):
		main(context)
		return {'FINISHED'}


def main(context):
	print("operatyor_faces_iron()")

	#utilities_uv.selection_store()

	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)

	bpy.context.scene.tool_settings.uv_select_mode = 'FACE'
	bpy.ops.mesh.mark_seam(clear=True)


	selected_faces = [f for f in bm.faces if f.select]

	# Hard edges to seams
	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
	bpy.ops.mesh.region_to_loop()
	bpy.ops.mesh.mark_seam(clear=False)

	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
	for face in selected_faces:
		face.select = True
	
	padding = utilities_ui.get_padding()
	bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=padding)

bpy.utils.register_class(op)