import bpy
import bmesh
import math

from mathutils import Vector
import numpy as np
from . import settings
from . import utilities_ui


precision = 5
multi_object_loop_stop = False



def multi_object_loop(func, *args, need_results = False, **kwargs) :

	selected_obs = [ob for ob in bpy.context.selected_objects if ob.type == 'MESH']
	# if bpy.context.edit_object not in selected_obs:
	# 	selected_obs.append(bpy.context.edit_object)

	if len(selected_obs) > 1:
		global multi_object_loop_stop
		multi_object_loop_stop = False

		premode = bpy.context.active_object.mode
		preactiv_name = bpy.context.view_layer.objects.active.name
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
				#if result:
				results.append(result)
			else:
				func(*args, **kwargs)
			if "ob_num" in kwargs:
				kwargs["ob_num"] += 1
			bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
			bpy.ops.object.select_all(action='DESELECT')

		for ob in selected_obs:
			ob.select_set(True)

		bpy.context.view_layer.objects.active = bpy.data.objects[preactiv_name]
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



def selection_store(bm=None, uv_layers=None, return_selected_UV_faces=False, return_selected_faces_edges=False, return_selected_faces_loops=False):
	if bm is None:
		bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
		uv_layers = bm.loops.layers.uv.verify()

	settings.use_uv_sync = bpy.context.scene.tool_settings.use_uv_select_sync
	settings.selection_uv_mode = bpy.context.scene.tool_settings.uv_select_mode

	contextViewUV = utilities_ui.GetContextViewUV()
	if contextViewUV:
		settings.selection_uv_pivot = contextViewUV['area'].spaces[0].pivot_point
		settings.selection_uv_pivot_pos = contextViewUV['area'].spaces[0].cursor_location.copy()

	# Clear previous selection
	settings.selection_vert_indexies.clear()
	settings.selection_edge_indexies.clear()
	settings.selection_face_indexies.clear()
	settings.seam_edges.clear()

	settings.selection_mode = tuple(bpy.context.scene.tool_settings.mesh_select_mode)

	if settings.selection_mode[0]:
		for vert in bm.verts:
			if vert.select:
				settings.selection_vert_indexies.add(vert.index)
	if settings.selection_mode[1]:
		for edge in bm.edges:
			if edge.select:
				settings.selection_edge_indexies.add(edge.index)

	# Face selections (Loops)
	settings.selection_uv_loops.clear()
	if return_selected_UV_faces:
		selected_faces = []
	elif return_selected_faces_edges or return_selected_faces_loops:
		selected_faces_loops = {}

	for face in bm.faces:
		if face.select:
			settings.selection_face_indexies.add(face.index)
		n_selected_loops = 0
		if return_selected_faces_edges or return_selected_faces_loops:
			face_selected_loops = []
		
		for loop in face.loops:
			if loop.edge.seam == True:
				settings.seam_edges.add(loop.edge)
			if loop[uv_layers].select:
				n_selected_loops += 1
				settings.selection_uv_loops.add( (face.index, loop.vert.index) )
				if return_selected_faces_edges or return_selected_faces_loops:
					face_selected_loops.append(loop)
		
		if return_selected_UV_faces and n_selected_loops == len(face.loops) and face.select:
			selected_faces.append(face)
		elif return_selected_faces_edges and n_selected_loops == 2 and face.select:
			selected_faces_loops.update({face: face_selected_loops})
		elif return_selected_faces_loops and n_selected_loops > 0 and face.select:
			selected_faces_loops.update({face: face_selected_loops})

	if return_selected_UV_faces:
		return selected_faces
	elif return_selected_faces_edges or return_selected_faces_loops:
		return selected_faces_loops



