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
	#Unneeded materials have to be deleted before unneeded images because images have them as users
	for material in bpy.data.materials:
		if material and image_material_prefix in material.name:
			if not material.users:
				bpy.data.materials.remove(material, do_unlink=True)

	for image in bpy.data.images:
		if image and image_material_prefix in image.name:
			if not image.users:
				bpy.data.images.remove(image, do_unlink=True)


def get_checker_name(mode, size_x, size_y):
	return f'{image_material_prefix}{size_x}x{size_y}_{mode}'


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
	obj.select_set(True)
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
	if len(objs) == 0:
		return
	else:
		for obj in objs:
			if stored_materials.get(obj) == None :
				bpy.ops.object.mode_set(mode='OBJECT')
				bpy.ops.object.select_all(action='DESELECT')
				obj.select_set(True)
				bpy.context.view_layer.objects.active = obj
				count = len(obj.material_slots)
				for i in range(count):
					bpy.ops.object.material_slot_remove()
		objs = [obj for obj in objs if obj in stored_materials]

	for obj in objs:
		# Enter edit mode
		bpy.context.view_layer.objects.active = obj
		bpy.ops.object.mode_set(mode='EDIT')
		bm = bmesh.from_edit_mesh(obj.data)

		# Restore slots
		for index in range(len(stored_materials[obj])):
			material = stored_materials[obj][index]
			faces = stored_material_faces[obj][index]
			
			if material:
				material.name = material.name.replace('backup_', '')
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
	tile_name = f"{image.name}.{udim_tile}.{image.file_format.lower()}"
	purge = False
	if tile_name not in bpy.data.images:
		base_image_location = bpy.path.abspath(image.filepath)
		base_tile = re.findall('\d{4}', base_image_location)[-1]
		image_location = base_image_location.replace(base_tile, str(udim_tile))
		if not os.path.isfile(image_location):
			self.report({'INFO'}, f"Missing tile image {tile_name}")
			return 0
		else:
			bpy.data.images.load(image_location, check_existing=False)
			#bpy.ops.image.open(filepath=image_location, relative_path=False, use_udim_detecting=False)
			purge = True

	tile = bpy.data.images[tile_name]
	size = min(*tile.size)
	if purge:
		#bpy.data.batch_remove([tile])
		bpy.data.images.remove(tile, do_unlink=True)

	return size
