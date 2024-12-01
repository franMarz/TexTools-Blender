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
	bl_label = "Randomize"
	bl_description = "Randomize selected UV islands or faces"
	bl_options = {'REGISTER', 'UNDO'}
	
	bool_face: bpy.props.BoolProperty(name="Per Face", default=False)
	round_mode: bpy.props.EnumProperty(name="Round Mode", default='OFF', items=(('OFF', "Off", ""), ('INT', "Int", ""), ('STEPS', "Steps", "")))
	steps: bpy.props.FloatVectorProperty(
		name="Steps", description="Incorrectly works with Within Image Bounds",
		default=(0, 0), min=0, max=10, soft_min=0, soft_max=1, size=2, subtype='XYZ')
	strength: bpy.props.FloatVectorProperty(name="Strength", default=(1, 1), min=-10, max=10, soft_min=0, soft_max=1, size=2, subtype='XYZ')
	rotation: bpy.props.FloatProperty(
		name="Rotation Range", default=0, min=0, soft_max=math.pi*2, subtype='ANGLE',
		update=lambda self, _: setattr(self, 'rotation_steps', self.rotation) if self.rotation < self.rotation_steps else None)
	rotation_steps: bpy.props.FloatProperty(
		name="Rotation Steps", default=0, min=0, max=math.pi, subtype='ANGLE',
		update=lambda self, _: setattr(self, 'rotation', self.rotation_steps) if self.rotation < self.rotation_steps else None)
	scale_factor: bpy.props.FloatProperty(name="Scale Factor", default=0, min=0, soft_max=1, subtype='FACTOR')
	min_scale: bpy.props.FloatProperty(
		name="Min Scale", default=0.5, min=0, max=10, soft_min=0.1, soft_max=2,
		update=lambda self, _: setattr(self, 'max_scale', self.min_scale) if self.max_scale < self.min_scale else None)
	max_scale: bpy.props.FloatProperty(
		name="Max Scale", default=2, min=0, max=10, soft_min=0.1, soft_max=2,
		update=lambda self, _: setattr(self, 'min_scale', self.max_scale) if self.max_scale < self.min_scale else None)
	bool_bounds: bpy.props.BoolProperty(name="Within Image Bounds", default=False, description="Keep the UV faces/islands within the 0-1 UV domain")
	bool_bounds_scaling: bpy.props.BoolProperty(name="Scale Within Image Bounds", default=False, description="Scale islands within the 0-1 UV domain when necessary")
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

	def draw(self, context):
		layout = self.layout
		for prop in self.__annotations__:
			if prop == 'steps' and self.round_mode != 'STEPS':
				continue
			elif prop in ('min_scale', 'max_scale') and self.scale_factor == 0:
				continue
			elif prop == 'rotation_steps' and self.rotation == 0:
				continue
			elif prop == 'bool_bounds_scaling' and not self.bool_bounds:
				continue
			layout.prop(self, prop)

	def execute(self, context):
		udim_tile = 1001
		column = row = 0
		if self.bool_bounds:
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
		for e2, f in enumerate(group, start=100):
			seed = e1*e2+self.rand_seed+id(obj)
			random.seed(seed)
			rand_rotation = random.uniform(-self.rotation, self.rotation)
			random.seed(seed+2)
			rand_scale = random.uniform(self.min_scale, self.max_scale)

			f = (f,) if self.bool_face else f

			if self.bool_bounds or self.rotation or self.scale_factor != 0:
				bb = BBox.calc_bbox_uv(f, uv_layers)
				if not bb.is_valid:
					self.report({'WARNING'}, f"The {obj.name} object have UV-Island with zero area")
					continue

				vec_origin = bb.center

				if self.rotation:
					angle = rand_rotation
					if self.rotation_steps:
						angle = round_threshold(angle, self.rotation_steps)
						# clamp angle in self.rotation
						if angle > self.rotation:
							angle -= self.rotation_steps
						elif angle < -self.rotation:
							angle += self.rotation_steps
					if utilities_uv.rotate_island(f, uv_layers, angle, vec_origin):
						bb.rotate_expand(angle)

				scale = bl_math.lerp(1.0, rand_scale, self.scale_factor)

				new_scale = 1
				# Reset the scale to fit in the tile
				if self.bool_bounds and self.bool_bounds_scaling:
					max_length = bb.max_lenght
					if max_length * scale > 1:
						new_scale = 1 / max_length

				if self.scale_factor != 0 or (self.bool_bounds_scaling and new_scale < 1):
					# If the scale from random is smaller, we choose it
					scale = min(scale, new_scale)
					scale = Vector((scale, scale))
					utilities_uv.scale_island(f, uv_layers, scale, pivot=vec_origin)
					bb.scale(scale)

				if self.bool_bounds:
					to_center_delta = Vector((0.5, 0.5)) - vec_origin
					utilities_uv.translate_island(f, uv_layers, delta=to_center_delta)
					bb.translate(to_center_delta)

			if self.bool_bounds:
				move = Vector((
					max(bb.xmin, 0) * max(min(self.strength.x, 1), -1),
					max(bb.ymin, 0) * max(min(self.strength.y, 1), -1)
				))
			else:
				move = Vector((self.strength.x, self.strength.y))

			if not (move.x or move.y):
				continue

			random.seed(seed+3)
			rand_move_x = 2*(random.random()-0.5)
			random.seed(seed+4)
			rand_move_y = 2*(random.random()-0.5)

			randmove = Vector((rand_move_x, rand_move_y)) * move

			if self.round_mode == 'INT':
				randmove = Vector([round(i) for i in randmove])
			elif self.round_mode == 'STEPS':
				# TODO bool_bounds for steps
				if self.steps.x > 1e-05:
					randmove.x = round_threshold(randmove.x, self.steps.x)
				if self.steps.y > 1e-05:
					randmove.y = round_threshold(randmove.y, self.steps.y)

				# if self.bool_bounds:
				# 	pass

			if (not self.bool_bounds) or udim_tile == 1001:
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
