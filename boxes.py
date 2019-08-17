from abc import ABCMeta, abstractmethod

from headers import FullBoxHeader
from pybzparse import Parser

from fields_lists import *
from sub_fields_lists import ItemLocationSubFieldsList, ItemPropertyAssociationSubFieldsList


class MixinDictRepr(object):
    def __repr__(self, *args, **kwargs):
        return "{class_name} : {content!r} ".format(class_name=self.__class__.__name__,
                                                    content=self.__dict__)


class MixinMinimalRepr(object):
    """ A minimal representaion when the payload could be large """

    def __repr__(self, *args, **kwargs):
        return "{class_name} : {content!r} ".format(class_name=self.__class__.__name__,
                                                    content=self.__dict__.keys())


class AbstractBox(metaclass=ABCMeta):
    def __init__(self, header):
        self._header = header
        self._remaining_bytes = 0
        self._padding = None

    def __bytes__(self):
        return b''.join([bytes(self._header), self._get_content_bytes(), self.padding])

    @property
    def header(self):
        return self._header

    @header.setter
    def header(self, value):
        self._header = value

    @property
    def padding(self):
        return b'\0' * self._remaining_bytes if self._padding is None else \
            self._padding

    @padding.setter
    def padding(self, value):
        self._padding = value

    @abstractmethod
    def load(self, bstr):
        raise NotImplemented()

    def parse(self, bstr):
        self.parse_impl(bstr)
        self._remaining_bytes = self._header.start_pos + self._header.box_size - \
            bstr.bytepos
        if self._remaining_bytes != 0:
            self._padding = bstr.read(self._remaining_bytes * 8).bytes

    @abstractmethod
    def parse_impl(self, bstr):
        raise NotImplemented()

    @abstractmethod
    def _get_content_bytes(self):
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
        return super().parse_box(bstr, full_box_header)


class ContainerBox(AbstractBox, MixinDictRepr):
    def __init__(self, header):
        super().__init__(header)

        self._boxes_start_pos = None
        self._boxes = []

    @property
    def boxes(self):
        return self._boxes

    def load(self, bstr):
        for box in self._boxes:
            box.load(bstr)

    def parse(self, bstr):
        self.parse_impl(bstr)

    def parse_impl(self, bstr):
        self._boxes_start_pos = bstr.bytepos

    def parse_boxes(self, bstr, recursive=True):
        bstr.bytepos = self._boxes_start_pos
        self.parse_boxes_impl(bstr, recursive)
        # TODO: Validate in the specs if this check is needed
        self._remaining_bytes = self._header.start_pos + self._header.box_size - \
            bstr.bytepos
        if self._remaining_bytes != 0:
            self._padding = bstr.read(self._remaining_bytes * 8).bytes

    def parse_boxes_impl(self, bstr, recursive=True):
        self._boxes = []
        end_pos = self._header.start_pos + self._header.box_size
        box_iterator = Parser.parse(bstr, recursive=recursive)
        while bstr.bytepos < end_pos:
            self._boxes.append(next(box_iterator))

    def _get_content_bytes(self):
        return b''.join([bytes(box) for box in self._boxes])

    @classmethod
    def parse_box(cls, bstr, header):
        box = cls(header)
        box.parse(bstr)
        return box


class UnknownBox(AbstractBox, MixinDictRepr):
    type = b"____"

    def __init__(self, header):
        super().__init__(header)

        self._payload = b''

    @property
    def payload(self):
        return self._payload

    @payload.setter
    def payload(self, value):
        self._payload = value

    def load(self, bstr):
        bstr.bytepos = self._header.start_pos + self._header.header_size
        self._payload = bstr.read(self._header.content_size * 8).bytes

    def parse_impl(self, bstr):
        bstr.bytepos = self._header.start_pos + self._header.box_size

    def _get_content_bytes(self):
        return self._payload


class DataBox(AbstractBox, DataBoxFieldsList, MixinDictRepr):
    def __init__(self, header):
        DataBoxFieldsList.__init__(self)
        super().__init__(header)

    def load(self, bstr):
        bstr.bytepos = self._header.start_pos + self._header.header_size
        self.parse_fields(bstr, self._header)

    def parse_impl(self, bstr):
        bstr.bytepos = self._header.start_pos + self._header.box_size

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self)


