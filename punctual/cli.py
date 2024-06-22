import argparse
import time

from punctual.new_core import Schedule
from punctual.new_core import punctual


def parse_args():
    parser = argparse.ArgumentParser(description="Process entries and synonyms.")

    # Mandatory entries file path
    parser.add_argument(
        'entries_file',
        type=str,
        help='Path to the entries file'
    )

    # Optional synonyms file path
    parser.add_argument(
        '--synonyms_file',
        type=str,
        help='Path to the synonyms file'
    )

    # Enable loop option
    parser.add_argument(
        '--live',
        action=argparse.BooleanOptionalAction,
        help='The program will continue running until the user shuts it down'
    )

    # Optional contingency: an amount in minutes that will be added
    # to every entry
    parser.add_argument(
        '--contingency',
        type=int,
        help='An amount in minutes that will be added to every entry (default value is 2 minutes)',
        default=2
    )

    # Enhance the accuracy of duration calculations.
    # Trip durations will be calculated using a geocoding service,
    # while the durations of unknown entries will be estimated by an AI.
    parser.add_argument(
        '--online',
        action=argparse.BooleanOptionalAction,
        help='Enhance your schedule with online tools. Trip durations will be calculated using a geocoding service, while the durations of unknown entries will be estimated by an AI'
    )

    args = parser.parse_args()

    return args


def read_lines_from_file(file_path):
    """Read lines from a file and return them as a list."""
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
        return [line.strip() for line in lines]  # Stripping to remove any extra newline characters
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        return []
    except IOError:
        print(f"Error: An I/O error occurred while reading {file_path}.")
        return []


def parse_synonyms_file(file_path):
    """Parse the synonyms file and return a list of tuples (str, int)."""
    lines = read_lines_from_file(file_path)
    synonyms = []
    for line in lines:
        try:
            word, count = line.split(',')
            synonyms.append((word.strip(), int(count.strip())))
        except ValueError:
            print(f"Error: Invalid line format in {file_path}: '{line}'")
    return synonyms


def main():
    args = parse_args()

    print(f"Entries file path: {args.entries_file}")

    if args.live:
        print('Schedule will be generated every minute until user shuts the program down')

    if args.synonyms_file:
        print(f"Synonyms file path: {args.synonyms_file}")
    else:
        print("No synonyms provided.")

    while True:
        result: Schedule = punctual(
            entries=read_lines_from_file(args.entries_file),
            usr_synonyms=parse_synonyms_file(args.synonyms_file) if args.synonyms_file else [],
            online=args.online,
            contingency_in_minutes=args.contingency,
            tablefmt='simple_grid'
        )

        print(result)
        result.to_clipboard()

        if args.live:
            time.sleep(60)
        else:
            break


if __name__ == "__main__":
    main()
