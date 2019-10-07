from abc import ABCMeta, abstractmethod

from headers import FullBoxHeader
from pybzparse import Parser

from fields_lists import *
from sub_fields_lists import EditListSubFieldsList, \
    TimeToSampleSubFieldsList, \
    CompositionOffsetSubFieldsList, \
    SampleSizeSubFieldsList, \
    SampleToChunkSubFieldsList, \
    ChunkOffsetSubFieldsList, \
    ItemLocationSubFieldsList, \
    ItemPropertyAssociationSubFieldsList


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

    def refresh_box_size(self):
        # TODO: this could be optimized if needed
        content_size = len(self._get_content_bytes())
        padding_size = len(self.padding)
        box_size = len(bytes(self._header)) + content_size + padding_size
        if self._header.box_size != box_size:
            self._header.update_box_size(content_size + padding_size)

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

    def append(self, box):
        self._boxes.append(box)

    def clear(self):
        del self._boxes[:]

    def pop(self):
        return self._boxes.pop()

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

    def refresh_box_size(self):
        self.refresh_boxes_size()
        boxes_size = 0
        for box in self._boxes:
            boxes_size += box.header.box_size
        padding_size = len(self.padding)
        box_size = len(bytes(self._header)) + boxes_size + padding_size
        if self._header.box_size != box_size:
            self._header.update_box_size(boxes_size + padding_size)

    def refresh_boxes_size(self):
        for box in self._boxes:
            box.refresh_box_size()

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
        super().__init__(header)
        DataBoxFieldsList.__init__(self)

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
        super().__init__(header)
        FileTypeBoxFieldsList.__init__(self)

    def load(self, bstr):
        pass

    def parse_impl(self, bstr):
        self.parse_fields(bstr, self._header)

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self)


class MediaDataBox(DataBox):
    type = b"mdat"


class MovieBox(ContainerBox, MixinDictRepr):
    # TODO: auto-increment the next_track_id of mvhd when a track is appended

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
    # TODO: auto-increment next_track_id when a track is appended to the moov

    type = b"mvhd"

    def __init__(self, header):
        super().__init__(header)
        MovieHeaderBoxFieldsList.__init__(self)

    def load(self, bstr):
        pass

    def parse_impl(self, bstr):
        self.parse_fields(bstr, self._header)

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self)


class TrackBox(ContainerBox, MixinDictRepr):
    type = b"trak"


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
        super().__init__(header)
        ItemLocationSubFieldsList.__init__(self)

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


# trak boxes
class TrackHeaderBox(AbstractFullBox, TrackHeaderBoxFieldsList, MixinDictRepr):
    type = b"tkhd"

    def __init__(self, header):
        super().__init__(header)
        TrackHeaderBoxFieldsList.__init__(self)

    @property
    def width(self):
        return self._width.value[0]

    @width.setter
    def width(self, value):
        self._set_field(self._width, *value)

    @property
    def height(self):
        return self._height.value[0]

    @height.setter
    def height(self, value):
        self._set_field(self._height, *value)

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


class EditBox(ContainerBox, MixinDictRepr):
    type = b"edts"


# iref boxes
class SingleItemTypeReferenceBox(AbstractBox, SingleItemTypeReferenceBoxFieldsList,
                                 MixinDictRepr):
    type = b""

    def __init__(self, header):
        super().__init__(header)
        SingleItemTypeReferenceBoxFieldsList.__init__(self)

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
        super().__init__(header)
        SingleItemTypeReferenceBoxLargeFieldsList.__init__(self)

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
        super().__init__(header)
        ItemPropertyAssociationSubFieldsList.__init__(self)

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


# mdia boxes
class MediaHeaderBox(AbstractFullBox, MediaHeaderBoxFieldsList, MixinDictRepr):
    type = b"mdhd"

    def __init__(self, header):
        super().__init__(header)
        MediaHeaderBoxFieldsList.__init__(self)

    def load(self, bstr):
        pass

    def parse_impl(self, bstr):
        self.parse_fields(bstr, self._header)

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self)


class HandlerReferenceBox(AbstractFullBox, HandlerReferenceBoxFieldsList, MixinDictRepr):
    type = b"hdlr"

    def __init__(self, header):
        super().__init__(header)
        HandlerReferenceBoxFieldsList.__init__(self)

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


