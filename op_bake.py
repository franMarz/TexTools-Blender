import bpy
import os
import time

from . import utilities_ui
from . import utilities_uv
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
	'thickness':				ub.BakeMode('bake_thickness',		type='EMIT', 		color=(0, 0, 0, 1), 	params=["bake_samples","bake_thickness_distance","bake_thickness_contrast","bake_thickness_local"]),
	'cavity': 					ub.BakeMode('bake_cavity',			type='EMIT', 		setVColor=ub.setup_vertex_color_dirty),
	'paint_base': 				ub.BakeMode('bake_paint_base',		type='EMIT'),
	'dust': 					ub.BakeMode('bake_dust',			type='EMIT', 		setVColor=ub.setup_vertex_color_dirty),
	'ao':						ub.BakeMode('',						type='AO', 			params=["bake_samples"], engine='CYCLES'),
	'position':					ub.BakeMode('bake_position',		type='EMIT'),
	'curvature':				ub.BakeMode('',						type='NORMAL',		use_project=True, 	params=["bake_curvature_size"], composite="curvature"),
	'wireframe':				ub.BakeMode('bake_wireframe',		type='EMIT', 		color=(0, 0, 0, 1), params=["bake_wireframe_size"]),
	'id_element':				ub.BakeMode('bake_vertex_color',	type='EMIT', 		setVColor=ub.setup_vertex_color_id_element),
	'id_material':				ub.BakeMode('bake_vertex_color',	type='EMIT', 		setVColor=ub.setup_vertex_color_id_material),
	'selection':				ub.BakeMode('bake_vertex_color',	type='EMIT', 		color=(0, 0, 0, 1), setVColor=ub.setup_vertex_color_selection),
	'diffuse':					ub.BakeMode('',						type='DIFFUSE'),
	'base_color':				ub.BakeMode('',						type='EMIT',							relink = {'needed':True, 'b':ub.chs['ech'], 'n':0}),
	'sss_strength':				ub.BakeMode('',						type='ROUGHNESS',	color=(0, 0, 0, 1),	relink = {'needed':True, 'b':ub.chs['rch'], 'n':ub.chs['ssch']}),
	'sss_color':				ub.BakeMode('',						type='EMIT',							relink = {'needed':True, 'b':ub.chs['ech'], 'n':ub.chs['scch']}),
	'metallic':					ub.BakeMode('',						type='ROUGHNESS',	color=(0, 0, 0, 1),	relink = {'needed':True, 'b':ub.chs['rch'], 'n':ub.chs['mch']}),
	'specular':					ub.BakeMode('',						type='ROUGHNESS',	color=(0, 0, 0, 1),	relink = {'needed':True, 'b':ub.chs['rch'], 'n':ub.chs['sch']}),
	'specular_tint':			ub.BakeMode('',						type='EMIT',		color=(0, 0, 0, 1),	relink = {'needed':True, 'b':ub.chs['ech'], 'n':ub.chs['stch']}),
	'roughness':				ub.BakeMode('',						type='ROUGHNESS',	color=(0, 0, 0, 1)),
	'glossiness':				ub.BakeMode('',						type='ROUGHNESS',	color=(1, 1, 1, 1), invert=True),
	'anisotropic':				ub.BakeMode('',						type='ROUGHNESS',	color=(0, 0, 0, 1),	relink = {'needed':True, 'b':ub.chs['rch'], 'n':ub.chs['ach']}),
	'anisotropic_rotation':		ub.BakeMode('',						type='ROUGHNESS',	color=(0, 0, 0, 1),	relink = {'needed':True, 'b':ub.chs['rch'], 'n':ub.chs['arch']}),
	'sheen':					ub.BakeMode('',						type='ROUGHNESS',	color=(0, 0, 0, 1),	relink = {'needed':True, 'b':ub.chs['rch'], 'n':ub.chs['shch']}),
	'sheen_tint':				ub.BakeMode('',						type='EMIT',		color=(0, 0, 0, 1),	relink = {'needed':True, 'b':ub.chs['ech'], 'n':ub.chs['shtch']}),
	'clearcoat':				ub.BakeMode('',						type='ROUGHNESS',	color=(0, 0, 0, 1),	relink = {'needed':True, 'b':ub.chs['rch'], 'n':ub.chs['cch']}),
	'clearcoat_roughness':		ub.BakeMode('',						type='ROUGHNESS',	color=(0, 0, 0, 1),	relink = {'needed':True, 'b':ub.chs['rch'], 'n':ub.chs['crch']}),
	'transmission':				ub.BakeMode('',						type='TRANSMISSION'),
	'transmission_roughness':	ub.BakeMode('',						type='ROUGHNESS',	color=(0, 0, 0, 1),	relink = {'needed':True, 'b':ub.chs['rch'], 'n':ub.chs['trch']}),
	'emission':					ub.BakeMode('',						type='EMIT',		color=(0, 0, 0, 1)),
	'environment':				ub.BakeMode('',						type='ENVIRONMENT'),
	'uv':						ub.BakeMode('',						type='UV'),
	'shadow':					ub.BakeMode('',						type='SHADOW',		params=["bake_samples"]),
	'combined':					ub.BakeMode('',						type='COMBINED',	params=["bake_samples"])
}

