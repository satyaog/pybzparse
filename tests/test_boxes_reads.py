""" Benzina MP4 Parser based on https://github.com/use-sparingly/pymp4parse """

from bitstring import pack

from pybzparse import Parser, boxes as bx_def, fields_lists as flists
from pybzparse.headers import FullBoxHeader, MAX_UINT_32


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
    bs = pack("uintbe:32, bytes:4, uintbe:64", 1, b"abcd", MAX_UINT_32 + 1)
    fields_list = flists.BoxHeaderFieldsList()
    fields_list.parse_fields(bs)

    assert fields_list.box_size == 1
    assert fields_list.box_type == b"abcd"
    assert fields_list.box_ext_size == MAX_UINT_32 + 1
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
              MAX_UINT_32 + 1, b":benzina\x00\x00\x00\x00\x00\x00\x00\x00")
    fields_list = flists.BoxHeaderFieldsList()
    fields_list.parse_fields(bs)

    assert fields_list.box_size == 1
    assert fields_list.box_type == b"uuid"
    assert fields_list.box_ext_size == MAX_UINT_32 + 1
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
    bs = pack("uintbe:32, bytes:4, uintbe:64", 1, b"abcd", MAX_UINT_32 + 1)
    box_header = Parser.parse_header(bs)

    assert box_header.start_pos == 0
    assert box_header.type == b"abcd"
    assert box_header.box_size == MAX_UINT_32 + 1
    assert box_header.header_size == 16
    assert box_header.content_size == MAX_UINT_32 + 1 - 16
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
              MAX_UINT_32 + 1, b":benzina\x00\x00\x00\x00\x00\x00\x00\x00")
    box_header = Parser.parse_header(bs)

    assert box_header.start_pos == 0
    assert box_header.type == b"uuid:benzina\x00\x00\x00\x00\x00\x00\x00\x00"
    assert box_header.box_size == MAX_UINT_32 + 1
    assert box_header.header_size == 32
    assert box_header.content_size == MAX_UINT_32 + 1 - 32
    assert bytes(box_header) == bs.bytes


def test_full_box_header():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24",
              100, b"abcd", 1, b"\x00\x00\x07")
    box_header = Parser.parse_header(bs)
    full_box_header = FullBoxHeader()
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


def test_mdat_box():
    bs = pack("uintbe:32, bytes:4, "
              "bytes:4",
              12, b"mdat",
              b"1234")

    box_header = Parser.parse_header(bs)
    mdat = bx_def.MDAT.parse_box(bs, box_header)
    mdat.load(bs)
    box = mdat

    assert box.header.start_pos == 0
    assert box.header.type == b"mdat"
    assert box.header.box_size == 12
    assert box.data == b'1234'
    assert bytes(box) == bs.bytes


def test_mdat_box_empty():
    bs = pack("uintbe:32, bytes:4",
              8, b"mdat")

    box_header = Parser.parse_header(bs)
    mdat = bx_def.MDAT.parse_box(bs, box_header)
    mdat.load(bs)
    box = mdat

    assert box.header.start_pos == 0
    assert box.header.type == b"mdat"
    assert box.header.box_size == 8
    assert box.data == b''
    assert bytes(box) == bs.bytes


def test_mvhd_box():
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

    assert box.rate == [1, 0]
    assert box.volume == [1, 0]

    assert box.matrix == [65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824]
    assert box.pre_defined == [b"\x00" * 4] * 6

    assert box.next_track_id == 3

    assert bytes(box) == bs.bytes


def test_tkhd_box():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
              "uintbe:32, uintbe:32, uintbe:32, bits:32, uintbe:32, "
              "bits:32, bits:32, "
              "uintbe:16, uintbe:16, uintbe:8, uintbe:8, "
              "bits:16, "
              "uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, "
              "uintbe:16, uintbe:16, uintbe:16, uintbe:16",
              92, b"tkhd", 0, b"\x00\x00\x07",
              3596199850, 3596199850, 1, b"\x00" * 4, 6720313,
              b"\x00" * 4, b"\x00" * 4,
              0, 0, 0, 0,
              b"\x00" * 2,
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
    assert box.volume == [0, 0]

    assert box.matrix == [65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824]

    assert box.width == 318
    assert box.height == 180

    assert box.is_audio is False

    assert bytes(box) == bs.bytes


