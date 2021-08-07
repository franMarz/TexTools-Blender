import bpy
import bmesh

from . import utilities_ui
from . import utilities_uv
from . import op_rectify



class op(bpy.types.Operator):
	bl_idname = "uv.textools_unwrap_edge_peel"
	bl_label = "Peel Edge"
	bl_description = "Unwrap pipe along selected edges"
	bl_options = {'REGISTER', 'UNDO'}
	
	@classmethod
	def poll(cls, context):
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		if bpy.context.active_object.mode != 'EDIT':
			return False
		if tuple(bpy.context.scene.tool_settings.mesh_select_mode)[1] == False:
			return False
		return True


	def execute(self, context):
		padding = utilities_ui.get_padding()

		utilities_uv.multi_object_loop(unwrap_edges_pipe, self, context, padding)

		bpy.ops.uv.average_islands_scale()
		bpy.ops.uv.pack_islands(rotate=False, margin=padding)
		return {'FINISHED'}



def unwrap_edges_pipe(self, context, padding):
	contextViewUV = utilities_ui.GetContextViewUV()
	if not contextViewUV:
		self.report({'ERROR_INVALID_INPUT'}, "This tool requires an available UV/Image view.")
		return

	is_sync = bpy.context.scene.tool_settings.use_uv_select_sync

	me = bpy.context.active_object.data
	bm = bmesh.from_edit_mesh(me)
	uv_layers = bm.loops.layers.uv.verify()

	# Extend loop selection
	bpy.ops.mesh.loop_multi_select(ring=False)
	selected_edges = {edge for edge in bm.edges if edge.select}

	if len(selected_edges) == 0:
		#self.report({'ERROR_INVALID_INPUT'}, "No edges selected in the view" )
		return

	bpy.ops.mesh.select_linked(delimit=set())
	bpy.ops.mesh.mark_seam(clear=True)
	selected_faces = {face for face in bm.faces if face.select}

	if len(selected_faces) == 0:
		self.report({'ERROR_INVALID_INPUT'}, "It's not possible to perform the unwrap on loose edges" )
		return

	for edge in selected_edges:
		edge.seam = True

	# "Follow active quad" kind of unwrap
	bpy.context.scene.tool_settings.use_uv_select_sync = False

	bpy.ops.mesh.select_all(action='DESELECT')
	bpy.ops.uv.select_all(action='DESELECT')
	for face in selected_faces:
		face.select = True
		for loop in face.loops:
			loop[uv_layers].select = True

	bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=padding)


	# Rectify the unwrapped islands
	islands = utilities_uv.splittedSelectionByIsland(bm, uv_layers, selected_faces)

	for island in islands:
		unrectified_faces = set()
		rectified_faces = set()
		count = 3
		face_loops = {face : [loop for loop in face.loops] for face in island}
		active = {bm.faces.active}

		# Repeat Rectify until the result is not self-overlapping; max 3 iterations
		while count > 0:
			if count == 3:
				unrectified_faces = op_rectify.main(me, bm, uv_layers, island, face_loops, return_discarded_faces=True)
				rectified_faces = island.difference(unrectified_faces)
				for face in unrectified_faces:
					face.select_set(False)
			else:
				for f in rectified_faces:
					if f not in active:
						bm.faces.active = f
						active.add(f)
						break
				bpy.ops.mesh.select_all(action='DESELECT')
				for face in rectified_faces:
					face.select_set(True)
					for loop in face.loops:
						loop[uv_layers].select = True
				bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=padding)
				op_rectify.main(me, bm, uv_layers, island, face_loops)

			bpy.ops.uv.select_all(action='DESELECT')
			bpy.ops.uv.select_overlap(extend=False)
			for f in rectified_faces:
				if f.loops[0][uv_layers].select:
					count -= 1
				else:
					count = 0
				break

		# Reproject ngons and triangular faces
		if unrectified_faces:
			bpy.ops.mesh.select_all(action='DESELECT')
			for face in unrectified_faces:
				face.select_set(True)
				for loop in face.loops:
					loop[uv_layers].select = True
			bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=padding)


	# Restore selection
	for face in selected_faces:
		face.select_set(True)
		for loop in face.loops:
			loop[uv_layers].select = True

	if is_sync:
		bpy.context.scene.tool_settings.use_uv_select_sync = True


bpy.utils.register_class(op)