if settings.bversion >= 2.91:
	modes['emission_strength']= ub.BakeMode('',						type='ROUGHNESS',	color=(0, 0, 0, 1),	relink = {'needed':True, 'b':ub.chs['rch'], 'n':ub.chs['esch']})
	modes['alpha']= 			ub.BakeMode('',						type='ROUGHNESS',	color=(0, 0, 0, 1), relink = {'needed':True, 'b':ub.chs['rch'], 'n':ub.chs['alch']})
else:
	modes['alpha']= 			ub.BakeMode('',						type='ROUGHNESS',	color=(0, 0, 0, 1), relink = {'needed':True, 'b':ub.chs['rch'], 'n':ub.chs['esch']})



class op(bpy.types.Operator):
	bl_idname = "uv.textools_bake"
	bl_label = "Bake"
	bl_description = "Bake selected objects"

	@classmethod
	def poll(cls, context):

		if len(settings.sets) == 0:
			settings.bake_error = ""
			return False
		
		bake_mode = utilities_ui.get_bake_mode()
		if bake_mode not in modes:
			settings.bake_error = ""
			return False
		
		if bake_mode in {'ao','normal_tangent','normal_object','curvature','environment','uv','shadow'}:
			settings.bake_error = ""
			return True

		if bake_mode == 'combined':
			if (not bpy.context.scene.render.bake.use_pass_direct) and (not bpy.context.scene.render.bake.use_pass_indirect) and (not bpy.context.scene.render.bake.use_pass_emit):
				settings.bake_error = "Lighting or Emit needed"
				return False
			settings.bake_error = ""
			return True
		
		if modes[bake_mode].setVColor or not modes[bake_mode].material:
			def is_bakeable(obj):
				if len(obj.data.materials) <= 0:	# There are no material slots
					settings.bake_error = "Materials needed"
					return False
				elif not any(obj.data.materials):	# All material slots are empty
					settings.bake_error = "Materials needed"
					return False
				else:
					for slot in obj.material_slots:
						if slot.material is not None:
							if slot.material.use_nodes == False:
								settings.bake_error = "Nodal materials needed"
								return False
							bsdf_node = None
							for n in slot.material.node_tree.nodes:
								if n.bl_idname == "ShaderNodeBsdfPrincipled":
									bsdf_node = n
							if not bsdf_node:
								bool_alpha_ignore = bpy.context.preferences.addons[__package__].preferences.bool_alpha_ignore
								bool_clean_transmission = bpy.context.preferences.addons[__package__].preferences.bool_clean_transmission
								builtin_modes_material = {'diffuse','emission','roughness','glossiness','transmission'}
								if modes[bake_mode].relink['needed'] or (bool_clean_transmission and bake_mode == 'transmission') or (bool_alpha_ignore and bake_mode not in builtin_modes_material):
									settings.bake_error = "BSDF nodes needed"
									return False
						# else:
						# 	settings.bake_error = "Materials needed"
						# 	return False
				settings.bake_error = ""
				return True

			def is_vc_ready(obj):
				if len(obj.data.vertex_colors) > 7:
					settings.bake_error = "An empty VC layer needed"
					return False
				settings.bake_error = ""
				return True

			for bset in settings.sets:
				if (len(bset.objects_high) + len(bset.objects_float)) == 0:
					if not modes[bake_mode].material:
						for obj in bset.objects_low:
							if not is_bakeable(obj):
								return False
					if modes[bake_mode].setVColor:
						for obj in bset.objects_low:
							if not is_vc_ready(obj):
								return False
				else:
					if not modes[bake_mode].material:
						for obj in (bset.objects_high + bset.objects_float):
							if not is_bakeable(obj):
								return False
					if modes[bake_mode].setVColor:
						for obj in (bset.objects_high + bset.objects_float):
							if not is_vc_ready(obj):
								return False

		settings.bake_error = ""
		return True

		
	def execute(self, context):
		startTime = time.monotonic()
		preferences = bpy.context.preferences.addons[__package__].preferences
		circular_report = [False, ]
		color_report = [False, ]

		if preferences.bool_clean_transmission:
			modes['transmission']=		ub.BakeMode('',			type='ROUGHNESS',	color=(0, 0, 0, 1),	relink = {'needed':True, 'b':7, 'n':15})
		else:
			modes['transmission']=		ub.BakeMode('',			type='TRANSMISSION')

		bake_mode = utilities_ui.get_bake_mode()

		if bake_mode not in modes:
			self.report({'ERROR_INVALID_INPUT'}, "Unknown mode '{}' only available: '{}'".format(bake_mode, ", ".join(modes.keys() )) )
			return {'CANCELLED'}

		# Store Selection
		selected_objects 	= [obj for obj in bpy.context.selected_objects]
		active_object 		= bpy.context.view_layer.objects.active
		pre_selection_mode = None
		if active_object:
			pre_selection_mode = bpy.context.active_object.mode
		ub.store_bake_settings()

		if preferences.bake_device != 'DEFAULT':
			bpy.context.scene.cycles.device = preferences.bake_device
		bpy.context.scene.render.engine = modes[bake_mode].engine	#Switch render engine

		# Avoid weird rendering problems when Progressive Refine is activated from Blender 2.90
		if settings.bversion < 3:
			bpy.context.scene.cycles.use_progressive_refine = False
		# Make it sure that an Image, and not a Vertex Colors layer, is the target of the bake
		if settings.bversion >= 2.92:
			bpy.context.scene.render.bake.target = 'IMAGE_TEXTURES'
		# Disable denoising until it is properly implemented for baking
		if settings.bversion >= 3:
			bpy.context.scene.cycles.use_denoising = False

		# Render sets
		bake(
			self = self, 
			mode = bake_mode,
			size = bpy.context.scene.texToolsSettings.size, 

			bake_force = bpy.context.scene.texToolsSettings.bake_force,
			sampling_scale = int(bpy.context.scene.texToolsSettings.bake_sampling),
			samples = bpy.context.scene.texToolsSettings.bake_samples,
			cage_extrusion = bpy.context.scene.texToolsSettings.bake_cage_extrusion,
			ray_distance = bpy.context.scene.texToolsSettings.bake_ray_distance,
			circular_report = circular_report,
			color_report = color_report,
			selected = selected_objects,
			active = active_object,
			pre_selection_mode = pre_selection_mode
		)

		elapsed = round(time.monotonic()-startTime, 2)
		if circular_report[0]:
			if color_report[0]:
				self.report({'WARNING'}, "Possible Circular Dependency: a previously baked image may have affected the new bake; " + color_report[0] + "Baking finished in " + str(elapsed) + "s.")
			else:
				self.report({'WARNING'}, "Possible Circular Dependency: a previously baked image may have affected the new bake. Baking finished in " + str(elapsed) + "s.")
		else:
			if color_report[0]:
				self.report({'WARNING'}, color_report[0] + ". Baking finished in " + str(elapsed) + "s.")
			else:
				self.report({'INFO'}, "Baking finished in " + str(elapsed) + "s.")

		return {'FINISHED'}



