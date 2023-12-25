import bpy
import bmesh
import mathutils
from mathutils import Vector
import math

from . import utilities_texel
from . import utilities_uv



class op(bpy.types.Operator):
	bl_idname = "uv.textools_texel_density_set"
	bl_label = "Set Texel size"
	bl_description = "Apply to the selected UVs the current texel density by scaling them"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		if bpy.context.area.ui_type != 'UV':
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
		setmode = bpy.context.scene.texToolsSettings.texel_set_mode
		density = bpy.context.scene.texToolsSettings.texel_density
		udim_tile, column, row = utilities_uv.get_UDIM_tile_coords(bpy.context.active_object)

		utilities_uv.multi_object_loop(set_texel_density, self, context, edit_mode, getmode, setmode, density, udim_tile, column, row)

		if not edit_mode:
			bpy.ops.object.mode_set(mode='OBJECT')

		return {'FINISHED'}



def set_texel_density(self, context, edit_mode, getmode, setmode, density, udim_tile, column, row):
	is_sync = bpy.context.scene.tool_settings.use_uv_select_sync
	obj = bpy.context.active_object
	if obj.type != 'MESH' or not obj.data.uv_layers:
		return

	bpy.ops.object.mode_set(mode='EDIT')
	selection_mode = bpy.context.scene.tool_settings.uv_select_mode

	me = bpy.context.active_object.data
	bm = bmesh.from_edit_mesh(me)
	uv_layers = bm.loops.layers.uv.verify()

	if edit_mode:
		if is_sync:
			object_faces = [face for face in bm.faces if face.select]
		else:
			object_faces = utilities_uv.get_selected_uv_faces(bm, uv_layers)
	else:
		object_faces = bm.faces

	# Warning: No valid input objects
	if not object_faces:
		#self.report({'INFO'}, "No valid meshes or UV maps" )
		return

	if getmode == 'IMAGE':
		# Collect image/texture
		image = utilities_texel.get_object_texture_image(obj)
		if not image:
			self.report({'INFO'}, "No Texture found, assign Checker map or texture first" )
			return
		if image.source =='TILED':
			udim_tile, column, row = utilities_uv.get_UDIM_tile_coords(obj)
			if udim_tile != 1001:
				size = utilities_texel.get_tile_size(self, image, udim_tile)
				if not size:
					return
			else:
				size = min(image.size[0], image.size[1])
		else:
			size = min(image.size[0], image.size[1])

	elif getmode == 'SIZE':
		size = min(bpy.context.scene.texToolsSettings.size[0], bpy.context.scene.texToolsSettings.size[1])
	else:
		size = int(getmode)


	if getmode != 'IMAGE' or (image and getmode == 'IMAGE'):
		if is_sync:
			bpy.context.scene.tool_settings.use_uv_select_sync = False
			bpy.ops.uv.select_all(action='DESELECT')
			for face in object_faces:
				for loop in face.loops:
					loop[uv_layers].select = True

		# Collect groups of faces to scale together
		if setmode == 'ISLAND':
			if edit_mode:
				group_faces = utilities_uv.getSelectionIslands(bm, uv_layers)
			else:
				group_faces = utilities_uv.getAllIslands(bm, uv_layers)
		else:	
			# setmode == 'ALL' Scale all faces together
			if edit_mode:
				group_faces = [utilities_uv.get_selected_uv_faces(bm, uv_layers)]
			else:
				group_faces = [bm.faces]

		for group in group_faces:
			sum_area_vt = 0
			sum_area_uv = 0
			if setmode == 'ISLAND':
				pre_center = Vector((0.0, 0.0))
				n_loops = 0

			for face in group:
				# Decomposed face into triagles to calculate area
				tris = len(face.loops)-2
				if tris <=0:
					continue
				if setmode == 'ISLAND':
					for loop in face.loops:
						pre_center += loop[uv_layers].uv
						n_loops += 1

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

				sum_area_uv += math.sqrt( area_uv ) * size
				sum_area_vt += math.sqrt( area_vt )


			# Apply scale to group
			scale = 1
			if density > 0 and sum_area_uv > 0 and sum_area_vt > 0:
				if setmode == 'ISLAND':
					pre_center /= n_loops
					#pre_center = Vector((0.5, 0.5))
				else:
					if udim_tile != 1001:
						pre_center = Vector((column, row))
				scale = density / (sum_area_uv / sum_area_vt)

			if scale != 1:
				if setmode == 'ISLAND' or udim_tile != 1001:
					for face in group:
						for loop in face.loops:
							loop[uv_layers].uv = pre_center + (loop[uv_layers].uv - pre_center)*scale
				else:
					for face in group:
						for loop in face.loops:
							loop[uv_layers].uv = loop[uv_layers].uv * scale

	bmesh.update_edit_mesh(me, loop_triangles=False)

	# Workaround for selection not flushing properly from loops to EDGE Selection Mode, apparently since UV edge selection support was added to the UV space
	bpy.ops.uv.select_mode(type='VERTEX')
	bpy.context.scene.tool_settings.uv_select_mode = selection_mode

	if is_sync:
		bpy.context.scene.tool_settings.use_uv_select_sync = True


bpy.utils.register_class(op)
