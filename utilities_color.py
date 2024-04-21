import bpy
import bmesh
from mathutils import Color
from .settings import tt_settings

material_prefix = "TT_color_"
gamma = 2.2


def assign_slot(obj, index):
	if index < len(obj.material_slots):
		obj.material_slots[index].material = get_material(index)
		assign_color(index)  # Verify color


def safe_color(color):
	if len(color) == 3:
		return *color, 1
	elif len(color) == 4:
		return color
	return color


def assign_color(index):
	material = get_material(index)
	if material:
		# material.use_nodes = False

		rgba = (*get_color(index), 1)
		engine_type = bpy.context.scene.render.engine

		if material.use_nodes and engine_type in ('CYCLES', 'BLENDER_EEVEE'):
			# Cycles material (Preferred for baking)
			for n in material.node_tree.nodes:
				if n.bl_idname == "ShaderNodeBsdfPrincipled":
					n.inputs[0].default_value = rgba
			material.diffuse_color = rgba

		elif engine_type == 'BLENDER_EEVEE' and not material.use_nodes:
			# Legacy render engine, not suited for baking
			material.diffuse_color = rgba


def get_material(index):
	name = get_name(index)

	# Material already exists?
	if name in bpy.data.materials:
		material = bpy.data.materials[name]

		# Check for incorrect materials for current render engine
		if not material:
			replace_material(index)

		engine_type = bpy.context.scene.render.engine
		if (not material.use_nodes) and engine_type == 'CYCLES':
			replace_material(index)

		elif engine_type == 'BLENDER_EEVEE' and material.use_nodes:
			replace_material(index)
		else:
			return material

	material = create_material(index)
	assign_color(index)
	return material


# Replace an existing material with a new one; this is sometimes necessary after switching the render engine
def replace_material(index):
	name = get_name(index)
	if name in bpy.data.materials:
		material = bpy.data.materials[name]

		# Collect material slots we have to re-assign
		slots = []
		for obj in bpy.context.view_layer.objects: 
			for slot in obj.material_slots:
				if slot.material == material:
					slots.append(slot)

		bpy.data.materials.remove(material, do_unlink=True)

		# Create and assign new material to all previous slots
		material = create_material(index)
		for slot in slots:
			slot.material = material


def create_material(index):
	name = get_name(index)
	material = bpy.data.materials.new(name)
	material.preview_render_type = 'FLAT'
	if bpy.context.scene.render.engine == 'CYCLES':
		material.use_nodes = True 

	return material


def get_name(index):
	return f"{material_prefix}{index:02d}"


def get_color(index):
	if index < tt_settings().color_ID_count:
		return getattr(tt_settings(), f"color_ID_color_{index}")
	return 0, 0, 0  # Default return (Black)


def set_color(index, color):
	if index < tt_settings().color_ID_count:
		setattr(tt_settings(), f"color_ID_color_{index}", color)


def validate_face_colors(obj):
	# Validate face colors and material slots
	previous_mode = bpy.context.object.mode
	count = tt_settings().color_ID_count

	# Verify enough material slots
	if len(obj.material_slots) < count:
		for i in range(count):
			if len(obj.material_slots) < count:
				bpy.ops.object.material_slot_add()
				assign_slot(obj, len(obj.material_slots)-1)
			else:
				break


	# TODO: Check face.material_index
	bpy.ops.object.mode_set(mode='EDIT')
	bm = bmesh.from_edit_mesh(obj.data)
	for face in bm.faces:
		face.material_index %= count
	obj.data.update()

	# Remove material slots that are not used
	if len(obj.material_slots) > count:
		bpy.ops.object.mode_set(mode='OBJECT')
		for i in range(len(obj.material_slots) - count):
			if len(obj.material_slots) > count:
				# Remove last
				bpy.context.object.active_material_index = len(obj.material_slots)-1
				bpy.ops.object.material_slot_remove()

	# Restore previous mode
	bpy.ops.object.mode_set(mode=previous_mode)


