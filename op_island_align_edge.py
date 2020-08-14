import bpy
import bmesh
import operator
import math
from mathutils import Vector
from collections import defaultdict
from math import pi

from . import utilities_uv

class op(bpy.types.Operator):
	bl_idname = "uv.textools_island_align_edge"
	bl_label = "Align Island by Edge"
	bl_description = "Align the island by selected edge"
	bl_options = {'REGISTER', 'UNDO'}
	
	@classmethod
	def poll(cls, context):
		#Only in UV editor mode
		if bpy.context.area.type != 'IMAGE_EDITOR':
			return False

		if not bpy.context.active_object:
			return False

		if bpy.context.active_object.type != 'MESH':
			return False

		#Only in Edit mode
		if bpy.context.active_object.mode != 'EDIT':
			return False

		if bpy.context.scene.tool_settings.use_uv_select_sync:
			return False

		#Requires UV map
		if not bpy.context.object.data.uv_layers:
			return False

		# Requires UV Edge select mode
		if bpy.context.scene.tool_settings.uv_select_mode != 'EDGE':
		 	return False

		return True


	def execute(self, context):
		#Store selection
		utilities_uv.selection_store()

		main(context)

		#Restore selection
		utilities_uv.selection_restore()

		return {'FINISHED'}



def main(context):
	print("Executing operator_island_align_edge")

	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()
	
	faces_selected = [];
	for face in bm.faces:
		if face.select:
			for loop in face.loops:
				if loop[uv_layers].select:
					faces_selected.append(face)
					break
	
	print("faces_selected: "+str(len(faces_selected)))

	# Collect 2 uv verts for each island
	face_uvs = {}
	for face in faces_selected:
		uvs = []
		for loop in face.loops:
			if loop[uv_layers].select:
				uvs.append(loop[uv_layers])
				if len(uvs) >= 2:
					break
		if len(uvs) >= 2:
			face_uvs[face] = uvs

	faces_islands = {}
	faces_unparsed = faces_selected.copy()
	for face in face_uvs:
		if face in faces_unparsed:

			bpy.ops.uv.select_all(action='DESELECT')
			face_uvs[face][0].select = True;
			bpy.ops.uv.select_linked()#Extend selection
			
			#Collect faces
			faces_island = [face];
			for f in faces_unparsed:
				if f != face and f.select and f.loops[0][uv_layers].select:
					print("append "+str(f.index))
					faces_island.append(f)
			for f in faces_island:
				faces_unparsed.remove(f)

			#Assign Faces to island
			faces_islands[face] = faces_island

	print("Sets: {}x".format(len(faces_islands)))

	# Align each island to its edges
	for face in faces_islands:
		align_island(face_uvs[face][0].uv, face_uvs[face][1].uv, faces_islands[face])


def align_island(uv_vert0, uv_vert1, faces):
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()

	print("Align {}x faces".format(len(faces)))

	# Select faces
	bpy.ops.uv.select_all(action='DESELECT')
	for face in faces:
		for loop in face.loops:
			loop[uv_layers].select = True

	diff = uv_vert1 - uv_vert0
	current_angle = math.atan2(diff.y, diff.x)
	angle_to_rotate = round(current_angle / (math.pi/2)) * (math.pi/2) - current_angle

	bpy.ops.uv.select_linked()

	bpy.context.tool_settings.transform_pivot_point = 'CURSOR'
	bpy.ops.uv.cursor_set(location=uv_vert0 + diff/2)

	bpy.ops.transform.rotate(value=angle_to_rotate, orient_axis='Z', constraint_axis=(False, False, False), orient_type='GLOBAL', mirror=False, use_proportional_edit=False)


bpy.utils.register_class(op)
