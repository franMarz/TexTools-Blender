import bpy
import bmesh

from . import utilities_uv
from . import utilities_ui
from mathutils import Vector
from .utilities_bbox import BBox

class op(bpy.types.Operator):
	bl_idname = "uv.textools_uv_unwrap"
	bl_label = "Unwrap"
	bl_description = "Unwrap selected UVs"
	bl_options = {'REGISTER', 'UNDO'}

	axis: bpy.props.StringProperty(name="axis", default='', options={'HIDDEN'})

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
		if not bpy.context.object.data.uv_layers:
			return False
		if bpy.context.scene.tool_settings.use_uv_select_sync:
			return False
		return True

	def execute(self, context):
		main(self, self.axis)
		return {'FINISHED'}


def main(self, axis):
	groups = []
	selected_obj = utilities_uv.selected_unique_objects_in_mode_with_uv()
	for obj in selected_obj:
		bm = bmesh.from_edit_mesh(obj.data)
		uv_layer = bm.loops.layers.uv.verify()
		# selection_store
		sel_states = [(loop[uv_layer].select, loop[uv_layer].select_edge) for face in bm.faces for loop in face.loops]

		# analyze if a full uv-island has been selected.
		full_islands = []
		for island in utilities_uv.get_selected_islands(bm, uv_layer, selected=False, extend_selection_to_islands=True):
			if all(loop[uv_layer].select for face in island for loop in face.loops):
				full_islands.append(list(island))

		# store pins and edge seams
		edge_seam = []
		for edge in bm.edges:
			edge_seam.append(edge.seam)
			edge.seam = False

		# Pin the inverse of the current selection, and cache the uv coords
		pin_state = []
		uv_coords = []
		for face in bm.faces:
			for loop in face.loops:
				uv = loop[uv_layer]
				pin_state.append(uv.pin_uv)
				uv.pin_uv = not uv.select
				if axis:
					uv_coords.append(uv.uv.copy())

		# If entire islands are selected, pin one vert to keep the island somewhat in place,
		# otherwise it can get moved away quite randomly by the uv unwrap method; also store some uvs data to reconstruct orientation
		orient_uvs = []
		if full_islands:
			for island in full_islands:

				x_min = x_max = y_min = y_max = island[0].loops[0][uv_layer]
				x_min.pin_uv = True

				for face in island:
					for loop in face.loops:
						uv = loop[uv_layer]
						if uv.uv.x > x_max.uv.x:
							x_max = uv
						if uv.uv.x < x_min.uv.x:
							x_min = uv
						if uv.uv.y > y_max.uv.y:
							y_max = uv
						if uv.uv.y < y_min.uv.y:
							y_min = uv

				orient_uvs.append((x_min, x_max, y_min, y_max, x_min.uv.copy(), x_max.uv.copy(), y_min.uv.copy(), y_max.uv.copy()))

		groups.append((bm, uv_layer, sel_states, full_islands, edge_seam, pin_state, uv_coords, orient_uvs))

	# apply unwrap
	bpy.ops.uv.select_all(action='SELECT')
	bpy.ops.uv.seams_from_islands()

	padding = utilities_ui.get_padding()
	bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=padding)

	# try to reconstruct the original orientation of the uv island
	up = Vector((0, 1.0))
	for bm, uv_layer, sel_states, full_islands, edge_seam, pin_state, uv_coords, orient_uvs in groups:
		for bbox, island in zip(orient_uvs, full_islands):
			x_min, x_max, y_min, y_max, x_min_coord, x_max_coord, y_min_coord, y_max_coord = bbox
			prev_bbox = BBox(x_min_coord.x, x_max_coord.x, y_min_coord.y, y_max_coord.y)

			island_bbox = BBox.calc_bbox_uv(island, uv_layer)
			pivot = island_bbox.center

			# Case: Normal
			if prev_bbox.max_lenght > 0.0002 and prev_bbox.min_lenght > 2e-08:  # Zero area island protection
				intial_x_axis = x_min_coord - x_max_coord
				intial_x_angle = up.angle_signed(intial_x_axis)

				axis_x_current = x_min.uv - x_max.uv
				current_x_angle = up.angle_signed(axis_x_current)

				intial_y_axis = y_min_coord - y_max_coord
				intial_y_angle = up.angle_signed(intial_y_axis)

				axis_y_current = y_min.uv - y_max.uv
				current_y_angle = up.angle_signed(axis_y_current)

				angle_x = intial_x_angle - current_x_angle
				angle_y = intial_y_angle - current_y_angle
				angle = min(angle_x, angle_y)

				utilities_uv.rotate_island(island, uv_layer, angle, pivot)

				# keep it the same size
				scale_x = intial_x_axis.length / axis_x_current.length
				scale_y = intial_y_axis.length / axis_y_current.length
				scale = min([scale_x, scale_y], key=lambda x: abs(x-1.0))  # pick scale closer to 1.0

				utilities_uv.scale_island(island, uv_layer, Vector((scale, scale)), pivot)
			# case: when the island had zero area, but was stretched on the axis
			elif prev_bbox.max_lenght > 0.0001 and prev_bbox.min_lenght < 2e-09:
				scale = prev_bbox.max_lenght / island_bbox.max_lenght
				utilities_uv.scale_island(island, uv_layer, Vector((scale, scale)), pivot)
				self.report({'INFO'}, f'A stretched island with zero area has been found, and successfully deployed')
			# case: when area zero
			elif island_bbox.area > 0.2:
				scale = 0.2/island_bbox.max_lenght
				utilities_uv.scale_island(island, uv_layer, Vector((scale, scale)), pivot)
				self.report({'WARNING'}, f'UV Island with zero area was detected and scaled to 0.2.')
			# case: when island small
			elif island_bbox.area < 1e-05:
				length = prev_bbox.max_lenght
				if prev_bbox.max_lenght == 0:
					length = island_bbox.max_lenght
				sum_length = 0
				count_valid_bbox = 0
				# Finding the average size of other islands, and scaling to their size
				for orient_uv in orient_uvs:
					x_min, x_max, y_min, y_max = orient_uv[:4]
					all_bbox = BBox(x_min.uv.x, x_max.uv.x, y_min.uv.y, y_max.uv.y)
					max_length = all_bbox.max_lenght
					if max_length > 1e-05:
						sum_length += max_length
						count_valid_bbox += 1
				if count_valid_bbox:
					avg_length = sum_length / count_valid_bbox
					scale = avg_length / length
					self.report(
						{'WARNING'}, f"UV Island with a small area ({island_bbox.area}) was found and scaled "
						f"to the average size ({scale}) of the other islands. To validate the unwrap, try again.")
				else:
					scale = 0.2 / length
					self.report({'WARNING'}, f'UV Island with small area ({island_bbox.area}) was detected and scaled to 0.2')
				utilities_uv.scale_island(island, uv_layer, Vector((scale, scale)), pivot)
			else:
				self.report({'WARNING'}, f'Island not have boundary edges or other')

			# move back into place
			delta = x_min_coord - x_min.uv
			utilities_uv.translate_island(island, uv_layer, delta)

		# restore selections, pins & edge seams
		index = 0
		for face in bm.faces:
			for loop in face.loops:
				uv = loop[uv_layer]
				uv.pin_uv = pin_state[index]

				# apply axis constraint
				if axis:
					if axis == "x":
						uv.uv.y = uv_coords[index].y
					else:
						uv.uv.x = uv_coords[index].x
				index += 1

		for edge, seam in zip(bm.edges, edge_seam):
			edge.seam = seam

		# restore selection
		luvs = (loop[uv_layer] for face in bm.faces for loop in face.loops)
		for luv, sel_state in zip(luvs, sel_states):
			luv.select, luv.select_edge = sel_state

	for obj in selected_obj:
		bmesh.update_edit_mesh(obj.data)


bpy.utils.register_class(op)
