import bpy
import math

from . import utilities_uv



class op(bpy.types.Operator):
	bl_idname = "uv.textools_smoothing_uv_islands"
	bl_label = "Apply smooth normals and hard edges for UV Island borders."
	bl_description = "Set separate Mesh Smoothing groups by UV Islands."
	bl_options = {'REGISTER', 'UNDO'}
	
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
		utilities_uv.multi_object_loop(smooth_uv_islands, self, context)
		return {'FINISHED'}



def smooth_uv_islands(self, context):
	premode = bpy.context.active_object.mode
	bpy.ops.object.mode_set(mode='EDIT')
	#utilities_uv.selection_store(bm, uv_layers)

	# Smooth everything
	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
	bpy.ops.mesh.select_all(action='SELECT')
	bpy.ops.mesh.faces_shade_smooth()
	bpy.ops.mesh.mark_sharp(clear=True)

	bpy.ops.uv.select_all(action='SELECT')
	bpy.ops.uv.seams_from_islands(mark_seams=False, mark_sharp=True)

	bpy.ops.mesh.customdata_custom_splitnormals_clear()
	bpy.context.object.data.use_auto_smooth = True
	bpy.context.object.data.auto_smooth_angle = math.pi

	#utilities_uv.selection_restore(bm, uv_layers)
	bpy.ops.object.mode_set(mode=premode)


bpy.utils.register_class(op)
