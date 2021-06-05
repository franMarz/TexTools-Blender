import bpy
import bmesh
import operator
from mathutils import Vector
from collections import defaultdict
from math import pi

from . import utilities_color

class op(bpy.types.Operator):
	bl_idname = "uv.textools_color_clear"
	bl_label = "Clear Colors"
	bl_description = "Clears the Color IDs and materials on the selected model"
	bl_options = {'REGISTER', 'UNDO'}
	

	@classmethod
	def poll(cls, context):
		if not bpy.context.active_object:
			return False

		if bpy.context.active_object not in bpy.context.selected_objects:
			return False

		if bpy.context.active_object.type != 'MESH':
			return False

		#Only in UV editor mode
		if bpy.context.area.type != 'IMAGE_EDITOR':
			return False

		return True
	
	def execute(self, context):
		clear_colors(self, context)
		return {'FINISHED'}



def clear_colors(self, context):
	obj = bpy.context.active_object
	


	# Store previous mode
	previous_mode = bpy.context.active_object.mode
	if bpy.context.active_object.mode != 'EDIT':
		bpy.ops.object.mode_set(mode='EDIT')

	bm = bmesh.from_edit_mesh(bpy.context.active_object.data);

	# Set all faces
	for face in bm.faces:
		face.material_index = 0

	# Clear material slots
	bpy.ops.object.mode_set(mode='OBJECT')
	count = len(obj.material_slots)
	for i in range(count):
		bpy.ops.object.material_slot_remove()

	# Delete materials if not used
	for material in bpy.data.materials:
		if utilities_color.material_prefix in material.name:
			if material.users == 0:
				bpy.data.materials.remove(material, do_unlink=True)

	# Restore previous mode
	bpy.ops.object.mode_set(mode=previous_mode)


	for area in bpy.context.screen.areas:
		print("area: {}".format(area.type))
		if area.type == 'PROPERTIES':
			for space in area.spaces:
				if space.type == 'PROPERTIES':
					# space.shading.type = 'MATERIAL'
					space.context = 'MATERIAL'

	# Show Material Tab
	for area in bpy.context.screen.areas:
		if area.type == 'PROPERTIES':
			for space in area.spaces:
				if space.type == 'PROPERTIES':
					space.context = 'MATERIAL'

	# Switch Solid shading
	for area in bpy.context.screen.areas:
		if area.type == 'VIEW_3D':
			for space in area.spaces:
				if space.type == 'VIEW_3D':
					space.shading.type = 'SOLID'


bpy.utils.register_class(op)