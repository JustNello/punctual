from abc import ABC, abstractmethod
from datetime import datetime
from datetime import timedelta
from typing import Generic
from typing import List
from typing import Set
from typing import NamedTuple
from typing import Tuple
from typing import TypeVar
from typing import Union
from enum import Enum

from punctual.core import add_synonym_duration
from punctual.core import prettify_report
from punctual.core import parse_entry
from punctual.core import get_duration

ParsableEntryType = TypeVar('ParsableEntryType')


class Parser(ABC, Generic[ParsableEntryType]):

    @abstractmethod
    def parse(self, entry: Generic[ParsableEntryType], **kwargs) -> Tuple[str, timedelta, Union[datetime, None]]:
        raise NotImplementedError("To be implemented in subclasses")


class StandardParser(Parser):

    def __init__(self, synonyms: List[Tuple[str, int]], contingency: timedelta = None):
        # the user can specify synonyms: they are like labels with a duration
        # so that the user can refer to a duration by its label (i.e. synonym)
        self._synonyms = {}
        for syn in synonyms:
            add_synonym_duration(syn[0], self._synonyms, syn[1])
        self._contingency = contingency if contingency else timedelta(minutes=2)

    def parse(self, entry: Generic[ParsableEntryType], **kwargs) -> Tuple[str, timedelta, Union[datetime, None]]:
        entry_name, at = parse_entry(entry, kwargs.get('start_time'))
        entry_duration = get_duration(entry_name, self._synonyms)
        return entry_name, timedelta(minutes=entry_duration) + self._contingency, at


class Entry(NamedTuple):
    name: str
    start_time: datetime
    end_time: datetime
    duration: timedelta
    fixed: bool

    @property
    def minutes(self) -> float:
        return self.duration.total_seconds() / 60


class Feature(Enum):
    DETECT_SPARE_TIME = 1
    DETECT_OVERLAP = 2


class Schedule:

    def __init__(self, features: List[Feature] = None):
        self._entries: List[Entry] = []
        self._features: Set[Entry] = set(features) if features else set()

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
        for entry in entries:
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

    # TODO implement
    @property
    def _does_detect_overlap(self) -> bool:
        return Feature.DETECT_OVERLAP in self._features

    # TODO implement
    @property
    def _does_detect_spare_time(self) -> bool:
        return Feature.DETECT_SPARE_TIME in self._features

    # PRIVATE METHODS

    def _raise_error_if_empty(self):
        if self.empty:
            raise IndexError("There are no entries")

    def _start_end_time(self, duration: timedelta, start: datetime = None, previous_entry_index: int = None) -> Tuple[
        datetime, datetime]:
        # user may have provided a start time, that's why we check for
        # start if start else ...
        if self.empty:
            current = start if start else Schedule._now()
            return current, current + duration

        # Allows the user to insert an entry at a specified index,
        # otherwise defaults to last entry
        previous_entry: Entry
        if previous_entry_index is not None:
            previous_entry = self._entries[previous_entry_index]
        else:
            previous_entry = self.last
        return start if start else previous_entry.end_time, previous_entry.end_time + duration

    def _make_entry(self, name: str, duration: timedelta, start: datetime = None,
                    previous_entry_index: int = None) -> Entry:
        start_time, end_time = self._start_end_time(
            duration, start, previous_entry_index)
        return Entry(name, start_time, end_time, duration, True if start else False)

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


def punctual(entries: List[str],
             usr_synonyms: List[Tuple[str, int]],
             usr_start_time: datetime = None,
             contingency_in_minutes: int = 2) -> Schedule:
    return Schedule.from_entries(
        *entries,
        parser=StandardParser(synonyms=usr_synonyms, contingency=timedelta(minutes=contingency_in_minutes))
    )


if __name__ == '__main__':
    usr_synonyms = [
        ('shower', 20),
        ('snack', 10)
    ]

    schedule: Schedule = Schedule.from_entries(
        '30m', 'shower; 14:00', 'snack',
        parser=StandardParser(synonyms=usr_synonyms, contingency=None)
    )

    print(schedule)
    print('\nAFTER\n')

    schedule.insert(1, 'breakfast', timedelta(minutes=12))
    print(schedule)
