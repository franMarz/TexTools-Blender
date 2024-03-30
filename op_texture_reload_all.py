import bpy



class op(bpy.types.Operator):
	bl_idname = "uv.textools_texture_reload_all"
	bl_label = "Reload Textures and remove unused Textures"
	bl_description = "Reload all textures"

	@classmethod
	def poll(cls, context):
		return True


	def execute(self, context):
		main(context)
		return {'FINISHED'}



def main(context):
	count_clear_mat = 0
	count_clear_img = 0
	count_reload = 0

	for material in bpy.data.materials:
		if not material.users:
			count_clear_mat += 1
			bpy.data.materials.remove(material, do_unlink=True)

	# Clean up unused images
	for image in bpy.data.images:
		if not image.users:
			count_clear_img += 1
			bpy.data.images.remove(image, do_unlink=True)

	#Reload all File images
	for img in bpy.data.images :
		if img.source == 'FILE':
			count_reload += 1
			img.reload()

	# Refresh vieport texture
	for window in bpy.context.window_manager.windows:
		screen = window.screen
		for area in screen.areas:
			area.tag_redraw()

	# Show popup on cleared & reloaded items
	message = ""
	if count_reload > 0:
		message += "{}x reloaded. ".format(count_reload)
	if count_clear_mat > 0:
		message += "{}x mat cleared. ".format(count_clear_mat)
	if count_clear_img > 0:
		message += "{}x img cleared.".format(count_clear_img)

	if len(message) > 0:
		bpy.ops.ui.textools_popup('INVOKE_DEFAULT', message=message)
