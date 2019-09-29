from datetime import datetime

from bitstring import ConstBitStream, pack

import boxes as bx_def
import headers
import fields_lists as flists
from pybzparse import Parser
from utils import from_mp4_time, to_mp4_time


def _make_track(creation_time, modification_time,
                track_header, handler_reference, type_media_header,
                sample_descriptions, samples_sizes, samples_offsets):
    # MOOV.TRAK
    trak = bx_def.TRAK(headers.BoxHeader())
    trak.header.type = b"trak"

    trak.append(track_header)

    # # MOOV.TRAK.EDTS
    # edts = bx_def.EDTS(headers.BoxHeader())
    # edts.header.type = b"edts"
    #
    # # MOOV.TRAK.EDTS.ELST
    # elst = bx_def.ELST(headers.FullBoxHeader())
    #
    # elst.header.type = b"elst"
    # elst.header.version = (1,)
    # elst.header.flags = (b"\x00\x00\x00",)
    #
    # entry = elst.append_and_return()
    # entry.segment_duration = (60,)
    # entry.media_time = (0,)
    # entry.media_rate_integer = (1,)
    # entry.media_rate_fraction = (0,)
    #
    # elst.refresh_box_size()
    #
    # assert elst.header.type == b"elst"
    # assert elst.header.box_size == 36
    # assert elst.header.version == 1
    # assert elst.header.flags == b"\x00\x00\x00"
    #
    # assert elst.entry_count == 1
    # assert len(elst.entries) == 1
    # assert elst.entries[0].segment_duration == 60
    # assert elst.entries[0].media_time == 0
    # assert elst.entries[0].media_rate_integer == 1
    # assert elst.entries[0].media_rate_fraction == 0
    #
    # assert bytes(elst) == \
    #        pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
    #             "uintbe:32, uintbe:64, uintbe:64, uintbe:16, uintbe:16",
    #             36, b"elst", 1, b"\x00\x00\x00",
    #             1, 60, 0, 1, 0)
    #
    # edts.append(elst)
    #
    # edts.refresh_box_size()
    #
    # assert edts.header.type == b"edts"
    # assert edts.header.box_size == 8 + 36
    # assert len(edts.boxes) == 1
    #
    # trak.append(edts)

    # MOOV.TRAK.MDIA
    mdia = bx_def.MDIA(headers.BoxHeader())
    mdia.header.type = b"mdia"

    # MOOV.TRAK.MDIA.MDHD
    mdhd = bx_def.MDHD(headers.FullBoxHeader())

    mdhd.header.type = b"mdhd"
    mdhd.header.version = (1,)
    mdhd.header.flags = (b"\x00\x00\x00",)

    mdhd.creation_time = (creation_time,)
    mdhd.modification_time = (modification_time,)
    mdhd.timescale = (20,)
    mdhd.duration = (60,)

    # TODO: check the language code
    mdhd.language = ([21, 14, 4],)
    mdhd.pre_defined = (0,)

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

    mdia.append(mdhd)

    mdia.append(handler_reference)

    # MOOV.TRAK.MDIA.MINF
    minf = bx_def.MINF(headers.BoxHeader())
    minf.header.type = b"minf"

    minf.append(type_media_header)

    # MOOV.TRAK.MDIA.MINF.DINF
    dinf = bx_def.DINF(headers.BoxHeader())
    dinf.header.type = b"dinf"

    # MOOV.TRAK.MDIA.MINF.DINF.DREF
    dref = bx_def.DREF(headers.FullBoxHeader())
    dref.header.type = b"dref"
    dref.header.version = (0,)
    dref.header.flags = (b"\x00\x00\x00",)

    # MOOV.TRAK.MDIA.MINF.DINF.DREF.URL_
    url_ = bx_def.URL_(headers.FullBoxHeader())

    url_.header.type = b"url "
    url_.header.version = (0,)
    # TODO:  validate that this flags means that the data is in the same file
    url_.header.flags = (b"\x00\x00\x01",)

    url_.refresh_box_size()

    assert url_.header.type == b"url "
    assert url_.header.box_size == 12
    assert url_.header.version == 0
    assert url_.header.flags == b"\x00\x00\x01"
    assert url_.location is None

    assert bytes(url_) == pack("uintbe:32, bytes:4, uintbe:8, bits:24",
                               12, b"url ", 0, b"\x00\x00\x01")

    dref.append(url_)

    dref.refresh_box_size()

    assert dref.header.type == b"dref"
    assert dref.header.box_size == 12 + 16
    assert dref.header.version == 0
    assert dref.header.flags == b"\x00\x00\x00"
    assert dref.entry_count == 1
    assert len(dref.boxes) == 1

    dinf.append(dref)

    dinf.refresh_box_size()

    assert dinf.header.type == b"dinf"
    assert dinf.header.box_size == 8 + 28
    assert len(dinf.boxes) == 1

    minf.append(dinf)

    # MOOV.TRAK.MDIA.MINF.STBL
    stbl = bx_def.STBL(headers.BoxHeader())
    stbl.header.type = b"stbl"

    if sample_descriptions is not None:
        stbl.append(sample_descriptions)

    # MOOV.TRAK.MDIA.MINF.STBL.STTS
    stts = bx_def.STTS(headers.FullBoxHeader())

    stts.header.type = b"stts"
    stts.header.version = (0,)
    stts.header.flags = (b"\x00\x00\x00",)

    entry = stts.append_and_return()
    # imges count
    entry.sample_count = (3,)
    # 1 img / sec
    entry.sample_delta = (20,)

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

    stbl.append(stts)

    # MOOV.TRAK.MDIA.MINF.STBL.STSZ
    stsz = bx_def.STSZ(headers.FullBoxHeader())

    stsz.header.type = b"stsz"
    stsz.header.version = (0,)
    stsz.header.flags = (b"\x00\x00\x00",)

    stsz.sample_size = (0,)

    sample = stsz.append_and_return()
    sample.entry_size = (samples_sizes[0],)
    sample = stsz.append_and_return()
    sample.entry_size = (samples_sizes[1],)
    sample = stsz.append_and_return()
    sample.entry_size = (samples_sizes[2],)

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

    stbl.append(stsz)

    # MOOV.TRAK.MDIA.MINF.STBL.STSC
    stsc = bx_def.STSC(headers.FullBoxHeader())

    stsc.header.type = b"stsc"
    stsc.header.version = (0,)
    stsc.header.flags = (b"\x00\x00\x00",)

    entry = stsc.append_and_return()
    entry.first_chunk = (1,)
    entry.samples_per_chunk = (1,)
    entry.sample_description_index = (1 if sample_descriptions else 0,)

    stsc.refresh_box_size()

    assert stsc.header.type == b"stsc"
    assert stsc.header.box_size == 28
    assert stsc.header.version == 0
    assert stsc.header.flags == b"\x00\x00\x00"
    assert stsc.entry_count == 1
    assert len(stsc.entries) == 1
    assert stsc.entries[0].first_chunk == 1
    assert stsc.entries[0].samples_per_chunk == 1
    assert stsc.entries[0].sample_description_index == \
           (1 if sample_descriptions else 0)

    assert bytes(stsc) == pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
                               "uintbe:32, "
                               "uintbe:32, uintbe:32, uintbe:32",
                               28, b"stsc", 0, b"\x00\x00\x00",
                               1,
                               1, 1, (1 if sample_descriptions else 0))

    stbl.append(stsc)

    # MOOV.TRAK.MDIA.MINF.STBL.STCO
    stco = bx_def.STCO(headers.FullBoxHeader())

    stco.header.type = b"stco"
    stco.header.version = (0,)
    stco.header.flags = (b"\x00\x00\x00",)

    entry = stco.append_and_return()
    entry.chunk_offset = (samples_offsets[0],)
    entry = stco.append_and_return()
    entry.chunk_offset = (samples_offsets[1],)
    entry = stco.append_and_return()
    entry.chunk_offset = (samples_offsets[2],)

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

    stbl.append(stco)

    stbl.refresh_box_size()

    assert stbl.header.type == b"stbl"
    assert len(stbl.boxes) == 5 if sample_descriptions else 4

    minf.append(stbl)

    minf.refresh_box_size()

    assert minf.header.type == b"minf"
    assert len(minf.boxes) == 3

    mdia.append(minf)

    mdia.refresh_box_size()

    assert mdia.header.type == b"mdia"
    assert len(mdia.boxes) == 3

    trak.append(mdia)

    trak.refresh_box_size()

    assert trak.header.type == b"trak"
    assert len(trak.boxes) == 2

    return trak


