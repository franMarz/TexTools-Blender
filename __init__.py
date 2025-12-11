bl_info = {
	"name": "TexTools",
	"description": "Professional UV and Texture tools for Blender.",
	"author": "renderhjs, franMarz, Sav Martin",
	"version": (1, 6, 2),
	"blender": (2, 80, 0),
	"category": "UV",
	"location": "UV Image Editor > Tools > 'TexTools' panel"
}



from . import settings
from . import utilities_ui
from . import utilities_bake
from . import utilities_color
from . import utilities_texel
from . import utilities_bbox
from . import utilities_uv
from . import utilities_meshtex

from . import op_align
from . import op_bake
from . import op_bake_explode
from . import op_bake_organize_names
from . import op_texture_preview
from . import op_texture_preview_cleanup
from . import op_color_assign
from . import op_color_clear
from . import op_color_convert_texture
from . import op_color_convert_vertex_colors
from . import op_color_from_elements
from . import op_color_from_materials
from . import op_color_from_directions
from . import op_edge_split_bevel
from . import op_color_io_export
from . import op_color_io_import
from . import op_color_select
from . import op_color_select_vertex
from . import op_island_align_edge
from . import op_island_align_sort
from . import op_island_align_world
from . import op_island_mirror
from . import op_island_rotate_90
from . import op_island_straighten_edge_loops
from . import op_island_centralize
from . import op_randomize
from . import op_rectify
from . import op_select_islands_identical
from . import op_select_islands_outline
from . import op_select_islands_overlap
from . import op_select_islands_flipped
from . import op_select_zero
from . import op_relax
from . import op_smoothing_uv_islands
from . import op_meshtex_create
from . import op_meshtex_wrap
from . import op_meshtex_trim
from . import op_meshtex_trim_collapse
from . import op_meshtex_pattern
from . import op_texel_checker_map
from . import op_texel_checker_map_cleanup
from . import op_texel_density_get
from . import op_texel_density_set
from . import op_texture_reload_all
from . import op_texture_save
from . import op_texture_open
from . import op_texture_select
from . import op_texture_remove
from . import op_unwrap_faces_iron
from . import op_stitch
from . import op_unwrap_edge_peel
from . import op_uv_channel_add
from . import op_uv_channel_remove
from . import op_uv_channel_swap
from . import op_uv_crop
from . import op_uv_fill
from . import op_uv_resize
from . import op_uv_size_get
from . import op_uv_unwrap



# Import general modules. Important: must be placed here and not on top
import bpy
import math

from bpy.types import Menu, Operator, Panel, AddonPreferences, PropertyGroup
from bpy.props import (
	StringProperty,
	BoolProperty,
	IntProperty,
	IntVectorProperty,
	FloatProperty,
	FloatVectorProperty,
	EnumProperty,
	PointerProperty,
)

from .settings import tt_settings, prefs

def on_bake_def_back_color_set(self, context):
	if self.bool_bake_back_color:
		tt_settings().bake_back_color = self.bake_back_color_def


def on_bake_color_space_set(self, context):
	if utilities_ui.set_bake_color_space_int(utilities_ui.get_bake_mode()) == 1:
		tt_settings().bake_color_space = 'Non-Color'
	elif utilities_ui.set_bake_color_space_int(utilities_ui.get_bake_mode()) == 0:
		tt_settings().bake_color_space = 'sRGB'
	elif utilities_ui.set_bake_color_space_int(utilities_ui.get_bake_mode()) == 3:
		tt_settings().bake_color_space = 'Utility - Linear - sRGB'
	else:
		tt_settings().bake_color_space = 'Utility - sRGB - Texture'


class Panel_Preferences(AddonPreferences):
	bl_idname = __package__

	# Addon Preferences https://docs.blender.org/api/blender_python_api_2_67_release/bpy.types.AddonPreferences.html
	swizzle_y_coordinate: EnumProperty(items=
		(
			('Y+', 'Y+ OpenGL', 'Used in Blender, Maya, Modo, Toolbag, Unity'), 
			('Y-', 'Y- Direct X', 'Used in 3ds Max, CryENGINE, Source, Unreal Engine')
		),
		description="Color template",
		name="Swizzle Coordinates",
		default='Y+'
	)
	bake_device: EnumProperty(items=
		[	
			('DEFAULT', 'Default', 'Use the device specified in the Render Properties panel'), 
			('CPU', 'CPU', 'Always use the CPU when baking with Cycles'), 
			('GPU', 'GPU', 'Always use the GPU when baking with Cycles')
		], 
		description="Temporary device override only for baking", 
		name="Baking Device",
		default='DEFAULT'
	)
	bake_32bit_float: EnumProperty(items=
		(
			('8', '8 Bit', ''), 
			('32', '32 Bit', '')
		),
		description="", 
		name="Image depth",
		default='8'
	)
	bake_back_color_def: FloatVectorProperty(
		name="Global custom baking background color", 
		subtype='COLOR', 
		size=4, 
		min=0, max=1, 
		default=(0.0, 0.0, 0.0, 1.0), 
		update = on_bake_def_back_color_set
	)
	bool_bake_back_color: EnumProperty(items=
		[	
			('DEFAULT', 'Default', 'Use default TexTools background colors for baked textures'), 
			('CUSTOM', 'Custom', 'Set a global custom RGBA color for the background. Note that a transparent background can be specified')
		], 
		description="Mode for baked textures background color and alpha", 
		name="Bake background",
		default='DEFAULT',
		update=on_bake_def_back_color_set
	)
	bake_color_space_def: EnumProperty(items=
		[	
			('STANDARD', 'Standard', 'Set sRGB as Color Space for all baked textures except for Normal maps'), 
			('PBR', 'PBR typical', 'Set Linear as Color Space for all baked maps except for Diffuse/Base Color, SSS/Emission color, colored Transmission, Environment, Combined or any custom Mode'),
			('ASTANDARD', 'ACES standard', 'Set ACES sRGB Texture as Color Space for all baked textures except for Normal maps'), 
			('APBR', 'ACES PBR typical', 'Set ACES Linear sRGB as Color Space for all baked maps except for Diffuse/Base Color, SSS/Emission color, colored Transmission, Environment, Combined or any custom Mode')
		], 
		description="Automatically set the Color Space of the baked images. Can be changed in the Baking panel", 
		name="Bake Color Space",
		default='STANDARD',
		update=on_bake_color_space_set
	)
	bool_alpha_ignore: BoolProperty(
		name="Ignore Alpha when baking other modes", 
		default=True
	)
	bool_emission_ignore: BoolProperty(
		name="Ignore Emission Strength when baking Emission", 
		default=True
	)
	bool_clean_transmission: BoolProperty(
		name="Ignore other channels when baking Transmission", 
		default=False
	)
	bool_color_id_vertex_color_gamma: BoolProperty(
		name="Apply gamma to ID Colors in Vextex Color mode for visual consistency", 
		default=False
	)
	bool_modifier_auto_high: BoolProperty(
		name="Detect Objects with Subdiv or Bevel Mods as a Highpoly pair for baking", 
		default=True
	)
	bake_mode_panel_scale: FloatProperty(
		name="Bake Mode Panel Scale", 
		description="Scale of the bake mode selector panel icons", 
		default=3.6, 
		min=2, 
		max=10
	)
	texel_density_scale: FloatProperty(
		name="Texel Density Unit Scale", 
		description="Multiplier for scaling the System Units when working with Texel Density values", 
		default=1, 
		min=0.00000000001
	)
	bool_help: BoolProperty(
		name="Show help buttons on panels", 
		default=True
	)


	def draw(self, context):
		layout = self.layout

		box = layout.box()
		col = box.column(align=True)
		col.prop(self, "bake_device", icon='PREFERENCES')
		if self.bake_device == 'DEFAULT':
			col.label(text="Use the device specified in the Render Properties panel.")
		elif self.bake_device == 'CPU':
			col.label(text="Always use the CPU when baking in TexTools with Cycles.")
		elif self.bake_device == 'GPU':
			col.label(text="Always use the GPU when baking in TexTools with Cycles.")

		box.separator()
		col = box.column(align=True)
		col.prop(self, "swizzle_y_coordinate", icon='ORIENTATION_GLOBAL')
		if self.swizzle_y_coordinate == 'Y+':
			col.label(text="Y+ used in: Blender, Maya, Modo, Toolbag, Unity")
		elif self.swizzle_y_coordinate == 'Y-':
			col.label(text="Y- used in: 3ds Max, CryENGINE, Source, Unreal Engine")

		box.separator()
		col = box.column(align=True)
		col.prop(self, "bake_32bit_float", icon='IMAGE_RGB')
		if self.bake_32bit_float == '8':
			col.label(text="8 Bit images are used. Banding may appear in normal maps.")
		elif self.bake_32bit_float == '32':
			col.label(text="32 Bit images are used. Images may require dithering to 8 bit.")

		box.separator()
		col = box.column(align=True)
		col.prop(self, "bake_color_space_def", icon='IMAGE_ZDEPTH')
		if self.bake_device == 'STANDARD':
			col.label(text="Set sRGB as Color Space for all baked textures except for Normal maps.")
		elif self.bake_device == 'PBR':
			col.label(text="Set Linear as Color Space for all baked maps except for Diffuse/Base Color, SSS/Emission color, colored Transmission, Environment, Combined or any custom Mode.")
		elif self.bake_device == 'ASTANDARD':
			col.label(text="Set ACES sRGB Texture as Color Space for all baked textures except for Normal maps.")
		elif self.bake_device == 'APBR':
			col.label(text="Set ACES Linear sRGB as Color Space for all baked maps except for Diffuse/Base Color, SSS/Emission color, colored Transmission, Environment, Combined or any custom Mode.")
	
		box.separator()
		col = box.column(align=True)
		col.prop(self, "bool_bake_back_color", icon='IMAGE_RGB_ALPHA')
		if self.bool_bake_back_color == 'CUSTOM':
			col.prop(self, "bake_back_color_def", text ="")

		box.separator()
		col = box.column(align=True)
		col.prop(self, "bool_modifier_auto_high", icon='MESH_MONKEY')

		box.separator()
		col = box.column(align=True)
		col.prop(self, "bool_alpha_ignore", icon='ANIM')
		col.prop(self, "bool_clean_transmission", icon='ANIM')
		col.prop(self, "bool_emission_ignore", icon='ANIM')
		col.prop(self, "bake_mode_panel_scale")

		box.separator()
		col = box.column(align=True)
		col.prop(self, "texel_density_scale")

		box.separator()
		col = box.column(align=True)
		col.prop(self, "bool_color_id_vertex_color_gamma", icon='INDIRECT_ONLY_ON')

		box.separator()
		col = box.column(align=True)
		col.prop(self, "bool_help", icon='INFO')


		if not hasattr(bpy.types,"ShaderNodeBevel"):
			box.separator()
			col = box.column(align=True)
		
			col.label(text="Unlock Bevel Shader", icon='ERROR')
			col.operator("wm.url_open", text="Get Blender with Bevel Shader", icon='BLENDER').url = "https://builder.blender.org/download/"
			col.label(text="Use nightly builds of Blender 2.79 or 2.8 to access Bevel baking")


		box = layout.box()

		box.label(text="Additional Links")
		col = box.column(align=True)
		col.operator("wm.url_open", text="Donate", icon='HELP').url = "https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=ZC9X4LE7CPQN6"
		col.operator("wm.url_open", text="GIT Code", icon='WORDWRAP_ON').url = "https://github.com/SavMartin/TexTools-Blender"
		
		col.label(text="Discussions")
		row = col.row(align=True)
		row.operator("wm.url_open", text="BlenderArtists", icon='BLENDER').url = "https://blenderartists.org/forum/showthread.php?443182-TexTools-for-Blender"
		row.operator("wm.url_open", text="Polycount").url = "http://polycount.com/discussion/197226/textools-for-blender"
		row.operator("wm.url_open", text="Twitter").url = "https://twitter.com/search?q=%23textools"
		


