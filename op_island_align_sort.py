import bpy
import bmesh
import operator

from itertools import chain
from mathutils import Vector
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
		if bpy.context.active_object.mode != 'EDIT':
			return False
		if bpy.context.area.type != 'IMAGE_EDITOR':
			return False
		if not bpy.context.object.data.uv_layers:
			return False
		if bpy.context.scene.tool_settings.use_uv_select_sync:
			return False
		return True


	def execute(self, context):
		all_ob_bounds = utilities_uv.multi_object_loop(main, context, self.is_vertical, self.padding, need_results=True)

		if not any(all_ob_bounds):
			return {'CANCELLED'}

		utilities_uv.multi_object_loop(relocate, context, self.is_vertical, self.padding, all_ob_bounds, ob_num=0)
		return {'FINISHED'}



def main(context, isVertical, padding):
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()

	selected_faces = [face for face in bm.faces if any([loop[uv_layers].select for loop in face.loops]) and face.select]
	if not selected_faces:
		return {}

	boundsAll = utilities_uv.get_BBOX(selected_faces, bm, uv_layers)
	islands = utilities_uv.getSelectionIslands(bm, uv_layers, selected_faces)
	allSizes = {}
	allBounds = {}

	#Rotate to minimal bounds
	for i, island in enumerate(islands):
		utilities_uv.alignMinimalBounds(bm, uv_layers, island)

		#Collect BBox sizes
		bounds = utilities_uv.get_BBOX(island, bm, uv_layers)
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

		#Offset Island
		delta = Vector((boundsAll['min'].x - bounds['min'].x, boundsAll['max'].y - bounds['max'].y))
		if(isVertical):
			for face in island:
				for loop in face.loops:
					loop[uv_layers].uv += Vector((delta.x, delta.y-offset))
			offset += bounds['height'] + padding
		else:
			for face in island:
				for loop in face.loops:
					loop[uv_layers].uv += Vector((delta.x+offset, delta.y))
			offset += bounds['width'] + padding

	return utilities_uv.get_BBOX(chain.from_iterable(islands), bm, uv_layers)



def relocate(context, isVertical, padding, all_ob_bounds, ob_num=0):
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()

	islands = utilities_uv.getSelectionIslands(bm, uv_layers)

	if ob_num > 0 :
		if all_ob_bounds[ob_num]:
			offset = 0.0
			origin = Vector((0,0))
			for i in range(0, ob_num):
				if all_ob_bounds[i]:
					if isVertical:
						offset += all_ob_bounds[i]['height'] + padding
					else:
						offset += all_ob_bounds[i]['width'] + padding
			for i in range(0, ob_num+1):
				if all_ob_bounds[i]:
					origin.x = all_ob_bounds[i]['min'].x
					origin.y = all_ob_bounds[i]['max'].y
					break

			delta = Vector((origin.x - all_ob_bounds[ob_num]['min'].x, origin.y - all_ob_bounds[ob_num]['max'].y))
			if isVertical:
				for island in islands:
					for face in island:
						for loop in face.loops:
							loop[uv_layers].uv += Vector((delta.x, delta.y-offset))
			else:
				for island in islands:
					for face in island:
						for loop in face.loops:
							loop[uv_layers].uv += Vector((delta.x+offset, delta.y))


bpy.utils.register_class(op)