def test_mdhd_box():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
              "uintbe:32, uintbe:32, uintbe:32, uintbe:32, "
              "bits:1, uint:5, uint:5, uint:5, "
              "bits:16",
              32, b"mdhd", 0, b"\x00\x00\x00",
              3596199850, 3596199850, 30000, 4200196,
              0x1, 21, 14, 4,
              b"\x00" * 2)

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


def test_elst_box():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
              "uintbe:32, uintbe:32, uintbe:32, uintbe:16, uintbe:16",
              28, b"elst", 0, b"\x00\x00\x00",
              1, 3000, 0, 1, 0)

    box_header = Parser.parse_header(bs)
    elst = bx_def.ELST.parse_box(bs, box_header)
    box = elst

    assert box.header.start_pos == 0
    assert box.header.type == b"elst"
    assert box.header.box_size == 28
    assert box.header.version == 0
    assert box.header.flags == b"\x00\x00\x00"

    assert box.entry_count == 1
    assert len(box.entries) == 0

    box.load(bs)
    assert len(box.entries) == 1
    assert box.entries[0].segment_duration == 3000
    assert box.entries[0].media_time == 0
    assert box.entries[0].media_rate_integer == 1
    assert box.entries[0].media_rate_fraction == 0

    assert bytes(box) == bs.bytes


def test_vmhd_box():
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


def test_nmhd_box():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24",
              12, b"nmhd", 0, b"\x00\x00\x00")

    box_header = Parser.parse_header(bs)
    nmhd = bx_def.NMHD.parse_box(bs, box_header)
    box = nmhd

    assert box.header.start_pos == 0
    assert box.header.type == b"nmhd"
    assert box.header.box_size == 12
    assert box.header.version == 0
    assert box.header.flags == b"\x00\x00\x00"

    assert bytes(box) == bs.bytes


def test_stsd_box():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, uintbe:32",
              16, b"stsd", 0, b"\x00\x00\x00", 0)

    box_header = Parser.parse_header(bs)
    stsd = bx_def.STSD.parse_box(bs, box_header)
    box = stsd

    assert box.header.start_pos == 0
    assert box.header.type == b"stsd"
    assert box.header.box_size == 16
    assert box.header.version == 0
    assert box.header.flags == b"\x00\x00\x00"

    assert box.entry_count == 0

    assert bytes(box) == bs.bytes


def test_stts_box():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
              "uintbe:32, uintbe:32, uintbe:32",
              24, b"stts", 0, b"\x00\x00\x00",
              1, 1, 1)

    box_header = Parser.parse_header(bs)
    stts = bx_def.STTS.parse_box(bs, box_header)
    box = stts

    assert box.header.start_pos == 0
    assert box.header.type == b"stts"
    assert box.header.box_size == 24
    assert box.header.version == 0
    assert box.header.flags == b"\x00\x00\x00"

    assert box.entry_count == 1
    assert len(box.entries) == 0

    box.load(bs)
    assert len(box.entries) == 1
    assert box.entries[0].sample_count == 1
    assert box.entries[0].sample_delta == 1

    assert bytes(box) == bs.bytes


def test_ctts_box():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
              "uintbe:32, uintbe:32, uintbe:32",
              24, b"ctts", 0, b"\x00\x00\x00",
              1, 1, 1)

    box_header = Parser.parse_header(bs)
    ctts = bx_def.CTTS.parse_box(bs, box_header)
    box = ctts

    assert box.header.start_pos == 0
    assert box.header.type == b"ctts"
    assert box.header.box_size == 24
    assert box.header.version == 0
    assert box.header.flags == b"\x00\x00\x00"

    assert box.entry_count == 1
    assert len(box.entries) == 0

    box.load(bs)
    assert len(box.entries) == 1
    assert box.entries[0].sample_count == 1
    assert box.entries[0].sample_offset == 1

    assert bytes(box) == bs.bytes


