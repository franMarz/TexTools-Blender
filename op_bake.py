import bpy
import os
import bmesh
import time
from mathutils import Vector

from . import utilities_ui
from . import settings
from . import utilities_bake as ub


# Notes: https://docs.blender.org/manual/en/dev/render/blender_render/bake.html
modes={
	#'displacement':			ub.BakeMode('',						type='DISPLACEMENT', use_project=True, color=(0, 0, 0, 1), engine='CYCLES'),
	'normal_tangent':			ub.BakeMode('',						type='NORMAL', 		color=(0.5, 0.5, 1, 1), use_project=True),
	'normal_object': 			ub.BakeMode('',						type='NORMAL', 		color=(0.5, 0.5, 1, 1), normal_space='OBJECT'),
	'bevel_mask':				ub.BakeMode('bake_bevel_mask',		type='EMIT', 		color=(0, 0, 0, 1), 	params=["bake_bevel_samples","bake_bevel_size"]),
	'normal_tangent_bevel':		ub.BakeMode('bake_bevel_normal',	type='NORMAL', 		color=(0.5, 0.5, 1, 1),	params=["bake_bevel_samples","bake_bevel_size"]),
	'normal_object_bevel':		ub.BakeMode('bake_bevel_normal',	type='NORMAL', 		color=(0.5, 0.5, 1, 1),	normal_space='OBJECT', params=["bake_bevel_samples","bake_bevel_size"]),
	'cavity': 					ub.BakeMode('bake_cavity',			type='EMIT', 		setVColor=ub.setup_vertex_color_dirty),
	'paint_base': 				ub.BakeMode('bake_paint_base',		type='EMIT'),
	'dust': 					ub.BakeMode('bake_dust',			type='EMIT', 		setVColor=ub.setup_vertex_color_dirty),
	'ao':						ub.BakeMode('',						type='AO', 			params=["bake_samples"], engine='CYCLES'),
	'position':					ub.BakeMode('bake_position',		type='EMIT'),
	'curvature':				ub.BakeMode('',						type='NORMAL',		use_project=True, 		params=["bake_curvature_size"], composite="curvature"),
	'wireframe':				ub.BakeMode('bake_wireframe',		type='EMIT', 		color=(0, 0, 0, 1), 	params=["bake_wireframe_size"]),
	'id_element':				ub.BakeMode('bake_vertex_color',	type='EMIT', 		setVColor=ub.setup_vertex_color_id_element),
	'id_material':				ub.BakeMode('bake_vertex_color',	type='EMIT', 		setVColor=ub.setup_vertex_color_id_material),
	'selection':				ub.BakeMode('bake_vertex_color',	type='EMIT', 		color=(0, 0, 0, 1), setVColor=ub.setup_vertex_color_selection),
	'diffuse':					ub.BakeMode('',						type='DIFFUSE'),
	'base_color':				ub.BakeMode('',						type='DIFFUSE',		relink = {'needed':True, 'b':4}),
	'sss_strength':				ub.BakeMode('',						type='ROUGHNESS',	color=(0, 0, 0, 1),		relink = {'needed':True, 'b':7, 'n':1}),
	'sss_color':				ub.BakeMode('',						type='DIFFUSE',		relink = {'needed':True, 'b':0, 'n':3}),
	'metallic':					ub.BakeMode('',						type='ROUGHNESS',	color=(0, 0, 0, 1),		relink = {'needed':True, 'b':7, 'n':4}),
	'specular':					ub.BakeMode('',						type='ROUGHNESS',	color=(0, 0, 0, 1),		relink = {'needed':True, 'b':7, 'n':5}),
	'specular_tint':			ub.BakeMode('',						type='ROUGHNESS',	color=(0, 0, 0, 1),		relink = {'needed':True, 'b':7, 'n':6}),
	'roughness':				ub.BakeMode('',						type='ROUGHNESS',	color=(0, 0, 0, 1)),
	'glossiness':				ub.BakeMode('',						type='ROUGHNESS',	color=(1, 1, 1, 1), 	invert=True),
	'anisotropic':				ub.BakeMode('',						type='ROUGHNESS',	color=(0, 0, 0, 1),		relink = {'needed':True, 'b':7, 'n':8}),
	'anisotropic_rotation':		ub.BakeMode('',						type='ROUGHNESS',	color=(0, 0, 0, 1),		relink = {'needed':True, 'b':7, 'n':9}),
	'sheen':					ub.BakeMode('',						type='ROUGHNESS',	color=(0, 0, 0, 1),		relink = {'needed':True, 'b':7, 'n':10}),
	'sheen_tint':				ub.BakeMode('',						type='ROUGHNESS',	color=(0, 0, 0, 1),		relink = {'needed':True, 'b':7, 'n':11}),
	'clearcoat':				ub.BakeMode('',						type='ROUGHNESS',	color=(0, 0, 0, 1),		relink = {'needed':True, 'b':7, 'n':12}),
	'clearcoat_roughness':		ub.BakeMode('',						type='ROUGHNESS',	color=(0, 0, 0, 1),		relink = {'needed':True, 'b':7, 'n':13}),
	'transmission':				ub.BakeMode('',						type='ROUGHNESS',	color=(0, 0, 0, 1),		relink = {'needed':True, 'b':7, 'n':15}),
	'transmission_roughness':	ub.BakeMode('',						type='ROUGHNESS',	color=(0, 0, 0, 1),		relink = {'needed':True, 'b':7, 'n':16}),
	'emission':					ub.BakeMode('',						type='EMIT',		color=(0, 0, 0, 1))
}

