from string import digits, ascii_letters, whitespace
from typing import List


def csv_reader(file: str):
    with open(file, newline='', mode='r') as csv_file:
        while True:
            ch = csv_file.read(1)
            yield ch
            if not ch:
                return


def csv_old(file: str, delimiter: str = ';'):
    reader = csv_reader(file)
    result = {'columns': []}

    updated_column_index = False
    column_index = -1
    column_name = ''
    column_value = ''

    for ch in reader:
        if ch in ascii_letters:
            column_name = column_name + ch
        elif ch in ['\r', '\n']:
            if not updated_column_index:
                column_index = column_index + 1
                column_name = result['columns'][column_index]
            else:
                updated_column_index = True
                continue
        elif ch == delimiter:
            if column_name != '':
                result['columns'].append(column_name)
                result[column_name] = []
                column_name = ''
            else:
                result[column_name].append(int(column_value))
                column_value = ''
                column_index = column_index + 1
                column_name = result['columns'][column_index]
        elif ch in digits:
            column_value = column_value + ch
        else:
            raise NotImplementedError(f'Parsing error: {result}')

    return result


def csv(file: str, delimiter: str = ';'):
    reader = csv_reader(file)

    # gather all tokens
    tokens = ['']
    i = 0
    for ch in reader:
        if ch in whitespace:
            tokens.append('')
            i = i + 1
        elif ch == delimiter:
            tokens.append('')
            i = i + 1
        else:
            tokens[i] = tokens[i] + ch

    return tokens


if __name__ == '__main__':
    res = csv('refills.csv')
    print(res)
