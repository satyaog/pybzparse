from datetime import datetime

from bitstring import pack

import utils


def test_to_mp4_date():
    assert utils.to_mp4_time(datetime(2017, 12, 15, 16, 24, 10)) == 3596199850
    assert utils.to_mp4_time(datetime(1904, 1, 1, 0, 0)) == 0


def test_from_mp4_date():
    assert utils.from_mp4_time(3596199850) == datetime(2017, 12, 15, 16, 24, 10)
    assert utils.from_mp4_time(0) == datetime(1904, 1, 1, 0, 0)


def test_make_mvhd():
    creation_time = utils.to_mp4_time(datetime(2019, 9, 15, 0, 0, 0))
    modification_time = utils.to_mp4_time(datetime(2019, 9, 16, 0, 0, 0))

    mvhd = utils.make_mvhd(creation_time, modification_time, 3)
    mvhd.refresh_box_size()

    assert mvhd.header.type == b"mvhd"
    assert mvhd.header.box_size == 120
    assert mvhd.header.version == 1
    assert mvhd.header.flags == b"\x00\x00\x00"

    assert mvhd.creation_time == creation_time
    assert mvhd.modification_time == modification_time
    assert mvhd.timescale == 20
    assert mvhd.duration == 60

    assert mvhd.rate == [1, 0]
    assert mvhd.volume == [0, 0]

    assert mvhd.matrix == [65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824]
    assert mvhd.pre_defined == [b"\x00" * 4] * 6

    assert mvhd.next_track_id == 1

    assert bytes(mvhd) == \
           pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
                "uintbe:64, uintbe:64, uintbe:32, uintbe:64, "
                "uintbe:16, uintbe:16, uintbe:8, uintbe:8, "
                "bits:16, bits:32, bits:32, "
                "uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, "
                "bits:32, bits:32, bits:32, bits:32, bits:32, bits:32, "
                "uintbe:32",
                120, b"mvhd", 1, b"\x00\x00\x00",
                creation_time, modification_time, 20, 60,
                1, 0, 0, 0,
                b"\x00" * 2, b"\x00" * 4, b"\x00" * 4,
                65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824,
                b"\x00" * 4, b"\x00" * 4, b"\x00" * 4, b"\x00" * 4, b"\x00" * 4, b"\x00" * 4,
                1)


