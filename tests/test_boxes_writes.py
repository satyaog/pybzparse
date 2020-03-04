""" Benzina MP4 Parser based on https://github.com/use-sparingly/pymp4parse """

from bitstring import pack

from pybzparse import Parser, boxes as bx_def, fields_lists as flists
from pybzparse.headers import BoxHeader, FullBoxHeader, MAX_UINT_32


def test_header_fields_list():
    bs = pack("uintbe:32, bytes:4", 100, b"abcd")

    fields_list = flists.BoxHeaderFieldsList()
    fields_list.box_size = 100
    fields_list.box_type = b'abcd'

    assert fields_list.box_size == 100
    assert fields_list.box_type == b"abcd"
    assert fields_list.box_ext_size is None
    assert fields_list.user_type is None
    assert bytes(fields_list) == bs.bytes


def test_header_extended_fields_list():
    bs = pack("uintbe:32, bytes:4, uintbe:64", 1, b"abcd", MAX_UINT_32 + 1)

    fields_list = flists.BoxHeaderFieldsList()
    fields_list.box_size = 1
    fields_list.box_type = b"abcd"
    fields_list.box_ext_size = MAX_UINT_32 + 1

    assert fields_list.box_size == 1
    assert fields_list.box_type == b"abcd"
    assert fields_list.box_ext_size == MAX_UINT_32 + 1
    assert fields_list.user_type is None
    assert bytes(fields_list) == bs.bytes


def test_header_extended_fields_list_w_no_type():
    bs = pack("uintbe:32, bytes:4, uintbe:64", 1, b"abcd", MAX_UINT_32 + 1)

    fields_list = flists.BoxHeaderFieldsList()
    fields_list.box_size = (1,)
    fields_list.box_type = (b"abcd",)
    fields_list.box_ext_size = (MAX_UINT_32 + 1,)

    assert fields_list.box_size == 1
    assert fields_list.box_type == b"abcd"
    assert fields_list.box_ext_size == MAX_UINT_32 + 1
    assert fields_list.user_type is None
    assert bytes(fields_list) == bs.bytes


def test_header_user_type_fields_list():
    bs = pack("uintbe:32, bytes:4, bytes:16", 100, b"uuid",
              b":benzina\x00\x00\x00\x00\x00\x00\x00\x00")

    fields_list = flists.BoxHeaderFieldsList()
    fields_list.box_size = 100
    fields_list.box_type = b"uuid"
    fields_list.user_type = b":benzina\x00\x00\x00\x00\x00\x00\x00\x00"

    assert fields_list.box_size == 100
    assert fields_list.box_type == b"uuid"
    assert fields_list.box_ext_size is None
    assert fields_list.user_type == b":benzina\x00\x00\x00\x00\x00\x00\x00\x00"
    assert bytes(fields_list) == bs.bytes


def test_header_extended_user_type_fields_list():
    bs = pack("uintbe:32, bytes:4, uintbe:64, bytes:16", 1, b"uuid",
              MAX_UINT_32 + 1, b":benzina\x00\x00\x00\x00\x00\x00\x00\x00")

    fields_list = flists.BoxHeaderFieldsList()
    fields_list.box_size = 1
    fields_list.box_type = b"uuid"
    fields_list.box_ext_size = MAX_UINT_32 + 1
    fields_list.user_type = b":benzina\x00\x00\x00\x00\x00\x00\x00\x00"

    assert fields_list.box_size == 1
    assert fields_list.box_type == b"uuid"
    assert fields_list.box_ext_size == MAX_UINT_32 + 1
    assert fields_list.user_type == b":benzina\x00\x00\x00\x00\x00\x00\x00\x00"
    assert bytes(fields_list) == bs.bytes

    fields_list = flists.BoxHeaderFieldsList()
    fields_list.box_ext_size = MAX_UINT_32 + 1
    fields_list.user_type = b":benzina\x00\x00\x00\x00\x00\x00\x00\x00"
    fields_list.box_type = b"uuid"
    fields_list.box_size = 1

    assert fields_list.box_size == 1
    assert fields_list.box_type == b"uuid"
    assert fields_list.box_ext_size == MAX_UINT_32 + 1
    assert fields_list.user_type == b":benzina\x00\x00\x00\x00\x00\x00\x00\x00"
    assert bytes(fields_list) == bs.bytes


def test_box_header():
    bs = pack("uintbe:32, bytes:4", 100, b"abcd")

    box_header = BoxHeader()
    box_header.type = b"abcd"
    box_header.box_size = 100

    assert box_header.type == b"abcd"
    assert box_header.box_size == 100
    assert box_header.header_size == 8
    assert box_header.content_size == 92
    assert bytes(box_header) == bs.bytes

    box_header = BoxHeader()
    box_header.box_size = 100
    box_header.type = b"abcd"

    assert box_header.type == b"abcd"
    assert box_header.box_size == 100
    assert box_header.header_size == 8
    assert box_header.content_size == 92
    assert bytes(box_header) == bs.bytes


def test_box_header_force_box_extended_size():
    bs = pack("uintbe:32, bytes:4, uintbe:64", 1, b"abcd", 32)

    box_header = BoxHeader()
    box_header.type = b"abcd"
    box_header.box_ext_size = 32

    assert box_header.type == b"abcd"
    assert box_header.box_size == 32
    assert box_header.box_ext_size == 32
    assert box_header.header_size == 16
    assert box_header.content_size == 16
    assert bytes(box_header) == bs.bytes


def test_box_header_extended_user_type():
    bs = pack("uintbe:32, bytes:4, uintbe:64, bytes:16", 1, b"uuid",
              MAX_UINT_32 + 1, b":benzina\x00\x00\x00\x00\x00\x00\x00\x00")

    box_header = BoxHeader()
    box_header.type = b"uuid:benzina\x00\x00\x00\x00\x00\x00\x00\x00"
    box_header.box_size = MAX_UINT_32 + 1

    assert box_header.type == b"uuid:benzina\x00\x00\x00\x00\x00\x00\x00\x00"
    assert box_header.box_size == MAX_UINT_32 + 1
    assert box_header.header_size == 32
    assert box_header.content_size == MAX_UINT_32 + 1 - 32
    assert bytes(box_header) == bs.bytes

    box_header = BoxHeader()
    box_header.box_size = MAX_UINT_32 + 1
    box_header.type = b"uuid:benzina\x00\x00\x00\x00\x00\x00\x00\x00"

    assert box_header.type == b"uuid:benzina\x00\x00\x00\x00\x00\x00\x00\x00"
    assert box_header.box_size == MAX_UINT_32 + 1
    assert box_header.header_size == 32
    assert box_header.content_size == MAX_UINT_32 + 1 - 32
    assert bytes(box_header) == bs.bytes


