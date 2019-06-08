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
	bl_idname = "uv.textools_island_mirror"
	bl_label = "Symmetry"
	bl_description = "Mirrors selected faces to other half or averages based on selected edge center"
	bl_options = {'REGISTER', 'UNDO'}
	
	is_stack : bpy.props.BoolProperty(description="Stack the halves on top of each other?", default=False)

	@classmethod
	def poll(cls, context):


		if not bpy.context.active_object:
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


		if bpy.context.scene.tool_settings.use_uv_select_sync:
			return False


		if bpy.context.scene.tool_settings.uv_select_mode != 'EDGE' and bpy.context.scene.tool_settings.uv_select_mode != 'FACE':
		 	return False

		# if bpy.context.scene.tool_settings.use_uv_select_sync:
		# 	return False

		return True

	def execute(self, context):
		main(context)
		return {'FINISHED'}



def main(context):
	print("--------------------------- Executing operator_mirror")

	#Store selection
	utilities_uv.selection_store()

	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()

	if bpy.context.scene.tool_settings.uv_select_mode == 'EDGE':


		# 1.) Collect left and right side verts
		verts_middle = [];

		for face in bm.faces:
			if face.select:
				for loop in face.loops:
					if loop[uv_layers].select and loop.vert not in verts_middle:
						verts_middle.append(loop.vert)
					
		# 2.) Align UV shell
		alignToCenterLine()

		# Convert to Vert selection and extend edge loop in 3D space
		bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
		bpy.ops.mesh.select_all(action='DESELECT')
		for vert in verts_middle:
			vert.select = True

		bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='EDGE')
		bpy.ops.mesh.loop_multi_select(ring=False)
		for vert in bm.verts:
			if vert.select and vert not in verts_middle:
				print("Append extra vert to symmetry line from xyz edge loop")
				verts_middle.append(vert)

		# Select UV shell Again
		bpy.ops.mesh.select_linked(delimit={'UV'})
		verts_island = []
		for vert in bm.verts:
			if vert.select:
				verts_island.append(vert)


		# 3.) Restore UV vert selection
		x_middle = 0
		bpy.ops.uv.select_all(action='DESELECT')
		for face in bm.faces:
			if face.select:
				for loop in face.loops:
					if loop.vert in verts_middle:
						loop[uv_layers].select = True
						x_middle = loop[uv_layers].uv.x;


		print("Middle "+str(len(verts_middle))+"x, x pos: "+str(x_middle))

		# Extend selection
		bpy.ops.uv.select_more()
		verts_A = [];
		verts_B = [];
		for face in bm.faces:
			if face.select:
				for loop in face.loops:
					if loop[uv_layers].select and loop.vert not in verts_middle:
						if loop[uv_layers].uv.x <= x_middle:
							# Left
							if loop.vert not in verts_A:
								verts_A.append(loop.vert)

						elif loop[uv_layers].uv.x > x_middle:
							# Right
							if loop.vert not in verts_B:
								verts_B.append(loop.vert)

		

		
		def remove_doubles():
			verts_double = [vert for vert in verts_island if (vert in verts_A and vert in verts_B)]

			# print("Temp  double: "+str(len(verts_double))+"x")
			if len(verts_double) > 0:
				print("TODO: Remove doubles "+str(len(verts_double)))
				for vert in verts_double:
					verts_A.remove(vert)
					verts_B.remove(vert)
					verts_middle.append(vert)

		def extend_half_selection(verts_middle, verts_half, verts_other):
			# Select initial half selection
			bpy.ops.uv.select_all(action='DESELECT')
			for face in bm.faces:
				if face.select:
					for loop in face.loops:
						if loop.vert in verts_half:
							loop[uv_layers].select = True

			# Extend selection				
			bpy.ops.uv.select_more()

			# count_added = 0
			for face in bm.faces:
				if face.select:
					for loop in face.loops:
						if loop.vert not in verts_half and loop.vert not in verts_middle and loop[uv_layers].select:
							verts_half.append(loop.vert)


		remove_doubles()

		# Limit iteration loops
		max_loops_extend = 200
		for i in range(0, max_loops_extend):
			print("Now extend selection A / B")
			count_hash = str(len(verts_A))+"_"+str(len(verts_B));
			extend_half_selection(verts_middle, verts_A, verts_B)
			extend_half_selection(verts_middle, verts_B, verts_A)
			remove_doubles()

			count_hash_new = str(len(verts_A))+"_"+str(len(verts_B));
			if count_hash_new == count_hash:
				print("Break loop, same as previous loop")
				break;

		print("Edge, Sides: L:"+str(len(verts_A))+" | R:"+str(len(verts_B)))

		# 4.) Mirror Verts
		mirror_verts(verts_middle, verts_A, verts_B, False)


	if bpy.context.scene.tool_settings.uv_select_mode == 'FACE':

		# 1.) Get selected UV faces to vert faces
		selected_faces = []
		for face in bm.faces:
			if face.select:
				# Are all UV faces selected?
				countSelected = 0
				for loop in face.loops:
					if loop[uv_layers].select:
						countSelected+=1
						# print("Vert selected "+str(face.index))
				if countSelected == len(face.loops):
					selected_faces.append(face)


		# if bpy.context.scene.tool_settings.use_uv_select_sync == False:

		bpy.ops.uv.select_linked()
		verts_all = []
		for face in bm.faces:
			if face.select:
				for loop in face.loops:
					if(loop.vert not in verts_all):
						verts_all.append(loop.vert)

		print("Verts shell: "+str(len(verts_all)))


		bpy.ops.mesh.select_all(action='DESELECT')
		for face in selected_faces:
			face.select = True


		# 2.) Select Vert shell's outer edges
		bpy.ops.mesh.select_linked(delimit=set())
		bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
		bpy.ops.mesh.region_to_loop()
		edges_outer_shell = [e for e in bm.edges if e.select]

		# 3.) Select Half's outer edges
		bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
		bpy.ops.mesh.select_all(action='DESELECT')
		for face in selected_faces:
			face.select = True
		bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
		bpy.ops.mesh.region_to_loop()
		edges_outer_selected = [e for e in bm.edges if e.select]

		# 4.) Mask edges exclusive to edges_outer_selected (symmetry line)
		edges_middle = [item for item in edges_outer_selected if item not in edges_outer_shell]

		# 5.) Convert to UV selection
		verts_middle = []
		for edge in edges_middle:
			if edge.verts[0] not in verts_middle:
				verts_middle.append(edge.verts[0])
			if edge.verts[1] not in verts_middle:
				verts_middle.append(edge.verts[1])

		#Select all Vert shell faces
		bpy.ops.mesh.select_linked(delimit=set())
		#Select UV matching vert array
		bpy.ops.uv.select_all(action='DESELECT')
		for face in bm.faces:
			if face.select:
				for loop in face.loops:
					if loop.vert in verts_middle:
						loop[uv_layers].select = True

		# 5.) Align UV shell
		alignToCenterLine()

		# 7.) Collect left and right side verts
		verts_A = [];
		verts_B = [];

		bpy.ops.uv.select_all(action='DESELECT')
		for face in selected_faces:
			for loop in face.loops:
				if loop.vert not in verts_middle and loop.vert not in verts_A:
					verts_A.append(loop.vert)

		for vert in verts_all:
			if vert not in verts_middle and vert not in verts_A and vert not in verts_B:
				verts_B.append(vert)

		# 8.) Mirror Verts
		mirror_verts(verts_middle, verts_A, verts_B, True)

	#Restore selection
	# utilities_uv.selection_restore()





