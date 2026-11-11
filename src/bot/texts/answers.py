from html import escape
from src.shared import db
from src.shared.subway_map import subways


def town_chosen(town):
    town = escape(town)
    return f"Ищу квартиры в городе <b>{town}</b> \
    \n\nТеперь выбери <b>допустимую стоимость</b> в долларах США (USD) \
    <b>через пробел</b>\n\n<i>Например 300 450, значит от 300$ до 450$</i>"


def cost_chosen(min_cost, max_cost):
    return f"Ищу квартиры от <b>{min_cost}$ до {max_cost}$</b>"


def compose_params(id: int) -> str:
    params = db.get_user_params(id)
    params["town"] = escape(params["town"])

    text = f"""город: <b>{params["town"]}</b>
цена: <b>{params["minCost"]}$ - {params["maxCost"]}$</b>
от: <b>{params["landlord"]}</b>
комнат: <b>{", ".join(params["rooms"])}</b>\n"""

    if params["isSubwayNeed"]:
        text = text + "метро:"
        for st in params["subways"]:
            text = text + "\n<b>" + subways[int(st)].name + "</b>"
        text = text + f"\nдо ближайшего: <b>{params['subway_dist']}</b> м"
    else:
        text = text + "метро: <b>Не важно</b>"

    if params["isPointNeed"]:
        text = (
            text
            + f"\nширота: <b>{params['lat']}</b>\nдолгота: <b>{params['lon']}</b>\nв радиусе: <b>{params['point_dist']}</b> м"
        )
    else:
        text = text + "\nпо точке на карте <b>не выбрано</b>"

    return text


welcome = "Давай определимся с параметрами!"

enter_town = "Вводи <strong>навание города</strong>"

no_town_supported = "Не нашёл такого города. Проверь, нет ли опечатки.\n\n \
<i>Нажимай <b>⬆️Продолжить⬆️</b>, если всё правильно\n\nили вводи название другого города</i>"

enter_cost = "Теперь выбери <b>допустимую стоимость</b> в долларах США (USD) \
<b>через пробел</b>\n<i>Например 300 450, значит от 300$ до 450$</i>"

bad_input = "Что-то введено не так..."

min_max_error = "Минимальная стоимость больше максимальной, введи снова"

enter_rooms = "Кнопками выбери <b>количество комнат</b>, можно несколько. \
\n\n<b>⬆️Продолжить⬆️</b> <i>когда справишься</i>"

enter_landlord = "<b>Собственник, Агентство или Не важно?</b>"

enter_subway_need = "Отлично! Важно ли <b>метро</b>?"

enter_location_need = "<b>Отлично!</b>\nВыбирать <b>район поиска</b>? \
Ты можешь выбрать точку на карте и радиус, из которого присылать объявления!"

enter_subways = (
    "Выбирай кнопками нужные станции.\n\n<i>Когда закончишь - <b>⬆️Продолжить⬆️</b></i>"
)

enter_distance_subway = "<b>Максимальное расстояние в метрах</b> \
до ближайшей станции\n\n<i>или</i> <b>Не важно</b>"

bad_distance = "Не понял, напиши число в метрах либо <b>Не важно</b>"

finished = (
    "<b>Отлично!</b>\nКак только квартиры по заданным параметрам появятся, пришлю вам!"
)

enter_location = (
    "Присылай <b>координаты</b>\n\nС телефона ты можешь поделиться геопозицией, \
нажав <b>📎Прикретить</b>\n\n<b>Либо</b> бы можешь прислать <b>широту и долготу</b> \
через запятую, например из Яндекс Карт.\n\n<i>Вот так: </i>53.901519, 27.553638"
)

enter_radius = "Теперь <b>радиус в метрах</b>, чтобы определиться с площадью поиска\n\n"

paused = "Ничего не присылаю. Надеюсь, нашёл, что искал 😌"

reset_filters = "Давай заново, пиши <b>город</b>"

resumed = "Пришлю, как только появится что-то новое!"

bad_input_menu = "Не понял.\n<b>Возобновить</b> чтобы начать снова"

bad_input_universal = "Что-то не понял. Попробуй /start"

enter_message_to_broadcast = "Вводи сообщение для рассылки или /quit"
quited_broadcast = "Рассылка отменена, ты в состоянии sending. Введи все фильтры заново, если не приходят объявления"
