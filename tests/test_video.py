""" Benzina MP4 Parser based on https://github.com/use-sparingly/pymp4parse """

from bitstring import ConstBitStream

from pybzparse import Parser


# TODO: add test_video_guided_parsing
# TODO: add test_video_parsing


def test_video_bytes():
    bstr = ConstBitStream(filename="tests/data/small_vid.mp4")
    boxes = [box for box in Parser.parse(bstr)]

    assert b''.join([bytes(box) for box in boxes]) != bstr.bytes

    for box in boxes:
        box.load(bstr)

    assert b''.join([bytes(box) for box in boxes]) == bstr.bytes
