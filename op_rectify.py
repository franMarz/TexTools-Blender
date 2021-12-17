import bpy
import bmesh

from math import hypot
from collections import defaultdict
from . import utilities_uv


precision = 3



class op(bpy.types.Operator):
	bl_idname = "uv.textools_rectify"
	bl_label = "Rectify"
	bl_description = "Align selected faces or verts to rectangular distribution."
	bl_options = {'REGISTER', 'UNDO'}
	
	@classmethod
	def poll(cls, context):
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object.mode != 'EDIT':
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		if not bpy.context.active_object.data.uv_layers:
			return False
		if context.scene.tool_settings.use_uv_select_sync:
			return False
		return True


	def execute(self, context):
		utilities_uv.multi_object_loop(rectify, self, context)
		return {'FINISHED'}



def rectify(self, context, me=None, bm=None, uv_layers=None):
	if me is None:
		me = bpy.context.active_object.data
		bm = bmesh.from_edit_mesh(me)
		uv_layers = bm.loops.layers.uv.verify()

	# Store selection
	faces_loops = utilities_uv.selection_store(bm, uv_layers, return_selected_faces_loops=True)

	# Find selection islands
	islands = utilities_uv.splittedSelectionByIsland( bm, uv_layers, set(faces_loops.keys()) )

	for island in islands:
		bpy.ops.uv.select_all(action='DESELECT')
		utilities_uv.set_selected_faces(island, bm, uv_layers)
		main(me, bm, uv_layers, island, faces_loops)
	
	# Restore selection
	utilities_uv.selection_restore(bm, uv_layers)



def main(me, bm, uv_layers, selFacesMix, faces_loops, return_discarded_faces=False):

	filteredVerts, selFaces, vertsDict, discarded_faces = ListsOfVerts(bm, uv_layers, selFacesMix, faces_loops)   

	if len(filteredVerts) < 2:
		if return_discarded_faces:
			return set()
		return

	if not selFaces:
		if discarded_faces:
			if return_discarded_faces:
				return discarded_faces
		else:
			# Line is selected -> align on axis
			for luv in filteredVerts:
				x = round(luv.uv.x, precision)
				y = round(luv.uv.y, precision)
				if luv not in vertsDict[(x, y)]:
					vertsDict[(x, y)].append(luv)

			areLinedX = True
			areLinedY = True
			allowedError = 0.00001
			valX = filteredVerts[0].uv.x
			valY = filteredVerts[0].uv.y
			for v in filteredVerts:
				if abs(valX - v.uv.x) > allowedError:
					areLinedX = False
				if abs(valY - v.uv.y) > allowedError:
					areLinedY = False
			
			if not (areLinedX or areLinedY):
				verts = filteredVerts
				verts.sort(key=lambda x: x.uv[0])	#sort by .x
				first = verts[0]
				last = verts[len(verts)-1]

				horizontal = True
				if ((last.uv.x - first.uv.x) > 0.0009):
					slope = (last.uv.y - first.uv.y)/(last.uv.x - first.uv.x)
					if (slope > 1) or (slope <-1):
						horizontal = False 
				else:
					horizontal = False
				
				if horizontal == True:
					#scale to 0 on Y
					for v in verts:
						x = round(v.uv.x, precision)
						y = round(v.uv.y, precision)
						for luv in vertsDict[(x, y)]:
							luv.uv.y = first.uv.y
				else:
					#scale to 0 on X
					verts.sort(key=lambda x: x.uv[1])	#sort by .y
					verts.reverse()	#reverse because y values drop from up to down
					first = verts[0]
					last = verts[len(verts)-1]

					for v in verts:
						x = round(v.uv.x, precision)
						y = round(v.uv.y, precision)
						for luv in vertsDict[(x, y)]:
							luv.uv.x = first.uv.x

	else:
		# At least one face is selected -> rectify
		targetFace = bm.faces.active
		# Active face checks
		if targetFace is None or len({loop for loop in targetFace.loops}.intersection(filteredVerts)) != len(targetFace.verts) or targetFace.select == False or len(targetFace.verts) != 4:
			targetFace = selFaces[0]
		
		ShapeFace(uv_layers, targetFace, vertsDict)
		
		FollowActiveUV(me, targetFace, selFaces)

		bmesh.update_edit_mesh(me, loop_triangles=False)

		if return_discarded_faces:
			return discarded_faces



def ListsOfVerts(bm, uv_layers, selFacesMix, faces_loops):
	allEdgeVerts = []
	filteredVerts = []
	selFaces = []
	discarded_faces = set()
	vertsDict = defaultdict(list)
	
	for f in selFacesMix:
		isFaceSel = True
		facesEdgeVerts = [l[uv_layers] for l in faces_loops[f]]
		if len(faces_loops[f]) < len(f.loops):
			isFaceSel = False
		
		allEdgeVerts.extend(facesEdgeVerts)
		if isFaceSel:
			if len(f.verts) != 4:
				filteredVerts.extend(facesEdgeVerts)
				discarded_faces.add(f)
			else: 
				selFaces.append(f)
				for luv in facesEdgeVerts:
					x = round(luv.uv.x, precision)
					y = round(luv.uv.y, precision)
					vertsDict[(x, y)].append(luv)
		else:
			filteredVerts.extend(facesEdgeVerts)

	if len(filteredVerts) == 0:
		filteredVerts.extend(allEdgeVerts)

	return filteredVerts, selFaces, vertsDict, discarded_faces