def mirror_verts(verts_middle, verts_A, verts_B, isAToB):

	print("--------------------------------\nMirror: C:"+str(len(verts_middle))+" ; verts: "+str(len(verts_A))+"|"+str(len(verts_B))+"x, 	A to B? "+str(isAToB))


	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()


	# Get verts_island
	verts_island = []
	for vert in verts_middle:
		verts_island.append(vert)
	for vert in verts_A:
		verts_island.append(vert)
	for vert in verts_B:
		verts_island.append(vert)

	# Select Island as Faces
	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
	bpy.ops.mesh.select_all(action='DESELECT')
	for vert in verts_island:
		vert.select = True
	bpy.ops.mesh.select_mode(use_extend=False, use_expand=True, type='FACE')

	# Collect Librarys of verts / UV
	vert_to_uv = utilities_uv.get_vert_to_uv(bm, uv_layers)
	uv_to_vert = utilities_uv.get_uv_to_vert(bm, uv_layers)
	uv_to_face = {}
	# UV clusters / groups (within 0.000001 distance)
	clusters = []
	uv_to_clusters = {}
	vert_to_clusters = {}

	for face in bm.faces:
		if face.select:
			for loop in face.loops:
				vert = loop.vert
				uv = loop[uv_layers]

				if uv not in uv_to_face:
					uv_to_face[ uv ] = face;

				# clusters
				isMerged = False
				for cluster in clusters:
					d = (uv.uv - cluster.uvs[0].uv).length
					if d <= 0.0000001:
						#Merge
						cluster.append(uv)
						uv_to_clusters[uv] = cluster
						if vert not in vert_to_clusters:
							vert_to_clusters[vert] = cluster
						isMerged = True;
						break;
				if not isMerged:
					#New Group
					clusters.append( UVCluster(vert, [uv]) )
					uv_to_clusters[uv] = clusters[-1]
					if vert not in vert_to_clusters:
							vert_to_clusters[vert] = clusters[-1]

	# Get Center X
	x_middle = vert_to_uv[ verts_middle[0] ][0].uv.x;
	

	# 3.) Grow layer by layer
	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
	bpy.context.scene.tool_settings.uv_select_mode = 'VERTEX'


	clusters_processed = []

	def select_extend_filter(clusters_border, clusters_mask):
		# print("Extend A/B")
		connected_clusters = []
		for cluster in clusters_border:

			# Select and Extend selection
			bpy.ops.uv.select_all(action='DESELECT')
			for uv in cluster.uvs:
				uv.select = True
			bpy.ops.uv.select_more()

			# Collect extended
			uv_extended = [uv for clusterMask in clusters_mask for uv in clusterMask.uvs if (uv.select and clusterMask not in clusters_processed)]
			clusters_extended = []
			for uv in uv_extended:
				if uv_to_clusters[uv] not in clusters_extended:
					clusters_extended.append( uv_to_clusters[uv] )

			# Sort by distance
			groups_distance = {}
			for i in range(0, len(clusters_extended)):
				sub_group = clusters_extended[i]
				groups_distance[i] = (cluster.uvs[0].uv - sub_group.uvs[0].uv).length
			
			# Append to connected clusters
			array = []
			for item in sorted(groups_distance.items(), key=operator.itemgetter(1)):
				key = item[0]
				clust = clusters_extended[key]
				array.append( clust )
				if clust not in clusters_processed:
					clusters_processed.append(clust)

			connected_clusters.append( array )
			
			if cluster not in clusters_processed:
				clusters_processed.append( cluster )


			bpy.ops.uv.select_all(action='DESELECT')
			for uv in uv_extended:
				uv.select = True


		return connected_clusters





	
	mask_A = [vert_to_clusters[vert] for vert in verts_A]
	mask_B = [vert_to_clusters[vert] for vert in verts_B]

	border_A = list([vert_to_clusters[vert] for vert in verts_middle])
	border_B = list([vert_to_clusters[vert] for vert in verts_middle])
	
	for step in range(0, 8):

		if len(border_A) == 0:
			print("{}.: Finished scanning with no growth iterations".format(step))
			break;
		if len(border_A) != len(border_B) or len(border_A) == 0:
			print("Abort: non compatible border A/B: {}x {}x ".format(len(border_A), len(border_B)))
			break;

		print("{}.: border {}x|{}x, processed: {}x".format(step, len(border_A), len(border_B), len(clusters_processed)))
		
		# Collect connected pairs for each side
		connected_A = select_extend_filter(border_A, mask_A)
		connected_B = select_extend_filter(border_B, mask_B)

		print("  Connected: {}x|{}x".format(len(connected_A), len(connected_B)))

		border_A.clear()
		border_B.clear()

		# Traverse through pairs
		for i in range(0, min(len(connected_A), len(connected_B)) ):
			if len(connected_A[i]) == 0:
				continue
			if len(connected_A[i]) != len(connected_B[i]):
				print(".    Error: Inconsistent grow mappings from {}  {}x | {}x".format(i, len(connected_A[i]), len(connected_B[i]) ))
				continue

			indexA = [cluster.vertex.index for cluster in connected_A[i] ]
			indexB = [cluster.vertex.index for cluster in connected_B[i] ]
			indexA = str(indexA).replace("[","").replace("]","").replace(" ","")
			indexB = str(indexB).replace("[","").replace("]","").replace(" ","")
			print(".    Map {}|{} = {}x|{}x".format(indexA, indexB, len(connected_A[i]), len(connected_B[i]) ) )



			if True:#isAToB:
				# Copy A side to B
				for cluster in connected_B[i]:
					for uv in cluster.uvs:
						pos = connected_A[i][0].uvs[0].uv.copy()
						pos.x = x_middle - (pos.x-x_middle)# Flip cooreindate
						# uv.uv = pos
			
			# border_A[i] = uv_to_clusters[ connected_A[i][0] ] 
			# border_B[i] = uv_to_clusters[ connected_B[i][0] ] 
			for j in range(len(connected_A[i])):
				border_A.append( connected_A[i][j] )
				border_B.append( connected_B[i][j] )



			# for uv in clusters_B[idxB]:
		# 					pos = clusters_A[idxA][0].uv.copy()
		# 					# Flip cooreindate
		# 					pos.x = x_middle - (pos.x-x_middle)
		# 					uv.uv = pos

			# for j in range(0, len(connected_A[i])):
			# 	# Group A and B
			# 	groupA = connected_A[i][j];
			# 	groupB = connected_B[i][j];
			# 	# vertexA = [vert_to_clusters[key] for key in vert_to_clusters if vert_to_clusters[key] == groupA]
			# 	print("...map {} -> {}".format(groupA, groupB))



		# for j in range(0, count):
		# 	if len(connected_A[j]) != len(connected_B[j]):
		# 		# print("Error: Inconsistent grow mappings from {}:{}x | {}:{}x".format(border_A[j].index,len(connected_A[j]), border_B[j].index, len(connected_B[j]) ))
		# 		print("Error: Inconsistent grow mappings from {}  {}x | {}x".format(j, len(connected_A[j]), len(connected_B[j]) ))
		# 		continue

		# 	for k in range(0, len(connected_A[j])):
		# 		# Vertex A and B
		# 		vA = connected_A[j][k];
		# 		vB = connected_B[j][k];

		# 		uvsA = vert_to_uv[vA];
		# 		uvsB = vert_to_uv[vB];

		# 		clusters_A = collect_clusters(uvsA)
		# 		clusters_B = collect_clusters(uvsB)

		# 		if len(clusters_A) != len(clusters_B):
		# 			print("Error: Inconsistent vertex UV group pairs at vertex {} : {}".format(vA.index, vB.index))
		# 			continue


		# 		message= "...Map {0} -> {1}  = UVs {2}|{3}x | UV-Groups {4}x|{5}x".format( vA.index, vB.index, len(uvsA), len(uvsB), len(clusters_A), len(clusters_B) )
		# 		if len(clusters_A) > 1:
		# 			message = ">> "+message
		# 		print(message)



		# 		if len(clusters_A) > 0:
		# 			# For each group

		# 			sortA = {}
		# 			sortB = {}
		# 			for g in range(0, len(clusters_A)):
		# 				uv_A = clusters_A[g][0].uv.copy()
		# 				uv_B = clusters_B[g][0].uv.copy()

		# 				# localize X values (from symmetry line)
		# 				uv_A.x = (uv_A.x - x_middle)
		# 				uv_B.x = (uv_B.x - x_middle)

		# 				sortA[g] = abs(uv_A.x) + uv_A.y*2.0
		# 				sortB[g] = abs(uv_B.x) + uv_B.y*2.0
		# 				# print("    .   [{}] : {:.2f}, {:.2f} | {:.2f}, {:.2f}".format(g, uv_A.x, uv_A.y, uv_B.x, uv_B.y))
		# 				print("    .   [{}] : {:.2f} | {:.2f}".format(g, sortA[g], sortB[g]))

		# 			# Sort sortA by value
		# 			sortedA = sorted(sortA.items(), key=operator.itemgetter(1))
		# 			sortedB = sorted(sortB.items(), key=operator.itemgetter(1))
					
		# 			for g in range(0, len(clusters_A)):
		# 				# sortedA[g]
		# 				idxA = sortedA[g][0]
		# 				idxB = sortedB[g][0]

		# 				print("Map clusters_A {} -> ".format(idxA, idxB))
		# 				for uv in clusters_B[idxB]:
		# 					pos = clusters_A[idxA][0].uv.copy()
		# 					# Flip cooreindate
		# 					pos.x = x_middle - (pos.x-x_middle)
		# 					uv.uv = pos

		# 		border_A.append(vA)
		# 		border_B.append(vB)



	print("--------------------------------")
	'''

	def select_extend_filter(verts_border, verts_mask):
		# print("Extend A/B")
		connected_verts = []
		for i in range(0, len(verts_border)):
			 # Collect connected edge verts
			verts_connected_edges = []
			for edge in verts_border[i].link_edges:
				if(edge.verts[0] not in verts_connected_edges):
					verts_connected_edges.append(edge.verts[0])
				if(edge.verts[1] not in verts_connected_edges):
					verts_connected_edges.append(edge.verts[1])

			# Select vert on border
			bpy.ops.mesh.select_all(action='DESELECT')
			verts_border[i].select = True
			

			# Extend selection
			bpy.ops.mesh.select_more()

			# Filter selected verts against mask, connected edges, processed and border
			verts_extended = [vert for vert in bm.verts if (vert.select and vert in verts_connected_edges and vert in verts_mask and vert and vert not in verts_border and vert not in verts_processed)]
			

			# print("    "+str(i)+". scan: "+str(verts_border[i].index)+"; ext: "+str(len(verts_extended))+"x")

			connected_verts.append( [] )

			# Sort by distance
			verts_distance = {}
			for vert in verts_extended:
				verts_distance[vert] = (verts_border[i].co - vert.co).length

			for item in sorted(verts_distance.items(), key=operator.itemgetter(1)):
				connected_verts[i].append( item[0] )

			if verts_border[i] not in verts_processed:
				verts_processed.append(verts_border[i])

		return connected_verts

	# find UV vert blobs , see which ones are same spot
	def collect_clusters(uvs):
		groups = []
		for uv in uvs:
			if len(groups) == 0:
				groups.append([uv])
			else:
				isMerged = False
				for group in groups:
					d = (uv.uv - group[0].uv).length
					if d <= 0.0000001:
						#Merge
						group.append(uv)
						isMerged = True;
						break;
				if not isMerged:
					#New Group
					groups.append([uv])
		return groups

	
	border_A = [vert for vert in verts_middle]
	border_B = [vert for vert in verts_middle]
	

	for i in range(0, 200):

		if len(border_A) == 0:
			print("Finished scanning at {} growth iterations".format(i))
			break;
		if len(border_A) != len(border_B) or len(border_A) == 0:
			print("Abort: non compatible border A/B: {}x {}x ".format(len(border_A), len(border_B)))
			break;

		connected_A = select_extend_filter(border_A, verts_A)
		connected_B = select_extend_filter(border_B, verts_B)

		print("Map pairs: {}|{}".format(len(connected_A), len(connected_B)))

		border_A.clear()
		border_B.clear()

		count = min(len(connected_A), len(connected_B))
		for j in range(0, count):
			if len(connected_A[j]) != len(connected_B[j]):
				# print("Error: Inconsistent grow mappings from {}:{}x | {}:{}x".format(border_A[j].index,len(connected_A[j]), border_B[j].index, len(connected_B[j]) ))
				print("Error: Inconsistent grow mappings from {}  {}x | {}x".format(j, len(connected_A[j]), len(connected_B[j]) ))
				continue

			for k in range(0, len(connected_A[j])):
				# Vertex A and B
				vA = connected_A[j][k];
				vB = connected_B[j][k];

				uvsA = vert_to_uv[vA];
				uvsB = vert_to_uv[vB];

				clusters_A = collect_clusters(uvsA)
				clusters_B = collect_clusters(uvsB)

				if len(clusters_A) != len(clusters_B):
					print("Error: Inconsistent vertex UV group pairs at vertex {} : {}".format(vA.index, vB.index))
					continue


				message= "...Map {0} -> {1}  = UVs {2}|{3}x | UV-Groups {4}x|{5}x".format( vA.index, vB.index, len(uvsA), len(uvsB), len(clusters_A), len(clusters_B) )
				if len(clusters_A) > 1:
					message = ">> "+message
				print(message)



				if len(clusters_A) > 0:
					# For each group


					
					sortA = {}
					sortB = {}
					for g in range(0, len(clusters_A)):
						uv_A = clusters_A[g][0].uv.copy()
						uv_B = clusters_B[g][0].uv.copy()

						# localize X values (from symmetry line)
						uv_A.x = (uv_A.x - x_middle)
						uv_B.x = (uv_B.x - x_middle)

						sortA[g] = abs(uv_A.x) + uv_A.y*2.0
						sortB[g] = abs(uv_B.x) + uv_B.y*2.0
						# print("    .   [{}] : {:.2f}, {:.2f} | {:.2f}, {:.2f}".format(g, uv_A.x, uv_A.y, uv_B.x, uv_B.y))
						print("    .   [{}] : {:.2f} | {:.2f}".format(g, sortA[g], sortB[g]))

					# Sort sortA by value
					sortedA = sorted(sortA.items(), key=operator.itemgetter(1))
					sortedB = sorted(sortB.items(), key=operator.itemgetter(1))
					
					for g in range(0, len(clusters_A)):
						# sortedA[g]
						idxA = sortedA[g][0]
						idxB = sortedB[g][0]

						print("Map clusters_A {} -> ".format(idxA, idxB))
						for uv in clusters_B[idxB]:
							pos = clusters_A[idxA][0].uv.copy()
							# Flip cooreindate
							pos.x = x_middle - (pos.x-x_middle)
							uv.uv = pos
						
				
					# print("Sorted: '"+str(sortedA)+"'")
					# print("Sorted: '"+str(sortedB)+"'")

					# for item in sorted(verts_distance.items(), key=operator.itemgetter(1)):
					# 	connected_verts[i].append( item[0] )

					# TODO: Now map groups to each other
					# uv_avg_A = Vector([0,0])
					# uv_avg_B = Vector([0,0])
					# for m in range(0, len(clusters_A)):
					# 	print("        . ")
					# 	uv_avg_A+= clusters_A[m][0].uv;
					# 	uv_avg_B+= clusters_B[m][0].uv;

					# uv_avg_A/=len(clusters_A)
					# uv_avg_B/=len(clusters_B)

					# print("        avg: {} : {}".format(uv_avg_A, uv_avg_B))
			
				# Done processing, add to border arrays
				border_A.append(vA)
				border_B.append(vB)

	'''

