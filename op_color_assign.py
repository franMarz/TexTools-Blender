import bpy
import bmesh

from . import utilities_color
from . import utilities_ui


gamma = 2.2



class op(bpy.types.Operator):
	bl_idname = "uv.textools_color_assign"
	bl_label = "Assign Color"
	bl_description = "Assign color to selected Objects or faces in Edit Mode"
	bl_options = {'UNDO'}

	index : bpy.props.IntProperty(description="Color Index", default=0)

	@classmethod
	def poll(cls, context):
		if bpy.context.area.ui_type != 'UV':
			return False
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object not in bpy.context.selected_objects:
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		return True
	

	def execute(self, context):
		assign_color(self, context, self.index)
		return {'FINISHED'}



def assign_color(self, context, index):
	selected_obj = bpy.context.selected_objects.copy()

	previous_mode = 'OBJECT'
	if len(selected_obj) == 1:
		previous_mode = bpy.context.active_object.mode


	for obj in selected_obj:
		# Select object
		bpy.ops.object.mode_set(mode='OBJECT')
		bpy.ops.object.select_all(action='DESELECT')
		obj.select_set( state = True, view_layer = None)
		bpy.context.view_layer.objects.active = obj

		# Enter Edit mode
		bpy.ops.object.mode_set(mode='EDIT')
		bm = bmesh.from_edit_mesh(obj.data)

		if previous_mode == 'OBJECT':
			bpy.ops.mesh.select_all(action='SELECT')
		
		if bpy.context.scene.texToolsSettings.color_assign_mode == 'MATERIALS':
			# Verify material slots
			for _ in range(index+1):
				if index >= len(obj.material_slots):
					bpy.ops.object.material_slot_add()

			utilities_color.assign_slot(obj, index)

			# Assign to selection
			obj.active_material_index = index
			bpy.ops.object.material_slot_assign()

		else:	#mode == VERTEXCOLORS
			color = utilities_color.get_color(index).copy()
			if bpy.context.preferences.addons[__package__].preferences.bool_color_id_vertex_color_gamma:
				# Fix Gamma
				color[0] = pow(color[0],1/gamma)
				color[1] = pow(color[1],1/gamma)
				color[2] = pow(color[2],1/gamma)

			# Manage Vertex Color layer
			context_override = utilities_ui.GetContextView3D()
			if not context_override:
				self.report({'ERROR_INVALID_INPUT'}, "This tool requires an available View3D view.")
				return {'CANCELLED'}
			if 'TexTools_colorID' not in obj.data.vertex_colors:
				obj.data.vertex_colors.new(name='TexTools_colorID')
			obj.data.vertex_colors['TexTools_colorID'].active = True

			# Paint
			bpy.ops.object.mode_set(mode='VERTEX_PAINT')
			bpy.context.tool_settings.vertex_paint.brush.color = color
			bpy.context.object.data.use_paint_mask = True
			with bpy.context.temp_override(**context_override):
				bpy.ops.paint.vertex_color_set()
			bpy.context.object.data.use_paint_mask = False


	# restore mode
	bpy.ops.object.mode_set(mode='OBJECT')
	bpy.ops.object.select_all(action='DESELECT')
	for obj in selected_obj:
		obj.select_set( state = True, view_layer = None)
	bpy.ops.object.mode_set(mode=previous_mode)

	# Show Material or Data Tab
	utilities_color.update_properties_tab()

	#Change View mode
	utilities_color.update_view_mode()
