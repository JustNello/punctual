from datetime import datetime
from datetime import timedelta

from typing import NamedTuple
from typing import LiteralString
from typing import List


class Moment(NamedTuple):
    datetime: datetime
    previous_entry: "Entry"
    next_entry: "Entry"


class Entry(NamedTuple):
    name: LiteralString
    start_time: Moment
    end_time: Moment


class Schedule:

    def __init__(self):
        self._entries: List[Entry] = []

    # CONSTRUCTORS

    @classmethod
    def from_names(cls, *names: str, duration: timedelta) -> "Schedule":
        result: Schedule = Schedule()
        for name in names:
            result.append(name)
            print(name)
        return result

    # MAGIC METHODS & PROPERTIES

    def __len__(self):
        return len(self._entries)

    @property
    def empty(self) -> bool:
        return len(self) == 0

    # METHODS TO ADD ENTRIES

    def append(self, name: str, duration: timedelta) -> "Entry":
        if self.empty:
            start_time = datetime.now()
            end_time = start_time + duration
            # TODO Solve this: how to handle the fact that we both have to construct
            # an Entry and Moment instance and they reference each other?
            Entry(name=name, )



if __name__ == '__main__':
    start_time = datetime.now()
    samples = 10

    first: Schedule = Schedule.from_names(
        'Eating', 'Going to dinner', duration=timedelta(minutes=30))

    #second: Schedule = Schedule.from_names(
    #    'Breakfast', 'Movie', duration=timedelta(minutes=30))

    print('\nDONE')
