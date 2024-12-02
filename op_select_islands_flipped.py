import bpy
import bmesh

from . import utilities_uv


class op(bpy.types.Operator):
	bl_idname = "uv.textools_select_islands_flipped"
	bl_label = "Select Flipped"
	bl_description = "Detect flipped UV faces across all polygons (even hidden) of the selected objects"
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
		return select_flipped(self)

def select_flipped(self):
	bpy.ops.uv.select_all(action='DESELECT')
	sync = bpy.context.scene.tool_settings.use_uv_select_sync
	premode = bpy.context.scene.tool_settings.uv_select_mode

	if not sync and premode == 'VERTEX':
		bpy.ops.uv.select_mode(type='FACE')

	selected_objs = utilities_uv.selected_unique_objects_in_mode_with_uv()
	counter = 0
	for obj in selected_objs:
		bm = bmesh.from_edit_mesh(obj.data)
		uv_layer = bm.loops.layers.uv.verify()
		for f in bm.faces:
			area = 0.0
			uvs = [l[uv_layer].uv for l in f.loops]
			for i in range(len(uvs)):
				area += uvs[i - 1].cross(uvs[i])
			if area < 0:
				counter += 1
				if sync:
					f.select_set(True)
				else:
					for l in f.loops:
						l[uv_layer].select = True

	if not counter:
		self.report({'INFO'}, 'Flipped faces not found')
		bpy.ops.uv.select_mode(type=premode)
		return {'CANCELLED'}

	# Workaround to flush the selected UVs from loops to faces
	if not sync:
		bpy.ops.uv.select_mode(type='VERTEX')
		sel_mode = 'FACE' if premode == 'ISLAND' else premode
		bpy.ops.uv.select_mode(type=sel_mode)

	self.report({'WARNING'}, f'Detected {counter} flipped UV faces (THE AFFECTED MESH POLYGONS MAY BE HIDDEN OR UNSELECTED!)')
	return {'FINISHED'}
