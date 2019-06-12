""" Benzina MP4 Parser based on https://github.com/use-sparingly/pymp4parse """

from abc import ABCMeta, abstractmethod
import bitstring
from datetime import datetime
from collections import namedtuple
import logging

log = logging.getLogger(__name__)
log.setLevel(logging.WARN)


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
    def __init__(self):
        self.header = None

    @staticmethod
    @abstractmethod
    def parse(bs, header):
        raise NotImplemented()


class AbstractTable(metaclass=ABCMeta):
    @staticmethod
    @abstractmethod
    def parse(bs):
        raise NotImplemented()


# class FragmentRunTableBox(AbstractBox, MixinDictRepr):
#     pass


class UnknownBox(AbstractBox, MixinDictRepr):
    type = "unkn"

    @staticmethod
    def parse(bs, header):
        unkown = UnknownBox()
        unkown.header = header

        bs.bytepos += header.box_size

        return unkown


class MovieFragmentBox(AbstractBox, MixinDictRepr):
    type = "moof"

    @staticmethod
    def parse(bootstrap_bs, header):
        moof = MovieFragmentBox()
        moof.header = header

        box_bs = bootstrap_bs.read(moof.header.box_size * 8)

        for child_box in Parser.parse(bytes_input=box_bs.bytes):
            setattr(moof, child_box.type, child_box)

        return moof


class BootStrapInfoBox(AbstractBox, MixinDictRepr):
    type = "abst"

    def __init__(self):
        super(BootStrapInfoBox, self).__init__()
        self.version = None
        self.profile_raw = None
        self.live = None
        self.update = None
        self.time_scale = None
        self.current_media_time = None
        self.smpte_timecode_offset = None
        self.movie_identifier = None
        self.server_entry_table = None
        self.quality_entry_table = None
        self.drm_data = None
        self.meta_data = None
        self.segment_run_tables = None
        self.fragment_tables = None
        self._current_media_time = None

    @property
    def current_media_time(self):
        return self._current_media_time

    @current_media_time.setter
    def current_media_time(self, epoch_timestamp):
        """ Takes a timestamp arg and saves it as datetime """
        self._current_media_time = \
            datetime.utcfromtimestamp(epoch_timestamp / float(self.time_scale))

    @staticmethod
    def parse(bootstrap_bs, header):
        abst = BootStrapInfoBox()
        abst.header = header

        box_bs = bootstrap_bs.read(abst.header.box_size * 8)

        abst.version, abst.profile_raw, abst.live, abst.update, \
            abst.time_scale, abst.current_media_time, abst.smpte_timecode_offset = \
            box_bs.readlist("""pad:8, pad:24,
                               uintbe:32, uintbe:2, bool, bool,
                               pad:4,
                               uintbe:32, uintbe:64, uintbe:64""")
        abst.movie_identifier = Parser.read_string(box_bs)

        abst.server_entry_table = Parser.read_count_and_string_table(box_bs)
        abst.quality_entry_table = Parser.read_count_and_string_table(box_bs)

        abst.drm_data = Parser.read_string(box_bs)
        abst.meta_data = Parser.read_string(box_bs)

        abst.segment_run_tables = []

        segment_count = box_bs.read("uintbe:8")
        log.debug("segment_count: %d" % segment_count)
        for _ in range(0, segment_count):
            abst.segment_run_tables.append(SegmentRunTable.parse(box_bs))

        abst.fragment_tables = []
        fragment_count = box_bs.read("uintbe:8")
        log.debug("fragment_count: %d" % fragment_count)
        for _ in range(0, fragment_count):
            abst.fragment_tables.append(FragmentRunTable.parse(box_bs))

        log.debug("Finished parsing abst")

        return abst


class FragmentRandomAccessBox(AbstractBox, MixinDictRepr):
    """ aka afra """
    type = "afra"

    BoxEntry = namedtuple("FragmentRandomAccessBoxEntry", ["time", "offset"])
    BoxGlobalEntry = namedtuple("FragmentRandomAccessBoxGlobalEntry",
                                ["time", "segment_number", "fragment_number",
                                 "afra_offset", "sample_offset"])

    def __init__(self):
        super(FragmentRandomAccessBox, self).__init__()
        self.time_scale = None
        self.local_access_entries = None
        self.global_access_entries = None

    @staticmethod
    def parse(bs, header):
        afra = FragmentRandomAccessBox()
        afra.header = header

        # read the entire box in case there's padding
        afra_bs = bs.read(header.box_size * 8)
        # skip Version and Flags
        afra_bs.pos += 8 + 24
        long_ids, long_offsets, global_entries, afra.time_scale, local_entry_count = \
            afra_bs.readlist("bool, bool, bool, pad:5, uintbe:32, uintbe:32")

        if long_ids:
            id_bs_type = "uintbe:32"
        else:
            id_bs_type = "uintbe:16"

        if long_offsets:
            offset_bs_type = "uintbe:64"
        else:
            offset_bs_type = "uintbe:32"

        log.debug("local_access_entries entry count: %s", local_entry_count)
        afra.local_access_entries = []
        for _ in range(0, local_entry_count):
            time = Parser.parse_time_field(afra_bs, afra.time_scale)

            offset = afra_bs.read(offset_bs_type)

            afra_entry = FragmentRandomAccessBox.BoxEntry(time=time,
                                                          offset=offset)
            afra.local_access_entries.append(afra_entry)

        afra.global_access_entries = []

        if global_entries:
            global_entry_count = afra_bs.read("uintbe:32")

            log.debug("global_access_entries entry count: %s", global_entry_count)

            for _ in range(0, global_entry_count):
                time = Parser.parse_time_field(afra_bs, afra.time_scale)

                segment_number = afra_bs.read(id_bs_type)
                fragment_number = afra_bs.read(id_bs_type)

                afra_offset = afra_bs.read(offset_bs_type)
                sample_offset = afra_bs.read(offset_bs_type)

                afra_global_entry = \
                    FragmentRandomAccessBox.BoxGlobalEntry(
                        time=time,
                        segment_number=segment_number,
                        fragment_number=fragment_number,
                        afra_offset=afra_offset,
                        sample_offset=sample_offset)

                afra.global_access_entries.append(afra_global_entry)

        return afra


