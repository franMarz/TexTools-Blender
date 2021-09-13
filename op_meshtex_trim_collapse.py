import bpy
import bmesh

from . import utilities_meshtex



def is_available():
	# If the selection contains a boolean modifier
	obj_textures = utilities_meshtex.find_texture_meshes(bpy.context.selected_objects)
	for obj in obj_textures:
		for modifier in obj.modifiers:
 			if modifier.type == 'BOOLEAN':
 				return True
	return False



class op(bpy.types.Operator):
	bl_idname = "uv.textools_meshtex_trimcollapse"
	bl_label = "Collapse"
	bl_description = "Trim Mesh Texture"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		if (not bpy.context.active_object) or bpy.context.active_object.mode != 'OBJECT':
			return False
		return is_available()


	def execute(self, context):
		collapse(self)
		return {'FINISHED'}



def collapse(self):
	# Collect texture meshes
	obj_textures = utilities_meshtex.find_texture_meshes( bpy.context.selected_objects )
	
	previous_selection = bpy.context.selected_objects.copy()
	previous_active	= bpy.context.view_layer.objects.active

	if len(obj_textures) == 0:
		self.report({'ERROR_INVALID_INPUT'}, "No meshes found for mesh textures" )
		return

	# Apply bool modifier to trim
	for obj in obj_textures:
		bpy.ops.object.select_all(action='DESELECT')
		obj.select_set( state = True, view_layer = None)
		bpy.context.view_layer.objects.active = obj
		bpy.ops.object.convert(target='MESH')

	# restore selection
	bpy.ops.object.select_all(action='DESELECT')
	for obj in previous_selection:
		obj.select_set( state = True, view_layer = None)
	bpy.context.view_layer.objects.active = previous_active


bpy.utils.register_class(op)
