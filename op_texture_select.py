import bpy

from . import op_bake



class op(bpy.types.Operator):
	bl_idname = "uv.textools_texture_select"
	bl_label = "Select Texture"
	bl_description = "Select the texture and bake mode"

	name : bpy.props.StringProperty(
		name="image name", 
		default = ""
	)

	@classmethod
	def poll(cls, context):
		return True


	def execute(self, context):
		select_texture(self, context)
		return {'FINISHED'}



def select_texture(self, context):
	# Set bake mode
	found_modes = []
	for mode in op_bake.modes:
		if mode in self.name:
			found_modes.append(mode)
	
	mode = max(found_modes, key=len)
	print("Found mode: "+mode)

	prop = bpy.context.scene.bl_rna.properties["TT_bake_mode"]
	enum_values = [e.identifier for e in prop.enum_items]
	
	# find matching enum
	for key in enum_values:
		if (mode+".bip") == key:
			bpy.context.scene.TT_bake_mode = key
			break
	
	# Set background image
	if self.name in bpy.data.images:
		image = bpy.data.images[self.name]
		for area in bpy.context.screen.areas:
			if area.ui_type == 'UV':
				area.spaces[0].image = image


bpy.utils.register_class(op)
