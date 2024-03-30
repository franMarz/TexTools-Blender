import bpy
import bmesh
from mathutils import Vector

from . import utilities_uv
from . import utilities_ui
from . utilities_bbox import BBox


class op(bpy.types.Operator):
	bl_idname = "uv.textools_uv_crop"
	bl_label = "Crop"
	bl_description = "Frame the selected UVs to the 0-1 UV area"
	bl_options = {'REGISTER', 'UNDO'}

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
		return crop(self)


def crop(self, distort=False, general_bbox=None):
	selected_obs = utilities_uv.selected_unique_objects_in_mode_with_uv()
	sync = bpy.context.scene.tool_settings.use_uv_select_sync
	if sync:
		selection_mode = tuple(bpy.context.scene.tool_settings.mesh_select_mode)
		bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
	else:
		selection_mode = bpy.context.scene.tool_settings.uv_select_mode
		# Clean selection so that only entirely selected UV faces remain selected
		bpy.ops.uv.select_split()

	if general_bbox is None:
		general_bbox = BBox()
		for obj in selected_obs:
			bm = bmesh.from_edit_mesh(obj.data)
			uv_layers = bm.loops.layers.uv.verify()
			if sync:
				selection = (f for f in bm.faces if f.select)
			else:
				selection = (f for f in bm.faces if f.loops[0][uv_layers].select and f.select)
			bbox = BBox.calc_bbox_uv(selection, uv_layers)
			general_bbox.union(bbox)

		if not general_bbox.is_valid:
			self.report({'ERROR'}, "Zero area")
			return {'CANCELLED'}

	prepivot = bpy.context.space_data.pivot_point
	precursor = bpy.context.space_data.cursor_location.copy()
	bpy.context.space_data.pivot_point = 'CURSOR'
	bpy.context.space_data.cursor_location = (0.0, 0.0)

	padding = utilities_ui.get_padding()

	# Scale to fit bounds

	scale_u = (1.0-padding) / general_bbox.width
	scale_v = (1.0-padding) / general_bbox.height

	if not distort:
		scale_u = scale_v = min(scale_u, scale_v)

	bpy.ops.transform.resize(value=(scale_u, scale_v, 1), constraint_axis=(False, False, False), mirror=False, use_proportional_edit=False)

	# Reposition
	delta_position = Vector((padding/2 - scale_u*general_bbox.min.x, padding/2 - scale_v*general_bbox.min.y, 0))

	_, column, row = utilities_uv.get_UDIM_tile_coords(bpy.context.active_object)
	delta_position += Vector((column, row, 0))
	bpy.ops.transform.translate(value=delta_position, mirror=False, use_proportional_edit=False)

	bpy.context.space_data.pivot_point = prepivot
	bpy.context.space_data.cursor_location = precursor
	if sync:
		bpy.context.scene.tool_settings.mesh_select_mode = selection_mode
	else:
		# Workaround for selection not flushing properly from loops to EDGE Selection Mode, apparently since UV edge selection support was added to the UV space
		bpy.ops.uv.select_mode(type='VERTEX')
		bpy.context.scene.tool_settings.uv_select_mode = selection_mode
	return {'FINISHED'}
