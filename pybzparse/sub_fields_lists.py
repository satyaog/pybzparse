from abc import ABCMeta, abstractmethod

from pybzparse.fields_lists import *


class AbstractSubFieldsList(metaclass=ABCMeta):
    @abstractmethod
    def append_and_return(self):
        raise NotImplemented()

    @abstractmethod
    def clear(self):
        raise NotImplemented()

    @abstractmethod
    def pop(self):
        raise NotImplemented()

    @abstractmethod
    def load_sub_fields(self, bstr, header):
        raise NotImplemented()


# meta boxes
class ItemLocationSubFieldsList(AbstractSubFieldsList, ItemLocationBoxFieldsList):
    def __init__(self):
        super().__init__()

        self._items_start_pos = None
        self._items = []

    def __bytes__(self):
        return b''.join([ItemLocationBoxFieldsList.__bytes__(self)] +
                        [bytes(item) for item in self._items])

    @property
    def items(self):
        return self._items

    def append_and_return(self):
        item = ItemLocationItemSubFieldsList(self._index_size.value,
                                             self._offset_size.value,
                                             self._length_size.value,
                                             self._base_offset_size.value)
        self._items.append(item)
        self._item_count.value += 1
        return item

    def clear(self):
        del self._items[:]
        self._item_count.value = 0

    def pop(self):
        item = self._items.pop()
        self._item_count.value -= 1
        return item

    def load_sub_fields(self, bstr, header):
        bstr.bytepos = self._items_start_pos
        for i in range(self._item_count.value):
            item = ItemLocationItemSubFieldsList(self._index_size.value,
                                                 self._offset_size.value,
                                                 self._length_size.value,
                                                 self._base_offset_size.value)
            item.parse_fields(bstr, header)
            item.load_sub_fields(bstr, header)
            self._items.append(item)

    def parse_fields(self, bstr, header):
        super().parse_fields(bstr, header)
        self._items_start_pos = bstr.bytepos


class ItemLocationItemSubFieldsList(AbstractSubFieldsList,
                                    ItemLocationBoxItemFieldsList):
    def __init__(self, index_size, offset_size, length_size, base_offset_size):
        super().__init__(base_offset_size)

        self._index_size = 0 if index_size is None else index_size
        self._offset_size = offset_size
        self._length_size = length_size

        self._extents_start_pos = None
        self._extents = []

    def __bytes__(self):
        return b''.join([ItemLocationBoxItemFieldsList.__bytes__(self)] +
                        [bytes(extent) for extent in self._extents])

    @property
    def extents(self):
        return self._extents

    def append_and_return(self):
        extent = ItemLocationBoxItemExtentFieldsList(self._index_size,
                                                     self._offset_size,
                                                     self._length_size)
        self._extents.append(extent)
        self._extent_count.value += 1
        return extent

    def clear(self):
        del self._extents[:]
        self._extent_count.value = 0

    def pop(self):
        extent = self._extents.pop()
        self._extent_count.value -= 1
        return extent

    def load_sub_fields(self, bstr, header):
        bstr.bytepos = self._extents_start_pos
        for i in range(self._extent_count.value):
            extent = ItemLocationBoxItemExtentFieldsList(self._index_size,
                                                         self._offset_size,
                                                         self._length_size)
            extent.parse_fields(bstr, header)
            self._extents.append(extent)

    def parse_fields(self, bstr, header):
        super().parse_fields(bstr, header)
        self._extents_start_pos = bstr.bytepos


class ItemPropertyAssociationSubFieldsList(AbstractSubFieldsList,
                                           ItemPropertyAssociationBoxFieldsList):
    def __init__(self):
        super().__init__()

        self._entries_start_pos = None
        self._entries = []

    def __bytes__(self):
        return b''.join([ItemPropertyAssociationBoxFieldsList.__bytes__(self)] +
                        [bytes(entry) for entry in self._entries])

    @property
    def entries(self):
        return self._entries

    def append_and_return(self):
        entry = ItemPropertyAssociationEntrySubFieldsList()
        self._entries.append(entry)
        self._entry_count.value += 1
        return entry

    def clear(self):
        del self._entries[:]
        self._entry_count.value = 0

    def pop(self):
        entry = self._entries.pop()
        self._entry_count.value -= 1
        return entry

    def load_sub_fields(self, bstr, header):
        bstr.bytepos = self._entries_start_pos
        for i in range(self._entry_count.value):
            entry = ItemPropertyAssociationEntrySubFieldsList()
            entry.parse_fields(bstr, header)
            entry.load_sub_fields(bstr, header)
            self._entries.append(entry)

    def parse_fields(self, bstr, header):
        super().parse_fields(bstr, header)
        self._entries_start_pos = bstr.bytepos


