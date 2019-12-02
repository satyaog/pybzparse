from ctypes import c_uint32
from datetime import datetime, timedelta

from pybzparse import boxes as bx_def
from pybzparse.headers import BoxHeader, FullBoxHeader

BEGIN = datetime(1904, 1, 1, 0, 0)
MAX_UINT_32 = c_uint32(-1).value


def to_mp4_time(date_time):
    return int((date_time - BEGIN).total_seconds())


def from_mp4_time(seconds):
    return BEGIN + timedelta(0, seconds)


def gen_sample_offsets(samples_sizes, samples_offsets):
    if isinstance(samples_offsets, int):
        for size in samples_sizes:
            yield samples_offsets
            samples_offsets += size
    else:
        for offset in samples_offsets:
            yield offset


def make_mvhd(creation_time, modification_time, samples_count):
    # MOOV.MVHD
    mvhd = bx_def.MVHD(FullBoxHeader())

    mvhd.header.type = b"mvhd"
    mvhd.header.version = (1,)
    mvhd.header.flags = (b"\x00\x00\x00",)

    mvhd.creation_time = (creation_time,)
    mvhd.modification_time = (modification_time,)
    # TODO: 20 units / second (does not necessary means 20 img / sec)
    mvhd.timescale = (20,)
    # total duration in the indicated timescale
    mvhd.duration = (20 * samples_count,)

    # prefered play rate (1x, 2x, 1/2x, ...)
    mvhd.rate = ([1, 0],)
    # prefered volume (1 is full volume)
    mvhd.volume = ([0, 0],)

    # TODO: validate matrix (and check if those are 16.16 floats)
    mvhd.matrix = ([65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824],)
    # TODO: check what pre_defined is
    mvhd.pre_defined = ([b"\x00" * 4] * 6,)

    # == total number of tracks
    mvhd.next_track_id = (1,)

    return mvhd


