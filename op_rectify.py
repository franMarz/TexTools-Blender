import bpy
import bmesh
import operator
from mathutils import Vector
from collections import defaultdict
from math import pi
import time
from math import radians, hypot

from . import utilities_uv


class op(bpy.types.Operator):
	bl_idname = "uv.textools_rectify"
	bl_label = "Rectify"
	bl_description = "Align selected faces or verts to rectangular distribution."
	bl_options = {'REGISTER', 'UNDO'}
	
	@classmethod
	def poll(cls, context):
		if not bpy.context.active_object:
			return False

		if bpy.context.active_object.type != 'MESH':
			return False

		if bpy.context.active_object.mode != 'EDIT':
			return False

		# No Sync mode
		if context.scene.tool_settings.use_uv_select_sync:
			return False

		return True
	

	def execute(self, context):
		rectify(self, context)
		return {'FINISHED'}



precision = 3


def rectify(self, context):
	obj = bpy.context.active_object


	bm = bmesh.from_edit_mesh(obj.data)
	uv_layers = bm.loops.layers.uv.verify()

	#Store selection
	utilities_uv.selection_store()

	main(False)

	#Restore selection
	utilities_uv.selection_restore()


def main(square = False, snapToClosest = False):

	startTime = time.clock()
	obj = bpy.context.active_object
	me = obj.data
	bm = bmesh.from_edit_mesh(me)
	uv_layers = bm.loops.layers.uv.verify()
	# bm.faces.layers.tex.verify()  # currently blender needs both layers.

	face_act = bm.faces.active    
	targetFace = face_act
		
	#if len(bm.faces) > allowedFaces:
	#    operator.report({'ERROR'}, "selected more than " +str(allowedFaces) +" allowed faces.")
	#   return 

	edgeVerts, filteredVerts, selFaces, nonQuadFaces, vertsDict, noEdge = ListsOfVerts(uv_layers, bm)   
	
	if len(filteredVerts) is 0: return 
	if len(filteredVerts) is 1: 
		SnapCursorToClosestSelected(filteredVerts)
		return 
	
	cursorClosestTo = CursorClosestTo(filteredVerts)
	#line is selected
	
	if len(selFaces) is 0:
		if snapToClosest is True:
			SnapCursorToClosestSelected(filteredVerts)
			return
		
		VertsDictForLine(uv_layers, bm, filteredVerts, vertsDict)
		
		if AreVectsLinedOnAxis(filteredVerts) is False:
			ScaleTo0OnAxisAndCursor(filteredVerts, vertsDict, cursorClosestTo)
			return SuccessFinished(me, startTime)
				
		MakeEqualDistanceBetweenVertsInLine(filteredVerts, vertsDict, cursorClosestTo)
		return SuccessFinished(me, startTime)
		
   
	#else:
	
	#active face checks
	if targetFace is None or targetFace.select is False or len(targetFace.verts) is not 4:
		targetFace = selFaces[0]
	else:
		for l in targetFace.loops:
			if l[uv_layers].select is False: 
				targetFace = selFaces[0]
				break 
			
	ShapeFace(uv_layers, operator, targetFace, vertsDict, square)
	
	for nf in nonQuadFaces:
		for l in nf.loops:
			luv = l[uv_layers]
			luv.select = False
	
	if square: FollowActiveUV(operator, me, targetFace, selFaces, 'EVEN')
	else: FollowActiveUV(operator, me, targetFace, selFaces)
	
	if noEdge is False:
		#edge has ripped so we connect it back 
		for ev in edgeVerts:
			key = (round(ev.uv.x, precision), round(ev.uv.y, precision))
			if key in vertsDict:
				ev.uv = vertsDict[key][0].uv
				ev.select = True
		
	return SuccessFinished(me, startTime)



def ListsOfVerts(uv_layers, bm):
	edgeVerts = []
	allEdgeVerts = []
	filteredVerts = []
	selFaces = []
	nonQuadFaces = []
	vertsDict = defaultdict(list)                #dict
	
	for f in bm.faces:
		isFaceSel = True
		facesEdgeVerts = []
		if (f.select == False):
			continue
		
		#collect edge verts if any
		for l in f.loops:
			luv = l[uv_layers]
			if luv.select is True:
				facesEdgeVerts.append(luv)
			else: isFaceSel = False
		
		allEdgeVerts.extend(facesEdgeVerts)
		if isFaceSel:            
			if len(f.verts) is not 4:
				nonQuadFaces.append(f)
				edgeVerts.extend(facesEdgeVerts)
			else: 
				selFaces.append(f)
				
				for l in f.loops:
					luv = l[uv_layers]
					x = round(luv.uv.x, precision)
					y = round(luv.uv.y, precision)
					vertsDict[(x, y)].append(luv)
		
		else: edgeVerts.extend(facesEdgeVerts)
	
	noEdge = False
	if len(edgeVerts) is 0:
		noEdge = True
		edgeVerts.extend(allEdgeVerts)
	
	if len(selFaces) is 0:
		for ev in edgeVerts:
			if ListQuasiContainsVect(filteredVerts, ev) is False:
				filteredVerts.append(ev)
	else: filteredVerts = edgeVerts
		
	return edgeVerts, filteredVerts, selFaces, nonQuadFaces, vertsDict, noEdge