def ShapeFace(uv_layers, targetFace, vertsDict):
	corners = []
	for l in targetFace.loops:
		luv = l[uv_layers]
		corners.append(luv)
	
	if len(corners) != 4:
		return
	
	firstHighest = corners[0]
	for c in corners:
		if c.uv.y > firstHighest.uv.y:
			firstHighest = c    
	corners.remove(firstHighest)
	
	secondHighest = corners[0]
	for c in corners:
		if (c.uv.y > secondHighest.uv.y):
			secondHighest = c
	
	if firstHighest.uv.x < secondHighest.uv.x:
		leftUp = firstHighest
		rightUp = secondHighest
	else:
		leftUp = secondHighest
		rightUp = firstHighest
	corners.remove(secondHighest)
	
	firstLowest = corners[0]
	secondLowest = corners[1]
	
	if firstLowest.uv.x < secondLowest.uv.x:
		leftDown = firstLowest
		rightDown = secondLowest
	else:
		leftDown = secondLowest
		rightDown = firstLowest
	

	verts = [leftUp, leftDown, rightDown, rightUp]

	ratioX, ratioY = ImageRatio()
	min = float('inf')
	minV = verts[0]
	for v in verts:
		if v is None:
			continue
		for area in bpy.context.screen.areas:
			if area.type == 'IMAGE_EDITOR':
				loc = area.spaces[0].cursor_location
				hyp = hypot(loc.x/ratioX -v.uv.x, loc.y/ratioY -v.uv.y)
				if (hyp < min):
					min = hyp
					minV = v

	MakeUvFaceEqualRectangle(vertsDict, leftUp, rightUp, rightDown, leftDown, minV)



def MakeUvFaceEqualRectangle(vertsDict, leftUp, rightUp, rightDown, leftDown, startv):
	ratioX, ratioY = ImageRatio()
	ratio = ratioX/ratioY
	
	if startv is None: startv = leftUp.uv
	elif AreVertsQuasiEqual(startv, rightUp): startv = rightUp.uv
	elif AreVertsQuasiEqual(startv, rightDown): startv = rightDown.uv
	elif AreVertsQuasiEqual(startv, leftDown): startv = leftDown.uv
	else: startv = leftUp.uv
	
	leftUp = leftUp.uv
	rightUp = rightUp.uv
	rightDown = rightDown.uv
	leftDown = leftDown.uv    
   
	if (startv == leftUp): 
		finalScaleX = hypotVert(leftUp, rightUp)
		finalScaleY = hypotVert(leftUp, leftDown)
		currRowX = leftUp.x
		currRowY = leftUp.y
	
	elif (startv == rightUp):
		finalScaleX = hypotVert(rightUp, leftUp)
		finalScaleY = hypotVert(rightUp, rightDown)
		currRowX = rightUp.x - finalScaleX
		currRowY = rightUp.y
	   
	elif (startv == rightDown):
		finalScaleX = hypotVert(rightDown, leftDown)
		finalScaleY = hypotVert(rightDown, rightUp)
		currRowX = rightDown.x - finalScaleX
		currRowY = rightDown.y + finalScaleY
		
	else:
		finalScaleX = hypotVert(leftDown, rightDown)
		finalScaleY = hypotVert(leftDown, leftUp)
		currRowX = leftDown.x
		currRowY = leftDown.y +finalScaleY
	
	#leftUp, rightUp
	x = round(leftUp.x, precision)
	y = round(leftUp.y, precision)
	for v in vertsDict[(x,y)]:
		v.uv.x = currRowX
		v.uv.y = currRowY
  
	x = round(rightUp.x, precision)
	y = round(rightUp.y, precision)
	for v in vertsDict[(x,y)]:
		v.uv.x = currRowX + finalScaleX
		v.uv.y = currRowY
	
	#rightDown, leftDown
	x = round(rightDown.x, precision)
	y = round(rightDown.y, precision)    
	for v in vertsDict[(x,y)]:
		v.uv.x = currRowX + finalScaleX
		v.uv.y = currRowY - finalScaleY
		
	x = round(leftDown.x, precision)
	y = round(leftDown.y, precision)    
	for v in vertsDict[(x,y)]:
		v.uv.x = currRowX
		v.uv.y = currRowY - finalScaleY



