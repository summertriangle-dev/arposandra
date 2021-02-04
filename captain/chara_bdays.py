from datetime import datetime, timezone, timedelta

from .banners import BirthdayBanner

JST = timezone(timedelta(hours=9))

# TODO: move this somewhere else
BIRTHDAYS = {
    (8, 3): BirthdayBanner(1, datetime(3048, 8, 3, tzinfo=JST)),
    (10, 21): BirthdayBanner(2, datetime(3048, 10, 21, tzinfo=JST)),
    (9, 12): BirthdayBanner(3, datetime(3048, 9, 12, tzinfo=JST)),
    (3, 15): BirthdayBanner(4, datetime(3048, 3, 15, tzinfo=JST)),
    (11, 1): BirthdayBanner(5, datetime(3048, 11, 1, tzinfo=JST)),
    (4, 19): BirthdayBanner(6, datetime(3048, 4, 19, tzinfo=JST)),
    (6, 9): BirthdayBanner(7, datetime(3048, 6, 9, tzinfo=JST)),
    (1, 17): BirthdayBanner(8, datetime(3048, 1, 17, tzinfo=JST)),
    (7, 22): BirthdayBanner(9, datetime(3048, 7, 22, tzinfo=JST)),
    (8, 1): BirthdayBanner(101, datetime(3048, 8, 1, tzinfo=JST)),
    (9, 19): BirthdayBanner(102, datetime(3048, 9, 19, tzinfo=JST)),
    (2, 10): BirthdayBanner(103, datetime(3048, 2, 10, tzinfo=JST)),
    (1, 1): BirthdayBanner(104, datetime(3048, 1, 1, tzinfo=JST)),
    (4, 17): BirthdayBanner(105, datetime(3048, 4, 17, tzinfo=JST)),
    (7, 13): BirthdayBanner(106, datetime(3048, 7, 13, tzinfo=JST)),
    (3, 4): BirthdayBanner(107, datetime(3048, 3, 4, tzinfo=JST)),
    (6, 13): BirthdayBanner(108, datetime(3048, 6, 13, tzinfo=JST)),
    (9, 21): BirthdayBanner(109, datetime(3048, 9, 21, tzinfo=JST)),
    (3, 1): BirthdayBanner(201, datetime(3048, 3, 1, tzinfo=JST)),
    (1, 23): BirthdayBanner(202, datetime(3048, 1, 23, tzinfo=JST)),
    (4, 3): BirthdayBanner(203, datetime(3048, 4, 3, tzinfo=JST)),
    (6, 29): BirthdayBanner(204, datetime(3048, 6, 29, tzinfo=JST)),
    (5, 30): BirthdayBanner(205, datetime(3048, 5, 30, tzinfo=JST)),
    (12, 16): BirthdayBanner(206, datetime(3048, 12, 16, tzinfo=JST)),
    (8, 8): BirthdayBanner(207, datetime(3048, 8, 8, tzinfo=JST)),
    (2, 5): BirthdayBanner(208, datetime(3048, 2, 5, tzinfo=JST)),
    (11, 13): BirthdayBanner(209, datetime(3048, 11, 13, tzinfo=JST)),
    (10, 5): BirthdayBanner(210, datetime(3048, 10, 5, tzinfo=JST)),
}