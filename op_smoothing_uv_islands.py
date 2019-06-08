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
		smooth_uv_islands(self, context)
		return {'FINISHED'}



def smooth_uv_islands(self, context):
	if bpy.context.active_object.mode != 'EDIT':
		bpy.ops.object.mode_set(mode='EDIT')

	bm = bmesh.from_edit_mesh(bpy.context.active_object.data);
	uv_layers = bm.loops.layers.uv.verify();

	# Smooth everything
	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
	bpy.ops.mesh.select_all(action='SELECT')
	bpy.ops.mesh.faces_shade_smooth()
	bpy.ops.mesh.mark_sharp(clear=True)

	# Select Edges
	bpy.ops.mesh.select_all(action='DESELECT')
	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
	bpy.ops.uv.textools_select_islands_outline()
	bpy.ops.mesh.mark_sharp()
	bpy.ops.mesh.select_all(action='DESELECT')
	
	# Apply Edge split modifier
	bpy.context.object.data.use_auto_smooth = True
	bpy.context.object.data.auto_smooth_angle = math.pi

	# bpy.ops.object.modifier_add(type='EDGE_SPLIT')
	# bpy.context.object.modifiers["EdgeSplit"].use_edge_angle = False

	bpy.ops.object.mode_set(mode='OBJECT')

bpy.utils.register_class(op)