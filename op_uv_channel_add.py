import bpy

from . import utilities_ui



class op(bpy.types.Operator):
	bl_idname = "uv.textools_uv_channel_add"
	bl_label = "Add UV Channel"
	bl_description = "Add a new UV channel with smart UV projected UV's and padding."
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		if len(bpy.context.selected_objects) != 1:
			return False
		return True


	def execute(self, context):
		if len( bpy.context.object.data.uv_layers ) == 0:
			# Create first UV channel
			if bpy.context.active_object.mode != 'EDIT':
				bpy.ops.object.mode_set(mode='EDIT')

			# Smart project UV's
			bpy.ops.mesh.select_all(action='SELECT')
			bpy.ops.uv.smart_project(
				angle_limit=65, 
				island_margin=0.5, 
				user_area_weight=0, 
				use_aspect=True, 
				stretch_to_bounds=True
			)
			# Re-Apply padding as normalized values
			bpy.ops.uv.select_all(action='SELECT')
			bpy.ops.uv.pack_islands(margin=utilities_ui.get_padding())

		else:
			# Add new UV channel based on last
			bpy.ops.mesh.uv_texture_add()

		# Get current index
		index = len(bpy.context.object.data.uv_layers)-1
		bpy.context.object.data.uv_layers.active_index = index
		bpy.context.scene.texToolsSettings.uv_channel = str(index)

		return {'FINISHED'}


bpy.utils.register_class(op)
