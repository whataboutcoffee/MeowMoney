from aiogram.types import (InlineKeyboardButton,
                           InlineKeyboardMarkup)


class FirstInlKeyboard:
    """First inline keyboard, to view the agreement text"""
    btn: InlineKeyboardButton = InlineKeyboardButton(
        text='Прочесть соглашение!',
        callback_data='view_agreement'
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[btn]])


class AgreementInlKeyboard:
    """Keyboard to confirm/decline the agreement"""
    confirm_btn: InlineKeyboardButton = InlineKeyboardButton(
        text='Я согласен. Начать работу!',
        callback_data='confirm_agreement'
        )

    decline_btn: InlineKeyboardButton = InlineKeyboardButton(
        text='Нет, так не пойдет',
        callback_data='decline_agreement'
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[confirm_btn], [decline_btn]])


class OperationInlKeyboard:
    """Keyboard to confirm/decline an expense/income writing without new categories"""
    confirm_btn: InlineKeyboardButton = InlineKeyboardButton(
        text='Записываем!',
        callback_data='confirm_oper'
    )

    decline_btn: InlineKeyboardButton = InlineKeyboardButton(
        text='Отклонить операцию(',
        callback_data='decline_oper'
        )
    
    confirm_without_new_ctgrs_btn: InlineKeyboardButton = InlineKeyboardButton(
        text='Записываем, но только записи без новых категорий',
        callback_data='confirm_oper_no_new_ctgrs'
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[confirm_btn], [decline_btn]]
        )
    
    keyboard_new_ctgrs = InlineKeyboardMarkup(
        inline_keyboard=[[confirm_btn], [decline_btn], [confirm_without_new_ctgrs_btn]]
        )


class DeleteOperInlKeyboard:
    confirm_del: InlineKeyboardButton = InlineKeyboardButton(
        text='Удаляем!',
        callback_data='confirm_del'
    )

    decline_del: InlineKeyboardButton = InlineKeyboardButton(
        text='Нет-нет, не надо',
        callback_data='decline_del'
    )

    keyboard: InlineKeyboardMarkup = InlineKeyboardMarkup(
        inline_keyboard=[[confirm_del], [decline_del]]
    )
