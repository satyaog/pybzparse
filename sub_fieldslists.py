from abc import ABCMeta, abstractmethod

from fieldslists import *


class AbstractSubFieldsList(metaclass=ABCMeta):
    @abstractmethod
    def load_sub_fields(self, bstr, header):
        raise NotImplemented()


# iloc sub files lists
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


# ipma sub files lists
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

    def load_sub_fields(self, bstr, header):
        bstr.bytepos = self._associations_start_pos
        for i in range(self._association_count.value):
            association = ItemPropertyAssociationBoxEntryAssociationsFieldsList()
            association.parse_fields(bstr, header)
            self._associations.append(association)

    def parse_fields(self, bstr, header):
        super().parse_fields(bstr, header)
        self._associations_start_pos = bstr.bytepos
