import bpy
import bmesh

from mathutils import Vector
from . import utilities_uv



class op(bpy.types.Operator):
	bl_idname = "uv.textools_align"
	bl_label = "Align"
	bl_description = "Align vertices, edges or shells"
	bl_options = {'REGISTER', 'UNDO'}
	
	direction : bpy.props.StringProperty(name="Direction", default="top", options={'HIDDEN'})

	@classmethod
	def poll(cls, context):
		if bpy.context.area.ui_type != 'UV':
			return False
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object.mode != 'EDIT':
			return False
		if not bpy.context.object.data.uv_layers:
			return False
		return True


	def execute(self, context):
		align_mode = bpy.context.scene.texToolsSettings.align_mode

		if align_mode == 'SELECTION':
			all_ob_bounds = utilities_uv.multi_object_loop(utilities_uv.getSelectionBBox, need_results=True)
			if not any(all_ob_bounds):
				return {'CANCELLED'}

			boundsAll = utilities_uv.get_BBOX_multi(all_ob_bounds)

			utilities_uv.multi_object_loop(align, context, align_mode, self.direction, boundsAll=boundsAll)
		
		else:
			udim_tile, column, row = utilities_uv.get_UDIM_tile_coords(bpy.context.active_object)
			utilities_uv.multi_object_loop(align, context, align_mode, self.direction, column=column, row=row)
		
		return {'FINISHED'}



def align(context, align_mode, direction, boundsAll={}, column=0, row=0):
	prepivot = bpy.context.space_data.pivot_point
	bpy.context.space_data.pivot_point = 'CURSOR'

	obj = bpy.context.active_object
	bm = bmesh.from_edit_mesh(obj.data)
	uv_layers = bm.loops.layers.uv.verify()
	sync = bpy.context.scene.tool_settings.use_uv_select_sync

	if align_mode == 'SELECTION':
		center_all = boundsAll['center']
	elif align_mode == 'CURSOR':
		cursor = Vector(bpy.context.space_data.cursor_location.copy())
		center_all = boundsAll['min'] = boundsAll['max'] = cursor
	else:	#CANVAS
		if direction == "bottom" or direction == "left" or direction == "bottomleft":
			center_all = boundsAll['min'] = boundsAll['max'] = Vector((column, row))
		elif direction == "top" or direction == "topleft":
			center_all = boundsAll['min'] = boundsAll['max'] = Vector((column, row + 1))
		elif direction == "right" or direction == "topright":
			center_all = boundsAll['min'] = boundsAll['max'] = Vector((column + 1, row + 1))
		elif direction == "bottomright":
			center_all = boundsAll['min'] = boundsAll['max'] = Vector((column + 1, row))
		elif direction == "horizontal" or direction == "vertical" or direction == "center":
			center_all = boundsAll['min'] = boundsAll['max'] = Vector((column + 0.5, row + 0.5))

	if sync:
		if bpy.context.scene.tool_settings.mesh_select_mode[2]:
			selection_mode = 'FACE'
		else:
			selection_mode = 'VERTEX'
	else:
		selection_mode = bpy.context.scene.tool_settings.uv_select_mode

	if selection_mode == 'FACE' or selection_mode == 'ISLAND':
		islands = utilities_uv.get_selected_islands(bm, uv_layers)

		for island in islands:
			bounds = utilities_uv.get_BBOX(island, bm, uv_layers)
			center = bounds['center']

			if direction == "bottom":
				delta = boundsAll['min'] - bounds['min'] 				
				utilities_uv.move_island(island, 0, delta.y)
			
			elif direction == "top":
				delta = boundsAll['max'] - bounds['max']
				utilities_uv.move_island(island, 0, delta.y)
			
			elif direction == "left":
				delta = boundsAll['min'] - bounds['min'] 
				utilities_uv.move_island(island, delta.x, 0)
			
			elif direction == "right":
				delta = boundsAll['max'] - bounds['max']
				utilities_uv.move_island(island, delta.x, 0)
			
			elif direction == "center":
				delta = Vector((center_all - center))
				utilities_uv.move_island(island, delta.x, delta.y)
			
			elif direction == "horizontal":
				delta = Vector((center_all - center))
				utilities_uv.move_island(island, 0, delta.y)
			
			elif direction == "vertical":
				delta = Vector((center_all - center))
				utilities_uv.move_island(island, delta.x, 0)	

			elif direction == "bottomleft":
				delta = boundsAll['min'] - bounds['min']
				utilities_uv.move_island(island, delta.x, delta.y)

			elif direction == "topright":
				delta = boundsAll['max'] - bounds['max']
				utilities_uv.move_island(island, delta.x, delta.y)

			elif direction == "topleft":
				delta_x = boundsAll['min'] - bounds['min']
				delta_y = boundsAll['max'] - bounds['max']
				utilities_uv.move_island(island, delta_x.x, delta_y.y)

			elif direction == "bottomright":
				delta_x = boundsAll['max'] - bounds['max']
				delta_y = boundsAll['min'] - bounds['min']
				utilities_uv.move_island(island, delta_x.x, delta_y.y)

	else:	# Vertices or Edges UV selection mode
		for f in bm.faces:
			if f.select:
				for l in f.loops:
					luv = l[uv_layers]
					if sync or luv.select:
						# print("Idx: "+str(luv.uv))
						if direction == "top":
							luv.uv[1] = boundsAll['max'].y
						elif direction == "bottom":
							luv.uv[1] = boundsAll['min'].y
						elif direction == "left":
							luv.uv[0] = boundsAll['min'].x
						elif direction == "right":
							luv.uv[0] = boundsAll['max'].x
						elif direction == "center":
							luv.uv[0] = center_all.x
							luv.uv[1] = center_all.y
						elif direction == "horizontal":
							luv.uv[1] = center_all.y
						elif direction == "vertical":
							luv.uv[0] = center_all.x
						elif direction == "bottomleft":
							luv.uv[0] = boundsAll['min'].x
							luv.uv[1] = boundsAll['min'].y
						elif direction == "topright":
							luv.uv[0] = boundsAll['max'].x
							luv.uv[1] = boundsAll['max'].y
						elif direction == "topleft":
							luv.uv[0] = boundsAll['min'].x
							luv.uv[1] = boundsAll['max'].y
						elif direction == "bottomright":
							luv.uv[0] = boundsAll['max'].x
							luv.uv[1] = boundsAll['min'].y

		bmesh.update_edit_mesh(obj.data)

	# Workaround for selection not flushing properly from loops to EDGE Selection Mode, apparently since UV edge selection support was added to the UV space
	if not sync:
		bpy.ops.uv.select_mode(type='VERTEX')
	bpy.context.scene.tool_settings.uv_select_mode = selection_mode
	bpy.context.space_data.pivot_point = prepivot


bpy.utils.register_class(op)
