bl_info = {
	"name": "TexTools",
	"description": "Professional UV and Texture tools for Blender.",
	"author": "renderhjs, Sav Martin, franMarz",
	"version": (1, 4, 2),
	"blender": (2, 80, 0),
	"category": "UV",
	"location": "UV Image Editor > Tools > 'TexTools' panel",
	"wiki_url": "http://renderhjs.net/textools/blender/"
}


# Import local modules
# More info: https://wiki.blender.org/index.php/Dev:Py/Scripts/Cookbook/Code_snippets/Multi-File_packages
if "bpy" in locals():
	import imp
	imp.reload(utilities_ui)
	imp.reload(settings)
	imp.reload(utilities_bake)
	imp.reload(utilities_color)
	imp.reload(utilities_texel)
	imp.reload(utilities_uv)
	imp.reload(utilities_meshtex)
	
	imp.reload(op_align)
	imp.reload(op_bake)
	imp.reload(op_bake_explode)
	imp.reload(op_bake_organize_names)
	imp.reload(op_texture_preview)
	imp.reload(op_color_assign)
	imp.reload(op_color_clear)
	imp.reload(op_color_convert_texture)
	imp.reload(op_color_convert_vertex_colors)
	imp.reload(op_edge_split_bevel)
	imp.reload(op_color_from_elements)
	imp.reload(op_color_from_materials)
	imp.reload(op_color_from_directions)
	imp.reload(op_color_io_export)
	imp.reload(op_color_io_import)
	imp.reload(op_color_select)
	imp.reload(op_island_align_edge)
	imp.reload(op_island_align_sort)
	imp.reload(op_island_align_world)
	imp.reload(op_island_mirror)
	imp.reload(op_island_rotate_90)
	imp.reload(op_island_straighten_edge_loops)
	imp.reload(op_island_centralize)
	imp.reload(op_randomize)
	imp.reload(op_rectify)
	imp.reload(op_select_islands_identical)
	imp.reload(op_select_islands_outline)
	imp.reload(op_select_islands_overlap)
	imp.reload(op_select_islands_flipped)
	imp.reload(op_select_zero)
	imp.reload(op_smoothing_uv_islands)
	imp.reload(op_meshtex_create)
	imp.reload(op_meshtex_wrap)
	imp.reload(op_meshtex_trim)
	imp.reload(op_meshtex_trim_collapse)
	imp.reload(op_meshtex_pattern)
	imp.reload(op_texel_checker_map)
	imp.reload(op_texel_density_get)
	imp.reload(op_texel_density_set)
	imp.reload(op_texture_reload_all)
	imp.reload(op_texture_save)
	imp.reload(op_texture_open)
	imp.reload(op_texture_select)
	imp.reload(op_texture_remove)
	imp.reload(op_unwrap_faces_iron)
	imp.reload(op_unwrap_edge_peel)
	imp.reload(op_uv_channel_add)
	imp.reload(op_uv_channel_swap)
	imp.reload(op_uv_crop)
	imp.reload(op_uv_fill)
	imp.reload(op_uv_resize)
	imp.reload(op_uv_size_get)

	
else:
	from . import settings
	from . import utilities_ui
	from . import utilities_bake
	from . import utilities_color
	from . import utilities_texel
	from . import utilities_uv
	from . import utilities_meshtex

	from . import op_align
	from . import op_bake
	from . import op_bake_explode
	from . import op_bake_organize_names
	from . import op_texture_preview
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
	from . import op_smoothing_uv_islands
	from . import op_meshtex_create
	from . import op_meshtex_wrap
	from . import op_meshtex_trim
	from . import op_meshtex_trim_collapse
	from . import op_meshtex_pattern
	from . import op_texel_checker_map
	from . import op_texel_density_get
	from . import op_texel_density_set
	from . import op_texture_reload_all
	from . import op_texture_save
	from . import op_texture_open
	from . import op_texture_select
	from . import op_texture_remove
	from . import op_unwrap_faces_iron
	from . import op_unwrap_edge_peel
	from . import op_uv_channel_add
	from . import op_uv_channel_swap
	from . import op_uv_crop
	from . import op_uv_fill
	from . import op_uv_resize
	from . import op_uv_size_get
	

# Import general modules. Important: must be placed here and not on top
import bpy
import os
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



def on_bake_def_back_color_set(self, context):
	if self.bool_bake_back_color:
		bpy.context.scene.texToolsSettings.bake_back_color = self.bake_back_color_def


