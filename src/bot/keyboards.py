from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from src.shared.subway_map import subways
from src.shared.db import get_user_params


def reply(*rows):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t) for t in row] for row in rows],
        resize_keyboard=True,
    )


def generate_rooms_kb(id_tg):
    rooms = get_user_params(id_tg)["rooms"]

    def button(label, value, data):
        return InlineKeyboardButton(
            text=label + ("✅" if value in rooms else "❌"), callback_data=data
        )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [button(str(i), str(i), f"0{i}") for i in range(1, 5)],
            [button("Снимать комнату", "Комната", "10")],
            [InlineKeyboardButton(text="⬆️Продолжить⬆️", callback_data="go")],
        ]
    )


def generate_sub_kb(id_tg):
    selected = get_user_params(id_tg)["subways"]
    buttons = [
        InlineKeyboardButton(
            text=("✅" if str(i) in selected else "❌") + station.name,
            callback_data=str(i),
        )
        for i, station in enumerate(subways)
    ]
    rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    rows.append([InlineKeyboardButton(text="⬆️Продолжить⬆️", callback_data="go")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


landlord_kb = reply(["Собственник", "Агентство", "Не важно"])
yn_kb = reply(["Да✅", "Нет❌"])
dist_kb = reply(["Не важно"])
towns_kb = reply(["Минск", "Витебск", "Могилёв", "Гомель"])
main_menu_kb = reply(["Изменить", "Параметры", "Приостановить"])
restart_kb = reply(["Возобновить"])
continue_kb = reply(["⬆️Продолжить⬆️"])
