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

		return True
	
	def execute(self, context):
		crop(self, context)
		return {'FINISHED'}



def crop(self, context):
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data);
	uv_layers = bm.loops.layers.uv.verify();

	padding = utilities_ui.get_padding()

	
	# Scale to fit bounds
	bbox = utilities_uv.getSelectionBBox()
	scale_u = (1.0-padding) / bbox['width']
	scale_v = (1.0-padding) / bbox['height']
	scale = min(scale_u, scale_v)

	bpy.ops.transform.resize(value=(scale, scale, scale), constraint_axis=(False, False, False), mirror=False, use_proportional_edit=False)

	# Reposition
	bbox = utilities_uv.getSelectionBBox()

	delta_position = Vector((padding/2,1-padding/2)) - Vector((bbox['min'].x, bbox['min'].y + bbox['height']))
	bpy.ops.transform.translate(value=(delta_position.x, delta_position.y, 0))

bpy.utils.register_class(op)