# edts boxes
class EditListBox(AbstractFullBox, EditListSubFieldsList, MixinDictRepr):
    type = b"elst"

    def __init__(self, header):
        super().__init__(header)
        EditListSubFieldsList.__init__(self)

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
        return EditListSubFieldsList.__bytes__(self)


# minf boxes
class VideoMediaHeaderBox(AbstractFullBox, VideoMediaHeaderBoxFieldsList, MixinDictRepr):
    type = b"vmhd"

    def __init__(self, header):
        super().__init__(header)
        VideoMediaHeaderBoxFieldsList.__init__(self)

    def load(self, bstr):
        pass

    def parse_impl(self, bstr):
        self.parse_fields(bstr, self._header)

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self)


class NullMediaHeaderBox(AbstractFullBox, MixinDictRepr):
    type = b"nmhd"

    def load(self, bstr):
        pass

    def parse_impl(self, bstr):
        pass

    def _get_content_bytes(self):
        return b''


class SubtitleMediaHeaderBox(AbstractFullBox, MixinDictRepr):
    type = b"sthd"

    def load(self, bstr):
        pass

    def parse_impl(self, bstr):
        pass

    def _get_content_bytes(self):
        return b''


class DataInformationBox(ContainerBox, MixinDictRepr):
    type = b"dinf"


# stbl boxes
class SampleDescriptionBox(ContainerBox, SampleDescriptionBoxFieldsList, MixinDictRepr):
    type = b"stsd"

    def __init__(self, header):
        super().__init__(header)
        SampleDescriptionBoxFieldsList.__init__(self)

    def append(self, box):
        super().append(box)
        self._entry_count.value += 1

    def clear(self):
        super().clear()
        self._entry_count.value = 0

    def pop(self):
        box = super().pop()
        self._entry_count.value -= 1
        return box

    def parse_impl(self, bstr):
        self.parse_fields(bstr, self._header)
        self._boxes_start_pos = bstr.bytepos

    def parse_boxes_impl(self, bstr, recursive=True):
        self._boxes = []
        box_iterator = Parser.parse(bstr, recursive=recursive)
        for i in range(self._entry_count.value):
            self._boxes.append(next(box_iterator))

    def refresh_box_size(self):
        self.refresh_boxes_size()
        boxes_size = 0
        for box in self._boxes:
            boxes_size += box.header.box_size
        fields_size = len(AbstractFieldsList.__bytes__(self))
        padding_size = len(self.padding)
        box_size = len(bytes(self._header)) + fields_size + boxes_size + padding_size
        if self._header.box_size != box_size:
            self._header.update_box_size(fields_size + boxes_size + padding_size)

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self) + \
               b''.join([bytes(box) for box in self._boxes])

    @classmethod
    def parse_box(cls, bstr, header):
        full_box_header = FullBoxHeader()
        full_box_header.extend_header(bstr, header)
        del header
        return super().parse_box(bstr, full_box_header)


class TimeToSampleBox(AbstractFullBox, TimeToSampleSubFieldsList,
                      MixinDictRepr):
    type = b"stts"

    def __init__(self, header):
        super().__init__(header)
        TimeToSampleSubFieldsList.__init__(self)

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
        return TimeToSampleSubFieldsList.__bytes__(self)


class CompositionOffsetBox(AbstractFullBox, CompositionOffsetSubFieldsList,
                           MixinDictRepr):
    type = b"ctts"

    def __init__(self, header):
        super().__init__(header)
        CompositionOffsetSubFieldsList.__init__(self)

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
        return CompositionOffsetSubFieldsList.__bytes__(self)


class SampleSizeBox(AbstractFullBox, SampleSizeSubFieldsList, MixinDictRepr):
    type = b"stsz"

    def __init__(self, header):
        super().__init__(header)
        SampleSizeSubFieldsList.__init__(self)

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
        return SampleSizeSubFieldsList.__bytes__(self)


class SampleToChunkBox(AbstractFullBox, SampleToChunkSubFieldsList,
                       MixinDictRepr):
    type = b"stsc"

    def __init__(self, header):
        super().__init__(header)
        SampleToChunkSubFieldsList.__init__(self)

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
        return SampleToChunkSubFieldsList.__bytes__(self)


