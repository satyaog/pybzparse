# MP4 ISO Base Media File Format Parser Library

Parses out and returns a limited set of MP4 boxes

# Usage:

## Parse boxes

    import pybzparse
    
    boxes = pybzparse.Parser.parse(filename='my.mp4')
    for box in boxes:
        print box.type
        print dir(box)

## Check is MP4 file
Reads the first box header at byte 0. Returns `False` if box header does not exist or is invalid  

    >>> pybzparse.Parser.is_mp4(filename='my.mp4')
    True
    >>> pybzparse.Parser.is_mp4(filename='/etc/resolv.conf')
    False


### Prerequisites
You'll need:

1. Bitstring - https://pypi.python.org/pypi/bitstring/
