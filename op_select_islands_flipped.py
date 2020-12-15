import bpy
import bmesh
import operator
from mathutils import Vector
from collections import defaultdict
from math import pi

from . import utilities_uv
import imp
imp.reload(utilities_uv)

class op(bpy.types.Operator):
	bl_idname = "uv.textools_select_islands_flipped"
	bl_label = "Select Flipped"
	bl_description = "Select all flipped UV islands"
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

		##Requires UV map
		if not bpy.context.object.data.uv_layers:
			return False

		#Not in Synced mode
		if bpy.context.scene.tool_settings.use_uv_select_sync:
			return False
			
		return True


	def execute(self, context):
		utilities_uv.multi_object_loop(select_flipped, context)
		return {'FINISHED'}



def select_flipped(context):
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()

	bpy.context.scene.tool_settings.uv_select_mode = 'FACE'
	bpy.ops.uv.select_all(action='SELECT')

	islands = utilities_uv.getSelectionIslands()
	
	bpy.context.scene.tool_settings.uv_select_mode = 'FACE'
	bpy.context.scene.tool_settings.use_uv_select_sync = False
	bpy.ops.uv.select_all(action='DESELECT')

	for island in islands:

		is_flipped = False
		for face in island:
			if is_flipped:
				break

			# Using 'Sum of Edges' to detect counter clockwise https://stackoverflow.com/questions/1165647/how-to-determine-if-a-list-of-polygon-points-are-in-clockwise-order
			sum = 0
			count = len(face.loops)
			for i in range(count):
				uv_A = face.loops[i][uv_layers].uv
				uv_B = face.loops[(i+1)%count][uv_layers].uv
				sum += (uv_B.x - uv_A.x) * (uv_B.y + uv_A.y)

			if sum > 0:
				# Flipped
				is_flipped = True
				break

		# Select Island if flipped
		if is_flipped:
			for face in island:
				for loop in face.loops:
					loop[uv_layers].select = True



class Island_bounds:
	faces = []
	center = Vector([0,0])
	min = Vector([0,0])
	max = Vector([0,0])

	def __init__(self, faces):
		bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
		uv_layers = bm.loops.layers.uv.verify()
		
		# Collect topology stats
		self.faces = faces

		#Select Island
		bpy.ops.uv.select_all(action='DESELECT')
		utilities_uv.set_selected_faces(faces)

		bounds = utilities_uv.getSelectionBBox()
		self.center = bounds['center']
		self.min = bounds['min']
		self.max = bounds['max']

	def isEqual(A, B):

		# Bounding Box AABB intersection?
		min_x = max(A.min.x, B.min.x)
		min_y = max(A.min.y, B.min.y)
		max_x = min(A.max.x, B.max.x)
		max_y = min(A.max.y, B.max.y)
		if not (max_x < min_x or max_y < min_y):
			return True
		
		return False


bpy.utils.register_class(op)