def selection_restore(bm = None, uv_layers = None, restore_seams=False):
	mode = bpy.context.object.mode
	if mode != 'EDIT':
		bpy.ops.object.mode_set(mode = 'EDIT')
	if bm is None:
		bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
		uv_layers = bm.loops.layers.uv.verify()

	bpy.context.scene.tool_settings.use_uv_select_sync = settings.use_uv_sync
	bpy.context.scene.tool_settings.uv_select_mode = settings.selection_uv_mode

	contextViewUV = utilities_ui.GetContextViewUV()
	if contextViewUV:
		contextViewUV['area'].spaces[0].pivot_point = settings.selection_uv_pivot
		bpy.ops.uv.cursor_set(contextViewUV, location=settings.selection_uv_pivot_pos)

	#Restore seams
	if restore_seams:
		bpy.ops.mesh.select_all(action='SELECT')
		bpy.ops.mesh.mark_seam(clear=True)
		for edge in settings.seam_edges:
			edge.seam = True

	bpy.ops.mesh.select_all(action='DESELECT')

	#Selection Mode
	bpy.context.scene.tool_settings.mesh_select_mode = settings.selection_mode
	
	if settings.selection_mode[0]:
		bm.verts.ensure_lookup_table()
		for index in settings.selection_vert_indexies:
			if index < len(bm.verts):
				bm.verts[index].select = True
	if settings.selection_mode[1]:
		bm.edges.ensure_lookup_table()
		for index in settings.selection_edge_indexies:
			if index < len(bm.edges):
				bm.edges[index].select = True
	bm.faces.ensure_lookup_table()
	for index in settings.selection_face_indexies:
		if index < len(bm.faces):
			bm.faces[index].select = True

	#UV Face-UV Selections (Loops)
	if contextViewUV:
		bpy.ops.uv.select_all(contextViewUV, action='DESELECT')
	else:
		for face in bm.faces:
			for loop in face.loops:
				loop[uv_layers].select = False
	for uv_set in settings.selection_uv_loops:
		for loop in bm.faces[uv_set[0]].loops:
			if loop.vert.index == uv_set[1]:
				loop[uv_layers].select = True
				break
	



	bpy.context.view_layer.update()
	bpy.ops.object.mode_set(mode=mode)



def move_island(island, dx, dy):
	me = bpy.context.active_object.data
	bm = bmesh.from_edit_mesh(me)
	uv_layer = bm.loops.layers.uv.verify()

	# adjust uv coordinates
	for face in island:
		for loop in face.loops:
			loop_uv = loop[uv_layer]
			loop_uv.uv[0] += dx
			loop_uv.uv[1] += dy
	
	bmesh.update_edit_mesh(me)



def set_selected_faces(faces, bm, uv_layers):
	for face in faces:
		for loop in face.loops:
			loop[uv_layers].select = True



def get_selected_uvs(bm, uv_layers):
	"""Returns selected mesh vertices of selected UV's"""
	uvs = set()
	for face in bm.faces:
		if face.select:
			for loop in face.loops:
				if loop[uv_layers].select:
					uvs.add( loop[uv_layers] )
	return uvs



def get_selected_uv_verts(bm, uv_layers, selected=None):
	"""Returns selected mesh vertices of selected UV's"""
	verts = set()
	if selected is None:
		for face in bm.faces:
			if face.select:
				for loop in face.loops:
					if loop[uv_layers].select:
						verts.add( loop.vert )
	else:
		for loop in selected:
			verts.add( loop.vert )
	return verts



def get_selected_uv_edges(bm, uv_layers, selected=None):
	"""Returns selected mesh edges of selected UV's"""
	verts = get_selected_uv_verts(bm, uv_layers, selected)
	edges = set()
	for edge in bm.edges:
		if edge.verts[0] in verts and edge.verts[1] in verts:
			edges.add(edge)
	return edges



def get_selected_uv_faces(bm, uv_layers):
	"""Returns selected mesh faces of selected UV's"""
	faces = [face for face in bm.faces if all([loop[uv_layers].select for loop in face.loops]) and face.select]
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



def getSelectionBBox(bm=None, uv_layers=None):
	if bm is None:
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
				if loop[uv_layers].select == True:
					select = True
					uv = loop[uv_layers].uv
					boundsMin.x = min(boundsMin.x, uv.x)
					boundsMin.y = min(boundsMin.y, uv.y)
					boundsMax.x = max(boundsMax.x, uv.x)
					boundsMax.y = max(boundsMax.y, uv.y)
	if not select:
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



def get_BBOX(group, bm, uv_layers, are_loops=False):
	bbox = {}
	boundsMin = Vector((99999999.0,99999999.0))
	boundsMax = Vector((-99999999.0,-99999999.0))

	if not are_loops:
		for face in group:
			for loop in face.loops:
				uv = loop[uv_layers].uv
				boundsMin = Vector(( min(boundsMin.x, uv.x), min(boundsMin.y, uv.y) ))
				boundsMax = Vector(( max(boundsMax.x, uv.x), max(boundsMax.y, uv.y) ))
	else:
		for loop in group:
			uv = loop[uv_layers].uv
			boundsMin = Vector(( min(boundsMin.x, uv.x), min(boundsMin.y, uv.y) ))
			boundsMax = Vector(( max(boundsMax.x, uv.x), max(boundsMax.y, uv.y) ))
	
	bbox['min'] = boundsMin
	bbox['max'] = boundsMax
	bbox['width'] = (boundsMax - boundsMin).x
	bbox['height'] = (boundsMax - boundsMin).y

	bbox['center'] = Vector(( (boundsMax.x + boundsMin.x)/2, (boundsMax.y + boundsMin.y)/2 ))
	bbox['area'] = bbox['width'] * bbox['height']
	bbox['minLength'] = min(bbox['width'], bbox['height'])

	return bbox



