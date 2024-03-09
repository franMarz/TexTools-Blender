import bpy
import bmesh
import collections

from . import utilities_uv
from .utilities_bbox import BBox
from mathutils import Vector


class op(bpy.types.Operator):
	bl_idname = "uv.textools_align"
	bl_label = "Align"
	bl_description = "Align vertices, edges or shells"
	bl_options = {'REGISTER', 'UNDO'}
	
	direction: bpy.props.StringProperty(name="Direction", default="top", options={'HIDDEN'})

	@classmethod
	def poll(cls, context):
		if bpy.context.area.ui_type != 'UV':
			return False
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object.mode != 'EDIT':
			return False
		if not bpy.context.object.data.uv_layers:
			return False
		return True

	def execute(self, context):
		align_mode = bpy.context.scene.texToolsSettings.align_mode

		if align_mode == 'SELECTION':
			all_ob_bounds = utilities_uv.multi_object_loop(utilities_uv.getSelectionBBox, need_results=True)
			if not any(all_ob_bounds):
				return {'CANCELLED'}

			boundsAll = utilities_uv.get_BBOX_multi(all_ob_bounds)
			utilities_uv.multi_object_loop(align, context, align_mode, self.direction, boundsAll=boundsAll)
		else:
			utilities_uv.multi_object_loop(align, context, align_mode, self.direction)
		
		return {'FINISHED'}

def is_island_mode():
	scene = bpy.context.scene
	if scene.tool_settings.use_uv_select_sync:
		selection_mode = 'FACE' if scene.tool_settings.mesh_select_mode[2] else 'VERTEX'
	else:
		selection_mode = scene.tool_settings.uv_select_mode
	return selection_mode == 'FACE' or selection_mode == 'ISLAND', selection_mode

def calc_general_bbox(align_mode, direction, boundsAll):
	_, column, row = utilities_uv.get_UDIM_tile_coords(bpy.context.active_object)
	bb = collections.namedtuple('BBox', ['min', 'max', 'center'])

	if align_mode == 'SELECTION':
		general_bbox = bb(boundsAll['min'], boundsAll['max'], boundsAll['center'])
	elif align_mode == 'CURSOR':
		cursor = Vector(bpy.context.space_data.cursor_location.copy())
		general_bbox = bb(cursor, cursor, cursor)
	else:  # CANVAS
		if direction in {'bottom', 'left', 'bottomleft'}:
			canvas = Vector((column, row))
		elif direction in {'top', 'topleft'}:
			canvas = Vector((column, row + 1))
		elif direction in {'right', 'topright'}:
			canvas = Vector((column + 1, row + 1))
		elif direction == 'bottomright':
			canvas = Vector((column + 1, row))
		elif direction in {'horizontal', 'vertical', 'center'}:
			canvas = Vector((column + 0.5, row + 0.5))
		else:
			raise NotImplemented
		general_bbox = bb(canvas, canvas, canvas)
	return general_bbox


def align_islands(groups, bm, uv_layer, sync, direction, general_bbox):
	islands = utilities_uv.get_selected_islands(bm, uv_layer)

	for island in islands:
		bounds = BBox.calc_bbox_uv(island, uv_layer)
		center = bounds.center

		if direction == 'bottom':
			delta = Vector((0, (general_bbox.min - bounds.min).y))

		elif direction == 'top':
			delta = Vector((0, (general_bbox.max - bounds.max).y))

		elif direction == 'left':
			delta = Vector(((general_bbox.min - bounds.min).x, 0))

		elif direction == 'right':
			delta = Vector(((general_bbox.max - bounds.max).x, 0))

		elif direction == 'center':
			delta = Vector((general_bbox.center - center))

		elif direction == 'horizontal':
			delta = Vector((0, (general_bbox.center - center).y))

		elif direction == 'vertical':
			delta = Vector(((general_bbox.center - center).x, 0))

		elif direction == 'bottomleft':
			delta = general_bbox.min - bounds.min

		elif direction == 'topright':
			delta = general_bbox.max - bounds.max

		elif direction == 'topleft':
			delta_x = general_bbox.min - bounds.min
			delta_y = general_bbox.max - bounds.max
			delta = Vector((delta_x.x, delta_y.y))

		elif direction == 'bottomright':
			delta_x = general_bbox.max - bounds.max
			delta_y = general_bbox.min - bounds.min
			delta = Vector((delta_x.x, delta_y.y))
		else:
			raise NotImplemented

		utilities_uv.translate_island(island, uv_layer, delta)

def align_corners(groups, bm, uv_layer, sync, direction, general_bbox):
	luvs = (luv[uv_layer] for f in bm.faces if f.select for luv in f.loops if sync or luv[uv_layer].select)
	if direction in {'left', 'right', 'vertical'}:
		if direction == 'left':
			destination = general_bbox.min.x
		elif direction == 'right':
			destination = general_bbox.max.x
		else:
			destination = general_bbox.center.x

		for luv in luvs:
			luv.uv[0] = destination
	elif direction in {'top', 'bottom', 'horizontal'}:
		if direction == 'top':
			destination = general_bbox.max.y
		elif direction == 'bottom':
			destination = general_bbox.min.y
		else:
			destination = general_bbox.center.y

		for luv in luvs:
			luv.uv[1] = destination
	else:
		if direction == 'center':
			destination = general_bbox.center
		elif direction == 'bottomleft':
			destination = general_bbox.min
		elif direction == 'topright':
			destination = general_bbox.max
		elif direction == 'topleft':
			destination = Vector((general_bbox.min.x, general_bbox.max.y))
		elif direction == 'bottomright':
			destination = Vector((general_bbox.max.x, general_bbox.min.y))
		else:
			raise NotImplemented

		for luv in luvs:
			luv.uv = destination

def align(context, align_mode, direction, boundsAll=None):
	scene = bpy.context.scene
	obj = bpy.context.active_object
	bm = bmesh.from_edit_mesh(obj.data)
	uv_layer = bm.loops.layers.uv.verify()
	sync = scene.tool_settings.use_uv_select_sync

	general_bbox = calc_general_bbox(align_mode, direction, boundsAll)

	is_island_mode_, selection_mode = is_island_mode()
	if is_island_mode_:
		align_islands(None, bm, uv_layer, sync, direction, general_bbox)

	else:  # Vertices or Edges UV selection mode
		align_corners(None, bm, uv_layer, sync, direction, general_bbox)
		bmesh.update_edit_mesh(obj.data)

	# Workaround for selection not flushing properly from loops to EDGE Selection Mode, apparently since UV edge selection support was added to the UV space
	if not sync:
		bpy.ops.uv.select_mode(type='VERTEX')
	scene.tool_settings.uv_select_mode = selection_mode


bpy.utils.register_class(op)
