""" Benzina MP4 Parser based on https://github.com/use-sparingly/pymp4parse """

from bitstring import ConstBitStream

from pybzparse import Parser, boxes as bx_def
from pybzparse.boxes import UnknownBox, SingleItemTypeReferenceBox


def test_photo_heic_guided_parsing():
    bstr = ConstBitStream(filename="data/photo.heic")

    box_header = Parser.parse_header(bstr)
    ftyp = bx_def.FTYP.parse_box(bstr, box_header)
    assert ftyp.header.start_pos == 0
    assert ftyp.header.type == b"ftyp"
    assert ftyp.header.box_size == 24
    assert ftyp.major_brand == 1751476579  # b"heic"
    assert ftyp.minor_version == 0
    assert ftyp.compatible_brands == [1835623985,  # b"mif1"
                                      1751476579]  # b"heic"
    assert ftyp.padding == b''

    # meta
    box_header = Parser.parse_header(bstr)
    meta = bx_def.META.parse_box(bstr, box_header)
    assert meta.header.start_pos == 24
    assert meta.header.type == b"meta"
    assert meta.header.box_size == 3955
    assert meta.header.version == 0
    assert meta.header.flags == b"\x00\x00\x00"
    assert meta.padding == b''

    # meta/hdlr
    box_header = Parser.parse_header(bstr)
    hdlr = bx_def.HDLR.parse_box(bstr, box_header)
    assert hdlr.header.start_pos == 36
    assert hdlr.header.type == b"hdlr"
    assert hdlr.header.box_size == 34
    assert hdlr.header.version == 0
    assert hdlr.header.flags == b"\x00\x00\x00"
    assert hdlr.pre_defined == 0
    assert hdlr.handler_type == b"pict"
    assert hdlr.name == b'\0'
    assert hdlr.padding == b'\0'

    # meta/dinf
    box_header = Parser.parse_header(bstr)
    dinf = bx_def.DINF.parse_box(bstr, box_header)
    assert dinf.header.start_pos == 70
    assert dinf.header.type == b"dinf"
    assert dinf.header.box_size == 36
    assert dinf.padding == b''

    # meta/dinf/dref
    box_header = Parser.parse_header(bstr)
    dref = bx_def.DREF.parse_box(bstr, box_header)
    assert dref.header.start_pos == 78
    assert dref.header.type == b"dref"
    assert dref.header.box_size == 28
    assert dref.header.version == 0
    assert dref.header.flags == b"\x00\x00\x00"
    assert dref.entry_count == 1
    assert dref.padding == b''

    # meta/dinf/dref/url_
    box_header = Parser.parse_header(bstr)
    url = bx_def.URL_.parse_box(bstr, box_header)
    assert url.header.start_pos == 94
    assert url.header.type == b"url "
    assert url.header.box_size == 12
    assert url.location is None
    assert url.padding == b''

    # meta/pitm
    box_header = Parser.parse_header(bstr)
    pitm = bx_def.PITM.parse_box(bstr, box_header)
    assert pitm.header.start_pos == 106
    assert pitm.header.type == b"pitm"
    assert pitm.header.box_size == 14
    assert pitm.padding == b''

    # meta/iinf
    box_header = Parser.parse_header(bstr)
    iinf = bx_def.IINF.parse_box(bstr, box_header)
    assert iinf.header.start_pos == 120
    assert iinf.header.type == b"iinf"
    assert iinf.header.box_size == 1085
    assert iinf.entry_count == 51
    assert iinf.padding == b''

    for i in range(iinf.entry_count):
        # meta/iinf/infe
        box_header = Parser.parse_header(bstr)
        infe = bx_def.INFE.parse_box(bstr, box_header)

        if infe.item_id == 49:
            assert infe.header.start_pos == 134 + 48 * 21
            assert infe.header.type == b"infe"
            assert infe.header.box_size == 21
            assert infe.header.version == 2
            assert infe.header.flags == b"\x00\x00\x00"

            assert infe.item_id == 49
            assert infe.item_protection_index == 0
            assert infe.item_type == 1735551332     # b"grid"
            assert infe.item_name == b'\0'
            assert infe.content_type is None
            assert infe.content_encoding is None
            assert infe.item_uri_type is None
            assert infe.extension_type is None
            assert infe.padding == b''
        elif infe.item_id == 50:
            assert infe.header.start_pos == 134 + 49 * 21
            assert infe.header.type == b"infe"
            assert infe.header.box_size == 21
            assert infe.header.version == 2
            assert infe.header.flags == b"\x00\x00\x00"

            assert infe.item_id == 50
            assert infe.item_protection_index == 0
            assert infe.item_type == 1752589105     # b"hvc1"
            assert infe.item_name == b'\0'
            assert infe.content_type is None
            assert infe.content_encoding is None
            assert infe.item_uri_type is None
            assert infe.extension_type is None
            assert infe.padding == b''
        elif infe.item_id == 51:
            assert infe.header.start_pos == 134 + 50 * 21
            assert infe.header.type == b"infe"
            assert infe.header.box_size == 21
            assert infe.header.version == 2
            assert infe.header.flags == b"\x00\x00\x01"

            assert infe.item_id == 51
            assert infe.item_protection_index == 0
            assert infe.item_type == 1165519206     # b"Exif"
            assert infe.item_name == b'\0'
            assert infe.content_type is None
            assert infe.content_encoding is None
            assert infe.item_uri_type is None
            assert infe.extension_type is None
            assert infe.padding == b''
        else:
            assert infe.header.start_pos == 134 + i * 21
            assert infe.header.type == b"infe"
            assert infe.header.box_size == 21
            assert infe.header.version == 2
            assert infe.header.flags == b"\x00\x00\x01"

            assert infe.item_id == i + 1
            assert infe.item_protection_index == 0
            assert infe.item_type == 1752589105     # b"hvc1"
            assert infe.item_name == b'\0'
            assert infe.content_type is None
            assert infe.content_encoding is None
            assert infe.item_uri_type is None
            assert infe.extension_type is None
            assert infe.padding == b''

    # meta/iref
    box_header = Parser.parse_header(bstr)
    iref = bx_def.IREF.parse_box(bstr, box_header)
    assert iref.header.start_pos == 1205
    assert iref.header.type == b"iref"
    assert iref.header.box_size == 148
    assert iref.header.version == 0
    assert iref.header.flags == b"\x00\x00\x00"
    assert iref.padding == b''

    # meta/iref/dimg
    box_header = Parser.parse_header(bstr)
    dimg = SingleItemTypeReferenceBox.parse_box(bstr, box_header)
    assert dimg.header.start_pos == 1217
    assert dimg.header.type == b"dimg"
    assert dimg.header.box_size == 108
    assert dimg.from_item_id == 49
    assert dimg.reference_count == 48
    assert dimg.to_item_ids == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
                                15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26,
                                27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38,
                                39, 40, 41, 42, 43, 44, 45, 46, 47, 48]
    assert dimg.padding == b''

    # meta/iref/thmb
    box_header = Parser.parse_header(bstr)
    thmb = SingleItemTypeReferenceBox.parse_box(bstr, box_header)
    assert thmb.header.start_pos == 1325
    assert thmb.header.type == b"thmb"
    assert thmb.header.box_size == 14
    assert thmb.from_item_id == 50
    assert thmb.reference_count == 1
    assert thmb.to_item_ids == [49]
    assert thmb.padding == b''

    # meta/iref/cdsc
    box_header = Parser.parse_header(bstr)
    cdsc = SingleItemTypeReferenceBox.parse_box(bstr, box_header)
    assert cdsc.header.start_pos == 1339
    assert cdsc.header.type == b"cdsc"
    assert cdsc.header.box_size == 14
    assert cdsc.from_item_id == 51
    assert cdsc.reference_count == 1
    assert cdsc.to_item_ids == [49]
    assert cdsc.padding == b''

    # meta/iprp
    box_header = Parser.parse_header(bstr)
    iprp = bx_def.IPRP.parse_box(bstr, box_header)
    assert iprp.header.start_pos == 1353
    assert iprp.header.type == b"iprp"
    assert iprp.header.box_size == 1778
    assert iprp.padding == b''

    # meta/iprp/ipco
    box_header = Parser.parse_header(bstr)
    ipco = bx_def.IPCO.parse_box(bstr, box_header)
    assert ipco.header.start_pos == 1361
    assert ipco.header.type == b"ipco"
    assert ipco.header.box_size == 1452
    assert ipco.padding == b''

    # meta/iprp/ipco/colr
    box_header = Parser.parse_header(bstr)
    colr = UnknownBox.parse_box(bstr, box_header)
    assert colr.header.start_pos == 1369
    assert colr.header.type == b"colr"
    assert colr.header.box_size == 560
    assert colr.padding == b''

    # meta/iprp/ipco/hvcC
    box_header = Parser.parse_header(bstr)
    hvcC = UnknownBox.parse_box(bstr, box_header)
    assert hvcC.header.start_pos == 1929
    assert hvcC.header.type == b"hvcC"
    assert hvcC.header.box_size == 112
    assert hvcC.padding == b''

    # meta/iprp/ipco/ispe
    box_header = Parser.parse_header(bstr)
    ispe = UnknownBox.parse_box(bstr, box_header)
    assert ispe.header.start_pos == 2041
    assert ispe.header.type == b"ispe"
    assert ispe.header.box_size == 20
    assert ispe.padding == b''

    # meta/iprp/ipco/ispe
    box_header = Parser.parse_header(bstr)
    ispe = UnknownBox.parse_box(bstr, box_header)
    assert ispe.header.start_pos == 2061
    assert ispe.header.type == b"ispe"
    assert ispe.header.box_size == 20
    assert ispe.padding == b''

    # meta/iprp/ipco/irot
    box_header = Parser.parse_header(bstr)
    irot = UnknownBox.parse_box(bstr, box_header)
    assert irot.header.start_pos == 2081
    assert irot.header.type == b"irot"
    assert irot.header.box_size == 9
    assert irot.padding == b''

    # meta/iprp/ipco/pixi
    box_header = Parser.parse_header(bstr)
    pixi = UnknownBox.parse_box(bstr, box_header)
    assert pixi.header.start_pos == 2090
    assert pixi.header.type == b"pixi"
    assert pixi.header.box_size == 16
    assert pixi.padding == b''

    # meta/iprp/ipco/colr
    box_header = Parser.parse_header(bstr)
    colr = UnknownBox.parse_box(bstr, box_header)
    assert colr.header.start_pos == 2106
    assert colr.header.type == b"colr"
    assert colr.header.box_size == 560
    assert colr.padding == b''

    # meta/iprp/ipco/hvcC
    box_header = Parser.parse_header(bstr)
    hvcC = UnknownBox.parse_box(bstr, box_header)
    assert hvcC.header.start_pos == 2666
    assert hvcC.header.type == b"hvcC"
    assert hvcC.header.box_size == 111
    assert hvcC.padding == b''

    # meta/iprp/ipco/ispe
    box_header = Parser.parse_header(bstr)
    ispe = UnknownBox.parse_box(bstr, box_header)
    assert ispe.header.start_pos == 2777
    assert ispe.header.type == b"ispe"
    assert ispe.header.box_size == 20
    assert ispe.padding == b''

    # meta/iprp/ipco/pixi
    box_header = Parser.parse_header(bstr)
    pixi = UnknownBox.parse_box(bstr, box_header)
    assert pixi.header.start_pos == 2797
    assert pixi.header.type == b"pixi"
    assert pixi.header.box_size == 16
    assert pixi.padding == b''

    # meta/iprp/ipma
    box_header = Parser.parse_header(bstr)
    ipma = bx_def.IPMA.parse_box(bstr, box_header)
    assert ipma.header.start_pos == 2813
    assert ipma.header.type == b"ipma"
    assert ipma.header.box_size == 318
    assert ipma.header.version == 0
    assert ipma.header.flags == b"\x00\x00\x00"
    assert ipma.entry_count == 50
    assert len(ipma.entries) == 0
    assert ipma.padding == b''

    ipma.load(bstr)
    assert len(ipma.entries) == 50
    assert ipma.padding == b''

    entry = ipma.entries[0]
    assert entry.item_id == 1
    assert entry.association_count == 3
    assert len(entry.associations) == 3
    association = entry.associations[0]
    assert association.essential == 1
    assert association.property_index == 3
    association = entry.associations[1]
    assert association.essential == 1
    assert association.property_index == 1
    association = entry.associations[2]
    assert association.essential == 1
    assert association.property_index == 2

    entry = ipma.entries[1]
    assert entry.item_id == 2
    assert entry.association_count == 3
    assert len(entry.associations) == 3
    association = entry.associations[0]
    assert association.essential == 1
    assert association.property_index == 3
    association = entry.associations[1]
    assert association.essential == 1
    assert association.property_index == 1
    association = entry.associations[2]
    assert association.essential == 1
    assert association.property_index == 2

    entry = ipma.entries[48]
    assert entry.item_id == 49
    assert entry.association_count == 3
    assert len(entry.associations) == 3
    association = entry.associations[0]
    assert association.essential == 0
    assert association.property_index == 4
    association = entry.associations[1]
    assert association.essential == 1
    assert association.property_index == 5
    association = entry.associations[2]
    assert association.essential == 0
    assert association.property_index == 6

    entry = ipma.entries[49]
    assert entry.item_id == 50
    assert entry.association_count == 5
    assert len(entry.associations) == 5
    association = entry.associations[0]
    assert association.essential == 1
    assert association.property_index == 7
    association = entry.associations[1]
    assert association.essential == 1
    assert association.property_index == 8
    association = entry.associations[2]
    assert association.essential == 0
    assert association.property_index == 9
    association = entry.associations[3]
    assert association.essential == 1
    assert association.property_index == 5
    association = entry.associations[4]
    assert association.essential == 0
    assert association.property_index == 10

    # meta/idat
    box_header = Parser.parse_header(bstr)
    idat = bx_def.IDAT.parse_box(bstr, box_header)
    idat.load(bstr)
    assert idat.header.start_pos == 3131
    assert idat.header.type == b"idat"
    assert idat.header.box_size == 16
    assert len(idat.data) == 8
    assert idat.data[0] == int.from_bytes(b"\x00", "big")
    assert idat.data[1] == int.from_bytes(b"\x00", "big")
    assert idat.data[6] == int.from_bytes(b"\x0b", "big")
    assert idat.data[7] == int.from_bytes(b"\xd0", "big")
    assert idat.padding == b''

    # meta/iloc
    box_header = Parser.parse_header(bstr)
    iloc = bx_def.ILOC.parse_box(bstr, box_header)
    assert iloc.header.start_pos == 3147
    assert iloc.header.type == b"iloc"
    assert iloc.header.box_size == 832
    assert iloc.header.version == 1
    assert iloc.header.flags == b"\x00\x00\x00"
    assert iloc.padding == b''

    assert iloc.offset_size == 4
    assert iloc.length_size == 4
    assert iloc.base_offset_size == 0
    assert iloc.index_size == 0
    assert iloc.item_count == 51
    assert len(iloc.items) == 0
    assert iloc.padding == b''

    iloc.load(bstr)
    assert len(iloc.items) == 51
    assert iloc.padding == b''

    item = iloc.items[0]
    assert item.item_id == 1
    assert item.construction_method == 0
    assert item.data_reference_index == 0
    assert item.base_offset is None
    assert item.extent_count == 1
    assert len(item.extents) == 1
    extent = item.extents[0]
    assert extent.extent_index is None
    assert extent.extent_offset == 14854
    assert extent.extent_length == 33763

    item = iloc.items[1]
    assert item.item_id == 2
    assert item.construction_method == 0
    assert item.data_reference_index == 0
    assert item.base_offset is None
    assert item.extent_count == 1
    assert len(item.extents) == 1
    extent = item.extents[0]
    assert extent.extent_index is None
    assert extent.extent_offset == 48617
    assert extent.extent_length == 35158

    item = iloc.items[49]
    assert item.item_id == 50
    assert item.construction_method == 0
    assert item.data_reference_index == 0
    assert item.base_offset is None
    assert item.extent_count == 1
    assert len(item.extents) == 1
    extent = item.extents[0]
    assert extent.extent_index is None
    assert extent.extent_offset == 3995
    assert extent.extent_length == 8651

    item = iloc.items[50]
    assert item.item_id == 51
    assert item.construction_method == 0
    assert item.data_reference_index == 0
    assert item.base_offset is None
    assert item.extent_count == 1
    assert len(item.extents) == 1
    extent = item.extents[0]
    assert extent.extent_index is None
    assert extent.extent_offset == 12646
    assert extent.extent_length == 2208

    # mdat
    box_header = Parser.parse_header(bstr)
    mdat = bx_def.MDAT.parse_box(bstr, box_header)
    mdat.load(bstr)
    assert mdat.header.start_pos == 3979
    assert mdat.header.type == b"mdat"
    assert mdat.header.box_size == 1350049
    assert len(mdat.data) == 1350033
    assert mdat.data[0] == int.from_bytes(b"\x00", "big")
    assert mdat.data[1] == int.from_bytes(b"\x00", "big")
    assert mdat.data[6] == int.from_bytes(b"\xaf", "big")
    assert mdat.data[7] == int.from_bytes(b"\x88", "big")
    assert mdat.data[1350031] == int.from_bytes(b"\xfd", "big")
    assert mdat.data[1350032] == int.from_bytes(b"\x80", "big")
    assert mdat.padding == b''


