import bpy
import bmesh

from mathutils import Vector
from . import utilities_uv
from .utilities_bbox import BBox

class op(bpy.types.Operator):
	bl_idname = "uv.textools_island_align_sort"
	bl_label = "Align & Sort"
	bl_description = "Rotate UV islands to minimal bounds and sort them horizontally or vertically"
	bl_options = {'REGISTER', 'UNDO'}

	is_vertical: bpy.props.BoolProperty(name='Vertical', description="Vertical or Horizontal orientation", default=True)
	align: bpy.props.BoolProperty(name='Align', description="Align Island orientation", default=True)
	padding: bpy.props.FloatProperty(name='Padding', description="Padding between UV islands", default=0.05)

	@classmethod
	def poll(cls, context):
		if bpy.context.area.ui_type != 'UV':
			return False
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		if bpy.context.active_object.mode != 'EDIT':
			return False
		if not bpy.context.object.data.uv_layers:
			return False
		return True

	def execute(self, context):
		general_bbox = BBox()
		all_groups = []
		bmeshes = [] # bmesh objects must be saved, otherwise they will disappear from the scope and cause an error
		selected_objs = utilities_uv.selected_unique_objects_in_mode_with_uv()
		for obj in selected_objs:
			bm = bmesh.from_edit_mesh(obj.data)
			uv_layer = bm.loops.layers.uv.verify()
			islands = utilities_uv.get_selected_islands(bm, uv_layer, selected=False, extend_selection_to_islands=True)
			if not islands:
				continue
			for i, island in enumerate(islands):
				bbox_pre = BBox.calc_bbox_uv(island, uv_layer)
				general_bbox.union(bbox_pre)
				if self.align:
					angle = utilities_uv.calc_min_align_angle(island, uv_layer)
					utilities_uv.rotate_island(island, uv_layer, angle)

				bbox = BBox.calc_bbox_uv(island, uv_layer) if self.align else bbox_pre
				all_groups.append((island, bbox, uv_layer))
			bmeshes.append(bm)

		all_groups.sort(key=lambda x: x[1].max_lenght, reverse=True)

		# transform
		if self.is_vertical:
			margin_x = general_bbox.xmin
			margin_y = general_bbox.ymin

			for island, bbox, uv_layer in all_groups:
				delta = Vector((margin_x, margin_y)) - bbox.left_bottom
				utilities_uv.translate_island(island, uv_layer, delta)
				margin_y += self.padding + bbox.height
		else:
			margin_x = general_bbox.xmin
			margin_y = general_bbox.ymin

			for island, bbox, uv_layer in all_groups:
				delta = Vector((margin_x, margin_y)) - bbox.min
				utilities_uv.translate_island(island, uv_layer, delta)
				margin_x += self.padding + bbox.width

		for obj in selected_objs:
			bmesh.update_edit_mesh(obj.data)

		return {'FINISHED'}


bpy.utils.register_class(op)