class UV_OT_op_debug(Operator):
	bl_idname = "uv.op_debug"
	bl_label = "Debug"
	bl_description = "Open console and enable debug mode"

	@classmethod
	def poll(cls, context):
		return True

	def execute(self, context):
		bpy.app.debug = True	# Debug Vertex indexies
		bpy.context.object.data.show_extra_indices = True
		bpy.app.debug_value = 1	#Set to Non '0
		return {'FINISHED'}



class UV_OT_op_select_bake_set(Operator):
	bl_idname = "uv.op_select_bake_set"
	bl_label = "Select"
	bl_description = "Select this bake set in scene"

	select_set : StringProperty(default="")

	@classmethod
	def poll(cls, context):
		return True

	def execute(self, context):
		premode = bpy.context.active_object.mode
		if self.select_set != "":
			for bset in settings.sets:
				if bset.name == self.select_set:
					bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
					bpy.ops.object.select_all(action='DESELECT')
					for obj in bset.objects_low:
						obj.select_set(True)
					for obj in bset.objects_high:
						obj.select_set(True)
					for obj in bset.objects_cage:
						obj.select_set(True)
					# Set active object to low poly to better visualize high and low wireframe color
					if bset.objects_low:
						bpy.context.view_layer.objects.active = bset.objects_low[0]
					break
			bpy.ops.object.mode_set(mode=premode)

		return {'FINISHED'}



class UV_OT_op_select_bake_type(Operator):
	bl_idname = "uv.op_select_bake_type"
	bl_label = "Select"
	bl_description = "Select bake objects of this type"

	select_type: StringProperty(default='low')

	@classmethod
	def poll(cls, context):
		return True

	def execute(self, context):
		objects = []
		for bset in settings.sets:
			if self.select_type == 'low':
				objects += bset.objects_low
			elif self.select_type == 'high':
				objects += bset.objects_high
			elif self.select_type == 'cage':
				objects += bset.objects_cage
			elif self.select_type == 'float':
				objects += bset.objects_float
			elif self.select_type == 'issue' and bset.has_issues:
				objects += bset.objects_low
				objects += bset.objects_high
				objects += bset.objects_cage
				objects += bset.objects_float

		if objects:
			premode = bpy.context.active_object.mode
			bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
			bpy.ops.object.select_all(action='DESELECT')
			for obj in objects:
				obj.select_set(True)
			bpy.ops.object.mode_set(mode=premode)

		return {'FINISHED'}



def on_dropdown_size(self, context):
	# Help: http://elfnor.com/drop-down-and-button-select-menus-for-blender-operator-add-ons.html
	size = int(tt_settings().size_dropdown)
	tt_settings().size = size, size

	if size <= 256:
		tt_settings().padding = 2
	else:
		tt_settings().padding = 4



def on_dropdown_uv_channel(self, context):
	selected_obs = [ob for ob in bpy.context.selected_objects if ob.type == 'MESH']
	if selected_obs:
		for ob in selected_obs:
			if ob.data.uv_layers:
				# Change Mesh UV Channel
				index = int(tt_settings().uv_channel)
				if index < len(ob.data.uv_layers):
					ob.data.uv_layers.active_index = index
					#bpy.context.object.data.uv_layers[index].active_render = True
					ob.data.uv_layers[0].active_render = True



def on_color_changed(self, context):
	if tt_settings().color_assign_mode == 'MATERIALS':
		for i in range(0, tt_settings().color_ID_count):
			utilities_color.assign_color(i)



def on_color_dropdown_template(self, context):
	hex_colors = tt_settings().color_ID_templates.split(',')
	tt_settings().color_ID_count = len(hex_colors)

	for i in range(0, len(hex_colors)):
		color = utilities_color.hex_to_color("#"+hex_colors[i])
		utilities_color.set_color(i, color)
	
	if tt_settings().color_assign_mode == 'MATERIALS':
		utilities_color.assign_color(i)



def on_color_count_changed(self, context):
	if bpy.context.active_object and tt_settings().color_assign_mode == 'MATERIALS':
		utilities_color.validate_face_colors(bpy.context.active_object)



def on_color_mode_change(self, context):
	if tt_settings().color_assign_mode == 'MATERIALS':
		# Refresh color palette of existing colored materials
		for i in range(0, tt_settings().color_ID_count):
			utilities_color.assign_color(i)
	if bpy.context.active_object is not None:
		if bpy.context.active_object.mode != 'EDIT' and bpy.context.active_object.mode != 'OBJECT':
			bpy.ops.object.mode_set(mode='OBJECT')
	utilities_color.update_properties_tab()
	utilities_color.update_view_mode()



def get_dropdown_uv_values(self, context):
	options = []
	obj = bpy.context.active_object
	if obj and obj.type == 'MESH' and obj.data.uv_layers:
		step = 0
		for uvLoop in obj.data.uv_layers:
			options.append((str(step), f'UV {step+1}', f"Change active UV Channel of all selected Objects to '{uvLoop.name}' where possible", step))
			step += 1
	return options



def on_slider_meshtexture_wrap(self, context):
	value = tt_settings().meshtexture_wrap
	obj_uv = utilities_meshtex.find_uv_mesh(bpy.context.selected_objects)
	if obj_uv:
		obj_uv.data.shape_keys.key_blocks["uv"].value = value