def bake(self, mode, size, bake_force, sampling_scale, samples, cage_extrusion, ray_distance, circular_report, color_report, selected, active, pre_selection_mode):
	print("Bake '{}'".format(mode))

	# Get the baking sets / pairs
	sets = settings.sets

	for bset in sets:
		# Requires 1+ low poly objects
		if len(bset.objects_low) == 0:
			self.report({'ERROR_INVALID_INPUT'}, "No low poly object as part of the '{}' set".format(bset.name) )
			return {'CANCELLED'}
		# Check for UV maps
		for obj in bset.objects_low:
			if (not obj.data.uv_layers) or len(obj.data.uv_layers) == 0:
				self.report({'ERROR_INVALID_INPUT'}, "No UV map available for '{}'".format(obj.name))
				return {'CANCELLED'}
		# Check for cage inconsistencies
		if len(bset.objects_cage) > 0 and (len(bset.objects_low) != len(bset.objects_cage)):
			self.report({'ERROR_INVALID_INPUT'}, "{}x cage objects do not match {}x low poly objects for '{}'".format(len(bset.objects_cage), len(bset.objects_low), obj.name))
			return {'CANCELLED'}

	# Disable edit mode
	if bpy.context.view_layer.objects.active != None and bpy.context.object.mode != 'OBJECT':
		bpy.ops.object.mode_set(mode='OBJECT')

	bool_emission_strength_ignore = bpy.context.preferences.addons[__package__].preferences.bool_emission_ignore
	bool_alpha_ignore = bpy.context.preferences.addons[__package__].preferences.bool_alpha_ignore
	render_width = sampling_scale * size[0]
	render_height = sampling_scale * size[1]


	# Get custom materials
	material_loaded = get_material(mode)

	# Setup properties of the custom material_loaded
	if material_loaded is not None:
		setup_material_loaded(mode, material_loaded)


	# If baking Material ID, make sure the color for each material is consistent between bakes
	if mode == 'id_material':
		# Try to redirect deleted materials which were recovered with undo 
		if len(ub.allMaterials) > 0 :
			for i, mtl in enumerate(ub.allMaterials):
				try: mtl.name
				except:	ub.allMaterials[i] = bpy.data.materials.get(ub.allMaterialsNames[i])
		else:	# Store a persistent ordered list of all originally used materials in the scene
			ub.allMaterials = [mtl for mtl in bpy.data.materials if (mtl is not None and mtl.users != 0)]
			ub.allMaterialsNames = [mtl.name for mtl in ub.allMaterials]

	# If baking Element ID, make sure the color for each element is consistent between bakes
	if mode == 'id_element':
		ub.elementsCount = 0

	# Create dictionaries to remember original and temporary -copied- materials used in the baked objects
	previous_materials = {}
	copied_materials = {}
	# Container to save existing UDIM tile names of each set
	tiles = []

	for bset in sets:
		for obj in (bset.objects_low + bset.objects_high + bset.objects_float):
			if obj not in previous_materials:
				previous_materials[obj] = []
				for i, mtl in enumerate(obj.data.materials):
					if mtl is None:
						previous_materials[obj].append(None)
					else:
						previous_materials[obj].append(obj.data.materials[i].name)

	# Substitute original materials for copied ones to avoid restoral after tuning
	def use_copied_mtls(obj):
		for i, mtl in enumerate(obj.data.materials):
			if mtl is not None:
				if mtl not in copied_materials:
					mat_copied = mtl.copy()
					obj.data.materials[i] = mat_copied
					copied_materials[mtl.name] = mat_copied.name
				else:
					obj.data.materials[i] = copied_materials[mtl.name]

	def use_material_loaded(obj):
		if len(obj.data.materials) > 0:
			for i in range(len(obj.data.materials)):
				obj.data.materials[i] = bpy.data.materials[material_loaded]
		else:
			obj.data.materials.append(bpy.data.materials[material_loaded])

	for bset in settings.sets:
		if (len(bset.objects_high) + len(bset.objects_float)) == 0:
			tiles.append( utilities_uv.get_UDIM_tiles( bset.objects_low ) )
			for obj in bset.objects_low:
				if material_loaded is None:
					use_copied_mtls(obj)
				else:
					use_material_loaded(obj)
		else:
			tiles.append( utilities_uv.get_UDIM_tiles( bset.objects_high + bset.objects_float ) )
			if material_loaded is None:
				for obj in (bset.objects_low + bset.objects_high + bset.objects_float):
					use_copied_mtls(obj)
			else:
				for obj in bset.objects_low:
					use_copied_mtls(obj)
				for obj in (bset.objects_high+bset.objects_float):
					use_material_loaded(obj)


	relinkedMaterials = []
	EmissionIgnoredMaterials = []
	AlphaIgnoredMaterials = []

	bakeReadyMaterials = []	# Store references of materials where the baking image node is ready and an Avoid Circular Dependency action has been taken
	image = previous_image = imagecopy = None	# Store image references globally just in case they have to be used to bake all sets
	stored_images = []	# [image, previous_image, imagecopy] list of lists


	try:
		for s,bset in enumerate(sets):

			# Get image name
			name_texture = "{}_{}".format(bset.name, mode)
			if bake_force == "Single":
				name_texture = "{}_{}".format(sets[0].name, mode)	# In Single mode, bake into the same texture
			#path = bpy.path.abspath("//{}.tga".format(name_texture))

			is_clear = (not bake_force == "Single") or (bake_force == "Single" and s==0)

			# Setup "image" to bake on and retrieve "previous_image": an image that exists in the blend file with the same name than "image", maybe used in materials involved in the bake
			if is_clear:
				bakeReadyMaterials = []
				loaded = True
				if material_loaded is None:
					loaded = False

				image, previous_image = setup_image(color_report, mode, name_texture, render_width, render_height, tiles[s], material_load=loaded)

				# Avoid Circular Dependency method A: Create image copy to use in existing nodes that may be affected if baking directly in a "previous_image" whose source is an external file
				if image == previous_image:
					imagecopy = image.copy()
				else:
					imagecopy = None

				image_name = image.name

				if previous_image is None:
					previous_image_name = None
				else:
					previous_image_name = previous_image.name

				if imagecopy is None:
					imagecopy_name = None
				else:
					imagecopy_name = imagecopy.name

				stored_images.append([image_name, previous_image_name, imagecopy_name, name_texture])



			def assign_tune_materials(obj, setup_bake_nodes=False):

				if material_loaded is not None:
					# If baking ID Materials, update the persistent ordered list of all materials in the scene
					if mode == 'id_material':
						for mtlname in previous_materials[obj]:
							if mtlname is not None:
								if bpy.data.materials[mtlname] not in ub.allMaterials:
									ub.allMaterials.append(bpy.data.materials[mtlname])
									ub.allMaterialsNames.append(mtlname)
					if modes[mode].setVColor:
						ub.assign_vertex_color(obj)
						if mode == 'id_material':
							modes[mode].setVColor(obj, previous_materials)
						else:
							modes[mode].setVColor(obj)
				
				elif modes[mode].relink['needed']:
					for slot in obj.material_slots:
						if slot.material:
							if slot.material not in relinkedMaterials:
								relink_nodes(mode, slot.material)
								relinkedMaterials.append(slot.material)
							if modes[mode].type == 'EMIT' and settings.bversion >= 2.91:
								if slot.material not in EmissionIgnoredMaterials:
									channel_ignore(modes['emission_strength'].relink['n'], slot.material)
									EmissionIgnoredMaterials.append(slot.material)
							if (bool_alpha_ignore and mode != 'ao' and mode != 'diffuse') or mode == 'alpha':
								if slot.material not in AlphaIgnoredMaterials:
									channel_ignore(modes['alpha'].relink['n'], slot.material)
									AlphaIgnoredMaterials.append(slot.material)
					if setup_bake_nodes:
						setup_image_bake_node(obj, bakeReadyMaterials, image_name, previous_image_name, imagecopy_name)
				
				elif bool_emission_strength_ignore and settings.bversion >= 2.91 and mode == 'emission':
					for slot in obj.material_slots:
						if slot.material:
							if slot.material.use_nodes:
								bsdf_node = None
								for n in slot.material.node_tree.nodes:
									if n.bl_idname == "ShaderNodeBsdfPrincipled":
										bsdf_node = n
								if bsdf_node:
									if slot.material not in EmissionIgnoredMaterials:
										channel_ignore(modes['emission_strength'].relink['n'], slot.material)
										EmissionIgnoredMaterials.append(slot.material)
									if (bool_alpha_ignore and mode != 'ao' and mode != 'diffuse') or mode == 'alpha':
										if slot.material not in AlphaIgnoredMaterials:
											channel_ignore(modes['alpha'].relink['n'], slot.material)
											AlphaIgnoredMaterials.append(slot.material)
					if setup_bake_nodes:
						setup_image_bake_node(obj, bakeReadyMaterials, image_name, previous_image_name, imagecopy_name)
				
				else:
					if (bool_alpha_ignore and mode != 'ao' and mode != 'diffuse') or mode == 'alpha':
						for slot in obj.material_slots:
							if slot.material:
								if slot.material.use_nodes:
									bsdf_node = None
									for n in slot.material.node_tree.nodes:
										if n.bl_idname == "ShaderNodeBsdfPrincipled":
											bsdf_node = n
									if bsdf_node:
										if slot.material not in AlphaIgnoredMaterials:
											channel_ignore(modes['alpha'].relink['n'], slot.material)
											AlphaIgnoredMaterials.append(slot.material)
					if setup_bake_nodes:
						setup_image_bake_node(obj, bakeReadyMaterials, image_name, previous_image_name, imagecopy_name)


			# Assign Materials to Objects / tune the existing materials, and distribute temp bake image nodes
			if (len(bset.objects_high) + len(bset.objects_float)) == 0:
				# Low poly bake: Assign material to lowpoly or tune the existing material/s
				for obj in bset.objects_low:
					if mode in {'ao','normal_tangent','normal_object','curvature','environment','uv','shadow','combined'}:
						# Clean unused material slots?
						# if len(obj.data.materials) > 0:
						# 	if not any(obj.data.materials):	# All material slots are empty
						# 		obj.active_material_index = 0
						# 		for i in range(len(obj.material_slots)):
						# 			bpy.ops.object.material_slot_remove({'object': obj})
						if len(obj.material_slots) == 0 or (not all(obj.data.materials)):
							if "TT_bake_node" not in bpy.data.materials:
								bpy.data.materials.new(name="TT_bake_node")
							if len(obj.material_slots) == 0:
								obj.data.materials.append(bpy.data.materials["TT_bake_node"])
							else:
								for slot in obj.material_slots:
									if not slot.material:
										slot.material = bpy.data.materials["TT_bake_node"]
					assign_tune_materials(obj, setup_bake_nodes=True)
				if material_loaded is not None :
					setup_image_bake_node(bset.objects_low[0], bakeReadyMaterials, image_name, previous_image_name, imagecopy_name)
			else:
				# High to low poly: Low poly requires any material to bake into image
				for obj in bset.objects_low:
					if len(obj.material_slots) == 0 or (not all(obj.data.materials)):
						if "TT_bake_node" not in bpy.data.materials:
							bpy.data.materials.new(name="TT_bake_node")
						if len(obj.material_slots) == 0:
							obj.data.materials.append(bpy.data.materials["TT_bake_node"])
						else:
							for slot in obj.material_slots:
								if not slot.material:
									slot.material = bpy.data.materials["TT_bake_node"]
					setup_image_bake_node(obj, bakeReadyMaterials, image_name, previous_image_name, imagecopy_name)
				# Assign material to highpoly or tune the existing material/s
				for obj in (bset.objects_high+bset.objects_float):
					assign_tune_materials(obj)



			#print("Bake '{}' = {}".format(bset.name, path))
			print("Bake "+bset.name)

			# Hide all cage objects i nrender
			for obj_cage in bset.objects_cage:
				obj_cage.hide_render = True

			# Bake each low poly object in this set
			for i in range(len(bset.objects_low)):
				obj_low = bset.objects_low[i]
				obj_cage = None if i >= len(bset.objects_cage) else bset.objects_cage[i]

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
				# 		if area.ui_type == 'UV':
				# 			area.spaces[0].image = image
				# 	# bpy.data.screens['UV Editing'].areas[1].spaces[0].image = image
				# 	bpy.ops.object.mode_set(mode='OBJECT')

				if is_clear and i == 0:
					# Set background image (CYCLES & BLENDER_EEVEE)
					# for area in bpy.context.screen.areas:
					# 	if area.ui_type == 'UV':
					# 		area.spaces[0].image = bpy.data.images[image_name]
					# Invert background if final invert of the baked image is needed
					if modes[mode].invert:
						bpy.ops.image.invert(invert_r=True, invert_g=True, invert_b=True, invert_a=False)

				for obj_high in (bset.objects_high):
					obj_high.select_set( state = True, view_layer = None)
				
				cycles_bake(
					mode,
					bpy.context.scene.texToolsSettings.padding,
					sampling_scale,
					samples,
					cage_extrusion,
					ray_distance,
					len(bset.objects_high) > 0,
					obj_cage
				)

				# Bake Floaters separate bake
				if len(bset.objects_float) > 0:
					bpy.ops.object.select_all(action='DESELECT')
					for obj_high in (bset.objects_float):
						obj_high.select_set( state = True, view_layer = None)
					obj_low.select_set( state = True, view_layer = None)

					cycles_bake(
						mode,
						0,
						sampling_scale,
						samples,
						cage_extrusion,
						ray_distance,
						len(bset.objects_float) > 0,
						obj_cage
					)

			# Restore renderable for cage objects
			for obj_cage in bset.objects_cage:
				obj_cage.hide_render = False

			# Operations to be made only after the bake is -or the bakes are- finished
			if (not bake_force == "Single") or (bake_force == "Single" and s == len(sets)-1):
				if modes[mode].invert:
					bpy.ops.image.invert(invert_r=True, invert_g=True, invert_b=True, invert_a=False)
				if render_width != size[0] or render_height != size[1]:
					bpy.data.images[image_name].scale(size[0],size[1])

				if modes[mode].composite:
					apply_composite(image_name, modes[mode].composite, bpy.context.scene.texToolsSettings.bake_curvature_size)


			# TODO: if autosave: image.save()


	finally:
		# Restore materials whether or not there is a problem during the baking
		for obj in previous_materials:
			if len(previous_materials[obj]) == 0:
				if len(obj.material_slots) > 0:
					obj.active_material_index = 0
					context_override = {'object': obj}
					for i in range(len(obj.material_slots)):
						with bpy.context.temp_override(**context_override):
							bpy.ops.object.material_slot_remove()
			else:
				for i, mtlname in enumerate(previous_materials[obj]):
					if mtlname is None:
						obj.data.materials[i] = None
					else:
						obj.data.materials[i] = bpy.data.materials[mtlname]

			if material_loaded is not None:
				if modes[mode].setVColor:
					vclsNames = [vcl.name for vcl in obj.data.vertex_colors]
					if 'TexTools_temp' in vclsNames :
						obj.data.vertex_colors.remove(obj.data.vertex_colors['TexTools_temp'])


		for mtl in copied_materials.values():
			bpy.data.materials.remove(bpy.data.materials[mtl], do_unlink=True)

		if "TT_bake_node" in bpy.data.materials:
			bpy.data.materials.remove(bpy.data.materials["TT_bake_node"], do_unlink=True)

		if material_loaded is not None:
			bpy.data.materials.remove(bpy.data.materials[material_loaded], do_unlink=True)


		for images in stored_images:
			if images[1] and images[1] in bpy.data.images and bpy.data.images[images[0]] != bpy.data.images[images[1]]:
				# If Avoid Circular Dependency method B was used, change previous_image for the newly baked image in all materials
				#bpy.data.images[images[1]].user_remap(bpy.data.images[images[0]])
				for material in bpy.data.materials:
					if material.use_nodes == True:
						tree = material.node_tree
						for node in tree.nodes:
							if node.bl_idname == 'ShaderNodeTexImage':
								if node.image == bpy.data.images[images[1]]:
									if material in copied_materials:
										circular_report[0] = True
									node.image = bpy.data.images[images[0]]

			# Force previous or temporary images to be removed (user related errors may be prompted in console, but the process should be stable)
			if images[2] and images[2] in bpy.data.images:
				#bpy.data.images[images[2]].user_clear()
				#bpy.data.batch_remove([bpy.data.images[images[2]]])
				bpy.data.images.remove(bpy.data.images[images[2]], do_unlink=True)	# Delete imagecopy
			elif images[1] and images[1] in bpy.data.images:
				#bpy.data.images[images[1]].user_clear()
				#bpy.data.batch_remove([bpy.data.images[images[1]]])
				bpy.data.images.remove(bpy.data.images[images[1]], do_unlink=True)	# Delete previous_image

			# If Avoid Circular Dependency method A was used, clear users of the saved image and recover them for the newly baked image (they share the ID but are not the same)
			if images[2]:
				circular_report[0] = True
				bpy.data.images[images[0]].user_clear()
				for material in bpy.data.materials:
					if material.use_nodes == True:
						tree = material.node_tree
						for node in tree.nodes:
							if node.bl_idname == 'ShaderNodeTexImage':
								if node.image.name == images[0]:
									node.image = bpy.data.images[images[0]]

			# Always set proper name to the newly baked image (when all previous or temporary images have been removed)
			bpy.data.images[images[0]].name = images[3]


		# Restore settings and selection mode
		ub.restore_bake_settings()
		bpy.ops.object.select_all(action='DESELECT')
		for obj in selected:
			obj.select_set( state = True, view_layer = None)
		# Enter and exit Edit Mode to force set a real vertex colors layer as active
		bpy.ops.object.mode_set(mode='EDIT')
		bpy.ops.object.mode_set(mode='OBJECT')
		if active:
			bpy.context.view_layer.objects.active = active
			bpy.ops.object.mode_set(mode=pre_selection_mode)