class ItemPropertyAssociationEntrySubFieldsList(
      AbstractSubFieldsList, ItemPropertyAssociationBoxEntryFieldsList):
    def __init__(self):
        super().__init__()

        self._associations_start_pos = None
        self._associations = []

    def __bytes__(self):
        return b''.join([ItemPropertyAssociationBoxEntryFieldsList.__bytes__(self)] +
                        [bytes(association) for association in self._associations])

    @property
    def associations(self):
        return self._associations

    def append_and_return(self):
        entry = ItemPropertyAssociationBoxEntryAssociationsFieldsList()
        self._associations.append(entry)
        self._association_count.value += 1
        return entry

    def clear(self):
        del self._associations[:]
        self._association_count.value = 0

    def pop(self):
        entry = self._associations.pop()
        self._association_count.value -= 1
        return entry

    def load_sub_fields(self, bstr, header):
        bstr.bytepos = self._associations_start_pos
        for i in range(self._association_count.value):
            association = ItemPropertyAssociationBoxEntryAssociationsFieldsList()
            association.parse_fields(bstr, header)
            self._associations.append(association)

    def parse_fields(self, bstr, header):
        super().parse_fields(bstr, header)
        self._associations_start_pos = bstr.bytepos


# edts boxes
class EditListSubFieldsList(AbstractSubFieldsList, EditListBoxFieldsList):
    def __init__(self):
        super().__init__()

        self._entries_start_pos = None
        self._entries = []

    def __bytes__(self):
        return b''.join([EditListBoxFieldsList.__bytes__(self)] +
                        [bytes(sample) for sample in self._entries])

    @property
    def entries(self):
        return self._entries

    def append_and_return(self):
        entry = EditListBoxEntryFieldsList()
        self._entries.append(entry)
        self._entry_count.value += 1
        return entry

    def clear(self):
        del self._entries[:]
        self._entry_count.value = 0

    def pop(self):
        entry = self._entries.pop()
        self._entry_count.value -= 1
        return entry

    def load_sub_fields(self, bstr, header):
        bstr.bytepos = self._entries_start_pos
        for i in range(self._entry_count.value):
            entry = EditListBoxEntryFieldsList()
            entry.parse_fields(bstr, header)
            self._entries.append(entry)

    def parse_fields(self, bstr, header):
        super().parse_fields(bstr, header)
        self._entries_start_pos = bstr.bytepos


# stbl boxes
class TimeToSampleSubFieldsList(AbstractSubFieldsList,
                                TimeToSampleBoxFieldsList):
    def __init__(self):
        super().__init__()

        self._entries_start_pos = None
        self._entries = []

    def __bytes__(self):
        return b''.join([TimeToSampleBoxFieldsList.__bytes__(self)] +
                        [bytes(entry) for entry in self._entries])

    @property
    def entries(self):
        return self._entries

    def append_and_return(self):
        entry = TimeToSampleBoxEntryFieldsList()
        self._entries.append(entry)
        self._entry_count.value += 1
        return entry

    def clear(self):
        del self._entries[:]
        self._entry_count.value = 0

    def pop(self):
        entry = self._entries.pop()
        self._entry_count.value -= 1
        return entry

    def load_sub_fields(self, bstr, header):
        bstr.bytepos = self._entries_start_pos
        for i in range(self._entry_count.value):
            entry = TimeToSampleBoxEntryFieldsList()
            entry.parse_fields(bstr, header)
            self._entries.append(entry)

    def parse_fields(self, bstr, header):
        super().parse_fields(bstr, header)
        self._entries_start_pos = bstr.bytepos


class CompositionOffsetSubFieldsList(AbstractSubFieldsList,
                                     CompositionOffsetBoxFieldsList):
    def __init__(self):
        super().__init__()

        self._entries_start_pos = None
        self._entries = []

    def __bytes__(self):
        return b''.join([CompositionOffsetBoxFieldsList.__bytes__(self)] +
                        [bytes(entry) for entry in self._entries])

    @property
    def entries(self):
        return self._entries

    def append_and_return(self):
        entry = CompositionOffsetBoxEntryFieldsList()
        self._entries.append(entry)
        self._entry_count.value += 1
        return entry

    def clear(self):
        del self._entries[:]
        self._entry_count.value = 0

    def pop(self):
        entry = self._entries.pop()
        self._entry_count.value -= 1
        return entry

    def load_sub_fields(self, bstr, header):
        bstr.bytepos = self._entries_start_pos
        for i in range(self._entry_count.value):
            entry = CompositionOffsetBoxEntryFieldsList()
            entry.parse_fields(bstr, header)
            self._entries.append(entry)

    def parse_fields(self, bstr, header):
        super().parse_fields(bstr, header)
        self._entries_start_pos = bstr.bytepos


