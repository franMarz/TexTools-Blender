import bpy

from . import utilities_color
from .settings import tt_settings


class op(bpy.types.Operator):
	bl_idname = "uv.textools_color_io_export"
	bl_label = "Export"
	bl_description = "Export current color palette to clipboard"

	@classmethod
	def poll(cls, context):
		if bpy.context.area.ui_type != 'UV':
			return False
		return True

	def execute(self, context):
		export_colors(self, context)
		return {'FINISHED'}


def export_colors(self, context):
	hex_colors = []
	for i in range(tt_settings().color_ID_count):
		color = getattr(tt_settings(), f"color_ID_color_{i}")
		hex_colors.append( utilities_color.color_to_hex( color) )

	bpy.context.window_manager.clipboard = ", ".join(hex_colors)
	bpy.ops.ui.textools_popup('INVOKE_DEFAULT', message=f"{len(hex_colors)}x colors copied to clipboard")
