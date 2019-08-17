import bitstring as bs


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
    def value_size(self):
        return 0 if self._value_size is None else self._value_size

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


class AbstractFieldsList:
    def __init__(self, length):
        self._fields = [None] * length
        self._end_index = 0

    def __bytes__(self):
        values = []
        types = []
        for field in self._fields[:self._end_index]:
            if field is None:
                continue
            if field.is_list:
                values.extend(field.value)
                types.extend([field.type] * len(field.value))
            else:
                values.append(field.value)
                types.append(field.type)
        return bs.pack(','.join(types), *values).bytes

    def __len__(self):
        # TODO: this could be optimized if needed
        return len([field for field in self._fields[:self._end_index]
                    if field is not None])

    def _set_field(self, field, value, value_type=None):
        if value is not None:
            if field.index is None:
                self._register_field(field)
            else:
                self._end_index = field.index + 1
            if field.value is None:
                self._fields[field.index] = field
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

    def _register_field(self, field):
        field.index = self._end_index
        self._end_index += 1
        return field

    @property
    def fields(self):
        # TODO: this could be optimized if needed
        return [field for field in self._fields[:self._end_index] if
                field is not None]


class BoxHeaderFieldsList(AbstractFieldsList):
    def __init__(self, length=0):
        super().__init__(length + 4)

        self._box_size = self._register_field(Field(value_type="uintbe", size=32))
        self._box_type = self._register_field(Field(value_type="bytes", size=4))
        self._box_ext_size = self._register_field(Field(value_type="uintbe", size=64))
        self._user_type = self._register_field(Field(value_type="bytes", size=16))

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
        if self._box_size.value == 1:
            self._read_field(bstr, self._box_ext_size)

        if self._box_type.value == b'uuid':
            self._read_field(bstr, self._user_type)


class FullBoxHeaderFieldsList(AbstractFieldsList):
    def __init__(self, length=0):
        super().__init__(length + 2)

        self._version = self._register_field(Field(value_type="uintbe", size=8))
        self._flags = self._register_field(Field(value_type="bits", size=24))

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


class DataBoxFieldsList(AbstractFieldsList):
    def __init__(self, length=0):
        super().__init__(length + 1)

        self._data = self._register_field(Field(value_type="bytes"))

    @property
    def data(self):
        return self._data.value

    @data.setter
    def data(self, value):
        self._set_field(self._data, *value)

    def parse_fields(self, bstr, header):
        data_length = header.box_size - header.header_size
        self._read_field(bstr, self._data, value_type="bytes:{}".format(data_length))


