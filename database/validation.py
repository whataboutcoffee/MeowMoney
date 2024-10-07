# переместить файл в другую папку, вместе с services
import datetime
import re
from functools import reduce

from typing import Dict, List, Tuple, Union


def _validate_ctgr_name(ctgr: str):
    if re.fullmatch(r'\w+', ctgr) == None:
        raise ValueError(f'Некорректное название категории для записи "{ctgr}". Допустимы только буквы, цифры и нижнее подчеркивание')
    else:
        return ctgr

# block of functions to process dates range from a message
def _validate_date(date: str):
        try:
            date = datetime.datetime.strptime(date, '%d.%m.%y').date()
            return date
        except ValueError as ex:
            raise ValueError(f'Некорретно введена дата {date} - допустимый формат: дд.мм.гг. Также возможны проблемы с разделителем - допустимо только "-"')

def validate_dates_str(row: str):
    """Returns a list of datetime.date from a date row from a message"""
    dates: List[str] = [date.strip() for date in row.split('-')]
    dates: List[datetime.date] = [validate_single_date(date) for date in dates]
    if len(dates) == 1: 
        dates.append(dates[0])
    elif len(dates) > 2:
         raise ValueError('Диапазон дат должен содержать не более 2 дат')
    if dates[1] < dates[0]:
         raise ValueError('Вторая дата не может быть меньше первой)')
    return dates

def validate_single_date(row: str):
    if row == '':
         return datetime.date.today()
    return _validate_date(row)

# for the service to add operation in the database
def validate_categories(categories: str):
    lst = re.split(r",+", categories)
    lst = [v for v in lst if v != '']
    splt_lst = [tuple(re.split(r'\s*[:=]\s*', s.strip().lower(), )) for s in lst]

    # check whether a separator for the record is correct (a record example "зп=80000")
    check_sep: List[str] = [i for tup in splt_lst for i in tup if len(tup) == 1]
    if check_sep != []:
        raise ValueError(f'Для записи "{", ".join(check_sep)}" неверный разделитель между категорией и числом/выражением - должно быть "=" либо ":"')
    data = list(zip(*splt_lst))

    try:
        vals = tuple(map(eval, data[1]))
    # search for the record where the separator is incorrect and formation of an error message
    except SyntaxError as ex:
        err_text = ex.text
        for i in lst:
            if err_text in i:
                err_loc = i
                break
            else:
                err_loc = None
        raise ValueError(f'Синтаксическая ошибка в арифметическом выражении "{err_text}" в записи "{err_loc}"')

    # raise an error if a category name is incorrect
    list(map(_validate_ctgr_name, data[0]))

    return data[0], vals # the first set is the categories sequence (an example: ('еда', 'зп')),
    # the second tuple - the values tuple (an example: (2540.45, 5000)

# block of functions for the service for deleting records from the db
def _row_to_fetch(expr: str):
    if '+-' in expr and '=' not in expr:
        raise ValueError('Использование оператора "+-" допустимо только с "="')
    if re.search(r">=|<=", expr) != None:
        raise ValueError(f'Недопустимый оператор сравнения для записи "{expr}"')
    return re.split(r"\s*(=|>|<|[+]-)\s*", expr)

## main fuctions of the module for deleting records from the db
def validate_records_to_fetch(input_row: Union[str, None]):
    if input_row == None:
        return list()
    lst_ctgrs = re.split(r"\s*,\s*", input_row)
    lst_ctgrs = [v.strip() for v in lst_ctgrs if v != '']
    lst = list(map(_row_to_fetch, lst_ctgrs))
    for i, row in enumerate(lst):
        amount_nan = 5 - len(row)
        if amount_nan < 0:
            raise ValueError(f'Что-то не так с записью "{lst_ctgrs[i]}"')
        _validate_ctgr_name(row[0])
        row += [None for _ in range(amount_nan)]
        if '' in (row[0], row[2]):
            raise ValueError(f'Для записи "{lst_ctgrs[i]}" не указана категория/число или выражение')
        if amount_nan < 4:
            try:
                row[2] = eval(row[2])
            except SyntaxError as ex:
                err_text = ex.text
                raise ValueError(f'Синтаксическая ошибка в арифметическом выражении "{err_text}" в записи "{lst_ctgrs[i]}"')
        row[4] = float(row[4]) if row[4] != None else None
    return lst


# переместить в services
def change_records(lst_ctgrs: list) -> list:
    """Transform a list of a single record to except"""
    res = []
    for record in lst_ctgrs:
        if record[3] == "+-":
            r1 = [record[0], "<", record[2] - record[4], None, None]
            r2 = [record[0], ">", record[2] + record[4], None, None]
            res.append(r1)
            res.append(r2)
        elif record[1] == "<":
            record[1] = ">"
            res.append(record)
        elif record[1] == ">":
            record[1] = "<"
            res.append(record)
        elif record[1] == "=" and record[3] == None:
            record[1] = "<"
            res.append(record)
            record[1] = ">"
            res.append(record)
        elif record[1] == None:
            res.append(record)
    return res


# пойдет, только переименоватьв validate_records_row
def process_records_row(input_row: str) -> Tuple[Union[str, None]]:
    search_except_ctgrs = re.search(r"\.{3}\s*кроме", input_row)
    if search_except_ctgrs != None:
        start_sep, fin_sep = search_except_ctgrs.span()
        ctgrs_to_fetch_row, except_ctgrs_row = input_row[:start_sep].strip().lower(), input_row[fin_sep:].strip().lower()
    else:
        if 'кроме' in input_row:
            raise ValueError('"кроме" может быть использован только с троеточием: "... кроме"')
        ctgrs_to_fetch_row = input_row
        except_ctgrs_row = None
    return ctgrs_to_fetch_row, except_ctgrs_row



