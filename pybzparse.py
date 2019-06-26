""" Benzina MP4 Parser based on https://github.com/use-sparingly/pymp4parse """

from abc import ABCMeta, abstractmethod
from ctypes import c_uint32
import logging

import bitstring as bs

log = logging.getLogger(__name__)
log.setLevel(logging.WARN)

MAX_UINT_32 = c_uint32(-1).value


class AbstractFieldsList():
    class Field:
        def __init__(self, index=None, value=None, value_type=None, size=None,
                     is_list=False, is_string=False):
            self.index = index
            self.value = value
            self._value_type = value_type
            self._value_size = size
            self._is_list = is_list
            self._is_string = is_string

        def __repr__(self, *args, **kwargs):
            return "{type}:{value}".format(type=self.type, value=self.value)

        @property
        def type(self):
            return self._value_type if self._value_size is None else \
                   "{}:{}".format(self._value_type, self._value_size)

        @type.setter
        def type(self, value):
            split_iter = iter(value.split(':'))
            self._value_type = next(split_iter, None)
            self._value_size = next(split_iter, None)

        @property
        def is_list(self):
            return self._is_list

        @property
        def is_string(self):
            return self._is_string

    def __init__(self, length):
        self._fields = [None] * length
        self._last_index = 0

    def __bytes__(self):
        values = []
        types = []
        for field in self._fields[:self._last_index]:
            if field.is_list:
                values.extend(field.value)
                types.extend([field.type] * len(field.value))
            else:
                values.append(field.value)
                types.append(field.type)
        return bs.pack(','.join(types), *values).bytes

    def __len__(self):
        """ Define the length of the split """
        return self._last_index

    def _set_field(self, field, value, value_type=None):
        if field.index is None and value is not None:
            field.index = self._last_index
            self._fields[field.index] = field
            self._last_index += 1
        field.value = value
        if value_type is not None:
            field.type = value_type

    def _read_field(self, bstr, field, value_type=None, until_pos=None):
        if value_type is None:
            value_type = field.type
        if field.is_string:
            value = bstr.readto(b'\0', bytealigned=True).bytes
        elif field.is_list:
            value = []
            while bstr.bitpos < until_pos:
                value.append(bstr.read(value_type))
        else:
            value = bstr.read(value_type)
        self._set_field(field, value, value_type)

    @property
    def fields(self):
        return self._fields[:self._last_index]


class AbstractBox(metaclass=ABCMeta):
    def __init__(self, header):
        self._header = header

    def __bytes__(self):
        return bytes(self._header)

    @property
    def header(self):
        return self._header

    @header.setter
    def header(self, value):
        self._header = value

    @abstractmethod
    def load(self, bstr):
        raise NotImplemented()

    @abstractmethod
    def parse(self, bstr):
        raise NotImplemented()

    @classmethod
    def parse_box(cls, bstr, header):
        box = cls(header)
        box.parse(bstr)
        return box


class AbstractFullBox(AbstractBox, metaclass=ABCMeta):
    @classmethod
    def parse_box(cls, bstr, header):
        full_box_header = FullBoxHeader()
        full_box_header.extend_header(bstr, header)
        del header
        return super(AbstractFullBox, cls).parse_box(bstr, full_box_header)


class MixinDictRepr(object):
    def __repr__(self, *args, **kwargs):
        return "{class_name} : {content!r} ".format(class_name=self.__class__.__name__,
                                                    content=self.__dict__)


class MixinMinimalRepr(object):
    """ A minimal representaion when the payload could be large """

    def __repr__(self, *args, **kwargs):
        return "{class_name} : {content!r} ".format(class_name=self.__class__.__name__,
                                                    content=self.__dict__.keys())


