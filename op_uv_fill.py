import bpy
import bmesh
import operator
import math

from mathutils import Vector
from collections import defaultdict


from . import utilities_uv
from . import utilities_ui

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

		return True
	
	def execute(self, context):
		fill(self, context)
		return {'FINISHED'}



def fill(self, context):


	#Store selection
	utilities_uv.selection_store()

	bm = bmesh.from_edit_mesh(bpy.context.active_object.data);
	uv_layers = bm.loops.layers.uv.verify();

	
	# 1.) Rotate minimal bounds (less than 45 degrees rotation)
	steps = 8
	angle = 45;	# Starting Angle, half each step
	bboxPrevious = utilities_uv.getSelectionBBox()
	
	for i in range(0, steps):
		# Rotate right
		bpy.ops.transform.rotate(value=(angle * math.pi / 180), orient_axis='Z')
		bbox = utilities_uv.getSelectionBBox()


		print("Rotate {}, diff le: {}".format(angle, bbox['height'] - bboxPrevious['height']))


		if i == 0:
			# Check if already squared
			sizeA = bboxPrevious['width'] * bboxPrevious['height']
			sizeB = bbox['width'] * bbox['height']
			if abs(bbox['width'] - bbox['height']) <= 0.0001 and sizeA < sizeB:
				bpy.ops.transform.rotate(value=(-angle * math.pi / 180), orient_axis='Z')
				break;

		if bbox['minLength'] < bboxPrevious['minLength']:
			bboxPrevious = bbox;	# Success
		else:
			# Rotate Left
			bpy.ops.transform.rotate(value=(-angle*2 * math.pi / 180), orient_axis='Z')
			bbox = utilities_uv.getSelectionBBox()
			if bbox['minLength'] < bboxPrevious['minLength']:
				bboxPrevious = bbox;	# Success
			else:
				# Restore angle of this iteration
				bpy.ops.transform.rotate(value=(angle * math.pi / 180), orient_axis='Z')

		angle = angle / 2

	if bboxPrevious['width'] < bboxPrevious['height']:
		bpy.ops.transform.rotate(value=(90 * math.pi / 180), orient_axis='Z')

	# 2.) Match width and height to UV bounds
	bbox = utilities_uv.getSelectionBBox()

	scale_x = 1.0 / bbox['width']
	scale_y = 1.0 / bbox['height']
		
	print("Scale {} | {}".format(scale_x, scale_y))

	bpy.context.tool_settings.transform_pivot_point = 'BOUNDING_BOX_CENTER'
	bpy.ops.transform.resize(value=(scale_x, scale_y, 1), constraint_axis=(False, False, False), orient_type='GLOBAL', use_proportional_edit=False)


	bbox = utilities_uv.getSelectionBBox()
	offset_x = -bbox['min'].x
	offset_y = -bbox['min'].y
	
	bpy.ops.transform.translate(value=(offset_x, offset_y, 0), constraint_axis=(False, False, False), orient_type='GLOBAL', use_proportional_edit=False)

	#Restore selection
	utilities_uv.selection_restore()

bpy.utils.register_class(op)