def test_box_header_w_drop():
    bs = pack("uintbe:32, bytes:4", 100, b"abcd")

    box_header = BoxHeader()
    box_header.type = b"uuid:benzina\x00\x00\x00\x00\x00\x00\x00\x00"
    box_header.box_size = MAX_UINT_32 + 1

    box_header.type = b"abcd"
    box_header.box_size = 100

    assert box_header.type == b"abcd"
    assert box_header.box_size == 100
    assert box_header.header_size == 8
    assert box_header.content_size == 92
    assert bytes(box_header) == bs.bytes


def test_box_header_extended_user_type_w_drop():
    bs = pack("uintbe:32, bytes:4, uintbe:64, bytes:16", 1, b"uuid",
              MAX_UINT_32 + 1, b":benzina\x00\x00\x00\x00\x00\x00\x00\x00")

    box_header = BoxHeader()
    box_header.type = b"uuid:benzina\x00\x00\x00\x00\x00\x00\x00\x00"
    box_header.box_size = MAX_UINT_32 + 1

    box_header.type = b"abcd"
    box_header.box_size = 100

    box_header.type = b"uuid:benzina\x00\x00\x00\x00\x00\x00\x00\x00"
    box_header.box_size = MAX_UINT_32 + 1

    assert box_header.type == b"uuid:benzina\x00\x00\x00\x00\x00\x00\x00\x00"
    assert box_header.box_size == MAX_UINT_32 + 1
    assert box_header.header_size == 32
    assert box_header.content_size == MAX_UINT_32 + 1 - 32
    assert bytes(box_header) == bs.bytes


def test_full_box_header():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24",
              100, b"abcd", 1, b"\x00\x00\x07")

    full_box_header = FullBoxHeader()
    full_box_header.type = b"abcd"
    full_box_header.box_size = 100
    full_box_header.version = 1
    full_box_header.flags = b"\x00\x00\x07"
    full_box_header.refresh_cache()

    assert full_box_header.type == b"abcd"
    assert full_box_header.box_size == 100
    assert full_box_header.header_size == 12
    assert full_box_header.content_size == 88
    assert full_box_header.version == 1
    assert full_box_header.flags == b"\x00\x00\x07"

    assert bytes(full_box_header) == bs.bytes

    full_box_header = FullBoxHeader()
    full_box_header.flags = b"\x00\x00\x07"
    full_box_header.type = b"abcd"
    full_box_header.version = 1
    full_box_header.box_size = 100
    full_box_header.refresh_cache()

    assert full_box_header.type == b"abcd"
    assert full_box_header.box_size == 100
    assert full_box_header.header_size == 12
    assert full_box_header.content_size == 88
    assert full_box_header.version == 1
    assert full_box_header.flags == b"\x00\x00\x07"

    assert bytes(full_box_header) == bs.bytes


def test_full_box_header_w_drop():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24",
              100, b"abcd", 1, b"\x00\x00\x07")

    full_box_header = FullBoxHeader()
    full_box_header.flags = b"\x00\x00\x07"
    full_box_header.type = b"uuid:benzina\x00\x00\x00\x00\x00\x00\x00\x00"
    full_box_header.version = 1
    full_box_header.box_size = MAX_UINT_32 + 1

    full_box_header.type = b"abcd"
    full_box_header.box_size = 100
    full_box_header.refresh_cache()

    assert full_box_header.type == b"abcd"
    assert full_box_header.box_size == 100
    assert full_box_header.header_size == 12
    assert full_box_header.content_size == 88
    assert full_box_header.version == 1
    assert full_box_header.flags == b"\x00\x00\x07"

    assert bytes(full_box_header) == bs.bytes


def test_ftyp_box():
    bs = pack("uintbe:32, bytes:4, "
              "bytes:4, uintbe:32, bytes:8",
              24, b"ftyp",
              b"bzna", 10, b"mp42mp41")

    box_header = BoxHeader()
    ftyp = bx_def.FTYP(box_header)
    ftyp.header.type = b"ftyp"
    ftyp.major_brand = 1652190817           # b"bzna"
    ftyp.minor_version = 10
    ftyp.compatible_brands = [1836069938,   # b"mp42"
                              1836069937]   # b"mp41"
    ftyp.refresh_box_size()

    box = ftyp

    assert box.header.type == b"ftyp"
    assert box.header.box_size == 24
    assert box.major_brand == 1652190817            # b"bzna"
    assert box.minor_version == 10
    assert box.compatible_brands == [1836069938,    # b"mp42"
                                     1836069937]    # b"mp41"

    assert bytes(next(Parser.parse(bs))) == bs.bytes
    assert bytes(box) == bs.bytes


def test_ftyp_box_w_no_type():
    bs = pack("uintbe:32, bytes:4, "
              "bytes:4, uintbe:32, bytes:8",
              24, b"ftyp",
              b"bzna", 10, b"mp42mp41")

    box_header = BoxHeader()
    ftyp = bx_def.FTYP(box_header)
    ftyp.header.type = b"ftyp"
    ftyp.major_brand = (1652190817,)            # b"bzna"
    ftyp.minor_version = (10,)
    ftyp.compatible_brands = ([1836069938,      # b"mp42"
                               1836069937],)    # b"mp41"
    ftyp.refresh_box_size()

    box = ftyp

    assert box.header.type == b"ftyp"
    assert box.header.box_size == 24
    assert box.major_brand == 1652190817            # b"bzna"
    assert box.minor_version == 10
    assert box.compatible_brands == [1836069938,    # b"mp42"
                                     1836069937]    # b"mp41"

    assert bytes(next(Parser.parse(bs))) == bs.bytes
    assert bytes(box) == bs.bytes


