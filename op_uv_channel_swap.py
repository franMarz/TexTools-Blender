import bpy
import bmesh
import operator
from mathutils import Vector
from collections import defaultdict
from math import pi


class op(bpy.types.Operator):
	bl_idname = "uv.textools_uv_channel_swap"
	bl_label = "Move UV Channel"
	bl_description = "Move UV channel up or down"
	bl_options = {'REGISTER', 'UNDO'}

	is_down : bpy.props.BoolProperty(default=False)

	@classmethod
	def poll(cls, context):
		if bpy.context.active_object == None:
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		if len(bpy.context.object.data.uv_layers) <= 1:
			return False
		return True


	def execute(self, context):
		uv_layers = bpy.context.object.data.uv_layers

		if uv_layers.active_index == 0 and not self.is_down:
			return {'FINISHED'}
		elif uv_layers.active_index == len(uv_layers)-1 and self.is_down:
			return {'FINISHED'}

		def get_index(name):
			return ([i for i in range(len(uv_layers)) if uv_layers[i].name == name])[0]

		def move_bottom(name):
			# Set index
			uv_layers.active_index = get_index(name)
			# Copy (to bottom)
			bpy.ops.mesh.uv_texture_add()
			# Delete previous
			uv_layers.active_index = get_index(name)
			bpy.ops.mesh.uv_texture_remove()
			# Rename new
			uv_layers.active_index = len(uv_layers)-1
			uv_layers.active.name = name

		count = len(uv_layers)

		index_A = uv_layers.active_index
		index_B = index_A + (1 if self.is_down else -1)

		if not self.is_down:
			# Move up
			for n in [uv_layers[i].name for i in range(index_B, count) if i != index_A]:
				move_bottom(n)
			bpy.context.scene.texToolsSettings.uv_channel = str(index_B)

		elif self.is_down:
			# Move down
			for n in [uv_layers[i].name for i in range(index_A, count) if i != index_B]:
				move_bottom(n)
			bpy.context.scene.texToolsSettings.uv_channel = str(index_B)

		return {'FINISHED'}

bpy.utils.register_class(op)