class TexToolsSettings(PropertyGroup):

	def get_bake_back_color(self):
		return self.get("bake_back_color", bpy.context.preferences.addons[__package__].preferences.bake_back_color_def)

	def set_bake_back_color(self, value):
		if value is not None:
			self["bake_back_color"] = value

	def get_bake_color_space(self):
		return self.get("bake_color_space", utilities_ui.set_bake_color_space_int(utilities_ui.get_bake_mode()))

	def set_bake_color_space(self, value):
		if value is not None:
			self["bake_color_space"] = value


	#Width and Height
	size : IntVectorProperty(
		name = "Size", 
		size=2, 
		description="Texture & UV size in pixels", 
		default = (512,512), 
		subtype = "XYZ"
	)
	size_dropdown : EnumProperty(
		items = utilities_ui.size_textures, 
		name = "Texture Size", 
		update = on_dropdown_size, 
		default = '512'
	)
	uv_channel : EnumProperty(
		items = get_dropdown_uv_values, 
		name = "UV", 
		update = on_dropdown_uv_channel
	)
	UDIMs_source : EnumProperty(items= 
		[('OBJECT', 'From Object', 'Work on the first detected Tiled UDIM Image in the Active Object Materials'), 
		('EDITOR', 'Editor Image', 'Work on the UV Editor Linked Image')], 
		name = "UDIM Tiles Source", 
		default = 'OBJECT'
	)
	padding : IntProperty(
		name = "Padding",
		description = "Padding size in pixels",
		default = 4,
		min = 0,
		max = 256
	)
	bake_samples : IntProperty(
		name = "Samples",
		description = "Samples in Cycles for baking. The higher, the less noise. Use with caution with high values",
		default = 8,
		min = 1,
		max = 4000
	)
	bake_curvature_size : IntProperty(
		name = "Curvature",
		description = "Curvature offset in pixels to process",
		default = 1,
		min = 1,
		max = 64
	)
	bake_wireframe_size : FloatProperty(
		name = "Thickness",
		description = "Wireframe thickness in pixels",
		default = 1,
		min = 0.1,
		max = 4.0
	)
	bake_bevel_size : FloatProperty(
		name = "Radius",
		description = "Bevel radius",
		default = 0.05,
		min = 0.0,
		max = 16
	)
	bake_bevel_samples : IntProperty(
		name = "Bevel Samples",
		description = "Bevel samples. The higher, the less noise. Use with caution with values higher than 64",
		default = 16,
		min = 1,
		max = 256
	)
	bake_thickness_distance : FloatProperty(
		name = "Distance",
		description = "AO distance",
		default = 1.0,
		min = 0.0,
		max = 16.0
	)
	bake_thickness_contrast : FloatProperty(
		name = "Contrast",
		description = "AO contrast",
		default = 1.0,
		min = 0.0,
		max = 2.0
	)
	bake_thickness_local : BoolProperty(
		name = "Only Local",
		description = "Only detect occlusion from the object itself, and not others",
		default = True
	)
	bake_ray_distance : FloatProperty(
		name = "Ray Distance",
		description = "The maximum ray distance for matching points between the active and selected objects. If zero, there is no limit",
		default = 0.00,
		min = 0.000,
		max = 100.00
	)
	bake_cage_extrusion : FloatProperty(
		name = "Cage Extrusion",
		description = "Cage Extrusion, Inflate the cage object by the specified distance for baking",
		default = 0.00,
		min = 0.000,
		max = 100.00
	)
	bake_force : EnumProperty(items= 
		[('None', 'Normal', 'Use the default TexTools baking behaviour'), 
		('Single', 'Single', 'Force a single texture bake across all selected Objects'), 
		('Multi', 'Multi', 'Force a texture bake for each selected Mesh Object by disabling automatic pairing by name')], name = "Force", default = 'None'
	)
	bake_sampling : EnumProperty(items= 
		[('1', 'None', 'No Anti Aliasing (Fast)'), 
		('2', '2x', 'Render 2x and downsample'), 
		('4', '4x', 'Render 2x and downsample')], name = "AA", default = '1'
	)
	# Default Color Space have to be Linear as the first bake mode loaded in the UI before refreshing the bake mode is Tangent Normal
	bake_color_space : EnumProperty(items= 
		[('sRGB', 'sRGB', 'Standard RGB output color space for the baked texture'), 
		('Non-Color', 'Linear', 'Linear or Non-Color output color space for the baked texture'),
		('Utility - sRGB - Texture', 'Utility - sRGB - Texture', 'ACES Standard RGB Texture output color space for the baked texture'), 
		('Utility - Linear - sRGB', 'Utility - Linear - sRGB', 'ACES Linear Standard RGB output color space for the baked texture')], 
		name = "CS", 
		default = 'Non-Color', 
		get = get_bake_color_space, 
		set = set_bake_color_space
	)
	bake_back_color : FloatVectorProperty( 
		description = "Baked texture background color", 
		name = "BK", 
		subtype = 'COLOR', 
		size = 4, 
		min = 0, 
		max = 1, 
		default = (0.0, 0.0, 0.0, 1.0), 
		get = get_bake_back_color, 
		set = set_bake_back_color
	)
	bake_freeze_selection : BoolProperty(
		name="Lock",
		description="Lock baking sets, don't change with selection",
		default = False
	)
	align_mode : EnumProperty(items= 
		[('SELECTION', 'Selection', 'Align selected islands to the selection limits'), 
		('CANVAS', 'Canvas', 'Align selected islands to the canvas margins'), 
		('CURSOR', 'Cursor', 'Align selected islands to the cursor position')], 
		name = "Mode", 
		default = 'SELECTION'
	)
	texel_get_mode : EnumProperty(items= 
		[('IMAGE', 'Image', 'Per object, get the resolution of the first image found in any used material'), 
		('SIZE', 'TexTools Size', 'Use the Size specified under the TexTools tab')] + utilities_ui.size_textures, 
		name = "Texture Size", 
		default = 'IMAGE'
	)
	texel_set_mode : EnumProperty(items= 
		[('ISLAND', 'Islands', 'Scale UV islands to match Texel Density'), 
		('ALL', 'Combined', 'Scale all UVs together to match Texel Density')], 
		name = "Set Mode", 
		default = 'ISLAND'
	)
	texel_density : FloatProperty(
		name = "Texel",
		description = "Texel size or Pixels per unit ratio",
		default = 256,
		min = 0.0
	)
	meshtexture_wrap : FloatProperty(
		name = "Wrap",
		description = "Transition of mesh texture wrap",
		default = 1,
		min = 0,
		max = 1,
		update = on_slider_meshtexture_wrap, 
		subtype  = 'FACTOR'
	)
	vertex_color_threshold : FloatProperty(
		name = "Vertex Color Threshold",
		description = "Color threshold for vertex color selection",
		default = .01,
		min = 0.0,
		max = 0.5,
		precision=3,
		step=1
	)

	def get_color(hex = "808080"):
		return FloatVectorProperty(
			name="Color1", 
			description="Set Color 1 for the Palette", 
			subtype="COLOR", 
			default=utilities_color.hex_to_color(hex), 
			size=3, 
			max=1.0, min=0.0,
			update=on_color_changed
		)

	# 10 Color ID's
	color_ID_color_0 : get_color(hex="#ff0000")
	color_ID_color_1 : get_color(hex="#0000ff")
	color_ID_color_2 : get_color(hex="#00ff00")
	color_ID_color_3 : get_color(hex="#ffff00")
	color_ID_color_4 : get_color(hex="#00ffff")
	color_ID_color_5 : get_color()
	color_ID_color_6 : get_color()
	color_ID_color_7 : get_color()
	color_ID_color_8 : get_color()
	color_ID_color_9 : get_color()
	color_ID_color_10 : get_color()
	color_ID_color_11 : get_color()
	color_ID_color_12 : get_color()
	color_ID_color_13 : get_color()
	color_ID_color_14 : get_color()
	color_ID_color_15 : get_color()
	color_ID_color_16 : get_color()
	color_ID_color_17 : get_color()
	color_ID_color_18 : get_color()
	color_ID_color_19 : get_color()

	color_ID_templates : EnumProperty(items= 
		[	
			('3d3d3d,7f7f7f,b8b8b8,ffffff', '4 Gray', '...'), 
			('003153,345d4b,688a42,9db63a,d1e231', '5 Greens', '...'),
			('ff0000,0000ff,00ff00,ffff00,00ffff', '5 Code', '...'),
			('3a4342,2e302f,242325,d5cc9e,d6412b', '5 Sea Wolf', '...'),
			('7f87a0,2d3449,000000,ffffff,f99c21', '5 Mustang', '...'),
			('143240,209d8c,fed761,ffab56,fb6941', '5 Sunset', '...'), 
			('0087ed,23ca7a,eceb1d,e37a29,da1c2c', '5 Heat', '...'), 
			('9e00af,7026b9,4f44b5,478bf4,39b7d5,229587,47b151,9dcf46,f7f235,f7b824,f95f1e,c5513c,78574a,4d4b4b,9d9d9d', '15 Rainbow', '...')
		], 
		description="Color template",
		name = "Preset", 
		update = on_color_dropdown_template,
		default = 'ff0000,0000ff,00ff00,ffff00,00ffff'
	)

	color_ID_count : IntProperty(
		name = "Count",
		description="Number of color IDs",
		default = 5,
		update = on_color_count_changed,
		min = 2,
		max = 20
	)

	color_assign_mode : EnumProperty(items= 
		[('MATERIALS', 'Materials', 'Assign simple colored materials to objects or selected faces'), 
		('VERTEXCOLORS', 'Vertex Colors', 'Assign colors as Vertex Colors to objects or selected faces')], 
		name = "Assign Mode", 
		default = 'MATERIALS', 
		update = on_color_mode_change
	)

	# bake_do_save = BoolProperty(
	# 	name="Save",
	# 	description="Save the baked texture?",
	# 	default = False)



