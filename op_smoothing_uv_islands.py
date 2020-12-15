import bpy
import bmesh
import operator
import math
from mathutils import Vector
from collections import defaultdict

from . import utilities_uv
from . import utilities_ui


class op(bpy.types.Operator):
	bl_idname = "uv.textools_smoothing_uv_islands"
	bl_label = "Apply smooth normals and hard edges for UV Island borders."
	bl_description = "Set mesh smoothing by uv islands"
	bl_options = {'REGISTER', 'UNDO'}
	
	@classmethod
	def poll(cls, context):
		if not bpy.context.active_object:
			return False
		
		if bpy.context.active_object.type != 'MESH':
			return False

		#Requires UV map
		if not bpy.context.object.data.uv_layers:
			return False

		return True
	
	def execute(self, context):
		utilities_uv.multi_object_loop(smooth_uv_islands, self, context)
		return {'FINISHED'}


def smooth_uv_islands(self, context):

	premode = (bpy.context.active_object.mode)
	bpy.ops.object.mode_set(mode='EDIT')

	#Store selection
	utilities_uv.selection_store()

	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()
	
	# Smooth everything
	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
	bpy.ops.mesh.select_all(action='SELECT')
	bpy.ops.mesh.faces_shade_smooth()
	bpy.ops.mesh.mark_sharp(clear=True)

	# Select Edges
	bpy.ops.mesh.select_all(action='DESELECT')
	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
	presync = bpy.context.scene.tool_settings.use_uv_select_sync
	if not presync:
		bpy.context.scene.tool_settings.use_uv_select_sync = True
	bpy.ops.mesh.select_all(action='SELECT')
	bpy.ops.uv.textools_select_islands_outline()
	bpy.ops.mesh.mark_sharp()
	bpy.ops.mesh.select_all(action='DESELECT')
	bpy.context.scene.tool_settings.use_uv_select_sync = presync
	
	bpy.context.object.data.use_auto_smooth = True
	bpy.context.object.data.auto_smooth_angle = math.pi

	# Restore selection
	utilities_uv.selection_restore()
	
	bpy.ops.object.mode_set(mode=premode)


bpy.utils.register_class(op)