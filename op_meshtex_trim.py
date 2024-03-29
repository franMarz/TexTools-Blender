import bpy
import bmesh

from . import utilities_meshtex



class op(bpy.types.Operator):
	bl_idname = "uv.textools_meshtex_trim"
	bl_label = "Trim"
	bl_description = "Trim Mesh Texture"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		if (not bpy.context.active_object) or bpy.context.active_object.mode != 'OBJECT':
			return False
		if len(bpy.context.selected_objects) >= 1:
			# Find a UV mesh
			if utilities_meshtex.find_uv_mesh(bpy.context.selected_objects):
				# Find 1 or more meshes to wrap
				if len(utilities_meshtex.find_texture_meshes(bpy.context.selected_objects)) > 0:
					return True
		return False


	def execute(self, context):
		trim(self)
		return {'FINISHED'}



def trim(self):
	# Collect UV mesh
	obj_uv = utilities_meshtex.find_uv_mesh(bpy.context.selected_objects)
	if not obj_uv:
		self.report({'ERROR_INVALID_INPUT'}, "No UV mesh found" )
		return

	# Collect texture meshes
	obj_textures = utilities_meshtex.find_texture_meshes( bpy.context.selected_objects )
	
	if len(obj_textures) == 0:
		self.report({'ERROR_INVALID_INPUT'}, "No meshes found for mesh textures" )
		return

	# Setup Thickness
	utilities_meshtex.uv_mesh_fit(obj_uv, obj_textures)

	# Apply bool modifier to trim
	for obj in obj_textures:
		name = "Trim UV"
		if name in obj.modifiers:
			obj.modifiers.remove( obj.modifiers[name] )

		modifier_bool = obj.modifiers.new(name=name, type='BOOLEAN')
		modifier_bool.solver = 'FAST'
		modifier_bool.operation = 'INTERSECT'
		modifier_bool.operand_type = 'OBJECT'
		modifier_bool.object = obj_uv
