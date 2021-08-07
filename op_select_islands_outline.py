import bpy
import bmesh

from . import utilities_uv



class op(bpy.types.Operator):
	bl_idname = "uv.textools_select_islands_outline"
	bl_label = "Select Island outline"
	bl_description = "Select island edge bounds"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		if bpy.context.area.type != 'IMAGE_EDITOR':
			return False
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object.mode != 'EDIT':
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		if not bpy.context.object.data.uv_layers:
			return False
		return True


	def execute(self, context):
		utilities_uv.multi_object_loop(select_outline, self, context)
		return {'FINISHED'}



def select_outline(self, context, bm=None, uv_layers=None):
	if bm is None:
		bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
		uv_layers = bm.loops.layers.uv.verify()

	sync = bpy.context.scene.tool_settings.use_uv_select_sync

	if sync:
		selected_loops = {l for e in bm.edges for l in e.link_loops if e.select}
	else:
		selected_loops = {l for f in bm.faces for l in f.loops if l[uv_layers].select and l.link_loop_next[uv_layers].select and l.edge.select}

	# Store previous edge seams
	edges_seam = {l.edge for l in selected_loops if l.edge.seam}
	
	# Clear original seams
	for edge in edges_seam:
		edge.seam = False

	bpy.ops.uv.seams_from_islands(mark_seams=True, mark_sharp=False)

	if sync:
		boundary_edges = {l.edge for l in selected_loops if l.edge.seam or l.edge.is_boundary}
	else:
		boundary_loops = {l for l in selected_loops if l.edge.seam or l.edge.is_boundary}
		boundary_edges = {l.edge for l in boundary_loops}

	# Select bound edges from edges marked as seams and edge boundaries
	if sync:
		bpy.ops.mesh.select_all(action='DESELECT')
		bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
		for edge in boundary_edges:
			edge.select_set(True)
	else:
		bpy.ops.uv.select_all(action='DESELECT')
		bpy.context.scene.tool_settings.uv_select_mode = 'EDGE'
		for loop in boundary_loops:
			loop[uv_layers].select = True
			loop.link_loop_next[uv_layers].select = True

	# Restore seam selection
	for edge in boundary_edges:
		edge.seam = False
	for edge in edges_seam:
		edge.seam = True


bpy.utils.register_class(op)
