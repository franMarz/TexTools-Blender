from io import BytesIO
from base64 import b64decode


class _BIPFormat:
    '''BIP format info.'''

    def __init__(self, exts: list, magic: bytes):
        self.exts = exts
        self.magic = magic


class _PILFormat:
    '''PIL format info.'''

    def __init__(self, exts: list, magic: bytes, tests: list):
        self.exts = exts
        self.magic = magic
        self.tests = tests
        self.supported = False


_png_tests = [
    b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAQMAAAAl21bKAAAAA1BMVEUAAACnej3aAAAAAXRSTlMAQObYZgAAAApJREFUCNdjYAAAAAIAAeIhvDMAAAAASUVORK5CYII=',
]

_jpg_tests = [
    b'/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiigD//2Q==',
]

BIP_FORMATS = {
    'BIP2': _BIPFormat(
        exts=['.bip', '.bip2'],
        magic=b'BIP2',
    ),
}

PIL_FORMATS = {
    'PNG':
        _PILFormat(
            exts=['.png'],
            magic=b'\x89\x50\x4e\x47',
            tests=_png_tests,
        ),
    'JPG':
        _PILFormat(
            exts=['.jpg', '.jpeg', '.jpe', '.jif', '.jfif'],
            magic=b'\xff\xd8',
            tests=_jpg_tests,
        ),
}

MAGIC_LENGTH = max(
    max([len(spec.magic) for spec in BIP_FORMATS.values()]),
    max([len(spec.magic) for spec in PIL_FORMATS.values()]),
)


def _run_test(test: bytes) -> bool:
    '''Try a test image with Pillow.'''
    from PIL import Image

    try:
        with Image.open(BytesIO(b64decode(test))) as image:
            image.convert('RGBA')
    except:
        return False
    else:
        return True


def test_formats():
    '''Test which formats are supported by Pillow.'''
    for spec in PIL_FORMATS.values():
        spec.supported = all(map(_run_test, spec.tests))


def unsupported_formats() -> bool:
    '''Get the names of unsupported formats.'''
    return [name for name, spec in PIL_FORMATS.items() if not spec.supported]
