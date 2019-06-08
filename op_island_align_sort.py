import bpy
import bmesh
import operator
import math

from mathutils import Vector
from collections import defaultdict


from . import utilities_uv
import imp
imp.reload(utilities_uv)


class op(bpy.types.Operator):
	bl_idname = "uv.textools_island_align_sort"
	bl_label = "Align & Sort"
	bl_description = "Rotates UV islands to minimal bounds and sorts them horizontal or vertical"
	bl_options = {'REGISTER', 'UNDO'}


	is_vertical : bpy.props.BoolProperty(description="Vertical or Horizontal orientation", default=True)
	padding : bpy.props.FloatProperty(description="Padding between UV islands", default=0.05)

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
			return False 	#self.report({'WARNING'}, "Object must have more than one UV map")

		#Not in Synced mode
		if bpy.context.scene.tool_settings.use_uv_select_sync:
			return False

		return True


	def execute(self, context):
		main(context, self.is_vertical, self.padding)
		return {'FINISHED'}


def main(context, isVertical, padding):
	print("Executing IslandsAlignSort main {}".format(padding))
   	
	#Store selection
	utilities_uv.selection_store()

	if bpy.context.tool_settings.transform_pivot_point != 'CURSOR':
		bpy.context.tool_settings.transform_pivot_point = 'CURSOR'

	#Only in Face or Island mode
	if bpy.context.scene.tool_settings.uv_select_mode is not 'FACE' or 'ISLAND':
		bpy.context.scene.tool_settings.uv_select_mode = 'FACE'

	bm = bmesh.from_edit_mesh(bpy.context.active_object.data);
	uv_layers = bm.loops.layers.uv.verify();
	

	boundsAll = utilities_uv.getSelectionBBox()


	islands = utilities_uv.getSelectionIslands()
	allSizes = {}	#https://stackoverflow.com/questions/613183/sort-a-python-dictionary-by-value
	allBounds = {}

	print("Islands: "+str(len(islands))+"x")

	bpy.context.window_manager.progress_begin(0, len(islands))

	#Rotate to minimal bounds
	for i in range(0, len(islands)):
		alignIslandMinimalBounds(uv_layers, islands[i])

		# Collect BBox sizes
		bounds = utilities_uv.getSelectionBBox()
		allSizes[i] = max(bounds['width'], bounds['height']) + i*0.000001;#Make each size unique
		allBounds[i] = bounds;
		print("Rotate compact:  "+str(allSizes[i]))

		bpy.context.window_manager.progress_update(i)

	bpy.context.window_manager.progress_end()


	#Position by sorted size in row
	sortedSizes = sorted(allSizes.items(), key=operator.itemgetter(1))#Sort by values, store tuples
	sortedSizes.reverse()
	offset = 0.0
	for sortedSize in sortedSizes:
		index = sortedSize[0]
		island = islands[index]
		bounds = allBounds[index]

		#Select Island
		bpy.ops.uv.select_all(action='DESELECT')
		utilities_uv.set_selected_faces(island)
		
		#Offset Island
		if(isVertical):
			delta = Vector((boundsAll['min'].x - bounds['min'].x, boundsAll['max'].y - bounds['max'].y));
			bpy.ops.transform.translate(value=(delta.x, delta.y-offset, 0))
			offset += bounds['height']+padding
		else:
			print("Horizontal")
			delta = Vector((boundsAll['min'].x - bounds['min'].x, boundsAll['max'].y - bounds['max'].y));
			bpy.ops.transform.translate(value=(delta.x+offset, delta.y, 0))
			offset += bounds['width']+padding


	#Restore selection
	utilities_uv.selection_restore()


def alignIslandMinimalBounds(uv_layers, faces):
	# Select Island
	bpy.ops.uv.select_all(action='DESELECT')
	utilities_uv.set_selected_faces(faces)

	steps = 8
	angle = 45;	# Starting Angle, half each step

	bboxPrevious = utilities_uv.getSelectionBBox()

	for i in range(0, steps):
		# Rotate right
		bpy.ops.transform.rotate(value=(angle * math.pi / 180), orient_axis='Z')
		bbox = utilities_uv.getSelectionBBox()

		if i == 0:
			sizeA = bboxPrevious['width'] * bboxPrevious['height']
			sizeB = bbox['width'] * bbox['height']
			if abs(bbox['width'] - bbox['height']) <= 0.0001 and sizeA < sizeB:
				# print("Already squared")
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

bpy.utils.register_class(op)