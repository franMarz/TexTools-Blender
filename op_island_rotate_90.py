import bpy
import bmesh
import operator
import math
from mathutils import Vector
from collections import defaultdict
from math import pi

from . import utilities_uv

class op(bpy.types.Operator):
	bl_idname = "uv.textools_island_rotate_90"
	bl_label = "Rotate 90 degrees"
	bl_description = "Rotate the selected UV island 90 degrees left or right"
	bl_options = {'REGISTER', 'UNDO'}
	
	angle : bpy.props.FloatProperty(name="Angle")


	@classmethod
	def poll(cls, context):
		#Only in UV editor mode
		if bpy.context.area.type != 'IMAGE_EDITOR':
			return False

		if not bpy.context.active_object:
			return False

		if bpy.context.active_object.type != 'MESH':
			return False

		#Only in Edit mode
		if bpy.context.active_object.mode != 'EDIT':
			return False

		#Requires UV map
		if not bpy.context.object.data.uv_layers:
			return False
			
		# Not in Synced mode
		if bpy.context.scene.tool_settings.use_uv_select_sync:
			return False

		return True


	def execute(self, context):

		main(context, self.angle)
		return {'FINISHED'}


def main(context, angle):
	
	#Store selection
	utilities_uv.selection_store()

	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()
	
	bpy.ops.uv.select_linked()

	#Bounds
	bounds_initial = utilities_uv.getSelectionBBox()
	bpy.ops.transform.rotate(value=angle, orient_axis='Z', constraint_axis=(False, False, False), use_proportional_edit=False)

	#Align rotation to top left|right
	bounds_post = utilities_uv.getSelectionBBox()
	dy = bounds_post['max'].y - bounds_initial['max'].y
	dx = 0
	if angle > 0:
		dx = bounds_post['max'].x - bounds_initial['max'].x
	else:
		dx = bounds_post['min'].x - bounds_initial['min'].x
	bpy.ops.transform.translate(value=(-dx, -dy, 0), constraint_axis=(False, False, False), use_proportional_edit=False)


	#Restore selection
	utilities_uv.selection_restore()

bpy.utils.register_class(op)