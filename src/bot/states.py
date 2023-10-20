from aiogram.dispatcher.filters.state import StatesGroup, State

class State(StatesGroup):
    choose_town = State()
    confirm_town = State()
    choose_cost = State()
    choose_rooms = State()
    choose_sources = State()
    choose_landlord = State()
    is_subway_needed = State()
    is_point_needed = State()
    select_point = State()
    select_radius = State()
    sending = State()
    select_branch = State()
    distance = State()
    pause = State()
    broadcast = State()