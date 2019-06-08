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
		
		# Use multiple steps
		for i in range(3):
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
	vert_to_uv = utilities_uv.get_vert_to_uv(bm, uv_layers)
	uv_to_vert = utilities_uv.get_uv_to_vert(bm, uv_layers)

	processed_edges = []
	edges = []
	for face in faces:
		for edge in face.edges:
			if edge not in processed_edges:
				processed_edges.append(edge)
				delta = edge.verts[0].co -edge.verts[1].co
				max_side = max(abs(delta.x), abs(delta.y), abs(delta.z))

				# Check edges dominant in active axis
				if( abs(delta[x]) == max_side or abs(delta[y]) == max_side):
				# if( abs(delta[y]) == max_side):
					edges.append(edge)

	print("Edges {}x".format(len(edges)))

	avg_angle = 0
	for edge in edges:
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
		
		# 	delta_verts.y = edge.verts[0].co[y] - edge.verts[1].co[y]
			

		delta_uvs = Vector((
			uv1.uv.x - uv0.uv.x,
			uv1.uv.y - uv0.uv.y
		))
		a0 = math.atan2(delta_verts.y, delta_verts.x) - math.pi/2
		a1 = math.atan2(delta_uvs.y, delta_uvs.x) - math.pi/2

		


		a_delta = math.atan2(math.sin(a0-a1), math.cos(a0-a1)) 
		# edge.verts[0].index, edge.verts[1].index
		# print("  turn {:.1f}	.. {:.1f} , {:.1f}".format(a_delta*180/math.pi, a0*180/math.pi,a1*180/math.pi))
		avg_angle+=a_delta


	avg_angle/=len(edges) # - math.pi/2
	print("Turn {:.1f}".format(avg_angle * 180/math.pi))
	
	bpy.ops.uv.select_all(action='DESELECT')
	for face in faces:
		for loop in face.loops:
			loop[uv_layers].select = True


	bpy.context.tool_settings.transform_pivot_point = 'MEDIAN_POINT'
	bpy.ops.transform.rotate(value=avg_angle, orient_axis='Z')
	# bpy.ops.transform.rotate(value=0.58191, axis=(-0, -0, -1), constraint_axis=(False, False, False), orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SPHERE', proportional_size=0.0267348)


	# processed = []
	

	'''
	bpy.ops.uv.select_all(action='DESELECT')
	for face in faces:

		# Collect UV to Vert
		for loop in face.loops:
			loop[uv_layers].select = True
			vert = loop.vert
			uv = loop[uv_layers]
			# vert_to_uv
			if vert not in vert_to_uv:
				vert_to_uv[vert] = [uv];
			else:
				vert_to_uv[vert].append(uv)
			# uv_to_vert
			if uv not in uv_to_vert:
				uv_to_vert[ uv ] = vert;


		for vert in face.verts:
			if vert not in processed:
				processed.append(vert)

				vert_y = (vert.co)[y] #obj.matrix_world * 

				print("idx {} = {}".format(vert.index, vert_y))

				if not minmax_vert[0] or not minmax_vert[1]:
					minmax_vert[0] = vert
					minmax_vert[1] = vert
					minmax_val[0] = vert_y
					minmax_val[1] = vert_y
					continue

				if vert_y < minmax_val[0]:
					# Not yet defined or smaller
					minmax_vert[0] = vert
					minmax_val[0] = vert_y
					
				elif vert_y > minmax_val[1]:
					minmax_vert[1] = vert
					minmax_val[1] = vert_y
					

	if minmax_vert[0] and minmax_vert[1]:
		axis_names = ['x', 'y', 'z']
		print("  Min #{} , Max #{} along '{}'".format(minmax_vert[0].index, minmax_vert[1].index, axis_names[y] ))
		# print("  A1 {:.1f} , A2 {:.1f} along ".format(minmax_val[0], minmax_val[1] ))
		
		vert_A = minmax_vert[0]
		vert_B = minmax_vert[1]
		uv_A = vert_to_uv[vert_A][0]
		uv_B = vert_to_uv[vert_B][0]

		delta_verts = Vector((
			vert_B.co[x] - vert_A.co[x],
			vert_B.co[y] - vert_A.co[y]
		))

		delta_uvs = Vector((
			uv_B.uv.x - uv_A.uv.x,
			uv_B.uv.y - uv_A.uv.y,

		))
		# Get angles
		angle_vert = math.atan2(delta_verts.y, delta_verts.x) - math.pi/2
		angle_uv = math.atan2(delta_uvs.y, delta_uvs.x) - math.pi/2

		angle_delta = math.atan2(math.sin(angle_vert-angle_uv), math.cos(angle_vert-angle_uv))

		print("  Angles {:.2f} | {:.2f}".format(angle_vert*180/math.pi, angle_uv*180/math.pi))
		print("  Angle Diff {:.2f}".format(angle_delta*180/math.pi))

		bpy.context.tool_settings.transform_pivot_point = 'MEDIAN_POINT'
		bpy.ops.transform.rotate(value=angle_delta, axis='Z')
		# bpy.ops.transform.rotate(value=0.58191, axis=(-0, -0, -1), constraint_axis=(False, False, False), orient_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SPHERE', proportional_size=0.0267348)


		# bpy.ops.mesh.select_all(action='DESELECT')
		# vert_A.select = True
		# vert_B.select = True

		# return
	'''

bpy.utils.register_class(op)
