from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton

from src.shared.subway_map import subways
from src.shared.db import get_user_params
from typing import List, Literal

def generate_rooms_kb(id_tg: int) -> InlineKeyboardMarkup:
    inline_kb1 = InlineKeyboardMarkup(row_width=4)
    rooms = get_user_params(id_tg)['rooms']
    inline_btn_1 = InlineKeyboardButton('1' + ('✅' if '1' in rooms else '❌'), callback_data='01')
    inline_btn_2 = InlineKeyboardButton('2' + ('✅' if '2' in rooms else '❌'), callback_data='02')
    inline_btn_3 = InlineKeyboardButton('3' + ('✅' if '3' in rooms else '❌'), callback_data='03')
    inline_btn_4 = InlineKeyboardButton('4' + ('✅' if '4' in rooms else '❌'), callback_data='04')
    inline_btn_5 = InlineKeyboardButton('Снимать комнату' + ('✅' if 'Комната' in rooms else '❌'), callback_data='10')
    inline_btn_6 = InlineKeyboardButton('⬆️Продолжить⬆️', callback_data='go')
    return inline_kb1.add(inline_btn_1, inline_btn_2, inline_btn_3, inline_btn_4, inline_btn_5).row(inline_btn_6)


def generate_sub_kb(id_tg: int) -> InlineKeyboardMarkup:
    inline_kb = InlineKeyboardMarkup(row_width=2)
    subs = get_user_params(id_tg)['subways']
    for i in range(0, 15):
        inline_kb.add(InlineKeyboardButton(('✅' if str(i) in subs else '❌') + subways[i].name, callback_data=str(i)),
                       InlineKeyboardButton(('✅' if str(i + 15) in subs else '❌') + subways[i + 15].name, callback_data=str(i + 15)))
    for i in range(30, 33):
        inline_kb.add(InlineKeyboardButton(('✅' if str(i) in subs else '❌') + subways[i].name, callback_data=i))
    inline_kb.add(InlineKeyboardButton('⬆️Продолжить⬆️', callback_data='go'))
    return inline_kb

# not really need it
def generate_new_kb(call: InlineKeyboardMarkup,
                    num: Literal['01', '02', '03', '04', '10'],
                    size: int)-> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=size)
    target = call[int(num[0])][int(num[1]) - 1]
    if '❌' in target.text:
        target.text = target.text.replace('❌', '✅')
    else:
        target.text = target.text.replace('✅', '❌')
    for row in call[:-1]:
        for item in row:
            keyboard.insert(item)
    return keyboard.add(call[-1][-1])

def generate_chosen_rooms_kb(id_tg: int) -> InlineKeyboardMarkup:
    inline_kb = InlineKeyboardMarkup(row_width=4)
    rooms = get_user_params(id_tg)['rooms']
    inline_btn_1 = InlineKeyboardButton('1' + ('✅' if '1' in rooms else '❌'), callback_data='01')
    inline_btn_2 = InlineKeyboardButton('2' + ('✅' if '2' in rooms else '❌'), callback_data='02')
    inline_btn_3 = InlineKeyboardButton('3' + ('✅' if '3' in rooms else '❌'), callback_data='03')
    inline_btn_4 = InlineKeyboardButton('4' + ('✅' if '4' in rooms else '❌'), callback_data='04')
    inline_btn_5 = InlineKeyboardButton('Снимать комнату' + ('✅' if 'Комната' in rooms else '❌'), callback_data='10')
    inline_btn_6 = InlineKeyboardButton('⬆️Продолжить⬆️', callback_data='go')
    return inline_kb.add(inline_btn_1, inline_btn_2, inline_btn_3, inline_btn_4, inline_btn_5).row(inline_btn_6)

def generate_subway_chosen_kb(id_tg: int) -> InlineKeyboardMarkup:
    inline_kb = InlineKeyboardMarkup(row_width=2)
    subs = get_user_params(id_tg)['subways']
    for i in range(0, 15):
        inline_kb.add(InlineKeyboardButton(('✅' if str(i) in subs else '❌') + subways[i].name, callback_data=str(i)),
                       InlineKeyboardButton(('✅' if str(i + 15) in subs else '❌') + subways[i + 15].name, callback_data=str(i + 15)))
    for i in range(30, 33):
        inline_kb.add(InlineKeyboardButton(('✅' if str(i) in subs else '❌') + subways[i].name, callback_data=i))
    inline_kb.add(InlineKeyboardButton('⬆️Продолжить⬆️', callback_data='go'))
    return inline_kb


landlord_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
btn_lord_1 = KeyboardButton('Собственник')
btn_lord_2 = KeyboardButton('Агентство')
btn_lord_3 = KeyboardButton('Не важно')
landlord_kb.add(btn_lord_1, btn_lord_2, btn_lord_3)

yn_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
btn_yn_1 = KeyboardButton('Да✅')
btn_yn_2 = KeyboardButton('Нет❌')
yn_kb.add(btn_yn_1, btn_yn_2)

dist_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(KeyboardButton('Не важно'))

towns_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
btn_town_1 = KeyboardButton('Минск')
btn_town_2 = KeyboardButton('Витебск')
btn_town_3 = KeyboardButton('Могилёв')
btn_town_4 = KeyboardButton('Гомель')
towns_kb.row(btn_town_1, btn_town_2, btn_town_3, btn_town_4)

main_menu_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
btn_my_setup = KeyboardButton('Параметры')
btn_change_setup = KeyboardButton('Изменить')
btn_pause = KeyboardButton('Приостановить')
main_menu_kb.add(btn_change_setup, btn_my_setup, btn_pause)

restart_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(KeyboardButton('Возобновить'))

continue_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add('⬆️Продолжить⬆️')