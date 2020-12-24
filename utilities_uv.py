import bpy
import bmesh
import operator
import time
from mathutils import Vector
from collections import defaultdict
import math

from . import settings
from . import utilities_ui


multi_object_loop_stop = False

def multi_object_loop(func, *args, need_results = False, **kwargs) :

	selected_obs = [ob for ob in bpy.context.selected_objects if ob.type == 'MESH']
	
	if len(selected_obs) > 1:
		global multi_object_loop_stop
		multi_object_loop_stop = False

		premode = (bpy.context.active_object.mode)
		bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
		bpy.ops.object.select_all(action='DESELECT')
		
		if need_results :
			results = []
		
		for ob in selected_obs:
			if multi_object_loop_stop: break
			bpy.context.view_layer.objects.active = ob
			bpy.ops.object.mode_set(mode='EDIT', toggle=False)
			if "ob_num" in kwargs :
				print("Operating on object " + str(kwargs["ob_num"]))
			if need_results :
				result = func(*args, **kwargs)
				results.append(result)
			else:
				func(*args, **kwargs)
			if "ob_num" in kwargs :
				kwargs["ob_num"] += 1
			bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
			bpy.ops.object.select_all(action='DESELECT')
		
		for ob in selected_obs:
			ob.select_set(True)
		
		bpy.ops.object.mode_set(mode=premode)

		if need_results :
			return results
		
	else:
		if need_results :
			result = func(*args, **kwargs)
			results = [result]
			return results
		else:
			func(*args, **kwargs)



def selection_store():	
	
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()

	# https://blender.stackexchange.com/questions/5781/how-to-list-all-selected-elements-in-python
	# print("selectionStore")
	settings.selection_uv_mode = bpy.context.scene.tool_settings.uv_select_mode
	#settings.selection_uv_pivot = bpy.context.tool_settings.transform_pivot_point
	settings.selection_uv_pivot = bpy.context.space_data.pivot_point
	
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
		bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	if not uv_layers:
		uv_layers = bm.loops.layers.uv.verify()

	# print("selectionRestore")
	bpy.context.scene.tool_settings.uv_select_mode = settings.selection_uv_mode
	#bpy.context.tool_settings.transform_pivot_point = settings.selection_uv_pivot
	bpy.context.space_data.pivot_point = settings.selection_uv_pivot

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

def move_island(island, dx,dy):
	
	obj = bpy.context.active_object
	me = obj.data
	bm = bmesh.from_edit_mesh(me)

	uv_layer = bm.loops.layers.uv.verify()

	# adjust uv coordinates
	for face in island:
		for loop in face.loops:
			loop_uv = loop[uv_layer]
			loop_uv.uv[0] += dx
			loop_uv.uv[1] += dy 
	bmesh.update_edit_mesh(me)



def get_selected_faces():
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	faces = []
	for face in bm.faces:
		if face.select:
			faces.append(face)

	return faces



def set_selected_faces(faces):
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()
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
				vert_to_uv[vert] = [uv]
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
				uv_to_vert[ uv ] = vert
	return uv_to_vert



def getSelectionBBox():
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()
	
	bbox = {}
	boundsMin = Vector((99999999.0,99999999.0))
	boundsMax = Vector((-99999999.0,-99999999.0))
	boundsCenter = Vector((0.0,0.0))

	select = False
	for face in bm.faces:
		if face.select:
			for loop in face.loops:
				if loop[uv_layers].select is True:
					select = True
					uv = loop[uv_layers].uv
					boundsMin.x = min(boundsMin.x, uv.x)
					boundsMin.y = min(boundsMin.y, uv.y)
					boundsMax.x = max(boundsMax.x, uv.x)
					boundsMax.y = max(boundsMax.y, uv.y)
	if not select:
		# bbox = {'min':Vector((0,0)), 'max':Vector((0,0)), 'width':0, 'height':0}
		return bbox
	
	bbox['min'] = boundsMin
	bbox['max'] = boundsMax
	bbox['width'] = (boundsMax - boundsMin).x
	bbox['height'] = (boundsMax - boundsMin).y

	boundsCenter.x = (boundsMax.x + boundsMin.x)/2
	boundsCenter.y = (boundsMax.y + boundsMin.y)/2

	bbox['center'] = boundsCenter
	bbox['area'] = bbox['width'] * bbox['height']
	bbox['minLength'] = min(bbox['width'], bbox['height'])

	return bbox



