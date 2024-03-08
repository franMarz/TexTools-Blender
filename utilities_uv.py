import bpy
import bmesh
import math
import mathutils

from mathutils import Vector
from . import settings
from . import utilities_ui


precision = 5
multi_object_loop_stop = False



def multi_object_loop(func, *args, need_results = False, **kwargs) :
	selected_obs = [ob for ob in bpy.context.selected_objects if ob.type == 'MESH']

	if len(selected_obs) == 1:
		preactiv_name = bpy.context.view_layer.objects.active.name
		bpy.context.view_layer.objects.active = selected_obs[0]
		if not need_results:
			func(*args, **kwargs)
			if bpy.data.objects[preactiv_name]:
				bpy.context.view_layer.objects.active = bpy.data.objects[preactiv_name]
		else:
			result = func(*args, **kwargs)
			results = [result]
			if bpy.data.objects[preactiv_name]:
				bpy.context.view_layer.objects.active = bpy.data.objects[preactiv_name]
			return results

	else:
		global multi_object_loop_stop
		multi_object_loop_stop = False
		premode = bpy.context.active_object.mode
		preactiv_name = bpy.context.view_layer.objects.active.name

		bpy.ops.object.mode_set(mode='EDIT', toggle=False)
		unique_selected_obs = [ob for ob in bpy.context.objects_in_mode_unique_data if ob.type == 'MESH' and ob.select_get()]
		bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
		bpy.ops.object.select_all(action='DESELECT')

		if need_results :
			results = []

		for ob in unique_selected_obs:
			if multi_object_loop_stop:
				break
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
		selected_faces = set()
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
			selected_faces.add(face)
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
		if settings.bversion >= 3.2:
			with bpy.context.temp_override(**contextViewUV):
				bpy.ops.uv.cursor_set(location=settings.selection_uv_pivot_pos)
		else:
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
		if settings.bversion >= 3.2:
			with bpy.context.temp_override(**contextViewUV):
				bpy.ops.uv.select_all(action='DESELECT')
		else:
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

	# Workaround for selection not flushing properly from loops in EDGE or FACE UV Selection Mode, apparently since UV edge selection support was added to the UV space
	if settings.selection_uv_mode != "VERTEX":
		bpy.ops.uv.select_mode(type='VERTEX')
	bpy.context.scene.tool_settings.uv_select_mode = settings.selection_uv_mode

	bpy.context.view_layer.update()
	bpy.ops.object.mode_set(mode=mode)


def selected_unique_objects_in_mode_with_uv():
	return [obj for obj in bpy.context.objects_in_mode_unique_data if obj.type == 'MESH' and obj.data.uv_layers]

def get_UDIM_tile_coords(obj):
	udim_tile = 1001
	column = row = 0

	if bpy.context.scene.texToolsSettings.UDIMs_source == 'OBJECT':
		if obj and obj.type == 'MESH' and obj.data.uv_layers:
			for i in range(len(obj.material_slots)):
				slot = obj.material_slots[i]
				if slot.material:
					if slot.material.use_nodes:
						nodes = slot.material.node_tree.nodes
						if nodes:
							for node in nodes:
								if node.type == 'TEX_IMAGE' and node.image and node.image.source =='TILED':
									udim_tile = node.image.tiles.active.number
									break
				else:
					continue
				break
	else:
		image = bpy.context.space_data.image
		if image:
			udim_tile = image.tiles.active.number

	if udim_tile != 1001:
		column = int(str(udim_tile - 1)[-1])
		if udim_tile > 1010:
			row = int(str(udim_tile - 1001)[0:-1])

	return udim_tile, column, row



def get_UDIM_tiles(objs):
	tiles = set()
	for obj in objs:
		for i in range(len(obj.material_slots)):
			slot = obj.material_slots[i]
			if slot.material:
				if slot.material.use_nodes:
					nodes = slot.material.node_tree.nodes
					if nodes:
						for node in nodes:
							if node.type == 'TEX_IMAGE' and node.image and node.image.source =='TILED':
								tiles.update({tile.number for tile in node.image.tiles})
	return tiles



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


def translate_island(island, uv_layer, delta):
	for face in island:
		for loop in face.loops:
			loop[uv_layer].uv += delta


def rotate_island(island, uv_layer=None, angle=0, pivot=None):
    '''Rotate a list of faces by angle (in radians) around a center'''
    rot_matrix = mathutils.Matrix.Rotation(-angle, 2)
    if uv_layer is None:
        me = bpy.context.active_object.data
        bm = bmesh.from_edit_mesh(me)
        uv_layer = bm.loops.layers.uv.verify()
    if pivot:
        for face in island:
            for loop in face.loops:
                uv = loop[uv_layer]
                uv.uv = rot_matrix @ (uv.uv - pivot) + pivot
        return

    for face in island:
        for loop in face.loops:
            uv = loop[uv_layer]
            uv.uv = uv.uv @ rot_matrix


