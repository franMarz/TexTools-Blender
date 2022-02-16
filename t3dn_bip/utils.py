import bpy
import io
from zlib import decompress
from array import array
from .formats import BIP_FORMATS, MAGIC_LENGTH



def can_load(filepath: str) -> bool:
    '''Return whether an image can be loaded.'''
    # Read magic for format detection.
    with open(filepath, 'rb') as file:
        magic = file.read(MAGIC_LENGTH)

    # We support BIP (currently only BIP2).
    for spec in BIP_FORMATS.values():
        if magic.startswith(spec.magic):
            return True

    return False


def load_file(filepath: str) -> dict:
    '''Load image preview data from file.

    Args:
        filepath: The input file path.

    Returns:
        A dictionary with icon_size, icon_pixels, image_size, image_pixels.

    Raises:
        AssertionError: If pixel data type is not 32 bit.
        AssertionError: If pixel count does not match size.
    '''
    with open(filepath, 'rb') as bip:
        magic = bip.read(MAGIC_LENGTH)

        if magic.startswith(BIP_FORMATS['BIP2'].magic):
            bip.seek(len(BIP_FORMATS['BIP2'].magic), io.SEEK_SET)

            count = int.from_bytes(bip.read(1), 'big')
            assert count > 0, 'the file contains no images'

            icon_size = [int.from_bytes(bip.read(2), 'big') for _ in range(2)]
            icon_length = int.from_bytes(bip.read(4), 'big')
            bip.seek(8 * (count - 2), io.SEEK_CUR)
            image_size = [int.from_bytes(bip.read(2), 'big') for _ in range(2)]
            image_length = int.from_bytes(bip.read(4), 'big')

            icon_content = decompress(bip.read(icon_length))
            bip.seek(-image_length, io.SEEK_END)
            image_content = decompress(bip.read(image_length))

            icon_pixels = array('i', icon_content)
            assert icon_pixels.itemsize == 4, 'unexpected bytes per pixel'
            length = icon_size[0] * icon_size[1]
            assert len(icon_pixels) == length, 'unexpected amount of pixels'

            image_pixels = array('i', image_content)
            assert image_pixels.itemsize == 4, 'unexpected bytes per pixel'
            length = image_size[0] * image_size[1]
            assert len(image_pixels) == length, 'unexpected amount of pixels'

            return {
                'icon_size': icon_size,
                'icon_pixels': icon_pixels,
                'image_size': image_size,
                'image_pixels': image_pixels,
            }

    raise ValueError('input is not a supported file format')


def tag_redraw():
    '''Redraw every region in Blender.'''
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            for region in area.regions:
                region.tag_redraw()