def test_mp4_dataset():
    creation_time = to_mp4_time(datetime(2019, 9, 15, 0, 0, 0))
    modification_time = to_mp4_time(datetime(2019, 9, 16, 0, 0, 0))

    # FTYP
    ftyp = bx_def.FTYP(headers.BoxHeader())
    ftyp.header.type = b"ftyp"
    ftyp.major_brand = (1652190817,)            # b"bzna"
    ftyp.minor_version = (0,)
    ftyp.compatible_brands = ([1836069937],)    # b"mp41"

    ftyp.refresh_box_size()

    assert ftyp.header.type == b"ftyp"
    assert ftyp.header.box_size == 20
    assert ftyp.major_brand == 1652190817           # b"bzna"
    assert ftyp.minor_version == 0
    assert ftyp.compatible_brands == [1836069937]   # b"mp41"
    assert bytes(ftyp) == pack("uintbe:32, bytes:4, bytes:4, uintbe:32, "
                               "bytes:4",
                               20, b"ftyp", b"bzna", 0,
                               b"mp41")

    # MDAT
    mdat = bx_def.MDAT(headers.BoxHeader())
    mdat.header.type = b"mdat"

    data = []

    with open("data/small_vid_mdat_im0", "rb") as f:
        data.append(f.read())
    with open("data/small_vid_mdat_im1", "rb") as f:
        data.append(f.read())
    with open("data/small_vid_mdat_im2", "rb") as f:
        data.append(f.read())

    data.append(b"/path/image_1_name.JPEG")
    data.append(b"/path/image_2_name.JPEG")
    data.append(b"/path/image_3_name.JPEG")

    data.append((0).to_bytes(8, byteorder="little"))
    data.append((1).to_bytes(8, byteorder="little"))
    data.append((0).to_bytes(8, byteorder="little"))

    mdat.data = (b''.join(data),)

    mdat.refresh_box_size()

    assert mdat.header.type == b"mdat"
    assert mdat.header.box_size == 8 + sum(len(entry) for entry in data)

    # MOOV
    moov = bx_def.MOOV(headers.BoxHeader())
    moov.header.type = b"moov"

    # MOOV.MVHD
    mvhd = bx_def.MVHD(headers.FullBoxHeader())

    mvhd.header.type = b"mvhd"
    mvhd.header.version = (1,)
    mvhd.header.flags = (b"\x00\x00\x00",)

    mvhd.creation_time = (creation_time,)
    mvhd.modification_time = (modification_time,)
    # TODO: 20 units / second (does not necessary means 20 img / sec)
    mvhd.timescale = (20,)
    # total duration in the indicated timescale
    mvhd.duration = (60,)

    # prefered play rate (1x, 2x, 1/2x, ...)
    mvhd.rate = ([1, 0],)
    # prefered volume (1 is full volume)
    mvhd.volume = ([0, 0],)

    # TODO: validate matrix (and check if those are 16.16 floats)
    mvhd.matrix = ([65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824],)
    # TODO: check what pre_defined is
    mvhd.pre_defined = ([b"\x00" * 4] * 6,)

    # == total number of tracks
    mvhd.next_track_id = (4,)

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

    assert mvhd.next_track_id == 4

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
                4)

    moov.append(mvhd)

    # MOOV.TRAK.TKHD
    tkhd = bx_def.TKHD(headers.FullBoxHeader())

    tkhd.header.type = b"tkhd"
    tkhd.header.version = (1,)
    # "\x00\x00\x01" trak is enabled
    # "\x00\x00\x02" trak is used in the presentation
    # "\x00\x00\x04" trak is used in the preview
    # "\x00\x00\x08" trak size in not in pixel but in aspect ratio
    tkhd.header.flags = (b"\x00\x00\x03",)

    tkhd.creation_time = (creation_time,)
    tkhd.modification_time = (modification_time,)
    tkhd.track_id = (1,)
    tkhd.duration = (60,)

    tkhd.layer = (0,)
    tkhd.alternate_group = (0,)
    tkhd.volume = ([0, 0],)

    # TODO: validate matrix (and check if those are 16.16 floats)
    tkhd.matrix = ([65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824],)

    # TODO: make sure that this is the canvas size
    tkhd.width = ([512, 0],)
    tkhd.height = ([512, 0],)

    tkhd.refresh_box_size()

    assert tkhd.header.type == b"tkhd"
    assert tkhd.header.box_size == 104
    assert tkhd.header.version == 1
    assert tkhd.header.flags == b"\x00\x00\x03"

    assert tkhd.creation_time == creation_time
    assert tkhd.modification_time == modification_time
    assert tkhd.track_id == 1
    assert tkhd.duration == 60

    assert tkhd.layer == 0
    assert tkhd.alternate_group == 0
    assert tkhd.volume == [0, 0]

    assert tkhd.matrix == [65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824]

    assert tkhd.width == 512
    assert tkhd.height == 512

    assert tkhd.is_audio is False

    assert bytes(tkhd) == \
           pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
                "uintbe:64, uintbe:64, uintbe:32, "
                "bits:32, "
                "uintbe:64, "
                "bits:32, bits:32, "
                "uintbe:16, uintbe:16, uintbe:8, uintbe:8, "
                "bits:16, "
                "uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, "
                "uintbe:16, uintbe:16, uintbe:16, uintbe:16",
                104, b"tkhd", 1, b"\x00\x00\x03",
                creation_time, modification_time, 1,
                b"\x00" * 4,
                60,
                b"\x00" * 4, b"\x00" * 4,
                0, 0, 0, 0,
                b"\x00" * 2,
                65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824,
                512, 0, 512, 0)

    # MOOV.TRAK.MDIA.HDLR
    hdlr = bx_def.HDLR(headers.FullBoxHeader())

    hdlr.header.type = b"hdlr"
    hdlr.header.version = (0,)
    hdlr.header.flags = (b"\x00\x00\x00",)
    hdlr.pre_defined = (0,)
    hdlr.handler_type = (b"vide",)
    hdlr.name = (b"Benzina_inputs\0",)

    hdlr.refresh_box_size()

    assert hdlr.header.type == b"hdlr"
    assert hdlr.header.box_size == 32 + len(b"Benzina_inputs\0")
    assert hdlr.header.version == 0
    assert hdlr.header.flags == b"\x00\x00\x00"
    assert hdlr.pre_defined == 0
    assert hdlr.handler_type == b"vide"
    # TODO: validate the use of the name
    assert hdlr.name == b"Benzina_inputs\0"

    assert bytes(hdlr)[4:] == \
           pack("bytes:4, uintbe:8, bits:24, "
                "uintbe:32, bytes:4, bits:32, bits:32, bits:32",
                b"hdlr", 0, b"\x00\x00\x00",
                0, b"vide", b"\x00" * 4, b"\x00" * 4, b"\x00" * 4).bytes + \
           b"Benzina_inputs\0"

    # MOOV.TRAK.MDIA.MINF.VMHD
    vmhd = bx_def.VMHD(headers.FullBoxHeader())

    vmhd.header.type = b"vmhd"
    vmhd.header.version = (0,)
    # flag is 1
    vmhd.header.flags = (b"\x00\x00\x01",)
    vmhd.graphicsmode = (0,)
    vmhd.opcolor = ([0, 0, 0],)

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
    stsd = bx_def.STSD(headers.FullBoxHeader())

    stsd.header.type = b"stsd"
    stsd.header.version = (0,)
    stsd.header.flags = (b"\x00\x00\x00",)

    # MOOV.TRAK.MDIA.MINF.STBL.STSD.AVC1
    avc1 = bx_def.AVC1(headers.BoxHeader())

    avc1.header.type = b"avc1"
    avc1.data_reference_index = (1,)
    avc1.width = (512,)
    avc1.height = (512,)
    avc1.horizresolution = ([72, 0],)
    avc1.vertresolution = ([72, 0],)
    avc1.frame_count = (1,)
    avc1.compressorname = (b'\0' * 32,)
    avc1.depth = (24,)

    # TODO: implement MOOV.TRAK.MDIA.MINF.STBL.STSD.AVC1.AVCC
    avcC = bx_def.UnknownBox(headers.BoxHeader())
    avcC.header.type = b"avcC"
    avcC.payload = b'\x01d\x10\x16\xff\xe1\x00\x1bgd\x10\x16\xac\xb8\x10\x02' \
                   b'\r\xff\x80K\x00N\xb6\xa5\x00\x00\x03\x00\x01\x00\x00\x03' \
                   b'\x00\x02\x04\x01\x00\x07h\xee\x01\x9cL\x84\xc0'

    avcC.refresh_box_size()

    assert avcC.header.type == b"avcC"
    assert avcC.header.box_size == 53

    avc1.append(avcC)

    # TODO: implement MOOV.TRAK.MDIA.MINF.STBL.STSD.AVC1.PASP
    pasp = bx_def.UnknownBox(headers.BoxHeader())
    pasp.header.type = b"pasp"
    pasp.payload = b'\x00\x00\x00\x96\x00\x00\x00\x9d'

    pasp.refresh_box_size()

    assert pasp.header.type == b"pasp"
    assert pasp.header.box_size == 16

    avc1.append(pasp)

    avc1.refresh_box_size()

    assert avc1.header.type == b"avc1"
    assert avc1.header.box_size == 86 + 53 + 16

    stsd.append(avc1)

    stsd.refresh_box_size()

    assert stsd.header.type == b"stsd"
    assert stsd.header.box_size == 16 + 155
    assert len(stsd.boxes) == 1

    # MOOV.TRAK
    offset = ftyp.header.box_size + mdat.header.header_size
    sizes = [198297, 127477, 192476]
    trak = _make_track(creation_time, modification_time,
                       tkhd, hdlr, vmhd, stsd,
                       sizes, [offset,
                               offset + sum(sizes[0:1]),
                               offset + sum(sizes[0:2])])

    moov.append(trak)

    # MOOV.TRAK.TKHD
    tkhd = bx_def.TKHD(headers.FullBoxHeader())

    tkhd.header.type = b"tkhd"
    tkhd.header.version = (1,)
    # "\x00\x00\x01" trak is enabled
    # "\x00\x00\x02" trak is used in the presentation
    # "\x00\x00\x04" trak is used in the preview
    # "\x00\x00\x08" trak size in not in pixel but in aspect ratio
    tkhd.header.flags = (b"\x00\x00\x00",)

    tkhd.creation_time = (creation_time,)
    tkhd.modification_time = (modification_time,)
    tkhd.track_id = (2,)
    tkhd.duration = (60,)

    tkhd.layer = (0,)
    tkhd.alternate_group = (0,)
    tkhd.volume = ([0, 0],)

    # TODO: validate matrix (and check if those are 16.16 floats)
    tkhd.matrix = ([65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824],)

    # TODO: make sure that this is the canvas size
    tkhd.width = ([0, 0],)
    tkhd.height = ([0, 0],)

    tkhd.refresh_box_size()

    assert tkhd.header.type == b"tkhd"
    assert tkhd.header.box_size == 104
    assert tkhd.header.version == 1
    assert tkhd.header.flags == b"\x00\x00\x00"

    assert tkhd.creation_time == creation_time
    assert tkhd.modification_time == modification_time
    assert tkhd.track_id == 2
    assert tkhd.duration == 60

    assert tkhd.layer == 0
    assert tkhd.alternate_group == 0
    assert tkhd.volume == [0, 0]

    assert tkhd.matrix == [65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824]

    assert tkhd.width == 0
    assert tkhd.height == 0

    assert tkhd.is_audio is False

    assert bytes(tkhd) == \
           pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
                "uintbe:64, uintbe:64, uintbe:32, "
                "bits:32, "
                "uintbe:64, "
                "bits:32, bits:32, "
                "uintbe:16, uintbe:16, uintbe:8, uintbe:8, "
                "bits:16, "
                "uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, "
                "uintbe:16, uintbe:16, uintbe:16, uintbe:16",
                104, b"tkhd", 1, b"\x00\x00\x00",
                creation_time, modification_time, 2,
                b"\x00" * 4,
                60,
                b"\x00" * 4, b"\x00" * 4,
                0, 0, 0, 0,
                b"\x00" * 2,
                65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824,
                0, 0, 0, 0)

    # MOOV.TRAK.MDIA.HDLR
    hdlr = bx_def.HDLR(headers.FullBoxHeader())

    hdlr.header.type = b"hdlr"
    hdlr.header.version = (0,)
    hdlr.header.flags = (b"\x00\x00\x00",)
    hdlr.pre_defined = (0,)
    hdlr.handler_type = (b"text",)
    hdlr.name = (b"Benzina_fnames\0",)

    hdlr.refresh_box_size()

    assert hdlr.header.type == b"hdlr"
    assert hdlr.header.box_size == 32 + len(b"Benzina_fnames\0")
    assert hdlr.header.version == 0
    assert hdlr.header.flags == b"\x00\x00\x00"
    assert hdlr.pre_defined == 0
    assert hdlr.handler_type == b"text"
    # TODO: validate the use of the name
    assert hdlr.name == b"Benzina_fnames\0"

    assert bytes(hdlr)[4:] == \
           pack("bytes:4, uintbe:8, bits:24, "
                "uintbe:32, bytes:4, bits:32, bits:32, bits:32",
                b"hdlr", 0, b"\x00\x00\x00",
                0, b"text", b"\x00" * 4, b"\x00" * 4, b"\x00" * 4).bytes + \
           b"Benzina_fnames\0"

    # MOOV.TRAK.MDIA.MINF.NMHD
    nmhd = bx_def.NMHD(headers.FullBoxHeader())

    nmhd.header.type = b"nmhd"
    nmhd.header.version = (0,)
    nmhd.header.flags = (b"\x00\x00\x00",)

    nmhd.refresh_box_size()

    assert nmhd.header.type == b"nmhd"
    assert nmhd.header.box_size == 12
    assert nmhd.header.version == 0
    assert nmhd.header.flags == b"\x00\x00\x00"

    assert bytes(nmhd) == pack("uintbe:32, bytes:4, uintbe:8, bits:24",
                               12, b"nmhd", 0, b"\x00\x00\x00")

    # MOOV.TRAK
    offset += sum(sizes)
    sizes = [23, 23, 23]
    trak = _make_track(creation_time, modification_time,
                       tkhd, hdlr, nmhd, None,
                       sizes, [offset,
                               offset + sum(sizes[0:1]),
                               offset + sum(sizes[0:2])])

    moov.append(trak)

    # MOOV.TRAK.TKHD
    tkhd = bx_def.TKHD(headers.FullBoxHeader())

    tkhd.header.type = b"tkhd"
    tkhd.header.version = (1,)
    # "\x00\x00\x01" trak is enabled
    # "\x00\x00\x02" trak is used in the presentation
    # "\x00\x00\x04" trak is used in the preview
    # "\x00\x00\x08" trak size in not in pixel but in aspect ratio
    tkhd.header.flags = (b"\x00\x00\x00",)

    tkhd.creation_time = (creation_time,)
    tkhd.modification_time = (modification_time,)
    tkhd.track_id = (3,)
    tkhd.duration = (60,)

    tkhd.layer = (0,)
    tkhd.alternate_group = (0,)
    tkhd.volume = ([0, 0],)

    # TODO: validate matrix (and check if those are 16.16 floats)
    tkhd.matrix = ([65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824],)

    # TODO: make sure that this is the canvas size
    tkhd.width = ([0, 0],)
    tkhd.height = ([0, 0],)

    tkhd.refresh_box_size()

    assert tkhd.header.type == b"tkhd"
    assert tkhd.header.box_size == 104
    assert tkhd.header.version == 1
    assert tkhd.header.flags == b"\x00\x00\x00"

    assert tkhd.creation_time == creation_time
    assert tkhd.modification_time == modification_time
    assert tkhd.track_id == 3
    assert tkhd.duration == 60

    assert tkhd.layer == 0
    assert tkhd.alternate_group == 0
    assert tkhd.volume == [0, 0]

    assert tkhd.matrix == [65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824]

    assert tkhd.width == 0
    assert tkhd.height == 0

    assert tkhd.is_audio is False

    assert bytes(tkhd) == \
           pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
                "uintbe:64, uintbe:64, uintbe:32, "
                "bits:32, "
                "uintbe:64, "
                "bits:32, bits:32, "
                "uintbe:16, uintbe:16, uintbe:8, uintbe:8, "
                "bits:16, "
                "uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, "
                "uintbe:16, uintbe:16, uintbe:16, uintbe:16",
                104, b"tkhd", 1, b"\x00\x00\x00",
                creation_time, modification_time, 3,
                b"\x00" * 4,
                60,
                b"\x00" * 4, b"\x00" * 4,
                0, 0, 0, 0,
                b"\x00" * 2,
                65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824,
                0, 0, 0, 0)

    # MOOV.TRAK.MDIA.HDLR
    hdlr = bx_def.HDLR(headers.FullBoxHeader())

    hdlr.header.type = b"hdlr"
    hdlr.header.version = (0,)
    hdlr.header.flags = (b"\x00\x00\x00",)
    hdlr.pre_defined = (0,)
    hdlr.handler_type = (b"text",)
    hdlr.name = (b"Benzina_targets\0",)

    hdlr.refresh_box_size()

    assert hdlr.header.type == b"hdlr"
    assert hdlr.header.box_size == 32 + len(b"Benzina_targets\0")
    assert hdlr.header.version == 0
    assert hdlr.header.flags == b"\x00\x00\x00"
    assert hdlr.pre_defined == 0
    assert hdlr.handler_type == b"text"
    # TODO: validate the use of the name
    assert hdlr.name == b"Benzina_targets\0"

    assert bytes(hdlr)[4:] == \
           pack("bytes:4, uintbe:8, bits:24, "
                "uintbe:32, bytes:4, bits:32, bits:32, bits:32",
                b"hdlr", 0, b"\x00\x00\x00",
                0, b"text", b"\x00" * 4, b"\x00" * 4, b"\x00" * 4).bytes + \
           b"Benzina_targets\0"

    # MOOV.TRAK
    offset += sum(sizes)
    sizes = [8, 8, 8]
    trak = _make_track(creation_time, modification_time,
                       tkhd, hdlr, nmhd, None,
                       sizes, [offset,
                               offset + sum(sizes[0:1]),
                               offset + sum(sizes[0:2])])

    moov.append(trak)

    moov.refresh_box_size()

    assert mvhd.next_track_id == len(moov.boxes)

    assert moov.header.type == b"moov"
    assert len(moov.boxes) == 4

    mp4_bytes = b''.join([bytes(ftyp), bytes(mdat), bytes(moov)])

    for box in moov.boxes:
        if isinstance(box, bx_def.TRAK):
            mdia = box.boxes[1]
        else:
            continue

        # trak.mdia.tkhd.name == b"Benzina_inputs\0"
        if mdia.boxes[1].name == b"Benzina_inputs\0":
            pass
        # trak.mdia.tkhd.name == b"Benzina_names\0"
        elif mdia.boxes[1].name == b"Benzina_fnames\0":
            # trak.mdia.minf.stbl.stsz
            stsz = mdia.boxes[2].boxes[2].boxes[1]
            # trak.mdia.minf.stbl.stco
            stco = mdia.boxes[2].boxes[2].boxes[3]
            for i, (sample, entry) in enumerate(zip(stsz.samples, stco.entries)):
                sample_end = entry.chunk_offset + sample.entry_size
                if i == 0:
                    assert mp4_bytes[entry.chunk_offset:sample_end] == \
                           b"/path/image_1_name.JPEG"
                elif i == 1:
                    assert mp4_bytes[entry.chunk_offset:sample_end] == \
                           b"/path/image_2_name.JPEG"
                elif i == 2:
                    assert mp4_bytes[entry.chunk_offset:sample_end] == \
                           b"/path/image_3_name.JPEG"
        # trak.mdia.tkhd.name == b"Benzina_targets\0"
        elif mdia.boxes[1].name == b"Benzina_targets\0":
            # trak.mdia.minf.stbl.stsz
            stsz = mdia.boxes[2].boxes[2].boxes[1]
            # trak.mdia.minf.stbl.stco
            stco = mdia.boxes[2].boxes[2].boxes[3]
            for i, (sample, entry) in enumerate(zip(stsz.samples, stco.entries)):
                sample_end = entry.chunk_offset + sample.entry_size
                if i == 0:
                    assert mp4_bytes[entry.chunk_offset:sample_end] == \
                           (0).to_bytes(8, byteorder="little")
                elif i == 1:
                    assert mp4_bytes[entry.chunk_offset:sample_end] == \
                           (1).to_bytes(8, byteorder="little")
                elif i == 2:
                    assert mp4_bytes[entry.chunk_offset:sample_end] == \
                           (0).to_bytes(8, byteorder="little")

    with open("data/small_dataset.out.mp4", "rb") as f:
        assert mp4_bytes == f.read()


