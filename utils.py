from datetime import datetime, timedelta

BEGIN = datetime(1904, 1, 1, 0, 0)


def to_mp4_time(date_time):
    return int((date_time - BEGIN).total_seconds())


def from_mp4_time(seconds):
    return BEGIN + timedelta(0, seconds)