class UI_PT_Panel_Units(Panel):
	bl_label = " "
	bl_space_type = 'IMAGE_EDITOR'
	bl_region_type = 'UI'
	bl_category = "TexTools"
	#bl_options = {'HIDE_HEADER'}

	def draw_header(self, _):
		layout = self.layout
		row = layout.row(align=True)
		row.label(text ="TexTools")

	def draw(self, context):
		layout = self.layout
		
		if bpy.app.debug_value != 0:
			row = layout.row()
			row.alert =True
			row.operator("uv.op_debug", text="DEBUG", icon="CONSOLE")
		
		#---------- Settings ------------
		# row = layout.row()
		col = layout.column(align=True)
		r = col.row(align=True)
		r.prop(tt_settings(), "size_dropdown", text="Size")
		r.operator(op_uv_size_get.op.bl_idname, text="", icon = 'EYEDROPPER')

		r = col.row(align=True)
		r.prop(tt_settings(), "size", text="")

		r = col.row(align=True)
		r.prop(tt_settings(), "padding", text="Padding")
		r.operator(op_uv_resize.op.bl_idname, text="Resize", icon_value = icon_get("op_extend_canvas_open"))
		#col.operator(op_extend_canvas.op.bl_idname, text="Resize", icon_value = icon_get("op_extend_canvas"))


		obj = bpy.context.active_object
		if obj and (obj.mode == 'EDIT' or (bpy.context.selected_objects and obj in bpy.context.selected_objects)):
			if obj.type == 'MESH':

				row = layout.row()

				if not obj.data.uv_layers:
					row.operator(op_uv_channel_add.op.bl_idname, text="Add", icon = 'ADD')

				else:
					# UV Channel

					group = row.row(align=True)
					group.prop(tt_settings(), "uv_channel", text="")
					group.operator(op_uv_channel_add.op.bl_idname, text="", icon = 'ADD')
					group.operator(op_uv_channel_remove.op.bl_idname, text="", icon = 'REMOVE')

					r = group.column(align=True)
					r.active = obj.data.uv_layers.active_index > 0
					r.operator(op_uv_channel_swap.op.bl_idname, text="", icon = 'TRIA_UP_BAR').is_down = False
					
					r = group.column(align=True)
					r.active = obj.data.uv_layers.active_index < (len(obj.data.uv_layers)-1)
					r.operator(op_uv_channel_swap.op.bl_idname, text="", icon = 'TRIA_DOWN_BAR').is_down = True

					# UDIM Tiles

					row = layout.row()
					row.prop(tt_settings(), "UDIMs_source", text="Tiles")

					def get_UDIM_image():
						for i in range(len(obj.material_slots)):
							slot = obj.material_slots[i]
							if slot.material:
								tree = slot.material.node_tree
								if tree:
									nodes = tree.nodes
									if nodes:
										for node in nodes:
											if node.type == 'TEX_IMAGE' and node.image and node.image.source =='TILED':
												return node.image
						return None

					if tt_settings().UDIMs_source == 'OBJECT':
						image = get_UDIM_image()
					else:  # 'EDITOR'
						image = context.space_data.image

					if image:
						row = layout.row(align=True)
						col = row.column()
						col.template_list("IMAGE_UL_udim_tiles", "", image, "tiles", image.tiles, "active_index", rows=3, maxrows=3)


		col = layout.column(align=True)
		row = col.row(align = True)
		row.operator(op_texture_reload_all.op.bl_idname, text="Reload Textures", icon_value = icon_get("op_texture_reload_all"))

		if settings.bversion >= 3.0:
			row = col.row(align=True)
			row.scale_y = 1.75
			row.operator(op_texel_checker_map.op.bl_idname, text ="Checker Map", icon_value = icon_get("op_texel_checker_map"))
			row.operator(op_texel_checker_map_cleanup.op.bl_idname, text ="", icon = 'TRASH')
			if context.active_object and 'TT_CM_Scale' in context.active_object:
				row = col.row(align = True)
				row.prop(context.active_object, "TT_CM_Scale", text="Tiling")




class UI_PT_Panel_Layout(Panel):
	bl_label = " "
	bl_space_type = 'IMAGE_EDITOR'
	bl_region_type = 'UI'
	bl_category = "TexTools"
	bl_options = {'DEFAULT_CLOSED'}

	def draw_header(self, _):
		layout = self.layout
		row = layout.row(align=True)
		if bpy.context.preferences.addons[__package__].preferences.bool_help:
			row.operator("wm.url_open", text="", icon='INFO').url = "http://renderhjs.net/textools/blender/index.html#uvlayout"
		row.label(text ="UV Layout")

	# def draw_header(self, _):
	# 	layout = self.layout
	# 	layout.label(text="", icon_value=icon("logo"))

	def draw(self, context):
		layout = self.layout
		
		if bpy.app.debug_value != 0:
			pass
			# col = layout.column(align=True)
			# col.alert = True
			# row = col.row(align=True)
			# row.operator(op_island_mirror.op.bl_idname, text="Mirror", icon_value = icon_get("op_island_mirror")).is_stack = False
			# row.operator(op_island_mirror.op.bl_idname, text="Stack", icon_value = icon_get("op_island_mirror")).is_stack = True

		#---------- Layout ------------
		# layout.label(text="Layout")
		
		box = layout.box()
		col = box.column(align=True)


		row = col.row(align=True)
		row.operator(op_uv_crop.op.bl_idname, text="Crop", icon_value = icon_get("op_uv_crop"))
		row.operator(op_uv_fill.op.bl_idname, text="Fill", icon_value = icon_get("op_uv_fill"))


		row = col.row(align=True)
		row.operator(op_island_align_edge.op.bl_idname, text="Align Edge", icon_value = icon_get("op_island_align_edge"))
		
		row = col.row(align=True)
		row.operator(op_island_align_world.op.bl_idname, text="Align World", icon_value = icon_get("op_island_align_world"))

			
		if bpy.app.debug_value != 0:
			c = col.column(align=True)
			c.alert = True
			
			c.operator(op_edge_split_bevel.op.bl_idname, text="Split Bevel")
			
		col.separator()
		
		col_tr = col.column(align=True)
		
		row = col_tr.row(align=True)
		col = row.column(align=True)
		# col.label(text="")
		col.operator(op_align.op.bl_idname, text="↖", icon_value = icon_get("op_align_topleft")).direction = "topleft"
		col.operator(op_align.op.bl_idname, text="← ", icon_value = icon_get("op_align_left")).direction = "left"
		col.operator(op_align.op.bl_idname, text="↙", icon_value = icon_get("op_align_bottomleft")).direction = "bottomleft"
		
		col = row.column(align=True)
		col.operator(op_align.op.bl_idname, text="↑", icon_value = icon_get("op_align_top")).direction = "top"
		col.operator(op_align.op.bl_idname, text="+", icon_value = icon_get("op_align_center")).direction = "center"
		col.operator(op_align.op.bl_idname, text="↓", icon_value = icon_get("op_align_bottom")).direction = "bottom"

		col = row.column(align=True)
		# col.label(text="")
		col.operator(op_align.op.bl_idname, text="↗", icon_value = icon_get("op_align_topright")).direction = "topright"
		col.operator(op_align.op.bl_idname, text=" →", icon_value = icon_get("op_align_right")).direction = "right"
		col.operator(op_align.op.bl_idname, text="↘", icon_value = icon_get("op_align_bottomright")).direction = "bottomright"

		row_tr = col_tr.row(align=True)
		col = row_tr.column(align=True)
		col.scale_x = 0.5
		row = col.row(align=True)
		row.operator(op_align.op.bl_idname, text="—", icon_value = icon_get("op_align_horizontal")).direction = "horizontal"
		row.operator(op_align.op.bl_idname, text="|", icon_value = icon_get("op_align_vertical")).direction = "vertical"
		col = row_tr.column(align=True)
		col.prop(tt_settings(), "align_mode", text="", expand=False)

		col_tr.separator()
		row = col_tr.row(align=True)
		row.operator(op_island_rotate_90.op.bl_idname, text="90° CCW", icon_value = icon_get("op_island_rotate_90_left")).angle = -math.pi / 2
		row.operator(op_island_rotate_90.op.bl_idname, text="90° CW", icon_value = icon_get("op_island_rotate_90_right")).angle = math.pi / 2
		row = col_tr.row(align=True)
		row.operator(op_island_mirror.op.bl_idname, text="Mirror H", icon_value = icon_get("op_island_mirror_H")).is_vertical = False
		row.operator(op_island_mirror.op.bl_idname, text="Mirror V", icon_value = icon_get("op_island_mirror_V")).is_vertical = True

		col = box.column(align=True)
		row = col.row(align=True)
		op = row.operator(op_island_align_sort.op.bl_idname, text="Sort H", icon_value = icon_get("op_island_align_sort_h"))
		op.is_vertical = False
		op.padding = utilities_ui.get_padding()
		
		op = row.operator(op_island_align_sort.op.bl_idname, text="Sort V", icon_value = icon_get("op_island_align_sort_v"))
		op.is_vertical = True
		op.padding = utilities_ui.get_padding()

		aligned = box.row(align=True)
		col = aligned.column(align=True)

		row = col.row(align=True)
		row.operator(op_island_centralize.op.bl_idname, text="Centralize", icon_value = icon_get("op_island_centralize"))
		row.operator(op_randomize.op.bl_idname, text="Randomize", icon_value = icon_get("op_randomize"))

		col.separator()

		row = col.row(align=True)
		row.operator(op_island_straighten_edge_loops.op.bl_idname, text="Straight", icon_value = icon_get("op_island_straighten_edge_loops"))
		row.operator(op_rectify.op.bl_idname, text="Rectify", icon_value = icon_get("op_rectify"))

		split = col.split(factor=0.75, align=True)
		split.operator(op_uv_unwrap.op.bl_idname, text="Unwrap", icon_value = icon_get("op_uv_unwrap")).axis = ''
		row = split.row(align=True)
		row.operator(op_uv_unwrap.op.bl_idname, text="U").axis = "x"
		row.operator(op_uv_unwrap.op.bl_idname, text="V").axis = "y"
		
		if settings.bversion >= 3.2:
			row = col.row(align=True)
			row.scale_y = 1.25
			row.operator(op_relax.op.bl_idname, text="Relax", icon_value = icon_get("op_relax"))

		col.separator()
		if settings.bversion >= 3.2:
			col.operator(op_stitch.op.bl_idname, text="Stitch", icon_value = icon_get("op_meshtex_trim_collapse"))
		col.operator(op_unwrap_edge_peel.op.bl_idname, text="Edge Peel", icon_value = icon_get("op_unwrap_edge_peel"))
		row = col.row(align=True)
		row.scale_y = 1.5
		row.operator(op_unwrap_faces_iron.op.bl_idname, text="Iron Faces", icon_value = icon_get("op_unwrap_faces_iron"))

		col.separator()

		# col = box.column(align=True)
		row = col.row(align=True)
		row.label(text="" , icon_value = icon_get("texel_density"))
		row.separator()
		row.prop(tt_settings(), "texel_density", text="")

		row = col.row(align=True)
		row.operator(op_texel_density_get.op.bl_idname, text="Pick", icon = 'EYEDROPPER')
		row.prop(tt_settings(), "texel_get_mode", text = "", expand=False)

		row = col.row(align=True)
		row.operator(op_texel_density_set.op.bl_idname, text="Apply", icon = 'FACESEL')
		row.prop(tt_settings(), "texel_set_mode", text = "", expand=False)

		#---------- Selection ----------

		# box = layout.box()
		# box.label(text="Select")
		# col = box.column(align=True)
		col.separator()

		row = col.row(align=True)
		row.operator(op_select_islands_identical.op.bl_idname, text="Similar", icon_value = icon_get("op_select_islands_identical"))
		row.operator(op_select_islands_overlap.op.bl_idname, text="Overlap", icon_value = icon_get("op_select_islands_overlap"))

		row = col.row(align=True)
		row.operator(op_select_zero.op.bl_idname, text="Zero", icon_value = icon_get("op_select_zero"))
		row.operator(op_select_islands_flipped.op.bl_idname, text="Flipped", icon_value = icon_get('op_select_islands_flipped'))

		if settings.bversion >= 3.2:
			row = col.row(align=True)
			row.operator(op_select_islands_outline.op.bl_idname, text="Bounds", icon_value = icon_get("op_select_islands_outline"))




