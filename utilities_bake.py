import bpy
import bmesh
from mathutils import Vector
from math import pi

from . import utilities_color
from . import utilities_ui
from . import settings


keywords_low = ['lowpoly','low','lowp','lp','lo']		#excluded 'l' since TexTools v1.4
keywords_high = ['highpoly','high','highp','hp','hi']	#excluded 'h' since TexTools v1.4
keywords_cage = ['cage']								#excluded 'c' since TexTools v1.4
keywords_float = ['floater','float']					#excluded 'f' since TexTools v1.4

split_chars = [' ','_','.','-']

if settings.bversion >= 4.3:
	chs = {'ech':27, 'rch':2, 'trch':2, 'ssch':8, 'scch':0, 'mch':1, 'sch':13, 'stch':14, 'ach':15, 'arch':16, 'shch':24, 'shtch':26, 'cch':19, 'crch':20, 'esch':28, 'alch':4}
elif settings.bversion >= 4.0:
	chs = {'ech':26, 'rch':2, 'trch':2, 'ssch':7, 'scch':0, 'mch':1, 'sch':12, 'stch':13, 'ach':14, 'arch':15, 'shch':23, 'shtch':25, 'cch':18, 'crch':19, 'esch':27, 'alch':4}
else:
	sh = 0		# shift of channels, depends on the Blender version
	if settings.bversion >= 3.0:
		sh = 2
	chs = {'ech':17+sh, 'rch':7+sh, 'ssch':1, 'scch':3, 'mch':4+sh, 'sch':5+sh, 'stch':0, 'shtch':0, 'ach':8+sh, 'arch':9+sh, 'shch':10+sh, 'cch':12+sh, 'crch':13+sh, 'trch':16+sh, 'esch':18+sh, 'alch':19+sh}

allMaterials = []
allMaterialsNames = []
elementsCount = 0


class BakeMode:
	material = ""					#Material name from external blend file
	type = 'EMIT'
	normal_space = 'TANGENT'
	setVColor = None				#Set Vertex color method
	color = (0.23, 0.23, 0.23, 1)	#Background color
	engine = 'CYCLES'				#render engine, by default CYCLES
	composite = None				#use composite scene to process end result
	use_project = False				#Bake projected?
	invert = False
	relink = {'needed':False}
	params = []						#UI Parameters from scene settings

	def __init__(self, material="", type='EMIT', normal_space='TANGENT', setVColor=None, color= (0.23, 0.23, 0.23, 1), engine='CYCLES', params = [], composite=None, use_project=False, invert=False, relink = {'needed':False}):
		self.material = material
		self.type = type
		self.normal_space = normal_space
		self.setVColor = setVColor
		self.color = color
		self.engine = engine
		self.params = params
		self.composite = composite
		self.use_project = use_project
		self.invert = invert
		self.relink = relink



def on_select_bake_mode(mode):
	print("Mode changed {}".format(mode))

	if len(settings.sets) > 0:
		name_texture = "{}_{}".format(settings.sets[0].name, mode)

		if name_texture in bpy.data.images:
			image = bpy.data.images[name_texture]

			# Set background image
			for area in bpy.context.screen.areas:
				if area.ui_type == 'UV':
					area.spaces[0].image = image


def store_bake_settings():
	# Render Settings
	settings.bake_render_engine = bpy.context.scene.render.engine
	settings.bake_cycles_device = bpy.context.scene.cycles.device
	settings.bake_cycles_samples = bpy.context.scene.cycles.samples
	if settings.bversion >= 2.92:
		settings.bake_target_mode = bpy.context.scene.render.bake.target
	if settings.bversion < 3:
		settings.use_progressive_refine = bpy.context.scene.cycles.use_progressive_refine
	if settings.bversion >= 3:
		settings.use_denoising = bpy.context.scene.cycles.use_denoising

	# Disable Objects that are meant to be hidden
	sets = settings.sets
	objects_sets = []
	for bset in sets:
		for obj in bset.objects_low:
			if obj not in objects_sets:
				objects_sets.append(obj)
		for obj in bset.objects_high:
			if obj not in objects_sets:
				objects_sets.append(obj)
		for obj in bset.objects_cage:
			if obj not in objects_sets:
				objects_sets.append(obj)

	settings.bake_objects_hide_render = []

	# for obj in bpy.context.view_layer.objects:
	# 	if obj.hide_render == False and obj not in objects_sets:
    # 			Check if layer is active:
	# 		for l in range(0, len(obj.layers)):
	# 			if obj.layers[l] and bpy.context.scene.layers[l]:
	# 				settings.bake_objects_hide_render.append(obj)
	# 				break #sav

	for obj in settings.bake_objects_hide_render:
		obj.hide_render = True
		# obj.cycles_visibility.shadow = False



