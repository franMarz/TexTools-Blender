import bpy
import bmesh
import operator
import time
from mathutils import Vector
from collections import defaultdict
from math import pi

from . import settings
from . import utilities_ui

def selection_store():
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data);
	uv_layers = bm.loops.layers.uv.verify();

	# https://blender.stackexchange.com/questions/5781/how-to-list-all-selected-elements-in-python
	# print("selectionStore")
	settings.selection_uv_mode = bpy.context.scene.tool_settings.uv_select_mode
	settings.selection_uv_pivot = bpy.context.tool_settings.transform_pivot_point
	
	settings.selection_uv_pivot_pos = bpy.context.space_data.cursor_location.copy()

	#VERT Selection
	settings.selection_mode = tuple(bpy.context.scene.tool_settings.mesh_select_mode)
	settings.selection_vert_indexies = []
	for vert in bm.verts:
		if vert.select:
			settings.selection_vert_indexies.append(vert.index)

	settings.selection_face_indexies = []
	for face in bm.faces:
		if face.select:
			settings.selection_face_indexies.append(face.index)


	#Face selections (Loops)
	settings.selection_uv_loops = []
	for face in bm.faces:
		for loop in face.loops:
			if loop[uv_layers].select:
				settings.selection_uv_loops.append( [face.index, loop.vert.index] )



def selection_restore(bm = None, uv_layers = None):

	if bpy.context.object.mode != 'EDIT':
		bpy.ops.object.mode_set(mode = 'EDIT')

	if not bm:
		bm = bmesh.from_edit_mesh(bpy.context.active_object.data);
	if not uv_layers:
		uv_layers = bm.loops.layers.uv.verify();

	# print("selectionRestore")
	bpy.context.scene.tool_settings.uv_select_mode = settings.selection_uv_mode
	bpy.context.tool_settings.transform_pivot_point = settings.selection_uv_pivot

	contextViewUV = utilities_ui.GetContextViewUV()
	if contextViewUV:
		bpy.ops.uv.cursor_set(contextViewUV, location=settings.selection_uv_pivot_pos)


	bpy.ops.mesh.select_all(action='DESELECT')

	if hasattr(bm.verts, "ensure_lookup_table"): 
		bm.verts.ensure_lookup_table()
		# bm.edges.ensure_lookup_table()
		bm.faces.ensure_lookup_table()

	#FACE selection
	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
	for index in settings.selection_face_indexies:
		if index < len(bm.faces):
			bm.faces[index].select = True

	#VERT Selection
	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
	for index in settings.selection_vert_indexies:
		if index < len(bm.verts):
			bm.verts[index].select = True

	#Selection Mode
	bpy.context.scene.tool_settings.mesh_select_mode = settings.selection_mode


	#UV Face-UV Selections (Loops)
	bpy.ops.uv.select_all(contextViewUV, action='DESELECT')
	for uv_set in settings.selection_uv_loops:
		for loop in bm.faces[ uv_set[0] ].loops:
			if loop.vert.index == uv_set[1]:
				loop[uv_layers].select = True
				break

	bpy.context.view_layer.update()



def get_selected_faces():
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data);
	faces = [];
	for face in bm.faces:
		if face.select:
			faces.append(face)

	return faces



def set_selected_faces(faces):
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data);
	uv_layers = bm.loops.layers.uv.verify();
	for face in faces:
		for loop in face.loops:
			loop[uv_layers].select = True


def get_selected_uvs(bm, uv_layers):
	"""Returns selected mesh vertices of selected UV's"""
	uvs = []
	for face in bm.faces:
		if face.select:
			for loop in face.loops:
				if loop[uv_layers].select:
					uvs.append( loop[uv_layers] )
	return uvs



def get_selected_uv_verts(bm, uv_layers):
	"""Returns selected mesh vertices of selected UV's"""
	verts = set()
	for face in bm.faces:
		if face.select:
			for loop in face.loops:
				if loop[uv_layers].select:
					verts.add( loop.vert )
	return list(verts)



