import bpy
import bmesh

from . import utilities_uv
import imp
imp.reload(utilities_uv)



class op(bpy.types.Operator):
	bl_idname = "uv.textools_select_islands_flipped"
	bl_label = "Select Flipped"
	bl_description = "Select all flipped UVs"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		if bpy.context.active_object.mode != 'EDIT':
			return False
		if bpy.context.area.type != 'IMAGE_EDITOR':
			return False
		if not bpy.context.object.data.uv_layers:
			return False
		if bpy.context.scene.tool_settings.use_uv_select_sync:
			return False
		return True


	def execute(self, context):
		utilities_uv.multi_object_loop(select_flipped, context)
		return {'FINISHED'}



def select_flipped(context):
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()

	bpy.ops.uv.select_all(action='DESELECT')

	for face in bm.faces:
		# Using 'Sum of Edges' to detect counter clockwise https://stackoverflow.com/questions/1165647/how-to-determine-if-a-list-of-polygon-points-are-in-clockwise-order
		sum = 0
		count = len(face.loops)
		for i in range(count):
			uv_A = face.loops[i][uv_layers].uv
			uv_B = face.loops[(i+1)%count][uv_layers].uv
			sum += (uv_B.x - uv_A.x) * (uv_B.y + uv_A.y)

		if sum > 0:
			# Flipped
			for loop in face.loops:
				loop[uv_layers].select = True


bpy.utils.register_class(op)