def test_make_trak():
    creation_time = utils.to_mp4_time(datetime(2019, 9, 15, 0, 0, 0))
    modification_time = utils.to_mp4_time(datetime(2019, 9, 16, 0, 0, 0))

    samples_sizes = [198297, 127477, 192476]
    samples_offset = 10
    trak = utils.make_trak(creation_time, modification_time,
                           samples_sizes, samples_offset)

    assert trak.header.type == b"trak"
    assert len(trak.boxes) == 2

    # MOOV.TRAK.TKHD
    tkhd = trak.boxes[0]

    assert tkhd.header.type == b"tkhd"
    assert tkhd.header.version == 1
    assert tkhd.header.flags == b"\x00\x00\x00"

    assert tkhd.creation_time == creation_time
    assert tkhd.modification_time == modification_time
    assert tkhd.track_id == -1
    assert tkhd.duration == 60

    assert tkhd.layer == 0
    assert tkhd.alternate_group == 0
    assert tkhd.volume == [0, 0]

    assert tkhd.matrix == [65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824]

    assert tkhd.width == -1
    assert tkhd.height == -1

    assert tkhd.is_audio is False

    # MOOV.TRAK.MDIA
    mdia = trak.boxes[1]

    assert mdia.header.type == b"mdia"
    assert len(mdia.boxes) == 3

    # MOOV.TRAK.MDIA.MDHD
    mdhd = mdia.boxes[0]
    mdhd.refresh_box_size()

    assert mdhd.header.type == b"mdhd"
    assert mdhd.header.box_size == 44
    assert mdhd.header.version == 1
    assert mdhd.header.flags == b"\x00\x00\x00"

    assert mdhd.creation_time == creation_time
    assert mdhd.modification_time == modification_time
    assert mdhd.timescale == 20
    assert mdhd.duration == 60

    assert mdhd.language == [21, 14, 4]
    assert mdhd.pre_defined == 0

    assert bytes(mdhd) == \
           pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
                "uintbe:64, uintbe:64, uintbe:32, uintbe:64, "
                "bits:1, uint:5, uint:5, uint:5, "
                "bits:16",
                44, b"mdhd", 1, b"\x00\x00\x00",
                creation_time, modification_time, 20, 60,
                0x1, 21, 14, 4,
                b"\x00" * 2)

    # MOOV.TRAK.MDIA.HDLR
    hdlr = mdia.boxes[1]
    hdlr.refresh_box_size()

    assert hdlr.header.type == b"hdlr"
    assert hdlr.header.box_size == 33
    assert hdlr.header.version == 0
    assert hdlr.header.flags == b"\x00\x00\x00"
    assert hdlr.pre_defined == 0
    assert hdlr.handler_type == b"____"
    # TODO: validate the use of the name
    assert hdlr.name == b"\0"

    assert bytes(hdlr) == pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
                               "uintbe:32, bytes:4, "
                               "bits:32, bits:32, bits:32, "
                               "bytes:1",
                               33, b"hdlr", 0, b"\x00\x00\x00",
                               0, b"____",
                               b"\x00" * 4, b"\x00" * 4, b"\x00" * 4,
                               b"\0")

    # MOOV.TRAK.MDIA.MINF
    minf = mdia.boxes[2]

    assert minf.header.type == b"minf"
    assert len(minf.boxes) == 3

    # MOOV.TRAK.MDIA.MINF._MHD (placeholder)
    _mhd = minf.boxes[0]
    _mhd.refresh_box_size()

    assert _mhd.header.type == b"_mhd"
    assert _mhd.header.box_size == 8

    assert bytes(_mhd) == pack("uintbe:32, bytes:4", 8, b"_mhd")

    # MOOV.TRAK.MDIA.MINF.DINF
    dinf = minf.boxes[1]

    assert dinf.header.type == b"dinf"
    assert len(dinf.boxes) == 1

    # MOOV.TRAK.MDIA.MINF.DINF.DREF
    dref = dinf.boxes[0]

    assert dref.header.type == b"dref"
    assert dref.header.version == 0
    assert dref.header.flags == b"\x00\x00\x00"
    assert dref.entry_count == 1
    assert len(dref.boxes) == 1

    # MOOV.TRAK.MDIA.MINF.DINF.DREF.URL_
    url_ = dref.boxes[0]
    url_.refresh_box_size()

    assert url_.header.type == b"url "
    assert url_.header.box_size == 12
    assert url_.header.version == 0
    assert url_.header.flags == b"\x00\x00\x01"
    assert url_.location is None

    assert bytes(url_) == pack("uintbe:32, bytes:4, uintbe:8, bits:24",
                               12, b"url ", 0, b"\x00\x00\x01")

    # MOOV.TRAK.MDIA.MINF.STBL
    stbl = minf.boxes[2]

    assert stbl.header.type == b"stbl"
    assert len(stbl.boxes) == 5

    # MOOV.TRAK.MDIA.MINF.STBL.STSD
    stsd = stbl.boxes[0]
    stsd.refresh_box_size()

    assert stsd.header.type == b"stsd"
    assert stsd.header.box_size == 16
    assert stsd.header.version == 0
    assert stsd.header.flags == b"\x00\x00\x00"
    assert stsd.entry_count == 0

    assert bytes(stsd) == pack("uintbe:32, bytes:4, uintbe:8, bits:24, uintbe:32",
                               16, b"stsd", 0, b"\x00\x00\x00", 0)

    # MOOV.TRAK.MDIA.MINF.STBL.STTS
    stts = stbl.boxes[1]
    stts.refresh_box_size()

    assert stts.header.type == b"stts"
    assert stts.header.box_size == 24
    assert stts.header.version == 0
    assert stts.header.flags == b"\x00\x00\x00"
    assert stts.entry_count == 1
    assert len(stts.entries) == 1
    assert stts.entries[0].sample_count == 3
    assert stts.entries[0].sample_delta == 20

    assert bytes(stts) == pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
                               "uintbe:32, uintbe:32, uintbe:32",
                               24, b"stts", 0, b"\x00\x00\x00",
                               1, 3, 20)

    # MOOV.TRAK.MDIA.MINF.STBL.STSZ
    stsz = stbl.boxes[2]
    stsz.refresh_box_size()

    assert stsz.header.type == b"stsz"
    assert stsz.header.box_size == 32
    assert stsz.header.version == 0
    assert stsz.header.flags == b"\x00\x00\x00"
    assert stsz.sample_size == 0
    assert stsz.sample_count == 3
    assert len(stsz.samples) == 3
    assert stsz.samples[0].entry_size == samples_sizes[0]
    assert stsz.samples[1].entry_size == samples_sizes[1]
    assert stsz.samples[2].entry_size == samples_sizes[2]

    assert bytes(stsz) == pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
                               "uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32",
                               32, b"stsz", 0, b"\x00\x00\x00",
                               0, 3,
                               samples_sizes[0], samples_sizes[1], samples_sizes[2])

    # MOOV.TRAK.MDIA.MINF.STBL.STSC
    stsc = stbl.boxes[3]
    stsc.refresh_box_size()

    assert stsc.header.type == b"stsc"
    assert stsc.header.box_size == 28
    assert stsc.header.version == 0
    assert stsc.header.flags == b"\x00\x00\x00"
    assert stsc.entry_count == 1
    assert len(stsc.entries) == 1
    assert stsc.entries[0].first_chunk == 1
    assert stsc.entries[0].samples_per_chunk == 1
    assert stsc.entries[0].sample_description_index == 1

    assert bytes(stsc) == pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
                               "uintbe:32, "
                               "uintbe:32, uintbe:32, uintbe:32",
                               28, b"stsc", 0, b"\x00\x00\x00",
                               1,
                               1, 1, 1)

    # MOOV.TRAK.MDIA.MINF.STBL.STCO
    stco = stbl.boxes[4]
    stco.refresh_box_size()

    assert stco.header.type == b"stco"
    assert stco.header.box_size == 28
    assert stco.header.version == 0
    assert stco.header.flags == b"\x00\x00\x00"
    assert stco.entry_count == 3
    assert len(stco.entries) == 3
    assert stco.entries[0].chunk_offset == samples_offset
    assert stco.entries[1].chunk_offset == samples_offset + sum(samples_sizes[0:1])
    assert stco.entries[2].chunk_offset == samples_offset + sum(samples_sizes[0:2])

    assert bytes(stco) == pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
                               "uintbe:32, "
                               "uintbe:32, uintbe:32, uintbe:32",
                               28, b"stco", 0, b"\x00\x00\x00",
                               3,
                               samples_offset,
                               samples_offset + sum(samples_sizes[0:1]),
                               samples_offset + sum(samples_sizes[0:2]))


