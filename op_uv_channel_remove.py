import bpy
from . import utilities_uv



class op(bpy.types.Operator):
	bl_idname = "uv.textools_uv_channel_remove"
	bl_label = "Remove UV Channel"
	bl_description = "Remove the active UV channel from all the selected Objects"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		if not bpy.context.object.data.uv_layers:
			return False
		return True


	def execute(self, context):
		premode = bpy.context.active_object.mode
		utilities_uv.multi_object_loop(removeuvs, self, context)
		bpy.ops.object.mode_set(mode=premode)
		return {'FINISHED'}



def removeuvs(self, context):
	if bpy.context.object.data.uv_layers:
		# Remove active UV channel
		bpy.context.active_object.data.uv_layers.remove(bpy.context.object.data.uv_layers.active)

	# Get current index
	index = len(bpy.context.object.data.uv_layers)-1
	if index >= 0:
		bpy.context.object.data.uv_layers.active_index = index
		bpy.context.scene.texToolsSettings.uv_channel = str(index)
		bpy.context.active_object.data.uv_layers[0].active_render = True