class Panel_Preferences(AddonPreferences):
	bl_idname = __package__

	# Addon Preferences https://docs.blender.org/api/blender_python_api_2_67_release/bpy.types.AddonPreferences.html
	swizzle_y_coordinate : EnumProperty(items= 
		[	
			('Y+', 'Y+ OpenGL', 'Used in Blender, Maya, Modo, Toolbag, Unity'), 
			('Y-', 'Y- Direct X', 'Used in 3ds Max, CryENGINE, Source, Unreal Engine')
		], 
		description="Color template",
		name = "Swizzle Coordinates", 
		default = 'Y+'
	)
	bake_32bit_float : EnumProperty(items= 
		[	
			('8', '8 Bit', ''), 
			('32', '32 Bit', '')
		], 
		description="", 
		name = "Image depth", 
		default = '8'
	)
	bake_back_color_def : FloatVectorProperty( 
		description="color picker", 
		name="Global custom baking background color", 
		subtype='COLOR', 
		size=4, 
		min=0, max=1, 
		default=(0.0, 0.0, 0.0, 1.0), 
		update = on_bake_def_back_color_set
	)
	bool_bake_back_color : EnumProperty(items= 
		[	
			('DEFAULT', 'Default', 'Use default TexTools background colors for baked textures'), 
			('CUSTOM', 'Custom', 'Set a global custom RGBA color for the background. Note that a transparent background can be specified')
		], 
		description="Mode for baked textures background color and alpha", 
		name = "Bake background", 
		default = 'DEFAULT', 
		update = on_bake_def_back_color_set
	)
	bool_help : BoolProperty(name="Show help links buttons on panels", default=True)


	def draw(self, context):
		layout = self.layout

		box = layout.box()
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
		col.prop(self, "bool_bake_back_color", icon='IMAGE_RGB_ALPHA')
		if self.bool_bake_back_color == 'CUSTOM':
			col.prop(self, "bake_back_color_def")

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
	bl_description = "Open console and enable dbug mode"

	@classmethod
	def poll(cls, context):
		return True

	def execute(self, context):
		bpy.app.debug = True# Debug Vertex indexies
		bpy.context.object.data.show_extra_indices = True
		bpy.app.debug_value = 1 #Set to Non '0
		return {'FINISHED'}



class UV_OT_op_disable_uv_sync(Operator):
	bl_idname = "uv.op_disable_uv_sync"
	bl_label = "Disable Sync"
	bl_description = "Disable UV sync mode"

	@classmethod
	def poll(cls, context):
		return True

	def execute(self, context):
		bpy.context.scene.tool_settings.use_uv_select_sync = False
		bpy.ops.mesh.select_all(action='SELECT')
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
		print("Set: "+self.select_set)
		if self.select_set != "":
			for set in settings.sets:
				if set.name == self.select_set:
					# Select this entire set
					bpy.ops.object.select_all(action='DESELECT')
					for obj in set.objects_low:
						obj.select_set( state = True, view_layer = None)
					for obj in set.objects_high:
						obj.select_set( state = True, view_layer = None)
					for obj in set.objects_cage:
						obj.select_set( state = True, view_layer = None)
					# Set active object to low poly to better visualize high and low wireframe color
					if len(set.objects_low) > 0:
						bpy.context.view_layer.objects.active = set.objects_low[0]

					break
		return {'FINISHED'}



class UV_OT_op_select_bake_type(Operator):
	bl_idname = "uv.op_select_bake_type"
	bl_label = "Select"
	bl_description = "Select bake objects of this type"

	select_type : StringProperty(default='low')

	@classmethod
	def poll(cls, context):
		return True

	def execute(self, context):
		objects = []
		for set in settings.sets:
			if self.select_type == 'low':
				objects+=set.objects_low
			elif self.select_type == 'high':
				objects+=set.objects_high
			elif self.select_type == 'cage':
				objects+=set.objects_cage
			elif self.select_type == 'float':
				objects+=set.objects_float
			elif self.select_type == 'issue' and set.has_issues:
				objects+=set.objects_low
				objects+=set.objects_high
				objects+=set.objects_cage
				objects+=set.objects_float

		bpy.ops.object.select_all(action='DESELECT')
		for obj in objects:
			obj.select_set( state = True, view_layer = None)

		return {'FINISHED'}



def on_dropdown_size(self, context):
	# Help: http://elfnor.com/drop-down-and-button-select-menus-for-blender-operator-add-ons.html
	size = int(bpy.context.scene.texToolsSettings.size_dropdown)
	bpy.context.scene.texToolsSettings.size[0] = size
	bpy.context.scene.texToolsSettings.size[1] = size

	if size <= 128:
		bpy.context.scene.texToolsSettings.padding = 2
	elif size <= 512:
		bpy.context.scene.texToolsSettings.padding = 4
	else:
		bpy.context.scene.texToolsSettings.padding = 8



def on_dropdown_uv_channel(self, context):
	if bpy.context.active_object != None:
		if bpy.context.active_object.type == 'MESH':
			if bpy.context.object.data.uv_layers:

				# Change Mesh UV Channel
				index = int(bpy.context.scene.texToolsSettings.uv_channel)
				if index < len(bpy.context.object.data.uv_layers):
					bpy.context.object.data.uv_layers.active_index = index
					bpy.context.object.data.uv_layers[index].active_render = True



def on_color_changed(self, context):
	for i in range(0, context.scene.texToolsSettings.color_ID_count):
		utilities_color.assign_color(i)



def on_color_dropdown_template(self, context):
	# Change Mesh UV Channel
	hex_colors = bpy.context.scene.texToolsSettings.color_ID_templates.split(',')
	bpy.context.scene.texToolsSettings.color_ID_count = len(hex_colors)

	# Assign color slots
	for i in range(0, len(hex_colors)):
		color = utilities_color.hex_to_color("#"+hex_colors[i])
		utilities_color.set_color(i, color)
		utilities_color.assign_color(i)



