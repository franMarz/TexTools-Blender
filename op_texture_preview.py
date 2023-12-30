import bpy
import os

from . import settings
from . import utilities_bake


material_prefix = "TT_atlas_"
gamma = 2.2



class op(bpy.types.Operator):
	bl_idname = "uv.textools_texture_preview"
	bl_label = "Preview Texture"
	bl_description = "Preview the background Image of the UV Editor as a Material override on the appropriate selected Object"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		if not bpy.context.active_object:
			return False
		if len(settings.sets) == 0:
			return False
		for area in bpy.context.screen.areas:
			if area.ui_type == 'UV':
				return area.spaces[0].image
		return False


	def execute(self, context):
		premode = bpy.context.active_object.mode
		preview_texture(self, context)
		bpy.ops.object.mode_set(mode=premode)
		# Change View mode to TEXTURED
		for area in bpy.context.screen.areas:
			if area.type == 'VIEW_3D':
				for space in area.spaces:
					if space.type == 'VIEW_3D':
						if space.shading.type == 'SOLID':
							space.shading.color_type = 'TEXTURE'
		# Force redraw of viewport to update texture
		bpy.context.view_layer.update()
		return {'FINISHED'}



def preview_texture(self, context):
	# Collect all low objects from bake sets
	objects = {ob for s in settings.sets for ob in s.objects_low if ob.data.uv_layers and ob.select_get()}

	if objects:
		# Get background image
		image = None 
		for area in bpy.context.screen.areas:
			if area.ui_type == 'UV':
				image = area.spaces[0].image
				break

		if image:
			bpy.ops.object.mode_set(mode='OBJECT')
			base_nodegroup = get_override_nodegroup()
			base_material = bpy.data.materials.get('TT_material_override')
			preactiv_name = bpy.context.view_layer.objects.active.name

			for obj in objects:
				bpy.context.view_layer.objects.active = obj

				material_name = 'TT_material_override-' + obj.name
				if material_name in bpy.data.materials:
					material = bpy.data.materials[material_name]
				else:
					material = base_material.copy()
					material.name = 'TT_material_override-' + obj.name
				node_image = material.node_tree.nodes["image"]
				node_image.image = image

				if obj.modifiers:
					for m in obj.modifiers:
						if 'TT-material-override' in m.name:
							if m.node_group.name == 'TT-material-override-' + obj.name:
								break
							else:
								obj.modifiers.remove(m)
					else:
						obj.modifiers.new(name='TT-material-override', type='NODES')
						nodegroup = base_nodegroup.copy()
						nodegroup.name = 'TT-material-override-' + obj.name
						node_material = nodegroup.nodes["material"]
						node_material.inputs[2].default_value = material
						obj.modifiers.active.node_group = nodegroup
						obj.modifiers.active.show_render = False
				else:
					obj.modifiers.new(name='TT-material-override', type='NODES')
					nodegroup = base_nodegroup.copy()
					nodegroup.name = 'TT-material-override-' + obj.name
					node_material = nodegroup.nodes["material"]
					node_material.inputs[2].default_value = material
					obj.modifiers.active.node_group = nodegroup
					obj.modifiers.active.show_render = False
				bpy.ops.object.modifier_move_to_index(modifier='TT-material-override', index=len(obj.modifiers)-1)

			bpy.context.view_layer.objects.active = bpy.data.objects[preactiv_name]



def get_override_nodegroup():
	if bpy.data.node_groups.get('TT-material-override') is None:
		path = os.path.join(os.path.dirname(__file__), "resources/materials_3.0.blend", "NodeTree")
		bpy.ops.wm.append(filename='TT-material-override', directory=path, link=False, autoselect=False)

	return bpy.data.node_groups.get('TT-material-override')


bpy.utils.register_class(op)