def scale_island(island, uv_layer, scale_x, scale_y, pivot=None):
	"""Scale a list of faces by 'scale_x, scale_y'. """

	if not pivot:
		bbox = get_BBOX(island, None, uv_layer)
		pivot = bbox['center']
	
	for face in island:
		for loop in face.loops:
			x, y = loop[uv_layer].uv               
			xt = x - pivot.x
			yt = y - pivot.y
			xs = xt * scale_x
			ys = yt * scale_y
			loop[uv_layer].uv.x = xs + pivot.x
			loop[uv_layer].uv.y = ys + pivot.y


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
    
    xmin = math.inf
    xmax = -math.inf
    ymin = math.inf
    ymax = -math.inf

    select = False
    for face in bm.faces:
        if face.select:
            for loop in face.loops:
                if loop[uv_layers].select == True:
                    select = True
                    
                    x, y = loop[uv_layers].uv
                    if xmin > x:
                        xmin = x
                    if xmax < x:
                        xmax = x
                    if ymin > y:
                        ymin = y
                    if ymax < y:
                        ymax = y
                        
    if not select:
        return bbox
    
    bbox['min'] = Vector((xmin, ymin))
    bbox['max'] = Vector((xmax, ymax))
    
    bbox['width'] = xmax - xmin
    bbox['height'] = ymax - ymin

    xcenter = (xmax + xmin)*0.5
    ycenter = (ymax + ymin)*0.5

    bbox['center'] = Vector((xcenter, ycenter))
    bbox['area'] = bbox['width'] * bbox['height']
    bbox['minLength'] = min(bbox['width'], bbox['height'])

    return bbox



def get_BBOX(group, bm, uv_layers, are_loops=False):
	bbox = {}
	xmin = math.inf
	xmax = -math.inf
	ymin = math.inf
	ymax = -math.inf

	if not are_loops:
		for face in group:
			for loop in face.loops:
				x, y = loop[uv_layers].uv
				if xmin > x:
					xmin = x
				if xmax < x:
					xmax = x
				if ymin > y:
					ymin = y
				if ymax < y:
					ymax = y
	else:
		for loop in group:
			x, y = loop[uv_layers].uv
			if xmin > x:
				xmin = x
			if xmax < x:
				xmax = x
			if ymin > y:
				ymin = y
			if ymax < y:
				ymax = y

	bbox['min'] = Vector((xmin, ymin))
	bbox['max'] = Vector((xmax, ymax))

	bbox['width'] = xmax - xmin
	bbox['height'] = ymax - ymin

	xcenter = (xmax + xmin) * 0.5
	ycenter = (ymax + ymin) * 0.5

	bbox['center'] = Vector((xcenter, ycenter))
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



def get_selected_islands(bm, uv_layers, selected=True, extend_selection_to_islands=False):
    islands = []
    island = []

    sync = bpy.context.scene.tool_settings.use_uv_select_sync

    faces = bm.faces
    # Reset tags for unselected (if tag is False - skip)
    if selected:
        if sync:
            for face in faces:
                face.tag = face.select
        else:
            for face in faces:
                if face.select:
                    face.tag = all(l[uv_layers].select for l in face.loops)
                    continue
                face.tag = False
    else:
        if sync:
            for face in faces:
                face.tag = not face.hide
        else:
            for face in faces:
                face.tag = not face.hide and face.select

    for face in faces:
        # Skip unselected and appended faces
        if not face.tag:  # if is False:
            continue

        # Tag first element in island (dont add again)
        face.tag = False

        # Container collector of island elements
        parts_of_island = [face]

        # Container for get elements from loop from parts_of_island
        temp = []

        # Blank list == all faces of the island taken
        while parts_of_island:
            for f in parts_of_island:
                # Running through all the neighboring faces
                for l in f.loops:
                    link_face = l.link_loop_radial_next.face
                    # Skip appended
                    if not link_face.tag:  # if is False:
                        continue

                    for ll in link_face.loops:
                        if not ll.face.tag:  # if is False:
                            continue
                        # If the coordinates of the vertices of adjacent
                        # faces on the uv match, then this is part of the
                        # island and we append face to the list
                        if ll[uv_layers].uv != l[uv_layers].uv:
                            continue
                        # Skip non-manifold
                        if (l.link_loop_next[uv_layers].uv == ll.link_loop_prev[uv_layers].uv) or \
                                (ll.link_loop_next[uv_layers].uv == l.link_loop_prev[uv_layers].uv):
                            temp.append(ll.face)
                            ll.face.tag = False

            island.extend(parts_of_island)
            parts_of_island = temp
            temp = []

        # Skip the islands that don't have a single selected face.
        if selected is False and extend_selection_to_islands is True:
            if sync:
                for face in island:
                    if face.select:
                        break
                else:
                    island = []
                    continue
            else:
                for face in island:
                    if all(l[uv_layers].select for l in face.loops):
                        break
                else:
                    island = []
                    continue

        islands.append(island)
        island = []
    return islands


