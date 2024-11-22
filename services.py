from aiogram.types import Message, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from aiogram.enums import ParseMode
from aiogram.utils.media_group import MediaGroupBuilder

from asyncpg import Connection
from io import BytesIO
import matplotlib.pyplot as plt
# from numpy import cumsum
from itertools import chain
from typing import Any, Iterable, List, Literal

from database.validation import *
from database.database import *
import answers as answ
import keyboards


class StGrp(StatesGroup):
    operation = State()
    delete_operation = State()
    delete_ctgr = State()
    # get_table_st = State()


async def proc_uncor_answ(msg: Message, **kwargs):
    await msg.answer('Некорректно задано либо не задано ключевое слово')


async def add_operation(msg_list: list,
                      msg: Message,
                      connection: Connection,
                      state: FSMContext):
    type_dict = {'расход': 'expense',
                 'р': 'expense',
                 'д': 'income',
                 'доход': 'income'}
    try:
        type_oper = type_dict[msg_list[0]]

        date, r_ctgrs = msg_list[1], msg_list[2]
    except:
        await msg.answer(answ.Errors.msg_error)
    
    try:
        user_id = msg.from_user.id
        date = validate_single_date(date)
        ctgrs_all, vals = validate_categories(r_ctgrs)
        opers: List[tuple] = list(zip(ctgrs_all, vals))
        ctgrs = set(ctgrs_all)
        new_ctgrs = await DataBase.check_categories(connection, user_id, ctgrs)

        await state.set_state(StGrp.operation)

        if new_ctgrs != None:
            transactions_old_ctgrs = []
            transactions_new_ctgrs = []
            for oper in opers:
                if oper[0] in new_ctgrs:
                    transactions_new_ctgrs.append(oper)
                else:
                    transactions_old_ctgrs.append(oper)
            
            keyboard = keyboards.OperationInlKeyboard.keyboard_new_ctgrs if len(transactions_old_ctgrs) > 0 else keyboards.OperationInlKeyboard.keyboard

            await msg.answer(
            text=answ.Operation.oper(transactions_old_ctgrs, type_oper, date, transactions_new_ctgrs),
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
            )
            await state.update_data({'opers': opers,
                                    'old_ctgrs': transactions_old_ctgrs,
                                    'type': type_oper,
                                    'date': date,
                                    'new_ctgrs': new_ctgrs})
            return None
        
        await state.update_data({'opers': opers,
                                'old_ctgrs': [],
                                'type': type_oper,
                                'date': date,
                                'new_ctgrs': None})
        await msg.answer(
            text=answ.Operation.oper(opers, type_oper, date),
            reply_markup=keyboards.OperationInlKeyboard.keyboard,
            parse_mode=ParseMode.HTML
        )
    except ValueError as ex:
        await msg.answer(str(ex))
        return None
    except:
        await msg.answer(answ.Errors.general_error)


async def delete_oper(msg_list: list,
                      msg: Message,
                      connection: Connection,
                      state: FSMContext):
    
    opers, oper_ids, ctgrs_not_found, dates_db, amount, _ = await _get_table(msg_list,
                                                                            msg,
                                                                            connection,
                                                                            state)
    try:
        await state.set_state(StGrp.delete_operation)
        await state.update_data({'oper_ids': oper_ids})
        if amount > 0:
            min_date = min(dates_db)
            max_date = max(dates_db)
            if amount <= 30:
                text = answ.AnswersForTable.with_opers('del',
                                                amount,
                                                min_date,
                                                max_date,
                                                opers,
                                                ctgrs_not_found)
            else:
                text = answ.AnswersForTable.without_opers('del',
                                                    amount,
                                                    min_date,
                                                    max_date,
                                                    ctgrs_not_found)
            
            await msg.answer(text=text,
                        reply_markup=keyboards.DeleteOperInlKeyboard.keyboard,
                        parse_mode=ParseMode.HTML)
            
        else:
            text = answ.AnswersForTable.only_not_found()
            await msg.answer(text=text)
            await state.clear()
    except Exception as e:
        await msg.answer(answ.Errors.general_error)