def ListQuasiContainsVect(list, vect):
	for v in list:
		if AreVertsQuasiEqual(v, vect):
			return True
	return False



def SnapCursorToClosestSelected(filteredVerts):
	#TODO: snap to closest selected 
	if len(filteredVerts) is 1: 
		SetAll2dCursorsTo(filteredVerts[0].uv.x, filteredVerts[0].uv.y)
	
	return





def VertsDictForLine(uv_layers, bm, selVerts, vertsDict):
	for f in bm.faces:
		for l in f.loops:
				luv = l[uv_layers]
				if luv.select is True:
					x = round(luv.uv.x, precision)
					y = round(luv.uv.y, precision)
		 
					vertsDict[(x, y)].append(luv)



def AreVectsLinedOnAxis(verts):
	areLinedX = True
	areLinedY = True
	allowedError = 0.0009
	valX = verts[0].uv.x
	valY = verts[0].uv.y
	for v in verts:
		if abs(valX - v.uv.x) > allowedError:
			areLinedX = False
		if abs(valY - v.uv.y) > allowedError:
			areLinedY = False
	return areLinedX or areLinedY  



def ScaleTo0OnAxisAndCursor(filteredVerts, vertsDict, startv = None, horizontal = None):      
	
	verts = filteredVerts
	verts.sort(key=lambda x: x.uv[0])      #sort by .x
	
	first = verts[0]
	last = verts[len(verts)-1]
	
	if horizontal is None:
		horizontal = True
		if ((last.uv.x - first.uv.x) >0.0009):
			slope = (last.uv.y - first.uv.y)/(last.uv.x - first.uv.x)
			if (slope > 1) or (slope <-1):
				horizontal = False 
		else: 
			horizontal = False
	
	if horizontal is True:
		if startv is None:
			startv = first  
		
		SetAll2dCursorsTo(startv.uv.x, startv.uv.y)
		#scale to 0 on Y
		ScaleTo0('Y')
		return
	   
	else:
		verts.sort(key=lambda x: x.uv[1])  #sort by .y
		verts.reverse()     #reverse because y values drop from up to down
		first = verts[0]
		last = verts[len(verts)-1]
		if startv is None:
			startv = first  

		SetAll2dCursorsTo(startv.uv.x, startv.uv.y)
		#scale to 0 on X
		ScaleTo0('X')
		return



def SetAll2dCursorsTo(x,y):
	last_area = bpy.context.area.type
	bpy.context.area.type = 'IMAGE_EDITOR'
   
	bpy.ops.uv.cursor_set(location=(x, y))

	bpy.context.area.type = last_area
	return



def CursorClosestTo(verts, allowedError = 0.025):
	ratioX, ratioY = ImageRatio()
	
	#any length that is certantly not smaller than distance of the closest
	min = 1000
	minV = verts[0]
	for v in verts:
		if v is None: continue
		for area in bpy.context.screen.areas:
			if area.type == 'IMAGE_EDITOR':
				loc = area.spaces[0].cursor_location
				hyp = hypot(loc.x/ratioX -v.uv.x, loc.y/ratioY -v.uv.y)
				if (hyp < min):
					min = hyp
					minV = v
	
	if min is not 1000: 
		return minV
	return None




def SuccessFinished(me, startTime):
	#use for backtrack of steps 
	#bpy.ops.ed.undo_push()
	bmesh.update_edit_mesh(me)
	#elapsed = round(time.clock()-startTime, 2)
	#if (elapsed >= 0.05): operator.report({'INFO'}, "UvSquares finished, elapsed:", elapsed, "s.")
	return



def ShapeFace(uv_layers, operator, targetFace, vertsDict, square):
	corners = []
	for l in targetFace.loops:
		luv = l[uv_layers]
		corners.append(luv)
	
	if len(corners) is not 4: 
		#operator.report({'ERROR'}, "bla")
		return
	
	lucv, ldcv, rucv, rdcv = Corners(corners)
	
	cct = CursorClosestTo([lucv, ldcv, rdcv, rucv])
	if cct is None: 
		cct = lucv
	
	MakeUvFaceEqualRectangle(vertsDict, lucv, rucv, rdcv, ldcv, cct, square)
	return



