import bpy
import os

from . import utilities_bake
from . import op_bake
from .t3dn_bip import previews
from .settings import tt_settings, prefs

from bpy.props import StringProperty

class op_popup(bpy.types.Operator):
	bl_idname = "ui.textools_popup"
	bl_label = "Message"

	message: StringProperty()

	def execute(self, context):
		self.report({'INFO'}, self.message)
		print(self.message)
		return {'FINISHED'}

	def invoke(self, context, event):
		wm = context.window_manager
		return wm.invoke_popup(self, width=200)

	def draw(self, context):
		self.layout.label(text=self.message)


size_textures = [
	('32', '32', ''),
	('64', '64', ''),
	('128', '128', ''),
	('256', '256', ''),
	('512', '512', ''),
	('1024', '1024', ''),
	('2048', '2048', ''),
	('4096', '4096', ''),
	('8192', '8192', '')
]

# Preview collections created in the register function.
preview_icons = previews.new(max_size=(32, 32))
thumbnail_previews: 'previews.ImagePreviewCollection | None' = None


def icon_register(fileName):
	name = fileName.split('.')[0]  # Don't include file extension
	icons_location = os.path.join(os.path.dirname(__file__), "icons_bip")
	preview_icons.load_safe(name, os.path.join(icons_location, fileName), 'IMAGE')


def icon_get(name):
	return preview_icons[name].icon_id


def generate_bake_mode_previews():
	image_location = os.path.join(os.path.dirname(__file__), "resources/bake_modes_bip")	
	enum_items = []
	
	# Generate the thumbnails
	for i, image in enumerate(os.listdir(image_location)):
		mode = image[0:-4]
		if mode in op_bake.modes:
			filepath = os.path.join(image_location, image)
			thumb = thumbnail_previews.load_safe(filepath, filepath, 'IMAGE')
			enum_items.append((image, mode, "", thumb.icon_id, i))
	
	return enum_items


def GetContextView3D():
	for window in bpy.context.window_manager.windows:
		screen = window.screen
		for area in screen.areas:
			if area.type == 'VIEW_3D': 
				for region in area.regions:
					if region.type == 'WINDOW':
						# Stuff the override context with very common requests by operators.  MORE COULD BE NEEDED!
						override = {'window': window, 'screen': screen, 'area': area, 'region': region, 'scene': bpy.context.scene,
									'edit_object': bpy.context.edit_object, 'active_object': bpy.context.active_object,
									'selected_objects': bpy.context.selected_objects}
						return override					
	return None


def GetContextViewUV():
	for window in bpy.context.window_manager.windows:
		screen = window.screen
		for area in screen.areas:
			if area.ui_type == 'UV':
				for region in area.regions:
					if region.type == 'WINDOW':
						# Stuff the override context with very common requests by operators.  MORE COULD BE NEEDED!
						override = {'window': window, 'screen': screen, 'area': area, 'region': region, 'scene': bpy.context.scene,
									'edit_object': bpy.context.edit_object, 'active_object': bpy.context.active_object,
									'selected_objects': bpy.context.selected_objects}
						return override			
	return None


def get_padding():
	return tt_settings().padding / min(tt_settings().size)


def get_bake_mode():
	return str(bpy.context.scene.TT_bake_mode).replace('.bip', '').lower()


def set_bake_color_space_int(bake_mode):
	color_space = prefs().bake_color_space_def
	if "normal_" in bake_mode:
		return 3 if color_space in ('ASTANDARD', 'APBR') else 1
	elif color_space == 'STANDARD':
		return 0
	elif color_space == 'ASTANDARD':
		return 2
	elif color_space in ('PBR', 'APBR'):
		if (op_bake.modes[bake_mode].material != "") or (bake_mode == 'transmission' and not prefs().bool_clean_transmission) or \
				bake_mode in {'diffuse', 'base_color', 'sss_color', 'emission', 'environment', 'combined'}:
			return 0 if color_space == 'PBR' else 2
		return 1 if color_space == 'PBR' else 3

	if color_space not in {'PBR', 'APBR', 'STANDARD', 'ASTANDARD'}:
		raise NotImplementedError(f'{color_space=} not implement for set_bake_color_space_int()')
	raise NotImplementedError(f'{bake_mode=} is an invalid keyword argument for set_bake_color_space_int()')


def on_bakemode_set(self, context):
	bake_mode = get_bake_mode()
	if set_bake_color_space_int(bake_mode) == 1:
		tt_settings().bake_color_space = 'Non-Color'
	elif set_bake_color_space_int(bake_mode) == 0:
		tt_settings().bake_color_space = 'sRGB'
	elif set_bake_color_space_int(bake_mode) == 3:
		tt_settings().bake_color_space = 'Utility - Linear - sRGB'
	else:
		tt_settings().bake_color_space = 'Utility - sRGB - Texture'
	utilities_bake.on_select_bake_mode(bake_mode)




def register():
	global thumbnail_previews
	thumbnail_previews = previews.new(max_size=(128, 128))

	# This is an EnumProperty for storing all images
	# You really can save it anywhere in bpy.types.*  Just make sure the location makes sense
	bpy.types.Scene.TT_bake_mode = bpy.props.EnumProperty(
		items=generate_bake_mode_previews(),
		update=on_bakemode_set,
		default='normal_tangent.bip'
	)


def unregister():
	try:
		previews.remove(thumbnail_previews)
		previews.remove(preview_icons)
	except ResourceWarning as e:
		print(e)

	# del bpy.types.Scene.TT_bake_mode
