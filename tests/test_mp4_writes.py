from datetime import datetime

from bitstring import pack

import boxes as bx_def
import headers
from utils import to_mp4_time, make_track, \
    make_meta_track, make_text_track, make_vide_track


def test_mp4_dataset():
    creation_time = to_mp4_time(datetime(2019, 9, 15, 0, 0, 0))
    modification_time = to_mp4_time(datetime(2019, 9, 16, 0, 0, 0))

    # FTYP
    ftyp = bx_def.FTYP(headers.BoxHeader())
    ftyp.header.type = b"ftyp"
    ftyp.major_brand = (1769172845,)            # b"isom"
    ftyp.minor_version = (0,)
    ftyp.compatible_brands = ([1652190817,      # b"bzna"
                               1769172845],)    # b"isom"

    ftyp.refresh_box_size()

    assert ftyp.header.type == b"ftyp"
    assert ftyp.header.box_size == 24
    assert ftyp.major_brand == 1769172845           # b"isom"
    assert ftyp.minor_version == 0
    assert ftyp.compatible_brands == [1652190817,   # b"bzna"
                                      1769172845]   # b"isom"
    assert bytes(ftyp) == pack("uintbe:32, bytes:4, bytes:4, uintbe:32, "
                               "bytes:8",
                               24, b"ftyp", b"isom", 0,
                               b"bznaisom")

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
    mvhd.next_track_id = (5,)

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

    assert mvhd.next_track_id == 5

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
                5)

    moov.append(mvhd)

    # MOOV.TRAK
    offset = ftyp.header.box_size + mdat.header.header_size
    sizes = [198297, 127477, 192476]
    trak = make_vide_track(creation_time, modification_time, b"VideoHandler\0",
                           sizes, [offset,
                                   offset + sum(sizes[0:1]),
                                   offset + sum(sizes[0:2])])

    # MOOV.TRAK.TKHD
    tkhd = trak.boxes[0]

    # "\x00\x00\x01" trak is enabled
    # "\x00\x00\x02" trak is used in the presentation
    # "\x00\x00\x04" trak is used in the preview
    # "\x00\x00\x08" trak size in not in pixel but in aspect ratio
    tkhd.header.flags = (b"\x00\x00\x03",)

    tkhd.track_id = (1,)
    tkhd.duration = (60,)

    # TODO: make sure that this is the canvas size
    tkhd.width = ([512, 0],)
    tkhd.height = ([512, 0],)

    tkhd.refresh_box_size()

    assert tkhd.header.type == b"tkhd"
    assert tkhd.header.box_size == 104
    assert tkhd.header.flags == b"\x00\x00\x03"

    assert tkhd.track_id == 1
    assert tkhd.duration == 60

    assert tkhd.width == 512
    assert tkhd.height == 512

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

    # MOOV.TRAK.MDIA.MDHD
    mdhd = trak.boxes[-1].boxes[0]
    mdhd.timescale = (20,)
    mdhd.duration = (60,)

    mdhd.refresh_box_size()

    assert mdhd.header.type == b"mdhd"
    assert mdhd.header.box_size == 44
    assert mdhd.timescale == 20
    assert mdhd.duration == 60

    assert bytes(mdhd) == \
           pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
                "uintbe:64, uintbe:64, uintbe:32, uintbe:64, "
                "bits:1, uint:5, uint:5, uint:5, "
                "bits:16",
                44, b"mdhd", 1, b"\x00\x00\x00",
                creation_time, modification_time, 20, 60,
                0x1, 21, 14, 4,
                b"\x00" * 2)

    # MOOV.TRAK.MDIA.MINF.STBL.STSD.AVC1
    avc1 = trak.boxes[-1].boxes[-1].boxes[-1].boxes[0].boxes[0]
    avc1.width = (512,)
    avc1.height = (512,)
    avc1.horizresolution = ([72, 0],)
    avc1.vertresolution = ([72, 0],)

    assert avc1.header.type == b"avc1"
    assert avc1.width == 512
    assert avc1.height == 512
    assert avc1.horizresolution == [72, 0]
    assert avc1.vertresolution == [72, 0]

    moov.append(trak)

    # MOOV.TRAK
    trak = make_meta_track(creation_time, modification_time, b"bzna_inputs\0",
                           sizes, [offset,
                                   offset + sum(sizes[0:1]),
                                   offset + sum(sizes[0:2])])

    # MOOV.TRAK.TKHD
    tkhd = trak.boxes[0]

    # "\x00\x00\x01" trak is enabled
    # "\x00\x00\x02" trak is used in the presentation
    # "\x00\x00\x04" trak is used in the preview
    # "\x00\x00\x08" trak size in not in pixel but in aspect ratio
    tkhd.header.flags = (b"\x00\x00\x00",)

    tkhd.track_id = (2,)
    tkhd.duration = (60,)

    # TODO: make sure that this is the canvas size
    tkhd.width = ([0, 0],)
    tkhd.height = ([0, 0],)

    tkhd.refresh_box_size()

    assert tkhd.header.type == b"tkhd"
    assert tkhd.header.box_size == 104
    assert tkhd.header.flags == b"\x00\x00\x00"

    assert tkhd.track_id == 2
    assert tkhd.duration == 60

    assert tkhd.width == 0
    assert tkhd.height == 0

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

    # MOOV.TRAK.MDIA.MDHD
    mdhd = trak.boxes[-1].boxes[0]
    mdhd.timescale = (20,)
    mdhd.duration = (60,)

    mdhd.refresh_box_size()

    assert mdhd.header.type == b"mdhd"
    assert mdhd.header.box_size == 44
    assert mdhd.timescale == 20
    assert mdhd.duration == 60

    assert bytes(mdhd) == \
           pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
                "uintbe:64, uintbe:64, uintbe:32, uintbe:64, "
                "bits:1, uint:5, uint:5, uint:5, "
                "bits:16",
                44, b"mdhd", 1, b"\x00\x00\x00",
                creation_time, modification_time, 20, 60,
                0x1, 21, 14, 4,
                b"\x00" * 2)

    # MOOV.TRAK.MDIA.MINF.STBL.STSD.METT
    mett = trak.boxes[-1].boxes[-1].boxes[-1].boxes[0].boxes[0]
    mett.mime_format = (b'video/h264\0',)
    mett.refresh_box_size()

    assert mett.header.type == b"mett"
    assert mett.header.box_size == 28
    assert mett.mime_format == b'video/h264\0'

    moov.append(trak)

    # MOOV.TRAK
    offset += sum(sizes)
    sizes = [23, 23, 23]
    trak = make_text_track(creation_time, modification_time, b"bzna_fnames\0",
                           sizes, [offset,
                                   offset + sum(sizes[0:1]),
                                   offset + sum(sizes[0:2])])

    # MOOV.TRAK.TKHD
    tkhd = trak.boxes[0]

    # "\x00\x00\x01" trak is enabled
    # "\x00\x00\x02" trak is used in the presentation
    # "\x00\x00\x04" trak is used in the preview
    # "\x00\x00\x08" trak size in not in pixel but in aspect ratio
    tkhd.header.flags = (b"\x00\x00\x00",)

    tkhd.track_id = (3,)
    tkhd.duration = (60,)

    # TODO: make sure that this is the canvas size
    tkhd.width = ([0, 0],)
    tkhd.height = ([0, 0],)

    tkhd.refresh_box_size()

    assert tkhd.header.type == b"tkhd"
    assert tkhd.header.box_size == 104
    assert tkhd.header.flags == b"\x00\x00\x00"

    assert tkhd.track_id == 3
    assert tkhd.duration == 60

    assert tkhd.width == 0
    assert tkhd.height == 0

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

    # MOOV.TRAK.MDIA.MDHD
    mdhd = trak.boxes[-1].boxes[0]
    mdhd.timescale = (20,)
    mdhd.duration = (60,)

    mdhd.refresh_box_size()

    assert mdhd.header.type == b"mdhd"
    assert mdhd.header.box_size == 44
    assert mdhd.timescale == 20
    assert mdhd.duration == 60

    assert bytes(mdhd) == \
           pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
                "uintbe:64, uintbe:64, uintbe:32, uintbe:64, "
                "bits:1, uint:5, uint:5, uint:5, "
                "bits:16",
                44, b"mdhd", 1, b"\x00\x00\x00",
                creation_time, modification_time, 20, 60,
                0x1, 21, 14, 4,
                b"\x00" * 2)

    moov.append(trak)

    # MOOV.TRAK
    offset += sum(sizes)
    sizes = [8, 8, 8]
    trak = make_text_track(creation_time, modification_time, b"bzna_targets\0",
                           sizes, [offset,
                                   offset + sum(sizes[0:1]),
                                   offset + sum(sizes[0:2])])

    # MOOV.TRAK.TKHD
    tkhd = trak.boxes[0]

    # "\x00\x00\x01" trak is enabled
    # "\x00\x00\x02" trak is used in the presentation
    # "\x00\x00\x04" trak is used in the preview
    # "\x00\x00\x08" trak size in not in pixel but in aspect ratio
    tkhd.header.flags = (b"\x00\x00\x00",)

    tkhd.track_id = (4,)
    tkhd.duration = (60,)

    # TODO: make sure that this is the canvas size
    tkhd.width = ([0, 0],)
    tkhd.height = ([0, 0],)

    tkhd.refresh_box_size()

    assert tkhd.header.type == b"tkhd"
    assert tkhd.header.box_size == 104
    assert tkhd.header.flags == b"\x00\x00\x00"

    assert tkhd.track_id == 4
    assert tkhd.duration == 60

    assert tkhd.width == 0
    assert tkhd.height == 0

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
                creation_time, modification_time, 4,
                b"\x00" * 4,
                60,
                b"\x00" * 4, b"\x00" * 4,
                0, 0, 0, 0,
                b"\x00" * 2,
                65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824,
                0, 0, 0, 0)

    # MOOV.TRAK.MDIA.MDHD
    mdhd = trak.boxes[-1].boxes[0]
    mdhd.timescale = (20,)
    mdhd.duration = (60,)

    mdhd.refresh_box_size()

    assert mdhd.header.type == b"mdhd"
    assert mdhd.header.box_size == 44
    assert mdhd.timescale == 20
    assert mdhd.duration == 60

    assert bytes(mdhd) == \
           pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
                "uintbe:64, uintbe:64, uintbe:32, uintbe:64, "
                "bits:1, uint:5, uint:5, uint:5, "
                "bits:16",
                44, b"mdhd", 1, b"\x00\x00\x00",
                creation_time, modification_time, 20, 60,
                0x1, 21, 14, 4,
                b"\x00" * 2)

    moov.append(trak)

    moov.refresh_box_size()

    assert mvhd.next_track_id == len(moov.boxes)

    assert moov.header.type == b"moov"
    assert len(moov.boxes) == 5

    mp4_bytes = b''.join([bytes(ftyp), bytes(mdat), bytes(moov)])

    for box in moov.boxes:
        if isinstance(box, bx_def.TRAK):
            mdia = box.boxes[1]
        else:
            continue

        # trak.mdia.tkhd.name == b"bzna_inputs\0"
        if mdia.boxes[1].name == b"bzna_inputs\0":
            pass
        # trak.mdia.tkhd.name == b"bzna_names\0"
        elif mdia.boxes[1].name == b"bzna_fnames\0":
            # trak.mdia.minf.stbl.stsz
            stsz = mdia.boxes[2].boxes[2].boxes[2]
            # trak.mdia.minf.stbl.stco
            stco = mdia.boxes[2].boxes[2].boxes[4]
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
        # trak.mdia.tkhd.name == b"bzna_targets\0"
        elif mdia.boxes[1].name == b"bzna_targets\0":
            # trak.mdia.minf.stbl.stsz
            stsz = mdia.boxes[2].boxes[2].boxes[2]
            # trak.mdia.minf.stbl.stco
            stco = mdia.boxes[2].boxes[2].boxes[4]
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

    # MOOV.TRAK
    offset = ftyp.header.box_size + mdat.header.header_size
    sizes = [198297, 127477, 192476]
    trak = make_vide_track(creation_time, modification_time, b"VideoHandler\0",
                           sizes, [offset,
                                   offset + sum(sizes[0:1]),
                                   offset + sum(sizes[0:2])])

    # MOOV.TRAK.TKHD
    tkhd = trak.boxes[0]

    # "\x00\x00\x01" trak is enabled
    # "\x00\x00\x02" trak is used in the presentation
    # "\x00\x00\x04" trak is used in the preview
    # "\x00\x00\x08" trak size in not in pixel but in aspect ratio
    tkhd.header.flags = (b"\x00\x00\x03",)

    tkhd.track_id = (1,)
    tkhd.duration = (60,)

    # TODO: make sure that this is the canvas size
    tkhd.width = ([512, 0],)
    tkhd.height = ([512, 0],)

    tkhd.refresh_box_size()

    assert tkhd.header.type == b"tkhd"
    assert tkhd.header.box_size == 104
    assert tkhd.header.flags == b"\x00\x00\x03"

    assert tkhd.track_id == 1
    assert tkhd.duration == 60

    assert tkhd.width == 512
    assert tkhd.height == 512

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

    # MOOV.TRAK.MDIA.MDHD
    mdhd = trak.boxes[-1].boxes[0]
    mdhd.timescale = (20,)
    mdhd.duration = (60,)

    mdhd.refresh_box_size()

    assert mdhd.header.type == b"mdhd"
    assert mdhd.header.box_size == 44
    assert mdhd.timescale == 20
    assert mdhd.duration == 60

    assert bytes(mdhd) == \
           pack("uintbe:32, bytes:4, uintbe:8, bits:24, "
                "uintbe:64, uintbe:64, uintbe:32, uintbe:64, "
                "bits:1, uint:5, uint:5, uint:5, "
                "bits:16",
                44, b"mdhd", 1, b"\x00\x00\x00",
                creation_time, modification_time, 20, 60,
                0x1, 21, 14, 4,
                b"\x00" * 2)

    # MOOV.TRAK.MDIA.MINF.STBL.STSD
    stsd = trak.boxes[-1].boxes[-1].boxes[-1].boxes[0]

    assert stsd.header.type == b"stsd"
    assert len(stsd.boxes) == 1

    # MOOV.TRAK.MDIA.MINF.STBL.STSD.AVC1
    avc1 = stsd.boxes[0]
    avc1.width = (512,)
    avc1.height = (512,)
    avc1.horizresolution = ([72, 0],)
    avc1.vertresolution = ([72, 0],)

    assert avc1.header.type == b"avc1"
    assert avc1.width == 512
    assert avc1.height == 512
    assert avc1.horizresolution == [72, 0]
    assert avc1.vertresolution == [72, 0]

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
