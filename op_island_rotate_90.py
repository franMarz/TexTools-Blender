import bpy
import bmesh

from itertools import chain
from . import settings
from . import utilities_uv
from . utilities_bbox import BBox


class op(bpy.types.Operator):
	bl_idname = "uv.textools_island_rotate_90"
	bl_label = "Rotate 90 degrees"
	bl_description = "Rotate the selection 90 degrees left or right around the global Rotation/Scaling Pivot"
	bl_options = {'REGISTER', 'UNDO'}
	
	angle : bpy.props.FloatProperty(name="Angle", options={'HIDDEN'})

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
		#bpy.ops.uv.select_linked()
		if bpy.context.scene.tool_settings.use_uv_select_sync:
			return self.island_rotate_sync_mode()

		angle = - self.angle
		if settings.bversion == 2.83 or settings.bversion == 2.91:
			angle = -angle
		bpy.ops.transform.rotate(value=-angle, orient_axis='Z', constraint_axis=(False, False, False), use_proportional_edit=False)

		return {'FINISHED'}

	def island_rotate_sync_mode(self):
		all_groups = []
		update_obj = []
		bmeshes = []  # bmesh objects must be saved, otherwise they will be deallocated
		selected_objs = utilities_uv.selected_unique_objects_in_mode_with_uv()

		for obj in selected_objs:
			bm = bmesh.from_edit_mesh(obj.data)
			uv_layer = bm.loops.layers.uv.verify()
			islands = utilities_uv.get_selected_islands(bm, uv_layer, selected=False, extend_selection_to_islands=True)

			if not islands:
				continue

			all_groups.append((islands, uv_layer))
			bmeshes.append(bm)
			update_obj.append(obj)

		if bpy.context.space_data.pivot_point in ('CENTER', 'MEDIAN'):
			general_bbox = BBox()
			for islands, uv_layer in all_groups:
				bbox = BBox.calc_bbox_uv(chain.from_iterable(islands), uv_layer)
				general_bbox.union(bbox)

			pivot = general_bbox.center
			for islands, uv_layer in all_groups:
				utilities_uv.rotate_island(chain.from_iterable(islands), uv_layer, self.angle, pivot)

		if bpy.context.space_data.pivot_point == 'CURSOR':
			pivot = bpy.context.space_data.cursor_location
			for islands, uv_layer in all_groups:
				utilities_uv.rotate_island(chain.from_iterable(islands), uv_layer, self.angle, pivot)

		if bpy.context.space_data.pivot_point == 'INDIVIDUAL_ORIGINS':
			for islands, uv_layer in all_groups:
				for island in islands:
					pivot = BBox.calc_bbox_uv(island, uv_layer).center
					utilities_uv.rotate_island(island, uv_layer, self.angle, pivot)

		if not update_obj:
			return {'CANCELLED'}

		for obj in update_obj:
			bmesh.update_edit_mesh(obj.data)
		return {'FINISHED'}


bpy.utils.register_class(op)