class BoxHeaderFieldsList(AbstractFieldsList):
    def __init__(self, length=4):
        self._box_size = self.Field(value_type="uintbe", size=32)
        self._box_type = self.Field(value_type="bytes", size=4)
        self._box_ext_size = self.Field(value_type="uintbe", size=64)
        self._user_type = self.Field(value_type="bytes", size=16)
        super(BoxHeaderFieldsList, self).__init__(length)

    @property
    def box_size(self):
        return self._box_size.value

    @box_size.setter
    def box_size(self, value):
        self._set_field(self._box_size, *value)

    @property
    def box_type(self):
        return self._box_type.value

    @box_type.setter
    def box_type(self, value):
        self._set_field(self._box_type, *value)

    @property
    def box_ext_size(self):
        return self._box_ext_size.value

    @box_ext_size.setter
    def box_ext_size(self, value):
        self._set_field(self._box_ext_size, *value)

    @property
    def user_type(self):
        return self._user_type.value

    @user_type.setter
    def user_type(self, value):
        self._set_field(self._user_type, *value)

    def parse_fields(self, bstr):
        self._read_field(bstr, self._box_size)
        self._read_field(bstr, self._box_type)

        # if size == 1, then this is an extended size type.
        # Therefore read the next 64 bits as size
        if self._box_size.value == 1:
            self._read_field(bstr, self._box_ext_size)

        if self._box_type.value == b'uuid':
            self._read_field(bstr, self._user_type)


class FullBoxHeaderFieldsList(AbstractFieldsList):
    def __init__(self, length=2):
        self._version = self.Field(value_type="uintbe", size=8)
        self._flags = self.Field(value_type="bits", size=24)
        super(FullBoxHeaderFieldsList, self).__init__(length)

    @property
    def version(self):
        return self._version.value

    @version.setter
    def version(self, value):
        self._set_field(self._version, *value)

    @property
    def flags(self):
        return self._flags.value.bytes

    @flags.setter
    def flags(self, value):
        self._set_field(self._flags, *value)

    def parse_fields(self, bstr):
        self._read_field(bstr, self._version)
        self._read_field(bstr, self._flags)


class SampleDescriptionBoxHeaderFieldsList(AbstractFieldsList):
    def __init__(self, length=1):
        self._entry_count = self.Field(value_type="uintbe", size=32)
        super(SampleDescriptionBoxHeaderFieldsList, self).__init__(length)

    @property
    def entry_count(self):
        return self._entry_count.value

    @entry_count.setter
    def entry_count(self, value):
        self._set_field(self._entry_count, *value)

    def parse_fields(self, bstr):
        self._read_field(bstr, self._entry_count)


class FileTypeBoxFieldsList(AbstractFieldsList):
    def __init__(self):
        self._major_brand = self.Field(value_type="uintbe", size=32)
        self._minor_version = self.Field(value_type="uintbe", size=32)
        self._compatible_brands = self.Field(value_type="uintbe", size=32, is_list=True)
        super(FileTypeBoxFieldsList, self).__init__(3)

    @property
    def major_brand(self):
        return self._major_brand.value

    @major_brand.setter
    def major_brand(self, value):
        self._set_field(self._major_brand, *value)

    @property
    def minor_version(self):
        return self._minor_version.value

    @minor_version.setter
    def minor_version(self, value):
        self._set_field(self._minor_version, *value)

    @property
    def compatible_brands(self):
        return self._compatible_brands.value

    @compatible_brands.setter
    def compatible_brands(self, value):
        self._set_field(self._compatible_brands, *value)

    def parse_fields(self, bstr, header):
        self._read_field(bstr, self._major_brand)
        self._read_field(bstr, self._minor_version)
        self._read_field(bstr, self._compatible_brands,
                         until_pos=(header.start_pos + header.box_size) * 8)


