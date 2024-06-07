import os
from json import loads
from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime
from datetime import timedelta
from typing import Generic, Any
from typing import List
from typing import NamedTuple
from typing import Tuple
from typing import TypeVar
from typing import Union

import pyperclip

from punctual.core import add_synonym_duration
from punctual.core import get_duration
from punctual.core import is_overlap
from punctual.core import minutes_between_entries
from punctual.core import parse_entry
from punctual.core import prettify_report
from punctual.core import is_direction
from punctual.core import start_location
from punctual.core import end_location
from punctual._mapbox import geocode
from punctual._mapbox import direction_duration
from punctual._mapbox import RoutingProfile


class Profile:

    def __init__(self, file: str = None):
        with open(file if file else os.environ.get('PUNCTUAL_PROFILE'), 'r') as f:
            self._body = loads(f.read())

    @property
    def mapbox_token(self) -> str:
        return self._body['mapbox']['token']


class TripDurationProvider(Enum):
    SYNONYMS = 1
    MAPBOX = 2


ParsableEntryType = TypeVar('ParsableEntryType')


class Parser(ABC, Generic[ParsableEntryType]):

    @abstractmethod
    def is_parsable(self, entry: Generic[ParsableEntryType]) -> bool:
        raise NotImplementedError("To be implemented in subclasses")

    @abstractmethod
    def parse(self, entry: Generic[ParsableEntryType], **kwargs) -> Tuple[str, timedelta, Union[datetime, None]]:
        raise NotImplementedError("To be implemented in subclasses")


class MapboxParser(Parser):

    def __init__(self):
        self._profile = Profile()

    def _get_duration(self, entry_name: str) -> timedelta:
        # never fallback on synonyms for calculating the duration of a direction
        _, start_coord = geocode(start_location(entry_name), self._profile.mapbox_token)
        _, end_coord = geocode(end_location(entry_name), self._profile.mapbox_token)
        return direction_duration(
            # TODO 1. allow user to specify a routing profile per entry
            # TODO 2. allow user to specify a 'depart_at' time, as features by Mapbox API:
            # TODO    https://docs.mapbox.com/playground/directions/?coordinates=12.42942%2C41.834776&coordinates=12.496166500000001%2C41.902633&steps=false&notifications=none&alternatives=false
            [start_coord, end_coord], routing_profile=RoutingProfile.DRIVING, token=self._profile.mapbox_token)

    def _fix_entry_name(self, entry_name: str) -> str:
        # When using Mapbox, we need to update the user's entered location with the actual matched location.
        # This ensures the user can verify that Mapbox has provided the correct location.
        start_entry_name, _ = geocode(start_location(entry_name), self._profile.mapbox_token)
        end_entry_name, _ = geocode(end_location(entry_name), self._profile.mapbox_token)
        return (f'{start_entry_name}\n'
                f'{end_entry_name}')

    def is_parsable(self, entry: Generic[ParsableEntryType]) -> bool:
        return not entry.startswith('#') and is_direction(entry)

    def parse(self, entry: Generic[ParsableEntryType], **kwargs) -> Tuple[str, timedelta, Union[datetime, None]]:
        entry_name, at = parse_entry(entry, kwargs.get('start_time'))
        return self._fix_entry_name(entry_name), self._get_duration(entry_name), at


