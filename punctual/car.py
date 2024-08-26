import os
import csv

from typing import List, Dict
from functools import lru_cache
from enum import Enum


class EstimationType(Enum):
    INCREMENTAL_AVG = 1
    DIFFERENTIAL_AVG = 2
    DIFFERENTIAL_AVG_EXTRA = 3


def at_least_two_refills(file: str):
    if len(read(file)) < 2:
        raise ValueError(
            'Expected at least two refills in the CSV file in order to estimate consumption and forecasting')


def columns(file: str) -> List[str]:
    return list(read(file)[0].keys())


def parse_row(row: Dict[str, str]) -> Dict[str, float]:
    return {key: float(value) for key, value in row.items()}


@lru_cache
def read(file: str) -> List[Dict[str, float]]:
    with open(file, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        return [parse_row(row) for row in reader]


def estimate_column(file: str, column: str, estimation_type: EstimationType) -> float:
    values: List[float] = []
    extra: float = 0

    if (estimation_type == EstimationType.DIFFERENTIAL_AVG_EXTRA
            or estimation_type == EstimationType.DIFFERENTIAL_AVG):
        for i in range(1, len(read(file))):
            values.append(read(file)[i][column] - read(file)[i - 1][column])
    else:
        values = [row[column] for row in read(file)]

    if estimation_type == EstimationType.DIFFERENTIAL_AVG_EXTRA:
        extra = read(file)[-1][column]

    return round(sum(values) / len(read(file))) + extra


def estimate(file: str, strategy: str = 'avg') -> Dict[str, float]:
    if strategy == 'avg':
        return {
            'km': estimate_column(file, 'km', EstimationType.DIFFERENTIAL_AVG_EXTRA),
            'cost': estimate_column(file, 'cost', EstimationType.INCREMENTAL_AVG)
        }
    elif strategy == 'max':
        return {
            'km': read(file)[-1]['km'] + avg_km(file),
            'cost': estimate_maximum_refill(file)['cost']
        }


def estimate_maximum_refill(file: str) -> Dict[str, float]:
    return max(read(file), key=lambda refill: refill['cost'])


def avg_km(file: str) -> float:
    at_least_two_refills(file)
    if len(read(file)) > 2:
        return estimate_column(file, 'km', EstimationType.DIFFERENTIAL_AVG)
    return read(file)[1]['km'] - read(file)[0]['km']


def avg_cost(file: str) -> float:
    return estimate_column(file, 'cost', EstimationType.INCREMENTAL_AVG)


def gauge(file: str, current_km: float) -> str:
    prev_km = read(file)[-1]['km']
    next_km = estimate(usr_file, 'max')['km']
    diff_km = next_km - prev_km
    steps_nr = 20
    steps_km = round(diff_km / 20)
    usr_km = current_km - prev_km
    usr_steps_nr = round(usr_km / steps_km)
    steps_left_nr = steps_nr - usr_steps_nr
    perc = round((steps_left_nr / steps_nr) * 100)
    return f'{prev_km} km {"=" * usr_steps_nr} {current_km} km {"=" * steps_left_nr} {next_km} km [{perc}% of tank capacity left]'


if __name__ == '__main__':
    # USR SETTINGS
    usr_file = 'refills.csv'

    # DO NOT CHANGE CODE BELOW
    estimation = estimate(usr_file, 'max')

    print(f'You\'ll have next refill at {estimation["km"]} km and you\'ll pay € {estimation["cost"]}')
    print(f'On average, you drive {avg_km(usr_file)} km on each refill')
    print(f'On average, you pay € {avg_cost(usr_file)} at each refill')
    print(f'That is {round(avg_km(usr_file) / avg_cost(usr_file), 2)} km/euro')
    print(gauge(usr_file, 138700))
