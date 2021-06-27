import bpy
import re

bversion_string = bpy.app.version_string
bversion_reg = re.match("^(\d\.\d?\d)", bversion_string)
bversion = float(bversion_reg.group(0))

selection_uv_mode = ''
selection_uv_loops = []
selection_uv_pivot = ''
selection_uv_pivot_pos = (0,0)

selection_mode = [False, False, True]
selection_vert_indexies = []
selection_edge_indexies = []
selection_face_indexies = []

bake_error = ''
bake_render_engine = ''
bake_cycles_device = ''
bake_cycles_samples = 1
bake_target_mode = ''
use_progressive_refine = False
bake_objects_hide_render = []
sets = []
