# MP4 ISO Base Media File Format Parser Library

Parses out and returns a limited set of MP4 boxes

# Usage:

## Parse boxes

    import bitstring as bs

    import pybzparse
    
    bstr = bs.ConstBitStream(filename='my.mp4')
    boxes = pybzparse.Parser.parse(filename='my.mp4')
    for box in boxes:
        print box.header.type
        # Load the box content in memory
        box.load(bstr)

## Check is MP4 file
Reads the first box header at byte 0. Returns `False` if box header does not exist or is invalid  

    >>> pybzparse.Parser.is_mp4(filename='my.mp4')
    True
    >>> pybzparse.Parser.is_mp4(filename='/etc/resolv.conf')
    False
