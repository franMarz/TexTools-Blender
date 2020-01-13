import bpy
import bmesh
import operator
import math
from mathutils import Vector
from collections import defaultdict
from math import pi

from . import utilities_bake


class op(bpy.types.Operator):
	bl_idname = "uv.textools_bake_organize_names"
	bl_label = "Match Names"
	bl_description = "Match high poly object names to low poly objects by their bounding boxes."
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		# Require 2 or more objects to sort
		if len(bpy.context.selected_objects) <= 1:
			return False

		return True


	def execute(self, context):
		sort_objects(self)
		return {'FINISHED'}



def sort_objects(self):
	# Collect objects
	objects = []
	bounds = {}
	for obj in bpy.context.selected_objects:
		if obj.type == 'MESH':
			objects.append(obj)
			bounds[obj] = get_bbox(obj)

	print("Objects {}x".format(len(objects)))

	# Get smallest side of any bounding box
	min_side = min(bounds[objects[0]]['size'].x, bounds[objects[0]]['size'].y, bounds[objects[0]]['size'].z)
	avg_side = 0
	for obj in bounds:
		min_side = min(min_side, bounds[obj]['size'].x, bounds[obj]['size'].y, bounds[obj]['size'].z)
		avg_side+=bounds[obj]['size'].x
		avg_side+=bounds[obj]['size'].y
		avg_side+=bounds[obj]['size'].z
	avg_side/=(len(bounds)*3)

	# Get all Low and high poly objects
	objects_low = [obj for obj in objects if utilities_bake.get_object_type(obj)=='low']
	objects_high = [obj for obj in objects if utilities_bake.get_object_type(obj)=='high']

	if len(objects_low) == 0:
		self.report({'ERROR_INVALID_INPUT'}, "There are no low poly objects selected")
		return
	elif len(objects_high) == 0:
		self.report({'ERROR_INVALID_INPUT'}, "There are no high poly objects selected")
		return

	print("Low {}x, High {}x".format(len(objects_low),len(objects_high)))

	pairs_low_high = {}

	objects_left_high = objects_high.copy()
	for obj_A in objects_low:

		matches = {}
		for obj_B in objects_left_high:
			score = get_score(obj_A, obj_B)
			p = score / avg_side
			if p > 0 and p <= 0.65:
				matches[obj_B] = p
			else:
				print("Not matched: {} ".format(p))

		if(len(matches) > 0):
			sorted_matches = sorted(matches.items(), key=operator.itemgetter(1))
			for i in range(0, len(sorted_matches)):
				A = obj_A
				B = sorted_matches[i][0]
				p = sorted_matches[i][1]
				print("Check: {}%	'{}' = '{}' ".format(int(p * 100.0), A.name, B.name ))

			# Remove from list
			objects_left_high.remove(sorted_matches[0][0])
			pairs_low_high[obj_A] = sorted_matches[0][0]
			print("")

	# objects_unsorted = [obj for obj in objects if (obj not in pairs_low_high.values() and obj not in pairs_low_high.keys() )]
	
	bpy.ops.object.select_all(action='DESELECT')
	for obj_A in pairs_low_high:
		obj_B = pairs_low_high[obj_A]
		try:
			obj_B.name = utilities_bake.get_set_name(obj_A)+" high"

			obj_A.select_set( state = True, view_layer = None)
			obj_B.select_set( state = True, view_layer = None)
		except:
			print("Fail")

	print("Matched {}x".format(len(pairs_low_high)))



def get_score(A, B):

	bbox_A = get_bbox(A)
	bbox_B = get_bbox(B)

	# Not colliding
	if not is_colliding(bbox_A, bbox_B):
		return -1.0

	# Position
	delta_pos = (bbox_B['center'] - bbox_A['center']).length

	# Volume
	volume_A = bbox_A['size'].x * bbox_A['size'].y * bbox_A['size'].z
	volume_B = bbox_B['size'].x * bbox_B['size'].y * bbox_B['size'].z
	delta_vol = (max(volume_A, volume_B) - min(volume_A, volume_B))/3.0

	# Longest side
	side_A_max = max(bbox_A['size'].x, bbox_A['size'].y, bbox_A['size'].z )
	side_B_max = max(bbox_B['size'].x, bbox_B['size'].y, bbox_B['size'].z )
	delta_size_max = abs(side_A_max - side_B_max)

	return delta_pos + delta_vol + delta_size_max



def get_bbox(obj):
	corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]

	# Get world space Min / Max
	box_min = Vector((corners[0].x, corners[0].y, corners[0].z))
	box_max = Vector((corners[0].x, corners[0].y, corners[0].z))
	for corner in corners:
		# box_min.x = -8
		box_min.x = min(box_min.x, corner.x)
		box_min.y = min(box_min.y, corner.y)
		box_min.z = min(box_min.z, corner.z)
		
		box_max.x = max(box_max.x, corner.x)
		box_max.y = max(box_max.y, corner.y)
		box_max.z = max(box_max.z, corner.z)

	return {
		'min':box_min, 
		'max':box_max, 
		'size':(box_max-box_min),
		'center':box_min+(box_max-box_min)/2
	}



def is_colliding(bbox_A, bbox_B):
	def is_collide_1D(A_min, A_max, B_min, B_max):
		# One line is inside the other
		length_A = A_max-A_min
		length_B = B_max-B_min
		center_A = A_min + length_A/2
		center_B = B_min + length_B/2

		return abs(center_A - center_B) <= (length_A+length_B)/2

	collide_x = is_collide_1D(bbox_A['min'].x, bbox_A['max'].x, bbox_B['min'].x, bbox_B['max'].x)
	collide_y = is_collide_1D(bbox_A['min'].y, bbox_A['max'].y, bbox_B['min'].y, bbox_B['max'].y)
	collide_z = is_collide_1D(bbox_A['min'].z, bbox_A['max'].z, bbox_B['min'].z, bbox_B['max'].z)

	return collide_x and collide_y and collide_z

bpy.utils.register_class(op)