bversion = float(bpy.app.version_string[0:4])
if bversion >= 2.91:
	modes['emission_strength']= ub.BakeMode('',			type='ROUGHNESS', color=(0, 0, 0, 1), relink = {'needed':True, 'b':7, 'n':18})
	modes['alpha']= 			ub.BakeMode('',			type='ROUGHNESS', color=(0, 0, 0, 1), relink = {'needed':True, 'b':7, 'n':19})
else:
	modes['alpha']= 			ub.BakeMode('',			type='ROUGHNESS', color=(0, 0, 0, 1), relink = {'needed':True, 'b':7, 'n':18})



class op(bpy.types.Operator):
	bl_idname = "uv.textools_bake"
	bl_label = "Bake"
	bl_description = "Bake selected objects"

	@classmethod
	def poll(cls, context):

		if len(settings.sets) == 0:
			return False
		
		bake_mode = utilities_ui.get_bake_mode()
		if bake_mode not in modes:
			return False
		
		if modes[bake_mode].material == "":
			for set in settings.sets:
				if (len(set.objects_high) + len(set.objects_float)) == 0:
					for obj in set.objects_low:
						if len(obj.data.materials) <= 0:
							settings.bakeable = False
							return False
						else:
							for slot in obj.material_slots:
								if slot.material:
									if slot.material.use_nodes == False and modes[bake_mode].relink['needed']:
										settings.bakeable = False
										return False
									elif 'Principled BSDF' not in slot.material.node_tree.nodes and modes[bake_mode].relink['needed']:
										settings.bakeable = False
										return False
								else:
									settings.bakeable = False
									return False
				else:
					for obj in (set.objects_high+set.objects_float):
						if len(obj.data.materials) <= 0:
							settings.bakeable = False
							return False
						else:
							for slot in obj.material_slots:
								if slot.material:
									if slot.material.use_nodes == False and modes[bake_mode].relink['needed']:
										settings.bakeable = False
										return False
									elif 'Principled BSDF' not in slot.material.node_tree.nodes and modes[bake_mode].relink['needed']:
										settings.bakeable = False
										return False
								else:
									settings.bakeable = False
									return False

		settings.bakeable = True
		return True


	def execute(self, context):

		startTime = time.monotonic()
		bake_mode = utilities_ui.get_bake_mode()

		if bake_mode not in modes:
			self.report({'ERROR_INVALID_INPUT'}, "Uknown mode '{}' only available: '{}'".format(bake_mode, ", ".join(modes.keys() )) )
			return {'CANCELLED'}

		# Avoid weird rendering problems when Progressive Refine is activated from Blender 2.90 TODO: isolate inside an IF clause when cyclesX enters master
		#if bversion < 3.10 ? :
		pre_progressive_refine = bpy.context.scene.cycles.use_progressive_refine
		bpy.context.scene.cycles.use_progressive_refine = False
		if bversion >= 2.92:
			pretarget = bpy.context.scene.render.bake.target
			if pretarget != 'IMAGE_TEXTURES':
				bpy.context.scene.render.bake.target = 'IMAGE_TEXTURES'

		# Store Selection
		selected_objects 	= [obj for obj in bpy.context.selected_objects]
		active_object 		= bpy.context.view_layer.objects.active
		ub.store_bake_settings()

		if bake_mode == 'id_material':
			#try to redirect deleted materials which were recovered with undo 
			for i, material in enumerate(ub.allMaterials):
				try: material.name
				except:	ub.allMaterials[i] = bpy.data.materials.get(ub.allMaterialsNames[i])
			#store a persistent ordered list of all materials in the scene
			if len(ub.allMaterials) == 0 :
				ub.allMaterials = [material for material in bpy.data.materials if material.users != 0]
				ub.allMaterialsNames = [material.name for material in ub.allMaterials]
			else:
				for obj in selected_objects:
					for i in range(len(obj.material_slots)):
						slot = obj.material_slots[i]
						if slot.material:
							if slot.material not in ub.allMaterials :	# and slot.material.users != 0 
								ub.allMaterials.append(slot.material)
								ub.allMaterialsNames.append(slot.material.name)

		# Render sets
		bake(
			self = self, 
			mode = bake_mode,
			size = bpy.context.scene.texToolsSettings.size, 

			bake_single = bpy.context.scene.texToolsSettings.bake_force_single,
			sampling_scale = int(bpy.context.scene.texToolsSettings.bake_sampling),
			samples = bpy.context.scene.texToolsSettings.bake_samples,
			cage_extrusion = bpy.context.scene.texToolsSettings.bake_cage_extrusion,
			ray_distance = bpy.context.scene.texToolsSettings.bake_ray_distance
		)
		
		# Restore selection
		ub.restore_bake_settings()
		bpy.ops.object.select_all(action='DESELECT')
		for obj in selected_objects:
			obj.select_set( state = True, view_layer = None)
		if active_object:
			bpy.context.view_layer.objects.active = active_object
		
		#TODO: isolate inside an IF clause when cyclesX enters master
		#if bversion < 3.10 ? :
		bpy.context.scene.cycles.use_progressive_refine = pre_progressive_refine
		if bversion >= 2.92:
			bpy.context.scene.render.bake.target = pretarget

		elapsed = round(time.monotonic()-startTime, 2)
		self.report({'INFO'}, "Baking finished, elapsed:" + str(elapsed) + "s.")

		return {'FINISHED'}



