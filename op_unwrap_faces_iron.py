import bpy
import bmesh

from mathutils import Vector
from . import utilities_uv
from . import utilities_ui



class op(bpy.types.Operator):
	bl_idname = "uv.textools_unwrap_faces_iron"
	bl_label = "Iron"
	bl_description = "Unwrap selected faces into a single UV Island"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		if bpy.context.active_object.mode != 'EDIT':
			return False
		return True


	def execute(self, context):
		udim_tile, column, row = utilities_uv.get_UDIM_tile_coords(bpy.context.active_object)
		utilities_uv.multi_object_loop(main, self, context, udim_tile, column, row)
		return {'FINISHED'}



def main(self, context, udim_tile, column, row):
	pre_selection_mode = tuple(bpy.context.scene.tool_settings.mesh_select_mode)
	me = bpy.context.active_object.data
	bm = bmesh.from_edit_mesh(me)

	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
	bpy.ops.mesh.mark_seam(clear=True)

	selected_faces = [f for f in bm.faces if f.select]

	# Hard edges to seams
	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
	bpy.ops.mesh.region_to_loop()
	bpy.ops.mesh.mark_seam(clear=False)

	seams = False
	for face in selected_faces:
		face.select_set(True)
		if not seams:
			for edge in face.edges:
				if edge.seam:
					seams = True
					break
	if not seams:
		self.report({'INFO'}, "Unwrap not possible; don't select the entire object if it is manifold")
		return

	padding = utilities_ui.get_padding()
	bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=padding)

	# Move to active UDIM Tile TODO unwrap in the active UDIM Tile when implemented in Blender master (watch out for versioning)
	uv_layers = bm.loops.layers.uv.verify()

	if udim_tile != 1001:
		for face in selected_faces:
			for loop in face.loops:
				loop[uv_layers].uv += Vector((column, row))

	bpy.context.scene.tool_settings.mesh_select_mode = pre_selection_mode


bpy.utils.register_class(op)