def apply_composite(image_name, scene_name, size):
	image = bpy.data.images[image_name]
	previous_scene = bpy.context.window.scene
	# avoid Sun Position addon error
	preWorldPropertiesNodesBool = previous_scene.world.use_nodes

	# Get Scene with compositing nodes
	scene = None
	if scene_name in bpy.data.scenes:
		scene = bpy.data.scenes[scene_name]
	else:
		path = os.path.join(os.path.dirname(__file__), "resources/compositing.blend", "Scene")
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



def setup_image(color_report, mode, name, width, height, tiles, material_load=False):
	preferences = bpy.context.preferences.addons[__package__].preferences

	if preferences.bool_bake_back_color == 'CUSTOM':
		bake_back_color = bpy.context.scene.texToolsSettings.bake_back_color
	else:
		bake_back_color = modes[mode].color

	def set_color_space(color_report, image):
		image.alpha_mode = 'NONE'
		try:
			image.colorspace_settings.name = bpy.context.scene.texToolsSettings.bake_color_space
		except:
			try:
				if bpy.context.scene.texToolsSettings.bake_color_space == 'Utility - Linear - sRGB':
					bpy.context.scene.texToolsSettings.bake_color_space = 'Non-Color'
					color_report[0] = "ACES Color Space type is not available"
				elif bpy.context.scene.texToolsSettings.bake_color_space == 'Utility - sRGB - Texture':
					bpy.context.scene.texToolsSettings.bake_color_space = 'sRGB'
					color_report[0] = "ACES Color Space type is not available"
				elif bpy.context.scene.texToolsSettings.bake_color_space == 'Non-Color':
					bpy.context.scene.texToolsSettings.bake_color_space = 'Utility - Linear - sRGB'
					color_report[0] = "Standard RGB Color Space type is not available"
				elif bpy.context.scene.texToolsSettings.bake_color_space == 'sRGB':
					bpy.context.scene.texToolsSettings.bake_color_space = 'Utility - sRGB - Texture'
					color_report[0] = "Standard RGB Color Space type is not available"
				image.colorspace_settings.name = bpy.context.scene.texToolsSettings.bake_color_space
			except:
				color_report[0] = "No one of the known Color Space types is available"
				return None

	def resize(image):
		if image.size[0] != width or image.size[1] != height or image.generated_width != width or image.generated_height != height:
			image.scale(width, height)

	def set_image_as_background(image):
		for area in bpy.context.screen.areas:
			if area.ui_type == 'UV':
				area.spaces[0].image = bpy.data.images[image.name]

	def apply_color(image):
		# Set background color to a small version of the image for performance
		image.pixels = [pv for p in range(4) for pv in bake_back_color]
		# Set final size of the image
		resize(image)

	def image_create():
		is_float_32 = preferences.bake_32bit_float == '32'

		if tiles and settings.bversion >= 3.2:
			# Create a full size new tiled image with alpha background
			image = bpy.data.images.new(name, width=width, height=height, alpha=True, float_buffer=is_float_32, tiled=True)
		else:
			# Create a small new image
			image = bpy.data.images.new(name, width=2, height=2, alpha=True, float_buffer=is_float_32, tiled=False)

		set_image_as_background(image)
		set_color_space(color_report, image)

		if tiles and settings.bversion >= 3.2:
			image.tiles.get(1001).generated_color = bake_back_color
			for tile in tiles:
				bpy.ops.image.tile_add(number=tile, count=1, label="", fill=True, width=width, height=height, float=is_float_32, alpha=True, color=bake_back_color)
			image.tiles.active_index = 0
		else:
			apply_color(image)

		#TODO revisit this if image save is implemented
		#image.file_format = 'TARGA'
		return image


	if name in bpy.data.images:
		previous_image = bpy.data.images[name]
		if previous_image.source == 'FILE':
			# Clear image if it was deleted or moved outside
			print("Existing image expected path "+bpy.path.abspath(previous_image.filepath))
			if not os.path.isfile(bpy.path.abspath(previous_image.filepath)):
				print("Unlinking missing image "+name)
				image = image_create()
				if material_load:
					return image, None			# Not possible Circular Dependency
				return image, previous_image	# Avoid Circular Dependency: use method B
			else:
				set_image_as_background(previous_image)
				set_color_space(color_report, previous_image)
				if settings.bversion < 3.2 or not tiles:
					previous_image.scale(2, 2)
					apply_color(previous_image)
				if material_load:
					return previous_image, None			# Not possible Circular Dependency
				return previous_image, previous_image	# Avoid Circular Dependency: use method A
		else:
			if material_load:
				set_image_as_background(previous_image)
				set_color_space(color_report, previous_image)
				if settings.bversion < 3.2 or not tiles:
					previous_image.scale(2, 2)
					apply_color(previous_image)
				return previous_image, None		# Not possible Circular Dependency
			image = image_create()
			return image, previous_image		# Avoid Circular Dependency: use method B
	else:
		image = image_create()
		return image, None						# Not possible Circular Dependency