def test_mp4_small_vid():
    creation_time = to_mp4_time(datetime(2019, 9, 15, 0, 0, 0))
    modification_time = to_mp4_time(datetime(2019, 9, 16, 0, 0, 0))

    # FTYP
    ftyp = bx_def.FTYP(headers.BoxHeader())
    ftyp.header.type = b"ftyp"
    ftyp.major_brand = (1836069937,)                # b"mp41"
    ftyp.minor_version = (0,)
    ftyp.compatible_brands = ([1836069937],)        # b'mp41'

    ftyp.refresh_box_size()

    assert ftyp.header.type == b"ftyp"
    assert ftyp.header.box_size == 20
    assert ftyp.major_brand == 1836069937           # b"mp41"
    assert ftyp.minor_version == 0
    assert ftyp.compatible_brands == [1836069937]   # b'mp41'
    assert bytes(ftyp) == pack("uintbe:32, bytes:4, "
                               "bytes:4, uintbe:32, bytes:4",
                               20, b"ftyp",
                               b"mp41", 0, b'mp41')

    # MDAT
    mdat = bx_def.MDAT(headers.BoxHeader())
    mdat.header.type = b"mdat"

    data = []

    with open("data/small_vid_mdat_im0", "rb") as f:
        data.append(f.read())
    with open("data/small_vid_mdat_im1", "rb") as f:
        data.append(f.read())
    with open("data/small_vid_mdat_im2", "rb") as f:
        data.append(f.read())

    mdat.data = (b''.join(data),)

    mdat.refresh_box_size()

    assert mdat.header.type == b"mdat"
    assert mdat.header.box_size == 518258

    # MOOV
    moov = bx_def.MOOV(headers.BoxHeader())
    moov.header.type = b"moov"

    # MOOV.MVHD
    mvhd = bx_def.MVHD(headers.FullBoxHeader())

    mvhd.header.type = b"mvhd"
    mvhd.header.version = (1,)
    mvhd.header.flags = (b"\x00\x00\x00",)

    mvhd.creation_time = (creation_time,)
    mvhd.modification_time = (modification_time,)
    # TODO: 20 units / second (does not necessary means 20 img / sec)
    mvhd.timescale = (20,)
    # total duration in the indicated timescale
    mvhd.duration = (60,)

    # prefered play rate (1x, 2x, 1/2x, ...)
    mvhd.rate = ([1, 0],)
    # prefered volume (1 is full volume)
    mvhd.volume = ([0, 0],)

    # TODO: validate matrix (and check if those are 16.16 floats)
    mvhd.matrix = ([65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824],)
    # TODO: check what pre_defined is
    mvhd.pre_defined = ([b"\x00" * 4] * 6,)

    # == total number of tracks
    mvhd.next_track_id = (2,)

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

    assert mvhd.next_track_id == 2

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
                2)

    moov.append(mvhd)

    # MOOV.TRAK.TKHD
    tkhd = bx_def.TKHD(headers.FullBoxHeader())

    tkhd.header.type = b"tkhd"
    tkhd.header.version = (1,)
    # "\x00\x00\x01" trak is enabled
    # "\x00\x00\x02" trak is used in the presentation
    # "\x00\x00\x04" trak is used in the preview
    # "\x00\x00\x08" trak size in not in pixel but in aspect ratio
    tkhd.header.flags = (b"\x00\x00\x03",)

    tkhd.creation_time = (creation_time,)
    tkhd.modification_time = (modification_time,)
    tkhd.track_id = (1,)
    tkhd.duration = (60,)

    tkhd.layer = (0,)
    tkhd.alternate_group = (0,)
    tkhd.volume = ([0, 0],)

    # TODO: validate matrix (and check if those are 16.16 floats)
    tkhd.matrix = ([65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824],)

    # TODO: make sure that this is the canvas size
    tkhd.width = ([512, 0],)
    tkhd.height = ([512, 0],)

    tkhd.refresh_box_size()

    assert tkhd.header.type == b"tkhd"
    assert tkhd.header.box_size == 104
    assert tkhd.header.version == 1
    assert tkhd.header.flags == b"\x00\x00\x03"

    assert tkhd.creation_time == creation_time
    assert tkhd.modification_time == modification_time
    assert tkhd.track_id == 1
    assert tkhd.duration == 60

    assert tkhd.layer == 0
    assert tkhd.alternate_group == 0
    assert tkhd.volume == [0, 0]

    assert tkhd.matrix == [65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824]

    assert tkhd.width == 512
    assert tkhd.height == 512

    assert tkhd.is_audio is False

    assert bytes(tkhd) == \
           pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
                "uintbe:64, uintbe:64, uintbe:32, "
                "bits:32, "
                "uintbe:64, "
                "bits:32, bits:32, "
                "uintbe:16, uintbe:16, uintbe:8, uintbe:8, "
                "bits:16, "
                "uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, uintbe:32, "
                "uintbe:16, uintbe:16, uintbe:16, uintbe:16",
                104, b"tkhd", 1, b"\x00\x00\x03",
                creation_time, modification_time, 1,
                b"\x00" * 4,
                60,
                b"\x00" * 4, b"\x00" * 4,
                0, 0, 0, 0,
                b"\x00" * 2,
                65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824,
                512, 0, 512, 0)

    # MOOV.TRAK.MDIA.HDLR
    hdlr = bx_def.HDLR(headers.FullBoxHeader())

    hdlr.header.type = b"hdlr"
    hdlr.header.version = (0,)
    hdlr.header.flags = (b"\x00\x00\x00",)
    hdlr.pre_defined = (0,)
    hdlr.handler_type = (b"vide",)
    hdlr.name = (b"VideoHandler\0",)

    hdlr.refresh_box_size()

    assert hdlr.header.type == b"hdlr"
    assert hdlr.header.box_size == 32 + len(b"VideoHandler\0")
    assert hdlr.header.version == 0
    assert hdlr.header.flags == b"\x00\x00\x00"
    assert hdlr.pre_defined == 0
    assert hdlr.handler_type == b"vide"
    # TODO: validate the use of the name
    assert hdlr.name == b"VideoHandler\0"

    assert bytes(hdlr)[4:] == \
           pack("bytes:4, uintbe:8, bits:24, "
                "uintbe:32, bytes:4, bits:32, bits:32, bits:32",
                b"hdlr", 0, b"\x00\x00\x00",
                0, b"vide", b"\x00" * 4, b"\x00" * 4, b"\x00" * 4).bytes + \
           b"VideoHandler\0"

    # MOOV.TRAK.MDIA.MINF.VMHD
    vmhd = bx_def.VMHD(headers.FullBoxHeader())

    vmhd.header.type = b"vmhd"
    vmhd.header.version = (0,)
    # flag is 1
    vmhd.header.flags = (b"\x00\x00\x01",)
    vmhd.graphicsmode = (0,)
    vmhd.opcolor = ([0, 0, 0],)

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

    # MOOV.TRAK.MDIA.MINF.VMHD
    vmhd = bx_def.VMHD(headers.FullBoxHeader())

    vmhd.header.type = b"vmhd"
    vmhd.header.version = (0,)
    # flag is 1
    vmhd.header.flags = (b"\x00\x00\x01",)
    vmhd.graphicsmode = (0,)
    vmhd.opcolor = ([0, 0, 0],)

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
    stsd = bx_def.STSD(headers.FullBoxHeader())

    stsd.header.type = b"stsd"
    stsd.header.version = (0,)
    stsd.header.flags = (b"\x00\x00\x00",)

    # MOOV.TRAK.MDIA.MINF.STBL.STSD.AVC1
    avc1 = bx_def.AVC1(headers.BoxHeader())

    avc1.header.type = b"avc1"
    avc1.data_reference_index = (1,)
    avc1.width = (512,)
    avc1.height = (512,)
    avc1.horizresolution = ([72, 0],)
    avc1.vertresolution = ([72, 0],)
    avc1.frame_count = (1,)
    avc1.compressorname = (b'\0' * 32,)
    avc1.depth = (24,)

    # TODO: implement MOOV.TRAK.MDIA.MINF.STBL.STSD.AVC1.AVCC
    avcC = bx_def.UnknownBox(headers.BoxHeader())
    avcC.header.type = b"avcC"
    avcC.payload = b'\x01d\x10\x16\xff\xe1\x00\x1bgd\x10\x16\xac\xb8\x10\x02' \
                   b'\r\xff\x80K\x00N\xb6\xa5\x00\x00\x03\x00\x01\x00\x00\x03' \
                   b'\x00\x02\x04\x01\x00\x07h\xee\x01\x9cL\x84\xc0'

    avcC.refresh_box_size()

    assert avcC.header.type == b"avcC"
    assert avcC.header.box_size == 53

    avc1.append(avcC)

    # TODO: implement MOOV.TRAK.MDIA.MINF.STBL.STSD.AVC1.PASP
    pasp = bx_def.UnknownBox(headers.BoxHeader())
    pasp.header.type = b"pasp"
    pasp.payload = b'\x00\x00\x00\x96\x00\x00\x00\x9d'

    pasp.refresh_box_size()

    assert pasp.header.type == b"pasp"
    assert pasp.header.box_size == 16

    avc1.append(pasp)

    avc1.refresh_box_size()

    assert avc1.header.type == b"avc1"
    assert avc1.header.box_size == 86 + 53 + 16

    stsd.append(avc1)

    stsd.refresh_box_size()

    assert stsd.header.type == b"stsd"
    assert stsd.header.box_size == 16 + 155
    assert len(stsd.boxes) == 1

    # MOOV.TRAK
    offset = ftyp.header.box_size + mdat.header.header_size
    sizes = [198297, 127477, 192476]
    trak = _make_track(creation_time, modification_time,
                       tkhd, hdlr, vmhd, stsd,
                       sizes, [offset,
                               offset + sum(sizes[0:1]),
                               offset + sum(sizes[0:2])])

    moov.append(trak)

    moov.refresh_box_size()

    assert mvhd.next_track_id == len(moov.boxes)

    assert moov.header.type == b"moov"
    assert len(moov.boxes) == 2

    mp4_bytes = b''.join([bytes(ftyp), bytes(mdat), bytes(moov)])

    with open("data/small_vid.out.mp4", "rb") as f:
        assert mp4_bytes == f.read()

    # bstr = ConstBitStream(filename="data/small_vid.mp4")
    #
    # boxes = [box for box in Parser.parse(bstr)]
    # for box in boxes:
    #     box.load(bstr)
    # moov = boxes[3]
    # moov.pop()
    # moov.refresh_box_size()
    # with open("data/small_vid_no_moov_udta.mp4", "wb") as f:
    #     f.write(b''.join(bytes(box) for box in boxes))
    #
    # boxes = [boxes[0]] + boxes[2:]
    # for box in moov.boxes:
    #     if isinstance(box, bx_def.TRAK):
    #         mdia = box.boxes[2]
    #     else:
    #         continue
    #
    #     # trak.mdia.minf.stbl.stsz
    #     stsz = mdia.boxes[2].boxes[2].boxes[3]
    #     # trak.mdia.minf.stbl.stco
    #     stco = mdia.boxes[2].boxes[2].boxes[4]
    #     stco.entries[0].chunk_offset = (40,)
    # with open("data/small_vid_no_free_no_moov_udta.mp4", "wb") as f:
    #     f.write(b''.join(bytes(box) for box in boxes))
    #
    # for box in moov.boxes:
    #     if isinstance(box, bx_def.TRAK):
    #         mdia = box.pop()
    #         box.pop()
    #         box.append(mdia)
    #         box.refresh_box_size()
    #     else:
    #         continue
    # with open("data/small_vid_no_free_no_moov_udta_no_trak_edts.mp4", "wb") as f:
    #     f.write(b''.join(bytes(box) for box in boxes))
