from abc import ABC, abstractmethod
from datetime import datetime
from datetime import timedelta
from typing import Generic
from typing import List
from typing import NamedTuple
from typing import Tuple
from typing import TypeVar
from typing import Union

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

    # PRIVATE METHODS

    def _raise_error_if_empty(self):
        if self.empty:
            raise IndexError("There are no entries")

    def _start_end_time(self, duration: timedelta, start: datetime = None) -> Tuple[datetime, datetime]:
        # user may have provided a start time, that's why we check for
        # start if start else ...
        if self.empty:
            current = start if start else Schedule._now()
            return current, current + duration
        return start if start else self.last.end_time, self.last.end_time + duration

    # USER METHODS TO HANDLE ENTRIES

    def append(self, name: str, duration: timedelta, start: datetime = None) -> Entry:
        start_time, end_time = self._start_end_time(duration, start)
        result: Entry = Entry(name, start_time, end_time, duration)
        self._entries.append(result)
        return result


if __name__ == '__main__':
    usr_synonyms = [
        ('shower', 20),
        ('snack', 10)
    ]

    schedule: Schedule = Schedule.from_entries(
        'shower; 14:00', '30m', 'snack',
        parser=StandardParser(synonyms=usr_synonyms, contingency=None)
    )

    print(schedule)
