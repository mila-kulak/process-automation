import tkinter as tk

from adapters.csv_repository import CsvItemRepository
from adapters.tk_window import InventoryWindow
from core.inventory_service import InventoryService


def main():
    repository = CsvItemRepository()
    service = InventoryService(repository)
    root = tk.Tk()
    InventoryWindow(root, service)
    root.mainloop()


if __name__ == "__main__":
    main()
