import bpy
import os
import bmesh
from mathutils import Vector
from collections import defaultdict
from math import pi
from random import random

from . import utilities_ui
from . import settings
from . import utilities_bake as ub #Use shorthand ub = utitlites_bake


# Notes: https://docs.blender.org/manual/en/dev/render/blender_render/bake.html
modes={
	'normal_tangent':	ub.BakeMode('',					type='NORMAL', 	color=(0.5, 0.5, 1, 1), use_project=True),
	'normal_object': 	ub.BakeMode('',					type='NORMAL', 	color=(0.5, 0.5, 1, 1), normal_space='OBJECT' ),
	'cavity': 			ub.BakeMode('bake_cavity',		type='EMIT', 	setVColor=ub.setup_vertex_color_dirty),
	'paint_base': 		ub.BakeMode('bake_paint_base',	type='EMIT'),
	'dust': 			ub.BakeMode('bake_dust',		type='EMIT', 	setVColor=ub.setup_vertex_color_dirty),
	'id_element':		ub.BakeMode('bake_vertex_color',type='EMIT', 	setVColor=ub.setup_vertex_color_id_element),
	'id_material':		ub.BakeMode('bake_vertex_color',type='EMIT', 	setVColor=ub.setup_vertex_color_id_material),
	'selection':		ub.BakeMode('bake_vertex_color',type='EMIT', 	color=(0, 0, 0, 1), setVColor=ub.setup_vertex_color_selection),
	'diffuse':			ub.BakeMode('',					type='DIFFUSE'),
	# 'displacment':		ub.BakeMode('',					type='DISPLACEMENT', use_project=True, color=(0, 0, 0, 1), engine='CYCLES'),
	'ao':				ub.BakeMode('',					type='AO', 		params=["bake_samples"], engine='CYCLES'),
	'ao_legacy':		ub.BakeMode('',					type='AO', 		params=["bake_samples"], engine='CYCLES'),
	'position':			ub.BakeMode('bake_position',	type='EMIT'),
	'curvature':		ub.BakeMode('',					type='NORMAL',	use_project=True, params=["bake_curvature_size"], composite="curvature"),
	'wireframe':		ub.BakeMode('bake_wireframe',	type='EMIT', 	color=(0, 0, 0, 1), params=["bake_wireframe_size"])
}

if hasattr(bpy.types,"ShaderNodeBevel"):
	# Has newer bevel shader (2.7 nightly build series)
	modes['bevel_mask'] = ub.BakeMode('bake_bevel_mask',				type='EMIT', 	color=(0, 0, 0, 1), params=["bake_bevel_samples","bake_bevel_size"])
	modes['normal_tangent_bevel'] = ub.BakeMode('bake_bevel_normal',	type='NORMAL', 	color=(0.5, 0.5, 1, 1), params=["bake_bevel_samples","bake_bevel_size"])
	modes['normal_object_bevel'] = ub.BakeMode('bake_bevel_normal',		type='NORMAL', 	color=(0.5, 0.5, 1, 1), normal_space='OBJECT', params=["bake_bevel_samples","bake_bevel_size"])



class op(bpy.types.Operator):
	bl_idname = "uv.textools_bake"
	bl_label = "Bake"
	bl_description = "Bake selected objects"

	@classmethod
	def poll(cls, context):
		if len(settings.sets) == 0:
			return False
		return True

	def execute(self, context):
		bake_mode = utilities_ui.get_bake_mode()

		if bake_mode not in modes:
			self.report({'ERROR_INVALID_INPUT'}, "Uknown mode '{}' only available: '{}'".format(bake_mode, ", ".join(modes.keys() )) )
			return

		# Store Selection
		selected_objects 	= [obj for obj in bpy.context.selected_objects]
		active_object 		= bpy.context.view_layer.objects.active
		ub.store_bake_settings()

		# Render sets
		bake(
			self = self, 
			mode = bake_mode,
			size = bpy.context.scene.texToolsSettings.size, 

			bake_single = bpy.context.scene.texToolsSettings.bake_force_single,
			sampling_scale = int(bpy.context.scene.texToolsSettings.bake_sampling),
			samples = bpy.context.scene.texToolsSettings.bake_samples,
			ray_distance = bpy.context.scene.texToolsSettings.bake_ray_distance
		)
		
		# Restore selection
		ub.restore_bake_settings()
		bpy.ops.object.select_all(action='DESELECT')
		for obj in selected_objects:
			obj.select_set( state = True, view_layer = None)
		if active_object:
			bpy.context.view_layer.objects.active = active_object

		return {'FINISHED'}



