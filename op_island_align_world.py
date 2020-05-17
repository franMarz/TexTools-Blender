import bpy
import os
import bmesh
import math
import operator

from mathutils import Vector
from collections import defaultdict
from itertools import chain # 'flattens' collection of iterables

from . import utilities_uv




class op(bpy.types.Operator):
	bl_idname = "uv.textools_island_align_world"
	bl_label = "Align World"
	bl_description = "Align selected UV islands to world / gravity directions"
	bl_options = {'REGISTER', 'UNDO'}

	# is_global = bpy.props.BoolProperty(
	# 	name = "Global Axis",
	# 	description = "Global or local object axis alignment",
	# 	default = False
	# )

	# def draw(self, context):
	# 	layout = self.layout
	# 	layout.prop(self, "is_global")

	@classmethod
	def poll(cls, context):
		if not bpy.context.active_object:
			return False

		#Only in Edit mode
		if bpy.context.active_object.mode != 'EDIT':
			return False

		#Requires UV map
		if not bpy.context.object.data.uv_layers:
			return False

		if bpy.context.scene.tool_settings.use_uv_select_sync:
			return False

		#Only in UV editor mode
		if bpy.context.area.type != 'IMAGE_EDITOR':
			return False

		return True


	def execute(self, context):
		main(self)
		return {'FINISHED'}


def main(context):
	print("\n________________________\nis_global")

	#Store selection
	utilities_uv.selection_store()

	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()

	#Only in Face or Island mode
	if bpy.context.scene.tool_settings.uv_select_mode is not 'FACE' or 'ISLAND':
		bpy.context.scene.tool_settings.uv_select_mode = 'FACE'

	obj  = bpy.context.object
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data);
	uv_layers = bm.loops.layers.uv.verify();
	
	islands = utilities_uv.getSelectionIslands()
	
	for faces in islands:
		# Get average viewport normal of UV island
		avg_normal = Vector((0,0,0))
		for face in faces:
			avg_normal+=face.normal
		avg_normal/=len(faces)

		# avg_normal = (obj.matrix_world*avg_normal).normalized()

		# Which Side
		x = 0
		y = 1
		z = 2
		max_size = max(abs(avg_normal.x), abs(avg_normal.y), abs(avg_normal.z))
		
		#for i in range(3):  # Use multiple steps  #REMOVED: maybe should be reimplemented as a custom property
		if(abs(avg_normal.x) == max_size):
			print("x normal")
			align_island(obj, bm, uv_layers, faces, y, z, avg_normal.x < 0, False)
		elif(abs(avg_normal.y) == max_size):
			print("y normal")
			align_island(obj, bm, uv_layers, faces, x, z, avg_normal.y > 0, False)
		elif(abs(avg_normal.z) == max_size):
			print("z normal")
			align_island(obj, bm, uv_layers, faces, x, y, False, avg_normal.z < 0)

		print("align island: faces {}x n:{}, max:{}".format(len(faces), avg_normal, max_size))
	
	#Restore selection
	utilities_uv.selection_restore()


def align_island(obj, bm, uv_layers, faces, x=0, y=1, flip_x=False, flip_y=False):

	# Find lowest and highest verts
	minmax_val  = [0,0]
	minmax_vert = [None, None]

	axis_names = ['x', 'y', 'z']
	print("Align shell {}x 	at {},{} flip {},{}".format(len(faces), axis_names[x], axis_names[y], flip_x, flip_y))

		# print("  Min #{} , Max #{} along '{}'".format(minmax_vert[0].index, minmax_vert[1].index, axis_names[y] ))
		# print("  A1 {:.1f} , A2 {:.1f} along ".format(minmax_val[0], minmax_val[1] ))
	
	# Collect UV to Vert
	vert_to_uv = {}
	for face in faces:
		for loop in face.loops:
			vert = loop.vert
			uv = loop[uv_layers]
			if vert not in vert_to_uv:
				vert_to_uv[vert] = [uv];
			else:
				vert_to_uv[vert].append(uv)
	#uv_to_vert = utilities_uv.get_uv_to_vert(bm, uv_layers)
	processed_edges = []
	n_edges = 0
	avg_angle = 0
	for face in faces:
		for edge in face.edges:
			if edge not in processed_edges:
				processed_edges.append(edge)
				delta = edge.verts[0].co -edge.verts[1].co
				max_side = max(abs(delta.x), abs(delta.y), abs(delta.z))
				# Check edges dominant in active axis
				if( abs(delta[x]) == max_side or abs(delta[y]) == max_side):
					n_edges += 1
					uv0 = vert_to_uv[ edge.verts[0] ][0]
					uv1 = vert_to_uv[ edge.verts[1] ][0]

					delta_verts = Vector((
						edge.verts[1].co[x] - edge.verts[0].co[x],
						edge.verts[1].co[y] - edge.verts[0].co[y]
					))
					if flip_x:
						delta_verts.x = -edge.verts[1].co[x] + edge.verts[0].co[x]
					if flip_y:
						delta_verts.y = -edge.verts[1].co[y] + edge.verts[0].co[y]
					
					delta_uvs = Vector((
						uv1.uv.x - uv0.uv.x,
						uv1.uv.y - uv0.uv.y
					))

					a0 = math.atan2(delta_verts.y, delta_verts.x) #- math.pi/2
					a1 = math.atan2(delta_uvs.y, delta_uvs.x) #- math.pi/2
					
					a_delta = math.atan2(math.sin(a0-a1), math.cos(a0-a1))

					# Consolidation (math.atan2 gives the lower angle between -Pi and Pi, this triggers errors when using the average avg_angle /= n_edges for rotation angles close to Pi)
					if n_edges > 1:
						if abs((avg_angle / (n_edges-1)) - a_delta) > 2.8:
							if a_delta > 0:
								avg_angle+=(a_delta-math.pi*2)
							else:
								avg_angle+=(a_delta+math.pi*2)
						else:		
							avg_angle+=a_delta
					else:		
						avg_angle+=a_delta

	avg_angle /= n_edges
	
	print("Edges {}x".format(n_edges))
	print("Turn {:.1f}".format(avg_angle * 180/math.pi))
	
	bpy.ops.uv.select_all(action='DESELECT')
	for face in faces:
		for loop in face.loops:
			loop[uv_layers].select = True

	bpy.context.tool_settings.transform_pivot_point = 'MEDIAN_POINT'
	bpy.ops.transform.rotate(value=-avg_angle, orient_axis='Z')  # minus angle; Blender uses unconventional rotation notation (positive for clockwise)


bpy.utils.register_class(op)
