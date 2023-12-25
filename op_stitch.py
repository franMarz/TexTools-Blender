import bpy
import bmesh
import numpy as np

from mathutils import Vector

from . import op_select_islands_outline
from . import utilities_uv
from . import settings



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

	if selection:
		selectionFaces = {loop.face for loop in selection}
		selectionFacesTargets = {loop.link_loop_radial_next.face for loop in selection}
		extended_selection = {loop.link_loop_radial_next for loop in selection}
		extended_selection.update(selection)

		#Store selection
		utilities_uv.selection_store(bm, uv_layers)

		islands, target_islands = utilities_uv.getSelectedUnselectedIslands(bm, uv_layers, selected_faces=selectionFaces, target_faces=selectionFacesTargets)
		remaining_islands = islands.copy()
		remaining_islands.extend(target_islands)

		if islands:
			for island in islands:
				del remaining_islands[0]
				if remaining_islands:
					bpy.ops.uv.select_all(action='DESELECT')
					loop1 = next(iter(island)).loops[0]
					loop1[uv_layers].select=True
					bpy.ops.uv.select_linked()

					# Selection original coordinates
					loop2 = loop1.link_loop_next
					coords_before = (Vector((loop1[uv_layers].uv.x, loop1[uv_layers].uv.y)), Vector((loop2[uv_layers].uv.x, loop2[uv_layers].uv.y)))

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
									#l.append(loop.link_loop_next)
									break

					for grouped_loops in loopsByTarget:
						bpy.ops.uv.select_all(action='DESELECT')
						for base_loop in grouped_loops:
							base_loop[uv_layers].select = True
							base_loop[uv_layers].select_edge = True

						bpy.ops.uv.stitch(use_limit=False, snap_islands=True, midpoint_snap=False, clear_seams=True, mode='EDGE')

					loop1[uv_layers].select=True
					bpy.ops.uv.select_linked()

					# Relocate selection
					coords_after = (Vector((loop1[uv_layers].uv.x, loop1[uv_layers].uv.y)), Vector((loop2[uv_layers].uv.x, loop2[uv_layers].uv.y)))
					if coords_before != coords_after:
						displace =  coords_before[0] - coords_after[0]
						
						bpy.ops.transform.translate(value=(displace.x, displace.y, 0), use_proportional_edit=False)

						bpy.context.space_data.pivot_point = 'CURSOR'
						bpy.context.space_data.cursor_location = (coords_before[0])

						V1 = coords_before[1] - coords_before[0]
						V2 = coords_after[1] - coords_after[0]
						angl = np.math.atan2(np.linalg.det([V1,V2]),np.dot(V1,V2))

						# bpy.ops.transform.rotate behaves differently in the UV Editor on every version of Blender
						bversion = settings.bversion
						if bversion == 2.80 or bversion == 2.81 or bversion == 2.82 or bversion == 2.90:
							angl = -angl

						bpy.ops.transform.rotate(value=angl, orient_axis='Z', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, False), mirror=False, use_proportional_edit=False)

		#Restore selection
		utilities_uv.selection_restore()


bpy.utils.register_class(op)