class MovieHeaderBoxFieldsList(AbstractFieldsList):
    def __init__(self):
        self._creation_time = self.Field(value_type="uintbe", size=32)
        self._modification_time = self.Field(value_type="uintbe", size=32)
        self._timescale = self.Field(value_type="uintbe", size=32)
        self._duration = self.Field(value_type="uintbe", size=32)

        self._rate = self.Field(value_type="uintbe", size=32)
        self._volume = self.Field(value_type="uintbe", size=16)

        self._reserved0 = self.Field(value_type="bits", size=16)
        self._reserved1 = self.Field(value_type="bits", size=32, is_list=True)
        self._reserved1_length = 32 * 2

        self._matrix = self.Field(value_type="uintbe", size=32, is_list=True)
        self._matrix_length = 32 * 9
        self._pre_defined = self.Field(value_type="bits", size=32, is_list=True)
        self._pre_defined_length = 32 * 6

        self._next_track_id = self.Field(value_type="uintbe", size=32)

        super(MovieHeaderBoxFieldsList, self).__init__(11)

    @property
    def creation_time(self):
        return self._creation_time.value

    @creation_time.setter
    def creation_time(self, value):
        self._set_field(self._creation_time, *value)

    @property
    def modification_time(self):
        return self._modification_time.value

    @modification_time.setter
    def modification_time(self, value):
        self._set_field(self._modification_time, *value)

    @property
    def timescale(self):
        return self._timescale.value

    @timescale.setter
    def timescale(self, value):
        self._set_field(self._timescale, *value)

    @property
    def duration(self):
        return self._duration.value

    @duration.setter
    def duration(self, value):
        self._set_field(self._duration, *value)

    @property
    def rate(self):
        return self._rate.value

    @rate.setter
    def rate(self, value):
        self._set_field(self._rate, *value)

    @property
    def volume(self):
        return self._volume.value

    @volume.setter
    def volume(self, value):
        self._set_field(self._volume, *value)

    @property
    def matrix(self):
        return self._matrix.value

    @matrix.setter
    def matrix(self, value):
        self._set_field(self._matrix, *value)

    @property
    def pre_defined(self):
        return self._pre_defined.value

    @pre_defined.setter
    def pre_defined(self, value):
        self._set_field(self._pre_defined, *value)

    @property
    def next_track_id(self):
        return self._next_track_id.value

    @next_track_id.setter
    def next_track_id(self, value):
        self._set_field(self._next_track_id, *value)

    def parse_fields(self, bstr, header):
        if header.version == 1:
            self._read_field(bstr, self._creation_time, value_type="uintbe:64")
            self._read_field(bstr, self._modification_time, value_type="uintbe:64")
            self._read_field(bstr, self._timescale, value_type="uintbe:32")
            self._read_field(bstr, self._duration, value_type="uintbe:64")
        else:
            self._read_field(bstr, self._creation_time)
            self._read_field(bstr, self._modification_time)
            self._read_field(bstr, self._timescale)
            self._read_field(bstr, self._duration)

        self._read_field(bstr, self._rate)
        self._read_field(bstr, self._volume)

        self._read_field(bstr, self._reserved0)
        self._read_field(bstr, self._reserved1,
                         until_pos=bstr.bitpos + self._reserved1_length)

        self._read_field(bstr, self._matrix,
                         until_pos=bstr.bitpos + self._matrix_length)
        self._read_field(bstr, self._pre_defined,
                         until_pos=bstr.bitpos + self._pre_defined_length)

        self._read_field(bstr, self._next_track_id)


