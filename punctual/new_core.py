from typing import List

import numpy as np


class Schedule:

    def __init__(self):
        self._start_times: np.datetime64
        self._durations: List[int]

    def append(self, entry: str):
        pass
