import bpy
import math

from . import utilities_ui
from . import settings



class op(bpy.types.Operator):
	bl_idname = "uv.textools_meshtex_pattern"
	bl_label = "Create Pattern"
	bl_description = "Create mesh pattern"
	bl_options = {'REGISTER', 'UNDO'}

	mode : bpy.props.EnumProperty(items= 
		[('hexagon', 'Hexagons', ''),
		('triangle', 'Triangles', ''), 
		('diamond', 'Diamonds', ''),
		('rectangle', 'Rectangles', ''),
		('stripe', 'Stripes', ''),
		('brick', 'Bricks', '')], 
		name = "Mode", 
		default = 'brick'
	)

	size : bpy.props.IntProperty(
		name = "Size",
		description = "Size X and Y of the repetition",
		default = 4,
		min = 1,
		max = 128
	)

	scale : bpy.props.FloatProperty(
		name = "Scale",
		description = "Scale of the mesh pattern",
		default = 1,
		min = 0
	)

	@classmethod
	def poll(cls, context):
		if bpy.context.active_object and bpy.context.active_object.mode != 'OBJECT':
			return False
		return True


	def draw(self, context):
		layout = self.layout
		layout.prop(self, "mode")
		layout.prop(self, "size")
		layout.prop(self, "scale")


	def execute(self, context):
		create_pattern(self, self.mode, self.size, self.scale)
		return {'FINISHED'}


	def invoke(self, context, event):
		wm = context.window_manager
		return wm.invoke_props_dialog(self)



def AddArray(name, offset_x, offset_y, count):
	modifier = bpy.context.object.modifiers.new(name=name, type='ARRAY')
	# modifier = bpy.context.object.modifiers.new(name="{}_{}".format(name,count), type='ARRAY')
	modifier.relative_offset_displace[0] = offset_x
	modifier.relative_offset_displace[1] = offset_y
	modifier.count = count
	modifier.show_expanded = False
	return modifier