class ChunkOffsetBox(AbstractFullBox, ChunkOffsetSubFieldsList, MixinDictRepr):
    type = b"stco"

    def __init__(self, header):
        super().__init__(header)
        ChunkOffsetSubFieldsList.__init__(self)

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
        return ChunkOffsetSubFieldsList.__bytes__(self)


# dinf boxes
class DataReferenceBox(ContainerBox, DataReferenceBoxFieldsList, MixinDictRepr):
    type = b"dref"

    def __init__(self, header):
        super().__init__(header)
        DataReferenceBoxFieldsList.__init__(self)

    def append(self, box):
        super().append(box)
        self._entry_count.value += 1

    def clear(self):
        super().clear()
        self._entry_count.value = 0

    def pop(self):
        box = super().pop()
        self._entry_count.value -= 1
        return box

    def parse_impl(self, bstr):
        self.parse_fields(bstr, self._header)
        self._boxes_start_pos = bstr.bytepos

    def parse_boxes_impl(self, bstr, recursive=True):
        self._boxes = []
        box_iterator = Parser.parse(bstr, recursive=recursive)
        for i in range(self._entry_count.value):
            self._boxes.append(next(box_iterator))

    def refresh_box_size(self):
        self.refresh_boxes_size()
        boxes_size = 0
        for box in self._boxes:
            boxes_size += box.header.box_size
        fields_size = len(AbstractFieldsList.__bytes__(self))
        padding_size = len(self.padding)
        box_size = len(bytes(self._header)) + fields_size + boxes_size + padding_size
        if self._header.box_size != box_size:
            self._header.update_box_size(fields_size + boxes_size + padding_size)

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
        super().__init__(header)
        PrimaryItemBoxFieldsList.__init__(self)

    def load(self, bstr):
        pass

    def parse_impl(self, bstr):
        self.parse_fields(bstr, self._header)

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self)


class ItemInformationBox(ContainerBox, ItemInformationBoxFieldsList, MixinDictRepr):
    type = b"iinf"

    def __init__(self, header):
        super().__init__(header)
        ItemInformationBoxFieldsList.__init__(self)

    def append(self, box):
        super().append(box)
        self._entry_count.value += 1

    def clear(self):
        super().clear()
        self._entry_count.value = 0

    def pop(self):
        box = super().pop()
        self._entry_count.value -= 1
        return box

    def parse_impl(self, bstr):
        self.parse_fields(bstr, self._header)
        self._boxes_start_pos = bstr.bytepos

    def parse_boxes_impl(self, bstr, recursive=True):
        self._boxes = []
        box_iterator = Parser.parse(bstr, recursive=recursive)
        for i in range(self._entry_count.value):
            self._boxes.append(next(box_iterator))

    def refresh_box_size(self):
        self.refresh_boxes_size()
        boxes_size = 0
        for box in self._boxes:
            boxes_size += box.header.box_size
        fields_size = len(AbstractFieldsList.__bytes__(self))
        padding_size = len(self.padding)
        box_size = len(bytes(self._header)) + fields_size + boxes_size + padding_size
        if self._header.box_size != box_size:
            self._header.update_box_size(fields_size + boxes_size + padding_size)

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self) + \
               b''.join([bytes(box) for box in self._boxes])

    @classmethod
    def parse_box(cls, bstr, header):
        full_box_header = FullBoxHeader()
        full_box_header.extend_header(bstr, header)
        del header
        return super().parse_box(bstr, full_box_header)


# stsd boxes
class SampleEntryBox(ContainerBox, SampleEntryBoxFieldsList, MixinDictRepr):
    type = b"____"

    def __init__(self, header):
        super().__init__(header)
        SampleEntryBoxFieldsList.__init__(self)

    def parse_impl(self, bstr):
        self.parse_fields(bstr, self._header)
        self._boxes_start_pos = bstr.bytepos

    def refresh_box_size(self):
        self.refresh_boxes_size()
        boxes_size = 0
        for box in self._boxes:
            boxes_size += box.header.box_size
        fields_size = len(AbstractFieldsList.__bytes__(self))
        padding_size = len(self.padding)
        box_size = len(bytes(self._header)) + fields_size + boxes_size + padding_size
        if self._header.box_size != box_size:
            self._header.update_box_size(fields_size + boxes_size + padding_size)

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self) + \
               b''.join([bytes(box) for box in self._boxes])