def bake(self, mode, size, bake_single, sampling_scale, samples, cage_extrusion, ray_distance):

	print("Bake '{}'".format(mode))

	bpy.context.scene.render.engine = modes[mode].engine	#Switch render engine

	# Disable edit mode
	if bpy.context.view_layer.objects.active != None and bpy.context.object.mode != 'OBJECT':
		bpy.ops.object.mode_set(mode='OBJECT')

	render_width = sampling_scale * size[0]
	render_height = sampling_scale * size[1]

	# Get Materials
	tunedMaterials = {}
	material_loaded = get_material(mode)
	material_empty = None
	
	# Get the baking sets / pairs
	sets = settings.sets

	for s in range(0,len(sets)):
		set = sets[s]
		# Requires 1+ low poly objects
		if len(set.objects_low) == 0:
			self.report({'ERROR_INVALID_INPUT'}, "No low poly object as part of the '{}' set".format(set.name) )
			return {'CANCELLED'}
		# Check for UV maps
		for obj in set.objects_low:
			if not obj.data.uv_layers or len(obj.data.uv_layers) == 0:
				self.report({'ERROR_INVALID_INPUT'}, "No UV map available for '{}'".format(obj.name))
				return {'CANCELLED'}
		# Check for cage inconsistencies
		if len(set.objects_cage) > 0 and (len(set.objects_low) != len(set.objects_cage)):
			self.report({'ERROR_INVALID_INPUT'}, "{}x cage objects do not match {}x low poly objects for '{}'".format(len(set.objects_cage), len(set.objects_low), obj.name))
			return {'CANCELLED'}		

	preStates = []	# list to store original materials setups in case they must be changed and restored

	temp_sets = []
	if material_loaded:
		for bakeset in sets:
			low = []
			high = []
			cage = bakeset.objects_cage
			float = []
			name = bakeset.name
			temp_set = ub.BakeSet(name, low, cage, high, float)

			if (len(bakeset.objects_high) + len(bakeset.objects_float)) == 0 :
				for obj in bakeset.objects_low:
					temp_obj = obj.copy()
					temp_obj.data = obj.data.copy()
					obj.users_collection[0].objects.link(temp_obj)
					temp_set.objects_low.append(temp_obj)
			else:
				temp_set.objects_low = bakeset.objects_low
				for obj in bakeset.objects_high:
					temp_obj = obj.copy()
					temp_obj.data = obj.data.copy()
					obj.users_collection[0].objects.link(temp_obj)
					temp_set.objects_high.append(temp_obj)
				for obj in bakeset.objects_float:
					temp_obj = obj.copy()
					temp_obj.data = obj.data.copy()
					obj.users_collection[0].objects.link(temp_obj)
					temp_set.objects_float.append(temp_obj)
			
			temp_sets.append(temp_set)
	
	else:
		temp_sets = sets


	for s in range(0,len(temp_sets)):
		set = temp_sets[s]

		# Get image name
		name_texture = "{}_{}".format(set.name, mode)
		if bake_single:
			name_texture = "{}_{}".format(sets[0].name, mode)	# In Single mode bake into same texture
		#path = bpy.path.abspath("//{}.tga".format(name_texture))

		# Setup Image
		is_clear = (not bake_single) or (bake_single and s==0)
		image = setup_image(mode, name_texture, render_width, render_height, is_clear)
		
		preStatesSet = []

		# Assign Materials to Objects / tune the existing materials, and distribute temp bake image nodes
		if (len(set.objects_high) + len(set.objects_float)) == 0:
			# Low poly bake: Assign material to lowpoly or tune the existing material/s
			for obj in set.objects_low:
				if material_loaded is not None :
					assign_vertex_color(mode, obj)
					assign_material(mode, obj, material_loaded)
				elif modes[mode].relink['needed']:
					for i in range(len(obj.material_slots)):
						slot = obj.material_slots[i]
						if slot.material:
							if slot.material not in tunedMaterials :	# and slot.material.users != 0 
								tunedMaterials[slot.material] = relink_nodes(mode, slot.material)
					setup_image_bake_node(obj, image)
				else:
					setup_image_bake_node(obj, image)
			if material_loaded is not None :
				setup_image_bake_node(set.objects_low[0], image)
		else:
			# High to low poly: Low poly requires any material to bake into image
			for obj in set.objects_low:
				if len(obj.material_slots) == 0:
					if "TT_bake_node" in bpy.data.materials:
						material_empty = bpy.data.materials["TT_bake_node"]
					else:
						material_empty = bpy.data.materials.new(name="TT_bake_node")
					obj.data.materials.append(material_empty)
				setup_image_bake_node(obj, image)
			# Assign material to highpoly or tune the existing material/s
			for obj in (set.objects_high+set.objects_float):
				if material_loaded is not None :
					assign_vertex_color(mode, obj)
					assign_material(mode, obj, material_loaded)
				elif modes[mode].relink['needed']:
					for i in range(len(obj.material_slots)):
						slot = obj.material_slots[i]
						if slot.material:
							if slot.material not in tunedMaterials :	# and slot.material.users != 0 
								tunedMaterials[slot.material] = relink_nodes(mode, slot.material)

		preStates.append(preStatesSet)

		#print("Bake '{}' = {}".format(set.name, path))
		print("Bake "+set.name)

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

			# if modes[mode].engine == 'BLENDER_EEVEE':	#TODO would this still be needed when the set background code has been moved to the next lines?
			# 	# Assign image to texture faces
			# 	bpy.ops.object.mode_set(mode='EDIT')
			# 	bpy.ops.mesh.select_all(action='SELECT')
			# 	for area in bpy.context.screen.areas:
			# 		if area.type == 'IMAGE_EDITOR':
			# 			area.spaces[0].image = image
			# 	# bpy.data.screens['UV Editing'].areas[1].spaces[0].image = image
			# 	bpy.ops.object.mode_set(mode='OBJECT')

			if is_clear:
				# Set background image (CYCLES & BLENDER_EEVEE)
				for area in bpy.context.screen.areas:
					if area.type == 'IMAGE_EDITOR':
						area.spaces[0].image = image
				# Invert background if final invert of the baked image is needed
				if modes[mode].invert:
					bpy.ops.image.invert(invert_r=True, invert_g=True, invert_b=True)

			for obj_high in (set.objects_high):
				obj_high.select_set( state = True, view_layer = None)
			
			cycles_bake(
				mode,
				bpy.context.scene.texToolsSettings.padding,
				sampling_scale,
				samples,
				cage_extrusion,
				ray_distance,
				len(set.objects_high) > 0,
				obj_cage
			)

			# Bake Floaters separate bake
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
					cage_extrusion,
					ray_distance,
					len(set.objects_float) > 0,
					obj_cage
				)

		if modes[mode].invert and is_clear:
			bpy.ops.image.invert(invert_r=True, invert_g=True, invert_b=True)
		
		# Restore renderable for cage objects
		for obj_cage in set.objects_cage:
			obj_cage.hide_render = False

		# Downsample image? (when baking single, only downsample on last bake)
		if not bake_single or (bake_single and s == len(sets)-1):
			if render_width != size[0] or render_height != size[1]:
				image.scale(size[0],size[1])
		
		# Apply composite nodes on final image result (TODO: test if this works properly when baking single)
		if modes[mode].composite:
			apply_composite(image, modes[mode].composite, bpy.context.scene.texToolsSettings.bake_curvature_size)
		
		# TODO: if autosave: image.save() (when baking single, only save on last bake)


	# Restore Tuned Materials
	if modes[mode].relink['needed']:
		for material in tunedMaterials:
			relink_restore(mode, material, tunedMaterials[material])

	for s in range(0,len(temp_sets)):
		set = temp_sets[s]

		# Delete provisional bake nodes used during baking
		if (len(set.objects_high) + len(set.objects_float)) > 0:
			for obj in set.objects_low:
				if obj.material_slots[0].material == material_empty:
					bpy.ops.object.material_slot_remove({'object': obj})
				clear_image_bake_node(obj)
		else:
			for obj in set.objects_low:
				clear_image_bake_node(obj)
		
		# Delete temp objects created for baking
		if material_loaded:
			if (len(set.objects_high) + len(set.objects_float)) == 0 :
				for obj in set.objects_low:
					obj.data.materials.clear()
					bpy.data.objects.remove(obj, do_unlink=True)
			else:
				for obj in (set.objects_high + set.objects_float) :
					obj.data.materials.clear()
					bpy.data.objects.remove(obj, do_unlink=True)
			if s == len(temp_sets)-1:
				material_loaded.user_clear()