def hex_to_color(hex):
	hex = hex.strip('#')
	lv = len(hex)
	fin = list(int(hex[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
	r = pow(fin[0] / 255, gamma)
	g = pow(fin[1] / 255, gamma)
	b = pow(fin[2] / 255, gamma)
	fin.clear()
	fin.append(r)
	fin.append(g)
	fin.append(b)
	return tuple(fin)


def color_to_hex(color):
	rgb = []
	for i in range(3):
		rgb.append(pow(color[i], 1.0/gamma))

	r = int(rgb[0]*255)
	g = int(rgb[1]*255)
	b = int(rgb[2]*255)

	return f"#{r:02X}{g:02X}{b:02X}"



def get_color_id(index, count, jitter=False):
	# Get unique color
	color = Color()
	indexList = [0, 171, 64, 213, 32, 96, 160, 224, 16, 48, 80, 112, 144, 176, 208, 240, 8, 24, 40, 56, 72, 88, 104,
		120, 136, 152, 168, 184, 200, 216, 232, 248, 4, 12, 20, 28, 36, 44, 52, 60, 68, 76, 84, 92, 100, 108, 116, 124,
		132, 140, 148, 156, 164, 172, 180, 188, 196, 204, 212, 220, 228, 236, 244, 252, 2, 6, 10, 14, 18, 22, 26, 30, 34,
		38, 42, 46, 50, 54, 58, 62, 66, 70, 74, 78, 82, 86, 90, 94, 98, 102, 106, 110, 114, 118, 122, 126, 130, 134, 138,
		142, 146, 150, 154, 158, 162, 166, 170, 174, 178, 182, 186, 190, 194, 198, 202, 206, 210, 214, 218, 222, 226, 230,
		234, 238, 242, 246, 250, 254, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35, 37, 39, 41, 43,
		45, 47, 49, 51, 53, 55, 57, 59, 61, 63, 65, 67, 69, 71, 73, 75, 77, 79, 81, 83, 85, 87, 89, 91, 93, 95, 97, 99, 101,
		103, 105, 107, 109, 111, 113, 115, 117, 119, 121, 123, 125, 127, 129, 131, 133, 135, 137, 139, 141, 143, 145, 147,
		149, 151, 153, 155, 157, 159, 161, 163, 165, 167, 169, 128, 173, 175, 177, 179, 181, 183, 185, 187, 189, 191, 193,
		195, 197, 199, 201, 203, 205, 207, 209, 211, 192, 215, 217, 219, 221, 223, 225, 227, 229, 231, 233, 235, 237, 239,
		241, 243, 245, 247, 249, 251, 253, 255]

	i = 0
	if index > 255:
		while index > 255:
			index -= 256
			i += 1
	
	if jitter:
		color.hsv = ( ( indexList[index] + 1/(2**i) ) / 256 ), 0.9, 1.0
	else:
		color.hsv = ( index / (count) ), 0.9, 1.0
	
	return color


def update_properties_tab():
	for area in bpy.context.screen.areas:
		if area.type == 'PROPERTIES':
			for space in area.spaces:
				if space.type == 'PROPERTIES':
					if tt_settings().color_assign_mode == 'MATERIALS':
						space.context = 'MATERIAL'
					else:	#mode == VERTEXCOLORS
						space.context = 'DATA'


def update_view_mode():
	for area in bpy.context.screen.areas:
		if area.type == 'VIEW_3D':
			for space in area.spaces:
				if space.type == 'VIEW_3D':
					if space.shading.type == 'RENDERED':
						continue
					elif space.shading.type == 'MATERIAL' and tt_settings().color_assign_mode == 'MATERIALS':
						continue
					space.shading.type = 'SOLID'
					if tt_settings().color_assign_mode == 'MATERIALS':
						if space.shading.color_type != 'TEXTURE':
							space.shading.color_type = 'MATERIAL'
					else:	#mode == VERTEXCOLORS
						space.shading.color_type = 'VERTEX'
