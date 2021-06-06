import bpy
import bmesh
import mathutils
from mathutils import Vector

from . import utilities_uv

class op(bpy.types.Operator):
	bl_idname = "uv.textools_select_zero"
	bl_label = "Select zero"
	bl_description = "Select zero area UV faces"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		if not bpy.context.active_object:
			return False

		if bpy.context.active_object.type != 'MESH':
			return False

		#Only in Edit mode
		if bpy.context.active_object.mode != 'EDIT':
			return False

		#Only in UV editor mode
		if bpy.context.area.type != 'IMAGE_EDITOR':
			return False

		##Requires UV map
		if not bpy.context.object.data.uv_layers:
			return False

		#Not in Synced mode
		if bpy.context.scene.tool_settings.use_uv_select_sync:
			return False
			
		return True


	def execute(self, context):
		utilities_uv.multi_object_loop(select_zero, context)
		return {'FINISHED'}


def select_zero(context):
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()

	bpy.context.scene.tool_settings.uv_select_mode = 'FACE'
	bpy.ops.uv.select_all(action='DESELECT')

	for face in bm.faces:
		# Decomposed face into triagles to calculate area, evaluated area per triangle; if zero, uv area to be compared with real triangle area:
		# selected whole face if a triangle area is zero only in uv space
		tris = len(face.loops)-2
		if tris <=0:
			continue
		index = None
		normalize = False
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

			v1 = Vector(vA) - Vector(vB)
			v2 = Vector(vC) - Vector(vB)
			if not normalize:
				if v1.length > 1 or v2.length > 1:
					normalize = True
					length = max(v1.length, v2.length) 
			if normalize:
				area = mathutils.geometry.area_tri(Vector(vA)/length, Vector(vB)/length, Vector(vC)/length)
			else:
				area = mathutils.geometry.area_tri(Vector(vA), Vector(vB), Vector(vC))
			
			if area < 0.000001: #Tolerance: 1024->1px
				for loop in face.loops:
					loop[uv_layers].select = True
				vAr = face.loops[0].vert.co
				vBr = origin.vert.co
				vCr = origin.link_loop_next.vert.co

				v1r = Vector(vAr) - Vector(vBr)
				v2r = Vector(vCr) - Vector(vBr)
				if v1r.length > 1 or v2r.length > 1:
					length = max(v1r.length, v2r.length) 
					areaR = mathutils.geometry.area_tri(Vector(vAr)/length, Vector(vBr)/length, Vector(vCr)/length)
				else:
					areaR = mathutils.geometry.area_tri(Vector(vAr), Vector(vBr), Vector(vCr))
				
				if areaR > 0.000001: #Tolerance: 0.001 blender units
					for loop in face.loops:
						loop[uv_layers].select = True
					break

			index = origin.vert.index


bpy.utils.register_class(op)
