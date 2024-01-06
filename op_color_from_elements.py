import bpy
import bmesh

from . import utilities_color



class op(bpy.types.Operator):
	bl_idname = "uv.textools_color_from_elements"
	bl_label = "Color Elements"
	bl_description = "Assign a color ID to each mesh element"
	bl_options = {'REGISTER', 'UNDO'}
	
	@classmethod
	def poll(cls, context):
		if bpy.context.area.ui_type != 'UV':
			return False
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object not in bpy.context.selected_objects:
			return False
		if len(bpy.context.selected_objects) != 1:
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		return True


	def execute(self, context):
		color_elements(self, context)
		return {'FINISHED'}



def color_elements(self, context):
	obj = bpy.context.active_object

	# Setup Edit & Face mode
	if obj.mode != 'EDIT':
		bpy.ops.object.mode_set(mode='EDIT')
	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')

	# Collect groups
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)

	faces_indices_processed = set(bm.faces)
	groups = []
	
	while faces_indices_processed:
		# Select face & extend
		bpy.ops.mesh.select_all(action='DESELECT')
		face = faces_indices_processed.pop()
		face.select = True
		bpy.ops.mesh.select_linked(delimit={'NORMAL'})

		faces = {f for f in faces_indices_processed if f.select}
		faces_indices_processed.difference_update(faces)

		faces.add(face)
		groups.append(faces)


	# Assign color count (caps automatically e.g. max 20)
	bpy.context.scene.texToolsSettings.color_ID_count = len(groups)
	gamma = 2.2

	for i in range(bpy.context.scene.texToolsSettings.color_ID_count):
		color = utilities_color.get_color_id(i, bpy.context.scene.texToolsSettings.color_ID_count)
		# Fix Gamma
		color[0] = pow(color[0] , gamma)
		color[1] = pow(color[1] , gamma)
		color[2] = pow(color[2], gamma)
		utilities_color.set_color(i, color)

	# Assign Groups to colors
	index_color = 0
	for group in groups:
		bpy.ops.mesh.select_all(action='DESELECT')
		for face in group:
			face.select = True

		for i in range(index_color+1):
			if index_color >= len(obj.material_slots):
				bpy.ops.object.material_slot_add()

		utilities_color.assign_slot(obj, index_color)

		# Assign to selection
		obj.active_material_index = index_color
		bpy.ops.object.material_slot_assign()

		index_color = (index_color+1) % bpy.context.scene.texToolsSettings.color_ID_count

	bpy.ops.object.mode_set(mode='OBJECT')
	utilities_color.validate_face_colors(obj)


bpy.utils.register_class(op)