def get_selected_uv_edges(bm, uv_layers):
	"""Returns selected mesh edges of selected UV's"""
	verts = get_selected_uv_verts(bm, uv_layers)
	edges = []
	for edge in bm.edges:
		if edge.verts[0] in verts and edge.verts[1] in verts:
			edges.append(edge)
	return edges



def get_selected_uv_faces(bm, uv_layers):
	"""Returns selected mesh faces of selected UV's"""
	faces = []
	for face in bm.faces:
		if face.select:
			count = 0
			for loop in face.loops:
				if loop[uv_layers].select:
					count+=1
			if count == len(face.loops):
				faces.append(face)
	return faces



def get_vert_to_uv(bm, uv_layers):
	vert_to_uv = {}
	for face in bm.faces:
		for loop in face.loops:
			vert = loop.vert
			uv = loop[uv_layers]
			if vert not in vert_to_uv:
				vert_to_uv[vert] = [uv];
			else:
				vert_to_uv[vert].append(uv)
	return vert_to_uv



def get_uv_to_vert(bm, uv_layers):
	uv_to_vert = {}
	for face in bm.faces:
		for loop in face.loops:
			vert = loop.vert
			uv = loop[uv_layers]
			if uv not in uv_to_vert:
				uv_to_vert[ uv ] = vert;
	return uv_to_vert




def getSelectionBBox():
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data);
	uv_layers = bm.loops.layers.uv.verify();
	
	bbox = {}
	
	boundsMin = Vector((99999999.0,99999999.0))
	boundsMax = Vector((-99999999.0,-99999999.0))
	boundsCenter = Vector((0.0,0.0))
	countFaces = 0;
	
	for face in bm.faces:
		if face.select:
			for loop in face.loops:
				if loop[uv_layers].select is True:
					uv = loop[uv_layers].uv
					boundsMin.x = min(boundsMin.x, uv.x)
					boundsMin.y = min(boundsMin.y, uv.y)
					boundsMax.x = max(boundsMax.x, uv.x)
					boundsMax.y = max(boundsMax.y, uv.y)
			
					boundsCenter+= uv
					countFaces+=1
	
	bbox['min'] = boundsMin
	bbox['max'] = boundsMax
	bbox['width'] = (boundsMax - boundsMin).x
	bbox['height'] = (boundsMax - boundsMin).y
	
	if countFaces == 0:
		bbox['center'] = boundsMin
	else:
		bbox['center'] = boundsCenter / countFaces

	bbox['area'] = bbox['width'] * bbox['height']
	bbox['minLength'] = min(bbox['width'], bbox['height'])
				
	return bbox;



def getSelectionIslands(bm=None, uv_layers=None):
	if bm == None:
		bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
		uv_layers = bm.loops.layers.uv.verify()

	#Reference A: https://github.com/nutti/Magic-UV/issues/41
	#Reference B: https://github.com/c30ra/uv-align-distribute/blob/v2.2/make_island.py

	#Extend selection
	if bpy.context.scene.tool_settings.use_uv_select_sync == False:
		bpy.ops.uv.select_linked()
 
	#Collect selected UV faces
	faces_selected = [];
	for face in bm.faces:
		if face.select and face.loops[0][uv_layers].select:
			faces_selected.append(face)
		
	#Collect UV islands
	# faces_parsed = []
	faces_unparsed = faces_selected.copy()
	islands = []

	for face in faces_selected:
		if face in faces_unparsed:

			#Select single face
			bpy.ops.uv.select_all(action='DESELECT')
			face.loops[0][uv_layers].select = True;
			bpy.ops.uv.select_linked()#Extend selection
			
			#Collect faces
			islandFaces = [face];
			for faceAll in faces_unparsed:
				if faceAll != face and faceAll.select and faceAll.loops[0][uv_layers].select:
					islandFaces.append(faceAll)
			
			for faceAll in islandFaces:
				faces_unparsed.remove(faceAll)

			#Assign Faces to island
			islands.append(islandFaces)
	
	#Restore selection 
	# for face in faces_selected:
	# 	for loop in face.loops:
	# 		loop[uv_layers].select = True

	
	print("Islands: {}x".format(len(islands)))
	return islands