def make_trak(creation_time, modification_time, samples_sizes, samples_offsets):
    # MOOV.TRAK
    trak = bx_def.TRAK(BoxHeader())
    trak.header.type = b"trak"

    # MOOV.TRAK.TKHD
    tkhd = bx_def.TKHD(FullBoxHeader())

    tkhd.header.type = b"tkhd"
    tkhd.header.version = (1,)
    tkhd.header.flags = (b"\x00\x00\x00",)

    tkhd.creation_time = (creation_time,)
    tkhd.modification_time = (modification_time,)
    tkhd.track_id = (-1,)
    tkhd.duration = (20 * len(samples_sizes),)

    tkhd.layer = (0,)
    tkhd.alternate_group = (0,)
    tkhd.volume = ([0, 0],)

    # TODO: validate matrix (and check if those are 16.16 floats)
    tkhd.matrix = ([65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824],)

    # TODO: make sure that this is the canvas size
    tkhd.width = ([-1, 0],)
    tkhd.height = ([-1, 0],)

    trak.append(tkhd)

    # # MOOV.TRAK.EDTS
    # edts = bx_def.EDTS(BoxHeader())
    # edts.header.type = b"edts"
    #
    # # MOOV.TRAK.EDTS.ELST
    # elst = bx_def.ELST(FullBoxHeader())
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
    # edts.append(elst)
    #
    # trak.append(edts)

    # MOOV.TRAK.MDIA
    mdia = bx_def.MDIA(BoxHeader())
    mdia.header.type = b"mdia"

    # MOOV.TRAK.MDIA.MDHD
    mdhd = bx_def.MDHD(FullBoxHeader())

    mdhd.header.type = b"mdhd"
    mdhd.header.version = (1,)
    mdhd.header.flags = (b"\x00\x00\x00",)

    mdhd.creation_time = (creation_time,)
    mdhd.modification_time = (modification_time,)
    mdhd.timescale = (20,)
    mdhd.duration = (20 * len(samples_sizes),)

    # TODO: check the language code
    mdhd.language = ([21, 14, 4],)
    mdhd.pre_defined = (0,)

    mdia.append(mdhd)

    # MOOV.TRAK.MDIA.HDLR
    hdlr = bx_def.HDLR(FullBoxHeader())

    hdlr.header.type = b"hdlr"
    hdlr.header.version = (0,)
    hdlr.header.flags = (b"\x00\x00\x00",)
    hdlr.pre_defined = (0,)
    hdlr.handler_type = (b"____",)
    hdlr.name = (b"\0",)

    mdia.append(hdlr)

    # MOOV.TRAK.MDIA.MINF
    minf = bx_def.MINF(BoxHeader())
    minf.header.type = b"minf"

    # MOOV.TRAK.MDIA.MINF._MHD (placeholder)
    _mhd = bx_def.UnknownBox(BoxHeader())
    _mhd.header.type = b"_mhd"

    minf.append(_mhd)

    # MOOV.TRAK.MDIA.MINF.DINF
    dinf = bx_def.DINF(BoxHeader())
    dinf.header.type = b"dinf"

    # MOOV.TRAK.MDIA.MINF.DINF.DREF
    dref = bx_def.DREF(FullBoxHeader())
    dref.header.type = b"dref"
    dref.header.version = (0,)
    dref.header.flags = (b"\x00\x00\x00",)

    # MOOV.TRAK.MDIA.MINF.DINF.DREF.URL_
    url_ = bx_def.URL_(FullBoxHeader())

    url_.header.type = b"url "
    url_.header.version = (0,)
    # TODO:  validate that this flags means that the data is in the same file
    url_.header.flags = (b"\x00\x00\x01",)

    dref.append(url_)

    dinf.append(dref)

    minf.append(dinf)

    # MOOV.TRAK.MDIA.MINF.STBL
    stbl = bx_def.STBL(BoxHeader())
    stbl.header.type = b"stbl"

    # MOOV.TRAK.MDIA.MINF.STBL.STSD
    stsd = bx_def.STSD(FullBoxHeader())

    stsd.header.type = b"stsd"
    stsd.header.version = (0,)
    stsd.header.flags = (b"\x00\x00\x00",)

    stbl.append(stsd)

    # MOOV.TRAK.MDIA.MINF.STBL.STTS
    stts = bx_def.STTS(FullBoxHeader())

    stts.header.type = b"stts"
    stts.header.version = (0,)
    stts.header.flags = (b"\x00\x00\x00",)

    entry = stts.append_and_return()
    # imges count
    entry.sample_count = (len(samples_sizes),)
    # 1 img / sec
    entry.sample_delta = (20,)

    stbl.append(stts)

    # MOOV.TRAK.MDIA.MINF.STBL.STSZ
    stsz = bx_def.STSZ(FullBoxHeader())

    stsz.header.type = b"stsz"
    stsz.header.version = (0,)
    stsz.header.flags = (b"\x00\x00\x00",)

    stsz.sample_size = (0,)

    for samples_size in samples_sizes:
        sample = stsz.append_and_return()
        sample.entry_size = (samples_size,)

    stbl.append(stsz)

    # MOOV.TRAK.MDIA.MINF.STBL.STSC
    stsc = bx_def.STSC(FullBoxHeader())

    stsc.header.type = b"stsc"
    stsc.header.version = (0,)
    stsc.header.flags = (b"\x00\x00\x00",)

    entry = stsc.append_and_return()
    entry.first_chunk = (1,)
    entry.samples_per_chunk = (1,)
    entry.sample_description_index = (1,)

    stbl.append(stsc)

    # MOOV.TRAK.MDIA.MINF.STBL.STCO
    co = bx_def.STCO(FullBoxHeader())
    co.header.type = b"stco"
    co.header.version = (0,)
    co.header.flags = (b"\x00\x00\x00",)

    for offset in gen_sample_offsets(samples_sizes, samples_offsets):
        # If the offset gets bigger than 2^32-1, use the 64 bits implementation
        if offset > MAX_UINT_32:
            # MOOV.TRAK.MDIA.MINF.STBL.CO64
            co = bx_def.CO64(FullBoxHeader())
            co.header.type = b"co64"
            co.header.version = (0,)
            co.header.flags = (b"\x00\x00\x00",)
            break
        entry = co.append_and_return()
        entry.chunk_offset = (offset,)

    # If the offset gets bigger than 2^32-1, add again using co64
    if isinstance(co, bx_def.CO64):
        for offset in gen_sample_offsets(samples_sizes, samples_offsets):
            entry = co.append_and_return()
            entry.chunk_offset = (offset,)

    stbl.append(co)

    minf.append(stbl)

    mdia.append(minf)

    trak.append(mdia)

    return trak


def make_meta_trak(creation_time, modification_time, label,
                   samples_sizes, samples_offsets):
    trak = make_trak(creation_time, modification_time, samples_sizes, samples_offsets)

    # MOOV.TRAK.MDIA
    mdia = trak.boxes[-1]

    # MOOV.TRAK.MDIA.HDLR
    hdlr = mdia.boxes[1]
    hdlr.handler_type = (b"meta",)
    hdlr.name = (label,)

    # MOOV.TRAK.MDIA.MINF
    minf = mdia.boxes[-1]

    # MOOV.TRAK.MDIA.MINF.NMHD
    nmhd = bx_def.NMHD(FullBoxHeader())
    minf.boxes[0] = nmhd

    nmhd.header.type = b"nmhd"
    nmhd.header.version = (0,)
    nmhd.header.flags = (b"\x00\x00\x00",)

    # MOOV.TRAK.MDIA.MINF.STBL
    stbl = minf.boxes[-1]

    # MOOV.TRAK.MDIA.MINF.STBL.STSD
    stsd = stbl.boxes[0]

    # MOOV.TRAK.MDIA.MINF.STBL.STSD.METT
    mett = bx_def.METT(BoxHeader())

    mett.header.type = b"mett"
    mett.data_reference_index = (1,)
    mett.content_encoding = (b'\0',)
    mett.mime_format = (b'\0',)

    stsd.append(mett)

    return trak


