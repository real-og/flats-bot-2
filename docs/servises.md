# Парсеры и доставка

Три независимых источника → постоянный inbox → нормализация/фильтры → outbox
по получателям → Telegram. Процесс: `python -m src.service.main_flats_parser`.
Подробности и ограничения: [AUDIT.md](AUDIT.md), [OPERATIONS.md](OPERATIONS.md).
