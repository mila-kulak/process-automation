from abc import ABC, abstractmethod

from core.item import Item


class ItemRepository(ABC):
    @abstractmethod
    def all(self) -> list[Item]: ...

    @abstractmethod
    def get(self, item_id: str) -> Item | None: ...

    @abstractmethod
    def add(self, item: Item) -> None: ...

    @abstractmethod
    def update(self, item: Item) -> None: ...

    @abstractmethod
    def remove(self, item_id: str) -> None: ...