def bake(self, mode, size, bake_single, sampling_scale, samples, ray_distance):

	print("Bake '{}'".format(mode))

	bpy.context.scene.render.engine = modes[mode].engine #Switch render engine

	# Disable edit mode
	if bpy.context.view_layer.objects.active != None and bpy.context.object.mode != 'OBJECT':
		bpy.ops.object.mode_set(mode='OBJECT')

	ub.store_materials_clear()

	# Get the baking sets / pairs
	sets = settings.sets

	render_width = sampling_scale * size[0]
	render_height = sampling_scale * size[1]

	for s in range(0,len(sets)):
		set = sets[s]

		# Get image name
		name_texture = "{}_{}".format(set.name, mode)
		if bake_single:
			name_texture = "{}_{}".format(sets[0].name, mode)# In Single mode bake into same texture
		path = bpy.path.abspath("//{}.tga".format(name_texture))

		# Requires 1+ low poly objects
		if len(set.objects_low) == 0:
			self.report({'ERROR_INVALID_INPUT'}, "No low poly object as part of the '{}' set".format(set.name) )
			return

		# Check for UV maps
		for obj in set.objects_low:
			if not obj.data.uv_layers or len(obj.data.uv_layers) == 0:
				self.report({'ERROR_INVALID_INPUT'}, "No UV map available for '{}'".format(obj.name))
				return

		# Check for cage inconsistencies
		if len(set.objects_cage) > 0 and (len(set.objects_low) != len(set.objects_cage)):
			self.report({'ERROR_INVALID_INPUT'}, "{}x cage objects do not match {}x low poly objects for '{}'".format(len(set.objects_cage), len(set.objects_low), obj.name))
			return

		# Get Materials
		material_loaded = get_material(mode)
		material_empty = None
		if "TT_bake_node" in bpy.data.materials:
			material_empty = bpy.data.materials["TT_bake_node"]
		else:
			material_empty = bpy.data.materials.new(name="TT_bake_node")


		# Assign Materials to Objects
		if (len(set.objects_high) + len(set.objects_float)) == 0:
			# Low poly bake: Assign material to lowpoly
			for obj in set.objects_low:
				assign_vertex_color(mode, obj)
				assign_material(mode, obj, material_loaded, material_empty)
		else:
			# High to low poly: Low poly require empty material to bake into image
			for obj in set.objects_low:
				assign_material(mode, obj, None, material_empty)

			# Assign material to highpoly
			for obj in (set.objects_high+set.objects_float):
				assign_vertex_color(mode, obj)
				assign_material(mode, obj, material_loaded)


		# Setup Image
		is_clear = (not bake_single) or (bake_single and s==0)
		image = setup_image(mode, name_texture, render_width, render_height, path, is_clear)

		# Assign bake node to Material
		setup_image_bake_node(set.objects_low[0], image)
		

		print("Bake '{}' = {}".format(set.name, path))

		# Hide all cage objects i nrender
		for obj_cage in set.objects_cage:
			obj_cage.hide_render = True

		# Bake each low poly object in this set
		for i in range(len(set.objects_low)):
			obj_low = set.objects_low[i]
			obj_cage = None if i >= len(set.objects_cage) else set.objects_cage[i]

			# Disable hide render
			obj_low.hide_render = False

			bpy.ops.object.select_all(action='DESELECT')
			obj_low.select_set( state = True, view_layer = None)
			bpy.context.view_layer.objects.active = obj_low

			if modes[mode].engine == 'BLENDER_EEVEE':
				# Assign image to texture faces
				bpy.ops.object.mode_set(mode='EDIT')
				bpy.ops.mesh.select_all(action='SELECT')

				for area in bpy.context.screen.areas:
					if area.type == 'IMAGE_EDITOR':
						area.spaces[0].image = image
				# bpy.data.screens['UV Editing'].areas[1].spaces[0].image = image


				bpy.ops.object.mode_set(mode='OBJECT')

			for obj_high in (set.objects_high):
				obj_high.select_set( state = True, view_layer = None)
			cycles_bake(
				mode, 
				bpy.context.scene.texToolsSettings.padding,
				sampling_scale, 
				samples, 
				ray_distance,
				 len(set.objects_high) > 0, 
				 obj_cage
			)

			# Bake Floaters seperate bake
			if len(set.objects_float) > 0:
				bpy.ops.object.select_all(action='DESELECT')
				for obj_high in (set.objects_float):
					obj_high.select_set( state = True, view_layer = None)
				obj_low.select_set( state = True, view_layer = None)

				cycles_bake(
					mode, 
					0,
					sampling_scale, 
					samples, 
					ray_distance, 
					len(set.objects_float) > 0,
					obj_cage
				)

			# Set background image (CYCLES & BLENDER_EEVEE)
			for area in bpy.context.screen.areas:
				if area.type == 'IMAGE_EDITOR':
					area.spaces[0].image = image

		# Restore renderable for cage objects
		for obj_cage in set.objects_cage:
			obj_cage.hide_render = False


		# Downsample image?
		if not bake_single or (bake_single and s == len(sets)-1):
			# When baking single, only downsample on last bake
			if render_width != size[0] or render_height != size[1]:
				image.scale(size[0],size[1])
		
		# Apply composite nodes on final image result
		if modes[mode].composite:
			apply_composite(image, modes[mode].composite, bpy.context.scene.texToolsSettings.bake_curvature_size)

		# image.save()

	# Restore non node materials
	ub.restore_materials()




