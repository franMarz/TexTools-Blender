import bpy
import bmesh
import operator
from mathutils import Vector
from collections import defaultdict
from math import pi

from . import utilities_color


class op(bpy.types.Operator):
	bl_idname = "uv.textools_color_io_export"
	bl_label = "Export"
	bl_description = "Export current color palette to clipboard"

	@classmethod
	def poll(cls, context):
		
		#Only in UV editor mode
		if bpy.context.area.type != 'IMAGE_EDITOR':
			return False

		return True
	
	def execute(self, context):
		export_colors(self, context)
		return {'FINISHED'}



def export_colors(self, context):
	
	hex_colors = []
	for i in range(bpy.context.scene.texToolsSettings.color_ID_count):
		color = getattr(bpy.context.scene.texToolsSettings, "color_ID_color_{}".format(i))
		hex_colors.append( utilities_color.color_to_hex( color) )

	bpy.context.window_manager.clipboard = ", ".join(hex_colors)
	bpy.ops.ui.textools_popup('INVOKE_DEFAULT', message="{}x colors copied to clipboard".format(len(hex_colors)))


bpy.utils.register_class(op)