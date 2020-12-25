import bpy
import bmesh
import math
import random

from mathutils import Vector
from . import utilities_uv



class op(bpy.types.Operator):
	bl_idname = "uv.textools_randomize"
	bl_label = "Randomize Position"
	bl_description = "Randomize UV Islands/Faces Position"
	bl_options = {'REGISTER', 'UNDO'}
	
	bool_face: bpy.props.BoolProperty(name="Per Face", default=False)
	strengh_U: bpy.props.FloatProperty(name="U Strengh", default=0.3, min=0, max=1, soft_min=0, soft_max=1)
	strengh_V: bpy.props.FloatProperty(name="V Strengh", default=0.3, min=0, max=1, soft_min=0, soft_max=1)
	rotation: bpy.props.FloatProperty(name="Rotation Strengh", default=0, min=0, max=1, soft_min=0, soft_max=1)
	bool_precenter: bpy.props.BoolProperty(name="Pre Center Faces/Islands", default=False, description="Collect all faces/islands around the center of the UV space")
	bool_bounds: bpy.props.BoolProperty(name="Within Image Bounds", default=False, description="U and V Strength and pre-center properties are ignored, to be controlled only via seed and Rotation Strength")
	rand_seed: bpy.props.IntProperty(name="Seed", default=0)


	@classmethod
	def poll(cls, context):
		if not bpy.context.active_object:
			return False
		if bpy.context.active_object.type != 'MESH':
			return False
		if bpy.context.active_object.mode != 'EDIT':
			return False
		if bpy.context.area.type != 'IMAGE_EDITOR':
			return False
		if not bpy.context.object.data.uv_layers:
			return False
		if bpy.context.scene.tool_settings.use_uv_select_sync:
			return False
		return True


	def execute(self, context):
		utilities_uv.multi_object_loop(main, self, context, ob_num=0)
		return {'FINISHED'}

	def invoke(self, context, event):
		wm = context.window_manager
		return wm.invoke_props_dialog(self)



def main(self, context, ob_num=0):
	random.seed(self.rand_seed + ob_num)

	#Store selection
	utilities_uv.selection_store()

	ob = bpy.context.edit_object
	me = ob.data
	bm = bmesh.from_edit_mesh(me)
	uv_layers = bm.loops.layers.uv.verify()

	pregroup = [f for f in bm.faces if f.select and f.loops[0][uv_layers].select]
	if len(pregroup) == 0 :
		return {'FINISHED'}
	
	group = []
	strengh_U = self.strengh_U
	strengh_V = self.strengh_V

	if self.bool_precenter or self.bool_bounds:
		bpy.context.space_data.cursor_location = (0.5, 0.5)

	bpy.ops.mesh.select_mode(type="FACE")

	if not self.bool_face:
		group = utilities_uv.getSelectionIslands()
	else:
		group = pregroup

	bpy.ops.mesh.select_all(action='DESELECT')
	
	for f in group:
		if not self.bool_face:
			for i in f:
				i.select = True
		else:
			f.select = True
		
		if self.bool_precenter or self.bool_bounds:
			#fast but sloppy recenter
			bpy.context.space_data.pivot_point = 'CURSOR'
			bpy.ops.transform.resize(value=(0.001, 0.001, 1), use_proportional_edit=False)
			bpy.context.space_data.pivot_point = 'CENTER'
			bpy.ops.transform.resize(value=(1000, 1000, 1), use_proportional_edit=False)
		
		bpy.context.space_data.pivot_point = 'INDIVIDUAL_ORIGINS'

		if self.bool_bounds:
			boundsMin = Vector((99999999.0,99999999.0))
			boundsMax = Vector((-99999999.0,-99999999.0))

			if not self.bool_face:
				for i in f:
					for loop in i.loops:
						uv = loop[uv_layers].uv
						boundsMin.x = min(boundsMin.x, uv.x)
						boundsMin.y = min(boundsMin.y, uv.y)
						boundsMax.x = max(boundsMax.x, uv.x)
						boundsMax.y = max(boundsMax.y, uv.y)
			else:
				for loop in f.loops:
					uv = loop[uv_layers].uv
					boundsMin.x = min(boundsMin.x, uv.x)
					boundsMin.y = min(boundsMin.y, uv.y)
					boundsMax.x = max(boundsMax.x, uv.x)
					boundsMax.y = max(boundsMax.y, uv.y)
			strengh_U = min(boundsMin.x, 1-boundsMax.x)
			strengh_V = min(boundsMin.y, 1-boundsMax.y)

		bpy.ops.transform.translate(value=(strengh_U*(random.random()-0.5)*2, 0, 0), use_proportional_edit=False)
		bpy.ops.transform.translate(value=(0, strengh_V*(random.random()-0.5)*2, 0), use_proportional_edit=False)
		bpy.ops.transform.rotate(value=self.rotation*random.random()*2*math.pi, orient_axis='Z', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, False), mirror=False, use_proportional_edit=False)
		bpy.ops.mesh.select_all(action='DESELECT')
	
	#Restore selection
	utilities_uv.selection_restore()


bpy.utils.register_class(op)
