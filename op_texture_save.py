import bpy
import bmesh
import operator
import math
import os

from bpy.props import *
from . import settings
from . import utilities_bake


class op(bpy.types.Operator):
	bl_idname = "uv.textools_texture_save"
	bl_label = "Save Texture"
	bl_description = "Save the texture"

	name : bpy.props.StringProperty(
		name="image name",
		default = ""
	)

	# Properties used by the file browser
	# filepath = bpy.props.StringProperty(subtype="FILE_PATH")
	# http://nullege.com/codes/show/src%40b%40l%40blenderpython-HEAD%40scripts%40addons_extern%40io_scene_valvesource%40import_smd.py/90/bpy.context.window_manager.fileselect_add/python
	filepath : bpy.props.StringProperty(name="myName.png", description="Texture filepath", maxlen=1024, default="bla bla.png")
	filter_folder : BoolProperty(name="Filter folders", description="", default=True, options={'HIDDEN'})
	filter_glob : StringProperty(default="*.png;*.tga;*.jpg;*.tif;*.exr", options={'HIDDEN'})

	def invoke(self, context, event):
		# if self.filepath == "":
		# 	self.filepath = bpy.context.scene.FBXBundleSettings.path
		# blend_filepath = context.blend_data.filepath
		# https://blender.stackexchange.com/questions/6159/changing-default-text-value-in-file-dialogue
		context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}


	def draw(self, context):
		layout = self.layout

		layout.label(text="Choose your Unity Asset directory")


	@classmethod
	def poll(cls, context):
		return True

	def execute(self, context):
		save_texture(self.filepath)
		return {'FINISHED'}



def save_texture(path):
	print("Save image.. "+path)





# class op(bpy.types.Operator):
# 	bl_idname = "uv.textools_texture_save"
# 	bl_label = "Save Texture"
# 	bl_description = "Save the texture"

# 	name = bpy.props.StringProperty(
# 		name="image name",
# 		default = ""
# 	)

# 	@classmethod
# 	def poll(cls, context):
# 		return True
	
# 	def execute(self, context):
# 		save_texture(self, context)
# 		return {'FINISHED'}



		



'''
class op_ui_image_save(bpy.types.Operator):
	bl_idname = "uv.textools_ui_image_save"
	bl_label = "Save image"
	bl_description = "Save this image"

	image_name = bpy.props.StringProperty(
		name="image name",
		default = ""
	)

	@classmethod
	def poll(cls, context):
		return True

	def execute(self, context):
		# bpy.context.scene.tool_settings.use_uv_select_sync = False
		# bpy.ops.mesh.select_all(action='SELECT')

		print("Saving image {}".format(self.image_name))
		# bpy.ops.image.save_as()
		return {'FINISHED'}

'''
bpy.utils.register_class(op)