def apply_composite(image, scene_name, size):
	previous_scene = bpy.context.window.scene
	# avoid Sun Position addon error
	preWorldPropertiesNodesBool = previous_scene.world.use_nodes

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
		bpy.context.window.scene.world.use_nodes = preWorldPropertiesNodesBool

		#Setup composite nodes for Curvature
		if "Image" in scene.node_tree.nodes:
			scene.node_tree.nodes["Image"].image = image

		if "Offset" in scene.node_tree.nodes:
			scene.node_tree.nodes["Offset"].outputs[0].default_value = size

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



def setup_image(mode, name, width, height, is_clear):
	image = None
	preferences = bpy.context.preferences.addons[__package__].preferences

	if preferences.bool_bake_back_color == 'CUSTOM':
		bake_back_color = bpy.context.scene.texToolsSettings.bake_back_color
	else:
		bake_back_color = modes[mode].color

	def set_color_space(image):
		image.alpha_mode = 'NONE'
		if "_normal_" in image.name:
			image.colorspace_settings.name = 'Non-Color'
		else:
			image.colorspace_settings.name = bpy.context.scene.texToolsSettings.bake_color_space

	def resize(image):
		if image.size[0] != width or image.size[1] != height or image.generated_width != width or image.generated_height != height:
			#image.generated_width = width
			#image.generated_height = height
			image.scale(width, height)

	def apply_color(image):
		# Set background color to a small version of the image for performance
		image.pixels = [pv for p in range(4) for pv in bake_back_color]
		# Set final size of the image
		resize(image)

	def image_create():
		# Create a small new image
		is_float_32 = preferences.bake_32bit_float == '32'
		image = bpy.data.images.new(name, width=2, height=2, alpha=True, float_buffer=is_float_32)
		set_color_space(image)
		apply_color(image)
		image.file_format = 'TARGA'	#TODO revisit this when implementing image save
		return image

	if name in bpy.data.images:
		image = bpy.data.images[name]
		if image.source == 'FILE':
			# Clear image if it was deleted or moved outside
			print("Existing image expected path "+bpy.path.abspath(image.filepath))
			if not os.path.isfile(bpy.path.abspath(image.filepath)):
				print("Unlinking missing image "+name)
				bpy.data.images.remove(image, do_unlink=True)
				image = image_create()
				return image
		
		if is_clear:
			set_color_space(image)
			#image.generated_width = 2
			#image.generated_height = 2
			image.scale(2, 2)
			apply_color(image)
	else:
		image = image_create()
	
	return image



