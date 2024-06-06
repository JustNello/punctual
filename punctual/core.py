import re

from datetime import datetime, timedelta
from typing import List
from typing import Tuple
from typing import LiteralString

from tabulate import tabulate

# GLOBALS (they must not be visible outside this module)

DIRECTION_SYMBOL = ' -> '
ENTRY_DETAIL_SEPARATOR = ';'


# IMPLEMENTATION


def hello_world():
    return 'Hello world!'


def is_direction(entry: str) -> bool:
    return DIRECTION_SYMBOL in entry


def is_synonym(entry: str, synonyms: dict) -> bool:
    key = direction_key(entry) if is_direction(entry) else synonym_key(entry)
    return synonyms.get(key) is not None


def locations_in_direction(entry: str) -> List[str]:
    if not is_direction(entry):
        raise ValueError('Expected an entry that represents a direction, that is a trip from a location to another')
    return entry.lower().split(DIRECTION_SYMBOL)


def direction_key(entry: str) -> str:
    locations = locations_in_direction(entry)
    locations.sort()
    # expected at max two locations
    return f'{locations[0]} - {locations[1]}'


def start_location(entry: str) -> str:
    return locations_in_direction(entry)[0]


def end_location(entry: str) -> str:
    return locations_in_direction(entry)[1]


def synonym_key(entry: str) -> str:
    return entry.lower()


def add_synonym_duration(entry: str, synonyms: dict, duration_in_minutes: int):
    key = direction_key(entry) if is_direction(entry) else synonym_key(entry)
    synonyms[key] = {'duration': duration_in_minutes}


def get_synonym_duration(entry: str, synonyms: dict) -> int:
    key = direction_key(entry) if is_direction(entry) else synonym_key(entry)
    return synonyms[key]['duration']


def get_duration(entry: str, synonyms: dict) -> int:
    # always do an attempt to get duration from entries such as:
    # "1h33m", "30m", "2h"
    entry_duration_minutes = parse_duration(entry)

    # entry is in the form of a synonym, such as:
    # "Rome -> Paris", "Shower"
    if entry_duration_minutes == 0 and is_synonym(entry, synonyms):
        entry_duration_minutes = get_synonym_duration(entry, synonyms)

    return entry_duration_minutes


def parse_duration(entry: str) -> int:
    """
    Convert a duration string like '1h30m', '1h', or '23m' into the total number of minutes as an integer.

    Parameters:
        entry (str): The duration string.

    Returns:
        int: The total duration in minutes.
    """
    hours = 0
    minutes = 0

    # Regular expressions to find hours and minutes
    hours_match = re.search(r'(\d+)h', entry)
    minutes_match = re.search(r'(\d+)m', entry)

    if hours_match:
        hours = int(hours_match.group(1))

    if minutes_match:
        minutes = int(minutes_match.group(1))

    total_minutes = hours * 60 + minutes

    return total_minutes


def datetime_plus_minutes(date: datetime, minutes) -> datetime:
    return date + timedelta(minutes=minutes)


def prettify_date(date: datetime) -> str:
    return date.strftime('%H:%M')


def prettify_all_dates_in_list(obj: list, perform_copy: bool = True) -> list:
    copy = obj.copy() if perform_copy else obj
    result = []
    for value in copy:
        if isinstance(value, datetime):
            result.append(value)
        elif isinstance(value, list):
            result.append(prettify_all_dates_in_list(value, perform_copy=False))
        elif isinstance(value, dict):
            result.append(prettify_all_dates_in_dict(value))
    return result


def prettify_all_dates_in_dict(obj: dict, perform_copy: bool = True) -> dict:
    copy = obj.copy() if perform_copy else obj
    result = {}
    for key, value in copy.items():
        if isinstance(value, datetime):
            result[key] = prettify_date(value)
        elif isinstance(value, dict):
            # root object has already been copied
            result[key] = prettify_all_dates_in_dict(value, perform_copy=False)
        elif isinstance(value, list):
            result[key] = prettify_all_dates_in_list(value)
        else:
            result[key] = value
    return result


def prettify_report(report: dict, headers: List[str] = None) -> str:
    # TODO contribute to 'tabulate' library for custom formats of dates
    result = prettify_all_dates_in_dict(report)

    if headers:
        _entries = [headers] + [entry.values() for entry in result['entries']]
        _headers = 'firstrow'
    else:
        _entries = result['entries']
        _headers = 'keys'

    return f'''
Total time required: {round(result['total_duration_minutes'])} minutes
From {result['start_time']} to {result['end_time']}
{tabulate(_entries, headers=_headers)}
'''


def is_first_entry(user_output: dict) -> bool:
    return len(user_output['entries']) == 0


def parse_at(at_as_string: str, start_time: datetime) -> datetime:
    return datetime.combine(date=start_time.date(),
                            time=datetime.strptime(at_as_string, '%H:%M').time())


