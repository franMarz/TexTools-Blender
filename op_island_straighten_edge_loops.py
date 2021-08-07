import bpy
import bmesh

from math import copysign
from mathutils import Vector
from collections import defaultdict
from itertools import chain
from . import utilities_uv


precision = 5



class op(bpy.types.Operator):
	bl_idname = "uv.textools_island_straighten_edge_loops"
	bl_label = "Straight edges chain"
	bl_description = "Straighten selected edges chain and relax rest of the UV Island"
	bl_options = {'REGISTER', 'UNDO'}
	
	@classmethod
	def poll(cls, context):
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object.mode != 'EDIT':
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		if bpy.context.area.type != 'IMAGE_EDITOR':
			return False
		if not bpy.context.object.data.uv_layers:
			return False
		if bpy.context.scene.tool_settings.uv_select_mode != 'EDGE':
		 	return False
		if bpy.context.scene.tool_settings.use_uv_select_sync:
			return False
		return True


	def execute(self, context):
		utilities_uv.multi_object_loop(main, self, context)
		return {'FINISHED'}



def main(self, context):
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()

	selected_faces_loops = utilities_uv.selection_store(bm, uv_layers, return_selected_faces_loops=True)

	for face in selected_faces_loops.keys():
		if len(selected_faces_loops[face]) == len(face.loops):
			self.report({'ERROR_INVALID_INPUT'}, "No face should be selected." )
			return

	islands = utilities_uv.getSelectionIslands(bm, uv_layers, selected_faces_loops.keys())

	for island in islands:
		selected_loops_island = {loop for face in island.intersection(selected_faces_loops.keys()) for loop in selected_faces_loops[face]}

		openSegment = get_loops_segments(self, bm, uv_layers, selected_loops_island)
		if not openSegment:
			continue

		straighten(bm, uv_layers, island, openSegment)

	utilities_uv.selection_restore(bm, uv_layers, restore_seams=True)



def straighten(bm, uv_layers, island, segment_loops):
	bpy.ops.uv.select_all(action='DESELECT')
	bpy.ops.mesh.select_all(action='DESELECT')
	for face in island:
		face.select_set(True)
		for loop in face.loops:
			loop[uv_layers].select = True

	# Make edges of the island bounds seams temporarily for a more predictable result
	bpy.ops.uv.seams_from_islands(mark_seams=True, mark_sharp=False)

	bbox = segment_loops[-1][uv_layers].uv - segment_loops[0][uv_layers].uv
	straighten_in_x = True
	sign = copysign(1, bbox.x)
	if abs(bbox.y) >= abs(bbox.x):
		straighten_in_x = False
		sign = copysign(1, bbox.y)

	origin = segment_loops[0][uv_layers].uv
	edge_lengths = []
	length = 0
	newly_pinned = set()

	for i, loop in enumerate(segment_loops):
		if i > 0:
			vect = loop[uv_layers].uv - segment_loops[i-1][uv_layers].uv
			edge_lengths.append(vect.length)

	for i, loop in enumerate(segment_loops):
		if i == 0:
			if not loop[uv_layers].pin_uv:
				loop[uv_layers].pin_uv = True
				newly_pinned.add(loop)
		else:
			length += edge_lengths[i-1]
			for nodeLoop in loop.vert.link_loops:
				if nodeLoop[uv_layers].uv.to_tuple(precision) == loop[uv_layers].uv.to_tuple(precision):
					if straighten_in_x:
						nodeLoop[uv_layers].uv = origin + Vector((sign*length, 0))
					else:
						nodeLoop[uv_layers].uv = origin + Vector((0, sign*length))
					if not nodeLoop[uv_layers].pin_uv:
						nodeLoop[uv_layers].pin_uv = True
						newly_pinned.add(nodeLoop)

	try:	# Unwrapping may fail on certain mesh topologies
		bpy.ops.uv.unwrap(method='ANGLE_BASED', fill_holes=True, correct_aspect=True, use_subsurf_data=False, margin=0)
	except:
		pass

	for nodeLoop in newly_pinned:
		nodeLoop[uv_layers].pin_uv = False