class SampleSizeSubFieldsList(AbstractSubFieldsList, SampleSizeBoxFieldsList):
    def __init__(self):
        super().__init__()

        self._samples_start_pos = None
        self._samples = []

    def __bytes__(self):
        return b''.join([SampleSizeBoxFieldsList.__bytes__(self)] +
                        [bytes(sample) for sample in self._samples])

    @property
    def samples(self):
        return self._samples

    def append_and_return(self):
        sample = SampleSizeBoxSampleFieldsList()
        self._samples.append(sample)
        self._sample_count.value += 1
        return sample

    def clear(self):
        del self._samples[:]
        self._sample_count.value = 0

    def pop(self):
        entry = self._samples.pop()
        self._sample_count.value -= 1
        return entry

    def load_sub_fields(self, bstr, header):
        bstr.bytepos = self._samples_start_pos
        # if a constant size is used, there's no array
        if self._sample_size.value != 0:
            return
        for i in range(self._sample_count.value):
            sample = SampleSizeBoxSampleFieldsList()
            sample.parse_fields(bstr, header)
            self._samples.append(sample)

    def parse_fields(self, bstr, header):
        super().parse_fields(bstr, header)
        self._samples_start_pos = bstr.bytepos


class SampleToChunkSubFieldsList(AbstractSubFieldsList,
                                 SampleToChunkBoxFieldsList):
    def __init__(self):
        super().__init__()

        self._entries_start_pos = None
        self._entries = []

    def __bytes__(self):
        return b''.join([SampleToChunkBoxFieldsList.__bytes__(self)] +
                        [bytes(entry) for entry in self._entries])

    @property
    def entries(self):
        return self._entries

    def append_and_return(self):
        entry = SampleToChunkBoxEntryFieldsList()
        self._entries.append(entry)
        self._entry_count.value += 1
        return entry

    def clear(self):
        del self._entries[:]
        self._entry_count.value = 0

    def pop(self):
        entry = self._entries.pop()
        self._entry_count.value -= 1
        return entry

    def load_sub_fields(self, bstr, header):
        bstr.bytepos = self._entries_start_pos
        for i in range(self._entry_count.value):
            entry = SampleToChunkBoxEntryFieldsList()
            entry.parse_fields(bstr, header)
            self._entries.append(entry)

    def parse_fields(self, bstr, header):
        super().parse_fields(bstr, header)
        self._entries_start_pos = bstr.bytepos


class ChunkOffsetSubFieldsList(AbstractSubFieldsList, ChunkOffsetBoxFieldsList):
    def __init__(self):
        super().__init__()

        self._entries_start_pos = None
        self._entries = []

    def __bytes__(self):
        return b''.join([ChunkOffsetBoxFieldsList.__bytes__(self)] +
                        [bytes(sample) for sample in self._entries])

    @property
    def entries(self):
        return self._entries

    def append_and_return(self):
        entry = ChunkOffsetBoxEntryFieldsList()
        self._entries.append(entry)
        self._entry_count.value += 1
        return entry

    def clear(self):
        del self._entries[:]
        self._entry_count.value = 0

    def pop(self):
        entry = self._entries.pop()
        self._entry_count.value -= 1
        return entry

    def load_sub_fields(self, bstr, header):
        bstr.bytepos = self._entries_start_pos
        for i in range(self._entry_count.value):
            entry = ChunkOffsetBoxEntryFieldsList()
            entry.parse_fields(bstr, header)
            self._entries.append(entry)

    def parse_fields(self, bstr, header):
        super().parse_fields(bstr, header)
        self._entries_start_pos = bstr.bytepos


class ChunkOffset64SubFieldsList(ChunkOffsetSubFieldsList):
    def append_and_return(self):
        entry = ChunkOffset64BoxEntryFieldsList()
        self._entries.append(entry)
        self._entry_count.value += 1
        return entry

    def load_sub_fields(self, bstr, header):
        bstr.bytepos = self._entries_start_pos
        for i in range(self._entry_count.value):
            entry = ChunkOffset64BoxEntryFieldsList()
            entry.parse_fields(bstr, header)
            self._entries.append(entry)
