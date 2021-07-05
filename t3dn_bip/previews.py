import bpy
import bpy.utils.previews
from bpy.types import ImagePreview
from threading import Event
from typing import ItemsView, Iterator, KeysView, ValuesView
from .utils import support_pillow, can_load, load_file
from .formats import unsupported_formats
from .threads import load_async
from . import settings


class ImagePreviewCollection:
    '''Dictionary-like class of previews.'''

    def __init__(self, max_size: tuple = (128, 128), lazy_load: bool = True):
        '''Create collection and start internal timer.'''
        if settings.WARNINGS:
            if not support_pillow():
                print('Pillow is not installed, therefore:')
                print('- BIP images load without scaling.')

                if lazy_load:
                    print('- Other images load slowly (Blender standard).')
                if lazy_load and max_size != (128, 128):
                    print('- Other images load in 128x128 (Blender standard).')
                elif not lazy_load and max_size != (256, 256):
                    print('- Other images load in 256x256 (Blender standard).')

            else:
                unsupported = unsupported_formats()
                if unsupported:
                    print('Pillow is installed, but:')

                    for name in unsupported:
                        print(
                            f'- {name} images are not supported by Pillow',
                            'and load slowly (Blender standard).',
                        )

        self._collection = bpy.utils.previews.new()
        self._max_size = max_size
        self._lazy_load = lazy_load

        if self._lazy_load:
            self._abort_signal = None

    def __len__(self) -> int:
        '''Return the amount of previews in the collection.'''
        return len(self._collection)

    def __iter__(self) -> Iterator[str]:
        '''Return an iterator for the names in the collection.'''
        return iter(self._collection)

    def __contains__(self, key) -> bool:
        '''Return whether preview name is in collection.'''
        return key in self._collection

    def __getitem__(self, key) -> ImagePreview:
        '''Return preview with the given name.'''
        return self._collection[key]

    def pop(self, key: str) -> ImagePreview:
        '''Remove preview with the given name and return it.'''
        return self._collection.pop(key)

    def get(self, key: str, default=None) -> ImagePreview:
        '''Return preview with the given name, or default.'''
        return self._collection.get(key, default)

    def keys(self) -> KeysView[str]:
        '''Return preview names.'''
        return self._collection.keys()

    def values(self) -> ValuesView[ImagePreview]:
        '''Return previews.'''
        return self._collection.values()

    def items(self) -> ItemsView[str, ImagePreview]:
        '''Return pairs of name and preview.'''
        return self._collection.items()

    def new_safe(self, name: str) -> ImagePreview:
        '''Generate a new empty preview or return existing.'''
        if name in self:
            return self[name]

        return self.new(name)

    def new(self, name: str) -> ImagePreview:
        '''Generate a new empty preview.'''
        return self._collection.new(name)

    def load_safe(
        self,
        name: str,
        filepath: str,
        filetype: str,
    ) -> ImagePreview:
        '''Generate a new preview from the given filepath or return existing.'''
        if name in self:
            return self[name]

        return self.load(name, filepath, filetype)

    def load(self, name: str, filepath: str, filetype: str) -> ImagePreview:
        '''Generate a new preview from the given filepath.'''
        if filetype != 'IMAGE' or not can_load(filepath):
            return self._load_fallback(name, filepath, filetype)

        if not self._lazy_load:
            return self._load_eager(name, filepath)

        preview = self.new(name)

        load_async(
            self._collection,
            name,
            filepath,
            self._max_size,
            self._get_abort_signal(),
        )

        return preview

    def _load_fallback(
        self,
        name: str,
        filepath: str,
        filetype: str,
    ) -> ImagePreview:
        '''Load preview using Blender's standard method.'''
        preview = self._collection.load(name, filepath, filetype)

        if not self._lazy_load:
            preview.icon_size[:]  # Force Blender to load this icon now.
            preview.image_size[:]  # Force Blender to load this image now.

        return preview

    def _load_eager(self, name: str, filepath: str) -> ImagePreview:
        '''Load image contents from file and load preview.'''
        data = load_file(filepath, self._max_size)

        preview = self.new(name)
        preview.icon_size = data['icon_size']
        preview.icon_pixels = data['icon_pixels']
        preview.image_size = data['image_size']
        preview.image_pixels = data['image_pixels']

        return preview

    def clear(self):
        '''Clear all previews.'''
        if self._lazy_load:
            self._set_abort_signal()

        self._collection.clear()

    def close(self):
        '''Close the collection and clear all previews.'''
        if self._lazy_load:
            self._set_abort_signal()

        self._collection.close()

    def _get_abort_signal(self) -> Event:
        '''Get the abort signal, make one if necesssary.'''
        if self._abort_signal is None:
            self._abort_signal = Event()

        return self._abort_signal

    def _set_abort_signal(self):
        '''Set the abort signal, then remove the reference.'''
        if self._abort_signal is not None:
            self._abort_signal.set()
            self._abort_signal = None


def new(
    max_size: tuple = (128, 128),
    lazy_load: bool = True,
) -> ImagePreviewCollection:
    '''Return a new preview collection.'''
    return ImagePreviewCollection(max_size, lazy_load)


def remove(collection: ImagePreviewCollection):
    '''Remove the specified preview collection.'''
    collection.close()
