import bpy
import os

from . import utilities_uv



class op(bpy.types.Operator):
	bl_idname = "uv.textools_texel_checker_map"
	bl_label = "Checker Map"
	bl_description = "Add different checker map overrides to the selected Objects and cycle between them and the original Materials"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		if not bpy.context.active_object:
			return False
		if bpy.context.object.mode != 'EDIT' and bpy.context.object.mode != 'OBJECT':
			return False
		if bpy.context.object.mode == 'OBJECT' and len(bpy.context.selected_objects) == 0:
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		if not bpy.context.object.data.uv_layers:
			return False
		return True


	def execute(self, context):
		premode = bpy.context.active_object.mode
		utilities_uv.multi_object_loop(assign_checker_map)
		bpy.ops.object.mode_set(mode=premode)
		# Change Viewport Shading Type to MATERIAL
		for area in bpy.context.screen.areas:
			if area.type == 'VIEW_3D':
				for space in area.spaces:
					if space.type == 'VIEW_3D':
						space.shading.type = 'MATERIAL'
							#space.shading.color_type = 'TEXTURE'
		# Force redraw of viewport to update texture
		bpy.context.view_layer.update()
		return {'FINISHED'}



def assign_checker_map():
	obj = bpy.context.active_object
	if obj.type != 'MESH' or not obj.data.uv_layers:
		return

	bpy.ops.object.mode_set(mode='OBJECT')

	# Apply checker maps
	if obj.modifiers:
		for m in obj.modifiers:
			if m.name == 'TT-checker-override':
				if m.node_group.name == 'TT-checker-override-uvgrid':
					m.node_group = get_nodegroup('TT-checker-override-colorgrid')
				elif m.node_group.name == 'TT-checker-override-colorgrid':
					m.node_group = get_nodegroup('TT-checker-override-gravity')
				elif m.node_group.name == 'TT-checker-override-gravity':
					obj.modifiers.remove(m)
				break
		else:
			obj.modifiers.new(name='TT-checker-override', type='NODES')
			obj.modifiers.active.node_group = get_nodegroup('TT-checker-override-uvgrid')
			obj.modifiers.active.show_render = False
	else:
		obj.modifiers.new(name='TT-checker-override', type='NODES')
		obj.modifiers.active.node_group = get_nodegroup('TT-checker-override-uvgrid')
		obj.modifiers.active.show_render = False

	bpy.ops.object.modifier_move_to_index(modifier='TT-checker-override', index=len(obj.modifiers)-1)
	if 'TT_CM_Scale' not in obj:
		obj.TT_CM_Scale = 1



def get_nodegroup(name):
	if bpy.data.node_groups.get(name) is None:
		path = os.path.join(os.path.dirname(__file__), "resources/materials_3.0.blend", "NodeTree")
		bpy.ops.wm.append(filename=name, directory=path, link=False, autoselect=False)

	return bpy.data.node_groups.get(name)