async def _get_table(msg_list: list,
                      msg: Message,
                      connection: Connection,
                      state: FSMContext,
                      group_by: bool = False) -> None:
    try:
        dates_row: str = msg_list[1]
        records_row: str = msg_list[2].lower()
    except:
        await msg.answer(answ.Errors.msg_error)
        raise
    try:
        user_id: int = msg.from_user.id
        date1, date2 = validate_dates_str(dates_row)
        user_ctgrs = await DataBase.return_all_ctgrs(connection,
                                                            user_id)
        if records_row != '...':
            ctgrs_to_fetch_row, except_ctgrs_row = process_records_row(records_row)
            ctgrs_to_fetch = validate_records_to_fetch(ctgrs_to_fetch_row)
            except_ctgrs = change_records(validate_records_to_fetch(except_ctgrs_row))

            # Validate categories names before and after "кроме"
            names_to_fetch = set([r[0] for r in ctgrs_to_fetch])
            names_except_ctgrs = set([r[0] for r in except_ctgrs])
            intersection = names_to_fetch.intersection(names_except_ctgrs)
            
            if intersection != set():
                raise ValueError(f'Есть одинаковые категории до и после "кроме": {", ".join(intersection)}')

            if except_ctgrs != []:
                names_misc_ctgrs = list(set(user_ctgrs).difference(set(names_except_ctgrs), set(names_to_fetch)))
                misc_ctgrs = [[c, None, None, None, None] for c in names_misc_ctgrs]
                ctgrs_to_fetch += misc_ctgrs
        else:
            ctgrs_to_fetch = [[c, None, None, None, None] for c in user_ctgrs]
            except_ctgrs = []
        
        opers, oper_ids, ctgrs_not_found = await DataBase.fetch(connection,
                                                                user_id,
                                                                date1,
                                                                date2,
                                                                ctgrs_to_fetch + except_ctgrs,
                                                                user_ctgrs,
                                                                group_by)
        amount = len(opers)

        dates_db = [oper[2] for oper in opers] if not group_by else [d for oper in opers for d in oper[2]]
        return opers, oper_ids, ctgrs_not_found, dates_db, amount, user_ctgrs
    except ValueError as ex:
        await msg.answer(str(ex))
        raise
    except:
        await msg.answer(answ.Errors.general_error)
        raise
    
    
async def get_table(
        msg_list: list,
        msg: Message,
        connection: Connection,
        state: FSMContext
):
    opers, oper_ids, ctgrs_not_found, dates_db, amount, _ = await _get_table(msg_list,
                                                                    msg,
                                                                    connection,
                                                                    state)
    try:
        if amount > 0:
            min_date = min(dates_db)
            max_date = max(dates_db)
            text = answ.AnswersForTable.with_opers('table',
                                                amount,
                                                min_date,
                                                max_date,
                                                opers,
                                                ctgrs_not_found)
            await msg.answer(text=text + '\n' + answ.AnswersForTable.stats(opers),
                            parse_mode=ParseMode.HTML)
        else:
            text = answ.AnswersForTable.only_not_found()
            await msg.answer(text=text)
    except:
        await msg.answer(answ.Errors.general_error)
        raise


def _create_plot_bytes(fig: plt.Figure) -> BufferedInputFile:
    plot = BytesIO()
    fig.savefig(plot, format='png')
    plot.seek(0)
    return BufferedInputFile(file=plot.getvalue(), filename='plot.png')


async def bar(
        msg_list: list,
        msg: Message,
        connection: Connection,
        state: FSMContext
):
    opers, _, _, _, amount, _ = await _get_table(msg_list,
                                            msg,
                                            connection,
                                            state,
                                            group_by=True)
    if opers == []:
        await msg.answer(answ.AnswersForTable.only_not_found())
    else:
        try:
            ctgrs, vals, _, types = list(zip(*opers))
            if amount > 30:
                await msg.answer(answ.for_chart(amount, 20)) # WTF??
            fig, ax = plt.subplots()

            # create list of colors for bars depending on their types
            colors = ['tab:blue' if t == 'expense' else 'tab:green' for t in types] 
            ax.barh(tuple(map(str.title, ctgrs)), vals, color=colors)

            max_val = max(vals)
            for i in range(len(ctgrs)):
                r = vals[i]/max_val
                ax.text(vals[i]/2 if r >= 0.3 else vals[i] + max_val*0.03,
                         i,
                         answ.convert_num_to_str(vals[i], 'letters'),
                         ha='left',
                         va='center',
                         c='white' if r >= 0.3 else 'black')

            # format y ticks
            xticks = ax.get_xticks()
            ax.set_xticklabels([answ.convert_num_to_str(num, 'letters') for num in xticks])
            ax.yaxis.set_tick_params(left=False)
            
            fig.tight_layout()
            await msg.answer_photo(_create_plot_bytes(fig), f'Вот и твой график)\nА еще немного статистики:\n{answ.AnswersForTable.stats(opers)}')
        except:
            await msg.answer(answ.Errors.general_error)
            raise


def _squashed_opers_for_pie(opers: List[tuple],
                          ctgrs,
                          vals,
                          type_opers: Union[Literal['income'], Literal['expense']],
                          amount_squash: int):
    """Squashes opers with small values (that has a sequence number less than the specified amount_squah) into one operation with the specified type"""
    ctgr_to_add = 'Остальные расходы' if type_opers == 'expense' else 'Остальные доходы'
    new_ctgrs = (ctgr_to_add,) + ctgrs[amount_squash:]
    # misc_ctgrs = ctgrs[:amount_squash]
    misc_opers = opers[:amount_squash]
    misc_opers = [(oper[0], oper[1]) for oper in misc_opers]
    misc_sum = sum(oper[1] for oper in misc_opers)
    new_vals = (misc_sum,) + vals[amount_squash:]
    new_opers = [(ctgr_to_add, misc_sum, None, type_opers)] + opers[amount_squash:]

    return new_opers, new_ctgrs, new_vals, misc_opers