def setup_image_bake_node(obj, image):
	if len(obj.data.materials) <= 0:
		print("ERROR, need spare material to setup active image texture to bake!!!")
	else:
		for slot in obj.material_slots:
			if slot.material:
				if slot.material.use_nodes == False:
					slot.material.use_nodes = True
				# Assign bake node
				tree = slot.material.node_tree
				node = None
				if "TexTools_bake" in tree.nodes:
					node = tree.nodes["TexTools_bake"]
				else:
					node = tree.nodes.new("ShaderNodeTexImage")
					node.name = "TexTools_bake"
				node.select = True
				node.image = image
				tree.nodes.active = node



def clear_image_bake_node(obj):
	if len(obj.data.materials) <= 0:
		return
	else:
		for slot in obj.material_slots:
			if slot.material:
				if(slot.material.use_nodes == False):
					slot.material.use_nodes = True
				tree = slot.material.node_tree
				if "TexTools_bake" in tree.nodes:
					node = tree.nodes["TexTools_bake"]
					tree.nodes.remove(node)



def relink_nodes(mode, material):

	if material.use_nodes == False:
		material.use_nodes = True
	tree = material.node_tree
	bsdf_node = tree.nodes['Principled BSDF']

	preLinks = []

	if mode != 'base_color':
		# set b, which is the base(original) socket index, and n, which is the new-values-source index for the base socket
		b, n = modes[mode].relink['b'], modes[mode].relink['n']

		base_node = base_socket = None
		if len(bsdf_node.inputs[b].links) != 0 :
			base_node = bsdf_node.inputs[b].links[0].from_node
			base_socket = bsdf_node.inputs[b].links[0].from_socket.name
		base_value = (bsdf_node.inputs[b].default_value, )
		# If the base value is a color, decompose its value so it can be stored and recovered later, otherwise its value will change while the swap of sockets is committed
		if not isinstance(base_value[0], float):
			base_value = ((base_value[0][0],base_value[0][1],base_value[0][2],base_value[0][3]), )
		new_node = None

		if len(bsdf_node.inputs[n].links) != 0 :
			new_node = bsdf_node.inputs[n].links[0].from_node
			new_node_socket = bsdf_node.inputs[n].links[0].from_socket.name
			if (new_node == base_node and new_node != None) and base_socket == new_node_socket :
				preLinks = [None, None, (None,)]
			else:
				if base_node:
					preLinks = [base_node, base_socket, base_value]
				else:
					preLinks = [None, None, base_value]
				bsdf_node.inputs[b].default_value = bsdf_node.inputs[n].default_value
				tree.links.new(new_node.outputs[new_node_socket], bsdf_node.inputs[b])
		else:
			if base_node:
				preLinks = [base_node, base_socket, base_value]
				tree.links.remove(bsdf_node.inputs[b].links[0])
			else:
				preLinks = [None, None, base_value]
			bsdf_node.inputs[b].default_value = bsdf_node.inputs[n].default_value
	
	else:
		metallic_node = None
		if len(bsdf_node.inputs[4].links) != 0 :
			metallic_node = bsdf_node.inputs[4].links[0].from_node
			metallic_socket = bsdf_node.inputs[4].links[0].from_socket.name
			preLinks = [metallic_node, metallic_socket, (bsdf_node.inputs[4].default_value, )]
			tree.links.remove(bsdf_node.inputs[4].links[0])
		else:
			preLinks = [None, None, (bsdf_node.inputs[4].default_value, )]
		bsdf_node.inputs[4].default_value = 0

	return preLinks



