from base64 import b64decode


class _BIPFormat:
    '''BIP format info.'''

    def __init__(self, magic: bytes):
        self.magic = magic


BIP_FORMATS = {
    'BIP2': _BIPFormat(magic=b'BIP2'),
}

MAGIC_LENGTH = max([len(spec.magic) for spec in BIP_FORMATS.values()])
