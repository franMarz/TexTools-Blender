import bpy
import bmesh
import math

from . import op_select_islands_outline
from . import utilities_uv


class op(bpy.types.Operator):
	bl_idname = "uv.textools_stitch"
	bl_label = "Stitch"
	bl_description = "Stitch other Islands to the selection"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		if bpy.context.area.ui_type != 'UV':
			return False
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object.mode != 'EDIT':
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		if context.scene.tool_settings.use_uv_select_sync:
			return False
		if not bpy.context.object.data.uv_layers:
			return False
		return True

	def execute(self, context):
		utilities_uv.multi_object_loop(main, self, context)
		return {'FINISHED'}


def main(self, context):
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()

	op_select_islands_outline.select_outline(self, context)
	selection = {loop for face in bm.faces if face.select for loop in face.loops if loop[uv_layers].select_edge}

	if not selection:
		return

	selectionFaces = {loop.face for loop in selection}
	selectionFacesTargets = {loop.link_loop_radial_next.face for loop in selection}
	extended_selection = {loop.link_loop_radial_next for loop in selection}
	extended_selection.update(selection)

	# Store selection
	utilities_uv.selection_store(bm, uv_layers)

	islands, target_islands = utilities_uv.getSelectedUnselectedIslands(bm, uv_layers, selected_faces=selectionFaces, target_faces=selectionFacesTargets)
	remaining_islands = islands.copy()
	remaining_islands.extend(target_islands)

	if not islands:
		utilities_uv.selection_restore()
		return

	for island in islands:
		del remaining_islands[0]
		if remaining_islands:
			bpy.ops.uv.select_all(action='DESELECT')
			loop1 = next(iter(island)).loops[0]
			loop1[uv_layers].select = True
			bpy.ops.uv.select_linked()

			# Selection original coordinates
			loop2 = loop1.link_loop_next
			coords_before = loop1[uv_layers].uv.copy(), loop2[uv_layers].uv.copy()
			# Stitch
			op_select_islands_outline.select_outline(self, context)
			selectionBorder = {loop for face in island for loop in face.loops if loop[uv_layers].select_edge}
			selectionBorder.intersection_update(extended_selection)

			loopsByTarget = [[] for _ in range(len(remaining_islands))]
			for loop in selectionBorder:
				targetFace = loop.link_loop_radial_next.face
				if targetFace not in island:
					for l, i in zip(loopsByTarget, remaining_islands):
						if targetFace in i:
							l.append(loop)
							break

			for grouped_loops in loopsByTarget:
				bpy.ops.uv.select_all(action='DESELECT')
				for base_loop in grouped_loops:
					base_loop[uv_layers].select = True
					base_loop[uv_layers].select_edge = True

				bpy.ops.uv.stitch(use_limit=False, snap_islands=True, midpoint_snap=False, clear_seams=True, mode='EDGE')

			# Relocate selection
			coords_after = loop1[uv_layers].uv, loop2[uv_layers].uv
			if coords_before != coords_after:
				loop1[uv_layers].select = True
				bpy.ops.uv.select_linked()
				new_island = utilities_uv.get_selected_uv_faces(bm, uv_layers)

				V1 = coords_before[1] - coords_before[0]
				V2 = coords_after[1] - coords_after[0]
				angle = math.atan2(V1.cross(V2), V1.dot(V2))

				vec_origin = coords_after[0]
				displace = coords_before[0] - coords_after[0]

				utilities_uv.rotate_island(new_island, uv_layers, angle, vec_origin)
				utilities_uv.translate_island(new_island, uv_layers, displace)

	# Restore selection
	utilities_uv.selection_restore()
