import bpy
import bmesh
import operator
from mathutils import Vector
from collections import defaultdict
from math import pi

from . import utilities_uv


class op(bpy.types.Operator):
	bl_idname = "uv.textools_select_islands_identical"
	bl_label = "Select identical"
	bl_description = "Select identical UV islands with similar topology"
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
		swap(self, context)
		return {'FINISHED'}


def swap(self, context):

	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()

	# Get selected island
	islands = utilities_uv.getSelectionIslands()

	if len(islands) != 1:
		self.report({'ERROR_INVALID_INPUT'}, "Please select only 1 UV Island")
		return
	
	island_stats_source = Island_stats(islands[0])

	bpy.context.scene.tool_settings.uv_select_mode = 'FACE'
	bpy.ops.uv.select_all(action='SELECT')

	islands_all = utilities_uv.getSelectionIslands()
	islands_equal = []
	for island in islands_all:
		island_stats = Island_stats(island)

		if island_stats_source.isEqual(island_stats):
			islands_equal.append(island_stats.faces)

	print("Islands: "+str(len(islands_equal))+"x")

	bpy.ops.uv.select_all(action='DESELECT')
	for island in islands_equal:
		for face in island:
			for loop in face.loops:
				if not loop[uv_layers].select:
					loop[uv_layers].select = True



class Island_stats:
	countFaces = 0
	countVerts = 0
	faces = []
	area = 0
	countLinkedEdges = 0
	countLinkedFaces = 0
	

	def __init__(self, faces):
		bm = bmesh.from_edit_mesh(bpy.context.active_object.data);
		uv_layers = bm.loops.layers.uv.verify();
		
		# Collect topology stats
		self.faces = faces
		verts = []
		for face in faces:
			self.countFaces+=1
			self.area+=face.calc_area()

			for loop in face.loops:
				if loop.vert not in verts:
					verts.append(loop.vert)
					self.countVerts+=1
					self.countLinkedEdges+= len(loop.vert.link_edges)
					self.countLinkedFaces+= len(loop.vert.link_faces)
		
	def isEqual(self, other):
		if self.countVerts != other.countVerts:
			return False
		if self.countFaces != other.countFaces:
			return False

		if self.countLinkedEdges != other.countLinkedEdges:
			return False
		if self.countLinkedFaces != other.countLinkedFaces:
			return False

		# area needs to be 90%+ identical
		if min(self.area, other.area)/max(self.area, other.area) < 0.7:
			return False

		return True


bpy.utils.register_class(op)