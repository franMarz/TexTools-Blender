import bpy
import math
import bmesh

from . import utilities_uv
from . import settings



class op(bpy.types.Operator):
	bl_idname = "uv.textools_smoothing_uv_islands"
	bl_label = "Sharp edges from Islands"
	bl_description = "Apply Smooth Normals and Sharp Edges to the UV Island borders of the Mesh"
	bl_options = {'REGISTER', 'UNDO'}

	soft_self_border: bpy.props.BoolProperty(name="Soften own border", description="Do not sharpen uv-borders from an island to itself", default=False)

	@classmethod
	def poll(cls, context):
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		if not bpy.context.object.data.uv_layers:
			return False
		return True


	def execute(self, context):
		premode = bpy.context.active_object.mode
		utilities_uv.multi_object_loop(smooth_uv_islands, self, context)
		bpy.ops.object.mode_set(mode=premode)
		return {'FINISHED'}



def smooth_uv_islands(self, context):
	bpy.ops.object.mode_set(mode='EDIT')
	#utilities_uv.selection_store(bm, uv_layers)

	# Smooth everything
	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
	bpy.ops.mesh.select_all(action='SELECT')
	bpy.ops.mesh.faces_shade_smooth()
	bpy.ops.mesh.mark_sharp(clear=True)

	bpy.ops.uv.select_all(action='SELECT')
	bpy.ops.uv.seams_from_islands(mark_seams=False, mark_sharp=True)

	# Do not create sharp edges if the uv island has a uv seam to itself.
	# Best example is the lateral surface of a cylinder - which doesn't need 
	# a sharp edge when unrolled for normal map baking.

	if self.soft_self_border:
		bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
		uv_layer = bm.loops.layers.uv.verify()

		islands = utilities_uv.getAllIslands(bm, uv_layer)
		bpy.ops.uv.select_all(action='SELECT')
		tested_edges = set()

		for island in islands:
			for face in list(island):
				for edge in face.edges:
					if edge in tested_edges:
						continue

					smooth_border = True
					for link_face in edge.link_faces:
						if link_face not in island:
							smooth_border = False	
							break
					if smooth_border:
						edge.smooth = True

					tested_edges.add(edge)

	bpy.ops.mesh.customdata_custom_splitnormals_clear()
	if settings.bversion < 4.1:
		bpy.context.object.data.use_auto_smooth = True
		bpy.context.object.data.auto_smooth_angle = math.pi

	#utilities_uv.selection_restore(bm, uv_layers)
