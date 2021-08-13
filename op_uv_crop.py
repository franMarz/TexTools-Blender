import bpy
import bmesh
from mathutils import Vector

from . import utilities_uv
from . import utilities_ui



class op(bpy.types.Operator):
	bl_idname = "uv.textools_uv_crop"
	bl_label = "Crop"
	bl_description = "Crop UV area to selected UV faces"
	bl_options = {'REGISTER', 'UNDO'}
	
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
			return False
		#Not in Synced mode
		if bpy.context.scene.tool_settings.use_uv_select_sync:
			return False
		return True
	

	def execute(self, context):
		crop(self, context)
		return {'FINISHED'}



def crop(self, context, distort=False, selection=None):

	selected_obs = [ob for ob in bpy.context.selected_objects if ob.type == 'MESH']
	# Clean selection so that only entirely selected UV faces remain selected
	bpy.ops.uv.select_split()

	if len(selected_obs) <= 1:
		bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
		uv_layers = bm.loops.layers.uv.verify()
		if selection is None:
			selection = utilities_uv.get_selected_uv_faces(bm, uv_layers)
		if not selection:
			return {'CANCELLED'}
		boundsAll = utilities_uv.get_BBOX(selection, bm, uv_layers)

	elif len(selected_obs) > 1:
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

	delta_position = Vector((padding/2 - scale_u*boundsAll['min'].x, 1-padding/2 - scale_v*boundsAll['min'].y - scale_v*boundsAll['height'], 0))

	udim_tile, column, row = utilities_uv.get_UDIM_tile_coords(bpy.context.active_object)

	if udim_tile != 1001:
		delta_position += Vector((column, row, 0))

	bpy.ops.transform.translate(value=delta_position, mirror=False, use_proportional_edit=False)

	bpy.context.space_data.pivot_point = prepivot
	bpy.context.space_data.cursor_location = precursor


bpy.utils.register_class(op)
