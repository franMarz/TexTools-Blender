import bpy
import bmesh

from . import utilities_color


class op(bpy.types.Operator):
	bl_idname = "uv.textools_color_select"
	bl_label = "Select by Color"
	bl_description = "Select faces by this color"
	bl_options = {'REGISTER', 'UNDO'}
	
	index : bpy.props.IntProperty(description="Color Index", default=0)

	@classmethod
	def poll(cls, context):
		if not bpy.context.active_object:
			return False

		if bpy.context.active_object not in bpy.context.selected_objects:
			return False

		# Allow only 1 object selected
		if len(bpy.context.selected_objects) != 1:
			return False

		if bpy.context.active_object.type != 'MESH':
			return False

		#Only in UV editor mode
		if bpy.context.area.type != 'IMAGE_EDITOR':
			return False

		return True
	
	def execute(self, context):
		select_color(self, context, self.index)
		return {'FINISHED'}



def select_color(self, context, index):
	print("Color select "+str(index) )

	obj = bpy.context.active_object
	
	# Check for missing slots, materials,..
	if index >= len(obj.material_slots):
		self.report({'ERROR_INVALID_INPUT'}, "No material slot for color '{}' found".format(index) )
		return

	if not obj.material_slots[index].material:
		self.report({'ERROR_INVALID_INPUT'}, "No material found for material slot '{}'".format(index) )
		return		

	if bpy.context.active_object.mode != 'EDIT':
		bpy.ops.object.mode_set(mode='EDIT')

	# Select faces
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
	bpy.ops.mesh.select_all(action='DESELECT')
	for face in bm.faces:
		if face.material_index == index:
			face.select = True

	# Show Material Tab
	utilities_color.update_properties_tab()

	#Change View mode
	utilities_color.update_view_mode()


bpy.utils.register_class(op)
