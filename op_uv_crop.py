import bpy
import bmesh
from mathutils import Vector

from . import utilities_uv
from . import utilities_ui



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
		crop(self, context)
		return {'FINISHED'}



def crop(self, context, distort=False, selection=None):
	selected_obs = [ob for ob in bpy.context.selected_objects if ob.type == 'MESH']
	sync = bpy.context.scene.tool_settings.use_uv_select_sync
	if sync:
		selection_mode = tuple(bpy.context.scene.tool_settings.mesh_select_mode)
		bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
	else:
		selection_mode = bpy.context.scene.tool_settings.uv_select_mode
		# Clean selection so that only entirely selected UV faces remain selected
		bpy.ops.uv.select_split()

	if len(selected_obs) <= 1:
		bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
		uv_layers = bm.loops.layers.uv.verify()

		if selection is None:
			if sync:
				selection = [f for f in bm.faces if f.select]
			else:
				selection = [f for f in bm.faces if f.loops[0][uv_layers].select and f.select]
		if not selection:
			return {'CANCELLED'}

		boundsAll = utilities_uv.get_BBOX(selection, bm, uv_layers)

	elif len(selected_obs) > 1:
		unique_selected_obs = [ob for ob in bpy.context.objects_in_mode_unique_data if ob.type == 'MESH']
		bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
		bpy.ops.object.select_all(action='DESELECT')
		bpy.context.view_layer.objects.active = unique_selected_obs[0]
		for o in unique_selected_obs:
			o.select_set(True)
		bpy.ops.object.mode_set(mode='EDIT', toggle=False)
		all_ob_bounds = utilities_uv.multi_object_loop(utilities_uv.getSelectionBBox, need_results=True)
		if not any(all_ob_bounds):
			return {'CANCELLED'}
		boundsAll = utilities_uv.get_BBOX_multi(all_ob_bounds)

	prepivot = bpy.context.space_data.pivot_point
	precursor = bpy.context.space_data.cursor_location.copy()
	bpy.context.space_data.pivot_point = 'CURSOR'
	bpy.context.space_data.cursor_location = (0.0, 0.0)

	padding = utilities_ui.get_padding()

	# Scale to fit bounds

	scale_u = (1.0-padding) / boundsAll['width']
	scale_v = (1.0-padding) / boundsAll['height']
	if not distort:
		scale_u = scale_v = min(scale_u, scale_v)

	bpy.ops.transform.resize(value=(scale_u, scale_v, 1), constraint_axis=(False, False, False), mirror=False, use_proportional_edit=False)

	# Reposition

	delta_position = Vector((padding/2 - scale_u*boundsAll['min'].x, padding/2 - scale_v*boundsAll['min'].y, 0))

	udim_tile, column, row = utilities_uv.get_UDIM_tile_coords(bpy.context.active_object)

	if udim_tile != 1001:
		delta_position += Vector((column, row, 0))

	bpy.ops.transform.translate(value=delta_position, mirror=False, use_proportional_edit=False)

	if len(selected_obs) > 1:
		bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
		for o in selected_obs:
			o.select_set(True)
		bpy.ops.object.mode_set(mode='EDIT', toggle=False)

	bpy.context.space_data.pivot_point = prepivot
	bpy.context.space_data.cursor_location = precursor

	if sync:
		bpy.context.scene.tool_settings.mesh_select_mode = selection_mode
	else:
		# Workaround for selection not flushing properly from loops to EDGE Selection Mode, apparently since UV edge selection support was added to the UV space
		bpy.ops.uv.select_mode(type='VERTEX')
		bpy.context.scene.tool_settings.uv_select_mode = selection_mode


bpy.utils.register_class(op)
