import bpy
import bmesh


class op(bpy.types.Operator):
    bl_idname = "uv.textools_island_straighten_edge_loops"
    bl_label = "Straight edges chain"
    bl_description = "Straighten selected UV edges (Memory Safe)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_object and
                context.active_object.type == 'MESH' and
                context.active_object.mode == 'EDIT')

    def execute(self, context):
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.verify()

        sel_layer = bm.loops.layers.bool.get('select')
        if not sel_layer:
            sel_layer = bm.loops.layers.bool.new('select')

        target_loops = []

        for face in bm.faces:
            for loop in face.loops:
                if loop[sel_layer]:
                    target_loops.append(loop)

        if not target_loops:
            if context.tool_settings.mesh_select_mode[2]:
                for face in bm.faces:
                    if face.select:
                        for loop in face.loops:
                            target_loops.append(loop)
            elif context.tool_settings.mesh_select_mode[1]:
                for edge in bm.edges:
                    if edge.select:
                        for loop in edge.link_loops:
                            target_loops.append(loop)
            elif context.tool_settings.mesh_select_mode[0]:
                for vert in bm.verts:
                    if vert.select:
                        for loop in vert.link_loops:
                            target_loops.append(loop)

        target_loops = list(set(target_loops))

        if not target_loops:
            self.report({'WARNING'}, "No selection found.")
            return {'CANCELLED'}

        try:
            coords = [l[uv_layer].uv for l in target_loops]
        except ReferenceError:
            self.report({'ERROR'}, "Memory Reference Error. Undo and try again.")
            return {'CANCELLED'}

        if len(coords) < 2:
            self.report({'WARNING'}, "Select at least 2 vertices.")
            return {'CANCELLED'}

        min_x = min(c.x for c in coords)
        max_x = max(c.x for c in coords)
        min_y = min(c.y for c in coords)
        max_y = max(c.y for c in coords)

        is_horizontal = (max_x - min_x) > (max_y - min_y)

        if is_horizontal:
            avg_y = sum(c.y for c in coords) / len(coords)
            target_val = avg_y
        else:
            avg_x = sum(c.x for c in coords) / len(coords)
            target_val = avg_x

        for loop in target_loops:
            if is_horizontal:
                loop[uv_layer].uv.y = target_val
            else:
                loop[uv_layer].uv.x = target_val

            loop[uv_layer].pin_uv = True
            loop[sel_layer] = True

        bmesh.update_edit_mesh(obj.data)
        self.report({'INFO'}, "Edges Straightened & Pinned.")

        return {'FINISHED'}
