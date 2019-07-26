""" Benzina MP4 Parser based on https://github.com/use-sparingly/pymp4parse """

from abc import ABCMeta, abstractmethod
from ctypes import c_uint32
import logging

import bitstring as bs

from fieldslists import *

log = logging.getLogger(__name__)
log.setLevel(logging.WARN)

MAX_UINT_32 = c_uint32(-1).value


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
    type = b"____"

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


# Root boxes
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


# moov boxes
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


# trak boxes
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


# mdia boxes
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


class SampleTableBox(ContainerBox, MixinDictRepr):
    type = b"stbl"


# minf boxes
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


# stbl boxes
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


# Root boxes
FTYP = FileTypeBox
MOOV = MovieBox

# moov boxes
MVHD = MovieHeaderBox
TRAK = TrackBox

# trak boxes
TKHD = TrackHeaderBox
MDIA = MediaBox

# mdia boxes
MDHD = MediaHeaderBox
HDLR = HandlerReferenceBox
MINF = MediaInformationBox
STBL = SampleTableBox

# minf boxes
VMHD = VideoMediaHeaderBox
DINF = DataInformationBox

# stbl boxes
STSD = SampleDescriptionBox

# Root boxes
Parser.register_box(FTYP)
Parser.register_box(MOOV)

# moov boxes
Parser.register_box(MVHD)
Parser.register_box(TRAK)

# trak boxes
Parser.register_box(TKHD)
Parser.register_box(MDIA)

# mdia boxes
Parser.register_box(MDHD)
Parser.register_box(HDLR)
Parser.register_box(MINF)
Parser.register_box(STBL)

# minf boxes
Parser.register_box(VMHD)
Parser.register_box(DINF)

# stbl boxes
Parser.register_box(STSD)
