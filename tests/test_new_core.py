from datetime import datetime

from punctual.new_core import punctual
from punctual.new_core import Schedule


def test_example_usage():
    # given
    usr_entries = [
        'Shower; 17:02',
        'Getting ready to go out',
        'Clean',
        'Home -> Rome',
        '25m; 19:30',
        '1h33m',
        'Rome -> Home',
    ]

    usr_synonyms = [
        ('Grocery', 25),
        ('Parking', 15),
        ('Meal', 10),
        ('Clean', 10),
        ('Shower', 20),
        ('Getting ready to go out', 15),
        ('Home -> Rome', 61),
        ('Home -> Movie theater', 80)
    ]

    # when
    result: Schedule = punctual(entries=usr_entries,
                                usr_synonyms=usr_synonyms,
                                usr_start_time=datetime(2024, 5, 23, 13, 29, 0))

    # then
    assert result.__str__() == ('\n'
                                'Total time required: 299.0 minutes\n'
                                'From 17:02 to 22:35\n'
                                'name                     start_time    end_time    duration    extra      '
                                'fixed\n'
                                '-----------------------  ------------  ----------  ----------  ---------  '
                                '-------\n'
                                'Shower                   17:02         17:24       0:22:00                '
                                'True\n'
                                'Getting ready to go out  17:24         17:41       0:17:00                '
                                'False\n'
                                'Clean                    17:41         17:53       0:12:00                '
                                'False\n'
                                'Home -> Rome             17:53         18:56       1:03:00                '
                                'False\n'
                                '25m                      19:30         19:57       0:27:00     + 0:34:00  '
                                'True\n'
                                '1h33m                    19:57         21:32       1:35:00                '
                                'False\n'
                                'Rome -> Home             21:32         22:35       1:03:00                '
                                'False\n')
