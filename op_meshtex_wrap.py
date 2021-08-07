import bpy
import bmesh

from . import utilities_meshtex



class op(bpy.types.Operator):
	bl_idname = "uv.textools_meshtex_wrap"
	bl_label = "Wrap Mesh Texture"
	bl_description = "Swap UV to XYZ coordinates"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		if (not bpy.context.active_object) or bpy.context.active_object.mode != 'OBJECT':
			return False
			
		# Wrap texture mesh around UV mesh
		if len(bpy.context.selected_objects) >= 1:
			# Find a UV mesh
			if utilities_meshtex.find_uv_mesh(bpy.context.selected_objects):
				# Find 1 or more meshes to wrap
				if len( utilities_meshtex.find_texture_meshes(bpy.context.selected_objects)) > 0:
					return True
		return False


	def execute(self, context):
		wrap_meshtex(self)
		return {'FINISHED'}



def wrap_meshtex(self):
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

	print("Wrap {} texture meshes".format(len(obj_textures)))

	# Undo wrapping
	if bpy.context.scene.texToolsSettings.meshtexture_wrap > 0:
		bpy.context.scene.texToolsSettings.meshtexture_wrap = 0
		# Clear modifiers
		utilities_meshtex.uv_mesh_clear(obj_uv)
		return
	
	# Setup Thickness
	utilities_meshtex.uv_mesh_fit(obj_uv, obj_textures)

	for obj in obj_textures:
		# Delete previous modifiers
		for modifier in obj.modifiers:
			if modifier.type == 'SURFACE_DEFORM':
				obj.modifiers.remove(modifier)
				break

		# Add mesh modifier
		modifier_deform = obj.modifiers.new(name="SurfaceDeform", type='SURFACE_DEFORM')
		modifier_deform.target = obj_uv

		obj.select_set( state = True, view_layer = None)
		bpy.context.view_layer.objects.active = obj
		bpy.ops.object.surfacedeform_bind(modifier="SurfaceDeform")

	# Apply wrapped morph state
	bpy.context.scene.texToolsSettings.meshtexture_wrap = 1


bpy.utils.register_class(op)
