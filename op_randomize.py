import bpy
import bmesh
import math
import random
import numpy as np

from mathutils import Vector
from . import utilities_uv



class op(bpy.types.Operator):
	bl_idname = "uv.textools_randomize"
	bl_label = "Randomize Position"
	bl_description = "Randomize UV Islands/Faces Position and/or Rotation"
	bl_options = {'REGISTER', 'UNDO'}
	
	bool_face: bpy.props.BoolProperty(name="Per Face", default=False)
	strengh_U: bpy.props.FloatProperty(name="U Strengh", default=1, min=-10, max=10, soft_min=0, soft_max=1)
	strengh_V: bpy.props.FloatProperty(name="V Strengh", default=1, min=-10, max=10, soft_min=0, soft_max=1)
	rotation: bpy.props.FloatProperty(name="Rotation Strengh", default=0, min=-10, max=10, soft_min=0, soft_max=1)
	bool_precenter: bpy.props.BoolProperty(name="Pre Center Faces/Islands", default=False, description="Collect all faces/islands around the center of the UV space.")
	bool_bounds: bpy.props.BoolProperty(name="Within Image Bounds", default=False, description="Keep the UV faces/islands within the 0-1 UV domain.")
	rand_seed: bpy.props.IntProperty(name="Seed", default=0)

	@classmethod
	def poll(cls, context):
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		if bpy.context.active_object.mode != 'EDIT':
			return False
		if bpy.context.area.type != 'IMAGE_EDITOR':
			return False
		if not bpy.context.object.data.uv_layers:
			return False
		if bpy.context.scene.tool_settings.use_uv_select_sync:
			return False
		return True


	def execute(self, context):
		if self.bool_bounds or self.bool_precenter:
			udim_tile, column, row = utilities_uv.get_UDIM_tile_coords(bpy.context.active_object)
		else:
			udim_tile = 1001
			column = row = 0
		utilities_uv.multi_object_loop(main, self, context, udim_tile=udim_tile, column=column, row=row, ob_num=0)
		return {'FINISHED'}

	def invoke(self, context, event):
		wm = context.window_manager
		return wm.invoke_props_dialog(self)



def main(self, context, udim_tile=1001, column=0, row=0, ob_num=0):
	me = bpy.context.active_object.data
	bm = bmesh.from_edit_mesh(me)
	uv_layers = bm.loops.layers.uv.verify()

	pregroup = utilities_uv.get_selected_uv_faces(bm, uv_layers)
	if not pregroup:
		return

	random.seed(self.rand_seed + ob_num)

	if not self.bool_face:
		group = utilities_uv.getSelectionIslands(bm, uv_layers, pregroup)	#list of sets
	else:
		group = pregroup	#list


	for f in group:
		rand_v = Vector(( 2*(random.random()-0.5), 2*(random.random()-0.5) ))
		rand_3 = 2*(random.random()-0.5)


		if self.bool_bounds or self.bool_precenter or self.rotation:
			if self.rotation:
				theta = self.rotation*rand_3*math.pi
				matrix = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
			else:
				matrix = np.array([[1, 0], [0, 1]])
			
			if not self.bool_face:
				vec_origin = utilities_uv.get_center(f, bm, uv_layers)
				if self.bool_bounds or self.bool_precenter:
					for i in f:
						for loop in i.loops:
							uvs0 = loop[uv_layers].uv - vec_origin
							loop[uv_layers].uv = (0.5 + matrix[0][0]*uvs0.x + matrix[0][1]*uvs0.y, 0.5 + matrix[1][0]*uvs0.x + matrix[1][1]*uvs0.y)
				else:
					for i in f:
						for loop in i.loops:
							uvs0 = loop[uv_layers].uv - vec_origin
							loop[uv_layers].uv = (vec_origin.x + matrix[0][0]*uvs0.x + matrix[0][1]*uvs0.y, vec_origin.y + matrix[1][0]*uvs0.x + matrix[1][1]*uvs0.y)
			else:
				vec_origin = utilities_uv.get_center(f.loops, bm, uv_layers, are_loops=True)
				if self.bool_bounds or self.bool_precenter:
					for loop in f.loops:
						uvs0 = loop[uv_layers].uv - vec_origin
						loop[uv_layers].uv = (0.5 + matrix[0][0]*uvs0.x + matrix[0][1]*uvs0.y, 0.5 + matrix[1][0]*uvs0.x + matrix[1][1]*uvs0.y)
				else:
					for loop in f.loops:
						uvs0 = loop[uv_layers].uv - vec_origin
						loop[uv_layers].uv = (vec_origin.x + matrix[0][0]*uvs0.x + matrix[0][1]*uvs0.y, vec_origin.y + matrix[1][0]*uvs0.x + matrix[1][1]*uvs0.y)
			
			bmesh.update_edit_mesh(me, False)


		if self.bool_bounds:
			boundsMin = Vector((99999999.0,99999999.0))
			boundsMax = Vector((-99999999.0,-99999999.0))

			if not self.bool_face:
				for i in f:
					for loop in i.loops:
						uv = loop[uv_layers].uv
						boundsMin = Vector(( max( min(boundsMin.x, uv.x), 0 ), max( min(boundsMin.y, uv.y), 0 ) ))
						boundsMax = Vector(( min( max(boundsMax.x, uv.x), 1 ), min( max(boundsMax.y, uv.y), 1 ) ))
			else:
				for loop in f.loops:
					uv = loop[uv_layers].uv
					boundsMin = Vector(( max( min(boundsMin.x, uv.x), 0 ), max( min(boundsMin.y, uv.y), 0 ) ))
					boundsMax = Vector(( min( max(boundsMax.x, uv.x), 1 ), min( max(boundsMax.y, uv.y), 1 ) ))
			
			move = Vector(( min(boundsMin.x, abs(1-boundsMax.x)) * max( min(self.strengh_U, 1), -1 ),  min(boundsMin.y, abs(1-boundsMax.y)) * max( min(self.strengh_V, 1), -1 ) ))
		else:
			move = Vector((self.strengh_U, self.strengh_V))


		if (not self.bool_bounds and not self.bool_precenter) or udim_tile == 1001:
			if move.x or move.y:
				if not self.bool_face:
					for i in f:
						for loop in i.loops:
							loop[uv_layers].uv += rand_v*move
				else:
					for loop in f.loops:
						loop[uv_layers].uv += rand_v*move
		else:
			if move.x or move.y:
				if not self.bool_face:
					for i in f:
						for loop in i.loops:
							loop[uv_layers].uv += rand_v*move + Vector((column, row))
				else:
					for loop in f.loops:
						loop[uv_layers].uv += rand_v*move + Vector((column, row))


bpy.utils.register_class(op)