class TrackHeaderBoxFieldsList(AbstractFieldsList):
    def __init__(self):
        self._creation_time = self.Field(value_type="uintbe", size=32)
        self._modification_time = self.Field(value_type="uintbe", size=32)
        self._track_id = self.Field(value_type="uintbe", size=32)
        self._reserved0 = self.Field(value_type="bits", size=32)
        self._duration = self.Field(value_type="uintbe", size=32)

        self._reserved1 = self.Field(value_type="bits", size=32, is_list=True)
        self._reserved1_length = 32 * 2

        self._layer = self.Field(value_type="uintbe", size=16)
        self._alternate_group = self.Field(value_type="uintbe", size=16)
        self._volume = self.Field(value_type="uintbe", size=16)

        self._reserved2 = self.Field(value_type="bits", size=16)

        self._matrix = self.Field(value_type="uintbe", size=32, is_list=True)
        self._matrix_length = 32 * 9

        # TODO: create a 16.16 float representation
        self._width = self.Field(value_type="uintbe", size=16, is_list=True)
        self._width_length = 16 * 2
        self._height = self.Field(value_type="uintbe", size=16, is_list=True)
        self._height_length = 16 * 2

        super(TrackHeaderBoxFieldsList, self).__init__(13)

    @property
    def creation_time(self):
        return self._creation_time.value

    @creation_time.setter
    def creation_time(self, value):
        self._set_field(self._creation_time, *value)

    @property
    def modification_time(self):
        return self._modification_time.value

    @modification_time.setter
    def modification_time(self, value):
        self._set_field(self._modification_time, *value)

    @property
    def track_id(self):
        return self._track_id.value

    @track_id.setter
    def track_id(self, value):
        self._set_field(self._track_id, *value)

    @property
    def duration(self):
        return self._duration.value

    @duration.setter
    def duration(self, value):
        self._set_field(self._duration, *value)

    @property
    def layer(self):
        return self._layer.value

    @layer.setter
    def layer(self, value):
        self._set_field(self._layer, *value)

    @property
    def alternate_group(self):
        return self._alternate_group.value

    @alternate_group.setter
    def alternate_group(self, value):
        self._set_field(self._alternate_group, *value)

    @property
    def volume(self):
        return self._volume.value

    @volume.setter
    def volume(self, value):
        self._set_field(self._volume, *value)

    @property
    def matrix(self):
        return self._matrix.value

    @matrix.setter
    def matrix(self, value):
        self._set_field(self._matrix, *value)

    @property
    def width(self):
        return self._width.value

    @width.setter
    def width(self, value):
        self._set_field(self._width, *value)

    @property
    def height(self):
        return self._height.value

    @height.setter
    def height(self, value):
        self._set_field(self._height, *value)

    def parse_fields(self, bstr, header):
        if header.version == 1:
            self._read_field(bstr, self._creation_time, value_type="uintbe:64")
            self._read_field(bstr, self._modification_time, value_type="uintbe:64")
            self._read_field(bstr, self._track_id, value_type="uintbe:32")
            self._read_field(bstr, self._reserved0, value_type="uintbe:32")
            self._read_field(bstr, self._duration, value_type="uintbe:64")
        else:
            self._read_field(bstr, self._creation_time)
            self._read_field(bstr, self._modification_time)
            self._read_field(bstr, self._track_id)
            self._read_field(bstr, self._reserved0)
            self._read_field(bstr, self._duration)

        self._read_field(bstr, self._reserved1,
                         until_pos=bstr.bitpos + self._reserved1_length)

        self._read_field(bstr, self._layer)
        self._read_field(bstr, self._alternate_group)
        self._read_field(bstr, self._volume)

        self._read_field(bstr, self._reserved2)

        self._read_field(bstr, self._matrix,
                         until_pos=bstr.bitpos + self._matrix_length)

        self._read_field(bstr, self._width,
                         until_pos=bstr.bitpos + self._width_length)
        self._read_field(bstr, self._height,
                         until_pos=bstr.bitpos + self._height_length)