class StandardParser(Parser):

    def __init__(self,
                 synonyms: List[Tuple[str, int]],
                 trip_duration_provider: TripDurationProvider = TripDurationProvider.SYNONYMS,
                 additional_parsers: List[Parser] = None,
                 contingency: timedelta = None):
        # the user can specify synonyms: they are like labels with a duration
        # so that the user can refer to a duration by its label (i.e. synonym)
        self._synonyms = {}
        for syn in synonyms:
            add_synonym_duration(syn[0], self._synonyms, syn[1])
        self._contingency = contingency if contingency else timedelta(minutes=2)
        self._trip_duration_provider = trip_duration_provider
        # setup addition parsers
        self._additional_parsers = None
        self.with_addition_parsers(additional_parsers)

    def with_addition_parsers(self, additional_parsers: List[Parser]):
        self._additional_parsers: set[Parser] = set(additional_parsers) if additional_parsers else set()
        if self._trip_duration_provider is TripDurationProvider.MAPBOX:
            self._additional_parsers.add(MapboxParser())

    def is_parsable(self, entry: Generic[ParsableEntryType]) -> bool:
        return not entry.startswith('#')

    def parse(self, entry: Generic[ParsableEntryType], **kwargs) -> Tuple[str, timedelta, Union[datetime, None]]:
        parsers: List[Parser] = list(filter(lambda p: p.is_parsable(entry), self._additional_parsers))
        if len(parsers) > 0:
            entry_name, duration, at = parsers[0].parse(entry, **kwargs)
        # fallback to default parsing strategy
        else:
            entry_name, at = parse_entry(entry, kwargs.get('start_time'))
            duration = timedelta(minutes=get_duration(entry_name, self._synonyms))
        return entry_name, duration + self._contingency, at


class SignedTimedelta:
    _POSITIVE = '+'
    _NEGATIVE = '-'
    _ZERO = '='

    def __init__(self, sign: str, duration: timedelta):
        self._sign = sign
        self._duration = duration

    @classmethod
    def positive(cls, duration: timedelta) -> "SignedTimedelta":
        return SignedTimedelta(cls._POSITIVE, duration)

    @classmethod
    def negative(cls, duration: timedelta) -> "SignedTimedelta":
        return SignedTimedelta(cls._NEGATIVE, duration)

    @classmethod
    def zero(cls) -> "SignedTimedelta":
        return SignedTimedelta(cls._ZERO, timedelta(days=0, hours=0, minutes=0))

    @property
    def is_zero(self) -> bool:
        return self._sign == self._ZERO or self._duration.total_seconds() == 0

    def __str__(self):
        if self.is_zero:
            return ''
        return f'{self._sign} {self._duration}'


class Entry(NamedTuple):
    name: str
    start_time: datetime
    end_time: datetime
    duration: timedelta
    extra: SignedTimedelta
    fixed: bool

    @property
    def minutes(self) -> float:
        return self.duration.total_seconds() / 60