def _amount_opers_to_squash(vals: tuple, frac: float) -> int:
    """Finds the sequence number of the value which is the smallest number greater than the specified frac.
    The input vals tuple has to be sorted.
    If such a value does not exist returns None"""
    for i, val in enumerate(vals):
        if val > frac:
            return i
    return None


async def pie(
        msg_list: list,
        msg: Message,
        connection: Connection,
        state: FSMContext
):
    opers, _, ctgrs_not_found, _, _, _ = await _get_table(msg_list,
                                            msg,
                                            connection,
                                            state,
                                            group_by=True)
    if opers == []:
        await msg.answer(answ.AnswersForTable.only_not_found())
    else:
        try:
            opers_exp = list(filter(lambda x: x[3] == 'expense', opers))
            opers_inc = list(filter(lambda x: x[3] == 'income', opers))
            ctgrs_exp, vals_exp, _, _ = list(zip(*opers_exp))
            ctgrs_inc, vals_inc, _, _ = list(zip(*opers_inc))

            frac_exp = tuple(i/sum(vals_exp) for i in vals_exp)
            frac_inc = tuple(i/sum(vals_inc) for i in vals_inc)
            amount_squash_exp = _amount_opers_to_squash(frac_exp, 0.02)
            amount_squash_inc = _amount_opers_to_squash(frac_inc, 0.02)
            misc_opers_exp = []
            misc_opers_inc = []
            if amount_squash_exp > 1:
                opers_exp, ctgrs_exp, vals_exp, misc_opers_exp = _squashed_opers_for_pie(
                    opers_exp,
                    ctgrs_exp,
                    vals_exp,
                    'expense',
                    amount_squash_exp
                )
            if amount_squash_inc > 1:
                opers_inc, ctgrs_inc, vals_inc, misc_opers_inc = _squashed_opers_for_pie(
                    opers_inc,
                    ctgrs_inc,
                    vals_inc,
                    'income',
                    amount_squash_inc
                )
            fig_exp, ax_exp = plt.subplots(constrained_layout=True)
            labels_exp = [f'{ctgrs_exp[i].title()}: {answ.convert_num_to_str(vals_exp[i], "letters")}' for i in range(len(vals_exp))]
            labels_inc = [f'{ctgrs_inc[i].title()}: {answ.convert_num_to_str(vals_inc[i], "letters")}' for i in range(len(vals_inc))]
            ax_exp.pie(x=vals_exp,
                   labels=labels_exp ,
                   colors=['blue'],
                   wedgeprops={'linewidth': 1, 'edgecolor': "white"},
                   shadow=True
                   )
            
            fig_inc, ax_inc = plt.subplots(constrained_layout=True)
            ax_inc.pie(x=vals_inc,
                   labels=labels_inc,
                   colors=['green'],
                   wedgeprops={'linewidth': 1, 'edgecolor': "white"},
                   shadow=True
                   )

            media_group = MediaGroupBuilder()
            media_group.add_photo(media=_create_plot_bytes(fig_exp))
            media_group.add_photo(media=_create_plot_bytes(fig_inc))
            await msg.answer_media_group(media=media_group.build())
            await msg.answer(answ.Chart.caption(opers, ctgrs_not_found, misc_opers_exp, misc_opers_inc), parse_mode=ParseMode.HTML)
        except:
            await msg.answer(answ.Errors.general_error)
            raise


async def delete_ctgr(
        msg_list: list,
        msg: Message,
        connection: Connection,
        state: FSMContext
):
    try:
        ctgr: str = msg_list[1]
    except:
        await msg.answer(answ.Errors.msg_error)
    try:
        user_id = msg.from_user.id
        ctgr_set = set()
        ctgr_set.add(ctgr)
        new = await DataBase.check_categories(connection, user_id, ctgr_set)
        if new:
            raise ValueError('Такой категории нет')
        await state.set_state(StGrp.delete_ctgr)
        await state.update_data({'ctgr': ctgr})
        await msg.answer(text=answ.DelCtgr.del_ctgr(ctgr),
                         reply_markup=keyboards.DeleteCtgrInlKeyboard.keyboard,
                         parse_mode=ParseMode.HTML)
    except ValueError as ex:
        await msg.answer(str(ex))
    except:
        await msg.answer(answ.Errors.general_error)


async def get_short_table(msg_list: list,
        msg: Message,
        connection: Connection,
        state: FSMContext
):
    opers, _, ctgrs_not_found, dates_db, amount, _ = await _get_table(msg_list,
                                                                    msg,
                                                                    connection,
                                                                    state,
                                                                    group_by=True)
    try:
        if amount > 0:
            min_date = min(dates_db)
            max_date = max(dates_db)
            text = answ.AnswersForTable.with_opers_short_table(amount,
                                                min_date,
                                                max_date,
                                                opers,
                                                ctgrs_not_found)
            await msg.answer(text=text + '\n' + answ.AnswersForTable.stats(opers),
                            parse_mode=ParseMode.HTML)
        else:
            text = answ.AnswersForTable.only_not_found()
            await msg.answer(text=text)
    except:
        await msg.answer(answ.Errors.general_error)
        raise
    