class MediaHeaderBoxFieldsList(AbstractFieldsList):
    def __init__(self):
        self._creation_time = self.Field(value_type="uintbe", size=32)
        self._modification_time = self.Field(value_type="uintbe", size=32)
        self._timescale = self.Field(value_type="uintbe", size=32)
        self._duration = self.Field(value_type="uintbe", size=32)

        self._pad0 = self.Field(value_type="bits", size=1)

        # TODO: check if uintbe can be used here
        self._language = self.Field(value_type="uint", size=5, is_list=True)
        self._language_length = 5 * 3
        self._pre_defined = self.Field(value_type="uintbe", size=16)

        super(MediaHeaderBoxFieldsList, self).__init__(7)

    @property
    def creation_time(self):
        return self._creation_time.value

    @creation_time.setter
    def creation_time(self, value):
        self._set_field(self._creation_time, *value)

    @property
    def modification_time(self):
        return self._modification_time.value

    @modification_time.setter
    def modification_time(self, value):
        self._set_field(self._modification_time, *value)

    @property
    def timescale(self):
        return self._timescale.value

    @timescale.setter
    def timescale(self, value):
        self._set_field(self._timescale, *value)

    @property
    def duration(self):
        return self._duration.value

    @duration.setter
    def duration(self, value):
        self._set_field(self._duration, *value)

    @property
    def language(self):
        return self._language.value

    @language.setter
    def language(self, value):
        self._set_field(self._language, *value)

    @property
    def pre_defined(self):
        return self._pre_defined.value

    @pre_defined.setter
    def pre_defined(self, value):
        self._set_field(self._pre_defined, *value)

    def parse_fields(self, bstr, header):
        if header.version == 1:
            self._read_field(bstr, self._creation_time, value_type="uintbe:64")
            self._read_field(bstr, self._modification_time, value_type="uintbe:64")
            self._read_field(bstr, self._timescale, value_type="uintbe:32")
            self._read_field(bstr, self._duration, value_type="uintbe:64")
        else:
            self._read_field(bstr, self._creation_time)
            self._read_field(bstr, self._modification_time)
            self._read_field(bstr, self._timescale)
            self._read_field(bstr, self._duration)

        self._read_field(bstr, self._pad0)

        self._read_field(bstr, self._language,
                         until_pos=bstr.bitpos + self._language_length)
        self._read_field(bstr, self._pre_defined)


class HandlerReferenceBoxFieldsList(AbstractFieldsList):
    def __init__(self):
        self._pre_defined = self.Field(value_type="uintbe", size=32)
        self._handler_type = self.Field(value_type="bytes", size=4)

        self._reserved0 = self.Field(value_type="bits", size=32, is_list=True)
        self._reserved0_length = 32 * 3

        self._name = self.Field(value_type="bytes", is_string=True)

        super(HandlerReferenceBoxFieldsList, self).__init__(4)

    @property
    def pre_defined(self):
        return self._pre_defined.value

    @pre_defined.setter
    def pre_defined(self, value):
        self._set_field(self._pre_defined, *value)

    @property
    def handler_type(self):
        return self._handler_type.value

    @handler_type.setter
    def handler_type(self, value):
        self._set_field(self._handler_type, *value)

    @property
    def name(self):
        return self._name.value

    @name.setter
    def name(self, value):
        self._set_field(self._name, *value)

    def parse_fields(self, bstr, header):
        del header

        self._read_field(bstr, self._pre_defined)
        self._read_field(bstr, self._handler_type)

        self._read_field(bstr, self._reserved0,
                         until_pos=bstr.bitpos + self._reserved0_length)

        self._read_field(bstr, self._name)


class VideoMediaHeaderBoxFieldsList(AbstractFieldsList):
    def __init__(self):
        self._graphicsmode = self.Field(value_type="uintbe", size=16)
        self._opcolor = self.Field(value_type="uintbe", size=16, is_list=True)
        self._opcolor_length = 16 * 3

        super(VideoMediaHeaderBoxFieldsList, self).__init__(2)

    @property
    def graphicsmode(self):
        return self._graphicsmode.value

    @graphicsmode.setter
    def graphicsmode(self, value):
        self._set_field(self._graphicsmode, *value)

    @property
    def opcolor(self):
        return self._opcolor.value

    @opcolor.setter
    def opcolor(self, value):
        self._set_field(self._opcolor, *value)

    def parse_fields(self, bstr, header):
        del header
        self._read_field(bstr, self._graphicsmode)
        self._read_field(bstr, self._opcolor,
                         until_pos=bstr.bitpos + self._opcolor_length)


class SampleDescriptionBoxFieldsList(AbstractFieldsList):
    def __init__(self):
        self._entry_count = self.Field(value_type="uintbe", size=32)

        super(SampleDescriptionBoxFieldsList, self).__init__(1)

    @property
    def entry_count(self):
        return self._entry_count.value

    @entry_count.setter
    def entry_count(self, value):
        self._set_field(self._entry_count, *value)

    def parse_fields(self, bstr, header):
        del header
        self._read_field(bstr, self._entry_count)