def FollowActiveUV(me, f_act, faces):
	bm = bmesh.from_edit_mesh(me)
	uv_act = bm.loops.layers.uv.active
	
	# our own local walker
	def walk_face_init(faces, f_act):
		# first tag all faces True (so we dont uvmap them)
		for f in bm.faces:
			f.tag = True
		# then tag faces arg False
		for f in faces:
			f.tag = False
		# tag the active face True since we begin there
		f_act.tag = True

	def walk_face(f):
		# all faces in this list must be tagged
		f.tag = True
		faces_a = [f]
		faces_b = []

		while faces_a:
			for f in faces_a:
				for l in f.loops:
					l_edge = l.edge
					if l_edge.is_manifold == True and l_edge.seam == False:
						l_other = l.link_loop_radial_next
						f_other = l_other.face
						if not f_other.tag:
							yield (f, l, f_other)
							f_other.tag = True
							faces_b.append(f_other)
			# swap
			faces_a, faces_b = faces_b, faces_a
			faces_b.clear()

	def walk_edgeloop(l):
		"""
		Could make this a generic function
		"""
		e_first = l.edge
		e = None
		while True:
			e = l.edge
			yield e

			# don't step past non-manifold edges
			if e.is_manifold:
				# walk around the quad and then onto the next face
				l = l.link_loop_radial_next
				if len(l.face.verts) == 4:
					l = l.link_loop_next.link_loop_next
					if l.edge is e_first:
						break
				else:
					break
			else:
				break

	def extrapolate_uv(fac,
					   l_a_outer, l_a_inner,
					   l_b_outer, l_b_inner):
		l_b_inner[:] = l_a_inner
		l_b_outer[:] = l_a_inner + ((l_a_inner - l_a_outer) * fac)

	def apply_uv(f_prev, l_prev, f_next):
		l_a = [None, None, None, None]
		l_b = [None, None, None, None]

		l_a[0] = l_prev
		l_a[1] = l_a[0].link_loop_next
		l_a[2] = l_a[1].link_loop_next
		l_a[3] = l_a[2].link_loop_next

		#  l_b
		#  +-----------+
		#  |(3)        |(2)
		#  |           |
		#  |l_next(0)  |(1)
		#  +-----------+
		#        ^
		#  l_a   |
		#  +-----------+
		#  |l_prev(0)  |(1)
		#  |    (f)    |
		#  |(3)        |(2)
		#  +-----------+
		#  copy from this face to the one above.

		# get the other loops
		l_next = l_prev.link_loop_radial_next
		if l_next.vert != l_prev.vert:
			l_b[1] = l_next
			l_b[0] = l_b[1].link_loop_next
			l_b[3] = l_b[0].link_loop_next
			l_b[2] = l_b[3].link_loop_next
		else:
			l_b[0] = l_next
			l_b[1] = l_b[0].link_loop_next
			l_b[2] = l_b[1].link_loop_next
			l_b[3] = l_b[2].link_loop_next

		l_a_uv = [l[uv_act].uv for l in l_a]
		l_b_uv = [l[uv_act].uv for l in l_b]

		try:
			fac = edge_lengths[l_b[2].edge.index][0] / edge_lengths[l_a[1].edge.index][0]
		except ZeroDivisionError:
			fac = 1.0

		extrapolate_uv(fac,
					   l_a_uv[3], l_a_uv[0],
					   l_b_uv[3], l_b_uv[0])

		extrapolate_uv(fac,
					   l_a_uv[2], l_a_uv[1],
					   l_b_uv[2], l_b_uv[1])


	# Calculate average length per loop if needed
	bm.edges.index_update()
	edge_lengths = [None]*len(bm.edges)
	
	for f in faces:
		# we know its a quad
		l_quad = f.loops[:] 
		l_pair_a = (l_quad[0], l_quad[2])
		l_pair_b = (l_quad[1], l_quad[3])

		for l_pair in (l_pair_a, l_pair_b):
			if edge_lengths[l_pair[0].edge.index] is None:

				edge_length_store = [-1.0]
				edge_length_accum = 0.0
				edge_length_total = 0

				for l in l_pair:
					if edge_lengths[l.edge.index] is None:
						for e in walk_edgeloop(l):
							if edge_lengths[e.index] is None:
								edge_lengths[e.index] = edge_length_store
								edge_length_accum += e.calc_length()
								edge_length_total += 1

				edge_length_store[0] = edge_length_accum / edge_length_total


	walk_face_init(faces, f_act)
	for f_triple in walk_face(f_act):
		apply_uv(*f_triple)



def ImageRatio():
	ratioX, ratioY = 256,256
	for a in bpy.context.screen.areas:
		if a.type == 'IMAGE_EDITOR':
			img = a.spaces[0].image
			if img and img.size[0] != 0:
				ratioX, ratioY = img.size[0], img.size[1]
			break
	return ratioX, ratioY



def AreVertsQuasiEqual(v1, v2, allowedError = 0.00001):
	if abs(v1.uv.x -v2.uv.x) < allowedError and abs(v1.uv.y -v2.uv.y) < allowedError:
		return True
	return False



def hypotVert(v1, v2):
	hyp = hypot(v1.x - v2.x, v1.y - v2.y)
	return hyp


bpy.utils.register_class(op)
