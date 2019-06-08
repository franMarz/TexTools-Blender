import bpy
import bmesh
import operator

selection_uv_mode = '';
selection_uv_loops = []
selection_uv_pivot = '';
selection_uv_pivot_pos = (0,0)

selection_mode = [False, False, True];
selection_vert_indexies = []
selection_face_indexies = []

bake_render_engine = ''
bake_objects_hide_render = [] 
bake_cycles_samples = 1
sets = []