class BoxHeader(BoxHeaderFieldsList):
    def __init__(self, length=4):
        self._start_pos = None
        self._type_cache = None
        self._box_size_cache = None
        self._header_size_cache = None
        self._content_size_cache = None
        super(BoxHeader, self).__init__(length)

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
        self._update_cache(bstr.bytepos - self._start_pos)

    def _update_cache(self, header_size):
        self._type_cache = (self._box_type.value + self._user_type.value
                            if self._user_type.value is not None
                            else self._box_type.value)
        self._box_size_cache = (self._box_ext_size.value
                                if self._box_ext_size.value is not None
                                else self._box_size.value)
        self._header_size_cache = header_size
        self._content_size_cache = self._box_size_cache - header_size


class FullBoxHeader(BoxHeader, FullBoxHeaderFieldsList):
    def __init__(self, length=6):
        FullBoxHeaderFieldsList.__init__(self, length)
        super(FullBoxHeader, self).__init__(length)

    def parse_fields(self, bstr):
        super(FullBoxHeader, self).parse_fields(bstr)
        self._parse_extend_fields(bstr)

    def extend_header(self, bstr, header):
        self._set_field(self._box_size, header.box_size)
        self._set_field(self._box_type, header.box_type)
        self._set_field(self._box_ext_size, header.box_ext_size)
        self._set_field(self._user_type, header.user_type)

        self._start_pos = header.start_pos
        self._parse_extend_fields(bstr)
        self._update_cache(bstr.bytepos - self._start_pos)
    
    def _parse_extend_fields(self, bstr):
        FullBoxHeaderFieldsList.parse_fields(self, bstr)


class UnknownBox(AbstractBox, MixinDictRepr):
    type = b"unkn"

    def __init__(self, header):
        super(UnknownBox, self).__init__(header)
        self.payload = None

    def __bytes__(self):
        return super(UnknownBox, self).__bytes__() + \
               self.payload

    def load(self, bstr):
        bstr.bytepos = self.header.start_pos + self.header.header_size
        self.payload = bstr.read(self.header.content_size * 8).bytes

    def parse(self, bstr):
        bstr.bytepos = self._header.start_pos + self._header.box_size


class ContainerBox(AbstractBox, MixinDictRepr):
    def __init__(self, header):
        super(ContainerBox, self).__init__(header)
        self._boxes = None

    def __bytes__(self):
        bytes_buffer = [super(ContainerBox, self).__bytes__()]
        bytes_buffer.extend([bytes(box) for box in self._boxes])
        return b''.join(bytes_buffer)

    @property
    def boxes(self):
        return self._boxes

    def load(self, bstr):
        bstr.bitpos = self.header.start_pos + self.header.header_size
        for box in self._boxes:
            box.load(bstr)

    def parse(self, bstr):
        self.parse_boxes(bstr)

    def parse_boxes(self, bstr):
        self._boxes = []
        end_pos = self._header.start_pos + self._header.box_size
        while bstr.bytepos < end_pos:
            header = Parser.parse_header(bstr)
            self._boxes.append(Parser.parse_box(bstr, header))


class FileTypeBox(AbstractBox, FileTypeBoxFieldsList, MixinDictRepr):
    type = b"ftyp"

    def __init__(self, header):
        FileTypeBoxFieldsList.__init__(self)
        super(FileTypeBox, self).__init__(header)

    def __bytes__(self):
        return super(FileTypeBox, self).__bytes__() + \
               AbstractFieldsList.__bytes__(self)

    def load(self, bstr):
        pass

    def parse(self, bstr):
        self.parse_fields(bstr, self._header)


class MovieBox(ContainerBox, MixinDictRepr):
    type = b"moov"


class MovieHeaderBox(AbstractFullBox, MovieHeaderBoxFieldsList, MixinDictRepr):
    type = b"mvhd"

    def __init__(self, header):
        MovieHeaderBoxFieldsList.__init__(self)
        super(MovieHeaderBox, self).__init__(header)

    def __bytes__(self):
        return super(MovieHeaderBox, self).__bytes__() + \
               AbstractFieldsList.__bytes__(self)

    def load(self, bstr):
        pass

    def parse(self, bstr):
        self.parse_fields(bstr, self._header)


