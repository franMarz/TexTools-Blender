import bpy
import bmesh
import operator
import math
from mathutils import Vector
from collections import defaultdict
from math import pi

from . import utilities_uv

class op(bpy.types.Operator):
	bl_idname = "uv.textools_island_straighten_edge_loops"
	bl_label = "Straight edge loops"
	bl_description = "Straighten edge loops of UV Island and relax rest"
	bl_options = {'REGISTER', 'UNDO'}
	
	@classmethod
	def poll(cls, context):

		if not bpy.context.active_object:
			return False

		if bpy.context.active_object.type != 'MESH':
			return False

		#Only in Edit mode
		if bpy.context.active_object.mode != 'EDIT':
			return False

		#Only in UV editor mode
		if bpy.context.area.type != 'IMAGE_EDITOR':
			return False

		#Requires UV map
		if not bpy.context.object.data.uv_layers:
			return False

		if bpy.context.scene.tool_settings.uv_select_mode != 'EDGE':
		 	return False


		return True


	def execute(self, context):
 
		main(context)
		return {'FINISHED'}




def main(context):
	print("____________________________")
   	
	#Store selection
	utilities_uv.selection_store()

	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()
	
	edges = utilities_uv.get_selected_uv_edges(bm, uv_layers)
	islands = utilities_uv.getSelectionIslands()
	uvs = utilities_uv.get_selected_uvs(bm, uv_layers)
	faces = [f for island in islands for f in island ]


	# Get island faces
	

	# utilities_uv.selection_restore(bm, uv_layers)


	groups = get_edge_groups(bm, uv_layers, faces, edges, uvs)

	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
	bpy.ops.mesh.select_all(action='DESELECT')
	for face in faces:
		face.select = True


	print("Edges {}x".format(len(edges)))
	print("Groups {}x".format(len(groups)))

	# Restore 3D face selection
	

	


	# Restore UV seams and clear pins
	bpy.ops.uv.seams_from_islands()
	bpy.ops.uv.pin(clear=True)

	edge_sets = []
	for edges in groups:
		edge_sets.append( EdgeSet(bm, uv_layers, edges, faces) )
		# straighten_edges(bm, uv_layers, edges, faces)

	



	sorted_sets = sorted(edge_sets, key=lambda x: x.length, reverse=True)

	for edge_set in sorted_sets:
		edge_set.straighten()
		
	#Restore selection
	utilities_uv.selection_restore()
	