def restore_bake_settings():
	# Render Settings
	if settings.bake_render_engine != '':
		bpy.context.scene.render.engine = settings.bake_render_engine

	bpy.context.scene.cycles.device = settings.bake_cycles_device
	bpy.context.scene.cycles.samples = settings.bake_cycles_samples

	if settings.bversion >= 2.92:
		bpy.context.scene.render.bake.target = settings.bake_target_mode
	if settings.bversion < 3:
		bpy.context.scene.cycles.use_progressive_refine = settings.use_progressive_refine
	if settings.bversion >= 3:
		bpy.context.scene.cycles.use_denoising = settings.use_denoising

	# Restore Objects that were hidden for baking
	for obj in settings.bake_objects_hide_render:
		if obj:
			obj.hide_render = False
			# obj.cycles_visibility.shadow = True



def get_set_name_base(obj):

	def remove_digits(name):
		# Remove blender naming digits, e.g. cube.001, cube.002,...
		if len(name) > 4 and name[-4] == '.' and name[-3:].isdigit():
			return name[:-4]
		return name

	# Reference parent as base name
	if obj.parent and obj.parent in bpy.context.selected_objects:
		return remove_digits(obj.parent.name).lower()

	# Reference group name as base name
	elif len(obj.users_collection) == 2:
		return remove_digits(obj.users_collection[0].name).lower()

	# Use Object name
	else:
		return remove_digits(obj.name).lower()



def get_set_name(obj):

	if bpy.context.scene.texToolsSettings.bake_force == "Multi":
		return obj.name

	# Get Basic name
	name = get_set_name_base(obj)

	# Split by ' ','_','.' etc.
	split = name.lower()
	for char in split_chars:
		split = split.replace(char,' ')
	strings = split.split(' ')

	# Remove all keys from name
	keys = keywords_cage + keywords_high + keywords_low + keywords_float
	new_strings = []
	for string in strings:
		is_found = False
		for key in keys:
			if string == key:
				is_found = True
				break
		if not is_found:
			new_strings.append(string)
		elif len(new_strings) > 0:
			# No more strings once key is found if we have already something
			break

	return "_".join(new_strings)



def get_object_type(obj):

	if bpy.context.scene.texToolsSettings.bake_force == "Multi":
		return 'low'

	name = get_set_name_base(obj)

	# Detect by name pattern
	split = name.lower()
	for char in split_chars:
		split = split.replace(char,' ')
	strings = split.split(' ')

	# Detect float, more rare than low
	for string in strings:		
		for key in keywords_float:
			if key == string:
				return 'float'

	# Detect by modifiers (Only if more than 1 object selected)
	if bpy.context.preferences.addons[__package__].preferences.bool_modifier_auto_high:
		if len(bpy.context.selected_objects) > 1:
			if obj.modifiers:
				for modifier in obj.modifiers:
					if modifier.type == 'SUBSURF' and modifier.render_levels > 0:
						return 'high'
					elif modifier.type == 'BEVEL':
						return 'high'

	# Detect High first, more rare
	for string in strings:
		for key in keywords_high:
			if key == string:
				return 'high'
	
	# Detect cage, more rare than low
	for string in strings:		
		for key in keywords_cage:
			if key == string:
				return 'cage'

	# Detect low
	for string in strings:
		for key in keywords_low:
			if key == string:
				return 'low'

	# if nothing was detected, assume it is low
	return 'low'



def get_baked_images(sets):
	images = []
	for bset in sets:
		name_texture = "{}_".format(bset.name)
		for image in bpy.data.images:
			if name_texture in image.name:
				images.append(image)

	return images



def get_bake_sets():
	filtered = {}
	if len(bpy.context.selected_objects) == 0:
		if bpy.context.active_object is not None:
			if bpy.context.active_object.mode == 'EDIT' and bpy.context.active_object.type == 'MESH':
				filtered[bpy.context.active_object] = get_object_type(bpy.context.active_object)
	else:
		for obj in bpy.context.selected_objects:
			if obj.type == 'MESH':
				filtered[obj] = get_object_type(obj)

	groups = []
	# Group by names
	for obj in filtered:
		name = get_set_name(obj)

		if not groups:
			groups.append([obj])
		else:
			isFound = False
			for group in groups:
				groupName = get_set_name(group[0])
				if name == groupName:
					group.append(obj)
					isFound = True
					break

			if not isFound:
				groups.append([obj])

	# Sort groups alphabetically
	keys = [get_set_name(group[0]) for group in groups]
	keys.sort()
	sorted_groups = []
	for key in keys:
		for group in groups:
			if key == get_set_name(group[0]):
				sorted_groups.append(group)
				break

	groups = sorted_groups			

	bake_sets = []
	for group in groups:
		low = []
		high = []
		cage = []
		float = []
		for obj in group:
			if filtered[obj] == 'low':
				low.append(obj)
			elif filtered[obj] == 'high':
				high.append(obj)
			elif filtered[obj] == 'cage':
				cage.append(obj)
			elif filtered[obj] == 'float':
				float.append(obj)

		name = get_set_name(group[0])
		bake_sets.append(BakeSet(name, low, cage, high, float))

	return bake_sets



