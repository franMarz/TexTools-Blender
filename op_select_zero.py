import bpy
import bmesh
import mathutils
from mathutils import Vector

from . import utilities_uv



precision = 0.0002

class op(bpy.types.Operator):
	bl_idname = "uv.textools_select_zero"
	bl_label = "Select Degenerate"
	bl_description = "Select Degenerate UVs (zero area UV faces)"
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
		return True


	def execute(self, context):
		utilities_uv.multi_object_loop(select_zero, context)
		return {'FINISHED'}



def select_zero(context):
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()
	sync = bpy.context.scene.tool_settings.use_uv_select_sync
	if sync:
		bpy.ops.mesh.select_all(action='DESELECT')
		bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
	else:
		selection_mode = bpy.context.scene.tool_settings.uv_select_mode
		bpy.ops.uv.select_all(action='DESELECT')

	for face in bm.faces:
		if sync or face.select:
			# Decomposed face into triagles to calculate area, evaluated area per triangle; if zero, uv area to be compared with real triangle area:
			# selected whole face if a triangle area is zero only in uv space
			tris = len(face.loops)-2
			if tris <=0:
				continue

			index = None
			uv_edges_lengths = []
			for loop in face.loops:
				uv_edges_lengths.append( (loop.link_loop_next[uv_layers].uv - loop[uv_layers].uv).length )
			tolerance = max(uv_edges_lengths)**2 * precision

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
				if area <= tolerance:
					vAr = face.loops[0].vert.co
					vBr = origin.vert.co
					vCr = origin.link_loop_next.vert.co

					areaR = mathutils.geometry.area_tri(Vector(vAr), Vector(vBr), Vector(vCr))
					toleranceR = max([edge.calc_length() for edge in face.edges])**2 * precision
					if areaR > toleranceR:
						if sync:
							face.select_set(True)
						else:
							for loop in face.loops:
								loop[uv_layers].select = True
						break

				index = origin.vert.index

	if not sync:
		# Workaround for selection not flushing properly from loops to EDGE Selection Mode, apparently since UV edge selection support was added to the UV space
		bpy.ops.uv.select_mode(type='VERTEX')
		bpy.context.scene.tool_settings.uv_select_mode = selection_mode


bpy.utils.register_class(op)
