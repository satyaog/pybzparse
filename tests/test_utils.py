from datetime import datetime

import utils


def test_to_mp4_date():
    assert utils.to_mp4_time(datetime(2017, 12, 15, 16, 24, 10)) == 3596199850
    assert utils.to_mp4_time(datetime(1904, 1, 1, 0, 0)) == 0


def test_from_mp4_date():
    assert utils.from_mp4_time(3596199850) == datetime(2017, 12, 15, 16, 24, 10)
    assert utils.from_mp4_time(0) == datetime(1904, 1, 1, 0, 0)
