import bpy
import bmesh

from . import utilities_uv
from . import utilities_ui

class op(bpy.types.Operator):
	bl_idname = "uv.textools_uv_unfold"
	bl_label = "Unfold"
	bl_description = "Unfold selected uv's"
	bl_options = {'UNDO'}
	
	axis : bpy.props.StringProperty(name="axis", default="xy")

	@classmethod
	def poll(cls, context):

		if not bpy.context.active_object:
			return False

		if bpy.context.active_object.type != 'MESH':
			return False

		#Only in Edit mode
		if bpy.context.active_object.mode != 'EDIT':
			return False

		return True

	def execute(self, context):
		utilities_uv.multi_object_loop(main, context, self.axis)
		return {'FINISHED'}


def main(context, axis):
	print("operator_uv_unfold()")

	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()
	
	utilities_uv.selection_store()

	#store pins and edge seams
	edge_seam = []
	for edge in bm.edges:
		edge_seam.append(edge.seam)
		edge.seam = False

	pin_state = []
	uv_coords = []
	for face in bm.faces:
		for loop in face.loops:
			uv = loop[uv_layers]
			pin_state.append(uv.pin_uv)
			uv.pin_uv = not uv.select	
			
			uv_coords.append(uv.uv.copy())
				
	#apply unwrap
	bpy.ops.uv.select_all(action='SELECT')
	bpy.ops.uv.seams_from_islands()

	padding = utilities_ui.get_padding()
	bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=padding)

	#restore pins & edge seams
	index = 0
	for face in bm.faces:
		for loop in face.loops:
			uv = loop[uv_layers]
			uv.pin_uv = pin_state[index]			

			if axis == "x":
				uv.uv.y = uv_coords[index].y			
			elif axis == "y":
				uv.uv.x = uv_coords[index].x			

			index += 1

	for index, edge in enumerate(bm.edges):
		edge.seam = edge_seam[index]
	

	utilities_uv.selection_restore()


bpy.utils.register_class(op)