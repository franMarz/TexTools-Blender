import math
import random
import bpy
import bmesh
import bl_math

from . import utilities_uv
from .utilities_bbox import BBox
from mathutils import Vector


class op(bpy.types.Operator):
	bl_idname = "uv.textools_randomize"
	bl_label = "Randomize Position"
	bl_description = "Randomize selected UV faces position and/or rotation and/or scale"
	bl_options = {'REGISTER', 'UNDO'}
	
	bool_face: bpy.props.BoolProperty(name="Per Face", default=False)
	steps_U: bpy.props.FloatProperty(name="U Steps (Incorrectly works with Within Image Bounds)", default=0, min=0, max=10, soft_min=0, soft_max=1)
	steps_V: bpy.props.FloatProperty(name="V Steps (Incorrectly works with Within Image Bounds)", default=0, min=0, max=10, soft_min=0, soft_max=1)
	strength_U: bpy.props.FloatProperty(name="U Strength", default=1, min=-10, max=10, soft_min=0, soft_max=1)
	strength_V: bpy.props.FloatProperty(name="V Strength", default=1, min=-10, max=10, soft_min=0, soft_max=1)
	rotation: bpy.props.FloatProperty(name="Rotation Strength", default=0, min=-10, max=10, soft_min=0, soft_max=1)
	scale: bpy.props.FloatProperty(name="Scale Strength", default=1, min=0.0, max=10, soft_max=2)
	bool_precenter: bpy.props.BoolProperty(
		name="Pre Center Faces/Islands", default=False, description="Collect all faces/islands around the center of the UV space.")
	bool_bounds: bpy.props.BoolProperty(
		name="Within Image Bounds", default=False, description="Keep the UV faces/islands within the 0-1 UV domain.")
	rand_seed: bpy.props.IntProperty(name="Seed", default=0)

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
		udim_tile = 1001
		column = row = 0
		if self.bool_bounds or self.bool_precenter:
			udim_tile, column, row = utilities_uv.get_UDIM_tile_coords(bpy.context.active_object)

		return main(self, context, udim_tile=udim_tile, column=column, row=row)

	def invoke(self, context, event):
		wm = context.window_manager
		return wm.invoke_props_dialog(self)


def main(self, context, udim_tile=1001, column=0, row=0):
	counter = 0
	selected_obj = utilities_uv.selected_unique_objects_in_mode_with_uv()
	for e1, obj in enumerate(selected_obj, start=100):
		me = obj.data
		bm = bmesh.from_edit_mesh(me)
		uv_layers = bm.loops.layers.uv.verify()
		sync = bpy.context.scene.tool_settings.use_uv_select_sync

		if self.bool_face:
			if sync:
				group = {f for f in bm.faces if f.select}
			else:
				group = utilities_uv.get_selected_uv_faces(bm, uv_layers)
		else:
			group = utilities_uv.get_selected_islands(bm, uv_layers)

		if not group:
			continue

		counter += 1
		bb_general = BBox()
		for e2, f in enumerate(group, start=100):
			seed = e1*e2+self.rand_seed+id(obj)
			random.seed(seed)
			rand_rotation = 2*(random.random()-0.5)
			random.seed(seed+2)
			rand_scale = random.random()-0.5

			f = (f,) if self.bool_face else f

			if self.bool_bounds or self.bool_precenter or self.rotation or self.scale != 1:
				bb = BBox.calc_bbox_uv(f, uv_layers)
				if not bb.is_valid:
					self.report({'WARNING'}, f"The {obj.name} object have UV-Island with zero area")
					continue

				vec_origin = bb.center

				if self.rotation:
					angle = self.rotation * rand_rotation * math.pi
					if utilities_uv.rotate_island(f, uv_layers, angle, vec_origin):
						bb.rotate_expand(angle)

				scale = bl_math.lerp(rand_scale, 1.0, self.scale)
				scale = bl_math.clamp(scale, 0.01, 10.0)

				new_scale = 100
				# Reset the scale to 0.5 to fit in the tile.
				if self.bool_bounds or self.bool_precenter:
					max_length = bb.max_lenght
					max_length_lock = 1.0
					if self.bool_precenter:
						min_stretch = min(abs(self.strength_U), abs(self.strength_V))
						max_length_lock = max(min(1.0, min_stretch), 1e-09)

					if max_length * scale > max_length_lock:
						new_scale = max_length_lock / max_length

				if self.scale != 1 or new_scale < 1:
					# If the scale from random is smaller, we choose it
					scale = min(scale, new_scale)
					scale = Vector((scale, scale))
					utilities_uv.scale_island(f, uv_layers, scale, pivot=vec_origin)
					bb.scale(scale)

				if self.bool_bounds or self.bool_precenter:
					to_center_delta = Vector((0.5, 0.5)) - vec_origin
					utilities_uv.translate_island(f, uv_layers, delta=to_center_delta)
					bb.translate(to_center_delta)
					bb_general.union(bb)

			if self.bool_bounds:
				move = Vector((
					min(bb_general.xmin, abs(1 - bb_general.xmax)) * max(min(self.strength_U, 1), -1),
					min(bb_general.ymin, abs(1 - bb_general.ymax)) * max(min(self.strength_V, 1), -1)
				))
			else:
				move = Vector((self.strength_U, self.strength_V))

			if not (move.x or move.y):
				continue

			random.seed(seed+3)
			rand_move_x = 2*(random.random()-0.5)
			random.seed(seed+4)
			rand_move_y = 2*(random.random()-0.5)

			randmove = Vector((rand_move_x, rand_move_y)) * move
			# ToDo bool_bounds for steps
			if self.steps_U > 1e-05:
				randmove.x = round_threshold(randmove.x, self.steps_U)
			if self.steps_V > 1e-05:
				randmove.y = round_threshold(randmove.y, self.steps_V)

			# if self.bool_bounds:
			# 	pass

			if (not self.bool_bounds and not self.bool_precenter) or udim_tile == 1001:
				utilities_uv.translate_island(f, uv_layers, randmove)
			else:
				utilities_uv.translate_island(f, uv_layers, delta=randmove + Vector((column, row)))

		bmesh.update_edit_mesh(me, loop_triangles=False, destructive=False)

	if counter:
		return {'FINISHED'}

	self.report({'WARNING'}, "No object for randomize.")
	return {'CANCELLED'}

def round_threshold(a, min_clip):
	return round(float(a) / min_clip) * min_clip


bpy.utils.register_class(op)