def test_make_meta_trak():
    creation_time = utils.to_mp4_time(datetime(2019, 9, 15, 0, 0, 0))
    modification_time = utils.to_mp4_time(datetime(2019, 9, 16, 0, 0, 0))

    samples_sizes = [198297, 127477, 192476]
    samples_offset = 10
    trak = utils.make_meta_trak(creation_time, modification_time, b"bzna_inputs\0",
                                samples_sizes, samples_offset)

    # MOOV.TRAK.MDIA.HDLR
    hdlr = trak.boxes[-1].boxes[1]
    hdlr.refresh_box_size()

    assert hdlr.header.type == b"hdlr"
    assert hdlr.header.box_size == 44
    assert hdlr.handler_type == b"meta"
    # TODO: validate the use of the name
    assert hdlr.name == b"bzna_inputs\0"

    assert bytes(hdlr) == \
           pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
                "uintbe:32, bytes:4, bits:32, bits:32, bits:32, "
                "bytes:12",
                44, b"hdlr", 0, b"\x00\x00\x00",
                0, b"meta", b"\x00" * 4, b"\x00" * 4, b"\x00" * 4,
                b"bzna_inputs\0")

    # MOOV.TRAK.MDIA.MINF.NMHD
    nmhd = trak.boxes[-1].boxes[-1].boxes[0]
    nmhd.refresh_box_size()

    assert nmhd.header.type == b"nmhd"
    assert nmhd.header.box_size == 12
    assert nmhd.header.version == 0
    assert nmhd.header.flags == b"\x00\x00\x00"

    assert bytes(nmhd) == pack("uintbe:32, bytes:4, uintbe:8, bits:24",
                               12, b"nmhd", 0, b"\x00\x00\x00")

    # MOOV.TRAK.MDIA.MINF.STBL.STSD
    stsd = trak.boxes[-1].boxes[-1].boxes[-1].boxes[0]

    assert stsd.header.type == b"stsd"
    assert len(stsd.boxes) == 1

    # MOOV.TRAK.MDIA.MINF.STBL.STSD.METT
    mett = stsd.boxes[0]
    mett.refresh_box_size()

    assert mett.header.type == b"mett"
    assert mett.header.box_size == 18
    assert mett.data_reference_index == 1
    assert mett.content_encoding == b'\0'
    assert mett.mime_format == b'\0'
    assert len(mett.boxes) == 0