class UI_PT_Panel_Bake(Panel):
	bl_label = " "
	bl_space_type = 'IMAGE_EDITOR'
	bl_region_type = 'UI'
	bl_category = "TexTools"
	bl_options = {'DEFAULT_CLOSED'}

	def draw_header(self, _):
		layout = self.layout
		row = layout.row(align=True)
		if bpy.context.preferences.addons[__package__].preferences.bool_help:
			row.operator("wm.url_open", text="", icon='INFO').url = "http://renderhjs.net/textools/blender/index.html#texturebaking"
		row.label(text ="Baking")

	def draw(self, context):
		layout = self.layout
		preferences = prefs()
		
		#----------- Baking -------------
		row = layout.row()
		box = row.box()
		col = box.column(align=True)

		if not (tt_settings().bake_freeze_selection and len(settings.sets) > 0):
			# Update sets
			settings.sets = utilities_bake.get_bake_sets()


		# Bake Button
		count = 0
		if tt_settings().bake_force == "Single" and len(settings.sets) > 0:
			count = 1
		else:
			count = len(settings.sets)
		
		row = col.row(align=True)
		row.scale_y = 1.75
		row.operator(op_bake.op.bl_idname, text=f'Bake {count}x', icon_value=icon_get('op_bake'))

		bake_mode = utilities_ui.get_bake_mode()

		# Warning on material or Principled BSDF node need
		if settings.bake_error != "":
			col.label(text=settings.bake_error, icon='ERROR')

		col.separator()
		col_tr = col.column(align=True)
		row = col_tr.row(align=True)
		col = row.column(align=True)

		col.label(text="AA:")
		col.label(text="CS:")
		if preferences.bool_bake_back_color == 'CUSTOM':
			col.label(text="BG:")

		col = row.column(align=True)
		col.scale_x = 1.75

		# anti aliasing
		col.prop(tt_settings(), "bake_sampling", text="", icon_value =icon_get("bake_anti_alias"))
		
		# Color Space selector
		col.prop(tt_settings(), "bake_color_space", text="", icon_value =icon_get("bake_color_space"))

		# Background Color Picker
		if preferences.bool_bake_back_color == 'CUSTOM':
			col.prop(tt_settings(), "bake_back_color", text="")
		
		col = box.column(align=True)

		# Collected Related Textures
		if settings.bversion >= 3.0:
			row = col.row(align=True)
			row.scale_y = 1.5
			row.operator(op_texture_preview.op.bl_idname, text = "Preview Texture", icon_value = icon_get("op_texture_preview"))
			row.operator(op_texture_preview_cleanup.op.bl_idname, text = "", icon = 'TRASH')

		images = utilities_bake.get_baked_images(settings.sets)

		if len(images) > 0:

			image_background = None
			for area in bpy.context.screen.areas:
				if area.ui_type == 'UV':
					if area.spaces[0].image:
						image_background = area.spaces[0].image
						break

			box = col.box()
			# box.label(text="{}x images".format(len(images)), icon="IMAGE_DATA")
			col_box = box.column(align=True)
			for image in images:
				row = col_box.row(align=True)

				# row.label(text=image.name, icon='')
				icon = 'RADIOBUT_OFF'
				if image == image_background:
					icon = 'RADIOBUT_ON'
				row.operator(op_texture_select.op.bl_idname, text=image.name, icon=icon).name = image.name
	
				row = row.row(align=True)
				row.alignment = 'RIGHT'
				if image.filepath != "":
					row.operator(op_texture_open.op.bl_idname, text="", icon_value=icon_get("op_texture_open") ).name = image.name
				else:
					if bpy.app.debug_value != 0:
						row.operator(op_texture_save.op.bl_idname, text="", icon_value=icon_get("op_texture_save") ).name = image.name
					else:
						pass
				
				row.operator(op_texture_remove.op.bl_idname, text="", icon='X' ).name = image.name

				
			col.separator()


		# Bake Mode
		col.template_icon_view(bpy.context.scene, "TT_bake_mode", scale=5.0, scale_popup=preferences.bake_mode_panel_scale)

		if bpy.app.debug_value != 0:
			row = col.row()
			row.label(text=f"--> Mode: '{bpy.context.scene.TT_bake_mode}'")

		# Warning: Wrong bake mode, require 
		if bake_mode == 'diffuse':
			if bpy.context.scene.render.engine != 'CYCLES':
				if bpy.context.scene.render.engine != op_bake.modes[bake_mode].engine:
					col.label(text=f"Requires '{op_bake.modes[bake_mode].engine}'", icon='ERROR')

		# Optional Parameters
		col.separator()
		for bset in settings.sets:
			if len(bset.objects_high) > 0 and len(bset.objects_low) > 0:
				col.prop(tt_settings(), "bake_cage_extrusion")
				if settings.bversion >= 2.90:
					col.prop(tt_settings(), "bake_ray_distance")
				break

		# Display Bake mode properties / parameters
		if bake_mode in op_bake.modes:
			if bake_mode == 'combined':
				bake_settings = bpy.context.scene.render.bake
				col.prop(tt_settings(), "bake_samples")
				col.label(text="Lighting:")
				col.prop(bake_settings, "use_pass_direct")
				col.prop(bake_settings, "use_pass_indirect")
				col.label(text="Contributions:")
				col.prop(bake_settings, "use_pass_diffuse")
				col.prop(bake_settings, "use_pass_glossy")
				col.prop(bake_settings, "use_pass_transmission")
				if settings.bversion < 3:
					col.prop(bake_settings, "use_pass_ambient_occlusion")
				col.prop(bake_settings, "use_pass_emit")
			else:
				params = op_bake.modes[bake_mode].params
				if len(params) > 0:
					for param in params:
						col.prop(tt_settings(), param)

		# Warning about projection requirement
		if op_bake.modes[bake_mode].use_project == True and len(settings.sets) > 0:
			if len(settings.sets[0].objects_high) == 0 or len(settings.sets[0].objects_low) == 0:
				col.label(text="Need high and low;", icon='ERROR')
				row = col.row()
				row.label(text="       use suffixes as _hp, _lp")


		box = layout.box()
		col = box.column(align=True)
		
		# Select by type
		if len(settings.sets) > 0:
			row = col.row(align=True)
			row.active = len(settings.sets) > 0

			count_types = {
				'low':0, 'high':0, 'cage':0, 'float':0, 'issue':0, 
			}
			for bset in settings.sets:
				if bset.has_issues:
					count_types['issue']+=1
				if len(bset.objects_low) > 0:
					count_types['low']+=1
				if len(bset.objects_high) > 0:
					count_types['high']+=1
				if len(bset.objects_cage) > 0:
					count_types['cage']+=1
				if len(bset.objects_float) > 0:
					count_types['float']+=1

			# Freeze Selection
			c = row.column(align=True)
			c.active = len(settings.sets) > 0 or tt_settings().bake_freeze_selection
			icon = 'LOCKED' if tt_settings().bake_freeze_selection else 'UNLOCKED'
			c.prop(tt_settings(), "bake_freeze_selection", text=f'Lock {len(settings.sets)}x', icon=icon)

			# Select by type
			if count_types['issue'] > 0:
				row.operator("uv.op_select_bake_type", text='', icon='ERROR').select_type = 'issue'

			row.operator("uv.op_select_bake_type", text='', icon_value=icon_get("bake_obj_low")).select_type = 'low'
			row.operator("uv.op_select_bake_type", text='', icon_value=icon_get("bake_obj_high")).select_type = 'high'
			
			if count_types['float'] > 0:
				row.operator("uv.op_select_bake_type", text='', icon_value=icon_get("bake_obj_float")).select_type = 'float'
			
			if count_types['cage'] > 0:
				row.operator("uv.op_select_bake_type", text='', icon_value=icon_get("bake_obj_cage")).select_type = 'cage'

			# List bake sets
			box2 = box.box()
			row = box2.row()
			split = None

			countTypes = (0 if count_types['low'] == 0 else 1) + (0 if count_types['high'] == 0 else 1) + (0 if count_types['cage'] == 0 else 1) + (0 if count_types['float'] == 0 else 1)
			if countTypes > 2:
				# More than 3 types, use less space for label
				split = row.split(factor=0.45)
			else:
				# Only 2 or less types, use more space for label
				split = row.split(factor=0.55)

			c = split.column(align=True)
			for s,bset in enumerate(settings.sets):
				r = c.row(align=True)
				r.active = not (tt_settings().bake_force == "Single" and s > 0)

				if bset.has_issues:
					r.operator("uv.op_select_bake_set", text=bset.name, icon='ERROR').select_set = bset.name 
				else:
					r.operator("uv.op_select_bake_set", text=bset.name).select_set = bset.name 


			c = split.column(align=True)
			for bset in settings.sets:
				r = c.row(align=True)
				r.alignment = "LEFT"

				if len(bset.objects_low) > 0:
					r.label(text=f'{len(bset.objects_low)}', icon_value=icon_get("bake_obj_low"))
				elif count_types['low'] > 0:
					r.label(text="")

				if len(bset.objects_high) > 0:
					r.label(text=f'{len(bset.objects_high)}', icon_value=icon_get("bake_obj_high"))
				elif count_types['high'] > 0:
					r.label(text="")

				if len(bset.objects_float) > 0:
					r.label(text=f'{len(bset.objects_float)}', icon_value=icon_get("bake_obj_float"))
				elif count_types['float'] > 0:
					r.label(text="")

				if len(bset.objects_cage) > 0:
					r.label(text=f'{len(bset.objects_cage)}', icon_value=icon_get("bake_obj_cage"))
				elif count_types['cage'] > 0:
					r.label(text="")

			# Force single or multi texture baking
			col = box2.column(align=True)
			col.prop(tt_settings(), "bake_force", text="Force")
			if tt_settings().bake_force == "Single" and len(settings.sets) > 0:
				row.label(text=f"'{settings.sets[0].name}'")


		col = box.column(align=True)
		col.operator(op_bake_organize_names.op.bl_idname, text=f'Organize {len(bpy.context.selected_objects)}x', icon='BOOKMARKS')
		col.operator(op_bake_explode.op.bl_idname, text="Explode", icon_value=icon_get("op_bake_explode"))




