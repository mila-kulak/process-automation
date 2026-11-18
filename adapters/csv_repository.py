import csv
from pathlib import Path

from core.error_handlers import ValidationError
from core.item import Item, parse_item
from ports.item_repository import ItemRepository


CSV_FIELDS = ("id", "name", "category", "quantity", "price", "location", "created_at")


class CsvItemRepository(ItemRepository):
    def __init__(self, path: str | None = None):
        self.path = path
        self._items = {}

    def load(self, path: str) -> list[Item]:
        loaded: dict[str, Item] = {}
        try:
            with open(path, "r", encoding="utf-8", newline="") as file:
                reader = csv.DictReader(file, skipinitialspace=True)
                if reader.fieldnames is None:
                    raise ValueError("CSV-файл порожній або не містить заголовків")
                normalized_headers = [header.strip() for header in reader.fieldnames]
                if normalized_headers != list(CSV_FIELDS):
                    raise ValueError(
                            "Неправильні заголовки CSV. Очікуються: " + ", ".join(CSV_FIELDS)
                    )
                for line_number, row in enumerate(reader, start=2):
                    if None in row:
                        raise ValueError(f"Зайві колонки у рядку {line_number}")
                    normalized_row = {key.strip(): value for key, value in row.items() if key}
                    try:
                        item = parse_item(normalized_row)
                    except ValidationError as error:
                        raise ValueError(f"Рядок {line_number}, поле {error.field}: {error}") from error
                    if item.id in loaded:
                        raise ValueError(f"Рядок {line_number}: повторюється ID {item.id}")
                    loaded[item.id] = item
        except UnicodeDecodeError as error:
            raise ValueError("Не вдалося прочитати файл у кодуванні UTF-8") from error
        except csv.Error as error:
            raise ValueError(f"Помилка формату CSV: {error}") from error

        self._items = loaded
        self._path = str(path)
        return self.all()

    def all(self) -> list[Item]:
        return list(self._items.values())

    def get(self, item_id: str) -> Item | None:
        return self._items.get(str(item_id))

    def add(self, item: Item) -> None:
        if item.id in self._items:
            raise ValidationError("id", "Товар із таким ID уже існує")
        self._items[item.id] = item

    def update(self, item: Item) -> None:
        if item.id not in self._items:
            raise ValidationError("id", "Товар для оновлення не знайдено")
        self._items[item.id] = item

    def remove(self, item_id: str) -> None:
        self._items.pop(str(item_id), None)

    def save(self, path: str) -> None:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
            writer.writeheader()
            for item in self._items.values():
                writer.writerow({field: getattr(item, field) for field in CSV_FIELDS})
        self._path = str(destination)