def get_BBOX_multi(all_ob_bounds):
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



def get_center(group, bm, uv_layers, are_loops=False):
	n = 0
	total = Vector((0.0, 0.0))

	if not are_loops:
		for face in group:
			for loop in face.loops:
				total += loop[uv_layers].uv
				n += 1
	else:
		for loop in group:
			total += loop[uv_layers].uv
			n += 1

	return total / n



def getSelectionIslands(bm, uv_layers, selected_faces=None):
	if selected_faces is None:
		selected_faces = [face for face in bm.faces if all([loop[uv_layers].select for loop in face.loops]) and face.select]
	if not selected_faces:
		return []

	# Select islands
	bpy.ops.uv.select_linked()
	disordered_island_faces = {f for f in bm.faces if f.loops[0][uv_layers].select}

	# Collect UV islands
	islands = []

	for face in selected_faces:
		if face in disordered_island_faces:
			bpy.ops.uv.select_all(action='DESELECT')
			face.loops[0][uv_layers].select = True
			bpy.ops.uv.select_linked()

			islandFaces = {f for f in disordered_island_faces if f.loops[0][uv_layers].select}
			disordered_island_faces.difference_update(islandFaces)

			islands.append(islandFaces)
			if not disordered_island_faces:
				break

	# Restore selection
	bpy.ops.uv.select_all(action='DESELECT')
	for face in selected_faces:
		for loop in face.loops:
			loop[uv_layers].select = True
	
	return islands



def splittedSelectionByIsland(bm, uv_layers, selected_faces=None, restore_selected=False):
	if selected_faces is None:
		selected_faces = [f for f in bm.faces if any([l[uv_layers].select for l in f.loops]) and f.select]
	if not selected_faces:
		return []

	# Collect UV islands
	islands = []
	faces_unparsed = set(selected_faces)

	for face in selected_faces:
		if face in faces_unparsed:
			bpy.ops.uv.select_all(action='DESELECT')
			face.loops[0][uv_layers].select = True
			bpy.ops.uv.select_linked()

			islandFaces = {f for f in faces_unparsed if f.loops[0][uv_layers].select}
			faces_unparsed.difference_update(islandFaces)

			islands.append(islandFaces)
			if not faces_unparsed:
				break

	if restore_selected:
		bpy.ops.uv.select_all(action='DESELECT')
		for face in selected_faces:
			for loop in face.loops:
				loop[uv_layers].select = True

	return islands



def getAllIslands(bm, uv_layers):
	if len(bm.faces) == 0:
		return []

	bpy.ops.uv.select_all(action='SELECT')
	faces_unparsed = {f for f in bm.faces if f.select}

	# Collect UV islands
	islands = []

	for face in bm.faces:
		if face in faces_unparsed:
			bpy.ops.uv.select_all(action='DESELECT')
			face.loops[0][uv_layers].select = True
			bpy.ops.uv.select_linked()

			islandFaces = {f for f in faces_unparsed if f.loops[0][uv_layers].select}
			faces_unparsed.difference_update(islandFaces)

			islands.append(islandFaces)
			if not faces_unparsed:
				break

	return islands



def getSelectionFacesIslands(bm, uv_layers, selected_faces_loops):
	# Select islands
	bpy.ops.uv.select_linked()
	disordered_island_faces = {f for f in bm.faces if f.loops[0][uv_layers].select and f.select}

	# Collect UV islands
	selected_faces_islands = {}
	to_remove = set()

	for face in selected_faces_loops.keys():
		if face not in disordered_island_faces:
			to_remove.add(face)
		else:
			bpy.ops.uv.select_all(action='DESELECT')
			face.loops[0][uv_layers].select = True
			bpy.ops.uv.select_linked()

			face_island = {f for f in disordered_island_faces if f.loops[0][uv_layers].select}
			disordered_island_faces.difference_update(face_island)

			selected_faces_islands.update({face: face_island})

	for face in to_remove:
		selected_faces_loops.pop(face)

	return selected_faces_islands, selected_faces_loops


'''
def getSelectionLoopsIslands(bm, uv_layers, selected_loops):
	# Select islands
	bpy.ops.uv.select_linked()
	disordered_loops_islands = {loop for face in bm.faces for loop in face.loops if loop[uv_layers].select and loop.edge.select}

	selected_loops_islands = []

	for loop in selected_loops:
		if loop in disordered_loops_islands:
			bpy.ops.uv.select_all(action='DESELECT')
			loop[uv_layers].select = True
			bpy.ops.uv.select_linked()

			loops_island = {l for l in disordered_loops_islands if l[uv_layers].select}
			disordered_loops_islands.difference_update(loops_island)

			selected_loops_islands.append(loops_island)
			if not disordered_loops_islands:
				break

	return selected_loops_islands
'''