def test_mvhd_box_v0():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
              "uintbe:32, uintbe:32, uintbe:32, uintbe:32, "
              "uintbe:16, uintbe:16, uintbe:8, uintbe:8, "
              "bits:16, bits:32, bits:32, "
              "uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, "
              "bits:32, bits:32, bits:32, bits:32, bits:32, bits:32, "
              "uintbe:32",
              108, b"mvhd", 0, b"\x00\x00\x00",
              3596199850, 3596199850, 48000, 6720608,
              1, 0, 1, 0,
              b"\x00" * 2, b"\x00" * 4, b"\x00" * 4,
              65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824,
              b"\x00" * 4, b"\x00" * 4, b"\x00" * 4, b"\x00" * 4, b"\x00" * 4, b"\x00" * 4,
              3)

    box_header = FullBoxHeader()
    mvhd = bx_def.MVHD(box_header)

    mvhd.header.type = b"mvhd"
    mvhd.header.version = 0
    mvhd.header.flags = b"\x00\x00\x00"

    mvhd.creation_time = (3596199850, "uintbe:32")
    mvhd.modification_time = (3596199850, "uintbe:32")
    mvhd.timescale = (48000, "uintbe:32")
    mvhd.duration = (6720608, "uintbe:32")

    mvhd.rate = [1, 0]
    mvhd.volume = [1, 0]

    mvhd.matrix = [65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824]
    mvhd.pre_defined = [b"\x00" * 4] * 6

    mvhd.next_track_id = 3

    mvhd.refresh_box_size()

    box = mvhd

    assert box.header.type == b"mvhd"
    assert box.header.box_size == 108
    assert box.header.version == 0
    assert box.header.flags == b"\x00\x00\x00"

    assert box.creation_time == 3596199850
    assert box.modification_time == 3596199850
    assert box.timescale == 48000
    assert box.duration == 6720608

    assert box.rate == [1, 0]
    assert box.volume == [1, 0]

    assert box.matrix == [65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824]
    assert box.pre_defined == [b"\x00" * 4] * 6

    assert box.next_track_id == 3

    assert bytes(next(Parser.parse(bs))) == bs.bytes
    assert bytes(box) == bs.bytes


def test_mvhd_box_v1():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
              "uintbe:64, uintbe:64, uintbe:32, uintbe:64, "
              "uintbe:16, uintbe:16, uintbe:8, uintbe:8, "
              "bits:16, bits:32, bits:32, "
              "uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, "
              "bits:32, bits:32, bits:32, bits:32, bits:32, bits:32, "
              "uintbe:32",
              120, b"mvhd", 1, b"\x00\x00\x00",
              3596199850, 3596199850, 48000, 6720608,
              1, 0, 1, 0,
              b"\x00" * 2, b"\x00" * 4, b"\x00" * 4,
              65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824,
              b"\x00" * 4, b"\x00" * 4, b"\x00" * 4, b"\x00" * 4, b"\x00" * 4, b"\x00" * 4,
              3)

    box_header = FullBoxHeader()
    mvhd = bx_def.MVHD(box_header)

    mvhd.header.type = b"mvhd"
    mvhd.header.version = 1
    mvhd.header.flags = b"\x00\x00\x00"

    mvhd.creation_time = 3596199850
    mvhd.modification_time = 3596199850
    mvhd.timescale = 48000
    mvhd.duration = 6720608

    mvhd.rate = [1, 0]
    mvhd.volume = [1, 0]

    mvhd.matrix = [65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824]
    mvhd.pre_defined = [b"\x00" * 4] * 6

    mvhd.next_track_id = 3

    mvhd.refresh_box_size()

    box = mvhd

    assert box.header.type == b"mvhd"
    assert box.header.box_size == 120
    assert box.header.version == 1
    assert box.header.flags == b"\x00\x00\x00"

    assert box.creation_time == 3596199850
    assert box.modification_time == 3596199850
    assert box.timescale == 48000
    assert box.duration == 6720608

    assert box.rate == [1, 0]
    assert box.volume == [1, 0]

    assert box.matrix == [65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824]
    assert box.pre_defined == [b"\x00" * 4] * 6

    assert box.next_track_id == 3

    assert bytes(next(Parser.parse(bs))) == bs.bytes
    assert bytes(box) == bs.bytes


def test_tkhd_box_v0():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
              "uintbe:32, uintbe:32, uintbe:32, "
              "bits:32, "
              "uintbe:32, "
              "bits:32, bits:32, "
              "uintbe:16, uintbe:16, uintbe:8, uintbe:8, "
              "bits:16, "
              "uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, "
              "uintbe:16, uintbe:16, uintbe:16, uintbe:16",
              92, b"tkhd", 0, b"\x00\x00\x07",
              3596199850, 3596199850, 1,
              b"\x00" * 4,
              6720313,
              b"\x00" * 4, b"\x00" * 4,
              0, 0, 0, 0,
              b"\x00" * 2,
              65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824,
              318, 0, 180, 0)

    box_header = FullBoxHeader()
    tkhd = bx_def.TKHD(box_header)

    tkhd.header.type = b"tkhd"
    tkhd.header.version = 0
    tkhd.header.flags = b"\x00\x00\x07"

    tkhd.creation_time = (3596199850, "uintbe:32")
    tkhd.modification_time = (3596199850, "uintbe:32")
    tkhd.track_id = (1, "uintbe:32")
    tkhd.duration = (6720313, "uintbe:32")

    tkhd.layer = 0
    tkhd.alternate_group = 0
    tkhd.volume = [0, 0]

    tkhd.matrix = [65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824]

    tkhd.width = [318, 0]
    tkhd.height = [180, 0]

    tkhd.refresh_box_size()

    box = tkhd

    assert box.header.type == b"tkhd"
    assert box.header.box_size == 92
    assert box.header.version == 0
    assert box.header.flags == b"\x00\x00\x07"

    assert box.creation_time == 3596199850
    assert box.modification_time == 3596199850
    assert box.track_id == 1
    assert box.duration == 6720313

    assert box.layer == 0
    assert box.alternate_group == 0
    assert box.volume == [0, 0]

    assert box.matrix == [65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824]

    assert box.width == 318
    assert box.height == 180

    assert box.is_audio is False

    assert bytes(next(Parser.parse(bs))) == bs.bytes
    assert bytes(box) == bs.bytes


