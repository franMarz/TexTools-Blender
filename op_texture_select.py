import bpy
import bmesh
import operator
import math

from . import settings
from . import utilities_bake
from . import op_bake

class op(bpy.types.Operator):
	bl_idname = "uv.textools_texture_select"
	bl_label = "Select Texture"
	bl_description = "Select the texture and bake mode"
	bl_options = {'REGISTER', 'UNDO'}

	name : bpy.props.StringProperty(
		name="image name",
		default = ""
	)

	@classmethod
	def poll(cls, context):
		return True
	
	def execute(self, context):
		select_texture(self, context)
		return {'FINISHED'}



def select_texture(self, context):
	print("Select "+self.name)

	
	# Set bake mode
	for mode in op_bake.modes:
		if mode in self.name:
			print("Found mode: "+mode)

			prop = bpy.context.scene.bl_rna.properties["TT_bake_mode"]
			enum_values = [e.identifier for e in prop.enum_items]

			# find matching enum
			for key in enum_values:
				print("TT_bake "+key)
				if mode in key:
					print("set m: "+key)
					bpy.context.scene.TT_bake_mode = key
					break;

			break
			
	# Set background image
	if self.name in bpy.data.images:
		image = bpy.data.images[self.name]
		for area in bpy.context.screen.areas:
			if area.type == 'IMAGE_EDITOR':
				area.spaces[0].image = image


'''
class op_ui_image_select(bpy.types.Operator):
	bl_idname = "uv.textools_ui_image_select"
	bl_label = "Select image"
	bl_description = "Select this image"

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

		print("Select image {}".format(self.image_name))
		# bpy.ops.image.save_as()
		return {'FINISHED'}
'''
bpy.utils.register_class(op)