class VisualSampleEntryBox(SampleEntryBox, VisualSampleEntryBoxFieldsList):
    type = b"____"

    def __init__(self, header):
        super().__init__(header)
        VisualSampleEntryBoxFieldsList.__init__(self)

    def parse_impl(self, bstr):
        VisualSampleEntryBoxFieldsList.parse_fields(self, bstr, self._header)
        self._boxes_start_pos = bstr.bytepos

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self) + \
               b''.join([bytes(box) for box in self._boxes])


class AVC1SampleEntryBox(VisualSampleEntryBox):
    type = b"avc1"


class PlainTextSampleEntryBox(SampleEntryBox):
    type = b"____"


class SimpleTextSampleEntryBox(SampleEntryBox, SimpleTextSampleEntryBoxFieldsList):
    type = b"stxt"

    def __init__(self, header):
        super().__init__(header)
        SimpleTextSampleEntryBoxFieldsList.__init__(self)

    def parse_impl(self, bstr):
        SimpleTextSampleEntryBoxFieldsList.parse_fields(self, bstr, self._header)
        self._boxes_start_pos = bstr.bytepos

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self) + \
               b''.join([bytes(box) for box in self._boxes])


class MetaDataSampleEntry(SampleEntryBox):
    type = b"____"


class TextMetaDataSampleEntryBox(MetaDataSampleEntry, TextMetaDataSampleEntryBoxFieldsList):
    type = b"mett"

    def __init__(self, header):
        super().__init__(header)
        TextMetaDataSampleEntryBoxFieldsList.__init__(self)

    def parse_impl(self, bstr):
        TextMetaDataSampleEntryBoxFieldsList.parse_fields(self, bstr, self._header)
        self._boxes_start_pos = bstr.bytepos

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self) + \
               b''.join([bytes(box) for box in self._boxes])


class SubtitleSampleEntryBox(SampleEntryBox):
    type = b"____"


class TextSubtitleSampleEntryBox(MetaDataSampleEntry, TextSubtitleSampleEntryBoxFieldsList):
    type = b"sbtt"

    def __init__(self, header):
        super().__init__(header)
        TextSubtitleSampleEntryBoxFieldsList.__init__(self)

    def parse_impl(self, bstr):
        TextSubtitleSampleEntryBoxFieldsList.parse_fields(self, bstr, self._header)
        self._boxes_start_pos = bstr.bytepos

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self) + \
               b''.join([bytes(box) for box in self._boxes])


# dref boxes
class DataEntryUrlBox(AbstractFullBox, DataEntryUrlBoxFieldsList, MixinDictRepr):
    type = b"url "

    def __init__(self, header):
        super().__init__(header)
        DataEntryUrlBoxFieldsList.__init__(self)

    def load(self, bstr):
        pass

    def parse_impl(self, bstr):
        self.parse_fields(bstr, self._header)

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self)


class DataEntryUrnBox(AbstractFullBox, DataEntryUrnBoxFieldsList, MixinDictRepr):
    type = b"urn "

    def __init__(self, header):
        super().__init__(header)
        DataEntryUrnBoxFieldsList.__init__(self)

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
        super().__init__(header)
        ItemInfoEntryBoxFieldsList.__init__(self)

    def parse_impl(self, bstr):
        self.parse_fields(bstr, self._header)
        self._boxes_start_pos = bstr.bytepos

    def parse_boxes_impl(self, bstr, recursive=True):
        self._boxes = []
        if self._extension_type.value:
            bstr.bytepos = self._boxes_start_pos
            self._boxes.append(next(Parser.parse(bstr, recursive=recursive)))

    def refresh_box_size(self):
        self.refresh_boxes_size()
        boxes_size = 0
        for box in self._boxes:
            boxes_size += box.header.box_size
        fields_size = len(AbstractFieldsList.__bytes__(self))
        padding_size = len(self.padding)
        box_size = len(bytes(self._header)) + fields_size + boxes_size + padding_size
        if self._header.box_size != box_size:
            self._header.update_box_size(fields_size + boxes_size + padding_size)

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self) + \
               b''.join([bytes(box) for box in self._boxes])

    @classmethod
    def parse_box(cls, bstr, header):
        full_box_header = FullBoxHeader()
        full_box_header.extend_header(bstr, header)
        del header
        return super().parse_box(bstr, full_box_header)