def get_loops_segments(self, bm, uv_layers, island_loops_dirty):
	island_loops = set()
	island_loops_nexts = set()
	processed_edges = set()
	processed_coords = defaultdict(list)
	start_loops = []
	boundary_splitted_edges = {loop.edge for loop in island_loops_dirty if (not loop.edge.is_boundary) and loop[uv_layers].uv.to_tuple(precision) != loop.link_loop_radial_next.link_loop_next[uv_layers].uv.to_tuple(precision)}

	for loop in island_loops_dirty:
		if loop.link_loop_next in island_loops_dirty and (loop.edge in boundary_splitted_edges or loop.edge not in processed_edges):
			island_loops.add(loop)
			island_loops_nexts.add(loop.link_loop_next)
			processed_edges.add(loop.edge)

	if not processed_edges:
		self.report({'ERROR_INVALID_INPUT'}, "Invalid selection in an island: no edges selected." )
		return None

	for loop in chain(island_loops, island_loops_nexts):
		processed_coords[loop[uv_layers].uv.to_tuple(precision)].append(loop)

	for node_loops in processed_coords.values():
		if len(node_loops) > 2:
			self.report({'ERROR_INVALID_INPUT'}, "No forked edge loops should be selected." )
			return None
		elif len(node_loops) == 1:
			start_loops.extend(node_loops)

	if not start_loops:
		self.report({'ERROR_INVALID_INPUT'}, "Invalid selection in an island: closed UV edge loops." )
		return None
	elif len(start_loops) < 2:
		self.report({'ERROR_INVALID_INPUT'}, "Invalid selection in an island: self-intersecting edge loop." )
		return None
	elif len(start_loops) > 2:
		self.report({'ERROR_INVALID_INPUT'}, "Invalid selection in an island: multiple edge loops." )
		return None


	if len(processed_coords.keys()) < 2:
		self.report({'ERROR_INVALID_INPUT'}, "Invalid selection in an island: zero length edges." )
		return None

	elif len(processed_coords.keys()) == 2:
		single_edge_loops = list(chain.from_iterable(processed_coords.values()))
		if len(single_edge_loops) == 2:
			return single_edge_loops
		else:
			self.report({'ERROR_INVALID_INPUT'}, "Invalid selection in an island: zero length or overlapping edges." )
			return None

	else:

		island_nodal_loops = list(chain.from_iterable(processed_coords.values()))

		if start_loops[0] in island_nodal_loops:
			island_nodal_loops.remove(start_loops[0])
		island_nodal_loops.insert(0, start_loops[0])
		if start_loops[1] in island_nodal_loops:
			island_nodal_loops.remove(start_loops[1])
		island_nodal_loops.append(start_loops[1])


		def find_next_loop(loop):

			def get_prev(found_prev):
				if found_prev:
					for foundLoop in found_prev:
						if foundLoop[uv_layers].uv.to_tuple(precision) == loop.link_loop_prev[uv_layers].uv.to_tuple(precision):
							segment.append(foundLoop)
							for anyLoop in found_prev:
								if anyLoop[uv_layers].uv.to_tuple(precision) == loop.link_loop_prev[uv_layers].uv.to_tuple(precision):
									island_nodal_loops.remove(anyLoop)
							return foundLoop, False
				return None, True

			def get_next(found_next):
				for foundLoop in found_next:
					if foundLoop[uv_layers].uv.to_tuple(precision) == loop.link_loop_next[uv_layers].uv.to_tuple(precision):
						segment.append(foundLoop)
						for anyLoop in found_next:
							if anyLoop[uv_layers].uv.to_tuple(precision) == loop.link_loop_next[uv_layers].uv.to_tuple(precision):
								island_nodal_loops.remove(anyLoop)
						return foundLoop, False
				get_prev(set(island_nodal_loops).intersection(loop.link_loop_prev.vert.link_loops))


			found_next = set(island_nodal_loops).intersection(loop.link_loop_next.vert.link_loops)
			if found_next:
				loopNext, end = get_next(found_next)
			else:
				loopNext, end = get_prev(set(island_nodal_loops).intersection(loop.link_loop_prev.vert.link_loops))

			if end:
				openSegments.append(segment)

			return loopNext, end


		openSegments = []


		while len(island_nodal_loops) > 0:

			loop = island_nodal_loops[0]
			segment = [loop]
			end = False
			
			island_nodal_loops.pop(0)
			if loop in island_loops:
				if loop.link_loop_next in island_nodal_loops and loop.link_loop_next not in start_loops:
					island_nodal_loops.remove(loop.link_loop_next)
			elif loop.link_loop_prev in island_nodal_loops and loop.link_loop_prev not in start_loops:
				island_nodal_loops.remove(loop.link_loop_prev)
			
			while not end:
				loop, end = find_next_loop(loop)

				if not end:
					if loop.link_loop_next in island_nodal_loops and loop.link_loop_next not in start_loops:
						island_nodal_loops.remove(loop.link_loop_next)
					if loop.link_loop_prev in island_nodal_loops and loop.link_loop_prev not in start_loops:
						island_nodal_loops.remove(loop.link_loop_prev)

				if not island_nodal_loops:
					end = True
					openSegments.append(segment)
					break


		if len(openSegments) > 1:
			self.report({'ERROR_INVALID_INPUT'}, "Invalid selection in an island: multiple edge loops. Working in the longest one." )
			openSegments.sort(key=len, reverse=True)

	return openSegments[0]


bpy.utils.register_class(op)
