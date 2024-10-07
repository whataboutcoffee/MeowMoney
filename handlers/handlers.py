# To handle first commands, "/start" and the following ones,
# prior to normal work with bot

from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from aiogram.fsm.state import default_state, State, StatesGroup
from aiogram.fsm.context import FSMContext

from asyncpg import Connection
from typing import List

import answers as answ
import keyboards
import services
from database.database import DataBase


router = Router()

# Handler for "/start"
@router.message(CommandStart())
async def process_start_command(msg: Message):
    await msg.answer(text=answ.StartText.first_answ(),
                    reply_markup=keyboards.FirstInlKeyboard.keyboard)


# Handler for all the main text commands. Transfers
# the message text to the corresponding function
@router.message(F.text, StateFilter(default_state), flags={'database': True})
async def process_text(msg: Message, conn: Connection, state: FSMContext):
    msg_list = [i.lower().strip() for i in msg.text.split(sep='\n')]
    func_dict = {'расход': services.add_operation,
                 'р': services.add_operation,
                 'доход': services.add_operation,
                 'д': services.add_operation,
                 'удалить': services.delete_oper,
                 'у': services.delete_oper,
                 'т': services.get_table,
                 'таблица': services.get_table,
                 'с': services.bar,
                 'столбчатая диаграмма': services.bar,
                 'к': services.pie,
                 'круговая диаграмма': services.pie}
    if len(msg_list) == 1 and msg_list[0] in func_dict:
        await msg.answer('Что-что ты хочешь сделать? Я понял, какую функцию ты пытаешься использоапть, но мне недостаточно данных')
        return None
    await func_dict.get(msg_list[0], services.proc_uncor_answ)(msg_list=msg_list,
                                                      msg=msg,
                                                      connection=conn,
                                                      state=state)


# # Handler for "Прочти соглашение!"
# @router.callback_query(F.data == 'view_agreement')
# async def process_view_agreement(callback: CallbackQuery):
#     await callback.message.edit_text(
#         text=answ.StartText.agreement(),
#         reply_markup=keyboards.AgreementInlKeyboard.keyboard)


# # Handler for "confirm_agreement" callback data
# @router.callback_query(F.data == 'confirm_agreement')
# async def process_confirm_agreement(callback: CallbackQuery):
#     await callback.message.answer(text=answ.StartText.successful_agreement())


# Handler to confirm operation (expense/income)
@router.callback_query(F.data.in_(['confirm_oper', 'confirm_oper_no_new_ctgrs']),
                       StateFilter(services.StGrp.operation),
                       flags={'database': True})
async def process_confirm_oper(callback: CallbackQuery, conn: Connection, state: FSMContext, bot: Bot):
    data = await state.get_data()
    opers: List[tuple] = data["opers"] if callback.data == 'confirm_oper' else data['old_ctgrs']
    data_for_db = list(zip(*opers))
    ctgrs, vals = data_for_db[0], data_for_db[1]
    user_id = callback.from_user.id
    type_oper = data['type']
    date = data['date']
    await state.clear()
    new_ctgrs: set = data["new_ctgrs"]

    if callback.data == 'confirm_oper' and new_ctgrs != None:
        await DataBase.add_categories(conn, user_id, new_ctgrs, type_oper)
    
    await DataBase.add_operation_db(conn, user_id, date, type_oper, ctgrs, vals)
    oper = "расход" if type_oper == 'expense' else "доход"
    answer = answ.Operation.oper_confirmed(oper.capitalize()) if callback.data == 'confirm_oper' else answ.Operation.oper_confirmed_only_new_ctgrs(oper.capitalize())
    await callback.message.answer(answer)
    await bot.edit_message_reply_markup(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )


@router.callback_query(F.data == "decline_oper",
                       StateFilter(services.StGrp.operation))
async def process_decline_oper(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.clear()
    await bot.edit_message_reply_markup(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )
    await callback.message.answer('Запись операции отменена')


@router.message(StateFilter(services.StGrp.operation, services.StGrp.delete_operation))
async def process_text_confirm_oper(msg: Message):
    await msg.answer("Пожалуйста, сначала используйте последнюю инлайн-клавиатуру")


@router.callback_query(F.data == 'confirm_del', # TEST
                       StateFilter(services.StGrp.delete_operation),
                       flags={'database': True})
async def process_del_oper(callback: CallbackQuery, state: FSMContext, conn: Connection, bot: Bot):
    oper_ids: dict = await state.get_data()
    await state.clear()
    await DataBase.del_from_db(conn, oper_ids['oper_ids'])
    await callback.message.answer('Операции(-я) удалены(-а) из базы данных!')
    await bot.edit_message_reply_markup(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

@router.callback_query(F.data == 'decline_del',
                       StateFilter(services.StGrp.delete_operation))
async def process_decline_del_oper(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.clear()
    await bot.edit_message_reply_markup(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )
    await callback.message.answer('Удаление операций отменено')