def get_island_BBOX(island):
	bbox = {}
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	uv_layers = bm.loops.layers.uv.verify()

	boundsMin = Vector((99999999.0,99999999.0))
	boundsMax = Vector((-99999999.0,-99999999.0))
	boundsCenter = Vector((0.0,0.0))

	for face in island:
		for loop in face.loops:
			uv = loop[uv_layers].uv
			boundsMin.x = min(boundsMin.x, uv.x)
			boundsMin.y = min(boundsMin.y, uv.y)
			boundsMax.x = max(boundsMax.x, uv.x)
			boundsMax.y = max(boundsMax.y, uv.y)
	
	bbox['min'] = Vector((boundsMin))
	bbox['max'] = Vector((boundsMax))

	boundsCenter.x = (boundsMax.x + boundsMin.x)/2
	boundsCenter.y = (boundsMax.y + boundsMin.y)/2

	bbox['center'] = boundsCenter

	return bbox



def getMultiObjectSelectionBBox(all_ob_bounds):
	multibbox = {}
	boundsMin = Vector((99999999.0,99999999.0))
	boundsMax = Vector((-99999999.0,-99999999.0))
	boundsCenter = Vector((0.0,0.0))

	for ob_bounds in all_ob_bounds:
		if len(ob_bounds) > 1 :
			boundsMin.x = min(boundsMin.x, ob_bounds['min'].x)
			boundsMin.y = min(boundsMin.y, ob_bounds['min'].y)
			boundsMax.x = max(boundsMax.x, ob_bounds['max'].x)
			boundsMax.y = max(boundsMax.y, ob_bounds['max'].y)

	multibbox['min'] = boundsMin
	multibbox['max'] = boundsMax
	multibbox['width'] = (boundsMax - boundsMin).x
	multibbox['height'] = (boundsMax - boundsMin).y

	boundsCenter.x = (boundsMax.x + boundsMin.x)/2
	boundsCenter.y = (boundsMax.y + boundsMin.y)/2

	multibbox['center'] = boundsCenter
	multibbox['area'] = multibbox['width'] * multibbox['height']
	multibbox['minLength'] = min(multibbox['width'], multibbox['height'])

	return multibbox



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
	faces_selected = []
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
			face.loops[0][uv_layers].select = True
			bpy.ops.uv.select_linked()#Extend selection
			
			#Collect faces
			islandFaces = [face]
			for faceAll in faces_unparsed:
				if faceAll != face and faceAll.select and faceAll.loops[0][uv_layers].select:
					islandFaces.append(faceAll)
			
			for faceAll in islandFaces:
				faces_unparsed.remove(faceAll)

			#Assign Faces to island
			islands.append(islandFaces)
	
	#Restore selection 
	for face in faces_selected:
		for loop in face.loops:
			loop[uv_layers].select = True

	# print("Islands: {}x".format(len(islands)))
	
	return islands



def alignMinimalBounds(uv_layers=None):
	steps = 8
	angle = 45	# Starting Angle, half each step

	all_ob_bounds = multi_object_loop(getSelectionBBox, need_results=True)

	select = False
	for ob_bounds in all_ob_bounds:
		if len(ob_bounds) > 0 :
			select = True
			break
	if not select:
		return {'CANCELLED'}
	
	bboxPrevious = getMultiObjectSelectionBBox(all_ob_bounds)

	for i in range(0, steps):
		# Rotate right
		bpy.ops.transform.rotate(value=(angle * math.pi / 180), orient_axis='Z', constraint_axis=(False, False, False), use_proportional_edit=False)
		all_ob_bounds = multi_object_loop(getSelectionBBox, need_results=True)
		bbox = getMultiObjectSelectionBBox(all_ob_bounds)

		if i == 0:
			sizeA = bboxPrevious['width'] * bboxPrevious['height']
			sizeB = bbox['width'] * bbox['height']
			if abs(bbox['width'] - bbox['height']) <= 0.0001 and sizeA < sizeB:
				bpy.ops.transform.rotate(value=(-angle * math.pi / 180), orient_axis='Z', constraint_axis=(False, False, False), use_proportional_edit=False)
				break

		if bbox['minLength'] < bboxPrevious['minLength']:
			bboxPrevious = bbox	# Success
		else:
			# Rotate Left
			bpy.ops.transform.rotate(value=(-angle*2 * math.pi / 180), orient_axis='Z', constraint_axis=(False, False, False), use_proportional_edit=False)
			all_ob_bounds = multi_object_loop(getSelectionBBox, need_results=True)
			bbox = getMultiObjectSelectionBBox(all_ob_bounds)
			if bbox['minLength'] < bboxPrevious['minLength']:
				bboxPrevious = bbox	# Success
			else:
				# Restore angle of this iteration
				bpy.ops.transform.rotate(value=(angle * math.pi / 180), orient_axis='Z', constraint_axis=(False, False, False), use_proportional_edit=False)
			
		angle = angle / 2

	# if bboxPrevious['width'] < bboxPrevious['height']:
	# 	bpy.ops.transform.rotate(value=(90 * math.pi / 180), orient_axis='Z')