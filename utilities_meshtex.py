import bpy
import bmesh
import operator
import time
import math
from mathutils import Vector

# Find a mesh that contains UV mesh shape keys 
def find_uv_mesh(objects, insideModifiers=True):
	for obj in objects:
		# Requires mesh & UV channel
		if obj and obj.type == 'MESH':

			# Contains shape keys?
			if obj.data.shape_keys and len(obj.data.shape_keys.key_blocks) == 2:
				if "uv" in obj.data.shape_keys.key_blocks and "model" in obj.data.shape_keys.key_blocks:
					return obj

			if insideModifiers:
				# Find via mesh deform modifier
				if len(obj.modifiers) > 0:
					for modifier in obj.modifiers:
	 					if modifier.type == 'SURFACE_DEFORM':
	 						if modifier.target:
	 							if modifier.target.data.shape_keys and len(modifier.target.data.shape_keys.key_blocks) == 2:
	 								return modifier.target
	return None



# # Find meshes that can be wrapped aka texture meshes
def find_texture_meshes(objects):
	obj_textures = []

	for obj in objects:
		if obj and obj.type == 'MESH':
			if find_uv_mesh([obj], insideModifiers=False) == None:
				if obj not in obj_textures:
					obj_textures.append(obj)

	return obj_textures



def uv_mesh_clear(obj_uv):
	# Remove Previous Modifiers
	if "Solidify" in obj_uv.modifiers:
		obj_uv.modifiers.remove( obj_uv.modifiers["Solidify"] )
	# Remove Solidify and push modifiers



def uv_mesh_fit(obj_uv, obj_textures):
	# Clear first shape transition
	bpy.context.scene.texToolsSettings.meshtexture_wrap = 0

	# Clear modifiers first
	uv_mesh_clear(obj_uv)


	# Add solidify modifier
	modifier_solid = obj_uv.modifiers.new(name="Solidify", type='SOLIDIFY')
	modifier_solid.offset = 1
	modifier_solid.thickness = 0 #scale*0.1 #10% height
	modifier_solid.use_even_offset = True
	modifier_solid.thickness_clamp = 0
	modifier_solid.use_quality_normals = True

	min_z = obj_uv.location.z
	max_z = obj_uv.location.z
	for i in range(len(obj_textures)):
		obj = obj_textures[i]
		
		# Min Max Z
		if i == 0:
			min_z = get_bbox(obj)['min'].z
			max_z = get_bbox(obj)['max'].z
		else:
			min_z = min(min_z, get_bbox(obj)['min'].z)
			max_z = max(max_z, get_bbox(obj)['max'].z)
	
	# Set thickness
	size = max(0.1, (max_z - min_z))
	min_z-= size*0.25 #Padding
	max_z+= size*0.25
	size = (max_z - min_z)
	
	modifier_solid.thickness = size

	# Set offset
	if size > 0:
		p_z = (obj_uv.location.z - min_z) / (max_z - min_z)
		modifier_solid.offset = -(p_z-0.5)/0.5
	else:
		modifier_solid.offset = 0



def get_bbox(obj):
	corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]

	# Get world space Min / Max
	box_min = Vector((corners[0].x, corners[0].y, corners[0].z))
	box_max = Vector((corners[0].x, corners[0].y, corners[0].z))
	for corner in corners:
		# box_min.x = -8
		box_min.x = min(box_min.x, corner.x)
		box_min.y = min(box_min.y, corner.y)
		box_min.z = min(box_min.z, corner.z)
		
		box_max.x = max(box_max.x, corner.x)
		box_max.y = max(box_max.y, corner.y)
		box_max.z = max(box_max.z, corner.z)

	return {
		'min':box_min, 
		'max':box_max, 
		'size':(box_max-box_min),
		'center':box_min+(box_max-box_min)/2
	}