# Root boxes
class FileTypeBoxFieldsList(AbstractFieldsList):
    def __init__(self, length=0):
        super().__init__(length + 3)

        self._major_brand = \
            self._register_field(Field(value_type="uintbe", size=32))
        self._minor_version = \
            self._register_field(Field(value_type="uintbe", size=32))
        self._compatible_brands = \
            self._register_field(Field(value_type="uintbe", size=32, is_list=True))

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
    def __init__(self, length=0):
        super().__init__(length + 11)

        self._creation_time = \
            self._register_field(Field(value_type="uintbe", size=64))
        self._modification_time = \
            self._register_field(Field(value_type="uintbe", size=64))
        self._timescale = \
            self._register_field(Field(value_type="uintbe", size=32))
        self._duration = \
            self._register_field(Field(value_type="uintbe", size=64))

        self._rate = \
            self._register_field(Field(value_type="uintbe", size=32))
        self._volume = \
            self._register_field(Field(value_type="uintbe", size=16))

        self._reserved0 = \
            self._register_field(Field(value_type="bits", size=16))
        self._reserved1 = \
            self._register_field(Field(value_type="bits", size=32, is_list=True))
        self._reserved1_length = 32 * 2

        self._matrix = \
            self._register_field(Field(value_type="uintbe", size=32, is_list=True))
        self._matrix_length = 32 * 9
        self._pre_defined = \
            self._register_field(Field(value_type="bits", size=32, is_list=True))
        self._pre_defined_length = 32 * 6

        self._next_track_id = \
            self._register_field(Field(value_type="uintbe", size=32))

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
        if header.version != 1:
            self._creation_time.type = "uintbe:32"
            self._modification_time.type = "uintbe:32"
            self._timescale.type = "uintbe:32"
            self._duration.type = "uintbe:32"

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
    def __init__(self, length=0):
        super().__init__(length + 13)

        self._creation_time = \
            self._register_field(Field(value_type="uintbe", size=64))
        self._modification_time = \
            self._register_field(Field(value_type="uintbe", size=64))
        self._track_id = \
            self._register_field(Field(value_type="uintbe", size=32))
        self._reserved0 = \
            self._register_field(Field(value_type="bits", size=32))
        self._duration = \
            self._register_field(Field(value_type="uintbe", size=64))

        self._reserved1 = \
            self._register_field(Field(value_type="bits", size=32, is_list=True))
        self._reserved1_length = 32 * 2

        self._layer = \
            self._register_field(Field(value_type="uintbe", size=16))
        self._alternate_group = \
            self._register_field(Field(value_type="uintbe", size=16))
        self._volume = \
            self._register_field(Field(value_type="uintbe", size=16))

        self._reserved2 = \
            self._register_field(Field(value_type="bits", size=16))

        self._matrix = \
            self._register_field(Field(value_type="uintbe", size=32, is_list=True))
        self._matrix_length = 32 * 9

        # TODO: create a 16.16 float representation
        self._width = \
            self._register_field(Field(value_type="uintbe", size=16, is_list=True))
        self._width_length = 16 * 2
        self._height = \
            self._register_field(Field(value_type="uintbe", size=16, is_list=True))
        self._height_length = 16 * 2

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
        if header.version != 1:
            self._creation_time.type = "uintbe:32"
            self._modification_time.type = "uintbe:32"
            self._track_id.type = "uintbe:32"
            self._reserved0.type = "uintbe:32"
            self._duration.type = "uintbe:32"

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
    def __init__(self, length=0):
        super().__init__(length + 7)

        self._creation_time = \
            self._register_field(Field(value_type="uintbe", size=64))
        self._modification_time = \
            self._register_field(Field(value_type="uintbe", size=64))
        self._timescale = \
            self._register_field(Field(value_type="uintbe", size=32))
        self._duration = \
            self._register_field(Field(value_type="uintbe", size=64))

        self._pad0 = \
            self._register_field(Field(value_type="bits", size=1))

        # TODO: check if uintbe can be used here
        self._language = \
            self._register_field(Field(value_type="uint", size=5, is_list=True))
        self._language_length = 5 * 3
        self._pre_defined = \
            self._register_field(Field(value_type="uintbe", size=16))

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
        if header.version != 1:
            self._creation_time.type = "uintbe:32"
            self._modification_time.type = "uintbe:32"
            self._timescale.type = "uintbe:32"
            self._duration.type = "uintbe:32"

        self._read_field(bstr, self._creation_time)
        self._read_field(bstr, self._modification_time)
        self._read_field(bstr, self._timescale)
        self._read_field(bstr, self._duration)

        self._read_field(bstr, self._pad0)

        self._read_field(bstr, self._language,
                         until_pos=bstr.bitpos + self._language_length)
        self._read_field(bstr, self._pre_defined)


class HandlerReferenceBoxFieldsList(AbstractFieldsList):
    def __init__(self, length=0):
        super().__init__(length + 4)

        self._pre_defined = \
            self._register_field(Field(value_type="uintbe", size=32))
        self._handler_type = \
            self._register_field(Field(value_type="bytes", size=4))

        self._reserved0 = \
            self._register_field(Field(value_type="bits", size=32, is_list=True))
        self._reserved0_length = 32 * 3

        self._name = \
            self._register_field(Field(value_type="bytes", is_string=True))

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
    def __init__(self, length=0):
        super().__init__(length + 2)

        self._graphicsmode = \
            self._register_field(Field(value_type="uintbe", size=16))
        self._opcolor = \
            self._register_field(Field(value_type="uintbe", size=16, is_list=True))
        self._opcolor_length = 16 * 3

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
    def __init__(self, length=0):
        super().__init__(length + 1)

        self._entry_count = self._register_field(Field(value_type="uintbe", size=32))

    @property
    def entry_count(self):
        return self._entry_count.value

    @entry_count.setter
    def entry_count(self, value):
        self._set_field(self._entry_count, *value)

    def parse_fields(self, bstr, header):
        del header
        self._read_field(bstr, self._entry_count)