def MakeUvFaceEqualRectangle(vertsDict, lucv, rucv, rdcv, ldcv, startv, square = False):
	ratioX, ratioY = ImageRatio()
	ratio = ratioX/ratioY
	
	if startv is None: startv = lucv.uv
	elif AreVertsQuasiEqual(startv, rucv): startv = rucv.uv
	elif AreVertsQuasiEqual(startv, rdcv): startv = rdcv.uv
	elif AreVertsQuasiEqual(startv, ldcv): startv = ldcv.uv
	else: startv = lucv.uv
	
	lucv = lucv.uv
	rucv = rucv.uv
	rdcv = rdcv.uv
	ldcv = ldcv.uv    
   
	if (startv == lucv): 
		finalScaleX = hypotVert(lucv, rucv)
		finalScaleY = hypotVert(lucv, ldcv)
		currRowX = lucv.x
		currRowY = lucv.y
	
	elif (startv == rucv):
		finalScaleX = hypotVert(rucv, lucv)
		finalScaleY = hypotVert(rucv, rdcv)
		currRowX = rucv.x - finalScaleX
		currRowY = rucv.y
	   
	elif (startv == rdcv):
		finalScaleX = hypotVert(rdcv, ldcv)
		finalScaleY = hypotVert(rdcv, rucv)
		currRowX = rdcv.x - finalScaleX
		currRowY = rdcv.y + finalScaleY
		
	else:
		finalScaleX = hypotVert(ldcv, rdcv)
		finalScaleY = hypotVert(ldcv, lucv)
		currRowX = ldcv.x
		currRowY = ldcv.y +finalScaleY
	
	if square: finalScaleY = finalScaleX*ratio
	#lucv, rucv
	x = round(lucv.x, precision)
	y = round(lucv.y, precision)
	for v in vertsDict[(x,y)]:
		v.uv.x = currRowX
		v.uv.y = currRowY
  
	x = round(rucv.x, precision)
	y = round(rucv.y, precision)
	for v in vertsDict[(x,y)]:
		v.uv.x = currRowX + finalScaleX
		v.uv.y = currRowY
	
	#rdcv, ldcv
	x = round(rdcv.x, precision)
	y = round(rdcv.y, precision)    
	for v in vertsDict[(x,y)]:
		v.uv.x = currRowX + finalScaleX
		v.uv.y = currRowY - finalScaleY
		
	x = round(ldcv.x, precision)
	y = round(ldcv.y, precision)    
	for v in vertsDict[(x,y)]:
		v.uv.x = currRowX
		v.uv.y = currRowY - finalScaleY

		
	return



def FollowActiveUV(operator, me, f_act, faces, EXTEND_MODE = 'LENGTH_AVERAGE'):
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
					if (l_edge.is_manifold is True) and (l_edge.seam is False):
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
				# welk around the quad and then onto the next face
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

		if EXTEND_MODE == 'LENGTH_AVERAGE':
			fac = edge_lengths[l_b[2].edge.index][0] / edge_lengths[l_a[1].edge.index][0]
		elif EXTEND_MODE == 'LENGTH':
			a0, b0, c0 = l_a[3].vert.co, l_a[0].vert.co, l_b[3].vert.co
			a1, b1, c1 = l_a[2].vert.co, l_a[1].vert.co, l_b[2].vert.co

			d1 = (a0 - b0).length + (a1 - b1).length
			d2 = (b0 - c0).length + (b1 - c1).length
			try:
				fac = d2 / d1
			except ZeroDivisionError:
				fac = 1.0
		else:
			fac = 1.0

		extrapolate_uv(fac,
					   l_a_uv[3], l_a_uv[0],
					   l_b_uv[3], l_b_uv[0])

		extrapolate_uv(fac,
					   l_a_uv[2], l_a_uv[1],
					   l_b_uv[2], l_b_uv[1])

	# -------------------------------------------
	# Calculate average length per loop if needed

	if EXTEND_MODE == 'LENGTH_AVERAGE':
		bm.edges.index_update()
		edge_lengths = [None] * len(bm.edges)   #NoneType times the length of edges list
		
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

	# done with average length
	# ------------------------

	walk_face_init(faces, f_act)
	for f_triple in walk_face(f_act):
		apply_uv(*f_triple)

	bmesh.update_edit_mesh(me, False)


def ImageRatio():
	ratioX, ratioY = 256,256
	for a in bpy.context.screen.areas:
		if a.type == 'IMAGE_EDITOR':
			img = a.spaces[0].image
			if img is not None and img.size[0] is not 0:
				ratioX, ratioY = img.size[0], img.size[1]
			break
	return ratioX, ratioY



def Corners(corners):
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
	
	return leftUp, leftDown, rightUp, rightDown




def AreVertsQuasiEqual(v1, v2, allowedError = 0.0009):
	if abs(v1.uv.x -v2.uv.x) < allowedError and abs(v1.uv.y -v2.uv.y) < allowedError:
		return True
	return False



def hypotVert(v1, v2):
    hyp = hypot(v1.x - v2.x, v1.y - v2.y)
    return hyp

bpy.utils.register_class(op)