# avc1 boxes
class PixelAspectRatioBox(AbstractBox, PixelAspectRatioBoxFieldsList):
    type = b"pasp"

    def __init__(self, header):
        super().__init__(header)
        PixelAspectRatioBoxFieldsList.__init__(self)

    def load(self, bstr):
        pass

    def parse_impl(self, bstr):
        self.parse_fields(bstr, self._header)

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self)


class CleanApertureBox(AbstractBox, CleanApertureBoxFieldsList):
    type = b"clap"

    def __init__(self, header):
        super().__init__(header)
        CleanApertureBoxFieldsList.__init__(self)

    def load(self, bstr):
        pass

    def parse_impl(self, bstr):
        self.parse_fields(bstr, self._header)

    def _get_content_bytes(self):
        return AbstractFieldsList.__bytes__(self)


# Root boxes
FTYP = FileTypeBox
MDAT = MediaDataBox
MOOV = MovieBox
META = MetaBox

# moov boxes
MVHD = MovieHeaderBox
TRAK = TrackBox

# meta boxes
IREF = ItemReferenceBox
IPRP = ItemPropertiesBox
IDAT = ItemDataBox
ILOC = ItemLocationBox

# trak boxes
TKHD = TrackHeaderBox
MDIA = MediaBox
EDTS = EditBox

# iprp boxes
IPCO = ItemPropertyContainerBox
IPMA = ItemPropertyAssociationBox

# mdia boxes
MDHD = MediaHeaderBox
HDLR = HandlerReferenceBox
MINF = MediaInformationBox
STBL = SampleTableBox

# edts boxes
ELST = EditListBox

# minf boxes
VMHD = VideoMediaHeaderBox
NMHD = NullMediaHeaderBox
STHD = SubtitleMediaHeaderBox
DINF = DataInformationBox

# stbl boxes
STSD = SampleDescriptionBox
STTS = TimeToSampleBox
CTTS = CompositionOffsetBox
STSZ = SampleSizeBox
STSC = SampleToChunkBox
STCO = ChunkOffsetBox

# dinf boxes
DREF = DataReferenceBox
PITM = PrimaryItemBox
IINF = ItemInformationBox

# stsd boxes
AVC1 = AVC1SampleEntryBox
STXT = SimpleTextSampleEntryBox
METT = TextMetaDataSampleEntryBox
SBTT = TextSubtitleSampleEntryBox

# dref boxes
URL_ = DataEntryUrlBox
URN_ = DataEntryUrnBox

# iinf boxes
INFE = ItemInfoEntryBox

# avc1 boxes
PASP = PixelAspectRatioBox
CLAP = CleanApertureBox


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

# meta boxes
Parser.register_box(IREF)
Parser.register_box(IPRP)
Parser.register_box(IDAT)
Parser.register_box(ILOC)

# trak boxes
Parser.register_box(TKHD)
Parser.register_box(MDIA)
Parser.register_box(EDTS)

# iprp boxes
Parser.register_box(IPCO)
Parser.register_box(IPMA)

# mdia boxes
Parser.register_box(MDHD)
Parser.register_box(HDLR)
Parser.register_box(MINF)
Parser.register_box(STBL)

# edts boxes
Parser.register_box(ELST)

# minf boxes
Parser.register_box(VMHD)
Parser.register_box(NMHD)
Parser.register_box(STHD)
Parser.register_box(DINF)

# stbl boxes
Parser.register_box(STSD)
Parser.register_box(STTS)
Parser.register_box(CTTS)
Parser.register_box(STSZ)
Parser.register_box(STSC)
Parser.register_box(STCO)

# dinf boxes
Parser.register_box(DREF)
Parser.register_box(PITM)
Parser.register_box(IINF)

# stsd boxes
Parser.register_box(AVC1)
Parser.register_box(STXT)
Parser.register_box(METT)
Parser.register_box(SBTT)

# dref boxes
Parser.register_box(URL_)
Parser.register_box(URN_)

# iinf boxes
Parser.register_box(INFE)

# avc1 boxes
Parser.register_box(PASP)
Parser.register_box(CLAP)
