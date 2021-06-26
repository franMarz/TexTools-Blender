import bpy
import bmesh

from . import utilities_ui


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

		#Only in Edit mode
		if bpy.context.active_object.mode != 'EDIT':
			return False

		# Need view Face mode
		if tuple(bpy.context.scene.tool_settings.mesh_select_mode)[1] == False:
			return False

		return True

	def execute(self, context):
		unwrap_edges_pipe(self, context)
		return {'FINISHED'}



def unwrap_edges_pipe(self, context):

	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()

	is_sync = bpy.context.scene.tool_settings.use_uv_select_sync

	contextViewUV = utilities_ui.GetContextViewUV()
	if not contextViewUV:
		self.report({'ERROR_INVALID_INPUT'}, "This tool requires an available UV/Image view.")
		return

	# selected_initial = [edge for edge in bm.edges if edge.select]
	selected_edges = []
	selected_faces = []

	# Extend loop selection
	bpy.ops.mesh.loop_multi_select(ring=False)
	selected_edges = [edge for edge in bm.edges if edge.select]

	if len(selected_edges) == 0:
		self.report({'ERROR_INVALID_INPUT'}, "No edges selected in the view" )
		return

	# Convert linked selection to single UV island
	bpy.ops.mesh.select_linked(delimit=set())
	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
	bpy.ops.uv.textools_unwrap_faces_iron()
	selected_faces = [face for face in bm.faces if face.select]

	if len(selected_faces) == 0:
		self.report({'ERROR_INVALID_INPUT'}, "No faces available" )
		return

	# Mark previous selected edges as Seam
	bpy.ops.mesh.select_all(action='DESELECT')
	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
	for edge in selected_edges:
		edge.select = True
	bpy.ops.mesh.mark_seam(clear=False)

	# Follow active quad unwrap for faces
	bpy.ops.mesh.select_all(action='DESELECT')
	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
	for face in selected_faces:
		face.select = True
	bm.faces.active = selected_faces[0]

	bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.0226216)
	bpy.ops.uv.select_all(action='SELECT')

	bpy.context.scene.tool_settings.use_uv_select_sync = False
	bpy.ops.uv.textools_rectify(contextViewUV)
	if is_sync:
		bpy.context.scene.tool_settings.use_uv_select_sync = True

	# TODO: Restore initial selection
	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')


bpy.utils.register_class(op)
