
from datetime import datetime
from uuid import uuid4

from core.error_handlers import ValidationError


class Item:
    def __init__(self, id: str, name: str, category: str, quantity: int, price: float, location: str, created_at: str):
        self.id, self.name, self.category = id, name, category
        self.quantity, self.price, self.location = quantity, price, location
        self.created_at = created_at


FORM_FIELDS = ("id", "name", "category", "quantity", "price", "location")


def parse_quantity(value: str) -> int:
    try:
        result = int(str(value).strip())
    except ValueError:
        raise ValidationError("quantity", "Кількість має бути цілим числом")
    if result < 0:
        raise ValidationError("quantity", "Кількість не може бути від'ємною")
    return result


def parse_price(value: str) -> float:
    normalized = str(value).strip().replace(",", ".")
    try:
        result = float(normalized)
    except ValueError:
        raise ValidationError("price", "Ціна має бути числом")
    if result < 0:
        raise ValidationError("price", "Ціна не може бути від'ємною")
    return result


def parse_item(form: dict) -> Item:
    values = {}
    for field in FORM_FIELDS:
        values[field] = str(form.get(field, ""))

    for field in ("name", "category"):
        if not values[field].strip():
            labels = {"name": "Назва", "category": "Категорія"}
            raise ValidationError(field, f"{labels[field]} не може бути порожньою")

    item_id = values["id"].strip() or str(uuid4())
    created_at = datetime.now().isoformat(timespec="seconds")

    return Item(
        id=item_id,
        name=values["name"].strip(),
        category=values["category"].strip(),
        quantity=parse_quantity(values["quantity"]),
        price=parse_price(values["price"]),
        location=values["location"].strip(),
        created_at=created_at,
    )
