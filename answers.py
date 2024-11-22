import datetime
from typing import Union, List, Tuple, Literal


def convert_num_to_str(num: Union[float, int],
                       mode: Literal['digits', 'letters'] = 'digits') -> str:
    if mode == 'digits':
        return f'{num:,.0f}'.replace(",", " ")
    elif mode =='letters':
        # if abs(num) < 1000:
        #     return f'{num:.0f}'
        if abs(num) < 100_000:
            return f'{num:,.0f} р'.replace(",", " ")
        elif abs(num) < 1_000_000:
            return f'{num/1000:.0f} тыс. р'
        elif abs(num) < 1_000_000_000:
            return f'{num/1_000_000:.0f} млн. р'
    

def convert_obj_to_str(obj):
    if type(obj) in (float,int):
       return convert_num_to_str(obj, 'digits')
    elif type(obj) == datetime.date:
        return datetime.datetime.strftime(obj, '%d.%m.%Y')
    elif obj == "income":
        return "Доход"
    elif obj == "expense":
        return "Расход"
    else:
        return str(obj).capitalize()
    

def _create_table(data: List[tuple],
                cols: List[str],
                use_header_sep: bool = False,
                header_sep: str="=") -> str:
    data = [[convert_obj_to_str(el) for el in row] for row in data]
    # расчёт максимальной длинны колонок
    max_columns = [] # список максимальной длинны колонок
    for n, col in enumerate(zip(*data)):
        len_el = []
        [len_el.append(len(el)) for el in col]  
        max_columns.append(max(*len_el, len(cols[n])))
    
    # печать таблицы с колонками максимальной длинны строки
    # печать шапки таблицы
    res: str = ''
    amount_cols = len(cols)
    for n, column in enumerate(cols):
        add = 2 if n + 1 < amount_cols else 0
        res += f'{column:{max_columns[n] + add}}'
    res += '\n'

    # печать разделителя шапки
    if use_header_sep:
        amount_sep_symb = len(res) - 1
        res += f'{header_sep * amount_sep_symb}'
        res += '\n'
    # печать тела таблицы
    for row in data:
        for n, val in enumerate(row):
            add = 2 if n + 1 < amount_cols else 0
            res += f'{val:{max_columns[n] + add}}'
        res += '\n'
    
    return res.removesuffix('\n')


class StartText:
    """Texts for processing the '/start' command"""
    @classmethod
    def first_answ(cls) -> str:
        return 'Привет! Прежде чем увидеть мои возможности, тебе нужно ознакомиться с условиями обработки твоих данных'
    
    @classmethod
    def agreement(cls) -> str:
        return 'В процессе работы будет использован твой Telegram ID и вся информация о финансах, которую ты мне предоставишь. Эта информация будет храниться в базе данных на стороннем сервере. Информация доступна только создателю бота, для связи с сервером используется шифрование'
    
    # @classmethod
    # def first_time_answ(cls) -> str:
    #     return 'Ты не мог прочесть соглашение за столь малое время! Давай еще раз и по честному!'
    
    # @classmethod
    # def little_time_answ(cls, time: int) -> str:
    #     return f'Для нормального прочтения соглашения требуется около 14 секунд, а не {time} сек!'
    
    @classmethod
    def successful_agreement(cls) -> str:
        return 'Отлично! Давай начнем. Сперва предлагаю воспользоваться командой /help'


