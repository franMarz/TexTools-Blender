import bpy
import bmesh

from . import utilities_uv



class op(bpy.types.Operator):
	bl_idname = "uv.textools_select_islands_flipped"
	bl_label = "Select Flipped"
	bl_description = "Select flipped UV faces"
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
		utilities_uv.multi_object_loop(select_flipped, context)
		return {'FINISHED'}



def select_flipped(context):
	obj = bpy.context.active_object
	bm = bmesh.from_edit_mesh(obj.data)
	uv_layers = bm.loops.layers.uv.verify()
	sync = bpy.context.scene.tool_settings.use_uv_select_sync

	bpy.ops.uv.select_all(action='DESELECT')
	faces = [f for f in bm.faces]

	flipped_faces = []
	for f in faces:
		area = 0.0
		uvs = [l[uv_layers].uv for l in f.loops]
		for i in range(len(uvs)):
			uv1 = uvs[i - 1]
			uv2 = uvs[i]
			a = uv1.x * uv2.y - uv1.y * uv2.x
			area = area + a
		if area < 0:
			# clock-wise
			flipped_faces.append(f)

	for f in flipped_faces:
		if sync:
			f.select_set(True)
		else:
			for l in f.loops:
				l[uv_layers].select = True

	# Workaround to flush the selected UVs from loops to faces
	if not sync:
		bpy.ops.uv.select_mode(type='VERTEX')
		bpy.ops.uv.select_mode(type='FACE')


bpy.utils.register_class(op)