def test_tkhd_box_v1():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
              "uintbe:64, uintbe:64, uintbe:32, "
              "bits:32, "
              "uintbe:64, "
              "bits:32, bits:32, "
              "uintbe:16, uintbe:16, uintbe:8, uintbe:8, "
              "bits:16, "
              "uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, "
              "uintbe:16, uintbe:16, uintbe:16, uintbe:16",
              104, b"tkhd", 1, b"\x00\x00\x07",
              3596199850, 3596199850, 1,
              b"\x00" * 4,
              6720313,
              b"\x00" * 4, b"\x00" * 4,
              0, 0, 0, 0,
              b"\x00" * 2,
              65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824,
              318, 0, 180, 0)

    box_header = FullBoxHeader()
    tkhd = bx_def.TKHD(box_header)

    tkhd.header.type = b"tkhd"
    tkhd.header.version = 1
    tkhd.header.flags = b"\x00\x00\x07"

    tkhd.creation_time = 3596199850
    tkhd.modification_time = 3596199850
    tkhd.track_id = 1
    tkhd.duration = 6720313

    tkhd.layer = 0
    tkhd.alternate_group = 0
    tkhd.volume = [0, 0]

    tkhd.matrix = [65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824]

    tkhd.width = [318, 0]
    tkhd.height = [180, 0]

    tkhd.refresh_box_size()

    box = tkhd

    assert box.header.type == b"tkhd"
    assert box.header.box_size == 104
    assert box.header.version == 1
    assert box.header.flags == b"\x00\x00\x07"

    assert box.creation_time == 3596199850
    assert box.modification_time == 3596199850
    assert box.track_id == 1
    assert box.duration == 6720313

    assert box.layer == 0
    assert box.alternate_group == 0
    assert box.volume == [0, 0]

    assert box.matrix == [65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824]

    assert box.width == 318
    assert box.height == 180

    assert box.is_audio is False

    assert bytes(next(Parser.parse(bs))) == bs.bytes
    assert bytes(box) == bs.bytes


def test_mdhd_box_v0():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
              "uintbe:32, uintbe:32, uintbe:32, uintbe:32, "
              "bits:1, uint:5, uint:5, uint:5, "
              "bits:16",
              32, b"mdhd", 0, b"\x00\x00\x00",
              3596199850, 3596199850, 30000, 4200196,
              0x1, 21, 14, 4,
              b"\x00" * 2)

    box_header = FullBoxHeader()
    mdhd = bx_def.MDHD(box_header)

    mdhd.header.type = b"mdhd"
    mdhd.header.version = 0
    mdhd.header.flags = b"\x00\x00\x00"

    mdhd.creation_time = (3596199850, "uintbe:32")
    mdhd.modification_time = (3596199850, "uintbe:32")
    mdhd.timescale = (30000, "uintbe:32")
    mdhd.duration = (4200196, "uintbe:32")

    mdhd.language = [21, 14, 4]
    mdhd.pre_defined = 0

    mdhd.refresh_box_size()

    box = mdhd

    assert box.header.type == b"mdhd"
    assert box.header.box_size == 32
    assert box.header.version == 0
    assert box.header.flags == b"\x00\x00\x00"

    assert box.creation_time == 3596199850
    assert box.modification_time == 3596199850
    assert box.timescale == 30000
    assert box.duration == 4200196

    assert box.language == [21, 14, 4]
    assert box.pre_defined == 0

    assert bytes(next(Parser.parse(bs))) == bs.bytes
    assert bytes(box) == bs.bytes


def test_mdhd_box_v1():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
              "uintbe:64, uintbe:64, uintbe:32, uintbe:64, "
              "bits:1, uint:5, uint:5, uint:5, "
              "bits:16",
              44, b"mdhd", 1, b"\x00\x00\x00",
              3596199850, 3596199850, 30000, 4200196,
              0x1, 21, 14, 4,
              b"\x00" * 2)

    box_header = FullBoxHeader()
    mdhd = bx_def.MDHD(box_header)

    mdhd.header.type = b"mdhd"
    mdhd.header.version = 1
    mdhd.header.flags = b"\x00\x00\x00"

    mdhd.creation_time = 3596199850
    mdhd.modification_time = 3596199850
    mdhd.timescale = 30000
    mdhd.duration = 4200196

    mdhd.language = [21, 14, 4]
    mdhd.pre_defined = 0

    mdhd.refresh_box_size()

    box = mdhd

    assert box.header.type == b"mdhd"
    assert box.header.box_size == 44
    assert box.header.version == 1
    assert box.header.flags == b"\x00\x00\x00"

    assert box.creation_time == 3596199850
    assert box.modification_time == 3596199850
    assert box.timescale == 30000
    assert box.duration == 4200196

    assert box.language == [21, 14, 4]
    assert box.pre_defined == 0

    assert bytes(next(Parser.parse(bs))) == bs.bytes
    assert bytes(box) == bs.bytes


def test_hdlr_box():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
              "uintbe:32, bytes:4, bits:32, bits:32, bits:32, bytes:19",
              51, b"hdlr", 0, b"\x00\x00\x00",
              0, b"vide", b"\x00" * 4, b"\x00" * 4, b"\x00" * 4, b"Vireo Eyes v2.4.22\0")

    box_header = FullBoxHeader()
    hdlr = bx_def.HDLR(box_header)

    hdlr.header.type = b"hdlr"
    hdlr.header.version = 0
    hdlr.header.flags = b"\x00\x00\x00"

    hdlr.pre_defined = 0
    hdlr.handler_type = b"vide"
    hdlr.name = b"Vireo Eyes v2.4.22\0"

    hdlr.refresh_box_size()

    box = hdlr

    assert box.header.type == b"hdlr"
    assert box.header.box_size == 51
    assert box.header.version == 0
    assert box.header.flags == b"\x00\x00\x00"

    assert box.pre_defined == 0
    assert box.handler_type == b"vide"
    assert box.name == b"Vireo Eyes v2.4.22\0"

    assert bytes(next(Parser.parse(bs))) == bs.bytes
    assert bytes(box) == bs.bytes


def test_elst_box_v0():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
              "uintbe:32, uintbe:32, uintbe:32, uintbe:16, uintbe:16",
              28, b"elst", 0, b"\x00\x00\x00",
              1, 3000, 0, 1, 0)

    box_header = FullBoxHeader()
    elst = bx_def.ELST(box_header)

    elst.header.type = b"elst"
    elst.header.version = 0
    elst.header.flags = b"\x00\x00\x00"

    entry = elst.append_and_return()
    entry.segment_duration = (3000, "uintbe:32")
    entry.media_time = (0, "uintbe:32")
    entry.media_rate_integer = 1
    entry.media_rate_fraction = 0

    elst.refresh_box_size()

    box = elst

    assert box.header.type == b"elst"
    assert box.header.box_size == 28
    assert box.header.version == 0
    assert box.header.flags == b"\x00\x00\x00"

    assert box.entry_count == 1
    assert len(box.entries) == 1
    assert box.entries[0].segment_duration == 3000
    assert box.entries[0].media_time == 0
    assert box.entries[0].media_rate_integer == 1
    assert box.entries[0].media_rate_fraction == 0

    parsed_box = next(Parser.parse(bs))
    parsed_box.load(bs)
    assert bytes(parsed_box) == bs.bytes
    assert bytes(box) == bs.bytes