# dinf boxes
class DataReferenceBoxFieldsList(AbstractFieldsList):
    def __init__(self, length=0):
        super().__init__(length + 1)

        self._entry_count = self._register_field(Field(value_type="uintbe", size=32))

    @property
    def entry_count(self):
        return self._entry_count.value

    @entry_count.setter
    def entry_count(self, value):
        self._set_field(self._entry_count, *value)

    def parse_fields(self, bstr, header):
        del header
        self._read_field(bstr, self._entry_count)


class PrimaryItemBoxFieldsList(AbstractFieldsList):
    def __init__(self, length=0):
        super().__init__(length + 1)

        self._item_id = self._register_field(Field(value_type="uintbe", size=32))

    @property
    def item_id(self):
        return self._item_id.value

    @item_id.setter
    def item_id(self, value):
        self._set_field(self._item_id, *value)

    def parse_fields(self, bstr, header):
        if header.version == 0:
            self._item_id.type = "uintbe:16"

        self._read_field(bstr, self._item_id)


class ItemInformationBoxFieldsList(AbstractFieldsList):
    def __init__(self, length=0):
        super().__init__(length + 1)

        self._entry_count = self._register_field(Field(value_type="uintbe", size=32))

    @property
    def entry_count(self):
        return self._entry_count.value

    @entry_count.setter
    def entry_count(self, value):
        self._set_field(self._entry_count, *value)

    def parse_fields(self, bstr, header):
        if header.version == 0:
            self._entry_count.type = "uintbe:16"

        self._read_field(bstr, self._entry_count)


# dref boxes
class DataEntryUrlBoxFieldsList(AbstractFieldsList):
    def __init__(self, length=0):
        super().__init__(length + 1)

        self._location = self._register_field(Field(value_type="bytes", is_string=True))

    @property
    def location(self):
        return self._location.value

    @location.setter
    def location(self, value):
        self._set_field(self._location, *value)

    def parse_fields(self, bstr, header):
        # It seams that location can be empty (0 bytes) based on the result in
        # the test file photo.heic
        if bstr.bytepos < header.start_pos + header.box_size:
            self._read_field(bstr, self._location)


class DataEntryUrnBoxFieldsList(AbstractFieldsList):
    def __init__(self, length=0):
        super().__init__(length + 2)

        self._name = self._register_field(Field(value_type="bytes", is_string=True))
        self._location = self._register_field(Field(value_type="bytes", is_string=True))

    @property
    def location(self):
        return self._location.value

    @location.setter
    def location(self, value):
        self._set_field(self._location, *value)

    @property
    def name(self):
        return self._name.value

    @name.setter
    def name(self, value):
        self._set_field(self._name, *value)

    def parse_fields(self, bstr, header):
        end = header.start_pos + header.box_size
        self._read_field(bstr, self._name)
        # If this acts like the URL_ box, it seams that location can be empty
        # (0 bytes) based on the result in the test file photo.heic
        if bstr.bytepos < end:
            self._read_field(bstr, self._location)