def create_pattern(self, mode, size, scale):
	# bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
	context_override = None
	if bpy.context.area.type != 'VIEW_3D':
		context_override = utilities_ui.GetContextView3D()
		if not context_override:
			self.report({'ERROR_INVALID_INPUT'}, "This tool requires an available View3D view.")
			return {'CANCELLED'}


	if mode == 'hexagon':
		bpy.ops.mesh.primitive_circle_add(vertices=6, radius=scale, fill_type='NGON')

		bpy.ops.object.mode_set(mode = 'EDIT')
		if context_override:
			if settings.bversion >= 3.2:
				with bpy.context.temp_override(**context_override):
					bpy.ops.transform.rotate(value=math.pi*0.5,  orient_axis='Z')
			else:
				bpy.ops.transform.rotate(context_override, value=math.pi*0.5,  orient_axis='Z')
		else:
			bpy.ops.transform.rotate(value=math.pi*0.5,  orient_axis='Z')

		bpy.ops.object.mode_set(mode = 'OBJECT')

		AddArray("Array0", 0.75,-0.5,2)
		AddArray("Array1", 0,-0.66666666666,size)
		AddArray("Array2", 1 - (0.5/3.5),0,int(size*0.66))


	elif mode == 'triangle':
		bpy.ops.mesh.primitive_circle_add(vertices=3, radius=scale, fill_type='NGON')

		bpy.ops.object.mode_set(mode = 'EDIT')
		
		if context_override:
			if settings.bversion >= 3.2:
				with bpy.context.temp_override(**context_override):
					bpy.ops.transform.translate(value=(0, scale*0.5, 0), constraint_axis=(False, True, False))
			else:
				bpy.ops.transform.translate(context_override, value=(0, scale*0.5, 0), constraint_axis=(False, True, False))
		else:
			bpy.ops.transform.translate(value=(0, scale*0.5, 0), constraint_axis=(False, True, False))

		bpy.ops.object.mode_set(mode = 'OBJECT')
		
		modifier = bpy.context.object.modifiers.new(name="Mirror", type='MIRROR')
		modifier.use_axis[0] = False
		modifier.use_axis[1] = True
		modifier.show_expanded = False
		AddArray("Array0", 0.5,-0.5,2)
		AddArray("Array1", 1-1/3.0,0,size)
		AddArray("Array1", 0,-(1-1/3.0),int(size*0.66))


	elif mode == 'rectangle':
		bpy.ops.mesh.primitive_plane_add(size=scale)
		AddArray("Array0", 1,0,size)
		AddArray("Array1", 0,-1,size)


	elif mode == 'diamond':
		bpy.ops.mesh.primitive_plane_add(size=scale)

		bpy.ops.object.mode_set(mode = 'EDIT')

		if context_override:
			if settings.bversion >= 3.2:
				with bpy.context.temp_override(**context_override):
					bpy.ops.transform.rotate(value=math.pi*0.25,  orient_axis='Z')
			else:
				bpy.ops.transform.rotate(context_override, value=math.pi*0.25,  orient_axis='Z')
		else:
			bpy.ops.transform.rotate(value=math.pi*0.25,  orient_axis='Z')

		bpy.ops.object.mode_set(mode = 'OBJECT')

		AddArray("Array0", 0.5,-0.5,2)
		AddArray("Array1", 1-1/3,0,size)
		AddArray("Array2", 0,-(1-1/3),size)

	elif mode == 'brick':
		bpy.ops.mesh.primitive_plane_add(size=scale)

		bpy.ops.object.mode_set(mode = 'EDIT')

		if context_override:
			if settings.bversion >= 3.2:
				with bpy.context.temp_override(**context_override):
					bpy.ops.transform.resize(value=(1, 0.5, 1), constraint_axis=(True, True, False), orient_type='GLOBAL')
			else:
				bpy.ops.transform.resize(context_override, value=(1, 0.5, 1), constraint_axis=(True, True, False), orient_type='GLOBAL')
		else:
			bpy.ops.transform.resize(value=(1, 0.5, 1), constraint_axis=(True, True, False), orient_type='GLOBAL')

		bpy.ops.object.mode_set(mode = 'OBJECT')
		
		
		AddArray("Array0", 0.5,-1,2)
		AddArray("Array1", 1-(1/3),0,size)
		AddArray("Array2", 0,-1,size)


	elif mode == 'stripe':
		bpy.ops.mesh.primitive_plane_add(size=1)

		bpy.ops.object.mode_set(mode = 'EDIT')
		if context_override:
			if settings.bversion >= 3.2:
				with bpy.context.temp_override(**context_override):
					bpy.ops.transform.resize(value=(0.5, size/2, 1), constraint_axis=(True, True, False), orient_type='GLOBAL')
					bpy.ops.transform.resize(value=(scale, scale, 1), constraint_axis=(True, True, False), orient_type='GLOBAL')
					bpy.ops.transform.translate(value=(0, (-size/2)*scale, 0), constraint_axis=(False, True, False))
			else:
				bpy.ops.transform.resize(context_override, value=(0.5, size/2, 1), constraint_axis=(True, True, False), orient_type='GLOBAL')
				bpy.ops.transform.resize(context_override, value=(scale, scale, 1), constraint_axis=(True, True, False), orient_type='GLOBAL')
				bpy.ops.transform.translate(context_override, value=(0, (-size/2)*scale, 0), constraint_axis=(False, True, False))
		else:
			bpy.ops.transform.resize(value=(0.5, size/2, 1), constraint_axis=(True, True, False), orient_type='GLOBAL')
			bpy.ops.transform.resize(value=(scale, scale, 1), constraint_axis=(True, True, False), orient_type='GLOBAL')
			bpy.ops.transform.translate(value=(0, (-size/2)*scale, 0), constraint_axis=(False, True, False))
		
		bpy.ops.object.mode_set(mode = 'OBJECT')

		AddArray("Array0", 1,0, size)

	if bpy.context.object:
		bpy.context.object.name = "pattern_{}".format(mode)


bpy.utils.register_class(op)
