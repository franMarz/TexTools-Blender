import bpy

import os, sys, subprocess



class op(bpy.types.Operator):
	bl_idname = "uv.textools_texture_open"
	bl_label = "Open Texture"
	bl_description = "Open the texture on the system"

	name : bpy.props.StringProperty(
		name="image name",
		default = ""
	)

	@classmethod
	def poll(cls, context):
		return True
	

	def execute(self, context):
		open_texture(self, context)
		return {'FINISHED'}



def open_texture(self, context):
	if self.name in bpy.data.images:
		image = bpy.data.images[self.name]
		
		if image.filepath != "":
			path = bpy.path.abspath(image.filepath)
			# https://meshlogic.github.io/posts/blender/addons/extra-image-list/
			# https://docs.blender.org/api/blender_python_api_2_78_release/bpy.ops.image.html
			print("Open: {}".format(path))

			if sys.platform == "win32":
				os.startfile(path)
			else:
				opener ="open" if sys.platform == "darwin" else "xdg-open"
				subprocess.call([opener, path])


bpy.utils.register_class(op)
