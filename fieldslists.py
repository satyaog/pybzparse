import bitstring as bs


class AbstractFieldsList:
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


# Root boxes
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


# moov boxes
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


# trak boxes
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


# mdia boxes
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


# minf boxes
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


# stbl boxes
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
