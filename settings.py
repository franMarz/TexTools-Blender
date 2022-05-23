import bpy
import re

bversion_string = bpy.app.version_string
bversion_reg = re.match("^(\d\.\d?\d)", bversion_string)
bversion = float(bversion_reg.group(0))

selection_uv_mode = ''
selection_uv_loops = set()
selection_uv_pivot = ''
selection_uv_pivot_pos = (0,0)

use_uv_sync = False
selection_mode = [False, False, True]
selection_vert_indexies = set()
selection_edge_indexies = set()
selection_face_indexies = set()
seam_edges = set()

bake_error = ''
bake_render_engine = ''
bake_cycles_device = ''
bake_cycles_samples = 1
bake_target_mode = ''
use_progressive_refine = False
use_denoising = False
bake_objects_hide_render = []
sets = []