def test_photo_heic_parsing():
    bstr = ConstBitStream(filename="data/photo.heic")

    meta = None

    for i, box in enumerate(Parser.parse(bstr)):
        if i == 0:
            # ftyp
            ftyp = box
            assert isinstance(ftyp, bx_def.FTYP)
            assert ftyp.header.start_pos == 0
            assert ftyp.header.type == b"ftyp"
            assert ftyp.header.box_size == 24
            assert ftyp.major_brand == 1751476579  # b"heic"
            assert ftyp.minor_version == 0
            assert ftyp.compatible_brands == [1835623985,  # b"mif1"
                                              1751476579]  # b"heic"
            assert ftyp.padding == b''

        elif i == 1:
            # meta
            meta = box
            assert isinstance(meta, bx_def.META)
            assert meta.header.start_pos == 24
            assert meta.header.type == b"meta"
            assert meta.header.box_size == 3955
            assert meta.header.version == 0
            assert meta.header.flags == b"\x00\x00\x00"
            assert len(meta.boxes) == 8
            assert meta.padding == b''

        elif i == 2:
            # mdat
            mdat = box
            assert isinstance(mdat, bx_def.MDAT)
            assert mdat.header.start_pos == 3979
            assert mdat.header.type == b"mdat"
            assert mdat.header.box_size == 1350049
            assert mdat.padding == b''

        assert i < 3

    # meta/hdlr
    hdlr = meta.boxes[0]
    assert isinstance(hdlr, bx_def.HDLR)
    assert hdlr.header.start_pos == 36
    assert hdlr.header.type == b"hdlr"
    assert hdlr.header.box_size == 34
    assert hdlr.header.version == 0
    assert hdlr.header.flags == b"\x00\x00\x00"
    assert hdlr.pre_defined == 0
    assert hdlr.handler_type == b"pict"
    assert hdlr.name == b'\0'
    assert hdlr.padding == b'\0'

    # meta/dinf
    dinf = meta.boxes[1]
    assert isinstance(dinf, bx_def.DINF)
    assert dinf.header.start_pos == 70
    assert dinf.header.type == b"dinf"
    assert dinf.header.box_size == 36
    assert len(dinf.boxes) == 1
    assert dinf.padding == b''

    # meta/dinf/dref
    dref = dinf.boxes[0]
    assert isinstance(dref, bx_def.DREF)
    assert dref.header.start_pos == 78
    assert dref.header.type == b"dref"
    assert dref.header.box_size == 28
    assert dref.header.version == 0
    assert dref.header.flags == b"\x00\x00\x00"
    assert dref.entry_count == 1
    assert len(dref.boxes) == 1
    assert dref.padding == b''

    # meta/dinf/dref/url_
    url = dref.boxes[0]
    assert isinstance(url, bx_def.URL_)
    assert url.header.start_pos == 94
    assert url.header.type == b"url "
    assert url.header.box_size == 12
    assert url.location is None
    assert url.padding == b''

    # meta/pitm
    pitm = meta.boxes[2]
    assert isinstance(pitm, bx_def.PITM)
    assert pitm.header.start_pos == 106
    assert pitm.header.type == b"pitm"
    assert pitm.header.box_size == 14
    assert pitm.padding == b''

    # meta/iinf
    iinf = meta.boxes[3]
    assert isinstance(iinf, bx_def.IINF)
    assert iinf.header.start_pos == 120
    assert iinf.header.type == b"iinf"
    assert iinf.header.box_size == 1085
    assert iinf.entry_count == 51
    assert len(iinf.boxes) == 51
    assert iinf.padding == b''

    for i, infe in enumerate(iinf.boxes):
        # meta/iinf/infe
        assert isinstance(infe, bx_def.INFE)

        if infe.item_id == 49:
            assert infe.header.start_pos == 134 + 48 * 21
            assert infe.header.type == b"infe"
            assert infe.header.box_size == 21
            assert infe.header.version == 2
            assert infe.header.flags == b"\x00\x00\x00"

            assert infe.item_id == 49
            assert infe.item_protection_index == 0
            assert infe.item_type == 1735551332     # b"grid"
            assert infe.item_name == b'\0'
            assert infe.content_type is None
            assert infe.content_encoding is None
            assert infe.item_uri_type is None
            assert infe.extension_type is None
            assert infe.padding == b''
        elif infe.item_id == 50:
            assert infe.header.start_pos == 134 + 49 * 21
            assert infe.header.type == b"infe"
            assert infe.header.box_size == 21
            assert infe.header.version == 2
            assert infe.header.flags == b"\x00\x00\x00"

            assert infe.item_id == 50
            assert infe.item_protection_index == 0
            assert infe.item_type == 1752589105     # b"hvc1"
            assert infe.item_name == b'\0'
            assert infe.content_type is None
            assert infe.content_encoding is None
            assert infe.item_uri_type is None
            assert infe.extension_type is None
            assert infe.padding == b''
        elif infe.item_id == 51:
            assert infe.header.start_pos == 134 + 50 * 21
            assert infe.header.type == b"infe"
            assert infe.header.box_size == 21
            assert infe.header.version == 2
            assert infe.header.flags == b"\x00\x00\x01"

            assert infe.item_id == 51
            assert infe.item_protection_index == 0
            assert infe.item_type == 1165519206     # b"Exif"
            assert infe.item_name == b'\0'
            assert infe.content_type is None
            assert infe.content_encoding is None
            assert infe.item_uri_type is None
            assert infe.extension_type is None
            assert infe.padding == b''
        else:
            assert infe.header.start_pos == 134 + i * 21
            assert infe.header.type == b"infe"
            assert infe.header.box_size == 21
            assert infe.header.version == 2
            assert infe.header.flags == b"\x00\x00\x01"

            assert infe.item_id == i + 1
            assert infe.item_protection_index == 0
            assert infe.item_type == 1752589105     # b"hvc1"
            assert infe.item_name == b'\0'
            assert infe.content_type is None
            assert infe.content_encoding is None
            assert infe.item_uri_type is None
            assert infe.extension_type is None
            assert infe.padding == b''

    # meta/iref
    iref = meta.boxes[4]
    assert isinstance(iref, bx_def.IREF)
    assert iref.header.start_pos == 1205
    assert iref.header.type == b"iref"
    assert iref.header.box_size == 148
    assert iref.header.version == 0
    assert iref.header.flags == b"\x00\x00\x00"
    assert len(iref.boxes) == 3
    assert iref.padding == b''

    # meta/iref/dimg
    dimg = iref.boxes[0]
    assert dimg.header.start_pos == 1217
    assert dimg.header.type == b"dimg"
    assert dimg.header.box_size == 108
    assert dimg.from_item_id == 49
    assert dimg.reference_count == 48
    assert dimg.to_item_ids == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
                                15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26,
                                27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38,
                                39, 40, 41, 42, 43, 44, 45, 46, 47, 48]
    assert dimg.padding == b''

    # meta/iref/thmb
    thmb = iref.boxes[1]
    assert thmb.header.start_pos == 1325
    assert thmb.header.type == b"thmb"
    assert thmb.header.box_size == 14
    assert thmb.from_item_id == 50
    assert thmb.reference_count == 1
    assert thmb.to_item_ids == [49]
    assert thmb.padding == b''

    # meta/iref/cdsc
    cdsc = iref.boxes[2]
    assert cdsc.header.start_pos == 1339
    assert cdsc.header.type == b"cdsc"
    assert cdsc.header.box_size == 14
    assert cdsc.from_item_id == 51
    assert cdsc.reference_count == 1
    assert cdsc.to_item_ids == [49]
    assert cdsc.padding == b''

    # meta/iprp
    iprp = meta.boxes[5]
    assert isinstance(iprp, bx_def.IPRP)
    assert iprp.header.start_pos == 1353
    assert iprp.header.type == b"iprp"
    assert iprp.header.box_size == 1778
    assert len(iprp.boxes) == 2
    assert iprp.padding == b''

    # meta/iprp/ipco
    ipco = iprp.boxes[0]
    assert isinstance(ipco, bx_def.IPCO)
    assert ipco.header.start_pos == 1361
    assert ipco.header.type == b"ipco"
    assert ipco.header.box_size == 1452
    assert len(ipco.boxes) == 10
    assert ipco.padding == b''

    # meta/iprp/ipco/colr
    colr = ipco.boxes[0]
    assert colr.header.start_pos == 1369
    assert colr.header.type == b"colr"
    assert colr.header.box_size == 560
    assert colr.padding == b''

    # meta/iprp/ipco/hvcC
    hvcC = ipco.boxes[1]
    assert hvcC.header.start_pos == 1929
    assert hvcC.header.type == b"hvcC"
    assert hvcC.header.box_size == 112
    assert hvcC.padding == b''

    # meta/iprp/ipco/ispe
    ispe = ipco.boxes[2]
    assert ispe.header.start_pos == 2041
    assert ispe.header.type == b"ispe"
    assert ispe.header.box_size == 20
    assert ispe.padding == b''

    # meta/iprp/ipco/ispe
    ispe = ipco.boxes[3]
    assert ispe.header.start_pos == 2061
    assert ispe.header.type == b"ispe"
    assert ispe.header.box_size == 20
    assert ispe.padding == b''

    # meta/iprp/ipco/irot
    irot = ipco.boxes[4]
    assert irot.header.start_pos == 2081
    assert irot.header.type == b"irot"
    assert irot.header.box_size == 9
    assert irot.padding == b''

    # meta/iprp/ipco/pixi
    pixi = ipco.boxes[5]
    assert pixi.header.start_pos == 2090
    assert pixi.header.type == b"pixi"
    assert pixi.header.box_size == 16
    assert pixi.padding == b''

    # meta/iprp/ipco/colr
    colr = ipco.boxes[6]
    assert colr.header.start_pos == 2106
    assert colr.header.type == b"colr"
    assert colr.header.box_size == 560
    assert colr.padding == b''

    # meta/iprp/ipco/hvcC
    hvcC = ipco.boxes[7]
    assert hvcC.header.start_pos == 2666
    assert hvcC.header.type == b"hvcC"
    assert hvcC.header.box_size == 111
    assert hvcC.padding == b''

    # meta/iprp/ipco/ispe
    ispe = ipco.boxes[8]
    assert ispe.header.start_pos == 2777
    assert ispe.header.type == b"ispe"
    assert ispe.header.box_size == 20
    assert ispe.padding == b''

    # meta/iprp/ipco/pixi
    pixi = ipco.boxes[9]
    assert pixi.header.start_pos == 2797
    assert pixi.header.type == b"pixi"
    assert pixi.header.box_size == 16
    assert pixi.padding == b''

    # meta/iprp/ipma
    ipma = iprp.boxes[1]
    assert isinstance(ipma, bx_def.IPMA)
    assert ipma.header.start_pos == 2813
    assert ipma.header.type == b"ipma"
    assert ipma.header.box_size == 318
    assert ipma.header.version == 0
    assert ipma.header.flags == b"\x00\x00\x00"
    assert ipma.entry_count == 50
    assert len(ipma.entries) == 0
    assert ipma.padding == b''

    ipma.load(bstr)
    assert len(ipma.entries) == 50
    assert ipma.padding == b''

    entry = ipma.entries[0]
    assert entry.item_id == 1
    assert entry.association_count == 3
    assert len(entry.associations) == 3
    association = entry.associations[0]
    assert association.essential == 1
    assert association.property_index == 3
    association = entry.associations[1]
    assert association.essential == 1
    assert association.property_index == 1
    association = entry.associations[2]
    assert association.essential == 1
    assert association.property_index == 2

    entry = ipma.entries[1]
    assert entry.item_id == 2
    assert entry.association_count == 3
    assert len(entry.associations) == 3
    association = entry.associations[0]
    assert association.essential == 1
    assert association.property_index == 3
    association = entry.associations[1]
    assert association.essential == 1
    assert association.property_index == 1
    association = entry.associations[2]
    assert association.essential == 1
    assert association.property_index == 2

    entry = ipma.entries[48]
    assert entry.item_id == 49
    assert entry.association_count == 3
    assert len(entry.associations) == 3
    association = entry.associations[0]
    assert association.essential == 0
    assert association.property_index == 4
    association = entry.associations[1]
    assert association.essential == 1
    assert association.property_index == 5
    association = entry.associations[2]
    assert association.essential == 0
    assert association.property_index == 6

    entry = ipma.entries[49]
    assert entry.item_id == 50
    assert entry.association_count == 5
    assert len(entry.associations) == 5
    association = entry.associations[0]
    assert association.essential == 1
    assert association.property_index == 7
    association = entry.associations[1]
    assert association.essential == 1
    assert association.property_index == 8
    association = entry.associations[2]
    assert association.essential == 0
    assert association.property_index == 9
    association = entry.associations[3]
    assert association.essential == 1
    assert association.property_index == 5
    association = entry.associations[4]
    assert association.essential == 0
    assert association.property_index == 10

    # meta/idat
    idat = meta.boxes[6]
    assert isinstance(idat, bx_def.IDAT)
    assert idat.header.start_pos == 3131
    assert idat.header.type == b"idat"
    assert idat.header.box_size == 16
    assert idat.padding == b''

    # meta/iloc
    iloc = meta.boxes[7]
    assert isinstance(iloc, bx_def.ILOC)
    assert iloc.header.start_pos == 3147
    assert iloc.header.type == b"iloc"
    assert iloc.header.box_size == 832
    assert iloc.header.version == 1
    assert iloc.header.flags == b"\x00\x00\x00"

    assert iloc.offset_size == 4
    assert iloc.length_size == 4
    assert iloc.base_offset_size == 0
    assert iloc.index_size == 0
    assert iloc.item_count == 51
    assert len(iloc.items) == 0
    assert iloc.padding == b''

    iloc.load(bstr)
    assert len(iloc.items) == 51
    assert iloc.padding == b''

    item = iloc.items[0]
    assert item.item_id == 1
    assert item.construction_method == 0
    assert item.data_reference_index == 0
    assert item.base_offset is None
    assert item.extent_count == 1
    assert len(item.extents) == 1
    extent = item.extents[0]
    assert extent.extent_index is None
    assert extent.extent_offset == 14854
    assert extent.extent_length == 33763

    item = iloc.items[1]
    assert item.item_id == 2
    assert item.construction_method == 0
    assert item.data_reference_index == 0
    assert item.base_offset is None
    assert item.extent_count == 1
    assert len(item.extents) == 1
    extent = item.extents[0]
    assert extent.extent_index is None
    assert extent.extent_offset == 48617
    assert extent.extent_length == 35158

    item = iloc.items[49]
    assert item.item_id == 50
    assert item.construction_method == 0
    assert item.data_reference_index == 0
    assert item.base_offset is None
    assert item.extent_count == 1
    assert len(item.extents) == 1
    extent = item.extents[0]
    assert extent.extent_index is None
    assert extent.extent_offset == 3995
    assert extent.extent_length == 8651

    item = iloc.items[50]
    assert item.item_id == 51
    assert item.construction_method == 0
    assert item.data_reference_index == 0
    assert item.base_offset is None
    assert item.extent_count == 1
    assert len(item.extents) == 1
    extent = item.extents[0]
    assert extent.extent_index is None
    assert extent.extent_offset == 12646
    assert extent.extent_length == 2208


def test_photo_heic_bytes():
    bstr = ConstBitStream(filename="data/photo.heic")
    boxes = [box for box in Parser.parse(bstr)]

    assert b''.join([bytes(box) for box in boxes]) != bstr.bytes

    for box in boxes:
        box.load(bstr)

    assert b''.join([bytes(box) for box in boxes]) == bstr.bytes