class UI_MT_op_color_dropdown_io(Menu):
	bl_idname = "UI_MT_op_color_dropdown_io"
	bl_label = "IO"

	def draw(self, context):
		layout = self.layout

		layout.operator(op_color_io_export.op.bl_idname, text="Export Colors", icon = 'EXPORT')
		layout.operator(op_color_io_import.op.bl_idname, text="Import Colors", icon = 'IMPORT')




class UI_MT_op_color_dropdown_convert_from(Menu):
	bl_idname = "UI_MT_op_color_dropdown_convert_from"
	bl_label = "From"
	bl_description = "Create Color IDs from ..."

	def draw(self, context):
		layout = self.layout
		layout.operator(op_color_from_elements.op.bl_idname, text="Mesh Elements", icon_value = icon_get('op_color_from_elements'))
		layout.operator(op_color_from_materials.op.bl_idname, text="Materials", icon_value = icon_get('op_color_from_materials'))
		layout.operator(op_color_from_directions.op.bl_idname, text="Directions", icon_value = icon_get('op_color_from_directions'))
			



class UI_MT_op_color_dropdown_convert_to(Menu):
	bl_idname = "UI_MT_op_color_dropdown_convert_to"
	bl_label = "To"
	bl_description = "Convert Color IDs into ..."

	def draw(self, context):
		layout = self.layout
		layout.operator(op_color_convert_texture.op.bl_idname, text="Texture Atlas", icon_value = icon_get('op_color_convert_texture'))
		layout.operator(op_color_convert_vertex_colors.op.bl_idname, text="Vertex Colors", icon_value = icon_get("op_color_convert_vertex_colors"))



"""
class UV_OT_op_enable_cycles(Operator):
	bl_idname = "uv.textools_enable_cycles"
	bl_label = "Enable Cycles"
	bl_description = "Enable Cycles render engine"

	@classmethod
	def poll(cls, context):
		return True

	def execute(self, context):
		bpy.context.scene.render.engine = 'CYCLES'
		return {'FINISHED'}
"""



class UI_PT_Panel_Colors(Panel):
	bl_label = " "
	bl_space_type = 'IMAGE_EDITOR'
	bl_region_type = 'UI'
	bl_category = "TexTools"
	bl_options = {'DEFAULT_CLOSED'}

	def draw_header(self, _):
		layout = self.layout
		row = layout.row(align=True)
		if bpy.context.preferences.addons[__package__].preferences.bool_help:
			row.operator("wm.url_open", text="", icon='INFO').url = "http://renderhjs.net/textools/blender/index.html#colorid"
		row.label(text ="Color ID")

	def draw(self, context):
		layout = self.layout
		# layout.label(text="Select face and color")

		"""
		if bpy.context.scene.render.engine not in ('CYCLES', 'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
			row = layout.row(align=True)
			row.alert = True
			row.operator("uv.textools_enable_cycles", text="Enable 'CYCLES'", icon='CANCEL') #, icon='UV_SYNC_SELECT'
			return
		"""

		box = layout.box()
		col = box.column(align=True)

		def color_mode_icon():
			if tt_settings().color_assign_mode == 'MATERIALS':
				return icon_get("op_color_from_materials")
			else:
				return icon_get("op_color_convert_vertex_colors")

		row = col.row(align=True)
		split = row.split(factor=0.25, align=True)
		c = split.column(align=True)
		c.label(text="Mode:")
		c = split.column(align=True)
		c.prop(tt_settings(), "color_assign_mode", text="", icon_value = color_mode_icon())
		col.separator()

		row = col.row(align=True)
		split = row.split(factor=0.60, align=True)
		c = split.column(align=True)
		c.prop(tt_settings(), "color_ID_templates", text="")
		c = split.column(align=True)
		c.prop(tt_settings(), "color_ID_count", text="", expand=False)

		row = box.row(align=True)
		row.operator(op_color_clear.op.bl_idname, text="Clear", icon = 'X')
		row.menu(UI_MT_op_color_dropdown_io.bl_idname, icon='COLOR')


		max_columns = 5
		if tt_settings().color_ID_count < max_columns:
			max_columns = tt_settings().color_ID_count

		count = math.ceil(tt_settings().color_ID_count / max_columns)*max_columns

		# TODO: Simplify

		for i in range(count):

			if i%max_columns == 0:
				row = box.row(align=True)

			col = row.column(align=True)
			if i < tt_settings().color_ID_count:
				col.prop(tt_settings(), f"color_ID_color_{i}", text='')
				col.operator(op_color_assign.op.bl_idname, text='', icon="FILE_TICK").index = i
	
				if bpy.context.active_object:
					if bpy.context.active_object in bpy.context.selected_objects:
						if len(bpy.context.selected_objects) == 1:
							if bpy.context.active_object.type == 'MESH' and context.scene.texToolsSettings.color_assign_mode == 'MATERIALS':
								col.operator(op_color_select.op.bl_idname, text="", icon = "FACESEL").index = i
							else:
								col.operator(op_color_select_vertex.op.bl_idname, text="", icon = "FACESEL").index = i
			else:
				col.label(text=" ")

		if context.scene.texToolsSettings.color_assign_mode != "MATERIALS":
			row = box.row(align=True)
			row.prop(context.scene.texToolsSettings, "vertex_color_threshold", text="Threshold", expand=True)

		col = box.column(align=True)
		col.label(text="Convert:")
		row = col.row(align=True)
		row.menu(UI_MT_op_color_dropdown_convert_from.bl_idname)  # icon='IMPORT'
		row.menu(UI_MT_op_color_dropdown_convert_to.bl_idname,)	  # icon='EXPORT'