# Root boxes
class FileTypeBox(AbstractBox, FileTypeBoxFieldsList, MixinDictRepr):
    type = b"ftyp"

    def __init__(self, header):
        FileTypeBoxFieldsList.__init__(self)
        super().__init__(header)

    def load(self, bstr):
        pass

    def parse_impl(self, bstr):
        self.parse_fields(bstr, self._header)

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self)


class MediaDataBox(DataBox):
    type = b"mdat"


class MovieBox(ContainerBox, MixinDictRepr):
    type = b"moov"


class MetaBox(ContainerBox, MixinDictRepr):
    type = b"meta"

    @classmethod
    def parse_box(cls, bstr, header):
        full_box_header = FullBoxHeader()
        full_box_header.extend_header(bstr, header)
        del header
        return super().parse_box(bstr, full_box_header)


# moov boxes
class MovieHeaderBox(AbstractFullBox, MovieHeaderBoxFieldsList, MixinDictRepr):
    type = b"mvhd"

    def __init__(self, header):
        MovieHeaderBoxFieldsList.__init__(self)
        super().__init__(header)

    def load(self, bstr):
        pass

    def parse_impl(self, bstr):
        self.parse_fields(bstr, self._header)

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self)


class TrackBox(ContainerBox, MixinDictRepr):
    type = b"trak"


# trak boxes
class TrackHeaderBox(AbstractFullBox, TrackHeaderBoxFieldsList, MixinDictRepr):
    type = b"tkhd"

    def __init__(self, header):
        TrackHeaderBoxFieldsList.__init__(self)
        super().__init__(header)

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

    def parse_impl(self, bstr):
        self.parse_fields(bstr, self._header)

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self)


class MediaBox(ContainerBox, MixinDictRepr):
    type = b"mdia"


# mdia boxes
class MediaHeaderBox(AbstractFullBox, MediaHeaderBoxFieldsList, MixinDictRepr):
    type = b"mdhd"

    def __init__(self, header):
        MediaHeaderBoxFieldsList.__init__(self)
        super().__init__(header)

    def load(self, bstr):
        pass

    def parse_impl(self, bstr):
        self.parse_fields(bstr, self._header)

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self)


class HandlerReferenceBox(AbstractFullBox, HandlerReferenceBoxFieldsList, MixinDictRepr):
    type = b"hdlr"

    def __init__(self, header):
        HandlerReferenceBoxFieldsList.__init__(self)
        super().__init__(header)

    def load(self, bstr):
        pass

    def parse_impl(self, bstr):
        self.parse_fields(bstr, self._header)

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self)


class MediaInformationBox(ContainerBox, MixinDictRepr):
    type = b"minf"


class SampleTableBox(ContainerBox, MixinDictRepr):
    type = b"stbl"


# minf boxes
class VideoMediaHeaderBox(AbstractFullBox, VideoMediaHeaderBoxFieldsList, MixinDictRepr):
    type = b"vmhd"

    def __init__(self, header):
        VideoMediaHeaderBoxFieldsList.__init__(self)
        super().__init__(header)

    def load(self, bstr):
        pass

    def parse_impl(self, bstr):
        self.parse_fields(bstr, self._header)

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self)


class DataInformationBox(ContainerBox, MixinDictRepr):
    type = b"dinf"


# stbl boxes
class SampleDescriptionBox(ContainerBox, SampleDescriptionBoxFieldsList, MixinDictRepr):
    type = b"stsd"

    def __init__(self, header):
        SampleDescriptionBoxFieldsList.__init__(self)
        super().__init__(header)

    def parse_impl(self, bstr):
        self.parse_fields(bstr, self._header)
        self._boxes_start_pos = bstr.bytepos

    def parse_boxes_impl(self, bstr, recursive=True):
        self._boxes = []
        box_iterator = Parser.parse(bstr, recursive=recursive)
        for i in range(self._entry_count.value):
            self._boxes.append(next(box_iterator))

    def refresh_boxes_size(self):
        boxes_size = 0
        for box in self._boxes:
            boxes_size += box.refresh_box_size()

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self) + \
               b''.join([bytes(box) for box in self._boxes])

    @classmethod
    def parse_box(cls, bstr, header):
        full_box_header = FullBoxHeader()
        full_box_header.extend_header(bstr, header)
        del header
        return super().parse_box(bstr, full_box_header)


