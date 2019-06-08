import bpy
import bmesh
import operator
import time
from mathutils import Vector
from collections import defaultdict
from math import pi
from mathutils import Color

from . import settings


material_prefix = "TT_color_"
gamma = 2.2


def assign_slot(obj, index):
	if index < len(obj.material_slots):
		obj.material_slots[index].material = get_material(index)

		# Verify color
		assign_color(index)


def safe_color(color):
	if len(color) == 3:
		if bpy.app.version > (2, 80, 0):
			# Newer blender versions use RGBA
			return (color[0], color[1], color[2], 1)
		else:
			return color
	elif len(color) == 4:
		if bpy.app.version > (2, 80, 0):
			# Newer blender versions use RGBA
			return color
		else:
			return (color[0], color[1], color[2])

	return color


def assign_color(index):
	material = get_material(index)
	if material:
		# material.use_nodes = False
		
		rgb = get_color(index)
		rgba = (rgb[0], rgb[1], rgb[2], 1)

		if material.use_nodes and bpy.context.scene.render.engine == 'CYCLES' or material.use_nodes and bpy.context.scene.render.engine == 'BLENDER_EEVEE' :
			# Cycles material (Preferred for baking)
			material.node_tree.nodes["Principled BSDF"].inputs[0].default_value = rgba
			material.diffuse_color = rgba


		elif not material.use_nodes and bpy.context.scene.render.engine == 'BLENDER_EEVEE':
			# Legacy render engine, not suited for baking
			material.diffuse_color = rgba



def get_material(index):
	name = get_name(index)

	# Material already exists?
	if name in bpy.data.materials:
		material = bpy.data.materials[name];

		# Check for incorrect matreials for current render engine
		if not material:
			replace_material(index)

		if not material.use_nodes and bpy.context.scene.render.engine == 'CYCLES':
			replace_material(index)

		elif material.use_nodes and bpy.context.scene.render.engine == 'BLENDER_EEVEE':
			replace_material(index)

		else:
			return material;

	print("Could nt find {} , create a new one??".format(name))

	material = create_material(index)
	assign_color(index)
	return material



# Replaace an existing material with a new one
# This is sometimes necessary after switching the render engine
def replace_material(index):
	name = get_name(index)

	print("Replace material and create new")

	# Check if material exists
	if name in bpy.data.materials:
		material = bpy.data.materials[name];

		# Collect material slots we have to re-assign
		slots = []
		for obj in bpy.context.view_layer.objects: 
			for slot in obj.material_slots:
				if slot.material == material:
					slots.append(slot)

		# Get new material
		material.user_clear()
		bpy.data.materials.remove(material)
		
		# Re-assign new material to all previous slots
		material = create_material(index)
		for slot in slots:
			slot.material = material;



def create_material(index):
	name = get_name(index)

	# Create new image instead
	material = bpy.data.materials.new(name)
	material.preview_render_type = 'FLAT'

	if bpy.context.scene.render.engine == 'CYCLES':
		# Cycles: prefer nodes as it simplifies baking
		material.use_nodes = True 

	return material



def get_name(index):
	return (material_prefix+"{:02d}").format(index)



def get_color(index):
	if index < bpy.context.scene.texToolsSettings.color_ID_count:
		return getattr(bpy.context.scene.texToolsSettings, "color_ID_color_{}".format(index))

	# Default return (Black)
	return (0, 0, 0)



def set_color(index, color):
	if index < bpy.context.scene.texToolsSettings.color_ID_count:
		setattr(bpy.context.scene.texToolsSettings, "color_ID_color_{}".format(index), color)



def validate_face_colors(obj):
	# Validate face colors and material slots
	previous_mode = bpy.context.object.mode;
	count = bpy.context.scene.texToolsSettings.color_ID_count

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
	bm = bmesh.from_edit_mesh(obj.data);
	for face in bm.faces:
		face.material_index%= count
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
		rgb.append( pow(color[i] , 1.0/gamma) )

	r = int(rgb[0]*255)
	g = int(rgb[1]*255)
	b = int(rgb[2]*255)

	return "#{:02X}{:02X}{:02X}".format(r,g,b)



def get_color_id(index, count):
	# Get unique color
	color = Color()
	color.hsv = ( index / (count) ), 0.9, 1.0
	
	return color