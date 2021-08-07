import bpy

from . import settings



class op(bpy.types.Operator):
	bl_idname = "uv.textools_island_rotate_90"
	bl_label = "Rotate 90 degrees"
	bl_description = "Rotate the selected UV island 90 degrees left or right"
	bl_options = {'REGISTER', 'UNDO'}
	
	angle : bpy.props.FloatProperty(name="Angle")

	@classmethod
	def poll(cls, context):
		if bpy.context.area.type != 'IMAGE_EDITOR':
			return False
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		if bpy.context.active_object.mode != 'EDIT':
			return False
		if not bpy.context.object.data.uv_layers:
			return False
		if bpy.context.scene.tool_settings.use_uv_select_sync:
			return False
		return True


	def execute(self, context):
		bpy.ops.uv.select_linked()

		angle = - self.angle
		if settings.bversion == 2.83 or settings.bversion == 2.91:
			angle = -angle
		bpy.ops.transform.rotate(value=-angle, orient_axis='Z', constraint_axis=(False, False, False), use_proportional_edit=False)

		return {'FINISHED'}


bpy.utils.register_class(op)