def relink_restore(mode, material, preLinks):

	if material.use_nodes == False:
		material.use_nodes = True
	tree = material.node_tree
	bsdf_node = tree.nodes['Principled BSDF']

	# recover the b value, which is the base(original) socket index to be resetted to its original values
	b = modes[mode].relink['b']
	base_node = preLinks[0]
	base_socket = preLinks[1]
	base_value = preLinks[2][0]

	if base_node is None:
		if base_value is not None:
			if len(bsdf_node.inputs[b].links) != 0:
				tree.links.remove(bsdf_node.inputs[b].links[0])
			bsdf_node.inputs[b].default_value = base_value
	else:
		tree.links.new(base_node.outputs[base_socket], bsdf_node.inputs[b])
		bsdf_node.inputs[b].default_value = base_value



def assign_vertex_color(mode, obj):
	if modes[mode].setVColor:
		if len(obj.data.vertex_colors) > 0 :
			vclsNames = [vcl.name for vcl in obj.data.vertex_colors]
			if 'TexTools' in vclsNames :
				if obj.data.vertex_colors['TexTools'].active == False :
					obj.data.vertex_colors['TexTools'].active = True
			else:
				obj.data.vertex_colors.new(name='TexTools')
				obj.data.vertex_colors['TexTools'].active = True
		else:
			obj.data.vertex_colors.new(name='TexTools')
		
		modes[mode].setVColor(obj)