def setup_image_bake_node(obj, bakeReadyMaterials, image_name, previous_image_name, imagecopy_name):
	image = bpy.data.images[image_name]
	if previous_image_name:
		previous_image = bpy.data.images[previous_image_name]
	else:
		previous_image = None
	if imagecopy_name:
		imagecopy = bpy.data.images[imagecopy_name]
	else:
		imagecopy = None

	if len(obj.data.materials) <= 0:
		print("ERROR, need spare material to setup active image texture to bake!!!")

	else:
		def avoid_circular(tree, image):
			# Avoid Circular Dependency method A
			for node in tree.nodes:
				if node.bl_idname == 'ShaderNodeTexImage':
					if node.image == image:
						node.image = imagecopy

		def assign_node(tree):
			# Assign bake node
			node = None
			if "TexTools_bake" in tree.nodes:
				node = tree.nodes["TexTools_bake"]
			else:
				node = tree.nodes.new("ShaderNodeTexImage")
				node.name = "TexTools_bake"
			node.select = True
			node.image = image
			tree.nodes.active = node

		for slot in obj.material_slots:
			if slot.material:
				if slot.material.name not in bakeReadyMaterials:
					if image == previous_image:
						if slot.material.use_nodes == False:
							# No need to Avoid Circular Dependency
							slot.material.use_nodes = True
							assign_node(slot.material.node_tree)
						else:
							# Use Avoid Circular Dependency method A to preserve external linking of the existing previous_image
							avoid_circular(slot.material.node_tree, image)
							assign_node(slot.material.node_tree)
					else:
						# Avoid Circular Dependency method B is used just by not baking directly on the existing previous_image
						if slot.material.use_nodes == False:
							slot.material.use_nodes = True
						assign_node(slot.material.node_tree)
					
					bakeReadyMaterials.append(slot.material.name)