class SegmentRunTable(AbstractTable, MixinDictRepr):
    type = "asrt"

    TableEntry = namedtuple("SegmentRunTableEntry", ["first_segment",
                                                     "fragments_per_segment"])

    def __init__(self):
        super(SegmentRunTable, self).__init__()
        self.update = None
        self.quality_segment_url_modifiers = None
        self.segment_run_table_entries = None

    @staticmethod
    def parse(box_bs):
        """ Parse asrt / Segment Run Table Box """

        asrt = SegmentRunTable()
        asrt.header = Parser.read_box_header(box_bs)
        # read the entire box in case there's padding
        asrt_bs_box = box_bs.read(asrt.header.box_size * 8)

        asrt_bs_box.pos += 8
        update_flag = asrt_bs_box.read("uintbe:24")
        asrt.update = True if update_flag == 1 else False

        asrt.quality_segment_url_modifiers = Parser.read_count_and_string_table(asrt_bs_box)

        asrt.segment_run_table_entries = []
        segment_count = asrt_bs_box.read("uintbe:32")

        for _ in range(0, segment_count):
            first_segment = asrt_bs_box.read("uintbe:32")
            fragments_per_segment = asrt_bs_box.read("uintbe:32")
            asrt.segment_run_table_entries.append(
                SegmentRunTable.TableEntry(first_segment=first_segment,
                                           fragments_per_segment=fragments_per_segment))
        return asrt


class FragmentRunTable(AbstractTable, MixinDictRepr):
    type = "afrt"

    class TableEntry(namedtuple("FragmentRunTableEntry",
                                ["first_fragment",
                                 "first_fragment_timestamp",
                                 "fragment_duration",
                                 "discontinuity_indicator"])):
        DI_END_OF_PRESENTATION = 0
        DI_NUMBERING = 1
        DI_TIMESTAMP = 2
        DI_TIMESTAMP_AND_NUMBER = 3

        def __eq__(self, other):
            if self.first_fragment == other.first_fragment and \
                    self.first_fragment_timestamp == other.first_fragment_timestamp and \
                    self.fragment_duration == other.fragment_duration and \
                    self.discontinuity_indicator == other.discontinuity_indicator:
                return True

    def __init__(self):
        super(FragmentRunTable, self).__init__()
        self.update = None
        self.quality_fragment_url_modifiers = None
        self.fragments = None

    def __repr__(self, *args, **kwargs):
        return str(self.__dict__)

    @staticmethod
    def parse(box_bs):
        """ Parse afrt / Fragment Run Table Box """

        afrt = FragmentRunTable()
        afrt.header = Parser.read_box_header(box_bs)
        # read the entire box in case there's padding
        afrt_bs_box = box_bs.read(afrt.header.box_size * 8)

        afrt_bs_box.pos += 8
        update_flag = afrt_bs_box.read("uintbe:24")
        afrt.update = True if update_flag == 1 else False

        afrt.time_scale = afrt_bs_box.read("uintbe:32")
        afrt.quality_fragment_url_modifiers = Parser.read_count_and_string_table(afrt_bs_box)

        fragment_count = afrt_bs_box.read("uintbe:32")

        afrt.fragments = []

        for _ in range(0, fragment_count):
            first_fragment = afrt_bs_box.read("uintbe:32")
            first_fragment_timestamp_raw = afrt_bs_box.read("uintbe:64")

            try:
                first_fragment_timestamp = datetime.utcfromtimestamp(
                    first_fragment_timestamp_raw / float(afrt.time_scale))
            except ValueError:
                # Elemental sometimes create odd timestamps
                first_fragment_timestamp = None

            fragment_duration = afrt_bs_box.read("uintbe:32")

            if fragment_duration == 0:
                discontinuity_indicator = afrt_bs_box.read("uintbe:8")
            else:
                discontinuity_indicator = None

            frte = FragmentRunTable.TableEntry(first_fragment=first_fragment,
                                               first_fragment_timestamp=first_fragment_timestamp,
                                               fragment_duration=fragment_duration,
                                               discontinuity_indicator=discontinuity_indicator)
            afrt.fragments.append(frte)
        return afrt


