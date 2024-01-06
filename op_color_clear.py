import bpy

from . import utilities_color



class op(bpy.types.Operator):
	bl_idname = "uv.textools_color_clear"
	bl_label = "Clear Colors"
	bl_description = "Clears the Materials or Vertex Colors on the active Object"
	bl_options = {'REGISTER', 'UNDO'}
	
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
		premode = bpy.context.active_object.mode
		clear_colors(self, context)
		bpy.ops.object.mode_set(mode=premode)
		return {'FINISHED'}



def clear_colors(self, context):
	obj = bpy.context.active_object

	if bpy.context.scene.texToolsSettings.color_assign_mode == 'MATERIALS':
		previous_mode = bpy.context.active_object.mode
		bpy.ops.object.mode_set(mode='OBJECT')
		# Clear material slots
		count = len(obj.material_slots)
		for i in range(count):
			bpy.ops.object.material_slot_remove()
		# Delete materials if not used
		for material in bpy.data.materials:
			if utilities_color.material_prefix in material.name:
				if not material.users:
					bpy.data.materials.remove(material, do_unlink=True)
		bpy.ops.object.mode_set(mode=previous_mode)

	else:	#mode == VERTEXCOLORS
		vclsNames = [vcl.name for vcl in obj.data.vertex_colors]
		if 'TexTools_colorID' in vclsNames :
			obj.data.vertex_colors.remove(obj.data.vertex_colors['TexTools_colorID'])

	# Show Material or Data Tab
	utilities_color.update_properties_tab()

	# Change View mode
	utilities_color.update_view_mode()

	# Enter and exit Edit Mode to force set a real vertex colors layer as active
	bpy.ops.object.mode_set(mode='EDIT')
	bpy.ops.object.mode_set(mode='OBJECT')


bpy.utils.register_class(op)
