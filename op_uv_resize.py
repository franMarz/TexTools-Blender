import bpy
import bmesh
from mathutils import Vector

from . import utilities_uv
from . import utilities_ui
from . import utilities_texel

name_texture = "TT_resize_area"

utilities_ui.icon_register("op_extend_canvas_TL_active.bip")
utilities_ui.icon_register("op_extend_canvas_TR_active.bip")
utilities_ui.icon_register("op_extend_canvas_BL_active.bip")
utilities_ui.icon_register("op_extend_canvas_BR_active.bip")



def on_dropdown_size_x(self, context):
	self.size_x = int(self.dropdown_size_x)
	# context.area.tag_redraw()

def on_dropdown_size_y(self, context):
	self.size_y = int(self.dropdown_size_y)
	# context.area.tag_redraw()



class op(bpy.types.Operator):
	bl_idname = "uv.textools_uv_resize"
	bl_label = "Resize Area"
	bl_description = "Resize or extend the UV area"
	bl_options = {'REGISTER', 'UNDO'}

	size_x : bpy.props.IntProperty(
		name = "Width",
		description="padding size in pixels",
		default = 1024,
		min = 1,
		max = 8192
	)
	size_y : bpy.props.IntProperty(
		name = "Height",
		description="padding size in pixels",
		default = 1024,
		min = 1,
		max = 8192
	)
	dropdown_size_x : bpy.props.EnumProperty(
		items = utilities_ui.size_textures, 
		name = "", 
		update = on_dropdown_size_x, 
		default = '1024'
	)
	dropdown_size_y : bpy.props.EnumProperty(
		items = utilities_ui.size_textures, 
		name = "", 
		update = on_dropdown_size_y, 
		default = '1024'
	)

	direction : bpy.props.EnumProperty(name='direction', items=(
		('TL',' ','Top Left', utilities_ui.icon_get("op_extend_canvas_TL_active"),0),
		('BL',' ','Bottom Left', utilities_ui.icon_get("op_extend_canvas_BL_active"),2),
		('TR',' ','Top Right', utilities_ui.icon_get("op_extend_canvas_TR_active"),1),
		('BR',' ','Bottom Right', utilities_ui.icon_get("op_extend_canvas_BR_active"),3)
	))
	
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
		return True


	def invoke(self, context, event):
		print("Invoke resize area")
		self.size_x = bpy.context.scene.texToolsSettings.size[0]
		self.size_y = bpy.context.scene.texToolsSettings.size[1]

		for item in utilities_ui.size_textures:
			if int(item[0]) == self.size_x:
				self.dropdown_size_x = item[0]
				break
		for item in utilities_ui.size_textures:
			if int(item[0]) == self.size_y:
				self.dropdown_size_y = item[0]
				break

		return context.window_manager.invoke_props_dialog(self, width = 140)


	def check(self, context):
		return True


	def draw(self, context):
		# https://b3d.interplanety.org/en/creating-pop-up-panels-with-user-ui-in-blender-add-on/
		layout = self.layout
		layout.separator()

		# New Size
		row = layout.row()
		split = row.split(factor=0.6)
		c = split.column(align=True)
		c.prop(self, "size_x", text="X",expand=True)
		c.prop(self, "size_y", text="Y",expand=True)

		c = split.column(align=True)
		c.prop(self, "dropdown_size_x", text="")
		c.prop(self, "dropdown_size_y", text="")

		# Direction
		col = layout.column(align=True)
		col.label(text="Direction")
		row = col.row(align=True)
		row.prop(self,'direction', expand=True)

		# Summary
		size_A = "{} x {}".format(bpy.context.scene.texToolsSettings.size[0], bpy.context.scene.texToolsSettings.size[1])
		if bpy.context.scene.texToolsSettings.size[0] == bpy.context.scene.texToolsSettings.size[1]:
			size_A = "{}²".format(bpy.context.scene.texToolsSettings.size[0])
		size_B = "{} x {}".format(self.size_x, self.size_y)
		if self.size_x == self.size_y:
			size_B = "{}²".format(self.size_x)

		layout.label(text="{} to {}".format(
			size_A, size_B
		))

		layout.separator()

	
	def execute(self, context):
		#Store selection
		utilities_uv.selection_store()

		# Get start and end size
		size_A = Vector([ 
			bpy.context.scene.texToolsSettings.size[0],
			bpy.context.scene.texToolsSettings.size[1]
		])
		size_B = Vector([ 
			self.size_x,
			self.size_y
		])

		resize_uv(
			self,
			context,
			self.direction,
			size_A, 
			size_B
		)
		resize_image(
			context,
			self.direction,
			size_A,
			size_B
		)

		bpy.context.scene.texToolsSettings.size[0] = self.size_x
		bpy.context.scene.texToolsSettings.size[1] = self.size_y

		#Restore selection
		utilities_uv.selection_restore()

		return {'FINISHED'}



def resize_uv(self, context, mode, size_A, size_B):

	# Set pivot
	bpy.context.tool_settings.transform_pivot_point = 'CURSOR'
	if mode == 'TL':
		bpy.ops.uv.cursor_set(location=Vector([0,1]))
	elif mode == 'TR':
		bpy.ops.uv.cursor_set(location=Vector([1,1]))
	elif mode == 'BL':
		bpy.ops.uv.cursor_set(location=Vector([0,0]))
	elif mode == 'BR':
		bpy.ops.uv.cursor_set(location=Vector([1,0]))

	# Select all UV faces
	bpy.ops.uv.select_all(action='SELECT')

	# Resize
	scale_x = size_A.x / size_B.x
	scale_y = size_A.y / size_B.y
	bpy.ops.transform.resize(value=(scale_x, scale_y, 1.0), use_proportional_edit=False)



def resize_image(context, mode, size_A, size_B):
	# Notes: 	https://blender.stackexchange.com/questions/31514/active-image-of-uv-image-editor
	# 			https://docs.blender.org/api/blender_python_api_2_70_4/bpy.types.SpaceImageEditor.html

	if context.area.spaces.active != None:
		if context.area.spaces.active.image != None:
			image = context.area.spaces.active.image
			image_obj = utilities_texel.get_object_texture_image(bpy.context.active_object)
			if image == image_obj or name_texture in image.name:
				# Resize Image UV editor background image
				utilities_texel.image_resize(image, int(size_B.x), int(size_B.y))
		
		else:	# No Image assigned
			# Get background color from theme + 1.25x brighter
			theme = bpy.context.preferences.themes[0]
			color = theme.image_editor.space.back.copy()
			color.r*= 1.15
			color.g*= 1.15
			color.b*= 1.15

			image = None
			if name_texture in bpy.data.images:
				# TexTools Image already exists
				image = bpy.data.images[name_texture]
				image.scale( int(size_B.x), int(size_B.y) )
				image.generated_width = int(size_B.x)
				image.generated_height = int(size_B.y)
			else:
				# Create new image
				image = bpy.data.images.new(name_texture, width=int(size_B.x), height=int(size_B.y))
				image.generated_color = (color.r, color.g, color.b, 1.0)
				image.generated_type = 'BLANK'
				image.generated_width = int(size_B.x)
				image.generated_height = int(size_B.y)

			# Assign in UV view
			context.area.spaces.active.image = image

		# Clean up images and materials
		utilities_texel.checker_images_cleanup()


bpy.utils.register_class(op)