class BakeSet:
	objects_low = []	#low poly geometry
	objects_cage = []	#Cage low poly geometry
	objects_high = []	#High poly geometry
	objects_float = []	#Floating geometry
	name = ""

	has_issues = False

	def __init__(self, name, objects_low, objects_cage, objects_high, objects_float):
		self.objects_low = objects_low
		self.objects_cage = objects_cage
		self.objects_high = objects_high
		self.objects_float = objects_float
		self.name = name

		# Needs low poly objects to bake onto
		if len(objects_low) == 0:
			self.has_issues = True

		# Check Cage Object count to low poly count
		if len(objects_cage) > 0 and len(objects_low) != len(objects_cage):
			self.has_issues = True

		# Check for UV maps
		for obj in objects_low:
			if len(obj.data.uv_layers) == 0:
				self.has_issues = True
				break



def assign_vertex_color(obj):
	if len(obj.data.vertex_colors) > 0 :
		vclsNames = [vcl.name for vcl in obj.data.vertex_colors]
		if 'TexTools_temp' in vclsNames:
			obj.data.vertex_colors['TexTools_temp'].active = True
			obj.data.vertex_colors['TexTools_temp'].active_render = True
		else:
			obj.data.vertex_colors.new(name='TexTools_temp')
			obj.data.vertex_colors['TexTools_temp'].active = True
			obj.data.vertex_colors['TexTools_temp'].active_render = True
	else:
		obj.data.vertex_colors.new(name='TexTools_temp')
		obj.data.vertex_colors['TexTools_temp'].active = True
		obj.data.vertex_colors['TexTools_temp'].active_render = True



def setup_vertex_color_selection(obj):
	context_override = utilities_ui.GetContextView3D()
	if not context_override:
		print("This bake mode requires an available View3D view.")
		return

	bpy.ops.object.select_all(action='DESELECT')
	obj.select_set( state = True, view_layer = None)
	bpy.context.view_layer.objects.active = obj
	
	bpy.ops.object.mode_set(mode='VERTEX_PAINT')

	bpy.context.tool_settings.vertex_paint.brush.color = (0, 0, 0)
	bpy.context.object.data.use_paint_mask = False
	with bpy.context.temp_override(**context_override):
		bpy.ops.paint.vertex_color_set()

	bpy.context.tool_settings.vertex_paint.brush.color = (1, 1, 1)
	bpy.context.object.data.use_paint_mask = True
	with bpy.context.temp_override(**context_override):
		bpy.ops.paint.vertex_color_set()
	bpy.context.object.data.use_paint_mask = False

	bpy.ops.object.mode_set(mode='OBJECT')



def setup_vertex_color_dirty(obj):
	bpy.ops.object.select_all(action='DESELECT')
	obj.select_set( state = True, view_layer = None)
	bpy.context.view_layer.objects.active = obj
	bpy.ops.object.mode_set(mode='EDIT')

	# Fill white then, 
	bm = bmesh.from_edit_mesh(obj.data)
	if settings.bversion >= 3.4:
		colorLayerIndex = obj.data.attributes.active_color_index
		colorLayer = bm.loops.layers.color[colorLayerIndex]
	else:
		colorLayer = bm.loops.layers.color.active

	color = utilities_color.safe_color( (1, 1, 1) )

	for face in bm.faces:
		for loop in face.loops:
				loop[colorLayer] = color

	obj.data.update()
	bpy.ops.object.mode_set(mode='OBJECT')
	bpy.ops.paint.vertex_color_dirt(dirt_angle=pi/2)
	bpy.ops.paint.vertex_color_dirt()



def setup_vertex_color_id_material(obj, previous_materials):
	context_override = utilities_ui.GetContextView3D()
	if not context_override:
		print("This bake mode requires an available View3D view.")
		return

	bpy.ops.object.select_all(action='DESELECT')
	obj.select_set( state = True, view_layer = None)
	bpy.context.view_layer.objects.active = obj
	bpy.ops.object.mode_set(mode='EDIT')
	
	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')

	# bm = bmesh.from_edit_mesh(obj.data)
	# colorLayer = bm.loops.layers.color.active

	for i, mtlname in enumerate(previous_materials[obj]):
		if mtlname is not None:
			# Select related faces
			bpy.ops.object.mode_set(mode='EDIT')
			bpy.ops.mesh.select_all(action='DESELECT')

			bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
			for face in bm.faces:
				if face.material_index == i:
					face.select = True
			
			color = utilities_color.get_color_id(allMaterials.index(bpy.data.materials[mtlname]), 256, jitter=True)

			bpy.ops.object.mode_set(mode='VERTEX_PAINT')
			bpy.context.tool_settings.vertex_paint.brush.color = color
			bpy.context.object.data.use_paint_mask = True
			with bpy.context.temp_override(**context_override):
				bpy.ops.paint.vertex_color_set()

	obj.data.update()
	bpy.ops.object.mode_set(mode='OBJECT')