def make_text_trak(creation_time, modification_time, label,
                   samples_sizes, samples_offsets):
    trak = make_trak(creation_time, modification_time, samples_sizes, samples_offsets)

    # MOOV.TRAK.MDIA
    mdia = trak.boxes[-1]

    # MOOV.TRAK.MDIA.HDLR
    hdlr = mdia.boxes[1]
    hdlr.handler_type = (b"text",)
    hdlr.name = (label,)

    # MOOV.TRAK.MDIA.MINF
    minf = mdia.boxes[-1]

    # MOOV.TRAK.MDIA.MINF.NMHD
    nmhd = bx_def.NMHD(FullBoxHeader())
    minf.boxes[0] = nmhd

    nmhd.header.type = b"nmhd"
    nmhd.header.version = (0,)
    nmhd.header.flags = (b"\x00\x00\x00",)

    # MOOV.TRAK.MDIA.MINF.STBL
    stbl = minf.boxes[-1]

    # MOOV.TRAK.MDIA.MINF.STBL.STSD
    stsd = stbl.boxes[0]

    # MOOV.TRAK.MDIA.MINF.STBL.STSD.STXT
    stxt = bx_def.STXT(BoxHeader())

    stxt.header.type = b"stxt"
    stxt.data_reference_index = (1,)
    stxt.content_encoding = (b'\0',)
    stxt.mime_format = (b'text/plain\0',)

    stsd.append(stxt)

    return trak


def make_vide_trak(creation_time, modification_time, label,
                   samples_sizes, samples_offsets):
    trak = make_trak(creation_time, modification_time, samples_sizes, samples_offsets)

    # MOOV.TRAK.MDIA
    mdia = trak.boxes[-1]

    # MOOV.TRAK.MDIA.HDLR
    hdlr = mdia.boxes[1]
    hdlr.handler_type = (b"vide",)
    hdlr.name = (label,)

    # MOOV.TRAK.MDIA.MINF
    minf = mdia.boxes[-1]

    # MOOV.TRAK.MDIA.MINF.VMHD
    vmhd = bx_def.VMHD(FullBoxHeader())
    minf.boxes[0] = vmhd

    vmhd.header.type = b"vmhd"
    vmhd.header.version = (0,)
    # flag is 1
    vmhd.header.flags = (b"\x00\x00\x01",)
    vmhd.graphicsmode = (0,)
    vmhd.opcolor = ([0, 0, 0],)

    # MOOV.TRAK.MDIA.MINF
    stbl = minf.boxes[-1]

    # MOOV.TRAK.MDIA.MINF.STBL.STSD
    stsd = stbl.boxes[0]

    # MOOV.TRAK.MDIA.MINF.STBL.STSD.AVC1
    avc1 = bx_def.AVC1(BoxHeader())

    avc1.header.type = b"avc1"
    avc1.data_reference_index = (1,)
    avc1.width = (-1,)
    avc1.height = (-1,)
    avc1.horizresolution = ([72, 0],)
    avc1.vertresolution = ([72, 0],)
    avc1.frame_count = (1,)
    avc1.compressorname = (b'\0' * 32,)
    avc1.depth = (24,)

    # TODO: implement MOOV.TRAK.MDIA.MINF.STBL.STSD.AVC1.AVCC
    avcC = bx_def.UnknownBox(BoxHeader())
    avcC.header.type = b"avcC"
    avcC.payload = b'\x01d\x10\x16\xff\xe1\x00\x1bgd\x10\x16\xac\xb8\x10\x02' \
                   b'\r\xff\x80K\x00N\xb6\xa5\x00\x00\x03\x00\x01\x00\x00\x03' \
                   b'\x00\x02\x04\x01\x00\x07h\xee\x01\x9cL\x84\xc0'

    avc1.append(avcC)

    # MOOV.TRAK.MDIA.MINF.STBL.STSD.AVC1.PASP
    pasp = bx_def.PASP(BoxHeader())
    pasp.header.type = b"pasp"
    pasp.h_spacing = (1,)
    pasp.v_spacing = (1,)

    avc1.append(pasp)

    stsd.append(avc1)

    return trak


def find_boxes(boxes, box_types):
    for box in boxes:
        if box.header.type in box_types:
            yield box


def find_traks(boxes, trak_name):
    for box in find_boxes(boxes, b"trak"):
        # TRAK.MDIA.HDLR
        if box.boxes[-1].boxes[1].name == trak_name:
            yield box


def get_trak_sample(bstr, boxes, trak_name, index):
    sample = None

    for trak in find_traks(boxes, trak_name):
        # TRAK.MDIA.MINF.STBL
        stbl = trak.boxes[-1].boxes[-1].boxes[-1]

        stco = next(find_boxes(stbl.boxes, [b"stco", b"co64"]))
        stsz = next(find_boxes(stbl.boxes, b"stsz"))
        if index < len(stco.entries):
            offset = stco.entries[index].chunk_offset
            size = stsz.samples[index].entry_size
            bstr.bytepos = offset
            sample = bstr.read("bytes:{}".format(size))
        break

    return sample
