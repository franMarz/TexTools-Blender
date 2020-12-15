import bpy
import bmesh
import operator
from mathutils import Vector
from collections import defaultdict
from math import pi

from . import utilities_uv
from . import utilities_ui

class op(bpy.types.Operator):
	bl_idname = "uv.textools_uv_crop"
	bl_label = "Crop"
	bl_description = "Crop UV area to selected UV faces"
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
		all_ob_bounds = utilities_uv.multi_object_loop(utilities_uv.getSelectionBBox, need_results=True)

		select = False
		for ob_bounds in all_ob_bounds:
			if len(ob_bounds) > 0 :
				select = True
				break
		if not select:
			return {'CANCELLED'}
		
		boundsAll = utilities_uv.getMultiObjectSelectionBBox(all_ob_bounds)

		prepivot = bpy.context.space_data.pivot_point
		precursor = tuple(bpy.context.space_data.cursor_location)
		bpy.context.space_data.pivot_point = 'CURSOR'
		bpy.context.space_data.cursor_location = (0.0, 0.0)

		padding = utilities_ui.get_padding()

		# Scale to fit bounds
		scale_u = (1.0-padding) / boundsAll['width']
		scale_v = (1.0-padding) / boundsAll['height']
		scale = min(scale_u, scale_v)

		bpy.ops.transform.resize(value=(scale, scale, 1), constraint_axis=(False, False, False), mirror=False, use_proportional_edit=False)

		# Reposition
		delta_position = Vector((padding/2,1-padding/2)) - Vector((scale*boundsAll['min'].x, scale*boundsAll['min'].y + scale*boundsAll['height']))
		bpy.ops.transform.translate(value=(delta_position.x, delta_position.y, 0))

		bpy.context.space_data.pivot_point = prepivot
		bpy.context.space_data.cursor_location = precursor

		return {'FINISHED'}


bpy.utils.register_class(op)