class TrackBox(ContainerBox, MixinDictRepr):
    type = b"trak"


class TrackHeaderBox(AbstractFullBox, TrackHeaderBoxFieldsList, MixinDictRepr):
    type = b"tkhd"

    def __init__(self, header):
        TrackHeaderBoxFieldsList.__init__(self)
        super(TrackHeaderBox, self).__init__(header)

    def __bytes__(self):
        return super(TrackHeaderBox, self).__bytes__() + \
               AbstractFieldsList.__bytes__(self)

    @property
    def width(self):
        return self._width.value[0]

    @property
    def height(self):
        return self._height.value[0]

    @property
    def is_audio(self):
        return self._volume.value == 1

    def load(self, bstr):
        pass

    def parse(self, bstr):
        self.parse_fields(bstr, self._header)


class MediaBox(ContainerBox, MixinDictRepr):
    type = b"mdia"


class MediaHeaderBox(AbstractFullBox, MediaHeaderBoxFieldsList, MixinDictRepr):
    type = b"mdhd"

    def __init__(self, header):
        MediaHeaderBoxFieldsList.__init__(self)
        super(MediaHeaderBox, self).__init__(header)

    def __bytes__(self):
        return super(MediaHeaderBox, self).__bytes__() + \
               AbstractFieldsList.__bytes__(self)

    def load(self, bstr):
        pass

    def parse(self, bstr):
        self.parse_fields(bstr, self._header)


class HandlerReferenceBox(AbstractFullBox, HandlerReferenceBoxFieldsList, MixinDictRepr):
    type = b"hdlr"

    def __init__(self, header):
        HandlerReferenceBoxFieldsList.__init__(self)
        super(HandlerReferenceBox, self).__init__(header)

    def __bytes__(self):
        return super(HandlerReferenceBox, self).__bytes__() + \
               AbstractFieldsList.__bytes__(self)

    def load(self, bstr):
        pass

    def parse(self, bstr):
        self.parse_fields(bstr, self._header)


class MediaInformationBox(ContainerBox, MixinDictRepr):
    type = b"minf"


class VideoMediaHeaderBox(AbstractFullBox, VideoMediaHeaderBoxFieldsList, MixinDictRepr):
    type = b"vmhd"

    def __init__(self, header):
        VideoMediaHeaderBoxFieldsList.__init__(self)
        super(VideoMediaHeaderBox, self).__init__(header)

    def __bytes__(self):
        return super(VideoMediaHeaderBox, self).__bytes__() + \
               AbstractFieldsList.__bytes__(self)

    def load(self, bstr):
        pass

    def parse(self, bstr):
        self.parse_fields(bstr, self._header)


class DataInformationBox(ContainerBox, MixinDictRepr):
    type = b"dinf"


class SampleTableBox(ContainerBox, MixinDictRepr):
    type = b"stbl"


class SampleDescriptionBox(ContainerBox, SampleDescriptionBoxFieldsList, MixinDictRepr):
    type = b"stsd"

    def __init__(self, header):
        SampleDescriptionBoxFieldsList.__init__(self)
        super(SampleDescriptionBox, self).__init__(header)

    def __bytes__(self):
        return super(SampleDescriptionBox, self).__bytes__() + \
               AbstractFieldsList.__bytes__(self)

    def parse(self, bstr):
        self.parse_fields(bstr, self._header)
        self.parse_boxes(bstr)

    def parse_boxes(self, bstr):
        self._boxes = []
        for i in range(self._entry_count.value):
            header = Parser.parse_header(bstr)
            self._boxes.append(Parser.parse_box(bstr, header))

    @classmethod
    def parse_box(cls, bstr, header):
        full_box_header = FullBoxHeader()
        full_box_header.extend_header(bstr, header)
        del header
        return super(SampleDescriptionBox, cls).parse_box(bstr, full_box_header)


