import bpy

from . import utilities_ui
from . import utilities_uv



class op(bpy.types.Operator):
	bl_idname = "uv.textools_uv_channel_add"
	bl_label = "Add UV Channel"
	bl_description = "Add a new UV channel to all the selected Objects"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		return True


	def execute(self, context):
		premode = bpy.context.active_object.mode
		utilities_uv.multi_object_loop(adduvs, self, context)
		bpy.ops.object.mode_set(mode=premode)
		return {'FINISHED'}



def adduvs(self, context):
	if len( bpy.context.object.data.uv_layers ) == 0:
		bpy.context.active_object.data.uv_layers.new(name="UVMap")
	else:
		# Add new UV channel based on last
		#bpy.ops.mesh.uv_texture_add()
		name = "UVMap" + str(len(bpy.context.active_object.data.uv_layers)+1)
		bpy.context.active_object.data.uv_layers.new(name=name)

	# Get current index
	index = len(bpy.context.object.data.uv_layers)-1
	bpy.context.object.data.uv_layers.active_index = index
	bpy.context.scene.texToolsSettings.uv_channel = str(index)
	bpy.context.active_object.data.uv_layers[0].active_render = True


bpy.utils.register_class(op)
