import bpy

from . import utilities_texel



class op(bpy.types.Operator):
	bl_idname = "uv.textools_uv_size_get"
	bl_label = "Get Size"
	bl_description = "Get selected object's texture size"

	@classmethod
	def poll(cls, context):
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object not in bpy.context.selected_objects:
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		return True


	def execute(self, context):
		get_size(self, context)
		return {'FINISHED'}



def get_size(self, context):
	image = utilities_texel.get_object_texture_image(bpy.context.active_object)

	if not image:
		self.report({'ERROR_INVALID_INPUT'}, "No Texture found on selected object")
		return

	bpy.context.scene.texToolsSettings.size[0] = image.size[0]
	bpy.context.scene.texToolsSettings.size[1] = image.size[1]


bpy.utils.register_class(op)
