""" Benzina MP4 Parser based on https://github.com/use-sparingly/pymp4parse """

from bitstring import pack

import boxes as bx_def
import headers
import fields_lists as flists
from pybzparse import Parser


def test_header_fields_list():
    bs = pack("uintbe:32, bytes:4", 100, b"abcd")
    fields_list = flists.BoxHeaderFieldsList()
    fields_list.parse_fields(bs)

    assert fields_list.box_size == 100
    assert fields_list.box_type == b"abcd"
    assert fields_list.box_ext_size is None
    assert fields_list.user_type is None
    assert bytes(fields_list) == bs.bytes


def test_header_extended_fields_list():
    bs = pack("uintbe:32, bytes:4, uintbe:64", 1, b"abcd", headers.MAX_UINT_32 + 1)
    fields_list = flists.BoxHeaderFieldsList()
    fields_list.parse_fields(bs)

    assert fields_list.box_size == 1
    assert fields_list.box_type == b"abcd"
    assert fields_list.box_ext_size == headers.MAX_UINT_32 + 1
    assert fields_list.user_type is None
    assert bytes(fields_list) == bs.bytes


def test_header_user_type_fields_list():
    bs = pack("uintbe:32, bytes:4, bytes:16", 100, b"uuid",
              b":benzina\x00\x00\x00\x00\x00\x00\x00\x00")
    fields_list = flists.BoxHeaderFieldsList()
    fields_list.parse_fields(bs)

    assert fields_list.box_size == 100
    assert fields_list.box_type == b"uuid"
    assert fields_list.box_ext_size is None
    assert fields_list.user_type == b":benzina\x00\x00\x00\x00\x00\x00\x00\x00"
    assert bytes(fields_list) == bs.bytes


def test_header_extended_user_type_fields_list():
    bs = pack("uintbe:32, bytes:4, uintbe:64, bytes:16", 1, b"uuid",
              headers.MAX_UINT_32 + 1, b":benzina\x00\x00\x00\x00\x00\x00\x00\x00")
    fields_list = flists.BoxHeaderFieldsList()
    fields_list.parse_fields(bs)

    assert fields_list.box_size == 1
    assert fields_list.box_type == b"uuid"
    assert fields_list.box_ext_size == headers.MAX_UINT_32 + 1
    assert fields_list.user_type == b":benzina\x00\x00\x00\x00\x00\x00\x00\x00"
    assert bytes(fields_list) == bs.bytes


def test_box_header():
    bs = pack("uintbe:32, bytes:4", 100, b"abcd")
    box_header = Parser.parse_header(bs)

    assert box_header.start_pos == 0
    assert box_header.type == b"abcd"
    assert box_header.box_size == 100
    assert box_header.header_size == 8
    assert box_header.content_size == 92
    assert bytes(box_header) == bs.bytes


def test_box_header_extended():
    bs = pack("uintbe:32, bytes:4, uintbe:64", 1, b"abcd", headers.MAX_UINT_32 + 1)
    box_header = Parser.parse_header(bs)

    assert box_header.start_pos == 0
    assert box_header.type == b"abcd"
    assert box_header.box_size == headers.MAX_UINT_32 + 1
    assert box_header.header_size == 16
    assert box_header.content_size == headers.MAX_UINT_32 + 1 - 16
    assert bytes(box_header) == bs.bytes


def test_box_header_user_type():
    bs = pack("uintbe:32, bytes:4, bytes:16", 100, b"uuid",
              b":benzina\x00\x00\x00\x00\x00\x00\x00\x00")
    box_header = Parser.parse_header(bs)

    assert box_header.start_pos == 0
    assert box_header.type == b"uuid:benzina\x00\x00\x00\x00\x00\x00\x00\x00"
    assert box_header.box_size == 100
    assert box_header.header_size == 24
    assert box_header.content_size == 76
    assert bytes(box_header) == bs.bytes


def test_box_header_extended_user_type():
    bs = pack("uintbe:32, bytes:4, uintbe:64, bytes:16", 1, b"uuid",
              headers.MAX_UINT_32 + 1, b":benzina\x00\x00\x00\x00\x00\x00\x00\x00")
    box_header = Parser.parse_header(bs)

    assert box_header.start_pos == 0
    assert box_header.type == b"uuid:benzina\x00\x00\x00\x00\x00\x00\x00\x00"
    assert box_header.box_size == headers.MAX_UINT_32 + 1
    assert box_header.header_size == 32
    assert box_header.content_size == headers.MAX_UINT_32 + 1 - 32
    assert bytes(box_header) == bs.bytes


def test_full_box_header():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24",
              100, b"abcd", 1, b"\x00\x00\x07")
    box_header = Parser.parse_header(bs)
    full_box_header = bx_def.FullBoxHeader()
    full_box_header.extend_header(bs, box_header)
    del box_header

    assert full_box_header.start_pos == 0
    assert full_box_header.type == b"abcd"
    assert full_box_header.box_size == 100
    assert full_box_header.header_size == 12
    assert full_box_header.content_size == 88
    assert full_box_header.version == 1
    assert full_box_header.flags == b"\x00\x00\x07"

    assert bytes(full_box_header) == bs.bytes


