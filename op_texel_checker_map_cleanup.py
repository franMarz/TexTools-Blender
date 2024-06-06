import bpy

from . import utilities_texel



class op(bpy.types.Operator):
	bl_idname = "uv.textools_texel_checker_map_cleanup"
	bl_label = "Checker Map Cleanup"
	bl_description = "Remove and unlink checker map data from the selected Objects; + Alt , it's applied to all Objects in the Blendfile"
	bl_options = {'REGISTER', 'UNDO'}

	bool_all: bpy.props.BoolProperty(name="On all Objects", default=False)

	def invoke(self, context, event):
		self.bool_all = event.alt
		self.execute(context)
		return {'FINISHED'}


	def execute(self, context):
		premode = bpy.context.active_object.mode

		if self.bool_all:
			group = {ob for ob in bpy.data.objects if ob.type == 'MESH'}
		else:
			bpy.ops.object.mode_set(mode='EDIT', toggle=False)
			group = {ob for ob in bpy.context.objects_in_mode_unique_data if ob.type == 'MESH' and ob.select_get()}
			bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

		for obj in group:
			if obj.modifiers:
				for m in obj.modifiers:
					if m.name == 'TT-checker-override':
						obj.modifiers.remove(m)
			del obj['TT_CM_Scale']

		for nodegroup in bpy.data.node_groups:
			if nodegroup and 'TT-checker-override' in nodegroup.name:
				if not nodegroup.users:
					bpy.data.node_groups.remove(nodegroup, do_unlink=True)

		utilities_texel.checker_images_cleanup()

		bpy.ops.object.mode_set(mode=premode)
		return {'FINISHED'}