# iinf boxes
class ItemInfoEntryBoxFieldsList(AbstractFieldsList):
    def __init__(self, length=0):
        super().__init__(length + 8)

        self._item_id = \
            self._register_field(Field(value_type="uintbe", size=32))
        self._item_protection_index = \
            self._register_field(Field(value_type="uintbe", size=16))
        self._item_type = \
            self._register_field(Field(value_type="uintbe", size=32))
        self._item_name = \
            self._register_field(Field(value_type="bytes", is_string=True))
        self._item_uri_type = \
            self._register_field(Field(value_type="bytes", is_string=True))
        self._content_type = \
            self._register_field(Field(value_type="bytes", is_string=True))
        self._content_encoding = \
            self._register_field(Field(value_type="bytes", is_string=True))

        self._extension_type = \
            self._register_field(Field(value_type="uintbe", size=32))

    @property
    def item_id(self):
        return self._item_id.value

    @item_id.setter
    def item_id(self, value):
        self._set_field(self._item_id, *value)

    @property
    def item_protection_index(self):
        return self._item_protection_index.value

    @item_protection_index.setter
    def item_protection_index(self, value):
        self._set_field(self._item_protection_index, *value)

    @property
    def item_type(self):
        return self._item_type.value

    @item_type.setter
    def item_type(self, value):
        self._set_field(self._item_type, *value)

    @property
    def item_name(self):
        return self._item_name.value

    @item_name.setter
    def item_name(self, value):
        self._set_field(self._item_name, *value)

    @property
    def item_uri_type(self):
        return self._item_uri_type.value

    @item_uri_type.setter
    def item_uri_type(self, value):
        self._set_field(self._item_uri_type, *value)

    @property
    def content_type(self):
        return self._content_type.value

    @content_type.setter
    def content_type(self, value):
        self._set_field(self._content_type, *value)

    @property
    def content_encoding(self):
        return self._content_encoding.value

    @content_encoding.setter
    def content_encoding(self, value):
        self._set_field(self._content_encoding, *value)

    @property
    def extension_type(self):
        return self._extension_type.value

    @extension_type.setter
    def extension_type(self, value):
        self._set_field(self._extension_type, *value)

    def parse_fields(self, bstr, header):
        if header.version == 2:
            self._item_id.type = "uintbe:16"

        end = header.start_pos + header.box_size

        if header.version == 0 or header.version == 1:
            self._read_field(bstr, self._item_id)
            self._read_field(bstr, self._item_protection_index)
            self._read_field(bstr, self._item_name)

            self._read_field(bstr, self._content_type)
            if bstr.bytepos < end:
                self._read_field(bstr, self._content_encoding)

        if header.version == 1:
            if bstr.bytepos < end:
                self._read_field(bstr, self._extension_type)

        elif header.version == 2 or header.version == 3:
            self._read_field(bstr, self._item_id)
            self._read_field(bstr, self._item_protection_index)
            self._read_field(bstr, self._item_type)

            self._read_field(bstr, self._item_name)
            if self._item_type.value == 1835625829:     # b"mime"
                self._read_field(bstr, self._content_type)
                if bstr.bytepos < end:
                    self._read_field(bstr, self._content_encoding)
            elif self._item_type.value == 1970432288:   # b"uri "
                self._read_field(bstr, self._item_uri_type)
            elif self._item_type.value == 1752589105:   # b"hvc1"
                # TODO: find documentation regarding type hvc1
                pass
            elif self._item_type.value == 1735551332:   # b"grid"
                # TODO: find documentation regarding type grid
                pass
            elif self._item_type.value == 1165519206:   # b"Exif"
                # TODO: find documentation regarding type Exif
                pass


# meta boxes
class ItemLocationBoxFieldsList(AbstractFieldsList):
    def __init__(self, length=0):
        super().__init__(length + 6)

        self._offset_size = \
            self._register_field(Field(value_type="uint", size=4))
        self._length_size = \
            self._register_field(Field(value_type="uint", size=4))
        self._base_offset_size = \
            self._register_field(Field(value_type="uint", size=4))
        self._index_size = \
            self._register_field(Field(value_type="uint", size=4))
        self._reserved0 = \
            self._register_field(Field(value_type="uint", size=4))

        self._item_count = \
            self._register_field(Field(value_type="uintbe", size=32))

    @property
    def offset_size(self):
        return self._offset_size.value

    @offset_size.setter
    def offset_size(self, value):
        self._set_field(self._offset_size, *value)

    @property
    def length_size(self):
        return self._length_size.value

    @length_size.setter
    def length_size(self, value):
        self._set_field(self._length_size, *value)

    @property
    def base_offset_size(self):
        return self._base_offset_size.value

    @base_offset_size.setter
    def base_offset_size(self, value):
        self._set_field(self._base_offset_size, *value)

    @property
    def index_size(self):
        return self._index_size.value

    @index_size.setter
    def index_size(self, value):
        self._set_field(self._index_size, *value)

    @property
    def item_count(self):
        return self._item_count.value

    @item_count.setter
    def item_count(self, value):
        self._set_field(self._item_count, *value)

    def parse_fields(self, bstr, header):
        if header.version < 2:
            self._item_count.type = "uintbe:16"

        self._read_field(bstr, self._offset_size)
        self._read_field(bstr, self._length_size)
        self._read_field(bstr, self._base_offset_size)

        if header.version == 1 or header.version == 2:
            self._read_field(bstr, self._index_size)
        else:
            self._read_field(bstr, self._reserved0)

        self._read_field(bstr, self._item_count)


