import bpy
import bmesh
import mathutils
from mathutils import Vector
import math

from . import utilities_texel
from . import utilities_uv


class op(bpy.types.Operator):
	bl_idname = "uv.textools_texel_density_get"
	bl_label = "Get Texel size"
	bl_description = "Get Pixel per unit ratio or Texel density"
	bl_options = {'REGISTER', 'UNDO'}
	
	@classmethod
	def poll(cls, context):
		if bpy.context.area.type != 'IMAGE_EDITOR':
			return False
		if not bpy.context.active_object:
			return False
		if bpy.context.object.mode != 'EDIT' and bpy.context.object.mode != 'OBJECT':
			return False
		if bpy.context.object.mode == 'OBJECT' and len(bpy.context.selected_objects) == 0:
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		if not bpy.context.object.data.uv_layers:
			return False
		return True


	def execute(self, context):
		edit_mode = bpy.context.object.mode == 'EDIT'
		getmode = bpy.context.scene.texToolsSettings.texel_get_mode
		sum_area_uv = 0
		sum_area_vt = 0

		area_pairs = utilities_uv.multi_object_loop(get_texel_density, self, context, edit_mode, getmode, need_results = True)

		for area_pair in area_pairs:
			sum_area_uv += area_pair[0]
			sum_area_vt += area_pair[1]

		if sum_area_uv != 0 and sum_area_vt != 0:
			bpy.context.scene.texToolsSettings.texel_density = sum_area_uv / sum_area_vt

		if not edit_mode:
			bpy.ops.object.mode_set(mode='OBJECT')

		return {'FINISHED'}



def get_texel_density(self, context, edit_mode, getmode):
	is_sync = bpy.context.scene.tool_settings.use_uv_select_sync
	obj = bpy.context.active_object
	if obj.type != 'MESH' or not obj.data.uv_layers:
		return

	bpy.ops.object.mode_set(mode='EDIT')
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()

	if edit_mode:
		if is_sync:
			object_faces = [face for face in bm.faces if face.select]
		else:
			object_faces = utilities_uv.get_selected_uv_faces(bm, uv_layers)
	else:
		object_faces = bm.faces

	if not object_faces:
		#self.report({'INFO'}, "No UV maps or meshes selected" )
		return [0, 0]

	if getmode == 'IMAGE':
		# Collect image/texture
		image = utilities_texel.get_object_texture_image(obj)
		if not image:
			self.report({'INFO'}, "No Texture found, assign Checker map or texture first" )
			return [0, 0]
		if image.source =='TILED':
			udim_tile, column, row = utilities_uv.get_UDIM_tile_coords(obj)
			if udim_tile != 1001:
				size = utilities_texel.get_tile_size(self, image, udim_tile)
				if not size:
					return [0, 0]
			else:
				size = min(image.size[0], image.size[1])
		else:
			size = min(image.size[0], image.size[1])

	elif getmode == 'SIZE':
		size = min(bpy.context.scene.texToolsSettings.size[0], bpy.context.scene.texToolsSettings.size[1])
	else:
		size = int(getmode)


	area_uv_sq = 0
	area_vt_sq = 0

	# Get area for each face in UV space and 3D View
	if getmode != 'IMAGE' or (image and getmode == 'IMAGE'):
		for face in object_faces:
			# Decomposed face into triagles to calculate area
			tris = len(face.loops)-2
			if tris <=0:
				continue

			index = None
			area_uv = 0
			area_vt = 0

			for _ in range(tris):
				vA = face.loops[0][uv_layers].uv
				if index is None:
					origin = face.loops[0].link_loop_next
				else:
					for loop in face.loops:
						if loop.vert.index == index:
							origin = loop.link_loop_next
							break
				vB = origin[uv_layers].uv
				vC = origin.link_loop_next[uv_layers].uv

				area_uv += mathutils.geometry.area_tri(Vector(vA), Vector(vB), Vector(vC))

				index = origin.vert.index

			area_vt += face.calc_area()

			area_uv_sq += math.sqrt( area_uv ) * size
			area_vt_sq += math.sqrt( area_vt )

	return [area_uv_sq, area_vt_sq]


bpy.utils.register_class(op)