def test_elst_box_v1():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
              "uintbe:32, uintbe:64, uintbe:64, uintbe:16, uintbe:16",
              36, b"elst", 1, b"\x00\x00\x00",
              1, 3000, 0, 1, 0)

    box_header = FullBoxHeader()
    elst = bx_def.ELST(box_header)

    elst.header.type = b"elst"
    elst.header.version = 1
    elst.header.flags = b"\x00\x00\x00"

    entry = elst.append_and_return()
    entry.segment_duration = 3000
    entry.media_time = 0
    entry.media_rate_integer = 1
    entry.media_rate_fraction = 0

    elst.refresh_box_size()

    box = elst

    assert box.header.type == b"elst"
    assert box.header.box_size == 36
    assert box.header.version == 1
    assert box.header.flags == b"\x00\x00\x00"

    assert box.entry_count == 1
    assert len(box.entries) == 1
    assert box.entries[0].segment_duration == 3000
    assert box.entries[0].media_time == 0
    assert box.entries[0].media_rate_integer == 1
    assert box.entries[0].media_rate_fraction == 0

    parsed_box = next(Parser.parse(bs))
    parsed_box.load(bs)
    assert bytes(parsed_box) == bs.bytes
    assert bytes(box) == bs.bytes


def test_vmhd_box():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
              "uintbe:16, uintbe:16, uintbe:16, uintbe:16",
              20, b"vmhd", 0, b"\x00\x00\x01",
              0, 0, 0, 0)

    box_header = FullBoxHeader()
    vmhd = bx_def.VMHD(box_header)

    vmhd.header.type = b"vmhd"
    vmhd.header.version = 0
    vmhd.header.flags = b"\x00\x00\x01"

    vmhd.graphicsmode = 0
    vmhd.opcolor = [0, 0, 0]

    vmhd.refresh_box_size()

    box = vmhd

    assert box.header.type == b"vmhd"
    assert box.header.box_size == 20
    assert box.header.version == 0
    assert box.header.flags == b"\x00\x00\x01"

    assert box.graphicsmode == 0
    assert box.opcolor == [0, 0, 0]

    assert bytes(next(Parser.parse(bs))) == bs.bytes
    assert bytes(box) == bs.bytes


def test_nmhd_box():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24",
              12, b"nmhd", 0, b"\x00\x00\x00")

    box_header = FullBoxHeader()
    nmhd = bx_def.NMHD(box_header)

    nmhd.header.type = b"nmhd"
    nmhd.header.version = 0
    nmhd.header.flags = b"\x00\x00\x00"

    nmhd.refresh_box_size()

    box = nmhd

    assert box.header.type == b"nmhd"
    assert box.header.box_size == 12
    assert box.header.version == 0
    assert box.header.flags == b"\x00\x00\x00"

    assert bytes(next(Parser.parse(bs))) == bs.bytes
    assert bytes(box) == bs.bytes


def test_stsd_box():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, uintbe:32",
              16, b"stsd", 0, b"\x00\x00\x00", 1)

    box_header = FullBoxHeader()
    stsd = bx_def.STSD(box_header)

    stsd.header.type = b"stsd"
    stsd.header.version = 0
    stsd.header.flags = b"\x00\x00\x00"

    stsd.entry_count = 1

    stsd.refresh_box_size()

    box = stsd

    assert box.header.type == b"stsd"
    assert box.header.box_size == 16
    assert box.header.version == 0
    assert box.header.flags == b"\x00\x00\x00"

    assert box.entry_count == 1

    assert bytes(box) == bs.bytes


def test_stts_box():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
              "uintbe:32, uintbe:32, uintbe:32",
              24, b"stts", 0, b"\x00\x00\x00",
              1, 1, 1)

    box_header = FullBoxHeader()
    stts = bx_def.STTS(box_header)

    stts.header.type = b"stts"
    stts.header.version = 0
    stts.header.flags = b"\x00\x00\x00"

    entry = stts.append_and_return()
    entry.sample_count = 1
    entry.sample_delta = 1

    stts.refresh_box_size()

    box = stts

    assert box.header.type == b"stts"
    assert box.header.box_size == 24
    assert box.header.version == 0
    assert box.header.flags == b"\x00\x00\x00"

    assert box.entry_count == 1
    assert len(box.entries) == 1
    assert box.entries[0].sample_count == 1
    assert box.entries[0].sample_delta == 1

    parsed_box = next(Parser.parse(bs))
    parsed_box.load(bs)
    assert bytes(parsed_box) == bs.bytes
    assert bytes(box) == bs.bytes


def test_ctts_box_v0():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
              "uintbe:32, uintbe:32, uintbe:32",
              24, b"ctts", 0, b"\x00\x00\x00",
              1, 1, 1)

    box_header = FullBoxHeader()
    ctts = bx_def.CTTS(box_header)

    ctts.header.type = b"ctts"
    ctts.header.version = 0
    ctts.header.flags = b"\x00\x00\x00"

    entry = ctts.append_and_return()
    entry.sample_count = 1
    entry.sample_offset = 1

    ctts.refresh_box_size()

    box = ctts

    assert box.header.type == b"ctts"
    assert box.header.box_size == 24
    assert box.header.version == 0
    assert box.header.flags == b"\x00\x00\x00"

    assert box.entry_count == 1
    assert len(box.entries) == 1
    assert box.entries[0].sample_count == 1
    assert box.entries[0].sample_offset == 1

    parsed_box = next(Parser.parse(bs))
    parsed_box.load(bs)
    assert bytes(parsed_box) == bs.bytes
    assert bytes(box) == bs.bytes


