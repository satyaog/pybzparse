from datetime import datetime, timedelta

import boxes as bx_def
import headers

BEGIN = datetime(1904, 1, 1, 0, 0)


def to_mp4_time(date_time):
    return int((date_time - BEGIN).total_seconds())


def from_mp4_time(seconds):
    return BEGIN + timedelta(0, seconds)


def make_track(creation_time, modification_time, samples_sizes, samples_offsets):
    # MOOV.TRAK
    trak = bx_def.TRAK(headers.BoxHeader())
    trak.header.type = b"trak"

    # MOOV.TRAK.TKHD
    tkhd = bx_def.TKHD(headers.FullBoxHeader())

    tkhd.header.type = b"tkhd"
    tkhd.header.version = (1,)
    tkhd.header.flags = (b"\x00\x00\x00",)

    tkhd.creation_time = (creation_time,)
    tkhd.modification_time = (modification_time,)
    tkhd.track_id = (-1,)
    tkhd.duration = (-1,)

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
    # edts.append(elst)
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
    mdhd.timescale = (-1,)
    mdhd.duration = (-1,)

    # TODO: check the language code
    mdhd.language = ([21, 14, 4],)
    mdhd.pre_defined = (0,)

    mdia.append(mdhd)

    # MOOV.TRAK.MDIA.HDLR
    hdlr = bx_def.HDLR(headers.FullBoxHeader())

    hdlr.header.type = b"hdlr"
    hdlr.header.version = (0,)
    hdlr.header.flags = (b"\x00\x00\x00",)
    hdlr.pre_defined = (0,)
    hdlr.handler_type = (b"____",)
    hdlr.name = (b"\0",)

    mdia.append(hdlr)

    # MOOV.TRAK.MDIA.MINF
    minf = bx_def.MINF(headers.BoxHeader())
    minf.header.type = b"minf"

    # MOOV.TRAK.MDIA.MINF._MHD (placeholder)
    _mhd = bx_def.UnknownBox(headers.BoxHeader())
    _mhd.header.type = b"_mhd"

    minf.append(_mhd)

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

    dref.append(url_)

    dinf.append(dref)

    minf.append(dinf)

    # MOOV.TRAK.MDIA.MINF.STBL
    stbl = bx_def.STBL(headers.BoxHeader())
    stbl.header.type = b"stbl"

    # MOOV.TRAK.MDIA.MINF.STBL.STSD
    stsd = bx_def.STSD(headers.FullBoxHeader())

    stsd.header.type = b"stsd"
    stsd.header.version = (0,)
    stsd.header.flags = (b"\x00\x00\x00",)

    stbl.append(stsd)

    # MOOV.TRAK.MDIA.MINF.STBL.STTS
    stts = bx_def.STTS(headers.FullBoxHeader())

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

    stbl.append(stsz)

    # MOOV.TRAK.MDIA.MINF.STBL.STSC
    stsc = bx_def.STSC(headers.FullBoxHeader())

    stsc.header.type = b"stsc"
    stsc.header.version = (0,)
    stsc.header.flags = (b"\x00\x00\x00",)

    entry = stsc.append_and_return()
    entry.first_chunk = (1,)
    entry.samples_per_chunk = (1,)
    entry.sample_description_index = (1,)

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

    stbl.append(stco)

    minf.append(stbl)

    mdia.append(minf)

    trak.append(mdia)

    return trak