class UI_PT_Panel_MeshTexture(Panel):
	bl_label = " "
	bl_space_type = 'IMAGE_EDITOR'
	bl_region_type = 'UI'
	bl_category = "TexTools"
	bl_options = {'DEFAULT_CLOSED'}

	def draw_header(self, _):
		layout = self.layout
		row = layout.row(align=True)
		if bpy.context.preferences.addons[__package__].preferences.bool_help:
			row.operator("wm.url_open", text="", icon='INFO').url = "http://renderhjs.net/textools/blender/index.html#meshtexture"
		row.label(text ="Mesh UV Tools")

	def draw(self, context):
		layout = self.layout
		box = layout.box()

		if settings.bversion >= 3.2:
			col = box.column(align=True)
			row = col.row(align=True)
			row.scale_y = 1.5
			row.operator(op_meshtex_create.op.bl_idname, text="Create UV Mesh", icon_value = icon_get("op_meshtex_create"))

			row = col.row(align=True)
			row.operator(op_meshtex_trim.op.bl_idname, text="Trim", icon_value = icon_get("op_meshtex_trim"))

			# Warning about trimmed mesh
			if op_meshtex_trim_collapse.is_available():
				row.operator(op_meshtex_trim_collapse.op.bl_idname, text="Collapse Trim", icon_value=icon_get("op_meshtex_trim_collapse"))

			col = box.column(align=True)
			row = col.row(align = True)
			row.operator(op_meshtex_wrap.op.bl_idname, text="Wrap", icon_value = icon_get("op_meshtex_wrap"))

			row = col.row(align = True)
			if not utilities_meshtex.find_uv_mesh(bpy.context.selected_objects):
				row.enabled = False
			row.prop(tt_settings(), "meshtexture_wrap", text="Wrap")

		col = box.column(align=True)
		row = col.row(align=True)
		row.scale_y = 1.5
		row.operator(op_meshtex_pattern.op.bl_idname, text="Create Pattern", icon_value = icon_get("op_meshtex_pattern"))

		col = box.column(align=True)
		row = col.row(align=True)
		row.scale_y = 1.5
		row.operator(op_smoothing_uv_islands.op.bl_idname, text="Smooth by UV Islands", icon_value = icon_get("op_smoothing_uv_islands"))



keymaps = []

def icon_get(name):
	return utilities_ui.icon_get(name)


def menu_IMAGE_uvs(self, context):
	layout = self.layout
	layout.separator()
	layout.operator(op_uv_resize.op.bl_idname, text="Resize", icon_value = icon_get("op_extend_canvas_open"))
	layout.operator(op_rectify.op.bl_idname, text="Rectify", icon_value = icon_get("op_rectify"))
	layout.operator(op_uv_crop.op.bl_idname, text="Crop", icon_value = icon_get("op_uv_crop"))
	layout.operator(op_uv_fill.op.bl_idname, text="Fill", icon_value = icon_get("op_uv_fill"))
	layout.operator(op_uv_unwrap.op.bl_idname, text="Unwrap", icon_value = icon_get("op_uv_unwrap"))
	if settings.bversion >= 3.2:
		layout.operator(op_relax.op.bl_idname, text="Relax", icon_value = icon_get("op_relax"))

	layout.separator()
	layout.operator(op_island_align_sort.op.bl_idname, text="Sort H", icon_value = icon_get("op_island_align_sort_h"))
	layout.operator(op_island_align_sort.op.bl_idname, text="Sort V", icon_value = icon_get("op_island_align_sort_v"))
		
	layout.separator()
	layout.menu("VIEW3D_MT_submenu_align")
	layout.operator(op_island_align_edge.op.bl_idname, text="Align Edge", icon_value = icon_get("op_island_align_edge"))
	layout.operator(op_island_align_world.op.bl_idname, text="Align World", icon_value = icon_get("op_island_align_world"))

	layout.separator()
	layout.operator(op_island_centralize.op.bl_idname, text="Centralize Position", icon_value = icon_get("op_island_centralize"))
	layout.operator(op_randomize.op.bl_idname, text="Randomize Position", icon_value = icon_get("op_randomize"))



class VIEW3D_MT_submenu_align(Menu):
	bl_label="Align"
	bl_idname="VIEW3D_MT_submenu_align"
	def draw(self, context):
		layout = self.layout
		layout.operator(op_align.op.bl_idname, text="←", icon_value = icon_get("op_align_left")).direction = "left"
		layout.operator(op_align.op.bl_idname, text="↑", icon_value = icon_get("op_align_top")).direction = "top"
		layout.operator(op_align.op.bl_idname, text="↓", icon_value = icon_get("op_align_bottom")).direction = "bottom"
		layout.operator(op_align.op.bl_idname, text="→", icon_value = icon_get("op_align_right")).direction = "right"



def menu_IMAGE_select(self, context):
	layout = self.layout
	layout.separator()
	layout.operator(op_select_islands_identical.op.bl_idname, text="Similar", icon_value = icon_get("op_select_islands_identical"))
	layout.operator(op_select_islands_overlap.op.bl_idname, text="Overlap", icon_value = icon_get("op_select_islands_overlap"))
	layout.operator(op_select_zero.op.bl_idname, text="Zero", icon_value = icon_get("op_select_zero"))
	layout.operator(op_select_islands_flipped.op.bl_idname, text="Flipped", icon_value = icon_get('op_select_islands_flipped'))
	if settings.bversion >= 3.2:
		layout.operator(op_select_islands_outline.op.bl_idname, text="Bounds", icon_value = icon_get("op_select_islands_outline"))

def menu_IMAGE_MT_image(self, context):
	layout = self.layout
	layout.separator()
	layout.operator(op_texture_reload_all.op.bl_idname, text="Reload Textures", icon_value = icon_get("op_texture_reload_all"))
	if settings.bversion >= 3.0:
		layout.operator(op_texel_checker_map.op.bl_idname, text ="Checker Map", icon_value = icon_get("op_texel_checker_map"))
		layout.operator(op_texel_checker_map_cleanup.op.bl_idname, text ="Checker Map cleanup", icon = 'TRASH')
		layout.operator(op_texture_preview.op.bl_idname, text = "Preview Texture", icon_value = icon_get("op_texture_preview"))
		layout.operator(op_texture_preview_cleanup.op.bl_idname, text = "Preview Texture cleanup", icon = 'TRASH')

def menu_VIEW3D_MT_object(self, context):
	self.layout.separator()
	if settings.bversion >= 3.0:
		self.layout.operator(op_texel_checker_map.op.bl_idname, text ="Checker Map", icon_value = icon_get("op_texel_checker_map"))
		self.layout.operator(op_texel_checker_map_cleanup.op.bl_idname, text ="Checker Map cleanup", icon = 'TRASH')
	if settings.bversion >= 3.2:
		self.layout.operator(op_meshtex_create.op.bl_idname, text="Create UV Mesh", icon_value = icon_get("op_meshtex_create"))
	self.layout.operator(op_smoothing_uv_islands.op.bl_idname, text="Smooth by UV Islands", icon_value = icon_get("op_smoothing_uv_islands"))

def menu_VIEW3D_MT_mesh_add(self, context):
	self.layout.operator(op_meshtex_pattern.op.bl_idname, text="Create Pattern", icon_value = icon_get("op_meshtex_pattern"))