def test_ftyp_box():
    bs = pack("uintbe:32, bytes:4, "
              "bytes:4, uintbe:32, bytes:12",
              28, b"ftyp",
              b"mp42", 0, b"mp42mp41iso4")

    box_header = Parser.parse_header(bs)
    ftyp = bx_def.FTYP.parse_box(bs, box_header)
    box = ftyp

    assert box.header.start_pos == 0
    assert box.header.type == b"ftyp"
    assert box.header.box_size == 28
    assert box.major_brand == 1836069938            # b"mp42"
    assert box.minor_version == 0
    assert box.compatible_brands == [1836069938,    # b"mp42"
                                     1836069937,    # b"mp41"
                                     1769172788]    # b"iso4"
    assert bytes(box) == bs.bytes


def test_mvhd_header_box():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
              "uintbe:32, uintbe:32, uintbe:32, uintbe:32, "
              "uintbe:32, uintbe:16, bits:16, bits:32, bits:32, "
              "uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, "
              "bits:32, bits:32, bits:32, bits:32, bits:32, bits:32, "
              "uintbe:32",
              108, b"mvhd", 0, b"\x00\x00\x00",
              3596199850, 3596199850, 48000, 6720608,
              65536, 256, b"\x00" * 2, b"\x00" * 4, b"\x00" * 4,
              65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824,
              b"\x00" * 4, b"\x00" * 4, b"\x00" * 4, b"\x00" * 4, b"\x00" * 4, b"\x00" * 4,
              3)

    box_header = Parser.parse_header(bs)
    mvhd = bx_def.MVHD.parse_box(bs, box_header)
    box = mvhd

    assert box.header.start_pos == 0
    assert box.header.type == b"mvhd"
    assert box.header.box_size == 108
    assert box.header.version == 0
    assert box.header.flags == b"\x00\x00\x00"

    assert box.creation_time == 3596199850
    assert box.modification_time == 3596199850
    assert box.timescale == 48000
    assert box.duration == 6720608

    assert box.rate == 65536
    assert box.volume == 256

    assert box.matrix == [65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824]
    assert box.pre_defined == [b"\x00" * 4] * 6

    assert box.next_track_id == 3

    assert bytes(box) == bs.bytes


def test_tkhd_header_box():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
              "uintbe:32, uintbe:32, uintbe:32, bits:32, uintbe:32, "
              "bits:32, bits:32, uintbe:16, uintbe:16, uintbe:16, bits:16, "
              "uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, "
              "uintbe:16, uintbe:16, uintbe:16, uintbe:16",
              92, b"tkhd", 0, b"\x00\x00\x07",
              3596199850, 3596199850, 1, b"\x00" * 4, 6720313,
              b"\x00" * 4, b"\x00" * 4, 0, 0, 0, b"\x00" * 2,
              65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824,
              318, 0, 180, 0)

    box_header = Parser.parse_header(bs)
    tkhd = bx_def.TKHD.parse_box(bs, box_header)
    box = tkhd

    assert box.header.start_pos == 0
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
    assert box.volume == 0

    assert box.matrix == [65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824]

    assert box.width == 318
    assert box.height == 180

    assert box.is_audio is False

    assert bytes(box) == bs.bytes


def test_mdhd_header_box():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
              "uintbe:32, uintbe:32, uintbe:32, uintbe:32, "
              "bits:1, uint:5, uint:5, uint:5, bits:16",
              32, b"mdhd", 0, b"\x00\x00\x00",
              3596199850, 3596199850, 30000, 4200196,
              0x1, 21, 14, 4, b"\x00" * 2)

    box_header = Parser.parse_header(bs)
    mdhd = bx_def.MDHD.parse_box(bs, box_header)
    box = mdhd

    assert box.header.start_pos == 0
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

    assert bytes(box) == bs.bytes


def test_hdlr_box():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
              "uintbe:32, bytes:4, bits:32, bits:32, bits:32, bytes:19",
              51, b"hdlr", 0, b"\x00\x00\x00",
              0, b"vide", b"\x00" * 4, b"\x00" * 4, b"\x00" * 4, b"Vireo Eyes v2.4.22\0")

    box_header = Parser.parse_header(bs)
    hdlr = bx_def.HDLR.parse_box(bs, box_header)
    box = hdlr

    assert box.header.start_pos == 0
    assert box.header.type == b"hdlr"
    assert box.header.box_size == 51
    assert box.header.version == 0
    assert box.header.flags == b"\x00\x00\x00"

    assert box.pre_defined == 0
    assert box.handler_type == b"vide"
    assert box.name == b"Vireo Eyes v2.4.22\0"

    assert bytes(box) == bs.bytes


def test_vmhd_header_box():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
              "uintbe:16, uintbe:16, uintbe:16, uintbe:16",
              20, b"vmhd", 0, b"\x00\x00\x01",
              0, 0, 0, 0)

    box_header = Parser.parse_header(bs)
    vmhd = bx_def.VMHD.parse_box(bs, box_header)
    box = vmhd

    assert box.header.start_pos == 0
    assert box.header.type == b"vmhd"
    assert box.header.box_size == 20
    assert box.header.version == 0
    assert box.header.flags == b"\x00\x00\x01"

    assert box.graphicsmode == 0
    assert box.opcolor == [0, 0, 0]

    assert bytes(box) == bs.bytes
