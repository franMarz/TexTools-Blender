import bpy
import bmesh
import math
import re
import os

image_material_prefix = "TT_checker_"



def get_object_texture_image(obj):
	# Search in material & texture slots
	for slot_mat in obj.material_slots:
		if slot_mat.material:

			# Check for traditional texture slots in material
			for slot_tex in slot_mat.material.texture_paint_slots:
				if slot_tex and slot_tex.texture and hasattr(slot_tex.texture , 'image'):
					return slot_tex.texture.image

			# Check if material uses Nodes
			if hasattr(slot_mat.material , 'node_tree'):
				if slot_mat.material.node_tree:
					for node in slot_mat.material.node_tree.nodes:
						if type(node) is bpy.types.ShaderNodeTexImage:
							if node.image:
								return node.image
	return None



def image_resize(image, size_x, size_y):
	if image and image.source == 'FILE' or image.source == 'GENERATED':
		image.generated_width = int(size_x)
		image.generated_height = int(size_y)
		image.scale( int(size_x), int(size_y) )



def checker_images_cleanup():
	# Clean up unused images
	for image in bpy.data.images:
		if image and image_material_prefix in image.name:
			# Remove unused images
			if not image.users:
				bpy.data.images.remove(image, do_unlink=True)
				return

			# Check if name missmatches size
			name = get_checker_name(image.generated_type , image.size[0], image.size[1])
			if image.name != name:
				# In cycles find related material as well
				if image.name in bpy.data.materials:
					bpy.data.materials[image.name].name = name
				image.name = name

	for material in bpy.data.materials:
		if material and image_material_prefix in material.name:
			# Remove unused images
			if not material.users:
				bpy.data.materials.remove(material, do_unlink=True)



def get_checker_name(mode, size_x, size_y):
	return (image_material_prefix+"{1}x{2}_{0}").format(mode, size_x, size_y)



def get_area_triangle_uv(A,B,C, size_x, size_y):
	scale_x = size_x / max(size_x, size_y)
	scale_y = size_y / max(size_x, size_y)
	A.x/=scale_x
	B.x/=scale_x
	C.x/=scale_x
	
	A.y/=scale_y
	B.y/=scale_y
	C.y/=scale_y

	return get_area_triangle(A,B,C)


def get_area_triangle(A,B,C):
	# Heron's formula: http://www.1728.org/triang.htm
	# area = square root (s • (s - a) • (s - b) • (s - c))
	a = (B-A).length
	b = (C-B).length
	c = (A-C).length
	s = (a+b+c)/2

	# Use abs(s-a) for values that otherwise generate negative values e.g. pinched UV verts, otherwise math domain error
	return math.sqrt(s * abs(s-a) * abs(s-b) * abs(s-c))



stored_materials = {}
stored_material_faces = {}
def store_materials_clear():
	stored_materials.clear()
	stored_material_faces.clear()



def store_materials(obj):
	stored_materials[obj] = []
	stored_material_faces[obj] = []

	# Enter edit mode
	bpy.ops.object.select_all(action='DESELECT')
	obj.select_set( state = True, view_layer = None)
	bpy.context.view_layer.objects.active = obj

	bpy.ops.object.mode_set(mode='EDIT')
	bm = bmesh.from_edit_mesh(obj.data)

	# for each slot backup the material 
	for s in range(len(obj.material_slots)):
		slot = obj.material_slots[s]

		stored_materials[obj].append(slot.material)
		stored_material_faces[obj].append( [face.index for face in bm.faces if face.material_index == s] )

		if slot and slot.material:
			slot.material.name = "backup_"+slot.material.name
			slot.material.use_fake_user = True

	# Back to object mode
	bpy.ops.object.mode_set(mode='OBJECT')



def restore_materials(objs):
	if len(objs) == 0 :
		return
	else:
		for obj in objs :
			if stored_materials.get(obj) == None :
				bpy.ops.object.mode_set(mode='OBJECT')
				bpy.ops.object.select_all(action='DESELECT')
				obj.select_set( state = True, view_layer = None)
				bpy.context.view_layer.objects.active = obj
				count = len(obj.material_slots)
				for i in range(count):
					bpy.ops.object.material_slot_remove()
		objs = [obj for obj in objs if obj in stored_materials]

	for obj in objs :
		# Enter edit mode
		bpy.context.view_layer.objects.active = obj
		bpy.ops.object.mode_set(mode='EDIT')
		bm = bmesh.from_edit_mesh(obj.data)

		# Restore slots
		for index in range(len(stored_materials[obj])):
			material = stored_materials[obj][index]
			faces = stored_material_faces[obj][index]
			
			if material:
				material.name = material.name.replace("backup_","")
				obj.material_slots[index].material = material
				material.use_fake_user = False

				# Face material indexies
				for face in bm.faces:
					if face.index in faces:
						face.material_index = index

		# Back to object mode
		bpy.ops.object.mode_set(mode='OBJECT')

		# Remove material slots if none before
		if len(stored_materials[obj]) == 0 :
			for i in range(len(obj.material_slots)):
				bpy.ops.object.material_slot_remove()



def get_tile_size(self, image, udim_tile):
	tile_name = image.name+"."+str(udim_tile)+"."+image.file_format.lower()
	purge = False
	if tile_name not in bpy.data.images:
		base_image_location = bpy.path.abspath(image.filepath)
		base_tile = re.findall('\d{4}', base_image_location)[-1]
		image_location = base_image_location.replace(base_tile, str(udim_tile))
		if not os.path.isfile(image_location):
			self.report({'INFO'}, "Missing tile image "+tile_name)
			return 0
		else:
			bpy.data.images.load(image_location, check_existing=False)
			#bpy.ops.image.open(filepath=image_location, relative_path=False, use_udim_detecting=False)
			purge = True
	tile = bpy.data.images[tile_name]
	size = min(tile.size[0], tile.size[1])
	if purge:
		bpy.data.images.remove(tile, do_unlink=True)
	return size
