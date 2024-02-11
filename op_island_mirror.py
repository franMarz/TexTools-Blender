import bpy



class op(bpy.types.Operator):
	bl_idname = "uv.textools_island_mirror"
	bl_label = "Symmetry"
	bl_description = "Mirror selected faces with respect to the global Rotation/Scaling Pivot"
	bl_options = {'REGISTER', 'UNDO'}
	
	is_vertical : bpy.props.BoolProperty(name="is_vertical", options={'HIDDEN'})

	@classmethod
	def poll(cls, context):
		if bpy.context.area.ui_type != 'UV':
			return False
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		if bpy.context.active_object.mode != 'EDIT':
			return False
		if not bpy.context.object.data.uv_layers:
			return False
		if bpy.context.scene.tool_settings.use_uv_select_sync:
			return False
		return True


	def execute(self, context):
		#bpy.ops.uv.select_linked()
		bpy.ops.uv.select_split()

		is_vertical = self.is_vertical
		if is_vertical:
			bpy.ops.transform.mirror(orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, True, False))
		else:
			bpy.ops.transform.mirror(orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False))

		return {'FINISHED'}


bpy.utils.register_class(op)