def test_ctts_box_v1():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
              "uintbe:32, uintbe:32, intbe:32",
              24, b"ctts", 1, b"\x00\x00\x00",
              1, 1, -1)

    box_header = FullBoxHeader()
    ctts = bx_def.CTTS(box_header)

    ctts.header.type = b"ctts"
    ctts.header.version = 1
    ctts.header.flags = b"\x00\x00\x00"

    entry = ctts.append_and_return()
    entry.sample_count = 1
    entry.sample_offset = (-1, "intbe:32")

    ctts.refresh_box_size()

    box = ctts

    assert box.header.type == b"ctts"
    assert box.header.box_size == 24
    assert box.header.version == 1
    assert box.header.flags == b"\x00\x00\x00"

    assert box.entry_count == 1
    assert len(box.entries) == 1
    assert box.entries[0].sample_count == 1
    assert box.entries[0].sample_offset == -1

    parsed_box = next(Parser.parse(bs))
    parsed_box.load(bs)
    assert bytes(parsed_box) == bs.bytes
    assert bytes(box) == bs.bytes


def test_stsz_box():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
              "uintbe:32, uintbe:32, uintbe:32",
              24, b"stsz", 0, b"\x00\x00\x00",
              0, 1, 1)

    box_header = FullBoxHeader()
    stsz = bx_def.STSZ(box_header)

    stsz.header.type = b"stsz"
    stsz.header.version = 0
    stsz.header.flags = b"\x00\x00\x00"

    stsz.sample_size = 0
    sample = stsz.append_and_return()
    sample.entry_size = 1

    stsz.refresh_box_size()

    box = stsz

    assert box.header.type == b"stsz"
    assert box.header.box_size == 24
    assert box.header.version == 0
    assert box.header.flags == b"\x00\x00\x00"

    assert box.sample_size == 0
    assert box.sample_count == 1
    assert len(box.samples) == 1
    assert box.samples[0].entry_size == 1

    parsed_box = next(Parser.parse(bs))
    parsed_box.load(bs)
    assert bytes(parsed_box) == bs.bytes
    assert bytes(box) == bs.bytes


def test_stsc_box():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
              "uintbe:32, uintbe:32, uintbe:32, uintbe:32",
              28, b"stsc", 0, b"\x00\x00\x00",
              1, 1, 1, 1)

    box_header = FullBoxHeader()
    stsc = bx_def.STSC(box_header)

    stsc.header.type = b"stsc"
    stsc.header.version = 0
    stsc.header.flags = b"\x00\x00\x00"

    entry = stsc.append_and_return()
    entry.first_chunk = 1
    entry.samples_per_chunk = 1
    entry.sample_description_index = 1

    stsc.refresh_box_size()

    box = stsc

    assert box.header.type == b"stsc"
    assert box.header.box_size == 28
    assert box.header.version == 0
    assert box.header.flags == b"\x00\x00\x00"

    assert box.entry_count == 1
    assert len(box.entries) == 1
    assert box.entries[0].first_chunk == 1
    assert box.entries[0].samples_per_chunk == 1
    assert box.entries[0].sample_description_index == 1

    parsed_box = next(Parser.parse(bs))
    parsed_box.load(bs)
    assert bytes(parsed_box) == bs.bytes
    assert bytes(box) == bs.bytes


def test_stco_box():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
              "uintbe:32, uintbe:32, uintbe:32, uintbe:32",
              28, b"stco", 0, b"\x00\x00\x00",
              3, 0, 1, 2)

    box_header = FullBoxHeader()
    stco = bx_def.STCO(box_header)

    stco.header.type = b"stco"
    stco.header.version = 0
    stco.header.flags = b"\x00\x00\x00"

    entry = stco.append_and_return()
    entry.chunk_offset = 0
    entry = stco.append_and_return()
    entry.chunk_offset = 1
    entry = stco.append_and_return()
    entry.chunk_offset = 2

    stco.refresh_box_size()

    box = stco

    assert box.header.type == b"stco"
    assert box.header.box_size == 28
    assert box.header.version == 0
    assert box.header.flags == b"\x00\x00\x00"

    assert box.entry_count == 3
    assert len(box.entries) == 3
    assert box.entries[0].chunk_offset == 0
    assert box.entries[1].chunk_offset == 1
    assert box.entries[2].chunk_offset == 2

    parsed_box = next(Parser.parse(bs))
    parsed_box.load(bs)
    assert bytes(parsed_box) == bs.bytes
    assert bytes(box) == bs.bytes


def test_co64_box():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
              "uintbe:32, uintbe:64, uintbe:64, uintbe:64",
              40, b"co64", 0, b"\x00\x00\x00",
              3, 0, 1, 2)

    box_header = FullBoxHeader()
    stco = bx_def.CO64(box_header)

    stco.header.type = b"co64"
    stco.header.version = 0
    stco.header.flags = b"\x00\x00\x00"

    entry = stco.append_and_return()
    entry.chunk_offset = 0
    entry = stco.append_and_return()
    entry.chunk_offset = 1
    entry = stco.append_and_return()
    entry.chunk_offset = 2

    stco.refresh_box_size()

    box = stco

    assert box.header.type == b"co64"
    assert box.header.box_size == 40
    assert box.header.version == 0
    assert box.header.flags == b"\x00\x00\x00"

    assert box.entry_count == 3
    assert len(box.entries) == 3
    assert box.entries[0].chunk_offset == 0
    assert box.entries[1].chunk_offset == 1
    assert box.entries[2].chunk_offset == 2

    parsed_box = next(Parser.parse(bs))
    parsed_box.load(bs)
    assert bytes(parsed_box) == bs.bytes
    assert bytes(box) == bs.bytes


def test_dref_box():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, uintbe:32",
              16, b"dref", 0, b"\x00\x00\x00", 1)

    box_header = FullBoxHeader()
    dref = bx_def.DREF(box_header)

    dref.header.type = b"dref"
    dref.header.version = 0
    dref.header.flags = b"\x00\x00\x00"

    dref.entry_count = 1

    dref.refresh_box_size()

    box = dref

    assert box.header.type == b"dref"
    assert box.header.box_size == 16
    assert box.header.version == 0
    assert box.header.flags == b"\x00\x00\x00"

    assert box.entry_count == 1

    assert bytes(box) == bs.bytes


def test_sample_entry_box():
    bs = pack("uintbe:32, bytes:4, "
              "uintbe:8, uintbe:8, uintbe:8, uintbe:8, uintbe:8, uintbe:8, "
              "uintbe:16",
              16, b"____",
              0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
              1)

    box_header = BoxHeader()
    sample_entry_box = bx_def.SampleEntryBox(box_header)

    sample_entry_box.header.type = b"____"
    sample_entry_box.data_reference_index = 1

    sample_entry_box.refresh_box_size()

    box = sample_entry_box

    assert box.header.type == b"____"
    assert box.header.box_size == 16

    assert box.data_reference_index == 1

    assert len(box.boxes) == 0

    assert bytes(box) == bs.bytes