class Operation:
    # @staticmethod
    # def _df_to_str(df: DataFrame):
    #     df[1] = df[1].astype(str)
    #     splt_lst = list(df.itertuples(index=True, name=None))
    #     prep_s = [' - ' + ' - '.join(i).capitalize() for i in splt_lst]
    #     return '\n'.join(prep_s)

    @staticmethod
    def oper(old_ctgrs: List[tuple],
            type_oper: str,
            date: datetime.datetime.date,
            new_ctgrs: Union[List[str], List[tuple]] = []
            ) -> str:
        
        cols = ['Категория', 'Сумма']
        old_ctgrs_str = '<code>' + _create_table(old_ctgrs, cols) + '</code>' if len(old_ctgrs) > 0 else 'Отсутствуют)'
        new_ctgrs_str = '<code>' + _create_table(new_ctgrs, cols) + '</code>' if len(new_ctgrs) > 0 else 'Отсутствуют)'
        oper = "расход" if type_oper == 'expense' else "доход"
        
        return (
            f"Операция - {oper}\n"
            f"Дата - {datetime.datetime.strftime(date, '%d.%m.%Y')}\n"
            "Записи с категориями, которые ты уже использовал:\n"
            f"{old_ctgrs_str}\n"
            "Записи с новыми категориями:\n"
            f"{new_ctgrs_str}\n"
            f"Записываем {oper}?"
        )
    
    @staticmethod
    def oper_confirmed(oper_type: str):
        return f'{oper_type} успешно занесен в историю операций!'

    @staticmethod
    def oper_confirmed_only_new_ctgrs(oper_type: str):
        return f'{oper_type} успешно занесен в историю операций! Но только использованные категории'


class AnswersForTable:
    @staticmethod
    def _prep_opers_str(opers: List[tuple]):
        opers = [tuple(convert_obj_to_str(i) for i in tup) for tup in opers]
        # prep_s = [' - ' + ' - '.join(i).capitalize() for i in opers]
        prep_s = []
        for tup in opers:
            s: str = tup[0] + ' - ' + tup[1] + ' от ' + tup[2]
            prep_s.append(s)
        return '\n'.join(prep_s)
    
    @staticmethod
    def with_opers(
        mode: Literal['del', 'table'],
        amount: int,
        date1: datetime.datetime.date ,
        date2: datetime.datetime.date,
        opers: List[tuple],
        ctgrs_not_found: list
    ):
        # opers_str: str = DeleteOper._prep_opres_str(opers)
        opers_str = _create_table(opers, ['Категория', 'Сумма', 'Дата', 'Тип'])
        
        # ctgrs_not_found_str: str = ' - ' + ',\n - '.join(ctgrs_not_found) if ctgrs_not_found != [] else 'Отсутствуют)'
        ctgrs_not_found_str: str = '\n'.join(ctgrs_not_found).title() if ctgrs_not_found != set() else 'Отсутствуют)'
        
        if date1 == date2:
            dates_str = datetime.datetime.strftime(date1, '%d.%m.%Y')
        else:
            dates_str = f"с {datetime.datetime.strftime(date1, '%d.%m.%Y')} по {datetime.datetime.strftime(date2, '%d.%m.%Y')}"
        
        if mode == 'del':
            first_row = f"Удаляем {amount} запись(-и) {dates_str}:"
        elif mode == 'table':
            first_row = f"Нашел для тебя {amount} запись(-и) {dates_str}:"
        return (
            f'{first_row}\n'
            f'<code>{opers_str}</code>\n'
            f"Ненайденные категории:\n"
            f"<code>{ctgrs_not_found_str}</code>\n"
        )
    
    @staticmethod
    def without_opers(
        mode: Literal['del', 'table'],
        amount: int,
        date1: datetime.datetime.date ,
        date2: datetime.datetime.date,
        ctgrs_not_found: list
    ):
        ctgrs_not_found_str: str = ' - ' + ',\n - '.join(ctgrs_not_found).title() if ctgrs_not_found != [] else 'Отсутствуют)'
        if date1 == date2:
            dates_str = datetime.datetime.strftime(date1, '%d.%m.%Y')
        else:
            dates_str = f"с {datetime.datetime.strftime(date1, '%d.%m.%Y')} по {datetime.datetime.strftime(date2, '%d.%m.%Y')}"
        
        if mode == 'del':
            first_row = f"Удаляем {amount} запись(-и) {dates_str}:"
        elif mode == 'table':
            first_row = f"Нашел для тебя {amount} запись(-и) {dates_str}:"
        return (
            f'{first_row}\n'
            f"Ненайденные категории:\n"
            f"<code>{ctgrs_not_found_str}</code>"
        )
    
    @staticmethod
    def with_opers_short_table(
        amount: int,
        date1: datetime.datetime.date ,
        date2: datetime.datetime.date,
        opers: List[tuple],
        ctgrs_not_found: list
    ):
        opers_str = _create_table([[oper[0], oper[1], oper[3]] for oper in opers], ['Категория', 'Сумма', 'Тип'])
        
        ctgrs_not_found_str: str = '\n'.join(ctgrs_not_found).title() if ctgrs_not_found != set() else 'Отсутствуют)'
        
        if date1 == date2:
            dates_str = datetime.datetime.strftime(date1, '%d.%m.%Y')
        else:
            dates_str = f"с {datetime.datetime.strftime(date1, '%d.%m.%Y')} по {datetime.datetime.strftime(date2, '%d.%m.%Y')}"
        return (
            f"Нашел для тебя {amount} запись(-и) {dates_str}:\n"
            f'<code>{opers_str}</code>\n'
            f"Ненайденные категории:\n"
            f"<code>{ctgrs_not_found_str}</code>\n"
        )
    
    @staticmethod
    def only_not_found() -> str:
        return (
            f'Ни одна из перечисленных категорий не найдена в твоих записях в этот период времени'
        )

    @staticmethod
    def stats(opers: List[Tuple[str, float, int, str]]) -> str:
        income = sum([r[1] for r in opers if r[3] == 'income'])
        expense = sum([r[1] for r in opers if r[3] == 'expense'])
        income_str = convert_num_to_str(income, 'letters')
        expense_str = convert_num_to_str(expense, 'letters')
        dif = income - expense
        dif_str = convert_num_to_str(dif, 'letters')
        return (
            f'Расходы: {expense_str}\n'
            f'Доходы: {income_str}\n'
            f'Баланс: {dif_str}'
        )