def alignMinimalBounds(bm, uv_layers, selected_faces):
	steps = 8
	angle = math.pi / 4	# Starting Angle, half each step

	faces_loops = {loop for face in selected_faces for loop in face.loops}
	boundary_loops = {loop for loop in faces_loops if loop.edge.is_boundary or loop[uv_layers].uv.to_tuple(precision) != loop.link_loop_radial_next.link_loop_next[uv_layers].uv.to_tuple(precision)}

	align_angle = 0
	bboxPrevious = get_BBOX(boundary_loops, bm, uv_layers, are_loops=True)

	# Get align angle
	for i in range(0, steps):
		# Rotate right
		matrix = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
		for loop in boundary_loops:
			loop[uv_layers].uv = (matrix[0][0]*loop[uv_layers].uv.x + matrix[0][1]*loop[uv_layers].uv.y, matrix[1][0]*loop[uv_layers].uv.x + matrix[1][1]*loop[uv_layers].uv.y)
		bbox = get_BBOX(boundary_loops, bm, uv_layers, are_loops=True)

		# Consolidate iteration
		if bbox['minLength'] < bboxPrevious['minLength']:
			bboxPrevious = bbox	# Success
			align_angle += angle
		else:
			# Rotate Left
			matrix2 = np.array([[np.cos(-angle*2), -np.sin(-angle*2)], [np.sin(-angle*2), np.cos(-angle*2)]])
			for loop in boundary_loops:
				loop[uv_layers].uv = (matrix2[0][0]*loop[uv_layers].uv.x + matrix2[0][1]*loop[uv_layers].uv.y, matrix2[1][0]*loop[uv_layers].uv.x + matrix2[1][1]*loop[uv_layers].uv.y)
			bbox = get_BBOX(boundary_loops, bm, uv_layers, are_loops=True)
			if bbox['minLength'] < bboxPrevious['minLength']:
				bboxPrevious = bbox	# Success
				align_angle -= angle
			else:
				# Restore angle of this iteration
				for loop in boundary_loops:
					loop[uv_layers].uv = (matrix[0][0]*loop[uv_layers].uv.x + matrix[0][1]*loop[uv_layers].uv.y, matrix[1][0]*loop[uv_layers].uv.x + matrix[1][1]*loop[uv_layers].uv.y)

		angle = angle / 2


	if align_angle:
		matrix = np.array([[np.cos(align_angle), -np.sin(align_angle)], [np.sin(align_angle), np.cos(align_angle)]])
		faces_loops.difference_update(boundary_loops)
		for loop in faces_loops:
			loop[uv_layers].uv = (matrix[0][0]*loop[uv_layers].uv.x + matrix[0][1]*loop[uv_layers].uv.y, matrix[1][0]*loop[uv_layers].uv.x + matrix[1][1]*loop[uv_layers].uv.y)	# np.matmul/dot are, surprisingly, >3x slower



def alignMinimalBounds_multi():
	steps = 8
	angle = 45	# Starting Angle, half each step

	all_ob_bounds = multi_object_loop(getSelectionBBox, need_results=True)
	if not any(all_ob_bounds):
		return {'CANCELLED'}

	bboxPrevious = get_BBOX_multi(all_ob_bounds)

	for i in range(0, steps):
		# Rotate right
		bpy.ops.transform.rotate(value=(angle * math.pi / 180), orient_axis='Z', constraint_axis=(False, False, False), use_proportional_edit=False)
		all_ob_bounds = multi_object_loop(getSelectionBBox, need_results=True)
		bbox = get_BBOX_multi(all_ob_bounds)

		# Consolidate iteration
		if bbox['minLength'] < bboxPrevious['minLength']:
			bboxPrevious = bbox	# Success
		else:
			# Rotate Left
			bpy.ops.transform.rotate(value=(-angle*2 * math.pi / 180), orient_axis='Z', constraint_axis=(False, False, False), use_proportional_edit=False)
			all_ob_bounds = multi_object_loop(getSelectionBBox, need_results=True)
			bbox = get_BBOX_multi(all_ob_bounds)
			if bbox['minLength'] < bboxPrevious['minLength']:
				bboxPrevious = bbox	# Success
			else:
				# Restore angle of this iteration
				bpy.ops.transform.rotate(value=(angle * math.pi / 180), orient_axis='Z', constraint_axis=(False, False, False), use_proportional_edit=False)

		angle = angle / 2