def test_visual_sample_entry_box():
    bs = pack("uintbe:32, bytes:4, "
              "uintbe:8, uintbe:8, uintbe:8, uintbe:8, uintbe:8, uintbe:8, "
              "uintbe:16, "
              "uintbe:16, uintbe:16, uintbe:32, uintbe:32, uintbe:32, "
              "uintbe:16, uintbe:16, uintbe:16, uintbe:16, uintbe:16, uintbe:16, "
              "uintbe:32, "
              "uintbe:16, bytes:32, uintbe:16, "
              "intbe:16",
              86, b"____",
              0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
              1,
              0x0, 0x0, 0x0, 0x0, 0x0,
              512, 512, 72, 0, 72, 0,
              0x0,
              1, b'\0' * 32, 24,
              -1)

    box_header = BoxHeader()
    visual_sample_entry_box = bx_def.VisualSampleEntryBox(box_header)

    visual_sample_entry_box.header.type = b"____"
    visual_sample_entry_box.data_reference_index = 1
    visual_sample_entry_box.width = 512
    visual_sample_entry_box.height = 512
    visual_sample_entry_box.horizresolution = [72, 0]
    visual_sample_entry_box.vertresolution = [72, 0]
    visual_sample_entry_box.frame_count = 1
    visual_sample_entry_box.compressorname = b'\0' * 32
    visual_sample_entry_box.depth = 24

    visual_sample_entry_box.refresh_box_size()

    box = visual_sample_entry_box

    assert box.header.type == b"____"
    assert box.header.box_size == 86

    assert box.data_reference_index == 1
    assert box.width == 512
    assert box.height == 512
    assert box.horizresolution == [72, 0]
    assert box.vertresolution == [72, 0]
    assert box.frame_count == 1
    assert box.compressorname == b'\0' * 32
    assert box.depth == 24

    assert len(box.boxes) == 0

    assert bytes(box) == bs.bytes


def test_avc1_box():
    bs = pack("uintbe:32, bytes:4, "
              "uintbe:8, uintbe:8, uintbe:8, uintbe:8, uintbe:8, uintbe:8, "
              "uintbe:16, "
              "uintbe:16, uintbe:16, uintbe:32, uintbe:32, uintbe:32, "
              "uintbe:16, uintbe:16, uintbe:16, uintbe:16, uintbe:16, uintbe:16, "
              "uintbe:32, "
              "uintbe:16, bytes:32, uintbe:16, "
              "intbe:16",
              86, b"avc1",
              0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
              1,
              0x0, 0x0, 0x0, 0x0, 0x0,
              512, 512, 72, 0, 72, 0,
              0x0,
              1, b'\0' * 32, 24,
              -1)

    box_header = BoxHeader()
    avc1 = bx_def.AVC1(box_header)

    avc1.header.type = b"avc1"
    avc1.data_reference_index = 1
    avc1.width = 512
    avc1.height = 512
    avc1.horizresolution = [72, 0]
    avc1.vertresolution = [72, 0]
    avc1.frame_count = 1
    avc1.compressorname = b'\0' * 32
    avc1.depth = 24

    avc1.refresh_box_size()

    box = avc1

    assert box.header.type == b"avc1"
    assert box.header.box_size == 86

    assert box.data_reference_index == 1
    assert box.width == 512
    assert box.height == 512
    assert box.horizresolution == [72, 0]
    assert box.vertresolution == [72, 0]
    assert box.frame_count == 1
    assert box.compressorname == b'\0' * 32
    assert box.depth == 24

    assert len(box.boxes) == 0

    assert bytes(next(Parser.parse(bs))) == bs.bytes
    assert bytes(box) == bs.bytes


def test_stxt_box():
    bs = pack("uintbe:32, bytes:4, "
              "uintbe:8, uintbe:8, uintbe:8, uintbe:8, uintbe:8, uintbe:8, "
              "uintbe:16, "
              "bytes:1, bytes:11",
              28, b"stxt",
              0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
              1,
              b'\0', b'text/plain\0')

    box_header = BoxHeader()
    stxt = bx_def.STXT(box_header)

    stxt.header.type = b"stxt"
    stxt.data_reference_index = 1
    stxt.content_encoding = b'\0'
    stxt.mime_format = b'text/plain\0'

    stxt.refresh_box_size()

    box = stxt

    assert box.header.type == b"stxt"
    assert box.header.box_size == 28

    assert box.data_reference_index == 1
    assert box.content_encoding == b'\0'
    assert box.mime_format == b'text/plain\0'

    assert len(box.boxes) == 0

    assert bytes(next(Parser.parse(bs))) == bs.bytes
    assert bytes(box) == bs.bytes


def test_mett_box():
    bs = pack("uintbe:32, bytes:4, "
              "uintbe:8, uintbe:8, uintbe:8, uintbe:8, uintbe:8, uintbe:8, "
              "uintbe:16, "
              "bytes:1, bytes:11",
              28, b"mett",
              0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
              1,
              b'\0', b'image/heif\0')

    box_header = BoxHeader()
    mett = bx_def.METT(box_header)

    mett.header.type = b"mett"
    mett.data_reference_index = 1
    mett.content_encoding = b'\0'
    mett.mime_format = b'image/heif\0'

    mett.refresh_box_size()

    box = mett

    assert box.header.type == b"mett"
    assert box.header.box_size == 28

    assert box.data_reference_index == 1
    assert box.content_encoding == b'\0'
    assert box.mime_format == b'image/heif\0'

    assert len(box.boxes) == 0

    assert bytes(next(Parser.parse(bs))) == bs.bytes
    assert bytes(box) == bs.bytes


def test_sbtt_box():
    bs = pack("uintbe:32, bytes:4, "
              "uintbe:8, uintbe:8, uintbe:8, uintbe:8, uintbe:8, uintbe:8, "
              "uintbe:16, "
              "bytes:1, bytes:11",
              28, b"sbtt",
              0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
              1,
              b'\0', b'text/plain\0')

    box_header = BoxHeader()
    stxt = bx_def.STXT(box_header)

    stxt.header.type = b"sbtt"
    stxt.data_reference_index = 1
    stxt.content_encoding = b'\0'
    stxt.mime_format = b'text/plain\0'

    stxt.refresh_box_size()

    box = stxt

    assert box.header.type == b"sbtt"
    assert box.header.box_size == 28

    assert box.data_reference_index == 1
    assert box.content_encoding == b'\0'
    assert box.mime_format == b'text/plain\0'

    assert len(box.boxes) == 0

    assert bytes(next(Parser.parse(bs))) == bs.bytes
    assert bytes(box) == bs.bytes