def alignToCenterLine():
	print("align to center line")

	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()
	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')

	# 1.) Get average edges rotation + center
	average_angle = 0
	average_center = Vector((0,0))
	average_count = 0
	for face in bm.faces:
		if face.select:
			verts = []
			for loop in face.loops:
				if loop[uv_layers].select:
					verts.append(loop[uv_layers].uv)

			if len(verts) == 2:
				diff = verts[1] - verts[0]
				angle = math.atan2(diff.y, diff.x)%(math.pi)
				average_center += verts[0] + diff/2
				average_angle += angle
				average_count+=1

	if average_count >0:
		average_angle/=average_count
		average_center/=average_count

	average_angle-= math.pi/2 #Rotate -90 degrees so aligned horizontally

	# 2.) Rotate UV Shell around edge
	bpy.context.tool_settings.transform_pivot_point = 'CURSOR'
	bpy.ops.uv.cursor_set(location=average_center)

	bpy.ops.uv.select_linked()
	bpy.ops.transform.rotate(value=average_angle, orient_axis='Z', constraint_axis=(False, False, False), orient_type='GLOBAL', mirror=False, use_proportional_edit=False)



class UVCluster:
	uvs = []
	vertex = None
	
	def __init__(self, vertex, uvs):
		self.vertex = vertex
		self.uvs = uvs
	
	def append(self, uv):
		self.uvs.append(uv)

bpy.utils.register_class(op)