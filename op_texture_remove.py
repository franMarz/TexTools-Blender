import bpy
import bmesh
import operator
import math
import os

from bpy.props import *
from . import settings
from . import utilities_bake


class op(bpy.types.Operator):
	bl_idname = "uv.textools_texture_remove"
	bl_label = "Remove Texture"
	bl_description = "Remove the texture"
	bl_options = {'REGISTER', 'UNDO'}

	name : bpy.props.StringProperty(
		name="image name",
		default = ""
	)

	@classmethod
	def poll(cls, context):
		return True
	
	def execute(self, context):
		remove_texture(self.name)
		return {'FINISHED'}





def remove_texture(name):
	print("Save image.. "+name)


	if name in bpy.data.images:
		bpy.data.images.remove( bpy.data.images[name] )


bpy.utils.register_class(op)