class Schedule:

    def __init__(self):
        self._entries: List[Entry] = []

    # CONSTRUCTORS

    @classmethod
    def _now(cls) -> datetime:
        return datetime.now()

    @classmethod
    def from_names(cls, *names: str, duration: timedelta, start: datetime = None) -> "Schedule":
        result: Schedule = cls()
        for name in names:
            result.append(name, duration, start)
        return result

    @classmethod
    def from_entries(cls, *entries: Generic[ParsableEntryType], parser: Parser[Generic[ParsableEntryType]]):
        result: Schedule = cls()
        i = 0
        for entry in [e for e in entries if parser.is_parsable(e)]:
            name, duration, start = parser.parse(
                entry,
                # FIX-20240531: The StandardParser requires start_time to extrapolate
                # the date (year, month and day) to compose the entry start_time
                start_time=Schedule._now() if i == 0 else result.last.start_time
            )
            result.append(name, duration, start)
            i = i + 1
        return result

    # MAGIC METHODS & PROPERTIES

    def __len__(self):
        return len(self._entries)

    def __dict__(self):
        return {
            'entries': [entry._asdict() for entry in self._entries],
            'total_duration_minutes': self.minutes,
            'start_time': self.start,
            'end_time': self.end
        }

    def __str__(self):
        return prettify_report(self.__dict__())

    @property
    def empty(self) -> bool:
        return len(self) == 0

    @property
    def first(self) -> Entry:
        self._raise_error_if_empty()
        return self._entries[0]

    @property
    def last(self) -> Entry:
        self._raise_error_if_empty()
        return self._entries[-1]

    @property
    def minutes(self) -> float:
        return sum([entry.minutes for entry in self._entries])

    @property
    def start(self) -> datetime:
        return self.first.start_time

    @property
    def end(self) -> datetime:
        return self.last.end_time

    # PRIVATE METHODS

    def _raise_error_if_empty(self):
        if self.empty:
            raise IndexError("There are no entries")

    def _previous_entry(self, previous_entry_index: int = None) -> Entry:
        # Allows the user to insert an entry at a specified index,
        # otherwise defaults to last entry
        result: Entry
        if previous_entry_index is not None:
            result = self._entries[previous_entry_index]
        else:
            result = self.last
        return result

    def _start_end_time(self, duration: timedelta, start: datetime = None, previous_entry_index: int = None) -> Tuple[
        datetime, datetime]:
        # user may have provided a start time, that's why we check for
        # start if start else ...
        if self.empty:
            current = start if start else Schedule._now()
            return current, current + duration

        # Allows the user to insert an entry at a specified index,
        # otherwise defaults to last entry
        return (start if start else self._previous_entry(previous_entry_index).end_time,
                (start if start else self._previous_entry(previous_entry_index).end_time) + duration)

    def _spare_time_or_overlap(self, duration: timedelta, start: datetime = None,
                               previous_entry_index: int = None) -> SignedTimedelta:
        start_time, end_time = self._start_end_time(
            duration, start, previous_entry_index)

        # detect overlap or spare time between this and previous entry
        if self.empty:
            result: SignedTimedelta = SignedTimedelta.zero()
        else:
            overlap = is_overlap(
                previous=self._previous_entry(previous_entry_index).end_time,
                after=start_time)
            minutes_between = timedelta(minutes=minutes_between_entries(
                previous=self._previous_entry(previous_entry_index).end_time,
                after=start_time))
            result: SignedTimedelta = SignedTimedelta.negative(
                minutes_between) if overlap else SignedTimedelta.positive(minutes_between)

        return result

    def _make_entry(self, name: str, duration: timedelta, start: datetime = None,
                    previous_entry_index: int = None) -> Entry:
        start_time, end_time = self._start_end_time(
            duration, start, previous_entry_index)

        signed_timedelta = self._spare_time_or_overlap(
            duration, start, previous_entry_index)

        return Entry(name,
                     start_time,
                     end_time,
                     duration,
                     signed_timedelta,
                     True if start else False)

    def _propagate_time_changes(self, index: int):
        already_up_to_date: List[Entry] = self._entries[:index]
        to_be_updated: List[Entry] = self._entries[index:]
        self._entries = already_up_to_date
        for entry in to_be_updated:
            # start_time of fixed entries must not change, even after updating and at the risk
            # of overlapping
            self.append(entry.name, entry.duration, entry.start_time if entry.fixed else None)

    def _sort(self):
        self._entries = sorted(self._entries, key=lambda entry: entry.start_time)

    # USER METHODS TO HANDLE ENTRIES

    def append(self, name: str, duration: timedelta, start: datetime = None) -> Entry:
        result: Entry = self._make_entry(name, duration, start)
        self._entries.append(result)
        self._sort()
        return result

    def insert(self, index: int, name: str, duration: timedelta, start: datetime = None) -> Entry:
        result: Entry = self._make_entry(name, duration, start, index - 1 if index > 0 else None)
        self._entries.insert(index, result)
        self._propagate_time_changes(index)
        self._sort()
        return result

    # OTHER USER METHODS

    def to_clipboard(self):
        pyperclip.copy(self.__str__())


def punctual(entries: List[str],
             usr_synonyms: List[Tuple[str, int]],
             trip_duration_provider: TripDurationProvider = TripDurationProvider.SYNONYMS,
             contingency_in_minutes: int = 2) -> Schedule:
    return Schedule.from_entries(
        *entries,
        parser=StandardParser(
            synonyms=usr_synonyms,
            trip_duration_provider=trip_duration_provider,
            contingency=timedelta(minutes=contingency_in_minutes))
    )


if __name__ == '__main__':
    usr_synonyms = [
        ('shower', 20),
        ('snack', 10)
    ]

    schedule: Schedule = Schedule.from_entries(
        'Colosseo, Roma, Italia -> Piazza della Repubblica 00185, Roma RM', '30m', 'shower; 14:00', 'snack',
        parser=StandardParser(synonyms=usr_synonyms,
                              trip_duration_provider=TripDurationProvider.MAPBOX,
                              contingency=None)
    )

    print(schedule)
    print('\nAFTER\n')

    schedule.insert(1, 'breakfast', timedelta(minutes=12))
    print(schedule)
