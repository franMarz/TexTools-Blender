import bpy
import bmesh

from . import utilities_uv
from . import op_select_islands_outline


class op(bpy.types.Operator):
	bl_idname = "uv.textools_meshtex_create"
	bl_label = "UV Mesh"
	bl_description = "Create a new UV Mesh from your selected object"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		if not bpy.context.object.data.uv_layers:
			return False
		return True


	def execute(self, context):
		return create_uv_mesh(self, context, bpy.context.active_object)



def create_uv_mesh(self, context, obj, sk_create=True, bool_scale=True, delete_unselected=True, restore_selected=False):
	# New object management
	mode = bpy.context.active_object.mode
	bpy.ops.object.mode_set(mode='OBJECT')
	bpy.ops.object.select_all(action='DESELECT')

	mesh_obj = obj.copy()
	mesh_obj.data = obj.data.copy()
	obj.users_collection[0].objects.link(mesh_obj)

	mesh_obj.select_set( state = True, view_layer = None)
	bpy.context.view_layer.objects.active = mesh_obj
	
	mesh_obj.name = obj.name + "_UV_Mesh"

	# Shape Keys management
	if mesh_obj.data.shape_keys:
		if len(mesh_obj.data.shape_keys.key_blocks) > 1:
			for i in range(len(mesh_obj.data.shape_keys.key_blocks)):
				bpy.context.object.active_shape_key_index = 0
				bpy.ops.object.shape_key_remove(all=False)
	if sk_create:
		mesh_obj.shape_key_add(name="model", from_mix=True)
		mesh_obj.shape_key_add(name="uv", from_mix=True)
		mesh_obj.active_shape_key_index = 1
		bpy.context.active_object.active_shape_key.value = 1

	bpy.ops.object.mode_set(mode='EDIT')

	pre_sync = bpy.context.scene.tool_settings.use_uv_select_sync
	if pre_sync == True:
		bpy.context.scene.tool_settings.use_uv_select_sync = False
		bpy.ops.uv.select_all(action='SELECT')

	# Select all if OBJECT mode
	if mode == 'OBJECT':
		bpy.ops.mesh.select_all(action='SELECT')
		bpy.ops.uv.select_all(action='SELECT')

	# Select only UV faces
	bpy.ops.uv.select_split()

	bm = bmesh.from_edit_mesh(mesh_obj.data)
	uv_layers = bm.loops.layers.uv.verify()

	faces_by_island = utilities_uv.splittedSelectionByIsland(bm, uv_layers, restore_selected=True)

	if not faces_by_island:
		bpy.data.objects.remove(mesh_obj, do_unlink=True)
		obj.select_set( state = True, view_layer = None)
		bpy.context.view_layer.objects.active = obj
		bpy.context.scene.tool_settings.use_uv_select_sync = pre_sync
		bpy.ops.object.mode_set(mode=mode)
		if not restore_selected:
			return {'CANCELLED'}
		else:	# For the Relax operator
			return {'CANCELLED'}, None, None

	if delete_unselected:
		if mode != 'OBJECT':
			delete_faces = list({face for faces in faces_by_island for face in faces}.symmetric_difference(bm.faces))
			if delete_faces:
				bmesh.ops.delete(bm, geom=delete_faces, context='FACES')
	else:	# Needed for the Relax operator
	 	#for face in {face for faces in faces_by_island for face in faces}.symmetric_difference(bm.faces):
		#	if face.select:
		#		face.select_set(False)
		#bpy.ops.mesh.split()
		bpy.ops.mesh.select_all(action='DESELECT')
		selection_loops = {loop for faces in faces_by_island for face in faces for loop in face.loops}
		for faces in faces_by_island:
			for face in faces:
				for edge in face.edges:
					if not set(edge.link_loops).issubset(selection_loops):
						edge.select_set(True)
		bpy.ops.mesh.edge_split(type='EDGE')
		bmesh.update_edit_mesh(mesh_obj.data)
		bpy.ops.mesh.select_all(action='SELECT')	#TODO REFINE

	bpy.context.scene.tool_settings.use_uv_select_sync = True
	op_select_islands_outline.select_outline(self, context, bm, uv_layers)
	bpy.ops.mesh.edge_split(type='EDGE')
	bmesh.update_edit_mesh(mesh_obj.data)

	bpy.context.scene.tool_settings.use_uv_select_sync = False
	bpy.ops.mesh.select_all(action='SELECT')	#TODO REFINE
	if pre_sync == True:
		bpy.ops.uv.select_all(action='SELECT')

	if bool_scale:
		length_view = 0
		length_uv = 0
		for faces in faces_by_island:
			for face in faces:
				length_uv += (face.loops[0].link_loop_next[uv_layers].uv - face.loops[0][uv_layers].uv).length
				length_view += face.loops[0].edge.calc_length()

	# Reshape mesh to mimic UVs
	for faces in faces_by_island:
		for face in faces:
			for loop in face.loops:
				loop.vert.co = (loop[uv_layers].uv.x, loop[uv_layers].uv.y, 0)

	#Scale
	if bool_scale:
		if length_uv > 0 and length_view > 0:
			scale = length_view / length_uv
		else:
			scale = 1

		scaled_verts = set()
		for faces in faces_by_island:
			for face in faces:
				for loop in face.loops:
					if loop.vert not in scaled_verts:
						loop.vert.co *= scale
						scaled_verts.add(loop.vert)

	#bm.select_flush(True)
	bpy.context.scene.tool_settings.use_uv_select_sync = pre_sync

	if restore_selected:	# For the Relax operator
		bpy.ops.uv.select_all(action='DESELECT')
		for faces in faces_by_island:
			for face in faces:
				for loop in face.loops:
					loop[uv_layers].select = True

	if mode == 'EDIT' and not restore_selected:
		bpy.ops.object.mode_set(mode='OBJECT')
		bpy.ops.object.mode_set(mode=mode)
	else:
		bpy.ops.object.mode_set(mode=mode)


	if not restore_selected:
		return {'FINISHED'}
	else:	# For the Relax operator
		return bm, uv_layers, faces_by_island


bpy.utils.register_class(op)