class Chart:
    @staticmethod
    def caption(opers, ctgrs_not_found, misc_opers_exp, misc_opers_inc):
        misc_opers_exp_str = _create_table(misc_opers_exp, ['Категория', 'Сумма']) if misc_opers_exp != [] else 'Отсутствуют)'
        misc_opers_inc_str = _create_table(misc_opers_inc, ['Категория', 'Сумма']) if misc_opers_inc != [] else 'Отсутствуют)'
        ctgrs_not_found_str: str = ' - ' + ',\n - '.join(ctgrs_not_found).title() if ctgrs_not_found != [] else 'Отсутствуют)'
        return (
            f'Вот и твой график)\n'
            f'А еще немного статистики:\n'
            f'{AnswersForTable.stats(opers)}\n'
            '\n'
            f'Остальные расходы включают в себя:\n'
            f'<code>{misc_opers_exp_str}</code>\n'
            f'А остальные доходы:\n'
            f'<code>{misc_opers_inc_str}</code>\n'
            '\n'
            f"Ненайденные категории:\n"
            f"<code>{ctgrs_not_found_str}</code>"
        )


class DelCtgr:
    @staticmethod
    def del_ctgr(ctgr: str):
        return (
            f'Удаляем категорию <code>{ctgr}</code> и все записи, связанные с ней?'
        )


class CtgrsList:
    @staticmethod
    def format_ctgrs_list(ctgrs_list: list) -> str:
        # res = 'Твои категории:\n<code> - ' + ',\n - '.join(ctgrs_list).title() + '</code>' if ctgrs_list != [] else 'У тебя еще нет ни одной категории! Скорей заноси записи, чтобы создать новые категории расходов и доходов!'
        if ctgrs_list == []:
            return 'У тебя еще нет ни одной категории! Скорей заноси записи, чтобы создать новые категории расходов и доходов!'
        table = _create_table(ctgrs_list, ['Категория', 'Тип'])
        return (
            'Твои категории:\n'
            f'<code>{table}</code>'
        )
        
    

class Errors:
    general_error = "Прости, сегодня, кажется, не мой день - у меня не выходит выполнить твой запрос. Попробуй позже :("
    msg_error = 'Я не понимаю твоего сообщения - убедись, что оно не содержит ошибок. Если что, всегда есть команда \\help'

# class 