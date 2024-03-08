import bpy
import bmesh
import mathutils

from . import utilities_uv
from . import utilities_ui



class op(bpy.types.Operator):
    bl_idname = "uv.textools_uv_unwrap"
    bl_label = "Unwrap"
    bl_description = "Unwrap selected UVs"
    bl_options = {'REGISTER', 'UNDO'}

    axis: bpy.props.StringProperty(name="axis", default="xy", options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        if bpy.context.area.ui_type != 'UV':
            return False
        if not bpy.context.active_object:
            return False
        if bpy.context.active_object.mode != 'EDIT':
            return False
        if bpy.context.active_object.type != 'MESH':
            return False
        if not bpy.context.object.data.uv_layers:
            return False
        if bpy.context.scene.tool_settings.use_uv_select_sync:
            return False
        return True


    def execute(self, context):
        utilities_uv.multi_object_loop(main, context, self.axis)
        return {'FINISHED'}



def main(context, axis):
    bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
    uv_layer = bm.loops.layers.uv.verify()

    selected_faces = utilities_uv.selection_store(return_selected_UV_faces=True)

    # analyze if a full uv-island has been selected
    full_islands = utilities_uv.getSelectionIslands(bm, uv_layer, extend_selection_to_islands=True, selected_faces=selected_faces)
    islands = utilities_uv.getSelectionIslands(bm, uv_layer, extend_selection_to_islands=False, selected_faces=selected_faces, need_faces_selected=False)

    selected_uv_islands = []
    for island in islands:
        for full_island in full_islands:
            if island == full_island:
                selected_uv_islands.append(list(island))

    utilities_uv.selection_restore()

    # store pins and edge seams
    edge_seam = []
    for edge in bm.edges:
        edge_seam.append(edge.seam)
        edge.seam = False

    # Pin the inverse of the current selection, and cache the uv coords
    pin_state = []
    uv_coords = []
    for face in bm.faces:
        for loop in face.loops:
            uv = loop[uv_layer]
            pin_state.append(uv.pin_uv)
            uv.pin_uv = not uv.select

            uv_coords.append(uv.uv.copy())

    # If entire islands are selected, pin one vert to keep the island somewhat in place, 
    # otherwise it can get moved away quite randomly by the uv unwrap method; also store some uvs data to reconstruct orientation
    orient_uvs = []
    if selected_uv_islands:
        for island in selected_uv_islands:

            x_min = x_max = y_min = y_max = island[0].loops[0][uv_layer]
            x_min.pin_uv = True

            for face in island:
                for loop in face.loops:
                    uv = loop[uv_layer]
                    if uv.uv.x > x_max.uv.x:
                        x_max = uv
                    if uv.uv.x < x_min.uv.x:
                        x_min = uv
                    if uv.uv.y > y_max.uv.y:
                        y_max = uv
                    if uv.uv.y < y_min.uv.y:
                        y_min = uv
            
            orient_uvs.append((x_min, x_max, y_min, y_max, x_min.uv.copy(), x_max.uv.copy(), y_min.uv.copy(), y_max.uv.copy()))

    # apply unwrap
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.seams_from_islands()

    padding = utilities_ui.get_padding()
    bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=padding)

    # try to reconstruct the original orientation of the uvisland
    up = mathutils.Vector((0, 1.0))
    for index, island in enumerate(selected_uv_islands):
        island_bbox = utilities_uv.get_BBOX(island, bm, uv_layer)

        x_min, x_max, y_min, y_max, x_min_coord, x_max_coord, y_min_coord, y_max_coord = orient_uvs[index]
    
        intial_x_axis = x_min_coord - x_max_coord       
        intial_x_angle = up.angle_signed(intial_x_axis)

        axis_x_current = x_min.uv - x_max.uv
        current_x_angle = up.angle_signed(axis_x_current)

        intial_y_axis = y_min_coord - y_max_coord       
        intial_y_angle = up.angle_signed(intial_y_axis)

        axis_y_current = y_min.uv - y_max.uv
        current_y_angle = up.angle_signed(axis_y_current)

        angle_x = intial_x_angle - current_x_angle
        angle_y = intial_y_angle - current_y_angle
        angle = min(angle_x, angle_y)

        center = island_bbox['center']
        utilities_uv.rotate_island(island, uv_layer, angle, center)

        #keep it the same size
        scale_x = intial_x_axis.length / axis_x_current.length 
        scale_y = intial_y_axis.length / axis_y_current.length 
        scale  = min([scale_x, scale_y], key=lambda x:abs(x-1.0)) #pick scale closer to 1.0
        utilities_uv.scale_island(island, uv_layer, scale, scale, center)

        #move back into place
        delta = x_min_coord - x_min.uv
        utilities_uv.move_island(island, delta.x, delta.y)

    # restore selections, pins & edge seams
    index = 0
    for face in bm.faces:
        for loop in face.loops:
            uv = loop[uv_layer]
            uv.pin_uv = pin_state[index]

            #apply axis constraint
            if axis == "x":
                uv.uv.y = uv_coords[index].y
            elif axis == "y":
                uv.uv.x = uv_coords[index].x

            index += 1

    for index, edge in enumerate(bm.edges):
        edge.seam = edge_seam[index]

    utilities_uv.selection_restore()


bpy.utils.register_class(op)
