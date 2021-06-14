import bpy
import string

from . import utilities_color


class op(bpy.types.Operator):
	bl_idname = "uv.textools_color_io_import"
	bl_label = "Import"
	bl_description = "Import hex colors from the clipboard as current color palette"

	@classmethod
	def poll(cls, context):
		#Only in UV editor mode
		if bpy.context.area.type != 'IMAGE_EDITOR':
			return False
		return True
	
	def execute(self, context):
		import_colors(self, context)
		return {'FINISHED'}



def import_colors(self, context):
	# Clipboard hex strings
	hex_strings = bpy.context.window_manager.clipboard.split(',')

	for i in range(len(hex_strings)):
		hex_strings[i] = hex_strings[i].strip().strip('#')
		if len(hex_strings[i]) != 6 or not all(c in string.hexdigits for c in hex_strings[i]):
			# Incorrect format
			self.report({'ERROR_INVALID_INPUT'}, "Incorrect hex format '{}' use a #RRGGBB pattern".format(hex_strings[i]))
			return
		else:
			name = "color_ID_color_{}".format(i)
			if hasattr(bpy.context.scene.texToolsSettings, name):
				# Color Index exists
				color = utilities_color.hex_to_color( hex_strings[i] )
				setattr(bpy.context.scene.texToolsSettings, name, color)
			else:
				# More colors imported than supported
				self.report({'ERROR_INVALID_INPUT'}, "Only {}x colors have been imported instead of {}x".format(
					i,len(hex_strings)
				))
				return
	
	# Set number of colors
	bpy.context.scene.texToolsSettings.color_ID_count = len(hex_strings)

	bpy.ops.ui.textools_popup('INVOKE_DEFAULT', message="{}x colors imported from clipboard".format( len(hex_strings) ))


bpy.utils.register_class(op)
