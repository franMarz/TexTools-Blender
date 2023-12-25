import bpy
import os
import operator

from . import utilities_texel
from . import utilities_uv

texture_modes = ['UV_GRID','COLOR_GRID','GRAVITY','NONE']



class op(bpy.types.Operator):
	bl_idname = "uv.textools_texel_checker_map"
	bl_label = "Checker Map"
	bl_description = "Add a checker map to the selected model and UV view"
	bl_options = {'REGISTER', 'UNDO'}
	
	@classmethod
	def poll(cls, context):
		if bpy.context.area.ui_type != 'UV':
			return False
		if not bpy.context.active_object:
			return False
		if bpy.context.object.mode != 'EDIT' and bpy.context.object.mode != 'OBJECT':
			return False
		if bpy.context.object.mode == 'OBJECT' and len(bpy.context.selected_objects) == 0:
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		if not bpy.context.object.data.uv_layers:
			return False
		return True


	def execute(self, context):
		premode = bpy.context.active_object.mode
		utilities_uv.multi_object_loop(assign_checker_map, self, bpy.context.scene.texToolsSettings.size[0], bpy.context.scene.texToolsSettings.size[1])
		bpy.ops.object.mode_set(mode=premode)
		return {'FINISHED'}



def assign_checker_map(self, size_x, size_y):
	obj = bpy.context.active_object
	if obj.type != 'MESH' or not obj.data.uv_layers:
		return
	bpy.ops.object.mode_set(mode='OBJECT')

	#Change View mode to TEXTURED
	for area in bpy.context.screen.areas:
		if area.type == 'VIEW_3D':
			for space in area.spaces:
				if space.type == 'VIEW_3D':
					space.shading.type = 'MATERIAL'

	# Detect current Checker modes
	mode_count = {}
	for mode in texture_modes:
		mode_count[mode] = 0

	# Image sizes
	image_sizes_x = []
	image_sizes_y = []

	# Collect current modes in selected object
	image = utilities_texel.get_object_texture_image(obj)
	mode = 'NONE'
	if image:
		if "GRAVITY" in image.name.upper():
			mode = 'GRAVITY'

		elif image.generated_type in texture_modes:
			# Generated checker maps
			mode = image.generated_type

			# Track image sizes
			if image.size[0] not in image_sizes_x:
				image_sizes_x.append(image.size[0])
			if image.size[1] not in image_sizes_y:
				image_sizes_y.append(image.size[1])
	else:
		utilities_texel.store_materials(obj)

	mode_count[mode]+=1


	# Sort by count (returns tuple list of key,value)
	mode_max_count = sorted(mode_count.items(), key=operator.itemgetter(1))
	mode_max_count.reverse()

	# Determine next mode
	mode = 'NONE'
	if mode_max_count[0][1] == 0:
		# There are no maps
		mode = texture_modes[0]

	elif mode_max_count[0][0] in texture_modes:
		if mode_max_count[-1][1] > 0:
			# There is more than 0 of another mode, complete existing mode first
			mode = mode_max_count[0][0]
		else:
			# Switch to next checker mode
			index = texture_modes.index(mode_max_count[0][0])
			
			if texture_modes[ index ] != 'NONE' and len(image_sizes_x) > 1 or len(image_sizes_y) > 1:
				# There are multiple resolutions on selected objects
				mode = texture_modes[ index ]
			elif texture_modes[ index ] != 'NONE' and (len(image_sizes_x) > 0 and image_sizes_x[0] != size_x) and (len(image_sizes_y) > 0 and image_sizes_y[0] != size_y):
				# The selected objects have a different resolution
				mode = texture_modes[ index ]
			else:
				# Next mode
				mode = texture_modes[ (index+1)%len(texture_modes) ]

	# Apply checker maps
	if mode == 'UV_GRID':
		name = utilities_texel.get_checker_name(mode, size_x, size_y)
		image = get_image(name, mode, size_x, size_y)
		apply_image(obj, image)

	elif mode == 'GRAVITY':
		areaImages = []
		for area in bpy.context.screen.areas:
			if area.type == 'IMAGE_EDITOR':
				areaImages.append(area.spaces[0].image)

		image = load_image("checker_map_gravity")
		apply_image(obj, image)

		#Default behaviour of Blender when loading an external image is making it the background of the Image/UV Editor
		#Revert in all opened Image/UV editors
		areacount = 0
		for area in bpy.context.screen.areas:
			if area.type == 'IMAGE_EDITOR':
				area.spaces[0].image = areaImages[areacount]
				areacount += 1

	elif mode == 'NONE':
		utilities_texel.restore_materials([obj])

	else:
		name = utilities_texel.get_checker_name(mode, size_x, size_y)
		image = get_image(name, mode, size_x, size_y)
		apply_image(obj, image)
	
	# Clean up images and materials
	utilities_texel.checker_images_cleanup()

	# Force redraw of viewport to update texture
	bpy.context.view_layer.update()



def load_image(name):
	internalImageName = "TT_" + name

	# Image already exists?
	if internalImageName in bpy.data.images:
		return bpy.data.images[internalImageName]

	# Load new image instead
	pathTexture = os.path.join(os.path.dirname(__file__), "resources/{}.png".format(name))
	bpy.ops.image.open(filepath=pathTexture, relative_path=False)
	#remove extension in name
	if "{}.png".format(name) in bpy.data.images:
		bpy.data.images["{}.png".format(name)].name = internalImageName
		return bpy.data.images[internalImageName]



def apply_image(obj, image):

	bpy.ops.object.mode_set(mode='OBJECT')
	bpy.ops.object.select_all(action='DESELECT')
	obj.select_set( state = True, view_layer = None)
	bpy.context.view_layer.objects.active = obj

	# Assign Cycles material with image

	# Get Material
	material = None
	if image.name in bpy.data.materials:
		material = bpy.data.materials[image.name]
	else:
		material = bpy.data.materials.new(image.name)
		material.use_nodes = True

	# Assign material
	if obj.data.materials:
		for m in range(len(obj.data.materials)):
			obj.data.materials[m] = material
	else:
		obj.data.materials.append(material)

	#TODO: if the material exists, should the following be performed?
	# Setup Node
	tree = material.node_tree
	node = None
	if "checker" in tree.nodes:
		node = tree.nodes["checker"]
	else:
		node = tree.nodes.new("ShaderNodeTexImage")
	node.name = "checker"
	node.select = True
	tree.nodes.active = node
	node.image = image

	# Linking
	tree = obj.data.materials[0].node_tree
	links = tree.links
	node1 = tree.nodes['checker']
	#node2 = tree.nodes['Principled BSDF'] not working in recent versions of Blender for UIs in languages other than english
	node2 = None
	for n in tree.nodes:
		if n.bl_idname == "ShaderNodeBsdfPrincipled":
			node2 = n
	#The materials are cleaned up with each cycle, which makes the following unnecessary, but prior to a refactor of the script, make the comprobation just in case
	#Besides, the called function don't fail when node2 is null, but that could change in the future of the API
	if node2:	#TODO: else: raise error message, clean nodes in material?
		links.new(node1.outputs['Color'], node2.inputs['Base Color'])



def get_image(name, mode, size_x, size_y):
	# Image already exists?
	if name in bpy.data.images:
		# Update texture UV checker mode
		bpy.data.images[name].generated_type = mode
		return bpy.data.images[name]

	# Create new image instead
	image = bpy.data.images.new(name, width=size_x, height=size_y)
	image.generated_type = mode		#UV_GRID or COLOR_GRID
	image.generated_width = int(size_x)
	image.generated_height = int(size_y)
	return image


bpy.utils.register_class(op)
