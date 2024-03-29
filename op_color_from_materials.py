import bpy

from . import utilities_color



class op(bpy.types.Operator):
	bl_idname = "uv.textools_color_from_materials"
	bl_label = "Color Elements"
	bl_description = "Assign a color ID to each mesh material slot"
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
		color_materials(self, context)
		return {'FINISHED'}



def color_materials(self, context):
	obj = bpy.context.active_object
	
	for s in range(len(obj.material_slots)):
		slot = obj.material_slots[s]
		if slot.material:
			utilities_color.assign_slot(obj, s)

	utilities_color.validate_face_colors(obj)