def apply_composite(image, scene_name, size):
	previous_scene = bpy.context.window.scene

	# Get Scene with compositing nodes
	scene = None
	if scene_name in bpy.data.scenes:
		scene = bpy.data.scenes[scene_name]
	else:
		path = os.path.join(os.path.dirname(__file__), "resources/compositing.blend")+"\\Scene\\"
		bpy.ops.wm.append(filename=scene_name, directory=path, link=False, autoselect=False)
		scene = bpy.data.scenes[scene_name]

	if scene:
		# Switch scene
		bpy.context.window.scene = scene

		#Setup composite nodes for Curvature
		if "Image" in scene.node_tree.nodes:
			scene.node_tree.nodes["Image"].image = image

		if "Offset" in scene.node_tree.nodes:
			scene.node_tree.nodes["Offset"].outputs[0].default_value = size
			print("Assign offset: {}".format(scene.node_tree.nodes["Offset"].outputs[0].default_value))

		# Render image
		bpy.ops.render.render(use_viewport=False)
		

		# Get last images of viewer node and render result
		image_viewer_node = get_last_item("Viewer Node", bpy.data.images)
		image_render_result = get_last_item("Render Result", bpy.data.images)

		#Copy pixels
		image.pixels = image_viewer_node.pixels[:]
		image.update()

		if image_viewer_node:
			bpy.data.images.remove(image_viewer_node)
		if image_render_result:
			bpy.data.images.remove(image_render_result)

		#Restore scene & remove other scene
		bpy.context.window.scene = previous_scene
		
		# Delete compositing scene
		bpy.data.scenes.remove(scene)



def get_last_item(key_name, collection):
	# bpy.data.images
	# Get last image of a series, e.g. .001, .002, 003
	keys = []
	for item in collection:
		if key_name in item.name:
			keys.append(item.name)

	print("Search for {}x : '{}'".format(len(keys), ",".join(keys) ) )

	if len(keys) > 0:
		return collection[keys[-1]]

	return None