def assign_material(mode, obj, material_bake=None):
	if material_bake is None :
		return	# No material assignation required

	bpy.context.view_layer.objects.active = obj
	obj.select_set( state = True, view_layer = None)

	# Select All faces
	bpy.ops.object.mode_set(mode='EDIT')
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	for face in bm.faces:
		face.select = True

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

	# Override with material_bake
	if len(obj.material_slots) == 0:
		obj.data.materials.append(material_bake)
	else:
		obj.material_slots[0].material = material_bake
		obj.active_material_index = 0
		bpy.ops.object.material_slot_assign()

	bpy.ops.object.mode_set(mode='OBJECT')



def get_material(mode):

	if modes[mode].material == "":
		return None	# No material setup required

	# Find or load material
	name = modes[mode].material
	path = os.path.join(os.path.dirname(__file__), "resources/materials.blend")+"\\Material\\"
	if "bevel" in mode:
		path = os.path.join(os.path.dirname(__file__), "resources/materials_2.80.blend")+"\\Material\\"
	#print("Get material {}\n{}".format(mode, path))

	if bpy.data.materials.get(name) is None:
		#print("Material not yet loaded: "+mode)
		bpy.ops.wm.append(filename=name, directory=path, link=False, autoselect=False)

	return bpy.data.materials.get(name)




