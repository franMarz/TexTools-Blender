import bpy

from . import settings



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
		sync = bpy.context.scene.tool_settings.use_uv_select_sync
		if sync:
			selection_mode = tuple(bpy.context.scene.tool_settings.mesh_select_mode)
			bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')

		angle = - self.angle
		if settings.bversion == 2.83 or settings.bversion == 2.91:
			angle = -angle
		bpy.ops.transform.rotate(value=-angle, orient_axis='Z', constraint_axis=(False, False, False), use_proportional_edit=False)

		if sync:
			bpy.context.scene.tool_settings.mesh_select_mode = selection_mode

		return {'FINISHED'}


bpy.utils.register_class(op)