def test_url__box():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24",
              12, b"url ", 0, b"\x00\x00\x01")

    box_header = FullBoxHeader()
    url_ = bx_def.URL_(box_header)

    url_.header.type = b"url "
    url_.header.version = 0
    url_.header.flags = b"\x00\x00\x01"

    url_.refresh_box_size()

    box = url_

    assert box.header.type == b"url "
    assert box.header.box_size == 12
    assert box.header.version == 0
    assert box.header.flags == b"\x00\x00\x01"

    assert box.location is None

    assert bytes(next(Parser.parse(bs))) == bs.bytes
    assert bytes(box) == bs.bytes


def test_pasp_box():
    bs = pack("uintbe:32, bytes:4, uintbe:32, uintbe:32",
              16, b"pasp", 150, 157)

    box_header = BoxHeader()
    pasp = bx_def.PASP(box_header)
    pasp.header.type = b"pasp"

    pasp.h_spacing = 150
    pasp.v_spacing = 157

    pasp.refresh_box_size()

    box = pasp

    assert box.header.type == b"pasp"
    assert box.header.box_size == 16
    assert box.h_spacing == 150
    assert box.v_spacing == 157

    assert bytes(next(Parser.parse(bs))) == bs.bytes
    assert bytes(box) == bs.bytes


def test_clap_box():
    bs = pack("uintbe:32, bytes:4, "
              "uintbe:32, uintbe:32, uintbe:32, uintbe:32, "
              "intbe:32, uintbe:32, intbe:32, uintbe:32",
              40, b"clap",
              500, 1, 333, 1,
              -12, 2, -179, 2)

    box_header = BoxHeader()
    clap = bx_def.CLAP(box_header)
    clap.header.type = b"clap"

    clap.clean_aperture_width_n = 500
    clap.clean_aperture_width_d = 1
    clap.clean_aperture_height_n = 333
    clap.clean_aperture_height_d = 1
    clap.horiz_off_n = -12
    clap.horiz_off_d = 2
    clap.vert_off_n = -179
    clap.vert_off_d = 2

    clap.refresh_box_size()

    box = clap

    assert box.header.type == b"clap"
    assert box.header.box_size == 40
    assert box.clean_aperture_width_n == 500
    assert box.clean_aperture_width_d == 1
    assert box.clean_aperture_height_n == 333
    assert box.clean_aperture_height_d == 1
    assert box.horiz_off_n == -12
    assert box.horiz_off_d == 2
    assert box.vert_off_n == -179
    assert box.vert_off_d == 2

    assert bytes(next(Parser.parse(bs))) == bs.bytes
    assert bytes(box) == bs.bytes


def test_hvcc_box():
    bs = pack("uintbe:32, bytes:4, "
              "uintbe:8, "
              "int:2, int:1, int:5, uintbe:32, uintbe:48, uintbe:8, "
              "bits:4, int:12, bits:6, int:2, bits:6, int:2, bits:5, int:3, bits:5, int:3, "
              "uintbe:16, uint:2, uint:3, uint:1, uint:2, uint:8, "

              "uint:1, bits:1, uint:6, uintbe:16, "

              "uint:16, bytes:3",
              39, b"hvcc",
              1,
              0, 0, 3, 1879048192, 193514046488576, 90,
              '0b1111', 0, '0b111111', 0, '0b111111', 1, '0b11111', 0, '0b11111', 0,
              0, 0, 1, 0, 3, 1,

              1, '0b0', 32, 1,

              3, b"321")

    box_header = BoxHeader()
    hvcc = bx_def.HVCC(box_header)

    hvcc.header.type = b"hvcc"
    hvcc.header.box_size = 39

    hvcc.configuration_version = 1

    hvcc.general_profile_space = 0
    hvcc.general_tier_flag = 0
    hvcc.general_profile_idc = 3
    hvcc.general_profile_compatibility_flags = 1879048192
    hvcc.general_constraint_indicator_flags = 193514046488576
    hvcc.general_level_idc = 90

    hvcc.min_spatial_segmentation_idc = 0
    hvcc.parallelism_type = 0
    hvcc.chroma_format = 1
    hvcc.bit_depth_luma_minus_8 = 0
    hvcc.bit_depth_chroma_minus_8 = 0

    hvcc.avg_frame_rate = 0
    hvcc.constant_frame_rate = 0
    hvcc.num_temporal_layers = 1
    hvcc.temporal_id_nested = 0
    hvcc.length_size_minus_one = 3

    array = hvcc.append_and_return()
    array.array_completeness = 1
    array.nal_unit_type = 32

    nalu = array.append_and_return()
    nalu.nal_unit_length = 3
    nalu.nal_unit = (b"321", "bytes:3")

    box = hvcc

    assert box.header.type == b"hvcc"
    assert box.header.box_size == 39

    assert box.configuration_version == 1

    assert box.general_profile_space == 0
    assert box.general_tier_flag == 0
    assert box.general_profile_idc == 3
    assert box.general_profile_compatibility_flags == 1879048192
    assert box.general_constraint_indicator_flags == 193514046488576
    assert box.general_level_idc == 90

    assert box.min_spatial_segmentation_idc == 0
    assert box.parallelism_type == 0
    assert box.chroma_format == 1
    assert box.bit_depth_luma_minus_8 == 0
    assert box.bit_depth_chroma_minus_8 == 0

    assert box.avg_frame_rate == 0
    assert box.constant_frame_rate == 0
    assert box.num_temporal_layers == 1
    assert box.temporal_id_nested == 0
    assert box.length_size_minus_one == 3
    assert box.num_of_arrays == 1
    assert len(box.arrays) == 1

    array = box.arrays[0]
    assert array.array_completeness == 1
    assert array.nal_unit_type == 32
    assert array.num_nalus == 1
    assert len(array.nalus) == 1

    nalu = array.nalus[0]
    assert nalu.nal_unit_length == 3
    assert nalu.nal_unit == b"321"

    parsed_box = next(Parser.parse(bs))
    parsed_box.load(bs)
    assert bytes(parsed_box) == bs.bytes
    assert bytes(box) == bs.bytes
