import bpy
import bmesh
import numpy as np

from mathutils import Vector
from . import utilities_uv


precision = 5



class op(bpy.types.Operator):
	bl_idname = "uv.textools_island_align_world"
	bl_label = "Align World"
	bl_description = "Align selected UV islands or faces to world / gravity directions"
	bl_options = {'REGISTER', 'UNDO'}

	bool_face : bpy.props.BoolProperty(name="Per Face", default=False, description="Process each face independently.")
	axis : bpy.props.EnumProperty(items= 
		[('-1', 'Auto', 'Detect World axis to align to.'), 
		('0', 'X', 'Align to the X axis of the World.'), 
		('1', 'Y', 'Align to the Y axis of the World.'), 
		('2', 'Z', 'Align to the Z axis of the World.'), ], name = "Axis", default = '-1'
	)

	@classmethod
	def poll(cls, context):
		if bpy.context.area.ui_type != 'UV':
			return False
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object.mode != 'EDIT':
			return False
		if not bpy.context.object.data.uv_layers:
			return False
		return True


	def execute(self, context):
		utilities_uv.multi_object_loop(main, self, context)
		return {'FINISHED'}



def main(self, context):
	selection_mode = bpy.context.scene.tool_settings.uv_select_mode
	obj = bpy.context.active_object
	me = obj.data
	bm = bmesh.from_edit_mesh(me)
	uv_layers = bm.loops.layers.uv.verify()
	sync = bpy.context.scene.tool_settings.use_uv_select_sync

	if sync:
		selected_faces = {f for f in bm.faces if f.select}
	else:
		selected_faces = {f for f in bm.faces if all([loop[uv_layers].select for loop in f.loops]) and f.select}
	if not selected_faces:
		return

	if self.bool_face:
		islands = [[f] for f in selected_faces]
	else:
		islands = utilities_uv.get_selected_islands(bm, uv_layers, extend_selection_to_islands=True)

	for faces in islands:
		faces_set = set(faces)

		if self.bool_face:
			calc_loops = faces[0].loops
			avg_normal = faces[0].normal

		else:
			selected_faces_in_island = faces.intersection(selected_faces)

			if selected_faces_in_island:
				pre_calc_faces = selected_faces_in_island
			else:
				pre_calc_faces = faces

			if len(pre_calc_faces) == 1:
				selected_face = next(iter(pre_calc_faces))
				calc_loops = selected_face.loops
				avg_normal = selected_face.normal
			else:
				calc_loops = []
				calc_edges = set()
				island_edges = {edge for face in pre_calc_faces for edge in face.edges}
				island_loops = {loop for face in pre_calc_faces for loop in face.loops}
				for edge in island_edges:
					if len({loop[uv_layers].uv.to_tuple(precision) for vert in edge.verts for loop in vert.link_loops if loop in island_loops}) == 2:
						calc_edges.add(edge)
						for loop in edge.link_loops:
							if loop in island_loops:
								calc_loops.append(loop)
								break
				if not calc_loops:
					self.report({'ERROR_INVALID_INPUT'}, "Invalid selection in an island: zero non-splitted edges." )
					continue

				# Get average viewport normal of UV island
				avg_normal = Vector((0,0,0))
				calc_faces = [face for face in pre_calc_faces if {edge for edge in face.edges}.issubset(calc_edges)]
				if not calc_faces:
					self.report({'ERROR_INVALID_INPUT'}, "Invalid selection in an island: no faces formed by unique edges." )
					continue
				for face in calc_faces:
					avg_normal += face.normal
				avg_normal /= len(calc_faces)

		# Which Side
		x = 0
		y = 1
		z = 2
		max_size = max(map(abs, avg_normal))

		if (self.axis == '-1' and abs(avg_normal.z) == max_size) or self.axis == '2':
			align_island(self, me, bm, uv_layers, faces, calc_loops, x, y, False, avg_normal.z < 0)
		elif (self.axis == '-1' and abs(avg_normal.y) == max_size) or self.axis == '1':
			align_island(self, me, bm, uv_layers, faces, calc_loops, x, z, avg_normal.y > 0, False)
		else:	#(self.axis == '-1' and abs(avg_normal.x) == max_size) or self.axis == '0':
			align_island(self, me, bm, uv_layers, faces, calc_loops, y, z, avg_normal.x < 0, False)

	bmesh.update_edit_mesh(obj.data)

	# Workaround for selection not flushing properly from loops to EDGE Selection Mode, apparently since UV edge selection support was added to the UV space
	if not sync:
		bpy.ops.uv.select_mode(type='VERTEX')
	bpy.context.scene.tool_settings.uv_select_mode = selection_mode



def align_island(self, me, bm, uv_layers, faces, loops, x=0, y=1, flip_x=False, flip_y=False):
	n_edges = 0
	avg_angle = 0

	for loop in loops:
		co0 = loop.vert.co
		co1 = loop.link_loop_next.vert.co
		delta = co1- co0
		max_side = max(map(abs, delta))

		# Check edges dominant in active axis
		if abs(delta[x]) == max_side or abs(delta[y]) == max_side:
			n_edges += 1
			uv0 = loop[uv_layers].uv
			uv1 = loop.link_loop_next[uv_layers].uv

			delta_verts = Vector((0,0))
			if not flip_x:
				delta_verts.x = co1[x] - co0[x]
			else:
				delta_verts.x = co0[x] - co1[x]
			if not flip_y:
				delta_verts.y = co1[y] - co0[y]
			else:
				delta_verts.y = co0[y] - co1[y]
			
			delta_uvs = uv1 - uv0

			a0 = np.arctan2(delta_verts.y, delta_verts.x)
			a1 = np.arctan2(delta_uvs.y, delta_uvs.x)

			a_delta = np.arctan2(np.sin(a0-a1), np.cos(a0-a1))

			# Consolidation (np.arctan2 gives the lower angle between -Pi and Pi, this triggers errors when using the average avg_angle /= n_edges for rotation angles close to Pi)
			if n_edges > 1:
				if abs( (avg_angle / (n_edges-1)) - a_delta ) > 3.12:
					if a_delta > 0:
						avg_angle += (a_delta - np.pi*2)
					else:
						avg_angle += (a_delta + np.pi*2)
				else:
					avg_angle += a_delta
			else:
				avg_angle += a_delta

	avg_angle /= n_edges

	if avg_angle:
		matrix = np.array([[np.cos(avg_angle), -np.sin(avg_angle)], [np.sin(avg_angle), np.cos(avg_angle)]])
		vec_origin = utilities_uv.get_center(faces, bm, uv_layers)

		for face in faces:
			for loop in face.loops:
				uvs0 = loop[uv_layers].uv - vec_origin
				loop[uv_layers].uv = (vec_origin.x + matrix[0][0]*uvs0.x + matrix[0][1]*uvs0.y, vec_origin.y + matrix[1][0]*uvs0.x + matrix[1][1]*uvs0.y)

		if self.bool_face:
			bmesh.update_edit_mesh(me, loop_triangles=False)
