import bpy
import bmesh
import operator
from mathutils import Vector
from collections import defaultdict
from math import pi
import math
from . import utilities_uv
from . import utilities_texel
from . import utilities_meshtex


def get_mode():
	if not utilities_meshtex.find_uv_mesh([bpy.context.active_object]):
		# Create UV mesh from face selection
		if bpy.context.active_object and bpy.context.active_object.mode == 'EDIT':
			return 'FACES'

		# Create UV mesh from whole object
		if bpy.context.active_object and bpy.context.active_object.type == 'MESH':
			if "SurfaceDeform" not in bpy.context.active_object.modifiers:
				return 'OBJECT'

	return 'UNDEFINED'



class op(bpy.types.Operator):
	bl_idname = "uv.textools_meshtex_create"
	bl_label = "UV Mesh"
	bl_description = "Create a new UV Mesh from your selected object"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		if get_mode() == 'UNDEFINED':
			return False
		return True


	def execute(self, context):
		create_uv_mesh(self, bpy.context.active_object)	
		return {'FINISHED'}



def create_uv_mesh(self, obj):
	
	mode = bpy.context.active_object.mode

	# Select
	bpy.ops.object.mode_set(mode='OBJECT')
	bpy.ops.object.select_all(action='DESELECT')
	obj.select_set( state = True, view_layer = None)
	bpy.context.view_layer.objects.active = obj

	
	bpy.ops.object.mode_set(mode='EDIT')
	bpy.ops.mesh.select_mode(type="FACE")
	bpy.context.scene.tool_settings.use_uv_select_sync = False


	# Select all if OBJECT mode
	if mode == 'OBJECT':
		bpy.ops.mesh.select_all(action='SELECT')
		# bpy.ops.uv.select_all(action='SELECT')

	# Create UV Map
	if not obj.data.uv_layers:
		if mode == 'OBJECT':
			# Smart UV project
			bpy.ops.uv.smart_project(
				angle_limit=65, 
				island_margin=0.5, 
				user_area_weight=0, 
				use_aspect=True, 
				stretch_to_bounds=True
			)
		elif mode == 'EDIT':
			# Iron Faces
			bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0)
			bpy.ops.uv.textools_unwrap_faces_iron()

	
	bm = bmesh.from_edit_mesh(obj.data)
	uv_layers = bm.loops.layers.uv.verify()

	#Collect UV islands
	bpy.ops.uv.select_all(action='SELECT')
	islands = utilities_uv.getSelectionIslands(bm, uv_layers)

	# Collect clusters 
	uvs = {}
	clusters = []
	uv_to_clusters = {}
	vert_to_clusters = {}

	face_area_view = 0
	face_area_uv = 0

	for face in bm.faces:
		if face.select:
			# Calculate triangle area for UV and View
			# Triangle Verts
			tri_uv = [loop[uv_layers].uv for loop in face.loops ]
			tri_vt = [vert.co for vert in face.verts]

			#Triangle Areas
			face_area_view += math.sqrt(utilities_texel.get_area_triangle(
				tri_vt[0], 
				tri_vt[1], 
				tri_vt[2] 
			))
			face_area_uv += math.sqrt(utilities_texel.get_area_triangle(
				tri_uv[0], 
				tri_uv[1], 
				tri_uv[2]
			))

			for i in range(len(face.loops)):
				v = face.loops[i]
				uv = Get_UVSet(uvs, bm, uv_layers, face.index, i)

				# 	# clusters
				isMerged = False
				for cluster in clusters:
					d = (uv.pos() - cluster.uvs[0].pos()).length
					if d <= 0.0000001:
						#Merge
						cluster.append(uv)
						uv_to_clusters[uv] = cluster
						if v not in vert_to_clusters:
							vert_to_clusters[v] = cluster
						isMerged = True;
						break;
				if not isMerged:
					#New Group
					clusters.append( UVCluster(v, [uv]) )
					uv_to_clusters[uv] = clusters[-1]
					if v not in vert_to_clusters:
						vert_to_clusters[v] = clusters[-1]
	
	scale = face_area_view / face_area_uv

	print("Scale {}x   {} | {}".format(scale, face_area_view, face_area_uv))
	print("Islands {}x".format(len(islands)))
	print("UV Vert Clusters {}x".format(len(clusters)))

	m_vert_cluster = []
	m_verts_org = []
	m_verts_A = []
	m_verts_B = []
	m_faces = []
	
	for island in islands:
		for face in island:
			f = []
			for i in range(len(face.loops)):
				v = face.loops[i].vert
				uv = Get_UVSet(uvs, bm, uv_layers, face.index, i)
				c = uv_to_clusters[ uv ]

				index = 0
				if c in m_vert_cluster:
					index = m_vert_cluster.index(c)

				else:
					index = len(m_vert_cluster)
					m_vert_cluster.append(c)
					m_verts_org.append(v)

					m_verts_A.append( Vector((uv.pos().x*scale - scale/2, uv.pos().y*scale -scale/2, 0)) )
					m_verts_B.append( obj.matrix_world @ v.co - bpy.context.scene.cursor.location  )
					
				f.append(index)

			m_faces.append(f)

	# Add UV bounds as edges
	verts = [
		Vector((-scale/2, -scale/2, 0)),
		Vector(( scale/2, -scale/2, 0)),
		Vector(( scale/2, scale/2, 0)),
		Vector((-scale/2, scale/2, 0)),
	]
	m_verts_A = m_verts_A+verts;
	m_verts_B = m_verts_B+verts;

	bpy.ops.object.mode_set(mode='OBJECT')

	# Create Mesh
	mesh = bpy.data.meshes.new("mesh_texture")
	mesh.from_pydata(m_verts_A, [], m_faces)
	mesh.update()
	mesh_obj = bpy.data.objects.new("UV_mesh {0}".format(obj.name), mesh)
	mesh_obj.location = bpy.context.scene.cursor.location
	bpy.context.collection.objects.link(mesh_obj)

	# Add shape keys
	mesh_obj.shape_key_add(name="uv", from_mix=True)
	mesh_obj.shape_key_add(name="model", from_mix=True)
	mesh_obj.active_shape_key_index = 1

	# Select
	bpy.context.view_layer.objects.active = mesh_obj
	mesh_obj.select_set( state = True, view_layer = None)

	bpy.ops.object.mode_set(mode='EDIT')
	bm = bmesh.from_edit_mesh(mesh_obj.data)
	
	if hasattr(bm.faces, "ensure_lookup_table"): 
		bm.faces.ensure_lookup_table()
		bm.verts.ensure_lookup_table()

	bm.edges.new((bm.verts[-4], bm.verts[-3]))
	bm.edges.new((bm.verts[-3], bm.verts[-2]))
	bm.edges.new((bm.verts[-2], bm.verts[-1]))
	bm.edges.new((bm.verts[-1], bm.verts[-4]))


	for i in range(len(m_verts_B)):
		bm.verts[i].co = m_verts_B[i]


	# Split concave faces to resolve issues with Shape deform
	bpy.context.object.active_shape_key_index = 0
	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
	bpy.ops.mesh.select_all(action='SELECT')
	bpy.ops.mesh.vert_connect_concave()


	bpy.ops.object.mode_set(mode='OBJECT')


	# Display as edges only
	mesh_obj.show_wire = True
	mesh_obj.show_all_edges = True
	# mesh_obj.data.display_type = 'WIRE' #Esta linea deberia llevarte a la opcion wireframe
	


	bpy.ops.object.select_all(action='DESELECT')
	mesh_obj.select_set( state = True, view_layer = None)
	bpy.context.view_layer.objects.active = mesh_obj



def Get_UVSet(uvs, bm, layer, index_face, index_loop):
	index = get_uv_index(index_face, index_loop)
	if index not in uvs:
		uvs[index] = UVSet(bm, layer, index_face, index_loop)

	return uvs[index]



class UVSet:
	bm = None
	layer = None
	index_face = 0
	index_loop = 0

	def __init__(self, bm, layer, index_face, index_loop):
		self.bm = bm
		self.layer = layer
		self.index_face = index_face
		self.index_loop = index_loop
		
	def uv(self):
		face = self.bm.faces[self.index_face]
		return face.loops[self.index_loop][self.layer]

	def pos(self):
		return self.uv().uv

	def vertex(self):
		return face.loops[self.index_loop].vertex



def get_uv_index(index_face, index_loop):
	return (index_face*1000000)+index_loop

	
class UVCluster:
	uvs = []
	vertex = None
	
	def __init__(self, vertex, uvs):
		self.vertex = vertex
		self.uvs = uvs

	def append(self, uv):
		self.uvs.append(uv)

bpy.utils.register_class(op)
