import bpy
import bmesh

from mathutils import Vector
from itertools import chain
from collections import defaultdict
from . import op_meshtex_create
from . import utilities_uv



class op(bpy.types.Operator):
	bl_idname = "uv.textools_relax"
	bl_label = "Relax"
	bl_description = "Relax selected UVs"
	bl_options = {'REGISTER', 'UNDO'}

	iterations : bpy.props.IntProperty(name="Iterations", min=1, max=10, soft_max=4, default=1, description="Repeat Smooth the specified number of times.")
	area_preservation : bpy.props.FloatProperty(name="Area Preservation", min=0.0, max=1.0, default=0.95, description="Factor of rectification of the area shrink caused by the Smooth operator.")

	@classmethod
	def poll(cls, context):
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object.mode != 'EDIT':
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		if not bpy.context.active_object.data.uv_layers:
			return False
		if context.scene.tool_settings.use_uv_select_sync:
			return False
		return True


	def execute(self, context):
		utilities_uv.multi_object_loop(relax, self, context)	
		return {'FINISHED'}



def relax(self, context):
	# UV to temporary mesh
	pre_selection_mode = tuple(bpy.context.scene.tool_settings.mesh_select_mode)
	obj = bpy.context.active_object
	obj_name = bpy.context.active_object.name

	bm, uv_layers, faces_by_island = op_meshtex_create.create_uv_mesh(self, context, obj, sk_create=False, bool_scale=False, delete_unselected=False, restore_selected=True)
	if bm == {'CANCELLED'}:
		return

	temp_obj = bpy.context.active_object
	temp_obj_data_name = temp_obj.data.name

	bpy.ops.mesh.select_all(action='DESELECT')
	for face in chain.from_iterable(faces_by_island):
		face.select_set(True)

	# Smooth mesh
	bpy.ops.mesh.vertices_smooth(factor=0.5, repeat=self.iterations)


	# Mesh to UV
	for faces in faces_by_island:
		if self.area_preservation > 0:
			edge_length = 0
			edge_uv_length = 0
			pre_center = Vector((0.0, 0.0))
			n_loops = 0

		for face in faces:
			face.select = True
			for loop in face.loops:
				if self.area_preservation > 0:
					edge_length += (loop.link_loop_next.vert.co - loop.vert.co).length
					edge_uv_length += (loop.link_loop_next[uv_layers].uv - loop[uv_layers].uv).length
					pre_center += loop[uv_layers].uv
					n_loops += 1
				# Move UVs making sure future UV edges measures will be real
				if loop != face.loops[0]:
					if loop != face.loops[-1]:
						loop[uv_layers].uv = (loop.vert.co.x, loop.vert.co.y)
					else:
						loop[uv_layers].uv = (loop.vert.co.x, loop.vert.co.y)
						face.loops[0][uv_layers].uv = (face.loops[0].vert.co.x, face.loops[0].vert.co.y)

		scale = 1
		if self.area_preservation > 0 and edge_length > 0 and edge_uv_length > 0:
			pre_center /= n_loops
			scale = 1 + (edge_uv_length / edge_length - 1)*self.area_preservation

		if scale != 1:
			for face in faces:
				for loop in face.loops:
					loop[uv_layers].uv = pre_center + (loop[uv_layers].uv - pre_center)*scale


	# Copy and Paste UVs between temporary and original meshes
	copied_uvs = defaultdict(list)
	for face in bm.faces:
		if face.select:
			for loop in face.loops:
				copied_uvs[face.index].append(loop[uv_layers].uv.to_tuple())

	bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
	bpy.ops.object.select_all(action='DESELECT')
	bpy.context.view_layer.objects.active = bpy.data.objects[obj_name]
	bpy.ops.object.mode_set(mode='EDIT', toggle=False)

	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	bm.faces.ensure_lookup_table()
	bm.verts.ensure_lookup_table()
	uv_layers = bm.loops.layers.uv.verify()

	for face_index in copied_uvs:
		for i, loop in enumerate(bm.faces[face_index].loops):
			if loop[uv_layers].select:
				loop[uv_layers].uv = copied_uvs[face_index][i]

	# Remove temporary mesh and restore selection mode altered by meshtex_create
	bpy.data.meshes.remove(bpy.data.meshes[temp_obj_data_name], do_unlink=True)
	bpy.context.scene.tool_settings.mesh_select_mode = pre_selection_mode