def test_make_text_trak():
    creation_time = utils.to_mp4_time(datetime(2019, 9, 15, 0, 0, 0))
    modification_time = utils.to_mp4_time(datetime(2019, 9, 16, 0, 0, 0))

    samples_sizes = [198297, 127477, 192476]
    samples_offset = 10
    trak = utils.make_text_trak(creation_time, modification_time, b"bzna_fnames\0",
                                samples_sizes, samples_offset)

    # MOOV.TRAK.MDIA.HDLR
    hdlr = trak.boxes[-1].boxes[1]
    hdlr.refresh_box_size()

    assert hdlr.header.type == b"hdlr"
    assert hdlr.header.box_size == 44
    assert hdlr.handler_type == b"text"
    # TODO: validate the use of the name
    assert hdlr.name == b"bzna_fnames\0"

    assert bytes(hdlr) == \
           pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
                "uintbe:32, bytes:4, bits:32, bits:32, bits:32, "
                "bytes:12",
                44, b"hdlr", 0, b"\x00\x00\x00",
                0, b"text", b"\x00" * 4, b"\x00" * 4, b"\x00" * 4,
                b"bzna_fnames\0")

    # MOOV.TRAK.MDIA.MINF.NMHD
    nmhd = trak.boxes[-1].boxes[-1].boxes[0]
    nmhd.refresh_box_size()

    assert nmhd.header.type == b"nmhd"
    assert nmhd.header.box_size == 12
    assert nmhd.header.version == 0
    assert nmhd.header.flags == b"\x00\x00\x00"

    assert bytes(nmhd) == pack("uintbe:32, bytes:4, uintbe:8, bits:24",
                               12, b"nmhd", 0, b"\x00\x00\x00")

    # MOOV.TRAK.MDIA.MINF.STBL.STSD
    stsd = trak.boxes[-1].boxes[-1].boxes[-1].boxes[0]

    assert stsd.header.type == b"stsd"
    assert len(stsd.boxes) == 1

    # MOOV.TRAK.MDIA.MINF.STBL.STSD.STXT
    stxt = stsd.boxes[0]
    stxt.refresh_box_size()

    assert stxt.header.type == b"stxt"
    assert stxt.header.box_size == 28
    assert stxt.data_reference_index == 1
    assert stxt.content_encoding == b'\0'
    assert stxt.mime_format == b'text/plain\0'
    assert len(stxt.boxes) == 0