def relink_nodes(mode, material):
	if material.use_nodes == False:
		material.use_nodes = True
	tree = material.node_tree
	bsdf_node = None
	for n in tree.nodes:
		if n.bl_idname == "ShaderNodeBsdfPrincipled":
			bsdf_node = n

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
			pass
		else:
			bsdf_node.inputs[b].default_value = bsdf_node.inputs[n].default_value
			tree.links.new(new_node.outputs[new_node_socket], bsdf_node.inputs[b])
	else:
		if base_node:
			tree.links.remove(bsdf_node.inputs[b].links[0])
		bsdf_node.inputs[b].default_value = bsdf_node.inputs[n].default_value



def channel_ignore(channel, material):
	if material.use_nodes == False:
		material.use_nodes = True
	tree = material.node_tree
	bsdf_node = None
	for n in tree.nodes:
		if n.bl_idname == "ShaderNodeBsdfPrincipled":
			bsdf_node = n

	if len(bsdf_node.inputs[channel].links) != 0 :
		tree.links.remove(bsdf_node.inputs[channel].links[0])
	
	# So far, Channels whose effect on others is wanted to be ignored have to be set equal to 1.0
	bsdf_node.inputs[channel].default_value = 1.0



def setup_material_loaded(mode, name):
	material_bake = bpy.data.materials[name]
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
	if mode == 'thickness':
		if "ao" in material_bake.node_tree.nodes:
			material_bake.node_tree.nodes["ao"].samples = bpy.context.scene.texToolsSettings.bake_samples
			material_bake.node_tree.nodes["ao"].only_local = bpy.context.scene.texToolsSettings.bake_thickness_local
		if "Distance" in material_bake.node_tree.nodes:
			material_bake.node_tree.nodes["Distance"].outputs[0].default_value = bpy.context.scene.texToolsSettings.bake_thickness_distance
		if "Contrast" in material_bake.node_tree.nodes:
			material_bake.node_tree.nodes["Contrast"].outputs[0].default_value = bpy.context.scene.texToolsSettings.bake_thickness_contrast