def cycles_bake(mode, padding, sampling_scale, samples, cage_extrusion, ray_distance, is_multi, obj_cage):
	

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
			swizzle_y = bpy.context.preferences.addons[__package__].preferences.swizzle_y_coordinate
			if swizzle_y == 'Y-':
				bpy.context.scene.render.bake.normal_g = 'NEG_Y'
			elif swizzle_y == 'Y+':
				bpy.context.scene.render.bake.normal_g = 'POS_Y'

		# Set samples
		bpy.context.scene.cycles.samples = samples

		# Speed up samples for simple render modes
		if modes[mode].type == 'EMIT' or modes[mode].type == 'DIFFUSE' or modes[mode].type == 'ROUGHNESS':
			bpy.context.scene.cycles.samples = 1

		# Pixel Padding
		bpy.context.scene.render.bake.margin = padding * sampling_scale

		# Disable Direct and Indirect for all 'DIFFUSE' bake types
		if modes[mode].type == 'DIFFUSE':
			bpy.context.scene.render.bake.use_pass_direct = False
			bpy.context.scene.render.bake.use_pass_indirect = False
			bpy.context.scene.render.bake.use_pass_color = True
		
		if bversion < 2.90:
			if obj_cage is None:
				bpy.ops.object.bake(
					type=modes[mode].type, 
					use_clear=False, 
					use_selected_to_active=is_multi, 
					cage_extrusion=cage_extrusion, 
					normal_space=modes[mode].normal_space
				)
			else:
				bpy.ops.object.bake(
					type=modes[mode].type, 
					use_clear=False, 
					use_selected_to_active=is_multi, 
					cage_extrusion=cage_extrusion, 
					normal_space=modes[mode].normal_space, 
					use_cage=True, 
					cage_object=obj_cage.name
				)
		else:
			if obj_cage is None:
				bpy.ops.object.bake(
					type=modes[mode].type, 
					use_clear=False, 
					use_selected_to_active=is_multi, 
					cage_extrusion=cage_extrusion, 
					max_ray_distance=ray_distance, 
					normal_space=modes[mode].normal_space
				)
			else:
				bpy.ops.object.bake(
					type=modes[mode].type, 
					use_clear=False, 
					use_selected_to_active=is_multi, 
					cage_extrusion=cage_extrusion, 
					max_ray_distance=ray_distance, 
					normal_space=modes[mode].normal_space, 
					use_cage=True, 
					cage_object=obj_cage.name
				)


bpy.utils.register_class(op)
