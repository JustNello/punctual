import argparse
import ast

from punctual import punctual, prettify_report


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

    if args.synonyms_file:
        print(f"Synonyms file path: {args.synonyms_file}")
    else:
        print("No synonyms provided.")

    result = punctual(entries=read_lines_from_file(args.entries_file),
                      usr_synonyms=parse_synonyms_file(args.synonyms_file) if args.synonyms_file else [])

    print(prettify_report(result))


if __name__ == "__main__":
    main()
