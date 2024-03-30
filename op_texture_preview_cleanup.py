import bpy



class op(bpy.types.Operator):
	bl_idname = "uv.textools_texture_preview_cleanup"
	bl_label = "Texture Preview Cleanup"
	bl_description = "Remove and unlink texture preview data from the selected Objects; + Alt , it's applied to all Objects in the Blendfile"
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
					if m.name == 'TT-material-override':
						obj.modifiers.remove(m)

		for nodegroup in bpy.data.node_groups:
			if nodegroup and 'TT-material-override' in nodegroup.name:
				if not nodegroup.users:
					bpy.data.node_groups.remove(nodegroup, do_unlink=True)

		for material in bpy.data.materials:
			if material and 'TT_material_override' in material.name:
				if not material.users:
					bpy.data.materials.remove(material, do_unlink=True)

		bpy.ops.object.mode_set(mode=premode)
		return {'FINISHED'}