class Parser(object):
    _box_lookup = {}

    @classmethod
    def register_box(cls, box_cls):
        cls._box_lookup[box_cls.type] = box_cls.parse_box

    @classmethod
    def parse(cls, filename=None, bytes_input=None, file_input=None,
              offset_bytes=0, headers_only=False):
        """
        Parse an MP4 file or bytes into boxes

        :param filename: filename of mp4 file.
        :type filename: str.
        :param bytes_input: bytes of mp4 file.
        :type bytes_input: bytes / Python 2.x str.
        :param file_input: Filename or file object
        :type file_input: str, file
        :param offset_bytes: start parsing at offset.
        :type offset_bytes: int.
        :param headers_only: Ignore data and return just headers. Useful when data is cut short
        :type: headers_only: boolean
        :return: BMFF Boxes or Headers
        """

        if filename:
            bstr = bs.ConstBitStream(filename=filename, offset=offset_bytes * 8)
        elif bytes_input:
            bstr = bs.ConstBitStream(bytes=bytes_input, offset=offset_bytes * 8)
        else:
            bstr = bs.ConstBitStream(auto=file_input, offset=offset_bytes * 8)

        log.debug("Starting parse")
        log.debug("Size is %d bits", bstr.len)

        while bstr.pos < bstr.len:
            log.debug("Byte pos before header: %d relative to (%d)", bstr.bytepos, offset_bytes)
            log.debug("Reading header")
            header = cls.parse_header(bstr)
            log.debug("Header type: %s", header.box_type)
            log.debug("Byte pos after header: %d relative to (%d)", bstr.bytepos, offset_bytes)

            if headers_only:
                yield header

                # move pointer to next header if possible
                try:
                    bstr.bytepos = header.start_pos + header.box_size
                except ValueError:
                    log.warning("Premature end of data")
                    raise
            else:
                yield cls.parse_box(bstr, header)

    @staticmethod
    def parse_header(bstr):
        try:
            header = BoxHeader()
            header.parse(bstr)
        except bs.ReadError:
            log.error("Premature end of data while reading box header")
            raise
        return header

    @classmethod
    def parse_box(cls, bstr, header):
        # Get parser method for header type
        parse_function = cls._box_lookup.get(header.type, UnknownBox.parse_box)
        try:
            box = parse_function(bstr, header)
        except ValueError:
            log.error("Premature end of data")
            raise
        return box

    @classmethod
    def _is_mp4(cls, parser):
        try:
            _ = next(iter(parser))
            return True
        except ValueError:
            return False

    @classmethod
    def is_mp4_s(cls, bytes_input):
        """
        Is bytes_input the contents of an MP4 file

        :param bytes_input: str/bytes to check.
        :type bytes_input: str/bytes.
        :return:
        """

        parser = cls.parse(bytes_input=bytes_input, headers_only=True)
        return cls._is_mp4(parser)

    @classmethod
    def is_mp4(cls, file_input):
        """
        Checks input if it's an MP4 file

        :param file_input: Filename or file object
        :type file_input: str, file
        :returns:  bool.
        :raises: AttributeError, KeyError
        """

        if hasattr(file_input, "read"):
            parser = cls.parse(file_input=file_input, headers_only=True)
        else:
            parser = cls.parse(filename=file_input, headers_only=True)
        return cls._is_mp4(parser)


FTYP = FileTypeBox
MOOV = MovieBox
MVHD = MovieHeaderBox
TRAK = TrackBox
TKHD = TrackHeaderBox
MDIA = MediaBox
MDHD = MediaHeaderBox
HDLR = HandlerReferenceBox
MINF = MediaInformationBox
VMHD = VideoMediaHeaderBox
DINF = DataInformationBox
STBL = SampleTableBox
STSD = SampleDescriptionBox

Parser.register_box(FTYP)
Parser.register_box(MOOV)
Parser.register_box(MVHD)
Parser.register_box(TRAK)
Parser.register_box(TKHD)
Parser.register_box(MDIA)
Parser.register_box(MDHD)
Parser.register_box(HDLR)
Parser.register_box(MINF)
Parser.register_box(VMHD)
Parser.register_box(DINF)
Parser.register_box(STBL)
Parser.register_box(STSD)
