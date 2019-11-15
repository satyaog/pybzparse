from abc import ABCMeta, abstractmethod
from ctypes import c_uint32

from pybzparse import Parser
from pybzparse.fields_lists import BoxHeaderFieldsList, FullBoxHeaderFieldsList


MAX_UINT_32 = c_uint32(-1).value


class AbstractBoxHeader(metaclass=ABCMeta):
    def __init__(self):
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

    @type.setter
    @abstractmethod
    def type(self, value):
        raise NotImplemented()

    @property
    def box_size(self):
        return self._box_size_cache

    @box_size.setter
    @abstractmethod
    def box_size(self, value):
        raise NotImplemented()

    @property
    def header_size(self):
        return self._header_size_cache

    @property
    def content_size(self):
        return self._content_size_cache

    @abstractmethod
    def parse(self, bstr):
        raise NotImplemented()

    @abstractmethod
    def update_box_size(self, content_size):
        raise NotImplemented()

    @abstractmethod
    def refresh_cache(self):
        raise NotImplemented()


class BoxHeader(AbstractBoxHeader, BoxHeaderFieldsList):
    def __init__(self):
        super().__init__()
        BoxHeaderFieldsList.__init__(self)

    @property
    def type(self):
        return self._type_cache

    @type.setter
    def type(self, value):
        if value[:4] == b'uuid':
            self._set_field(self._box_type, value[:4])
            self._set_field(self._user_type, value[4:])
        else:
            self._set_field(self._box_type, value)
            self._drop_field(self._user_type)
        self._refresh_cache(len(bytes(self)))

    @property
    def box_size(self):
        return self._box_size_cache

    @box_size.setter
    def box_size(self, value):
        if value > MAX_UINT_32:
            self._set_field(self._box_size, 1)
            self._set_field(self._box_ext_size, value)
        else:
            self._set_field(self._box_size, value)
            self._drop_field(self._box_ext_size)
        self._refresh_cache(len(bytes(self)))

    @property
    def box_ext_size(self):
        return self._box_size_cache

    @box_ext_size.setter
    def box_ext_size(self, value):
        self._set_field(self._box_size, 1)
        self._set_field(self._box_ext_size, value)
        self._refresh_cache(len(bytes(self)))

    def parse(self, bstr):
        self._start_pos = bstr.bytepos
        self.parse_fields(bstr)
        self._refresh_cache(bstr.bytepos - self._start_pos)

    def update_box_size(self, content_size):
        header_size = len(bytes(self))
        # Add the size of the box_size field
        if self._box_size.value is None:
            header_size += 4
        # Add the size of the box_ext_size field
        if self._box_ext_size.value is None and \
           header_size + content_size > MAX_UINT_32:
            header_size += 8

        box_size = header_size + content_size

        if self._box_ext_size.value is not None or box_size > MAX_UINT_32:
            self._set_field(self._box_ext_size, box_size)
        else:
            self._set_field(self._box_size, box_size)

        self._refresh_cache(header_size)

    def refresh_cache(self):
        self._refresh_cache(len(bytes(self)))

    def _refresh_cache(self, header_size):
        self._type_cache = (self._box_type.value + self._user_type.value
                            if self._user_type.value is not None
                            else self._box_type.value)
        self._box_size_cache = (self._box_ext_size.value
                                if self._box_ext_size.value is not None
                                else self._box_size.value)
        self._header_size_cache = header_size
        self._content_size_cache = (self._box_size_cache - header_size
                                    if self._box_size_cache is not None
                                    else None)


class FullBoxHeader(BoxHeader, FullBoxHeaderFieldsList):
    def __init__(self):
        super().__init__()
        FullBoxHeaderFieldsList.__init__(self)

    def extend_header(self, bstr, header):
        bstr.bytepos = header.start_pos
        self.parse(bstr)


# Register header
Parser.register_box_header(BoxHeader)
