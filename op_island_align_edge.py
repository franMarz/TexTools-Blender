import bpy
import bmesh
import math

from . import utilities_uv

class op(bpy.types.Operator):
	bl_idname = "uv.textools_island_align_edge"
	bl_label = "Align Island by Edge"
	bl_description = "Align Islands by selected Edge"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		if bpy.context.active_object.mode != 'EDIT':
			return False
		if bpy.context.scene.tool_settings.use_uv_select_sync:
			return False
		if bpy.context.scene.tool_settings.uv_select_mode not in ('EDGE', 'VERTEX'):
			return False
		return True

	def execute(self, context):
		return main(self, context)

def main(self, context):
	counter = 0
	for obj in utilities_uv.selected_unique_objects_in_mode_with_uv():
		bm = bmesh.from_edit_mesh(obj.data)
		uv_layers = bm.loops.layers.uv.verify()

		if not any(l[uv_layers].select_edge for f in bm.faces for l in f.loops):
			continue

		counter += 1
		for island in utilities_uv.get_selected_islands(bm, uv_layers, selected=False):
			luvs = (l for f in island for l in f.loops)
			for l in luvs:
				if l[uv_layers].select_edge:
					uv_vert0 = l[uv_layers].uv
					uv_vert1 = l.link_loop_next[uv_layers].uv
					diff = uv_vert1 - uv_vert0
					current_angle = math.atan2(diff.x, diff.y)
					angle_to_rotate = round(current_angle / (math.pi / 2)) * (math.pi / 2) - current_angle
					pivot = uv_vert0 + diff/2
					utilities_uv.rotate_island(island, uv_layers, angle_to_rotate, pivot)
					break
		bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)

	if counter:
		return {'FINISHED'}

	self.report({'WARNING'}, "No object to align")
	return {'CANCELLED'}