def get_material(mode):
	if modes[mode].material == "":
		return None	# No material setup required

	# Find or load material
	name = modes[mode].material
	path = os.path.join(os.path.dirname(__file__), "resources/materials.blend", "Material")
	if "bevel" in mode or "thickness" in mode:
		path = os.path.join(os.path.dirname(__file__), "resources/materials_2.80.blend", "Material")
	#print("Get material {}\n{}".format(mode, path))

	if bpy.data.materials.get(name) is None:
		#print("Material not yet loaded: "+mode)
		bpy.ops.wm.append(filename=name, directory=path, link=False, autoselect=False)

	return name



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
		if modes[mode].type in {'EMIT', 'DIFFUSE', 'ROUGHNESS', 'TRANSMISSION', 'ENVIRONMENT', 'UV'} and mode != 'thickness':
			bpy.context.scene.cycles.samples = 1

		# Pixel Padding
		bpy.context.scene.render.bake.margin = padding * sampling_scale

		# Disable Direct and Indirect for all 'DIFFUSE' bake types
		if modes[mode].type == 'DIFFUSE':
			bpy.context.scene.render.bake.use_pass_direct = False
			bpy.context.scene.render.bake.use_pass_indirect = False
			bpy.context.scene.render.bake.use_pass_color = True
		
		if settings.bversion < 2.90:
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