def menu_VIEW3D_MT_uv_map(self, context):
	layout = self.layout
	layout.separator()
	layout.operator(op_unwrap_edge_peel.op.bl_idname, text="Edge Peel", icon_value = icon_get("op_unwrap_edge_peel"))
	layout.operator(op_unwrap_faces_iron.op.bl_idname, text="Iron Faces", icon_value = icon_get("op_unwrap_faces_iron"))

def menu_VIEW3D_MT_object_context_menu(self, context):
	layout = self.layout
	layout.separator()
	if settings.bversion >= 3.2:
		layout.operator(op_meshtex_create.op.bl_idname, text="Create UV Mesh", icon_value = icon_get("op_meshtex_create"))
		# layout.operator(op_meshtex_trim.op.bl_idname, text="Trim", icon_value = icon_get("op_meshtex_trim"))
		# # Warning about trimmed mesh
		# if op_meshtex_trim_collapse.is_available():
		# 	layout.operator(op_meshtex_trim_collapse.op.bl_idname, text="Collapse Trim", icon='CANCEL')
		# layout.prop(context.scene.texToolsSettings, "meshtexture_wrap", text="Wrap")
		# layout.operator(op_meshtex_wrap.op.bl_idname, text="Wrap", icon_value = icon_get("op_meshtex_wrap"))
	layout.operator(op_smoothing_uv_islands.op.bl_idname, text="Smooth by UV Islands", icon_value = icon_get("op_smoothing_uv_islands"))



classes = (
			op_align.op,
			op_bake.op,
			op_bake_explode.op,
			op_bake_organize_names.op,
			op_texture_preview.op,
			op_texture_preview_cleanup.op,
			op_color_assign.op,
			op_color_clear.op,
			op_color_convert_texture.op,
			op_color_convert_vertex_colors.op,
			op_color_from_elements.op,
			op_color_from_materials.op,
			op_color_from_directions.op,
			op_edge_split_bevel.op,
			op_color_io_export.op,
			op_color_io_import.op,
			op_color_select.op,
			op_color_select_vertex.op,
			op_island_align_edge.op,
			op_island_align_sort.op,
			op_island_align_world.op,
			op_island_mirror.op,
			op_island_rotate_90.op,
			op_island_straighten_edge_loops.op,
			op_island_centralize.op,
			op_randomize.op,
			op_rectify.op,
			op_select_islands_identical.op,
			op_select_islands_outline.op,
			op_select_islands_overlap.op,
			op_select_islands_flipped.op,
			op_select_zero.op,
			op_relax.op,
			op_smoothing_uv_islands.op,
			op_meshtex_create.op,
			op_meshtex_wrap.op,
			op_meshtex_trim.op,
			op_meshtex_trim_collapse.op,
			op_meshtex_pattern.op,
			op_texel_checker_map.op,
			op_texel_checker_map_cleanup.op,
			op_texel_density_get.op,
			op_texel_density_set.op,
			op_texture_reload_all.op,
			op_texture_save.op,
			op_texture_open.op,
			op_texture_select.op,
			op_texture_remove.op,
			op_unwrap_faces_iron.op,
			op_stitch.op,
			op_unwrap_edge_peel.op,
			op_uv_channel_add.op,
			op_uv_channel_remove.op,
			op_uv_channel_swap.op,
			op_uv_crop.op,
			op_uv_fill.op,
			op_uv_resize.op,
			op_uv_size_get.op,
			op_uv_unwrap.op,
			utilities_ui.op_popup,
			UV_OT_op_debug,
			UV_OT_op_select_bake_set,
			UV_OT_op_select_bake_type,
			TexToolsSettings,
			UI_PT_Panel_Units,
			UI_PT_Panel_Layout,
			UI_PT_Panel_Bake,
			UI_MT_op_color_dropdown_io,
			UI_MT_op_color_dropdown_convert_from,
			UI_MT_op_color_dropdown_convert_to,
			UI_PT_Panel_Colors,
			UI_PT_Panel_MeshTexture,
			VIEW3D_MT_submenu_align,
			Panel_Preferences
)


def register():
	for c in classes:
		bpy.utils.register_class(c)

	# Register settings
	bpy.types.Scene.texToolsSettings = PointerProperty(type=TexToolsSettings)
	bpy.types.Object.TT_CM_Scale = bpy.props.FloatProperty(name="Tiling", description="Checker Map scale for the Active Object", default=1, min=0.0001, max=1000)

	# GUI Utilities
	utilities_ui.register()

	# Register Icons
	icons = [
		"bake_anti_alias.bip", 
		"bake_color_space.bip", 
		"bake_obj_cage.bip", 
		"bake_obj_float.bip", 
		"bake_obj_high.bip", 
		"bake_obj_low.bip", 
		"op_align_bottom.bip", 
		"op_align_topleft.bip", 
		"op_align_left.bip", 
		"op_align_bottomleft.bip", 
		"op_align_topright.bip", 
		"op_align_right.bip", 
		"op_align_bottomright.bip", 
		"op_align_top.bip",
		"op_align_horizontal.bip",
		"op_align_vertical.bip",
		"op_align_center.bip",		 
		"op_bake.bip", 
		"op_bake_explode.bip", 
		"op_color_convert_texture.bip", 
		"op_color_convert_vertex_colors.bip", 
		"op_color_from_directions.bip", 
		"op_color_from_elements.bip", 
		"op_color_from_materials.bip", 
		"op_extend_canvas_open.bip",
		"op_island_align_edge.bip", 
		"op_island_align_sort_h.bip", 
		"op_island_align_sort_v.bip", 
		"op_island_align_world.bip", 
		"op_island_mirror_H.bip", 
		"op_island_mirror_V.bip", 
		"op_island_rotate_90_left.bip", 
		"op_island_rotate_90_right.bip", 
		"op_island_straighten_edge_loops.bip", 
		"op_meshtex_create.bip",
		"op_meshtex_pattern.bip",
		"op_meshtex_trim.bip",
		"op_meshtex_trim_collapse.bip", 
		"op_meshtex_wrap.bip",
		"op_island_centralize.bip",
		"op_randomize.bip",
		"op_rectify.bip", 
		"op_relax.bip", 
		"op_select_islands_flipped.bip", 
		"op_select_zero.bip", 
		"op_select_islands_identical.bip", 
		"op_select_islands_outline.bip", 
		"op_select_islands_overlap.bip", 
		"op_smoothing_uv_islands.bip", 
		"op_texel_checker_map.bip", 
		"op_texture_preview.bip", 
		"op_texture_reload_all.bip",
		"op_texture_save.bip",
		"op_texture_open.bip",
		"op_unwrap_faces_iron.bip", 
		"op_unwrap_edge_peel.bip", 
		"op_uv_crop.bip", 
		"op_uv_fill.bip", 
		"op_uv_unwrap.bip",
		"texel_density.bip"
	]
	for icon in icons:
		utilities_ui.icon_register(icon)

	bpy.types.IMAGE_MT_uvs.append(menu_IMAGE_uvs)
	bpy.types.IMAGE_MT_select.append(menu_IMAGE_select)
	bpy.types.IMAGE_MT_image.append(menu_IMAGE_MT_image)
	bpy.types.VIEW3D_MT_object.append(menu_VIEW3D_MT_object)
	bpy.types.VIEW3D_MT_add.append(menu_VIEW3D_MT_mesh_add)
	bpy.types.VIEW3D_MT_uv_map.append(menu_VIEW3D_MT_uv_map)
	bpy.types.VIEW3D_MT_object_context_menu.append(menu_VIEW3D_MT_object_context_menu)


def unregister():
	try:

		for c in reversed(classes):
			bpy.utils.unregister_class(c)
	except Exception as e:
		print(e)

	# Right way for delete properties, but settings not save
	# https://blender.stackexchange.com/questions/304852/how-to-delete-custom-properties-from-blend-file/305156#305156
	# del bpy.types.Scene.texToolsSettings

	# GUI Utilities
	utilities_ui.unregister()

	# Handle the keymap
	for km, kmi in keymaps:
		km.keymap_items.remove(kmi)
	keymaps.clear()

	bpy.types.IMAGE_MT_uvs.remove(menu_IMAGE_uvs)
	bpy.types.IMAGE_MT_select.remove(menu_IMAGE_select)
	bpy.types.IMAGE_MT_image.remove(menu_IMAGE_MT_image)
	bpy.types.VIEW3D_MT_object.remove(menu_VIEW3D_MT_object)
	bpy.types.VIEW3D_MT_add.remove(menu_VIEW3D_MT_mesh_add)
	bpy.types.VIEW3D_MT_uv_map.remove(menu_VIEW3D_MT_uv_map)
	bpy.types.VIEW3D_MT_object_context_menu.remove(menu_VIEW3D_MT_object_context_menu)


	# Unregister Settings
	# del bpy.types.Scene.texToolsSettings
	del bpy.types.Object.TT_CM_Scale



if __name__ == "__main__":
	register()