def parse_entry(parsable_entry: str, start_time: datetime):
    def haircut(parts: List[str]) -> List[str]:
        return [p.strip() for p in parts]

    if ';' in parsable_entry:
        entry, at_as_string = haircut(parsable_entry.split(';'))
        return entry, parse_at(at_as_string, start_time)
    return parsable_entry, None


def is_overlap(previous: datetime, after: datetime) -> bool:
    return previous > after


def minutes_between_entries(previous: datetime, after: datetime) -> int:
    return int(abs(after - previous).seconds / 60)


def punctual(entries: List[str],
             usr_synonyms: List[tuple],
             usr_start_time: datetime = None,
             contingency_in_minutes: int = 2) -> dict:
    # CHECK
    if len(entries) == 0:
        raise ValueError('Expected at least one entry')

    # INIT
    start_time = usr_start_time if usr_start_time else datetime.now()

    # the user can specify synonyms: they are like labels with a duration
    # so that the user can refer to a duration by its label (i.e. synonym)
    synonyms = {}
    for usr_synonym in usr_synonyms:
        add_synonym_duration(usr_synonym[0], synonyms, usr_synonym[1])

    # PROCESSING

    # adjust the start_time if the first entry starts on a fixed time
    if parse_entry(entries[0], start_time)[1]:
        start_time = parse_entry(entries[0], start_time)[1]

    # an entry is a string in either following formats:
    # <duration | synonym>; <start_time>
    # duration and label are mandatory
    # start_time is optional
    # the user shall specify either duration or label
    # a duration is expressed as hours and minutes, such as: 1h32m, 2h and 25m
    # a synonym is a string that references a duration specified in the "synonyms" dictionary
    entries_parsed: List[Tuple[LiteralString, datetime]] = \
        [parse_entry(entry, start_time) for entry in entries]

    # base duration plus the contingency, applied to every entry
    entries_duration: List[int] = \
        [get_duration(entry, synonyms) + contingency_in_minutes for entry, at in entries_parsed]

    # TODO refactor below

    entry_duration_minutes = 0
    result = {
        'entries': [],
        'total_duration_minutes': 0,
        # adjusted later
        'start_time': start_time,
        'end_time': None
    }
    # count the number of spare times added
    spares = 0

    # TODO end refactor above

    for i in range(len(entries)):
        e, at = entries_parsed[i]
        entry_duration_minutes = entries_duration[i]

        # TODO continue from here
        def actual_start_time() -> datetime:
            if i == 0:
                return start_time
            if at:
                return at
            # we may have also syntactic entries, such as spare times
            return result['entries'][i - 1 + spares]['end_time']

        def actual_end_time() -> datetime:
            return datetime_plus_minutes(start_time, result['total_duration_minutes'])

        def create_entry():
            return {
                'entry': e.capitalize(),
                'duration': entry_duration_minutes,
                'start_time': actual_start_time(),
                # missing spare duration to the total is adjusted later
                'end_time': actual_end_time(),
                # adjusted later
                'overlap': 0,
            }

        result['total_duration_minutes'] = result['total_duration_minutes'] + entry_duration_minutes
        result['entries'].append(create_entry())
        result['end_time'] = result['entries'][-1]['end_time']

        # suppose two entries following in time: entry A and entry B
        # when the user specifies a start time for entry B,
        # we want to calculate how much free time there is from the previous
        # entry (i.e. entry A)
        if i > 0 and at:
            minutes_between_prev_entry = minutes_between_entries(
                previous=result['entries'][i - 1]['end_time'],
                after=result['entries'][i]['start_time']
            )
            entries_overlap = is_overlap(
                previous=result['entries'][i - 1]['end_time'],
                after=result['entries'][i]['start_time']
            )
            # oh no, there's an overlap: "I guess the user won't have time
            # to comply with his plan"
            if entries_overlap:
                result['entries'][i]['overlap'] = minutes_between_prev_entry
            # spare time found: "The user may have time to prepare popcorn too"
            elif minutes_between_prev_entry > 0:
                result['entries'].insert(i, {
                    'entry': 'SPARE TIME',
                    'duration': minutes_between_prev_entry,
                    'start_time': result['entries'][i - 1]['end_time'],
                    'end_time': result['entries'][i]['start_time'],
                    # can never overlap
                    'overlap': 0,
                })
                spares = spares + 1
                # update the total
                result['total_duration_minutes'] = result['total_duration_minutes'] + minutes_between_prev_entry
                # adjust entry end time, now that total_duration_minutes includes the spare duration too
                result['entries'][i + 1]['end_time'] = actual_end_time()

    return result


if __name__ == '__main__':
    # USER INPUT
    # this shall come from any kind of user input (cli, gui, file, etc...)
    usr_entries = [
        'shower',
        '30m; 14:00',
        'snack'
    ]

    usr_synonyms = [
        ('shower', 20),
        ('snack', 10)
    ]

    # PROCESSING
    result = punctual(entries=usr_entries,
                      usr_synonyms=usr_synonyms,
                      usr_start_time=datetime(2024, 5, 23, 13, 29, 0))

    # USER OUTPUT
    print(prettify_report(result))