# dinf boxes
class DataReferenceBox(ContainerBox, DataReferenceBoxFieldsList, MixinDictRepr):
    type = b"dref"

    def __init__(self, header):
        DataReferenceBoxFieldsList.__init__(self)
        super().__init__(header)

    def parse_impl(self, bstr):
        self.parse_fields(bstr, self._header)
        self._boxes_start_pos = bstr.bytepos

    def parse_boxes_impl(self, bstr, recursive=True):
        self._boxes = []
        box_iterator = Parser.parse(bstr, recursive=recursive)
        for i in range(self._entry_count.value):
            self._boxes.append(next(box_iterator))

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self) + \
               b''.join([bytes(box) for box in self._boxes])

    @classmethod
    def parse_box(cls, bstr, header):
        full_box_header = FullBoxHeader()
        full_box_header.extend_header(bstr, header)
        del header
        return super().parse_box(bstr, full_box_header)


class PrimaryItemBox(AbstractFullBox, PrimaryItemBoxFieldsList, MixinDictRepr):
    type = b"pitm"

    def __init__(self, header):
        PrimaryItemBoxFieldsList.__init__(self)
        super().__init__(header)

    def load(self, bstr):
        pass

    def parse_impl(self, bstr):
        self.parse_fields(bstr, self._header)

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self)


class ItemInformationBox(ContainerBox, ItemInformationBoxFieldsList, MixinDictRepr):
    type = b"iinf"

    def __init__(self, header):
        ItemInformationBoxFieldsList.__init__(self)
        super().__init__(header)

    def parse_impl(self, bstr):
        self.parse_fields(bstr, self._header)
        self._boxes_start_pos = bstr.bytepos

    def parse_boxes_impl(self, bstr, recursive=True):
        self._boxes = []
        box_iterator = Parser.parse(bstr, recursive=recursive)
        for i in range(self._entry_count.value):
            self._boxes.append(next(box_iterator))

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self) + \
               b''.join([bytes(box) for box in self._boxes])

    @classmethod
    def parse_box(cls, bstr, header):
        full_box_header = FullBoxHeader()
        full_box_header.extend_header(bstr, header)
        del header
        return super().parse_box(bstr, full_box_header)


# dref boxes
class DataEntryUrlBox(AbstractFullBox, DataEntryUrlBoxFieldsList, MixinDictRepr):
    type = b"url "

    def __init__(self, header):
        DataEntryUrlBoxFieldsList.__init__(self)
        super().__init__(header)

    def load(self, bstr):
        pass

    def parse_impl(self, bstr):
        self.parse_fields(bstr, self._header)

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self)


class DataEntryUrnBox(AbstractFullBox, DataEntryUrnBoxFieldsList, MixinDictRepr):
    type = b"urn "

    def __init__(self, header):
        DataEntryUrnBoxFieldsList.__init__(self)
        super().__init__(header)

    def load(self, bstr):
        pass

    def parse_impl(self, bstr):
        self.parse_fields(bstr, self._header)

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self)


# iinf boxes
class ItemInfoEntryBox(ContainerBox, ItemInfoEntryBoxFieldsList, MixinDictRepr):
    type = b"infe"

    def __init__(self, header):
        ItemInfoEntryBoxFieldsList.__init__(self)
        super().__init__(header)

    def parse_impl(self, bstr):
        self.parse_fields(bstr, self._header)
        self._boxes_start_pos = bstr.bytepos

    def parse_boxes_impl(self, bstr, recursive=True):
        self._boxes = []
        if self._extension_type.value:
            bstr.bytepos = self._boxes_start_pos
            self._boxes.append(next(Parser.parse(bstr, recursive=recursive)))

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self) + \
               b''.join([bytes(box) for box in self._boxes])

    @classmethod
    def parse_box(cls, bstr, header):
        full_box_header = FullBoxHeader()
        full_box_header.extend_header(bstr, header)
        del header
        return super().parse_box(bstr, full_box_header)


# meta boxes
class ItemReferenceBox(ContainerBox, MixinDictRepr):
    type = b"iref"

    def parse_boxes_impl(self, bstr, recursive=True):
        self._boxes = []
        end_pos = self._header.start_pos + self._header.box_size

        item_reference_box_cls = None
        if self._header.version == 0:
            item_reference_box_cls = SingleItemTypeReferenceBox
        elif self._header.version == 1:
            item_reference_box_cls = SingleItemTypeReferenceBoxLarge

        while bstr.bytepos < end_pos:
            header = Parser.parse_header(bstr)
            self._boxes.append(Parser.parse_box(bstr, header,
                                                item_reference_box_cls,
                                                recursive))

    @classmethod
    def parse_box(cls, bstr, header):
        full_box_header = FullBoxHeader()
        full_box_header.extend_header(bstr, header)
        del header
        return super().parse_box(bstr, full_box_header)