class ItemLocationBoxItemFieldsList(AbstractFieldsList):
    def __init__(self, base_offset_size):
        # TODO: do mention that ItemLocationBoxItemFieldsList does not make
        #  use of super()
        AbstractFieldsList.__init__(self, 6)

        self._item_id = \
            self._register_field(Field(value_type="uintbe", size=32))
        self._reserved0 = \
            self._register_field(Field(value_type="uint", size=12))
        self._construction_method = \
            self._register_field(Field(value_type="uint", size=4))
        self._data_reference_index = \
            self._register_field(Field(value_type="uintbe", size=16))
        self._base_offset = \
            self._register_field(Field(value_type="uintbe", size=base_offset_size * 8))
        self._extent_count = \
            self._register_field(Field(value_type="uintbe", size=16))

    @property
    def item_id(self):
        return self._item_id.value

    @item_id.setter
    def item_id(self, value):
        self._set_field(self._item_id, *value)

    @property
    def construction_method(self):
        return self._construction_method.value

    @construction_method.setter
    def construction_method(self, value):
        self._set_field(self._construction_method, *value)

    @property
    def data_reference_index(self):
        return self._data_reference_index.value

    @data_reference_index.setter
    def data_reference_index(self, value):
        self._set_field(self._data_reference_index, *value)

    @property
    def base_offset(self):
        return self._base_offset.value

    @base_offset.setter
    def base_offset(self, value):
        self._set_field(self._base_offset, *value)

    @property
    def extent_count(self):
        return self._extent_count.value

    @extent_count.setter
    def extent_count(self, value):
        self._set_field(self._extent_count, *value)

    def parse_fields(self, bstr, header):
        if header.version < 2:
            self._item_id.type = "uintbe:16"

        self._read_field(bstr, self._item_id)

        if header.version == 1 or header.version == 2:
            self._read_field(bstr, self._reserved0)
            self._read_field(bstr, self._construction_method)

        self._read_field(bstr, self._data_reference_index)
        if self._base_offset.value_size > 0:
            self._read_field(bstr, self._base_offset)

        self._read_field(bstr, self._extent_count)


class ItemLocationBoxItemExtentFieldsList(AbstractFieldsList):
    def __init__(self, index_size, offset_size, length_size):
        # TODO: do mention that ItemLocationBoxItemExtentFieldsList does not
        #  make use of super()
        AbstractFieldsList.__init__(self, 3)

        self._extent_index = \
            self._register_field(Field(value_type="uintbe", size=index_size * 8))
        self._extent_offset = \
            self._register_field(Field(value_type="uintbe", size=offset_size * 8))
        self._extent_length = \
            self._register_field(Field(value_type="uintbe", size=length_size * 8))

    @property
    def extent_index(self):
        return self._extent_index.value

    @extent_index.setter
    def extent_index(self, value):
        self._set_field(self._extent_index, *value)

    @property
    def extent_offset(self):
        return self._extent_offset.value

    @extent_offset.setter
    def extent_offset(self, value):
        self._set_field(self._extent_offset, *value)

    @property
    def extent_length(self):
        return self._extent_length.value

    @extent_length.setter
    def extent_length(self, value):
        self._set_field(self._extent_length, *value)

    def parse_fields(self, bstr, header):
        if (header.version == 1 or header.version == 2) and \
           self._extent_index.value_size > 0:
            self._read_field(bstr, self._extent_index)

        if self._extent_offset.value_size > 0:
            self._read_field(bstr, self._extent_offset)
        if self._extent_length.value_size > 0:
            self._read_field(bstr, self._extent_length)


# iref boxes
class SingleItemTypeReferenceBoxFieldsList(AbstractFieldsList):
    def __init__(self, length=0):
        super().__init__(length + 3)

        self._from_item_id = \
            self._register_field(Field(value_type="uintbe", size=16))
        self._reference_count = \
            self._register_field(Field(value_type="uintbe", size=16))
        self._to_item_ids = \
            self._register_field(Field(value_type="uintbe", size=16, is_list=True))

    @property
    def from_item_id(self):
        return self._from_item_id.value

    @from_item_id.setter
    def from_item_id(self, value):
        self._set_field(self._from_item_id, *value)

    @property
    def reference_count(self):
        return self._reference_count.value

    @reference_count.setter
    def reference_count(self, value):
        self._set_field(self._reference_count, *value)

    @property
    def to_item_ids(self):
        return self._to_item_ids.value

    @to_item_ids.setter
    def to_item_ids(self, value):
        self._set_field(self._to_item_ids, *value)

    def parse_fields(self, bstr, header):
        del header
        self._read_field(bstr, self._from_item_id)
        self._read_field(bstr, self._reference_count)
        self._read_field(bstr, self._to_item_ids,
                         until_pos=bstr.bitpos + self._reference_count.value * 16)