def getFacesIslands(bm, uv_layers, faces, islands, disordered_island_faces):
	for face in faces:
		if face in disordered_island_faces:
			bpy.ops.uv.select_all(action='DESELECT')
			face.loops[0][uv_layers].select = True
			bpy.ops.uv.select_linked()

			islandFaces = {f for f in disordered_island_faces if f.loops[0][uv_layers].select}
			disordered_island_faces.difference_update(islandFaces)

			islands.append(islandFaces)
			if not disordered_island_faces:
				break



def getAllIslands(bm, uv_layers):
	faces = {f for f in bm.faces if f.select}
	if not faces:
		return []

	islands = []
	faces_unparsed = faces.copy()

	getFacesIslands(bm, uv_layers, faces, islands, faces_unparsed)

	return islands



def getSelectionIslands(bm, uv_layers, extend_selection_to_islands=False, selected_faces=None, need_faces_selected=True, restore_selected=True):
	if selected_faces is None:
		if need_faces_selected:
			selected_faces = {f for f in bm.faces if all([l[uv_layers].select for l in f.loops]) and f.select}
		else:
			selected_faces = {f for f in bm.faces if any([l[uv_layers].select for l in f.loops]) and f.select}
	if not selected_faces:
		return []

	# Select islands
	if extend_selection_to_islands:
		bpy.ops.uv.select_linked()
		disordered_island_faces = {f for f in bm.faces if f.loops[0][uv_layers].select and f.select}
	else:
		disordered_island_faces = selected_faces.copy()

	# Collect UV islands
	islands = []

	getFacesIslands(bm, uv_layers, selected_faces, islands, disordered_island_faces)

	# Restore selection
	if restore_selected:
		bpy.ops.uv.select_all(action='DESELECT')
		set_selected_faces(selected_faces, bm, uv_layers)
	
	return islands



def getSelectedUnselectedIslands(bm, uv_layers, selected_faces=None, target_faces=None, restore_selected=False):
	if selected_faces is None:
		return [], []

	# Collect selected UV islands
	selected_islands = []
	bpy.ops.uv.select_linked()
	disordered_islands_selected = {f for f in bm.faces if f.loops[0][uv_layers].select and f.select}

	getFacesIslands(bm, uv_layers, selected_faces, selected_islands, disordered_islands_selected)

	# Collect target UV islands
	if target_faces is None:
		return selected_islands, []

	target_islands = []
	target_faces.difference_update(disordered_islands_selected)
	bpy.ops.uv.select_all(action='DESELECT')
	for f in target_faces:
		f.loops[0][uv_layers].select = True
	bpy.ops.uv.select_linked()
	disordered_islands_targets = {f for f in bm.faces if f.loops[0][uv_layers].select and f.select}

	getFacesIslands(bm, uv_layers, target_faces, target_islands, disordered_islands_targets)

	if restore_selected:
		bpy.ops.uv.select_all(action='DESELECT')
		set_selected_faces(selected_faces, bm, uv_layers)

	return selected_islands, target_islands



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

def find_min_rotate_angle(angle):
    angle = math.degrees(angle)
    x = math.fmod(angle, 90)
    if angle > 45:
        y = 90 - x
        angle = -y if y < x else x
    elif angle < -45:
        y = -90 - x
        angle = -y if y > x else x

    return math.radians(angle)

# It is not quite clear what the reason is, but if the islands are very small,
# and you press the sort button repeatedly, the program sometimes crashes without errors.
# Maybe it is caused by a suboptimal loop -> utilities_uv.multi_object_loop.
# If such a problem occurs, you should check for island->BBox['area']>0.
# But hopefully this problem was only in my other script.
def alignMinimalBounds(bm, uv_layers, selected_faces):
    uv_coords = [l[uv_layers].uv for f in selected_faces for l in f.loops]
    align_angle_pre = mathutils.geometry.box_fit_2d(uv_coords)
    align_angle = find_min_rotate_angle(align_angle_pre)

    if align_angle > 0.001 or align_angle < 0.001:
        rot_matrix = mathutils.Matrix(((math.cos(align_angle), math.sin(align_angle)),
                                      (-math.sin(align_angle), math.cos(align_angle))))
        for f in selected_faces:
            for l in f.loops:
                l[uv_layers].uv = l[uv_layers].uv @ rot_matrix


def calc_min_align_angle(selected_faces, uv_layers):
    uv_coords = [l[uv_layers].uv for f in selected_faces for l in f.loops]
    align_angle_pre = mathutils.geometry.box_fit_2d(uv_coords)
    return find_min_rotate_angle(align_angle_pre)


def alignMinimalBounds_multi():
	steps = 8
	angle = 45	# Starting Angle, half each step

	all_ob_bounds = multi_object_loop(getSelectionBBox, need_results=True)
	if not any(all_ob_bounds):
		return {'CANCELLED'}

	bboxPrevious = get_BBOX_multi(all_ob_bounds)

	for _ in range(0, steps):
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
