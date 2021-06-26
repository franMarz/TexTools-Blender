import bpy
import bmesh
import mathutils
from mathutils import Vector
import math

from . import utilities_texel


class op(bpy.types.Operator):
	bl_idname = "uv.textools_texel_density_get"
	bl_label = "Get Texel size"
	bl_description = "Get Pixel per unit ratio or Texel density"
	bl_options = {'REGISTER', 'UNDO'}
	
	@classmethod
	def poll(cls, context):
		#Only in UV editor mode
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

		# if bpy.context.object.mode == 'EDIT':
		# 	# In edit mode requires face select mode
		# 	if bpy.context.scene.tool_settings.mesh_select_mode[2] == False:
		# 		return False

		return True

	def execute(self, context):
		get_texel_density(
			self, 
			context
		)
		return {'FINISHED'}



def get_texel_density(self, context):
	print("Get texel density")

	edit_mode = bpy.context.object.mode == 'EDIT'
	object_faces = utilities_texel.get_selected_object_faces()

	# Warning: No valid input objects
	if len(object_faces) == 0:
		self.report({'ERROR_INVALID_INPUT'}, "No UV maps or meshes selected" )
		return

	print("obj faces groups {}".format(len(object_faces)))

	# Collect Images / textures
	object_images = {}
	for obj in object_faces:
		image = utilities_texel.get_object_texture_image(obj)
		if image:
			object_images[obj] = image

	# Warning: No valid images
	if len(object_images) == 0:
		self.report({'ERROR_INVALID_INPUT'}, "No Texture found. Assign Checker map or texture first." )
		return

	sum_area_vt = 0
	sum_area_uv = 0

	# Get area for each triangle in view and UV
	for obj in object_faces:
		bpy.ops.object.mode_set(mode='OBJECT')
		bpy.ops.object.select_all(action='DESELECT')
		bpy.context.view_layer.objects.active = obj
		obj.select_set( state = True, view_layer = None)

		# Find image of object
		image = object_images[obj]
		if image:
			bpy.ops.object.mode_set(mode='EDIT')
			bm = bmesh.from_edit_mesh(obj.data)
			uv_layers = bm.loops.layers.uv.verify()
			bm.faces.ensure_lookup_table()
			
			for n in object_faces[obj]:
				face = bm.faces[n]
				# Decomposed face into triagles to calculate area
				tris = len(face.loops)-2
				if tris <=0:
					continue

				index = None
				area_uv = 0
				area_vt = 0

				for i in range(tris):
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

					vAr = face.loops[0].vert.co
					vBr = origin.vert.co
					vCr = origin.link_loop_next.vert.co

					area_vt += mathutils.geometry.area_tri(Vector(vAr), Vector(vBr), Vector(vCr))

					index = origin.vert.index

				sum_area_vt += math.sqrt( area_vt )
				sum_area_uv += math.sqrt( area_uv ) * min(image.size[0], image.size[1])


	# Restore selection
	bpy.ops.object.mode_set(mode='OBJECT')
	bpy.ops.object.select_all(action='DESELECT')
	for obj in object_faces:
		obj.select_set( state = True, view_layer = None)
	bpy.context.view_layer.objects.active = list(object_faces.keys())[0]
	if edit_mode:
		bpy.ops.object.mode_set(mode='EDIT')

	# print("Sum verts area {}".format(sum_area_vt))
	# print("Sum texture area {}".format(sum_area_uv))

	if sum_area_uv == 0 or sum_area_vt == 0:
		bpy.context.scene.texToolsSettings.texel_density = 0
	else:
		bpy.context.scene.texToolsSettings.texel_density = sum_area_uv / sum_area_vt


bpy.utils.register_class(op)
	