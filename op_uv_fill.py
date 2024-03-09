import bpy
import bmesh
import mathutils

from . import utilities_uv
from . import op_uv_crop
from . import settings
from . utilities_bbox import BBox


class op(bpy.types.Operator):
	bl_idname = "uv.textools_uv_fill"
	bl_label = "Fill"
	bl_description = "Fill the 0-1 UV area with the selected UVs"
	bl_options = {'REGISTER', 'UNDO'}

	align: bpy.props.BoolProperty(name='Align', description="Align orientation", default=False)

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
		selected_obs = utilities_uv.selected_unique_objects_in_mode_with_uv()
		sync = bpy.context.scene.tool_settings.use_uv_select_sync
		if sync:
			selection_mode = tuple(bpy.context.scene.tool_settings.mesh_select_mode)
			bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
		else:
			# Clean selection so that only entirely selected UV faces remain selected
			bpy.ops.uv.select_split()

		points = []
		bmesh_ref_count_save = []
		for obj in selected_obs:
			bm = bmesh.from_edit_mesh(obj.data)
			uv_layers = bm.loops.layers.uv.verify()
			if sync:
				selection = (f for f in bm.faces if f.select)
			else:
				selection = (f for f in bm.faces if f.loops[0][uv_layers].select and f.select)
			points.extend(l[uv_layers].uv for f in selection for l in f.loops)
			bmesh_ref_count_save.append(bm)

		if not points:
			return {'CANCELLED'}

		points = [points[i] for i in mathutils.geometry.convex_hull_2d(points)]  # It's relevant to reduce points
		rotatable = False
		if self.align:
			angle = utilities_uv.calc_min_align_angle_pt(points)
			rotatable = abs(angle) > 0.00001
			if rotatable:
				prepivot = bpy.context.space_data.pivot_point
				bpy.context.space_data.pivot_point = 'CENTER'
				if not (settings.bversion == 2.83 or settings.bversion == 2.91):
					angle = -angle
				bpy.ops.transform.rotate(value=angle)
				bpy.context.space_data.pivot_point = prepivot

		if self.align and rotatable:
			general_bbox = None
		else:
			general_bbox = BBox.calc_bbox(points)
			if not general_bbox.is_valid:
				self.report({'ERROR'}, "Zero area")
				return {'CANCELLED'}

		# Expand UV selection of all selected objects towards the UV space 0-1 limits
		ret = op_uv_crop.crop(self, distort=True, general_bbox=general_bbox)

		if sync:
			bpy.context.scene.tool_settings.mesh_select_mode = selection_mode

		return ret


bpy.utils.register_class(op)
