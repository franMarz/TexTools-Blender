import bpy



class op(bpy.types.Operator):
	bl_idname = "uv.textools_texture_remove"
	bl_label = "Remove Texture"
	bl_options = {'REGISTER', 'UNDO'}

	name : bpy.props.StringProperty(name="Image name", default="")


	def execute(self, context):
		if self.name in bpy.data.images:
			#bpy.data.batch_remove([bpy.data.images[self.name]])
			bpy.data.images.remove(bpy.data.images[self.name], do_unlink=True)
		return {'FINISHED'}


bpy.utils.register_class(op)
