from fieldslists import BoxHeaderFieldsList, FullBoxHeaderFieldsList
from pybzparse import Parser
from ctypes import c_uint32


MAX_UINT_32 = c_uint32(-1).value


class BoxHeader(BoxHeaderFieldsList):
    def __init__(self, length=0):
        super().__init__(length)

        self._start_pos = None
        self._type_cache = None
        self._box_size_cache = None
        self._header_size_cache = None
        self._content_size_cache = None

    @property
    def start_pos(self):
        return self._start_pos

    @property
    def type(self):
        return self._type_cache

    @property
    def box_size(self):
        return self._box_size_cache

    @property
    def header_size(self):
        return self._header_size_cache

    @property
    def content_size(self):
        return self._content_size_cache

    def parse(self, bstr):
        self._start_pos = bstr.bytepos
        self.parse_fields(bstr)
        self._refresh_cache(bstr.bytepos - self._start_pos)

    def _refresh_cache(self, header_size):
        self._type_cache = (self._box_type.value + self._user_type.value
                            if self._user_type.value is not None
                            else self._box_type.value)
        self._box_size_cache = (self._box_ext_size.value
                                if self._box_ext_size.value is not None
                                else self._box_size.value)
        self._header_size_cache = header_size
        self._content_size_cache = self._box_size_cache - header_size


class FullBoxHeader(BoxHeader, FullBoxHeaderFieldsList, BoxHeaderFieldsList):
    def __init__(self, length=0):
        super().__init__(length)

    def parse_fields(self, bstr):
        super().parse_fields(bstr)
        self._parse_extend_fields(bstr)

    def extend_header(self, bstr, header):
        self._set_field(self._box_size, header.box_size)
        self._set_field(self._box_type, header.box_type)
        self._set_field(self._box_ext_size, header.box_ext_size)
        self._set_field(self._user_type, header.user_type)

        self._start_pos = header.start_pos
        self._parse_extend_fields(bstr)
        self._refresh_cache(bstr.bytepos - self._start_pos)

    def _parse_extend_fields(self, bstr):
        FullBoxHeaderFieldsList.parse_fields(self, bstr)


# Register header
Parser.register_box_header(BoxHeader)
