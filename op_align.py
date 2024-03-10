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
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object.mode != 'EDIT':
			return False
		return True

	def execute(self, context):
		sync = bpy.context.scene.tool_settings.use_uv_select_sync
		all_groups = []  # islands, bboxes, uv_layer or corners, uv_layer
		update_obj = []
		general_bbox = BBox()
		bmeshes_refcount_safe = []

		selected_objs = utilities_uv.selected_unique_objects_in_mode_with_uv()
		align_mode = bpy.context.scene.texToolsSettings.align_mode
		_is_island_mode = is_island_mode()

		for obj in selected_objs:
			bm = bmesh.from_edit_mesh(obj.data)
			uv_layer = bm.loops.layers.uv.verify()
			if _is_island_mode:
				islands = utilities_uv.get_selected_islands(bm, uv_layer, selected=True)
				if not islands:
					continue
				for island in islands:
					bbox = BBox.calc_bbox_uv(island, uv_layer)
					general_bbox.union(bbox)

					all_groups.append((island, bbox, uv_layer))
				bmeshes_refcount_safe.append(bm)
				update_obj.append(obj)
			else:
				if sync:
					corners = [luv for f in bm.faces if f.select for luv in f.loops]
				else:
					corners = [luv for f in bm.faces if f.select for luv in f.loops if luv[uv_layer].select]
				if not corners:
					continue
				if align_mode == 'SELECTION':
					bbox = BBox.calc_bbox_uv(corners, uv_layer, are_loops=True)
					general_bbox.union(bbox)

				all_groups.append((corners, uv_layer))
				bmeshes_refcount_safe.append(bm)
				update_obj.append(obj)

		if not update_obj:
			self.report({'ERROR'}, "No object for manipulate")
			return {'CANCELLED'}
		if align_mode == 'SELECTION' and not general_bbox.is_valid:
			self.report({'ERROR'}, "Zero Area")
			return {'CANCELLED'}

		general_bbox = recalc_general_bbox_from_align_mode(align_mode, self.direction, general_bbox)
		if is_island_mode():
			align_islands(all_groups, self.direction, general_bbox)
		else:  # Vertices or Edges UV selection mode
			align_corners(all_groups, self.direction, general_bbox)

		for obj in update_obj:
			bmesh.update_edit_mesh(obj.data)

		return {'FINISHED'}


def align_islands(groups, direction, general_bbox):
	for island, bounds, uv_layer in groups:
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
		if delta != Vector((0, 0)):
			utilities_uv.translate_island(island, uv_layer, delta)

def align_corners(groups, direction, general_bbox):
	for luvs, uv_layer in groups:
		if direction in {'left', 'right', 'vertical'}:
			if direction == 'left':
				destination = general_bbox.min.x
			elif direction == 'right':
				destination = general_bbox.max.x
			else:
				destination = general_bbox.center.x

			for luv in luvs:
				luv[uv_layer].uv[0] = destination
		elif direction in {'top', 'bottom', 'horizontal'}:
			if direction == 'top':
				destination = general_bbox.max.y
			elif direction == 'bottom':
				destination = general_bbox.min.y
			else:
				destination = general_bbox.center.y

			for luv in luvs:
				luv[uv_layer].uv[1] = destination
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
				luv[uv_layer].uv = destination


def is_island_mode():
	scene = bpy.context.scene
	if scene.tool_settings.use_uv_select_sync:
		selection_mode = 'FACE' if scene.tool_settings.mesh_select_mode[2] else 'VERTEX'
	else:
		selection_mode = scene.tool_settings.uv_select_mode
	return selection_mode in ('FACE', 'ISLAND')

def recalc_general_bbox_from_align_mode(align_mode, direction, general_bbox):
	bb = collections.namedtuple('BBox', ['min', 'max', 'center'])

	if align_mode == 'SELECTION':
		general_bbox = bb(general_bbox.min, general_bbox.max, general_bbox.center)
	elif align_mode == 'CURSOR':
		cursor = Vector(bpy.context.space_data.cursor_location.copy())
		general_bbox = bb(cursor, cursor, cursor)
	else:  # CANVAS
		_, column, row = utilities_uv.get_UDIM_tile_coords(bpy.context.active_object)
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


bpy.utils.register_class(op)
