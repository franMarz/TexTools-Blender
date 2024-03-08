import bpy
import bmesh

from . import utilities_uv
from .utilities_bbox import BBox
from mathutils import Vector

class op(bpy.types.Operator):
	bl_idname = "uv.textools_island_centralize"
	bl_label = "Centralize"
	bl_description = "Move selected islands the closest possible to the 0-1 UV area without changes in the textured object"
	bl_options = {'REGISTER', 'UNDO'}
	
	@classmethod
	def poll(cls, context):
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object.mode != 'EDIT':
			return False
		return True

	def execute(self, context):
		_, column, row = utilities_uv.get_UDIM_tile_coords(bpy.context.active_object)
		return self.centralize(column, row)

	@staticmethod
	def centralize(column, row):
		selected_objs = utilities_uv.selected_unique_objects_in_mode_with_uv()
		update_obj = []
		for obj in selected_objs:
			bm = bmesh.from_edit_mesh(obj.data)
			uv_layer = bm.loops.layers.uv.verify()
			islands = utilities_uv.get_selected_islands(bm, uv_layer, selected=False, extend_selection_to_islands=True)

			if not islands:
				continue

			changed = False
			for island in islands:
				center = BBox.calc_bbox_uv(island, uv_layer).center
				delta = Vector((round(-center.x + 0.5) + column, round(-center.y + 0.5) + row))
				if delta != Vector((0, 0)):
					changed = True
					utilities_uv.translate_island(island, uv_layer, delta)
			if changed:
				update_obj.append(obj)
				
		if not update_obj:
			return {'CANCELLED'}

		for obj in update_obj:
			bmesh.update_edit_mesh(obj.data)
		return {'FINISHED'}


bpy.utils.register_class(op)