class ItemPropertiesBox(ContainerBox, MixinDictRepr):
    type = b"iprp"


class ItemDataBox(DataBox):
    type = b"idat"


class ItemLocationBox(AbstractFullBox, ItemLocationSubFieldsList, MixinDictRepr):
    type = b"iloc"

    def __init__(self, header):
        ItemLocationSubFieldsList.__init__(self)
        super().__init__(header)

    def load(self, bstr):
        self.load_sub_fields(bstr, self._header)

        self._remaining_bytes = self._header.start_pos + self._header.box_size - \
                                bstr.bytepos
        if self._remaining_bytes != 0:
            self._padding = bstr.read(self._remaining_bytes * 8).bytes

    def parse_impl(self, bstr):
        self.parse_fields(bstr, self._header)
        bstr.bytepos = self._header.start_pos + self._header.box_size

    def _get_content_bytes(self):
        return ItemLocationSubFieldsList.__bytes__(self)


# iref boxes
class SingleItemTypeReferenceBox(AbstractBox, SingleItemTypeReferenceBoxFieldsList,
                                 MixinDictRepr):
    type = b""

    def __init__(self, header):
        SingleItemTypeReferenceBoxFieldsList.__init__(self)
        super().__init__(header)

    def load(self, bstr):
        pass

    def parse_impl(self, bstr):
        self.parse_fields(bstr, self._header)

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self)


class SingleItemTypeReferenceBoxLarge(AbstractBox, SingleItemTypeReferenceBoxLargeFieldsList,
                                      MixinDictRepr):
    type = b""

    def __init__(self, header):
        SingleItemTypeReferenceBoxLargeFieldsList.__init__(self)
        super().__init__(header)

    def load(self, bstr):
        pass

    def parse_impl(self, bstr):
        self.parse_fields(bstr, self._header)

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self)


# iprp boxes
class ItemPropertyContainerBox(ContainerBox, MixinDictRepr):
    type = b"ipco"


class ItemPropertyAssociationBox(AbstractFullBox, ItemPropertyAssociationSubFieldsList,
                                 MixinDictRepr):
    type = b"ipma"

    def __init__(self, header):
        ItemPropertyAssociationSubFieldsList.__init__(self)
        super().__init__(header)

    def load(self, bstr):
        self.load_sub_fields(bstr, self._header)

        self._remaining_bytes = self._header.start_pos + self._header.box_size - \
                                bstr.bytepos
        if self._remaining_bytes != 0:
            self._padding = bstr.read(self._remaining_bytes * 8).bytes

    def parse_impl(self, bstr):
        self.parse_fields(bstr, self._header)
        bstr.bytepos = self._header.start_pos + self._header.box_size

    def _get_content_bytes(self):
        return ItemPropertyAssociationSubFieldsList.__bytes__(self)


# Root boxes
FTYP = FileTypeBox
MDAT = MediaDataBox
MOOV = MovieBox
META = MetaBox

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

# dinf boxes
DREF = DataReferenceBox
PITM = PrimaryItemBox
IINF = ItemInformationBox

# dref boxes
URL_ = DataEntryUrlBox
URN_ = DataEntryUrnBox

# iinf boxes
INFE = ItemInfoEntryBox

# meta boxes
IREF = ItemReferenceBox
IPRP = ItemPropertiesBox
IDAT = ItemDataBox
ILOC = ItemLocationBox

# iprp boxes
IPCO = ItemPropertyContainerBox
IPMA = ItemPropertyAssociationBox


# Register boxes
Parser.register_container_box(ContainerBox)
Parser.register_default_box(UnknownBox)

# Root boxes
Parser.register_box(FTYP)
Parser.register_box(MDAT)
Parser.register_box(MOOV)
Parser.register_box(META)

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

# dinf boxes
Parser.register_box(DREF)
Parser.register_box(PITM)
Parser.register_box(IINF)

# dref boxes
Parser.register_box(URL_)
Parser.register_box(URN_)

# iinf boxes
Parser.register_box(INFE)

# meta boxes
Parser.register_box(IREF)
Parser.register_box(IPRP)
Parser.register_box(IDAT)
Parser.register_box(ILOC)

# iprp boxes
Parser.register_box(IPCO)
Parser.register_box(IPMA)