def test_stsz_box():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
              "uintbe:32, uintbe:32, uintbe:32",
              24, b"stsz", 0, b"\x00\x00\x00",
              0, 1, 1)

    box_header = Parser.parse_header(bs)
    stsz = bx_def.STSZ.parse_box(bs, box_header)
    box = stsz

    assert box.header.start_pos == 0
    assert box.header.type == b"stsz"
    assert box.header.box_size == 24
    assert box.header.version == 0
    assert box.header.flags == b"\x00\x00\x00"

    assert box.sample_size == 0
    assert box.sample_count == 1
    assert len(box.samples) == 0

    box.load(bs)
    assert len(box.samples) == 1
    assert box.samples[0].entry_size == 1

    assert bytes(box) == bs.bytes


def test_stsc_box():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
              "uintbe:32, uintbe:32, uintbe:32, uintbe:32",
              28, b"stsc", 0, b"\x00\x00\x00",
              1, 1, 1, 1)

    box_header = Parser.parse_header(bs)
    stsc = bx_def.STSC.parse_box(bs, box_header)
    box = stsc

    assert box.header.start_pos == 0
    assert box.header.type == b"stsc"
    assert box.header.box_size == 28
    assert box.header.version == 0
    assert box.header.flags == b"\x00\x00\x00"

    assert box.entry_count == 1
    assert len(box.entries) == 0

    box.load(bs)
    assert len(box.entries) == 1
    assert box.entries[0].first_chunk == 1
    assert box.entries[0].samples_per_chunk == 1
    assert box.entries[0].sample_description_index == 1

    assert bytes(box) == bs.bytes


def test_stco_box():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
              "uintbe:32, uintbe:32, uintbe:32, uintbe:32",
              28, b"stco", 0, b"\x00\x00\x00",
              3, 0, 1, 2)

    box_header = Parser.parse_header(bs)
    stco = bx_def.STCO.parse_box(bs, box_header)
    box = stco

    assert box.header.start_pos == 0
    assert box.header.type == b"stco"
    assert box.header.box_size == 28
    assert box.header.version == 0
    assert box.header.flags == b"\x00\x00\x00"

    assert box.entry_count == 3
    assert len(box.entries) == 0

    box.load(bs)
    assert len(box.entries) == 3
    assert box.entries[0].chunk_offset == 0
    assert box.entries[1].chunk_offset == 1
    assert box.entries[2].chunk_offset == 2

    assert bytes(box) == bs.bytes


def test_co64_box():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
              "uintbe:32, uintbe:64, uintbe:64, uintbe:64",
              40, b"co64", 0, b"\x00\x00\x00",
              3, 0, 1, 2)

    box_header = Parser.parse_header(bs)
    stco = bx_def.CO64.parse_box(bs, box_header)
    box = stco

    assert box.header.start_pos == 0
    assert box.header.type == b"co64"
    assert box.header.box_size == 40
    assert box.header.version == 0
    assert box.header.flags == b"\x00\x00\x00"

    assert box.entry_count == 3
    assert len(box.entries) == 0

    box.load(bs)
    assert len(box.entries) == 3
    assert box.entries[0].chunk_offset == 0
    assert box.entries[1].chunk_offset == 1
    assert box.entries[2].chunk_offset == 2

    assert bytes(box) == bs.bytes