def setup_image(mode, name, width, height, path, is_clear):
	image = None

	print("Path "+path)
	if name in bpy.data.images:
		image = bpy.data.images[name]
		if image.source == 'FILE':
			# Clear image if it was deleted outside
			if not os.path.isfile(image.filepath):
				image.user_clear()
				bpy.data.images.remove(image)
		# bpy.data.images[name].update()

		# if bpy.data.images[name].has_data == False:
			

		# Previous image does not have data, remove first
	# 	print("Image pointer exists but no data "+name)
	# 	image = bpy.data.images[name]
	# 	image.update()
	# image.generated_height = height
	# bpy.data.images.remove(bpy.data.images[name])

	if name not in bpy.data.images:
		# Create new image with 32 bit float
		is_float_32 = bpy.context.preferences.addons["textools"].preferences.bake_32bit_float == '32'
		image = bpy.data.images.new(name, width=width, height=height, float_buffer=is_float_32)
		if "_normal_" in image.name:
    			image.colorspace_settings.name = 'Non-Color'
		else:
			image.colorspace_settings.name = 'sRGB'


	else:
		# Reuse existing Image
		image = bpy.data.images[name]
		# Reisze?
		if image.size[0] != width or image.size[1] != height or image.generated_width != width or image.generated_height != height:
			image.generated_width = width
			image.generated_height = height
			image.scale(width, height)

	# Fill with plain color
	if is_clear:
		image.generated_color = modes[mode].color
		image.generated_type = 'BLANK'


	image.file_format = 'TARGA'

	# TODO: Verify that the path exists
	# image.filepath_raw = path

	return image



def setup_image_bake_node(obj, image):

	if len(obj.data.materials) <= 0:
			print("ERROR, need spare material to setup active image texture to bake!!!")
	else:
		for slot in obj.material_slots:
			if slot.material:
				if(slot.material.use_nodes == False):
					slot.material.use_nodes = True

				# Assign bake node
				tree = slot.material.node_tree
				node = None
				if "bake" in tree.nodes:
					node = tree.nodes["bake"]
				else:
					node = tree.nodes.new("ShaderNodeTexImage")
				node.name = "bake"
				node.select = True
				node.image = image
				tree.nodes.active = node



def assign_vertex_color(mode, obj):
	if modes[mode].setVColor:
		modes[mode].setVColor(obj)



def assign_material(mode, obj, material_bake=None, material_empty=None):
	ub.store_materials(obj)

	bpy.context.view_layer.objects.active = obj
	obj.select_set( state = True, view_layer = None)

	# Select All faces
	bpy.ops.object.mode_set(mode='EDIT')
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data);
	faces = [face for face in bm.faces if face.select]
	bpy.ops.mesh.select_all(action='SELECT')


	if material_bake:
		# Setup properties of bake materials
		if mode == 'wireframe':
			if "Value" in material_bake.node_tree.nodes:
				material_bake.node_tree.nodes["Value"].outputs[0].default_value = bpy.context.scene.texToolsSettings.bake_wireframe_size
		if mode == 'bevel_mask':
			if "Bevel" in material_bake.node_tree.nodes:
				material_bake.node_tree.nodes["Bevel"].inputs[0].default_value = bpy.context.scene.texToolsSettings.bake_bevel_size
				material_bake.node_tree.nodes["Bevel"].samples = bpy.context.scene.texToolsSettings.bake_bevel_samples
		if mode == 'normal_tangent_bevel':
			if "Bevel" in material_bake.node_tree.nodes:
				material_bake.node_tree.nodes["Bevel"].inputs[0].default_value = bpy.context.scene.texToolsSettings.bake_bevel_size
				material_bake.node_tree.nodes["Bevel"].samples = bpy.context.scene.texToolsSettings.bake_bevel_samples
		if mode == 'normal_object_bevel':
			if "Bevel" in material_bake.node_tree.nodes:
				material_bake.node_tree.nodes["Bevel"].inputs[0].default_value = bpy.context.scene.texToolsSettings.bake_bevel_size
				material_bake.node_tree.nodes["Bevel"].samples = bpy.context.scene.texToolsSettings.bake_bevel_samples



	# Don't apply in diffuse mode
	if mode != 'diffuse':
		if material_bake:
			# Override with material_bake
			if len(obj.material_slots) == 0:
				obj.data.materials.append(material_bake)

			else:
				obj.material_slots[0].material = material_bake
				obj.active_material_index = 0
				bpy.ops.object.material_slot_assign()

		elif material_empty:
			#Assign material_empty if no material available
			if len(obj.material_slots) == 0:
				obj.data.materials.append(material_empty)

			else: # not obj.material_slots[0].material:
				obj.material_slots[0].material = material_empty
				obj.active_material_index = 0
				bpy.ops.object.material_slot_assign()

	# Restore Face selection
	bpy.ops.mesh.select_all(action='DESELECT')
	for face in faces:
		face.select = True

	bpy.ops.object.mode_set(mode='OBJECT')

			

			



