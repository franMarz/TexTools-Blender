import bpy
import bmesh
import math

from . import utilities_color
from . import utilities_bake

material_prefix = "TT_atlas_"
gamma = 2.2


class op(bpy.types.Operator):
	bl_idname = "uv.textools_color_convert_to_texture"
	bl_label = "Pack Texture"
	bl_description = "Pack ID Colors into single texture and UVs"
	bl_options = {'REGISTER', 'UNDO'}
	

	@classmethod
	def poll(cls, context):
		if not bpy.context.active_object:
			return False

		if bpy.context.active_object not in bpy.context.selected_objects:
			return False

		if len(bpy.context.selected_objects) != 1:
			return False

		if bpy.context.active_object.type != 'MESH':
			return False

		#Only in UV editor mode
		if bpy.context.area.type != 'IMAGE_EDITOR':
			return False

		return True
	
	def execute(self, context):
		pack_texture(self, context)
		return {'FINISHED'}



def pack_texture(self, context):
	obj = bpy.context.active_object
	name = material_prefix+obj.name

	if obj.mode != 'OBJECT':
		bpy.ops.object.mode_set(mode='OBJECT')


	# Determine size
	size_pixel = 8
	size_square = math.ceil(math.sqrt( context.scene.texToolsSettings.color_ID_count ))
	size_image = size_square * size_pixel
	size_image_pow = int(math.pow(2, math.ceil(math.log(size_image, 2))))

	# Maximize pixel size
	size_pixel = math.floor(size_image_pow/size_square)

	print("{0} colors = {1} x {1} = ({2}pix)  {3} x {3}  | {4} x {4}".format(
		context.scene.texToolsSettings.color_ID_count, 
		size_square,
		size_pixel,
		size_image,
		size_image_pow
	))

	# Create image
	image = bpy.data.images.new(name, width=size_image_pow, height=size_image_pow)
	pixels = [None] * size_image_pow * size_image_pow

	# Black pixels
	for x in range(size_image_pow):
		for y in range(size_image_pow):
			pixels[(y * size_image_pow) + x] = [0, 0, 0, 1]

	# Pixels
	for c in range(context.scene.texToolsSettings.color_ID_count):
		x = c % size_square
		y = math.floor(c/size_square)
		color = utilities_color.get_color(c).copy()
		for i in range(3):
			color[i] = pow(color[i] , 1.0/gamma)

		for sx in range(size_pixel):
			for sy in range(size_pixel):
				_x = x*size_pixel + sx
				_y = y*size_pixel + sy
				pixels[(_y * size_image_pow) + _x] = [color[0], color[1], color[2], 1]


	# flatten list & assign pixels
	pixels = [chan for px in pixels for chan in px]
	image.pixels = pixels

	# Set background image
	for area in bpy.context.screen.areas:
		if area.type == 'IMAGE_EDITOR':
			area.spaces[0].image = image

	# Edit mesh
	bpy.ops.object.mode_set(mode='EDIT')
	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
	bpy.ops.mesh.select_all(action='SELECT')
	# bpy.ops.uv.smart_project(angle_limit=1)
	bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.0078)


	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()

	for face in bm.faces:
		index = face.material_index

		# Get UV coordinates for index
		x = index%size_square
		y = math.floor(index/size_square)

		x*= (size_pixel / size_image_pow) 
		y*= (size_pixel / size_image_pow)
		x+= size_pixel/size_image_pow/2
		y+= size_pixel/size_image_pow/2

		for loop in face.loops:
			loop[uv_layers].uv = (x, y)

	# Remove Slots & add one
	bpy.ops.object.mode_set(mode='OBJECT')
	bpy.ops.uv.textools_color_clear()
	bpy.ops.object.material_slot_add()
	
	#Create material with image
	obj.material_slots[0].material = utilities_bake.get_image_material(image)

	#Display UVs
	bpy.ops.object.mode_set(mode='EDIT')

	# Switch textured shading
	for area in bpy.context.screen.areas:
		if area.type == 'VIEW_3D':
			for space in area.spaces:
				if space.type == 'VIEW_3D':
					if space.shading.type == 'RENDERED':
						continue
					elif space.shading.type == 'MATERIAL':
						continue
					space.shading.type = 'SOLID'
					space.shading.color_type = 'TEXTURE'

	bpy.ops.ui.textools_popup('INVOKE_DEFAULT', message="Packed texture with {} color IDs".format( context.scene.texToolsSettings.color_ID_count ))


bpy.utils.register_class(op)