class MediaDataBox(AbstractBox, MixinMinimalRepr):
    """ aka mdat """
    type = "mdat"

    def __init__(self):
        super(MediaDataBox, self).__init__()
        self.payload = None

    @staticmethod
    def parse(box_bs, header):
        """ Parse afrt / Fragment Run Table Box """

        mdat = MediaDataBox()
        mdat.header = header
        mdat.payload = box_bs.read(mdat.header.box_size * 8).bytes
        return mdat


class MovieFragmentHeader(AbstractBox, MixinDictRepr):
    type = "mfhd"

    @staticmethod
    def parse(bootstrap_bs, header):
        mfhd = MovieFragmentHeader()
        mfhd.header = header

        # skip box_bs
        _ = bootstrap_bs.read(mfhd.header.box_size * 8)
        return mfhd


class ProtectionSystemSpecificHeader(AbstractBox, MixinDictRepr):
    type = "pssh"

    def __init__(self):
        super(ProtectionSystemSpecificHeader, self).__init__()
        self.payload = None

    @staticmethod
    def parse(bootstrap_bs, header):
        pssh = ProtectionSystemSpecificHeader()
        pssh.header = header

        box_bs = bootstrap_bs.read(pssh.header.box_size * 8)
        # Payload appears to be 8 bytes in.
        pssh.payload = box_bs.bytes[8:]
        return pssh


BoxHeader = namedtuple("BoxHeader", ["box_size", "box_type", "header_size"])


class Parser(object):
    _box_lookup = {}

    @classmethod
    def register_box(cls, box_cls):
        cls._box_lookup[box_cls.type] = box_cls.parse

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
            bs = bitstring.ConstBitStream(filename=filename, offset=offset_bytes * 8)
        elif bytes_input:
            bs = bitstring.ConstBitStream(bytes=bytes_input, offset=offset_bytes * 8)
        else:
            bs = bitstring.ConstBitStream(auto=file_input, offset=offset_bytes * 8)

        log.debug("Starting parse")
        log.debug("Size is %d bits", bs.len)

        while bs.pos < bs.len:
            log.debug("Byte pos before header: %d relative to (%d)", bs.bytepos, offset_bytes)
            log.debug("Reading header")
            try:
                header = cls.read_box_header(bs)
            except bitstring.ReadError:
                log.error("Premature end of data while reading box header")
                raise

            log.debug("Header type: %s", header.box_type)
            log.debug("Byte pos after header: %d relative to (%d)", bs.bytepos, offset_bytes)

            if headers_only:
                yield header

                # move pointer to next header if possible
                try:
                    bs.bytepos += header.box_size
                except ValueError:
                    log.warning("Premature end of data")
                    raise
            else:
                # Get parser method for header type
                parse_function = cls._box_lookup.get(header.box_type, UnknownBox.parse)
                try:
                    yield parse_function(bs, header)
                except ValueError:
                    log.error("Premature end of data")
                    raise

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

    @staticmethod
    def read_string(bs):
        """ read UTF8 null terminated string """
        result = bs.readto('0x00', bytealigned=True).bytes.decode("utf-8")[:-1]
        return result if result else None

    @classmethod
    def read_count_and_string_table(cls, bs):
        """ Read a count then return the strings in a list """
        result = []
        entry_count = bs.read("uintbe:8")
        for _ in range(0, entry_count):
            result.append(cls.read_string(bs))
        return result

    @staticmethod
    def read_box_header(bs):
        header_start_pos = bs.bytepos
        size, box_type = bs.readlist("uintbe:32, bytes:4")

        # box_type should be an ASCII string. Decode as UTF-8 in case
        try:
            box_type = box_type.decode("utf-8")
        except UnicodeDecodeError:
            # we'll leave as bytes instead
            pass

        # if size == 1, then this is an extended size type.
        # Therefore read the next 64 bits as size
        if size == 1:
            size = bs.read("uintbe:64")
        header_end_pos = bs.bytepos
        header_size = header_end_pos - header_start_pos

        return BoxHeader(box_size=size - header_size, box_type=box_type,
                         header_size=header_size)

    @staticmethod
    def parse_time_field(bs, scale):
        timestamp = bs.read("uintbe:64")
        return datetime.utcfromtimestamp(timestamp / float(scale))


# =====
# Boxes
# =====
UNKN = UnknownBox
ABST = BootStrapInfoBox
AFRA = FragmentRandomAccessBox
MDAT = MediaDataBox
MOOF = MovieFragmentBox
MFHD = MovieFragmentHeader
PSSH = ProtectionSystemSpecificHeader

# ======
# Tables
# ======
ASRT = SegmentRunTable
AFRT = FragmentRunTable


Parser.register_box(BootStrapInfoBox)
Parser.register_box(FragmentRandomAccessBox)
Parser.register_box(MediaDataBox)
Parser.register_box(MovieFragmentBox)
Parser.register_box(MovieFragmentHeader)
Parser.register_box(ProtectionSystemSpecificHeader)