def on_color_count_changed(self, context):
	if bpy.context.active_object != None:
		utilities_color.validate_face_colors(bpy.context.active_object)



def get_dropdown_uv_values(self, context):
	# Requires mesh and UV data
	if bpy.context.active_object != None:
		if bpy.context.active_object.type == 'MESH':
			if bpy.context.object.data.uv_layers:
				options = []
				step = 0
				for uvLoop in bpy.context.object.data.uv_layers:
					# options.append((str(step), "#{}  {}".format(step+1, uvLoop.name), "Change UV channel to '{}'".format(uvLoop.name), step))
					options.append((str(step), "UV {}".format(step+1), "Change UV channel to '{}'".format(uvLoop.name), step))
					step+=1

				return options
	return []



def on_slider_meshtexture_wrap(self, context):
	value = bpy.context.scene.texToolsSettings.meshtexture_wrap
	obj_uv = utilities_meshtex.find_uv_mesh(bpy.context.selected_objects)
	if obj_uv:
		obj_uv.data.shape_keys.key_blocks["model"].value = value



class TexToolsSettings(PropertyGroup):

	def get_bake_back_color(self):
		return self.get("bake_back_color", bpy.context.preferences.addons[__package__].preferences.bake_back_color_def)
	
	def set_bake_back_color(self, value):
		if value is not None:
			self["bake_back_color"] = value

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
	padding : IntProperty(
		name = "Padding",
		description="padding size in pixels",
		default = 4,
		min = 0,
		max = 256
	)
	bake_samples : FloatProperty(
		name = "Samples",
		description = "Samples in Cycles for Baking. The higher the less noise. Default: 64",
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
		description = "Wireframe Thickness in pixels",
		default = 1,
		min = 0.1,
		max = 4.0
	)
	bake_bevel_size : FloatProperty(
		name = "Radius",
		description = "Bevel radius 1 to 16",
		default = 0.05,
		min = 0.0,
		max = 1.0
	)
	bake_bevel_samples : IntProperty(
		name = "Bevel Samples",
		description = "Bevel Samples",
		default = 4,
		min = 1,
		max = 16
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
	bake_force_single : BoolProperty(
		name="Single Texture",
		description="Force a single texture bake accross all selected objects",
		default = False
	)
	bake_sampling : EnumProperty(items= 
		[('1', 'None', 'No Anti Aliasing (Fast)'), 
		('2', '2x', 'Render 2x and downsample'), 
		('4', '4x', 'Render 2x and downsample')], name = "AA", default = '1'
	)
	bake_color_space : EnumProperty(items= 
		[('sRGB', 'sRGB', 'Standard RGB output color space for the baked texture'), 
		('Non-Color', 'Linear', 'Linear or Non-Color output color space for the baked texture')], name = "CS", default = 'sRGB'
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
	texel_mode_scale : EnumProperty(items= 
		[('ISLAND', 'Islands', 'Scale UV islands to match Texel Density'), 
		('ALL', 'Combined', 'Scale all UVs together to match Texel Density')], 
		name = "Mode", 
		default = 'ISLAND'
	)
	texel_density : FloatProperty(
		name = "Texel",
		description = "Texel size or Pixels per 1 unit ratio",
		default = 256,
		min = 0.0
		# max = 100.00
	)
	meshtexture_wrap : FloatProperty(
		name = "Wrap",
		description = "Transition of mesh texture wrap",
		default = 0,
		min = 0,
		max = 1,
		update = on_slider_meshtexture_wrap, 
		subtype  = 'FACTOR'
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
		)#, update=update_color_1

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
		#layout.label(text="Size: {} x {}".format(bpy.context.scene.texToolsSettings.size[0], bpy.context.scene.texToolsSettings.size[1]))

	def draw(self, context):
		layout = self.layout
		
		if bpy.app.debug_value != 0:
			row = layout.row()
			row.alert =True
			row.operator("uv.op_debug", text="DEBUG", icon="CONSOLE")
		
		#---------- Settings ------------
		# row = layout.row()
		col = layout.column(align=True)
		r = col.row(align = True)
		r.prop(context.scene.texToolsSettings, "size_dropdown", text="Size")
		r.operator(op_uv_size_get.op.bl_idname, text="", icon = 'EYEDROPPER')

		r = col.row(align = True)
		r.prop(context.scene.texToolsSettings, "size", text="")

		r = col.row(align = True)
		r.prop(context.scene.texToolsSettings, "padding", text="Padding")
		r.operator(op_uv_resize.op.bl_idname, text="Resize", icon_value = icon_get("op_extend_canvas_open"))
		

		# col.operator(op_extend_canvas.op.bl_idname, text="Resize", icon_value = icon_get("op_extend_canvas"))
		

		# UV Channel
		
		row = layout.row()

		has_uv_channel = False
		if bpy.context.active_object and len(bpy.context.selected_objects) == 1:
			if bpy.context.active_object in bpy.context.selected_objects:
				if bpy.context.active_object.type == 'MESH':
					
					# split = row.split(percentage=0.25)
					# c = row.column(align=True)
					# r = row.row(align=True)
					# r.alignment = 'RIGHT'
					# r.expand =
					# row.label(text="UV")#, icon='GROUP_UVS'

					
					if not bpy.context.object.data.uv_layers:
						# c = split.column(align=True)
						# row = c.row(align=True)
						# row.label(text="None", icon= 'ERROR')

						row.operator(op_uv_channel_add.op.bl_idname, text="Add", icon = 'REMOVE')
					else:
						# c = split.column(align=True)
						# row = c.row(align=True)
						group = row.row(align=True)
						group.prop(context.scene.texToolsSettings, "uv_channel", text="")
						group.operator(op_uv_channel_add.op.bl_idname, text="", icon = 'ADD')

						# c = split.column(align=True)
						# row = c.row(align=True)
						# row.alignment = 'RIGHT'
						group = row.row(align=True)
						r = group.column(align=True)
						r.active = bpy.context.object.data.uv_layers.active_index > 0
						r.operator(op_uv_channel_swap.op.bl_idname, text="", icon = 'TRIA_UP_BAR').is_down = False
						
						r = group.column(align=True)
						r.active = bpy.context.object.data.uv_layers.active_index < (len(bpy.context.object.data.uv_layers)-1)
						r.operator(op_uv_channel_swap.op.bl_idname, text="", icon = 'TRIA_DOWN_BAR').is_down = True

					has_uv_channel = True
		if not has_uv_channel:
			row.label(text="UV")


		col = layout.column(align=True)

		# col.separator()
		col.operator(op_texture_reload_all.op.bl_idname, text="Reload Textures", icon_value = icon_get("op_texture_reload_all"))
		
		row = col.row(align=True)
		row.scale_y = 1.75
		row.operator(op_texel_checker_map.op.bl_idname, text ="Checker Map", icon_value = icon_get("op_texel_checker_map"))
		

			
			

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

		if bpy.context.active_object and bpy.context.active_object.mode == 'EDIT' and bpy.context.scene.tool_settings.use_uv_select_sync:
			row = col.row(align=True)
			row.alert = True
			row.operator("uv.op_disable_uv_sync", text="Disable sync", icon='CANCEL')#, icon='UV_SYNC_SELECT'


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
		#col.label(text="")
		col.operator(op_align.op.bl_idname, text="←↑", icon_value = icon_get("op_align_topleft")).direction = "topleft"
		col.operator(op_align.op.bl_idname, text="← ", icon_value = icon_get("op_align_left")).direction = "left"
		col.operator(op_align.op.bl_idname, text="←↓", icon_value = icon_get("op_align_bottomleft")).direction = "bottomleft"
		
		col = row.column(align=True)
		col.operator(op_align.op.bl_idname, text="↑", icon_value = icon_get("op_align_top")).direction = "top"
		col.operator(op_align.op.bl_idname, text="+", icon_value = icon_get("op_align_center")).direction = "center"
		col.operator(op_align.op.bl_idname, text="↓", icon_value = icon_get("op_align_bottom")).direction = "bottom"

		col = row.column(align=True)
		#col.label(text="")
		col.operator(op_align.op.bl_idname, text="↑→", icon_value = icon_get("op_align_topright")).direction = "topright"
		col.operator(op_align.op.bl_idname, text=" →", icon_value = icon_get("op_align_right")).direction = "right"
		col.operator(op_align.op.bl_idname, text="↓→", icon_value = icon_get("op_align_bottomright")).direction = "bottomright"

		row_tr = col_tr.row(align=True)
		col = row_tr.column(align=True)
		col.scale_x = 0.5
		row = col.row(align=True)
		row.operator(op_align.op.bl_idname, text="—", icon_value = icon_get("op_align_horizontal")).direction = "horizontal"
		row.operator(op_align.op.bl_idname, text="|", icon_value = icon_get("op_align_vertical")).direction = "vertical"
		col = row_tr.column(align=True)
		col.prop(context.scene.texToolsSettings, "align_mode", text="", expand=False)

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
		col.operator(op_unwrap_edge_peel.op.bl_idname, text="Edge Peel", icon_value = icon_get("op_unwrap_edge_peel"))
		
		row = col.row(align=True)
		row.scale_y = 1.75
		row.operator(op_unwrap_faces_iron.op.bl_idname, text="Iron Faces", icon_value = icon_get("op_unwrap_faces_iron"))

		col.separator()

		# col = box.column(align=True)
		row = col.row(align=True)
		row.label(text="" , icon_value = icon_get("texel_density"))
		row.separator()
		row.prop(context.scene.texToolsSettings, "texel_density", text="")
		row.operator(op_texel_density_get.op.bl_idname, text="", icon = 'EYEDROPPER')

		row = col.row(align=True)
		row.operator(op_texel_density_set.op.bl_idname, text="Apply", icon = 'FACESEL')
		row.prop(context.scene.texToolsSettings, "texel_mode_scale", text = "", expand=False)

		#---------- Selection ------------
		

		# /box = layout.box()
		# box.label(text="Select")
		# col = box.column(align=True)
		col.separator()

		row = col.row(align=True)
		row.operator(op_select_islands_identical.op.bl_idname, text="Similar", icon_value = icon_get("op_select_islands_identical"))
		row.operator(op_select_islands_overlap.op.bl_idname, text="Overlap", icon_value = icon_get("op_select_islands_overlap"))

		row = col.row(align=True)
		row.operator(op_select_zero.op.bl_idname, text="Zero", icon_value = icon_get("op_select_zero"))
		row.operator(op_select_islands_flipped.op.bl_idname, text="Flipped", icon_value = icon_get('op_select_islands_flipped'))

		row = col.row(align=True)
		row.operator(op_select_islands_outline.op.bl_idname, text="Bounds", icon_value = icon_get("op_select_islands_outline"))

		col.separator()
		col.operator(op_smoothing_uv_islands.op.bl_idname, text="UV Smoothing", icon_value = icon_get("op_smoothing_uv_islands"))
		

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
		
		#----------- Baking -------------
		row = layout.row()
		box = row.box()
		col = box.column(align=True)

		if not (bpy.context.scene.texToolsSettings.bake_freeze_selection and len(settings.sets) > 0):
			# Update sets
			settings.sets = utilities_bake.get_bake_sets()


		# Bake Button
		count = 0
		if bpy.context.scene.texToolsSettings.bake_force_single and len(settings.sets) > 0:
			count = 1
		else:
			count = len(settings.sets)
		
		row = col.row(align=True)
		row.scale_y = 1.75
		row.operator(op_bake.op.bl_idname, text = "Bake {}x".format(count), icon_value = icon_get("op_bake"))

		# Warning about material need
		bake_mode = utilities_ui.get_bake_mode()
		if op_bake.modes[bake_mode].material == "":
			noMatInSelection = False
			for set in settings.sets:
				for obj in set.objects_low:
					if len(obj.material_slots) == 0:
						noMatInSelection = True
						break
				else:
					continue
				break
			if noMatInSelection:
				col.label(text="Need an active material", icon='ERROR')

		col.separator()

		col_tr = col.column(align=True)
		row = col_tr.row(align=True)
		col = row.column(align=True)

		col.label(text="AA:")
		col.label(text="CS:")
		if bpy.context.preferences.addons[__package__].preferences.bool_bake_back_color == 'CUSTOM':
			col.label(text="BG:")

		col = row.column(align=True)
		col.scale_x = 1.75

		# anti aliasing
		col.prop(context.scene.texToolsSettings, "bake_sampling", text="", icon_value =icon_get("bake_anti_alias"))
		
		# Color Space selector
		col.prop(context.scene.texToolsSettings, "bake_color_space", text="", icon_value =icon_get("bake_color_space"))

		# Background Color Picker
		if bpy.context.preferences.addons[__package__].preferences.bool_bake_back_color == 'CUSTOM':
			col.prop(context.scene.texToolsSettings, "bake_back_color", text="")
		
		col = box.column(align=True)

		if bpy.app.debug_value != 0:
			row = col.row()
			row.alert = True
			row.prop(context.scene.texToolsSettings, "bake_force_single", text="Dither Floats")


		# Collected Related Textures		
		row = col.row(align=True)
		row.scale_y = 1.5
		row.operator(op_texture_preview.op.bl_idname, text = "Preview Texture", icon_value = icon_get("op_texture_preview"))
		
		images = utilities_bake.get_baked_images(settings.sets)
		
		if len(images) > 0:

			image_background = None
			for area in bpy.context.screen.areas:
				if area.type == 'IMAGE_EDITOR':
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
				row.operator(op_texture_select.op.bl_idname, text=image.name, icon=icon).name = image.name #, 
	
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
		col.template_icon_view(bpy.context.scene, "TT_bake_mode")

		if bpy.app.debug_value != 0:
			row = col.row()
			row.label(text="--> Mode: '{}'".format(bpy.context.scene.TT_bake_mode))

		# Warning: Wrong bake mode, require 
		if bake_mode == 'diffuse':
			if bpy.context.scene.render.engine != 'CYCLES':
				if bpy.context.scene.render.engine != op_bake.modes[bake_mode].engine:
					col.label(text="Requires '{}'".format(op_bake.modes[bake_mode].engine), icon='ERROR')

		# Optional Parameters
		col.separator()
		for set in settings.sets:
			if len(set.objects_low) > 0 and len(set.objects_high) > 0:
				col.prop(context.scene.texToolsSettings, "bake_cage_extrusion")
				bversion = float(bpy.app.version_string[0:4])
				if bversion >= 2.90:
					col.prop(context.scene.texToolsSettings, "bake_ray_distance")
				break

		# Display Bake mode properties / parameters
		if bake_mode in op_bake.modes:
			params = op_bake.modes[bake_mode].params
			if len(params) > 0:
				for param in params:
					col.prop(context.scene.texToolsSettings, param)

		# Warning about projection requirement
		if len(settings.sets) > 0 and op_bake.modes[bake_mode].use_project == True:
			if len(settings.sets[0].objects_low) == 0 or len(settings.sets[0].objects_high) == 0:
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
			for set in settings.sets:
				if set.has_issues:
					count_types['issue']+=1
				if len(set.objects_low) > 0:
					count_types['low']+=1
				if len(set.objects_high) > 0:
					count_types['high']+=1
				if len(set.objects_cage) > 0:
					count_types['cage']+=1
				if len(set.objects_float) > 0:
					count_types['float']+=1

			# Freeze Selection
			c = row.column(align=True)
			c.active = len(settings.sets) > 0 or bpy.context.scene.texToolsSettings.bake_freeze_selection
			icon = 'LOCKED' if bpy.context.scene.texToolsSettings.bake_freeze_selection else 'UNLOCKED'
			c.prop(context.scene.texToolsSettings, "bake_freeze_selection",text="Lock {}x".format(len(settings.sets)), icon=icon)

			# Select by type
			if count_types['issue'] > 0:
				row.operator("uv.op_select_bake_type", text = "", icon = 'ERROR').select_type = 'issue'

			row.operator("uv.op_select_bake_type", text = "", icon_value = icon_get("bake_obj_low")).select_type = 'low'
			row.operator("uv.op_select_bake_type", text = "", icon_value = icon_get("bake_obj_high")).select_type = 'high'
			
			if count_types['float'] > 0:
				row.operator("uv.op_select_bake_type", text = "", icon_value = icon_get("bake_obj_float")).select_type = 'float'
			
			if count_types['cage'] > 0:
				row.operator("uv.op_select_bake_type", text = "", icon_value = icon_get("bake_obj_cage")).select_type = 'cage'

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
			for s in range(0, len(settings.sets)):
				set = settings.sets[s]
				r = c.row(align=True)
				r.active = not (bpy.context.scene.texToolsSettings.bake_force_single and s > 0)

				if set.has_issues:
					r.operator("uv.op_select_bake_set", text=set.name, icon='ERROR').select_set = set.name 
				else:
					r.operator("uv.op_select_bake_set", text=set.name).select_set = set.name 


			c = split.column(align=True)
			for set in settings.sets:
				r = c.row(align=True)
				r.alignment = "LEFT"

				if len(set.objects_low) > 0:
					r.label(text="{}".format(len(set.objects_low)), icon_value = icon_get("bake_obj_low"))
				elif count_types['low'] > 0:
					r.label(text="")

				if len(set.objects_high) > 0:
					r.label(text="{}".format(len(set.objects_high)), icon_value = icon_get("bake_obj_high"))
				elif count_types['high'] > 0:
					r.label(text="")

				if len(set.objects_float) > 0:
					r.label(text="{}".format(len(set.objects_float)), icon_value = icon_get("bake_obj_float"))
				elif count_types['float'] > 0:
					r.label(text="")

				if len(set.objects_cage) > 0:
					r.label(text="{}".format(len(set.objects_cage)), icon_value = icon_get("bake_obj_cage"))
				elif count_types['cage'] > 0:
					r.label(text="")

			# Force Single
			row = box2.row(align=True)
			row.active = len(settings.sets) > 0
			row.prop(context.scene.texToolsSettings, "bake_force_single", text="Single Texture")
			if len(settings.sets) > 0 and bpy.context.scene.texToolsSettings.bake_force_single:
				row.label(text="'{}'".format(settings.sets[0].name))
			# else:
			# 	row.label(text="")


		col = box.column(align=True)
		col.operator(op_bake_organize_names.op.bl_idname, text = "Organize {}x".format(len(bpy.context.selected_objects)), icon = 'BOOKMARKS')
		col.operator(op_bake_explode.op.bl_idname, text = "Explode", icon_value = icon_get("op_bake_explode"))


	

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
		
		if bpy.context.scene.render.engine != 'CYCLES' and bpy.context.scene.render.engine != 'BLENDER_EEVEE':
			row = layout.row(align=True)
			row.alert = True
			row.operator("uv.op_enable_cycles", text="Enable 'CYCLES'", icon='CANCEL')#, icon='UV_SYNC_SELECT'
			return


		box = layout.box()
		col = box.column(align=True)
		


		row = col.row(align=True)
		split = row.split(factor=0.60, align=True)
		c = split.column(align=True)
		c.prop(context.scene.texToolsSettings, "color_ID_templates", text="")
		c = split.column(align=True)
		c.prop(context.scene.texToolsSettings, "color_ID_count", text="", expand=False)

		row = box.row(align=True)
		row.operator(op_color_clear.op.bl_idname, text="Clear", icon = 'X')
		row.menu(UI_MT_op_color_dropdown_io.bl_idname, icon='COLOR')


		max_columns = 5
		if context.scene.texToolsSettings.color_ID_count < max_columns:
			max_columns = context.scene.texToolsSettings.color_ID_count

		count = math.ceil(context.scene.texToolsSettings.color_ID_count / max_columns)*max_columns

		for i in range(count):

			if i%max_columns == 0:
				row = box.row(align=True)

			col = row.column(align=True)
			if i < context.scene.texToolsSettings.color_ID_count:
				col.prop(context.scene.texToolsSettings, "color_ID_color_{}".format(i), text="")
				col.operator(op_color_assign.op.bl_idname, text="", icon = "FILE_TICK").index = i
	
				if bpy.context.active_object:
					if bpy.context.active_object in bpy.context.selected_objects:
						if len(bpy.context.selected_objects) == 1:
							if bpy.context.active_object.type == 'MESH':
								col.operator(op_color_select.op.bl_idname, text="", icon = "FACESEL").index = i
			else:
				col.label(text=" ")

		
		# split = row.split(percentage=0.25, align=True)
		# c = split.column(align=True)
		# c.operator(op_color_clear.op.bl_idname, text="", icon = 'X')
		# c = split.column(align=True)
		# c.operator(op_color_from_elements.op.bl_idname, text="Color Elements", icon_value = icon_get('op_color_from_elements'))
		

		
		col = box.column(align=True)
		col.label(text="Convert")
		row = col.row(align=True)
		row.menu(UI_MT_op_color_dropdown_convert_from.bl_idname)#, icon='IMPORT'
		row.menu(UI_MT_op_color_dropdown_convert_to.bl_idname,)# icon='EXPORT'
		



		# row = col.row(align=True)
		# row.operator(op_color_convert_texture.op.bl_idname, text="From Atlas", icon_value = icon_get('op_color_convert_texture'))
			


		# for i in range(context.scene.texToolsSettings.color_ID_count):



		# 	col = row.column(align=True)
		# 	col.prop(context.scene.texToolsSettings, "color_ID_color_{}".format(i), text="")
		# 	col.operator(op_color_assign.op.bl_idname, text="", icon = "FILE_TICK").index = i
			
		# 	if bpy.context.active_object:
		# 		if bpy.context.active_object.type == 'MESH':
		# 			if bpy.context.active_object.mode == 'EDIT':
		# 				col.operator(op_color_select.op.bl_idname, text="", icon = "FACESEL").index = i

		

		# https://github.com/blenderskool/kaleidoscope/blob/fb5cb1ab87a57b46618d99afaf4d3154ad934529/spectrum.py
	
			

	
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
		row.label(text ="Mesh Texture")

	def draw(self, context):
		layout = self.layout
		box = layout.box()
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
		row.prop(context.scene.texToolsSettings, "meshtexture_wrap", text="Wrap")

		box.operator(op_meshtex_pattern.op.bl_idname, text="Create Pattern", icon_value = icon_get("op_meshtex_pattern"))



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

	layout.separator()
	layout.operator(op_island_align_sort.op.bl_idname, text="Sort H", icon_value = icon_get("op_island_align_sort_h"))
	layout.operator(op_island_align_sort.op.bl_idname, text="Sort V", icon_value = icon_get("op_island_align_sort_v"))
		
	layout.separator()
	layout.operator(op_island_align_edge.op.bl_idname, text="Align Edge", icon_value = icon_get("op_island_align_edge"))
	layout.operator(op_island_align_world.op.bl_idname, text="Align World", icon_value = icon_get("op_island_align_world"))

	layout.separator()
	layout.operator(op_island_centralize.op.bl_idname, text="Centralize Position", icon_value = icon_get("op_island_centralize"))
	layout.operator(op_randomize.op.bl_idname, text="Randomize Position", icon_value = icon_get("op_randomize"))

	layout.menu(VIEW3D_MT_submenu_align)

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
	layout.operator(op_select_islands_outline.op.bl_idname, text="Bounds", icon_value = icon_get("op_select_islands_outline"))
	
def menu_IMAGE_MT_image(self, context):
	layout = self.layout
	layout.separator()
	layout.operator(op_texture_reload_all.op.bl_idname, text="Reload Textures", icon_value = icon_get("op_texture_reload_all"))
	layout.operator(op_texel_checker_map.op.bl_idname, text ="Checker Map", icon_value = icon_get("op_texel_checker_map"))
	layout.operator(op_texture_preview.op.bl_idname, text = "Preview Texture", icon_value = icon_get("op_texture_preview"))
		
def menu_VIEW3D_MT_object(self, context):
	self.layout.separator()
	self.layout.operator(op_texel_checker_map.op.bl_idname, text ="Checker Map", icon_value = icon_get("op_texel_checker_map"))
	self.layout.operator(op_meshtex_create.op.bl_idname, text="Create UV Mesh", icon_value = icon_get("op_meshtex_create"))
	
def menu_VIEW3D_MT_mesh_add(self, context):
	self.layout.operator(op_meshtex_pattern.op.bl_idname, text="Create Pattern", icon_value = icon_get("op_meshtex_pattern"))

def menu_VIEW3D_MT_uv_map(self, context):
	layout = self.layout
	layout.separator()
	layout.operator(op_unwrap_edge_peel.op.bl_idname, text="Peel Edge", icon_value = icon_get("op_unwrap_edge_peel"))
	layout.operator(op_unwrap_faces_iron.op.bl_idname, text="Iron Faces", icon_value = icon_get("op_unwrap_faces_iron"))
	layout.operator(op_smoothing_uv_islands.op.bl_idname, text="UV Smoothing", icon_value = icon_get("op_smoothing_uv_islands"))
		
def menu_VIEW3D_MT_object_context_menu(self, context):
	layout = self.layout
	layout.separator()
	layout.operator(op_meshtex_create.op.bl_idname, text="Create UV Mesh", icon_value = icon_get("op_meshtex_create"))
	layout.operator(op_meshtex_trim.op.bl_idname, text="Trim", icon_value = icon_get("op_meshtex_trim"))

	# Warning about trimmed mesh
	if op_meshtex_trim_collapse.is_available():
		layout.operator(op_meshtex_trim_collapse.op.bl_idname, text="Collapse Trim", icon='CANCEL')

	layout.prop(context.scene.texToolsSettings, "meshtexture_wrap", text="Wrap")
	layout.operator(op_meshtex_wrap.op.bl_idname, text="Wrap", icon_value = icon_get("op_meshtex_wrap"))


classes = (
		    UV_OT_op_debug,
			UV_OT_op_disable_uv_sync,
			UV_OT_op_select_bake_set,
			UV_OT_op_select_bake_type,
			TexToolsSettings,
			UI_PT_Panel_Units,
			UI_PT_Panel_Layout,
			UI_PT_Panel_Bake,
			UI_MT_op_color_dropdown_io,
			UI_MT_op_color_dropdown_convert_from,
			UI_MT_op_color_dropdown_convert_to,
			UV_OT_op_enable_cycles,
			UI_PT_Panel_Colors,
			UI_PT_Panel_MeshTexture,
			VIEW3D_MT_submenu_align,
			Panel_Preferences

)


def register():
	from bpy.utils import register_class
	for cls in classes:
		register_class(cls)

#Register settings
	bpy.types.Scene.texToolsSettings = PointerProperty(type=TexToolsSettings)

	#GUI Utilities
	utilities_ui.register()

	# Register Icons
	icons = [
		"bake_anti_alias.png", 
		"bake_color_space.png", 
		"bake_obj_cage.png", 
		"bake_obj_float.png", 
		"bake_obj_high.png", 
		"bake_obj_low.png", 
		"op_align_bottom.png", 
		"op_align_topleft.png", 
		"op_align_left.png", 
		"op_align_bottomleft.png", 
		"op_align_topright.png", 
		"op_align_right.png", 
		"op_align_bottomright.png", 
		"op_align_top.png",
		"op_align_horizontal.png",
		"op_align_vertical.png",
		"op_align_center.png",		 
		"op_bake.png", 
		"op_bake_explode.png", 
		"op_color_convert_texture.png", 
		"op_color_convert_vertex_colors.png", 
		"op_color_from_directions.png", 
		"op_color_from_elements.png", 
		"op_color_from_materials.png", 
		"op_extend_canvas_open.png",
		"op_island_align_edge.png", 
		"op_island_align_sort_h.png", 
		"op_island_align_sort_v.png", 
		"op_island_align_world.png", 
		"op_island_mirror_H.png", 
		"op_island_mirror_V.png", 
		"op_island_rotate_90_left.png", 
		"op_island_rotate_90_right.png", 
		"op_island_straighten_edge_loops.png", 
		"op_meshtex_create.png",
		"op_meshtex_pattern.png",
		"op_meshtex_trim.png",
		"op_meshtex_trim_collapse.png", 
		"op_meshtex_wrap.png",
		"op_island_centralize.png",
		"op_randomize.png",
		"op_rectify.png", 
		"op_select_islands_flipped.png", 
		"op_select_zero.png", 
		"op_select_islands_identical.png", 
		"op_select_islands_outline.png", 
		"op_select_islands_overlap.png", 
		"op_smoothing_uv_islands.png", 
		"op_texel_checker_map.png", 
		"op_texture_preview.png", 
		"op_texture_reload_all.png",
		"op_texture_save.png",
		"op_texture_open.png",
		"op_unwrap_faces_iron.png", 
		"op_unwrap_edge_peel.png", 
		"op_uv_crop.png", 
		"op_uv_fill.png", 
		"texel_density.png"
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
	from bpy.utils import unregister_class
	for cls in reversed(classes):
		unregister_class(cls)

	#Unregister Settings
	del bpy.types.Scene.texToolsSettings

	#handle the keymap
	for km, kmi in keymaps:
		km.keymap_items.remove(kmi)
	keymaps.clear()

	#GUI Utilities
	utilities_ui.unregister()

	bpy.types.IMAGE_MT_uvs.remove(menu_IMAGE_uvs)
	bpy.types.IMAGE_MT_select.remove(menu_IMAGE_select)
	bpy.types.IMAGE_MT_image.remove(menu_IMAGE_MT_image)
	bpy.types.VIEW3D_MT_object.remove(menu_VIEW3D_MT_object)
	bpy.types.VIEW3D_MT_add.remove(menu_VIEW3D_MT_mesh_add)
	bpy.types.VIEW3D_MT_uv_map.remove(menu_VIEW3D_MT_uv_map)
	bpy.types.VIEW3D_MT_object_context_menu.remove(menu_VIEW3D_MT_object_context_menu)
	
	

if __name__ == "__main__":
	register()
