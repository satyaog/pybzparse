from datetime import datetime

from bitstring import pack

import utils


def test_to_mp4_date():
    assert utils.to_mp4_time(datetime(2017, 12, 15, 16, 24, 10)) == 3596199850
    assert utils.to_mp4_time(datetime(1904, 1, 1, 0, 0)) == 0


def test_from_mp4_date():
    assert utils.from_mp4_time(3596199850) == datetime(2017, 12, 15, 16, 24, 10)
    assert utils.from_mp4_time(0) == datetime(1904, 1, 1, 0, 0)


def test_make_track():
    creation_time = utils.to_mp4_time(datetime(2019, 9, 15, 0, 0, 0))
    modification_time = utils.to_mp4_time(datetime(2019, 9, 16, 0, 0, 0))

    samples_sizes = [198297, 127477, 192476]
    samples_offsets = [10,
                       10 + sum(samples_sizes[0:1]),
                       10 + sum(samples_sizes[0:2])]
    trak = utils.make_track(creation_time, modification_time,
                            samples_sizes, samples_offsets)

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
    assert tkhd.duration == -1

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

    assert mdhd.header.type == b"mdhd"
    assert mdhd.header.version == 1
    assert mdhd.header.flags == b"\x00\x00\x00"

    assert mdhd.creation_time == creation_time
    assert mdhd.modification_time == modification_time
    assert mdhd.timescale == -1
    assert mdhd.duration == -1

    assert mdhd.language == [21, 14, 4]
    assert mdhd.pre_defined == 0

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
    assert stco.entries[0].chunk_offset == samples_offsets[0]
    assert stco.entries[1].chunk_offset == samples_offsets[1]
    assert stco.entries[2].chunk_offset == samples_offsets[2]

    assert bytes(stco) == pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
                               "uintbe:32, "
                               "uintbe:32, uintbe:32, uintbe:32",
                               28, b"stco", 0, b"\x00\x00\x00",
                               3,
                               samples_offsets[0], samples_offsets[1], samples_offsets[2])
