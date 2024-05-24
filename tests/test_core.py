from datetime import datetime

from punctual import hello_world, punctual, prettify_report, prettify_all_dates_in_dict


def test_hello_world():
    assert hello_world() == 'Hello world!'


def test_prettify_all_dates_in_dict():
    # given
    original_shall_not_be_modified = {
        'this': 'is a test',
        'answer': '42',
        'start': datetime(2024, 5, 5, 13, 18),
        'again': {
            'end': datetime(2024, 5, 5, 14, 18),
            'last_i_swear': {
                'end': datetime(2024, 5, 5, 14, 18)
            }
        }
    }

    original = {
        'this': 'is a test',
        'answer': '42',
        'start': datetime(2024, 5, 5, 13, 18),
        'again': {
            'end': datetime(2024, 5, 5, 14, 18),
            'last_i_swear': {
                'end': datetime(2024, 5, 5, 14, 18)
            }
        }
    }

    # when
    result = prettify_all_dates_in_dict(original)

    # then
    assert original == original_shall_not_be_modified
    assert result == {'again': {'end': '14:18', 'last_i_swear': {'end': '14:18'}},
                      'answer': '42',
                      'start': '13:18',
                      'this': 'is a test'}


def test_standard_usage():
    # given
    usr_entries = [
        'shower',
        'eating',
        'Plaza -> Movie Theater',
        '145m',
        'Movie Theater -> Plaza'
    ]

    usr_synonyms = [
        ('Plaza -> Roma', 60),
        ('Plaza -> Movie Theater', 50),
        ('shower', 20),
        ('grocery shopping', 25),
        ('diesel', 15),
        ('eating', 10)
    ]

    # when
    result = punctual(entries=usr_entries,
                      usr_synonyms=usr_synonyms,
                      usr_start_time=datetime(2024, 5, 23, 13, 29, 0))

    # then
    assert prettify_report(result) == ('\n'
                                       'Total time required: 285 minutes\n'
                                       'From 13:29 to 18:14\n'
                                       'entry                     duration  start_time    end_time    overlap\n'
                                       '----------------------  ----------  ------------  ----------  ---------\n'
                                       'Shower                          22  13:29         13:51       False\n'
                                       'Eating                          12  13:51         14:03       False\n'
                                       'Plaza -> movie theater          52  14:03         14:55       False\n'
                                       '145m                           147  14:55         17:22       False\n'
                                       'Movie theater -> plaza          52  17:22         18:14       False\n')


def test_detect_spare_time_in_the_middle_of_two_entries():
    # given
    usr_entries = [
        'shower',
        '30m; 14:00',
        'snack'
    ]

    usr_synonyms = [
        ('shower', 20),
        ('snack', 10)
    ]

    # when
    result = punctual(entries=usr_entries,
                      usr_synonyms=usr_synonyms,
                      usr_start_time=datetime(2024, 5, 23, 13, 29, 0))

    # then
    assert prettify_report(result) == ('\n'
                                       'Total time required: 75 minutes\n'
                                       'From 13:29 to 14:44\n'
                                       'entry         duration  start_time    end_time    overlap\n'
                                       '----------  ----------  ------------  ----------  ---------\n'
                                       'Shower              22  13:29         13:51       False\n'
                                       'SPARE TIME           9  13:51         14:00       False\n'
                                       '30m                 32  14:00         14:32       False\n'
                                       'Snack               12  14:32         14:44       False\n')


def test_detect_spare_time_on_the_first_entry():
    # given
    usr_entries = [
        'shower; 14:00',
        '30m',
        'snack'
    ]

    usr_synonyms = [
        ('shower', 20),
        ('snack', 10)
    ]

    # when
    result = punctual(entries=usr_entries,
                      usr_synonyms=usr_synonyms,
                      usr_start_time=datetime(2024, 5, 23, 13, 29, 0))

    # then
    assert prettify_report(result) == ('\n'
                                       'Total time required: 66 minutes\n'
                                       'From 14:00 to 15:06\n'
                                       'entry      duration  start_time    end_time    overlap\n'
                                       '-------  ----------  ------------  ----------  ---------\n'
                                       'Shower           22  14:00         14:22       False\n'
                                       '30m              32  14:22         14:54       False\n'
                                       'Snack            12  14:54         15:06       False\n')


def test_detect_spare_time_on_the_last_entry():
    # given
    usr_entries = [
        'shower',
        '30m',
        'Barcellona -> Madrid; 18:25'
    ]

    usr_synonyms = [
        ('shower', 20),
        ('Barcellona -> Madrid', 100)
    ]

    # when
    result = punctual(entries=usr_entries,
                      usr_synonyms=usr_synonyms,
                      usr_start_time=datetime(2024, 5, 23, 13, 29, 0))

    # then
    assert prettify_report(result) == ('\n'
                                       'Total time required: 398 minutes\n'
                                       'From 13:29 to 16:05\n'
                                       'entry                   duration  start_time    end_time    overlap\n'
                                       '--------------------  ----------  ------------  ----------  ---------\n'
                                       'Shower                        22  13:29         13:51       False\n'
                                       '30m                           32  13:51         14:23       False\n'
                                       'SPARE TIME                   242  14:23         18:25       False\n'
                                       'Barcellona -> madrid         102  18:25         20:07       False\n')
