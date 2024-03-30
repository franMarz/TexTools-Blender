import bpy
import bmesh
import mathutils

from . import utilities_uv


class op(bpy.types.Operator):
	bl_idname = "uv.textools_select_zero"
	bl_label = "Select Degenerate"
	bl_description = "Select degenerate UVs (zero area UV triangles)"
	bl_options = {'REGISTER', 'UNDO'}

	precision: bpy.props.FloatProperty(name='Precision', default=0.00005, min=0, step=0.00001, precision=7)

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
		return select_zero(self)


def select_zero(self):
	bpy.ops.uv.select_all(action='DESELECT')
	sync = bpy.context.scene.tool_settings.use_uv_select_sync
	premode = bpy.context.scene.tool_settings.uv_select_mode

	counter = 0
	for obj in utilities_uv.selected_unique_objects_in_mode_with_uv():
		bm = bmesh.from_edit_mesh(obj.data)
		uv_layer = bm.loops.layers.uv.verify()
		for f in bm.faces:
			for l in f.loops:
				l1 = l[uv_layer].uv
				l2 = l.link_loop_next[uv_layer].uv
				l3 = l.link_loop_prev[uv_layer].uv
				area = mathutils.geometry.area_tri(l1, l2, l3)
				thres = max((l1-l2).length, (l2-l3).length, (l1-l3).length)**2 * self.precision
				if area < thres:
					if sync:
						f.select_set(True)
					else:
						for i in f.loops:
							i[uv_layer].select = True
					counter += 1
					break
				elif len(f.loops) == 3:
					break

	if not counter:
		self.report({'INFO'}, f'Degenerate triangles not found')
		return {'FINISHED'}

	# Workaround to flush the selected UVs from loops to faces
	if not sync:
		if premode == 'EDGE':
			premode = 'VERTEX'
		bpy.ops.uv.select_mode(type='VERTEX')
		if premode == 'ISLAND':
			premode = 'FACE'
		bpy.ops.uv.select_mode(type=premode)

	self.report({'WARNING'}, f'Detected {counter} degenerate triangles')
	return {'FINISHED'}
