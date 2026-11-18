import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from core.error_handlers import ValidationError


class InventoryWindow:
    COLUMNS = ("id", "name", "category", "quantity", "price", "location")
    HEADINGS = {
        "id": "ID", "name": "Назва", "category": "Категорія",
        "quantity": "Кількість", "price": "Ціна", "location": "Місце зберігання",
    }

    def __init__(self, root: tk.Tk, service):
        self.root = root
        self.service = service


        self._current_path = "products.csv"
        self._selected_id = None
        self._sort_reverse: dict[str, bool] = {}

        self.root.title("Облік товарів")
        self.root.geometry("1120x650")
        self.root.minsize(850, 500)
        self._configure_style()
        self._build_menu()
        self._build_layout()
        self.refresh()

    def _configure_style(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Error.TEntry", fieldbackground="#ffd6d6")
        style.configure("Treeview", rowheight=25)

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Відкрити...", command=self.on_open)
        file_menu.add_command(label="Зберегти", command=self.on_save)
        file_menu.add_command(label="Зберегти як...", command=self.on_save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Вихід", command=self.root.destroy)
        menubar.add_cascade(label="Файл", menu=file_menu)
        self.root.config(menu=menubar)

    def _build_layout(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        search_frame = ttk.Frame(self.root, padding=(10, 10, 10, 4))
        search_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        search_frame.columnconfigure(1, weight=1)
        ttk.Label(search_frame, text="Пошук:").grid(row=0, column=0, padx=(0, 8))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky="ew")
        self.search_var.trace_add("write", lambda *_: self.refresh())

        table_frame = ttk.Frame(self.root, padding=(10, 4, 5, 5))
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(table_frame, columns=self.COLUMNS, show="headings", selectmode="browse")
        widths = {"id": 115, "name": 180, "category": 130, "quantity": 90, "price": 90, "location": 160}
        for column in self.COLUMNS:
            self.tree.heading(column, text=self.HEADINGS[column],
                              command=lambda c=column: self.sort_by(c))
            self.tree.column(column, width=widths[column], minwidth=65, anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=y_scroll.set)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        form_frame = ttk.LabelFrame(self.root, text="Інфа про товар", padding=12)
        form_frame.grid(row=1, column=1, sticky="ns", padx=(5, 10), pady=4)
        form_frame.columnconfigure(1, weight=1)
        self.fields = {name: tk.StringVar() for name in
                       ("id", "name", "category", "quantity", "price", "location")}
        self.entries = {}
        labels = {
            "id": "ID (необов'язково)", "name": "Назва *", "category": "Категорія *",
            "quantity": "Кількість *", "price": "Ціна *", "location": "Місце (склад/полиця)",
        }
        for row, field in enumerate(self.fields):
            ttk.Label(form_frame, text=labels[field]).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=5)
            entry = ttk.Entry(form_frame, textvariable=self.fields[field], width=25)
            entry.grid(row=row, column=1, sticky="ew", pady=5)
            self.entries[field] = entry

        buttons = ttk.Frame(form_frame)
        buttons.grid(row=len(self.fields), column=0, columnspan=2, sticky="ew", pady=(14, 0))
        for column in range(2):
            buttons.columnconfigure(column, weight=1)
        ttk.Button(buttons, text="Додати", command=self.on_add).grid(row=0, column=0, sticky="ew", padx=3, pady=3)
        ttk.Button(buttons, text="Оновити", command=self.on_update).grid(row=0, column=1, sticky="ew", padx=3, pady=3)
        ttk.Button(buttons, text="Видалити", command=self.on_delete).grid(row=1, column=0, sticky="ew", padx=3, pady=3)
        ttk.Button(buttons, text="Очистити форму", command=self.clear_form).grid(row=1, column=1, sticky="ew", padx=3, pady=3)

        self.status_var = tk.StringVar(value="Готово")
        ttk.Label(self.root, textvariable=self.status_var, anchor="w", relief="sunken").grid(
            row=2, column=0, columnspan=2, sticky="ew")

    def form_data(self):
        return {name: variable.get()
                for name, variable in self.fields.items()}

    def _clear_errors(self):
        for entry in self.entries.values():
            entry.configure(style="TEntry")

    def _show_validation_error(self, error: ValidationError):
        self._clear_errors()
        if error.field in self.entries:
            self.entries[error.field].configure(style="Error.TEntry")
            self.entries[error.field].focus_set()
        self.status_var.set(f"{error.field}: {error}")

    def refresh(self, select_id=None):
        for row_id in self.tree.get_children():
            self.tree.delete(row_id)
        try:
            items = self.service.search(self.search_var.get())
        except Exception as error:
            self.status_var.set(f"Не вдалося оновити таблицю: {error}")
            return
        for item in items:
            self.tree.insert("", "end", iid=item.id, values=(
                item.id, item.name, item.category, item.quantity,
                f"{item.price:.2f}", item.location,
            ))
        if select_id and self.tree.exists(select_id):
            self.tree.selection_set(select_id)
            self.tree.focus(select_id)
            self.tree.see(select_id)

    def on_select(self, _event=None):
        selection = self.tree.selection()
        if not selection:
            return
        item_id = selection[0]
        item = self.service.get(item_id)
        if item is None:
            return
        self._selected_id = item_id
        values = {
            "id": item.id, "name": item.name, "category": item.category,
            "quantity": str(item.quantity), "price": str(item.price), "location": item.location,
        }
        for field, value in values.items():
            self.fields[field].set(value)
        self.entries["id"].configure(state="disabled")
        self._clear_errors()
        self.status_var.set(f"Вибрано товар {item.id}")

    def clear_form(self):
        self._selected_id = None
        self.tree.selection_remove(self.tree.selection())
        self.entries["id"].configure(state="normal")
        for variable in self.fields.values():
            variable.set("")
        self._clear_errors()
        self.status_var.set("Форму очищено")

    def on_add(self):
        self._clear_errors()
        try:
            item = self.service.add(self.form_data())
        except ValidationError as error:
            self._show_validation_error(error)
            return
        self.clear_form()
        self.refresh(select_id=item.id)
        self.status_var.set(f"Додано товар {item.id}")

    def on_update(self):
        if not self._selected_id:
            self.status_var.set("Спочатку виберіть товар у таблиці")
            return
        self._clear_errors()
        try:
            item = self.service.update(self._selected_id, self.form_data())
        except ValidationError as error:
            self._show_validation_error(error)
            return
        self.refresh(select_id=item.id)
        self.status_var.set(f"Оновлено товар {item.id}")

    def on_delete(self):
        selection = self.tree.selection()
        if not selection:
            self.status_var.set("Спочатку виберіть товар для видалення")
            return
        item_id = selection[0]
        if not messagebox.askyesno("Підтвердження", f"Видалити товар {item_id}?", parent=self.root):
            return
        try:
            self.service.remove(item_id)
        except ValidationError as error:
            self._show_validation_error(error)
            return
        self.clear_form()
        self.refresh()
        self.status_var.set(f"Видалено товар {item_id}")

    def sort_by(self, column):
        reverse = self._sort_reverse.get(column, False)
        rows = [(self.tree.set(iid, column), iid) for iid in self.tree.get_children("")]
        numeric = column in ("quantity", "price")
        try:
            rows.sort(key=lambda pair: float(pair[0]) if numeric else pair[0].casefold(), reverse=reverse)
        except ValueError:
            rows.sort(key=lambda pair: pair[0].casefold(), reverse=reverse)
        for position, (_, item_id) in enumerate(rows):
            self.tree.move(item_id, "", position)
        self._sort_reverse[column] = not reverse

    def on_open(self):
        path = filedialog.askopenfilename(
            title="Відкрити CSV", filetypes=[("CSV файли", "*.csv"), ("Усі файли", "*.*")],
        )
        if not path:
            return
        try:
            self.service.load(path)
        except (OSError, ValueError) as error:
            messagebox.showerror("Помилка відкриття", str(error), parent=self.root)
            self.status_var.set("Не вдалося відкрити файл")
            return
        self._current_path = path
        self.clear_form()
        self.refresh()
        self.status_var.set(f"Завантажено {len(self.service.all())} товарів")

    def on_save(self):
        if not self._current_path:
            self.on_save_as()
            return
        self._save_to(self._current_path)

    def on_save_as(self):
        path = filedialog.asksaveasfilename(
            title="Зберегти CSV як", defaultextension=".csv",
            filetypes=[("CSV файли", "*.csv"), ("Усі файли", "*.*")],
        )
        if not path:
            return
        self._save_to(path)

    def _save_to(self, path):
        try:
            self.service.save(path)
        except OSError as error:
            messagebox.showerror("Помилка збереження", str(error), parent=self.root)
            self.status_var.set("Не вдалося зберегти файл")
            return
        self._current_path = path
        self.status_var.set(f"Збережено {len(self.service.all())} товарів")
