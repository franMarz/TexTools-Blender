import bpy
import bpy.utils.previews
from bpy.types import ImagePreview
from multiprocessing.dummy import Pool
from multiprocessing import cpu_count
from threading import Event
from queue import Queue
from traceback import print_exc
from time import time
from typing import ItemsView, Iterator, KeysView, ValuesView
from .utils import can_load, load_file, tag_redraw


class ImagePreviewCollection:
    '''Dictionary-like class of previews.'''

    def __init__(self, max_size: tuple = (128, 128), lazy_load: bool = True):
        '''Create collection and start internal timer.'''

        self._collection = bpy.utils.previews.new()
        self._max_size = max_size
        self._lazy_load = lazy_load

        if self._lazy_load:
            self._pool = Pool(processes=cpu_count())
            self._event = None
            self._queue = Queue()

            if not bpy.app.timers.is_registered(self._timer):
                bpy.app.timers.register(self._timer, persistent=True)

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

        self._pool.apply_async(
            func=self._load_async,
            args=(name, filepath, self._get_event()),
            error_callback=print,
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
        data = load_file(filepath)

        preview = self.new(name)
        preview.icon_size = data['icon_size']
        preview.icon_pixels = data['icon_pixels']
        preview.image_size = data['image_size']
        preview.image_pixels = data['image_pixels']

        return preview

    def _load_async(self, name: str, filepath: str, event: Event):
        '''Load image contents from file and queue preview load.'''
        if not event.is_set():
            data = load_file(filepath)

        if not event.is_set():
            self._queue.put((name, data, event))

    def _timer(self):
        '''Load queued image contents into previews.'''
        now = time()
        redraw = False
        delay = 0.1

        while time() - now < 0.1:
            try:
                args = self._queue.get(block=False)
            except:
                break

            try:
                self._load_queued(*args)
            except:
                print_exc()
            else:
                redraw = True

        else:
            delay = 0.0

        if redraw:
            tag_redraw()

        return delay

    def _load_queued(self, name: str, data: dict, event: Event):
        '''Load queued image contents into preview.'''
        if not event.is_set():
            if name in self:
                preview = self[name]
                preview.icon_size = data['icon_size']
                preview.icon_pixels = data['icon_pixels']
                preview.image_size = data['image_size']
                preview.image_pixels = data['image_pixels']

    def clear(self):
        '''Clear all previews.'''
        if self._lazy_load:
            self._set_event()

            with self._queue.mutex:
                self._queue.queue.clear()

        self._collection.clear()

    def close(self):
        '''Close the collection and clear all previews.'''
        if self._lazy_load:
            self._set_event()

            if bpy.app.timers.is_registered(self._timer):
                bpy.app.timers.unregister(self._timer)

        self._collection.close()

    def _get_event(self) -> Event:
        '''Get the clear event, make one if necesssary.'''
        if self._event is None:
            self._event = Event()

        return self._event

    def _set_event(self):
        '''Set the clear event, then remove the reference.'''
        if self._event is not None:
            self._event.set()
            self._event = None


def new(
    max_size: tuple = (128, 128),
    lazy_load: bool = True,
) -> ImagePreviewCollection:
    '''Return a new preview collection.'''
    return ImagePreviewCollection(max_size, lazy_load)


def remove(collection: ImagePreviewCollection):
    '''Remove the specified preview collection.'''
    collection.close()