def test_dref_box():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24, uintbe:32",
              16, b"dref", 0, b"\x00\x00\x00", 1)

    box_header = Parser.parse_header(bs)
    dref = bx_def.DREF.parse_box(bs, box_header)
    box = dref

    assert box.header.start_pos == 0
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

    box_header = Parser.parse_header(bs)
    sample_entry_box = bx_def.SampleEntryBox.parse_box(bs, box_header)
    box = sample_entry_box

    assert box.header.start_pos == 0
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
              58, b"____",
              0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
              1,
              0x0, 0x0, 0x0, 0x0, 0x0,
              512, 512, 72, 0, 72, 0,
              0x0,
              1, b'\0' * 32, 24,
              -1)

    box_header = Parser.parse_header(bs)
    visual_sample_entry_box = bx_def.VisualSampleEntryBox.parse_box(bs, box_header)
    box = visual_sample_entry_box

    assert box.header.start_pos == 0
    assert box.header.type == b"____"
    assert box.header.box_size == 58

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
              58, b"avc1",
              0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
              1,
              0x0, 0x0, 0x0, 0x0, 0x0,
              512, 512, 72, 0, 72, 0,
              0x0,
              1, b'\0' * 32, 24,
              -1)

    box_header = Parser.parse_header(bs)
    avc1 = bx_def.AVC1.parse_box(bs, box_header)
    box = avc1

    assert box.header.start_pos == 0
    assert box.header.type == b"avc1"
    assert box.header.box_size == 58

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


def test_stxt_box():
    bs = pack("uintbe:32, bytes:4, "
              "uintbe:8, uintbe:8, uintbe:8, uintbe:8, uintbe:8, uintbe:8, "
              "uintbe:16, "
              "bytes:1, bytes:11",
              28, b"stxt",
              0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
              1,
              b'\0', b'text/plain\0')

    box_header = Parser.parse_header(bs)
    stxt = bx_def.STXT.parse_box(bs, box_header)
    box = stxt

    assert box.header.start_pos == 0
    assert box.header.type == b"stxt"
    assert box.header.box_size == 28

    assert box.data_reference_index == 1
    assert box.content_encoding == b'\0'
    assert box.mime_format == b'text/plain\0'

    assert len(box.boxes) == 0

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

    box_header = Parser.parse_header(bs)
    mett = bx_def.METT.parse_box(bs, box_header)
    box = mett

    assert box.header.start_pos == 0
    assert box.header.type == b"mett"
    assert box.header.box_size == 28

    assert box.data_reference_index == 1
    assert box.content_encoding == b'\0'
    assert box.mime_format == b'image/heif\0'

    assert len(box.boxes) == 0

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

    box_header = Parser.parse_header(bs)
    mett = bx_def.METT.parse_box(bs, box_header)
    box = mett

    assert box.header.start_pos == 0
    assert box.header.type == b"sbtt"
    assert box.header.box_size == 28

    assert box.data_reference_index == 1
    assert box.content_encoding == b'\0'
    assert box.mime_format == b'text/plain\0'

    assert len(box.boxes) == 0

    assert bytes(box) == bs.bytes


def test_url__box():
    bs = pack("uintbe:32, bytes:4, uintbe:8, bits:24",
              12, b"url ", 0, b"\x00\x00\x01")

    box_header = Parser.parse_header(bs)
    url_ = bx_def.URL_.parse_box(bs, box_header)
    box = url_

    assert box.header.start_pos == 0
    assert box.header.type == b"url "
    assert box.header.box_size == 12
    assert box.header.version == 0
    assert box.header.flags == b"\x00\x00\x01"

    assert box.location is None

    assert bytes(box) == bs.bytes


def test_pasp_box():
    bs = pack("uintbe:32, bytes:4, uintbe:32, uintbe:32",
              16, b"pasp", 150, 157)

    box_header = Parser.parse_header(bs)
    pasp = bx_def.PASP.parse_box(bs, box_header)
    box = pasp

    assert box.header.start_pos == 0
    assert box.header.type == b"pasp"
    assert box.header.box_size == 16

    assert box.h_spacing == 150
    assert box.v_spacing == 157
    assert bytes(box) == bs.bytes


def test_clap_box():
    bs = pack("uintbe:32, bytes:4, "
              "uintbe:32, uintbe:32, uintbe:32, uintbe:32, "
              "intbe:32, uintbe:32, intbe:32, uintbe:32",
              40, b"clap",
              500, 1, 333, 1,
              -12, 2, -179, 2)

    box_header = Parser.parse_header(bs)
    clap = bx_def.CLAP.parse_box(bs, box_header)
    box = clap

    assert box.header.start_pos == 0
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
    assert bytes(box) == bs.bytes
