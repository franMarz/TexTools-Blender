import bpy
import bmesh

from . import utilities_uv



class op(bpy.types.Operator):
	bl_idname = "uv.textools_select_islands_identical"
	bl_label = "Select similar"
	bl_description = "Select UV islands with similar topology with respect to the selected UVs"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		if bpy.context.area.ui_type != 'UV':
			return False
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		if bpy.context.active_object.mode != 'EDIT':
			return False
		if not bpy.context.object.data.uv_layers:
			return False
		return True


	def execute(self, context):
		island_stats_source_list = utilities_uv.multi_object_loop(island_find, self, context, need_results = True)

		if not island_stats_source_list:
			return {'CANCELLED'}
		elif {'CANCELLED'} in island_stats_source_list:
			return {'CANCELLED'}
		elif len(list(filter(bool, island_stats_source_list))) > 1:
			self.report({'ERROR_INVALID_INPUT'}, "Please select only 1 UV Island")
			return {'CANCELLED'}

		island = None
		for island_stats_source in island_stats_source_list:
			if island_stats_source:
				island = island_stats_source
				break
		if island:
			utilities_uv.multi_object_loop(swap, self, context, island)

		return {'FINISHED'}



def island_find(self, context):
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()

	islands = utilities_uv.get_selected_islands(bm, uv_layers, selected=False, extend_selection_to_islands=True)
	if not islands:
		return {}
	if len(islands) > 1:
		self.report({'ERROR_INVALID_INPUT'}, "Please select only 1 UV Island")
		return {'CANCELLED'}

	island_stats_source = Island_stats(bm, islands[0])
	return island_stats_source



def swap(self, context, island_stats_source):
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()
	sync = bpy.context.scene.tool_settings.use_uv_select_sync
	if sync:
		selection_mode = tuple(bpy.context.scene.tool_settings.mesh_select_mode)
	else:
		selection_mode = bpy.context.scene.tool_settings.uv_select_mode

	if sync:
		bpy.ops.mesh.select_all(action='SELECT')
	else:
		bpy.ops.uv.select_all(action='SELECT')
	islands_all = utilities_uv.get_selected_islands(bm, uv_layers)

	islands_equal = []
	for island in islands_all:
		island_stats = Island_stats(bm, island)

		if island_stats_source.isEqual(island_stats):
			islands_equal.append(island)

	if sync:
		bpy.ops.mesh.select_all(action='DESELECT')
		bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
		for island in islands_equal:
			for face in island:
				face.select_set(True)
	else:
		bpy.ops.uv.select_all(action='DESELECT')
		for island in islands_equal:
			for face in island:
				for loop in face.loops:
					loop[uv_layers].select = True


	if sync:
		bpy.context.scene.tool_settings.mesh_select_mode = selection_mode
	else:
		# Workaround for selection not flushing properly from loops to EDGE Selection Mode, apparently since UV edge selection support was added to the UV space
		bpy.ops.uv.select_mode(type='VERTEX')
		bpy.context.scene.tool_settings.uv_select_mode = selection_mode



class Island_stats:
	countFaces = 0
	countVerts = 0
	area = 0
	countLinkedEdges = 0
	countLinkedFaces = 0


	def __init__(self, bm, faces):
		# Collect topology stats
		self.countFaces = len(faces)

		verts = {v for f in faces for v in f.verts}
		self.countVerts = len(verts)
		for vert in verts:
			self.countLinkedEdges += len(vert.link_edges)
			self.countLinkedFaces += len(vert.link_faces)

		for face in faces:
			self.area += face.calc_area()

	
	def isEqual(self, other):
		if self.countVerts != other.countVerts:
			return False
		if self.countFaces != other.countFaces:
			return False
		if self.countLinkedEdges != other.countLinkedEdges:
			return False
		if self.countLinkedFaces != other.countLinkedFaces:
			return False

		# area needs to be 90%+ identical
		if min(self.area, other.area)/max(self.area, other.area) < 0.7:
			return False
		return True


bpy.utils.register_class(op)