def setup_vertex_color_id_element(obj):
	bpy.ops.object.select_all(action='DESELECT')
	obj.select_set( state = True, view_layer = None)
	bpy.context.view_layer.objects.active = obj
	bpy.ops.object.mode_set(mode='EDIT')
	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')

	bm = bmesh.from_edit_mesh(obj.data)

	if settings.bversion >= 3.4:
		colorLayerIndex = obj.data.attributes.active_color_index
		colorLayer = bm.loops.layers.color[colorLayerIndex]
	else:
		colorLayer = bm.loops.layers.color.active


	# Collect elements
	processed = set([])
	groups = []
	for face in bm.faces:

		if face not in processed:
			bpy.ops.mesh.select_all(action='DESELECT')
			face.select = True
			bpy.ops.mesh.select_linked(delimit={'NORMAL'})
			linked = [face for face in bm.faces if face.select]

			for link in linked:
				processed.add(link)
			groups.append(linked)

	global elementsCount

	# Color each group
	for i in range(0,len(groups)):
		color = utilities_color.get_color_id(elementsCount + i, 256, jitter=True)
		color = utilities_color.safe_color( color )
		for face in groups[i]:
			for loop in face.loops:
				loop[colorLayer] = color

	elementsCount += len(groups)

	obj.data.update()
	bpy.ops.object.mode_set(mode='OBJECT')



def get_image_material(image):

	# Clear & Create new material
	material = None
	if image.name in bpy.data.materials:
		# Incorrect existing material, delete first and create new for cycles
		material = bpy.data.materials[image.name]
		bpy.data.materials.remove(material, do_unlink=True)
		material = bpy.data.materials.new(image.name)
	else:
		material = bpy.data.materials.new(image.name)


	# Cycles Material
	if bpy.context.scene.render.engine == 'CYCLES' or bpy.context.scene.render.engine == 'BLENDER_EEVEE':
		material.use_nodes = True

		# Image Node
		node_image = None
		if "image" in material.node_tree.nodes:
			node_image = material.node_tree.nodes["image"]
		else:
			node_image = material.node_tree.nodes.new("ShaderNodeTexImage")
			node_image.name = "image"
		node_image.select = True
		node_image.image = image
		material.node_tree.nodes.active = node_image

		#Base Diffuse BSDF
		bsdf_node = None
		for n in material.node_tree.nodes:
			if n.bl_idname == "ShaderNodeBsdfPrincipled":
				bsdf_node = n

		if "_normal_" in image.name:
			# Add Normal Map Nodes
			node_normal_map = None
			if "normal_map" in material.node_tree.nodes:
				node_normal_map = material.node_tree.nodes["normal_map"]
			else:
				node_normal_map = material.node_tree.nodes.new("ShaderNodeNormalMap")
				node_normal_map.name = "normal_map"

			# Tangent or World space
			if(image.name.endswith("normal_tangent")):
				node_normal_map.space = 'TANGENT'
			elif(image.name.endswith("normal_object")):
				node_normal_map.space = 'WORLD'

			# image to normal_map link
			material.node_tree.links.new(node_image.outputs[0], node_normal_map.inputs[1])

			# normal_map to diffuse_bsdf link
			if settings.bversion < 2.91:
				material.node_tree.links.new(node_normal_map.outputs[0], bsdf_node.inputs[19])
			else:
				material.node_tree.links.new(node_normal_map.outputs[0], bsdf_node.inputs[20])

			node_normal_map.location = bsdf_node.location - Vector((200, 0))
			node_image.location = node_normal_map.location - Vector((200, 0))

		else:
			# Other images display as Color
			# dump(node_image.color_mapping.bl_rna.property_tags)
			
			# image node to diffuse node link
			material.node_tree.links.new(node_image.outputs[0], bsdf_node.inputs[0])

		return material

	elif bpy.context.scene.render.engine == 'BLENDER_EEVEE':
		material.use_nodes = True
		
		texture = None
		if image.name in bpy.data.textures:
			texture = bpy.data.textures[image.name]
		else:
			texture = bpy.data.textures.new(image.name, 'IMAGE')

		texture.image = image
		slot = material.texture_slot.add()
		slot.texture = texture
		slot.mapping = 'FLAT' 

	# return material
