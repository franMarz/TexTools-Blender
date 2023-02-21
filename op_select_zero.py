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
		if bpy.context.area.ui_type != 'UV':
			return False
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		if bpy.context.active_object.mode != 'EDIT':
			return False
		if not bpy.context.object.data.uv_layers:
			return False
		if bpy.context.scene.tool_settings.use_uv_select_sync:
			return False
		return True


	def execute(self, context):
		utilities_uv.multi_object_loop(select_zero, context)
		return {'FINISHED'}



def select_zero(context):
	selection_mode = bpy.context.scene.tool_settings.uv_select_mode
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()

	bpy.ops.uv.select_all(action='DESELECT')

	for face in bm.faces:
		if face.select:
			# Decomposed face into triagles to calculate area, evaluated area per triangle; if zero, uv area to be compared with real triangle area:
			# selected whole face if a triangle area is zero only in uv space
			tris = len(face.loops)-2
			if tris <=0:
				continue

			index = None
			uv_edges_lengths = []
			for loop in face.loops:
				uv_edges_lengths.append( (loop.link_loop_next[uv_layers].uv - loop[uv_layers].uv).length )
			tolerance = max(uv_edges_lengths)**2

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

				area = mathutils.geometry.area_tri(Vector(vA), Vector(vB), Vector(vC))
				if area <= 0.000015*tolerance:
					vAr = face.loops[0].vert.co
					vBr = origin.vert.co
					vCr = origin.link_loop_next.vert.co

					areaR = mathutils.geometry.area_tri(Vector(vAr), Vector(vBr), Vector(vCr))
					toleranceR = max([edge.calc_length() for edge in face.edges])**2
					if areaR > 0.000015*toleranceR:
						for loop in face.loops:
							loop[uv_layers].select = True
						break

				index = origin.vert.index

	# Workaround for selection not flushing properly from loops to EDGE Selection Mode, apparently since UV edge selection support was added to the UV space
	bpy.ops.uv.select_mode(type='VERTEX')
	bpy.context.scene.tool_settings.uv_select_mode = selection_mode


bpy.utils.register_class(op)