class EdgeSet:
	bm = None
	edges = []
	faces = []
	uv_layers = ''
	vert_to_uv = {}
	edge_length = {}
	length = 0

	def __init__(self, bm, uv_layers, edges, faces):
		self.bm = bm
		self.uv_layers = uv_layers
		self.edges = edges
		self.faces = faces

		# Get Vert to UV within faces
		self.vert_to_uv = utilities_uv.get_vert_to_uv(bm, uv_layers)

		# Get edge lengths
		self.edge_length = {}
		self.length = 0
		for e in edges:
			uv1 = self.vert_to_uv[e.verts[0]][0].uv
			uv2 = self.vert_to_uv[e.verts[1]][0].uv
			self.edge_length[e] = (uv2 - uv1).length
			self.length+=self.edge_length[e]


	def straighten(self):
		print("Straight {}x at {:.2f} length ".format(len(self.edges), self.length))

		# Get edge angles in UV space
		angles = {}
		for edge in self.edges:
			uv1 = self.vert_to_uv[edge.verts[0]][0].uv
			uv2 = self.vert_to_uv[edge.verts[1]][0].uv
			delta = uv2 - uv1
			angle = math.atan2(delta.y, delta.x)%(math.pi/2)
			if angle >= (math.pi/4):
				angle = angle - (math.pi/2)
			angles[edge] = abs(angle)
			# print("Angle {:.2f} degr".format(angle * 180 / math.pi))

		# Pick edge with least rotation offset to U or V axis
		edge_main = sorted(angles.items(), key = operator.itemgetter(1))[0][0]

		print("Main edge: {} at {:.2f} degr".format( edge_main.index, angles[edge_main] * 180 / math.pi ))
		
		# Rotate main edge to closest axis
		uvs = [uv for v in edge_main.verts for uv in self.vert_to_uv[v]]
		bpy.ops.uv.select_all(action='DESELECT')
		for uv in uvs:
			uv.select = True
		uv1 = self.vert_to_uv[edge_main.verts[0]][0].uv
		uv2 = self.vert_to_uv[edge_main.verts[1]][0].uv
		diff = uv2 - uv1
		angle = math.atan2(diff.y, diff.x)%(math.pi/2)
		if angle >= (math.pi/4):
			angle = angle - (math.pi/2)
		# bpy.ops.transform.rotate behaves differently based on the version of Blender on the UV Editor. Not expected to be fixed for every version of master
		angle = -angle
		bversion = float(bpy.app.version_string[0:4])
		if bversion == 2.80 or bversion == 2.81 or bversion == 2.82 or bversion == 2.90:
			angle = -angle
		bpy.ops.uv.cursor_set(location=uv1 + diff/2)
		bpy.ops.transform.rotate(value=angle, orient_axis='Z', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, False), mirror=False, use_proportional_edit=False)

		# Expand edges and straighten
		count = len(self.edges)
		processed = [edge_main]
		for i in range(count):
			if(len(processed) < len(self.edges)):
				verts = set([v for e in processed for v in e.verts])
				edges_expand = [e for e in self.edges if e not in processed and (e.verts[0] in verts or e.verts[1] in verts)]
				verts_ends = [v for e in edges_expand for v in e.verts if v in verts]
				

				print("Step, proc {} exp: {}".format( [e.index for e in processed] , [e.index for e in edges_expand] ))

				if len(edges_expand) == 0:
					continue

				for edge in edges_expand:
					# if edge.verts[0] in verts_ends and edge.verts[1] in verts_ends:
					# 	print("Cancel at edge {}".format(edge.index))
					# 	return
						
					print("  E {} verts {} verts end: {}".format(edge.index, [v.index for v in edge.verts], [v.index for v in verts_ends]))
					v1 = [v for v in edge.verts if v in verts_ends][0]
					v2 = [v for v in edge.verts if v not in verts_ends][0]
					# direction
					previous_edge = [e for e in processed if e.verts[0] in edge.verts or e.verts[1] in edge.verts][0]
					prev_v1 = [v for v in previous_edge.verts if v != v1][0]
					prev_v2 = [v for v in previous_edge.verts if v == v1][0]
					direction = (self.vert_to_uv[prev_v2][0].uv - self.vert_to_uv[prev_v1][0].uv).normalized()

					for uv in self.vert_to_uv[v2]:
						uv.uv = self.vert_to_uv[v1][0].uv + direction * self.edge_length[edge]

				print("Procesed {}x Expand {}x".format(len(processed), len(edges_expand) ))
				print("verts_ends: {}x".format(len(verts_ends)))
				processed.extend(edges_expand)

		# Select edges
		uvs = list(set( [uv for e in self.edges for v in e.verts for uv in self.vert_to_uv[v] ] ))
		bpy.ops.uv.select_all(action='DESELECT')
		for uv in uvs:
			uv.select = True

		# Pin UV's
		bpy.ops.uv.pin()
		bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
		bpy.ops.uv.pin(clear=True)








def get_edge_groups(bm, uv_layers, faces, edges, uvs):
	print("Get edge groups, edges {}x".format(len(edges))+"x")

	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')	

	unmatched = edges.copy()

	groups = []

	for edge in edges:
		if edge in unmatched:

			# Loop select edge
			bpy.ops.mesh.select_all(action='DESELECT')
			edge.select = True
			bpy.ops.mesh.loop_multi_select(ring=False)

			# Isolate group within edges
			group = [e for e in bm.edges if e.select and e in edges]
			groups.append(group)

			# Remove from unmatched
			for e in group:
				if e in unmatched:
					unmatched.remove(e)

			print("  Edge {} : Group: {}x , unmatched: {}".format(edge.index, len(group), len(unmatched)))

			# return
			# group = [edge]
			# for e in bm.edges:
			# 	if e.select and e in unmatched:
			# 		unmatched.remove(e)
			# 		group.append(edge)

			
					
	return groups


bpy.utils.register_class(op)