def get_material(mode):

	

	if modes[mode].material == "":
		return None # No material setup requires

	# Find or load material
	name = modes[mode].material
	path = os.path.join(os.path.dirname(__file__), "resources/materials.blend")+"\\Material\\"
	if "bevel" in mode:
		path = os.path.join(os.path.dirname(__file__), "resources/materials_2.80.blend")+"\\Material\\"
	
	print("Get mat {}\n{}".format(mode, path))

	if bpy.data.materials.get(name) is None:
		print("Material not yet loaded: "+mode)
		bpy.ops.wm.append(filename=name, directory=path, link=False, autoselect=False)

	return bpy.data.materials.get(name)




def cycles_bake(mode, padding, sampling_scale, samples, ray_distance, is_multi, obj_cage):
	

	# if modes[mode].engine == 'BLENDER_EEVEE': 
	# 	# Snippet: https://gist.github.com/AndrewRayCode/760c4634a77551827de41ed67585064b
	# 	bpy.context.scene.render.bake_margin = padding

	# 	# AO Settings
	# 	bpy.context.scene.render.bake_type = modes[mode].type
	# 	bpy.context.scene.render.use_bake_normalize = True

	# 	if modes[mode].type == 'AO':
	# 		bpy.context.scene.world.light_settings.use_ambient_occlusion = True
	# 		bpy.context.scene.world.light_settings.gather_method = 'RAYTRACE'
	# 		bpy.context.scene.world.light_settings.samples = samples

	# 	bpy.context.scene.render.use_bake_selected_to_active = is_multi
	# 	bpy.context.scene.render.bake_distance = ray_distance
	# 	bpy.context.scene.render.use_bake_clear = False

	# 	bpy.ops.object.bake_image()


	if modes[mode].engine == 'CYCLES' or modes[mode].engine == 'BLENDER_EEVEE' :

		if modes[mode].normal_space == 'OBJECT':
			#See: https://twitter.com/Linko_3D/status/963066705584054272
			bpy.context.scene.render.bake.normal_r = 'POS_X'
			bpy.context.scene.render.bake.normal_g = 'POS_Z'
			bpy.context.scene.render.bake.normal_b = 'NEG_Y'

		elif modes[mode].normal_space == 'TANGENT':
			bpy.context.scene.render.bake.normal_r = 'POS_X'
			bpy.context.scene.render.bake.normal_b = 'POS_Z'
			# Adjust Y swizzle from Addon preferences
			swizzle_y = bpy.context.preferences.addons["textools"].preferences.swizzle_y_coordinate
			if swizzle_y == 'Y-':
				bpy.context.scene.render.bake.normal_g = 'NEG_Y'
			elif swizzle_y == 'Y+':
				bpy.context.scene.render.bake.normal_g = 'POS_Y'

		# Set samples
		bpy.context.scene.cycles.samples = samples

		# Speed up samples for simple render modes
		if modes[mode].type == 'EMIT' or modes[mode].type == 'DIFFUSE':
			bpy.context.scene.cycles.samples = 1

		# Pixel Padding
		bpy.context.scene.render.bake.margin = padding * sampling_scale

		# Disable Direct and Indirect for all 'DIFFUSE' bake types
		if modes[mode].type == 'DIFFUSE':
			bpy.context.scene.render.bake.use_pass_direct = False
			bpy.context.scene.render.bake.use_pass_indirect = False
			bpy.context.scene.render.bake.use_pass_color = True

		if obj_cage is None:
			# Bake with Cage
			bpy.ops.object.bake(
				type=modes[mode].type, 
				use_clear=False, 
				cage_extrusion=ray_distance, 

				use_selected_to_active=is_multi, 
				normal_space=modes[mode].normal_space
			)
		else:
			# Bake without Cage
			bpy.ops.object.bake(
				type=modes[mode].type, 
				use_clear=False, 
				cage_extrusion=ray_distance, 

				use_selected_to_active=is_multi, 
				normal_space=modes[mode].normal_space,

				#Use Cage and assign object
				use_cage=True, 	
				cage_object=obj_cage.name
			)

bpy.utils.register_class(op)