def test_make_vide_trak():
    creation_time = utils.to_mp4_time(datetime(2019, 9, 15, 0, 0, 0))
    modification_time = utils.to_mp4_time(datetime(2019, 9, 16, 0, 0, 0))

    samples_sizes = [198297, 127477, 192476]
    samples_offset = 10
    trak = utils.make_vide_trak(creation_time, modification_time, b"VideoHandler\0",
                                samples_sizes, samples_offset)

    # MOOV.TRAK.MDIA.HDLR
    hdlr = trak.boxes[-1].boxes[1]
    hdlr.refresh_box_size()

    assert hdlr.header.type == b"hdlr"
    assert hdlr.header.box_size == 45
    assert hdlr.handler_type == b"vide"
    # TODO: validate the use of the name
    assert hdlr.name == b"VideoHandler\0"

    assert bytes(hdlr) == \
           pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
                "uintbe:32, bytes:4, bits:32, bits:32, bits:32, "
                "bytes:13",
                45, b"hdlr", 0, b"\x00\x00\x00",
                0, b"vide", b"\x00" * 4, b"\x00" * 4, b"\x00" * 4,
                b"VideoHandler\0")

    # MOOV.TRAK.MDIA.MINF.VMHD
    vmhd = trak.boxes[-1].boxes[-1].boxes[0]
    vmhd.refresh_box_size()

    assert vmhd.header.type == b"vmhd"
    assert vmhd.header.box_size == 20
    assert vmhd.header.version == 0
    assert vmhd.header.flags == b"\x00\x00\x01"
    assert vmhd.graphicsmode == 0
    assert vmhd.opcolor == [0, 0, 0]

    assert bytes(vmhd) == pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
                               "uintbe:16, uintbe:16, uintbe:16, uintbe:16",
                               20, b"vmhd", 0, b"\x00\x00\x01",
                               0, 0, 0, 0)

    # MOOV.TRAK.MDIA.MINF.STBL.STSD
    stsd = trak.boxes[-1].boxes[-1].boxes[-1].boxes[0]

    assert stsd.header.type == b"stsd"
    assert len(stsd.boxes) == 1

    # MOOV.TRAK.MDIA.MINF.STBL.STSD.AVC1
    avc1 = stsd.boxes[0]

    assert avc1.header.type == b"avc1"
    assert avc1.data_reference_index == 1
    assert avc1.width == -1
    assert avc1.height == -1
    assert avc1.horizresolution == [72, 0]
    assert avc1.vertresolution == [72, 0]
    assert avc1.frame_count == 1
    assert avc1.compressorname == b'\0' * 32
    assert avc1.depth == 24
    assert len(avc1.boxes) == 2

    # MOOV.TRAK.MDIA.MINF.STBL.STSD.AVC1.AVCC
    avcC = avc1.boxes[0]
    avcC.refresh_box_size()

    assert avcC.header.type == b"avcC"
    assert avcC.header.box_size == 53
    assert avcC.payload == b'\x01d\x10\x16\xff\xe1\x00\x1bgd\x10\x16\xac\xb8' \
                           b'\x10\x02\r\xff\x80K\x00N\xb6\xa5\x00\x00\x03\x00' \
                           b'\x01\x00\x00\x03\x00\x02\x04\x01\x00\x07h\xee\x01' \
                           b'\x9cL\x84\xc0'

    # MOOV.TRAK.MDIA.MINF.STBL.STSD.AVC1.PASP
    pasp = avc1.boxes[1]
    pasp.refresh_box_size()

    assert pasp.header.type == b"pasp"
    assert pasp.header.box_size == 16
    assert pasp.h_spacing == 1
    assert pasp.v_spacing == 1