class SingleItemTypeReferenceBoxLargeFieldsList(AbstractFieldsList):
    def __init__(self, length=0):
        super().__init__(length + 3)

        self._from_item_id = \
            self._register_field(Field(value_type="uintbe", size=32))
        self._reference_count = \
            self._register_field(Field(value_type="uintbe", size=16))
        self._to_item_ids = \
            self._register_field(Field(value_type="uintbe", size=32, is_list=True))

    @property
    def from_item_id(self):
        return self._from_item_id.value

    @from_item_id.setter
    def from_item_id(self, value):
        self._set_field(self._from_item_id, *value)

    @property
    def reference_count(self):
        return self._reference_count.value

    @reference_count.setter
    def reference_count(self, value):
        self._set_field(self._reference_count, *value)

    @property
    def to_item_ids(self):
        return self._to_item_ids.value

    @to_item_ids.setter
    def to_item_ids(self, value):
        self._set_field(self._to_item_ids, *value)

    def parse_fields(self, bstr, header):
        del header
        self._read_field(bstr, self._from_item_id)
        self._read_field(bstr, self._reference_count)
        self._read_field(bstr, self._to_item_ids,
                         until_pos=bstr.bitpos + self._reference_count.value * 32)


# iprp boxes
class ItemPropertyAssociationBoxFieldsList(AbstractFieldsList):
    def __init__(self, length=0):
        super().__init__(length + 1)

        self._entry_count = self._register_field(Field(value_type="uintbe", size=32))

    @property
    def entry_count(self):
        return self._entry_count.value

    @entry_count.setter
    def entry_count(self, value):
        self._set_field(self._entry_count, *value)

    def parse_fields(self, bstr, header):
        self._read_field(bstr, self._entry_count)


class ItemPropertyAssociationBoxEntryFieldsList(AbstractFieldsList):
    def __init__(self, length=0):
        super().__init__(length + 2)

        self._item_id = \
            self._register_field(Field(value_type="uintbe", size=32))
        self._association_count = \
            self._register_field(Field(value_type="uintbe", size=8))

    @property
    def item_id(self):
        return self._item_id.value

    @item_id.setter
    def item_id(self, value):
        self._set_field(self._item_id, *value)

    @property
    def association_count(self):
        return self._association_count.value

    @association_count.setter
    def association_count(self, value):
        self._set_field(self._association_count, *value)

    def parse_fields(self, bstr, header):
        if header.version < 1:
            self._item_id.type = "uintbe:16"

        self._read_field(bstr, self._item_id)
        self._read_field(bstr, self._association_count)


class ItemPropertyAssociationBoxEntryAssociationsFieldsList(AbstractFieldsList):
    def __init__(self, length=0):
        super().__init__(length + 3)

        self._essential = \
            self._register_field(Field(value_type="bits", size=1))
        self._property_index_8b = \
            self._register_field(Field(value_type="uint", size=8))
        self._property_index_7b = \
            self._register_field(Field(value_type="uint", size=7))
        self._property_index_cache = None

    @property
    def essential(self):
        return self._essential.value.bool

    @essential.setter
    def essential(self, value):
        self._set_field(self._essential, *value)

    @property
    def property_index(self):
        return self._property_index_cache

    @property_index.setter
    def property_index(self, value):
        value, value_type = value
        # TODO: validate that this writing is correct
        self._set_field(self._property_index_8b, value & 255)
        self._set_field(self._property_index_7b, (value & 127 << 8) >> 8)
        self._property_index_cache = value

    def parse_fields(self, bstr, header):
        self._read_field(bstr, self._essential)
        if int.from_bytes(header.flags, "big") & 1:
            # TODO: validate that this parsing is correct
            self._read_field(bstr, self._property_index_8b)
            self._read_field(bstr, self._property_index_7b)
            self._property_index_cache = self._property_index_8b.value + \
                self._property_index_7b.value << 8
        else:
            self._read_field(bstr, self._property_index_7b)
            self._property_index_cache = self._property_index_7b.value
