from core.error_handlers import ValidationError
from core.item import Item, parse_item
from ports.item_repository import ItemRepository


class InventoryService:

    def __init__(self, repository: ItemRepository):
        self._repository = repository

    def all(self) -> list[Item]:
        return self._repository.all()

    def get(self, item_id: str) -> Item | None:
        return self._repository.get(item_id)

    def add(self, form: dict[str, str]) -> Item:
        item = parse_item(form)
        if self._repository.get(item.id):
            raise ValidationError("id", "Товар із таким ID уже існує")
        self._repository.add(item)
        return item

    def update(self, item_id: str, form: dict[str, str]) -> Item:
        if self._repository.get(item_id) is None:
            raise ValidationError("id", "Товар для оновлення не знайдено")
        prepared = dict(form)
        prepared["id"] = item_id
        old_item = self._repository.get(item_id)
        prepared["created_at"] = old_item.created_at
        item = parse_item(prepared)
        self._repository.update(item)
        return item

    def remove(self, item_id: str) -> None:
        if self._repository.get(item_id) is None:
            raise ValidationError("id", "Товар не знайдено")
        self._repository.remove(item_id)

    def search(self, text: str) -> list[Item]:
        query = text.strip().lower()
        items = self._repository.all()
        return [item for item in items
                if query in item.name.lower() or query in item.category.lower()]

    def load(self, path: str) -> list[Item]:
        return self._repository.load(path)

    def save(self, path: str) -> None:
        self._repository.save(path)
