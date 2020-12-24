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
		utilities_uv.multi_object_loop(main, context, self.is_vertical, self.padding)

		all_ob_bounds = utilities_uv.multi_object_loop(utilities_uv.getSelectionBBox, need_results=True)
		utilities_uv.multi_object_loop(relocate, context, self.is_vertical, self.padding, all_ob_bounds, ob_num=0)
		
		return {'FINISHED'}


def main(context, isVertical, padding):
	print("Executing IslandsAlignSort main {}".format(padding))

	#Store selection
	utilities_uv.selection_store()

	bpy.context.tool_settings.transform_pivot_point = 'CURSOR'
	bpy.context.scene.tool_settings.uv_select_mode = 'FACE'

	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()
	
	boundsAll = utilities_uv.getSelectionBBox()
	islands = utilities_uv.getSelectionIslands()
	allSizes = {}	#https://stackoverflow.com/questions/613183/sort-a-python-dictionary-by-value
	allBounds = {}

	#Rotate to minimal bounds
	for i in range(0, len(islands)):
		# Select Island
		bpy.ops.uv.select_all(action='DESELECT')
		utilities_uv.set_selected_faces(islands[i])

		utilities_uv.alignMinimalBounds(uv_layers=uv_layers)

		# Collect BBox sizes
		bounds = utilities_uv.getSelectionBBox()
		allSizes[i] = max(bounds['width'], bounds['height']) + i*0.000001	#Make each size unique
		allBounds[i] = bounds

	#Position by sorted size in row
	sortedSizes = sorted(allSizes.items(), key=operator.itemgetter(1))	#Sort by values, store tuples
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
			delta = Vector((boundsAll['min'].x - bounds['min'].x, boundsAll['max'].y - bounds['max'].y))
			bpy.ops.transform.translate(value=(delta.x, delta.y-offset, 0))
			offset += bounds['height']+padding
		else:
			delta = Vector((boundsAll['min'].x - bounds['min'].x, boundsAll['max'].y - bounds['max'].y))
			bpy.ops.transform.translate(value=(delta.x+offset, delta.y, 0))
			offset += bounds['width']+padding

	#Restore selection
	utilities_uv.selection_restore()


def relocate(context, isVertical, padding, all_ob_bounds, ob_num=0):

	if ob_num > 0 :
		if len(all_ob_bounds[ob_num]) > 0:
			offset = 0.0
			origin = Vector((0,0))
			for i in range(0, ob_num):
				if len(all_ob_bounds[i]) > 0:
					if isVertical:
						offset += all_ob_bounds[i]['height']+padding
					else:
						offset += all_ob_bounds[i]['width']+padding
			for i in range(0, ob_num+1):
				if len(all_ob_bounds[i]) > 0:
					origin.x = all_ob_bounds[i]['min'].x
					origin.y = all_ob_bounds[i]['max'].y
					break
			
			delta = Vector((origin.x - all_ob_bounds[ob_num]['min'].x, origin.y - all_ob_bounds[ob_num]['max'].y))
			if isVertical:
				bpy.ops.transform.translate(value=(delta.x, delta.y-offset, 0))
			else:
				bpy.ops.transform.translate(value=(delta.x+offset, delta.y, 0))


bpy.utils.register_class(op)