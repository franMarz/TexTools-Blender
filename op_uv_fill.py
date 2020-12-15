import bpy
import bmesh
import operator
import math

from mathutils import Vector
from collections import defaultdict


from . import utilities_uv
from . import utilities_ui
from . import op_uv_crop


class op(bpy.types.Operator):
	bl_idname = "uv.textools_uv_fill"
	bl_label = "Fill"
	bl_description = "Fill UV selection to UV canvas"
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

		#Only in UV editor mode
		if bpy.context.area.type != 'IMAGE_EDITOR':
			return False

		#Requires UV map
		if not bpy.context.object.data.uv_layers:
			return False
		
		#Not in Synced mode
		if bpy.context.scene.tool_settings.use_uv_select_sync:
			return False
		
		return True
	
	def execute(self, context):
		prepivot = bpy.context.space_data.pivot_point
		precursor = tuple(bpy.context.space_data.cursor_location)
		bpy.context.space_data.pivot_point = 'CURSOR'
		bpy.context.space_data.cursor_location = (0.0, 0.0)

		utilities_uv.alignMinimalBounds()
		
		bpy.context.space_data.pivot_point = prepivot
		bpy.context.space_data.cursor_location = precursor

		bpy.ops.uv.textools_uv_crop()

		return {'FINISHED'}


bpy.utils.register_class(op)