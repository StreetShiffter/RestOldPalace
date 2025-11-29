import tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk

MEDIA_DIR = Path(__file__).parent / "media"


class RestaurantHallMap:
    def __init__(self, root):
        self.root = root
        self.root.title("Выбор столиков")
        self.root.geometry("1420x700")

        # Фильтр: None = BASE_ALL, 2 = BASE_ONLY_2, 4 = BASE_ONLY_4
        self.current_filter = None
        self.selected_tables = set()  # номера выбранных столов
        self.marker_images = {}  # {table_number: image_id} для удаления маркеров

        # Загрузка изображений
        self.load_images()

        # Списки столов для каждого фона
        self.tables_all = [
            {"x": 78, "y": 40, "shape": "rect", "capacity": 2, "number": 1},
            {"x": 231, "y": 40, "shape": "rect", "capacity": 2, "number": 2},
            {"x": 384, "y": 40, "shape": "rect", "capacity": 2, "number": 3},
            {"x": 57, "y": 135, "shape": "round", "capacity": 4, "number": 4},
            {"x": 234.5, "y": 135, "shape": "round", "capacity": 4, "number": 5},
            {"x": 57, "y": 278, "shape": "round", "capacity": 4, "number": 6},
            {"x": 234.5, "y": 278, "shape": "round", "capacity": 4, "number": 7},
            {"x": 416, "y": 278, "shape": "round", "capacity": 4, "number": 8},
            {"x": 53, "y": 422, "shape": "round", "capacity": 4, "number": 9},
            {"x": 231.5, "y": 422, "shape": "round", "capacity": 4, "number": 10},
            {"x": 411, "y": 422, "shape": "round", "capacity": 4, "number": 11},
            {"x": 179, "y": 626.5, "shape": "rect", "capacity": 2, "number": 12},
            {"x": 333, "y": 626.5, "shape": "rect", "capacity": 2, "number": 13},
            {"x": 485.5, "y": 626.5, "shape": "rect", "capacity": 2, "number": 14},
            {"x": 640, "y": 626.5, "shape": "rect", "capacity": 2, "number": 15},
        ]

        self.tables_only_2 = [
            {"x": 78, "y": 40, "shape": "rect", "capacity": 2, "number": 1},
            {"x": 231, "y": 40, "shape": "rect", "capacity": 2, "number": 2},
            {"x": 384, "y": 40, "shape": "rect", "capacity": 2, "number": 3},
            {"x": 179, "y": 626.5, "shape": "rect", "capacity": 2, "number": 12},
            {"x": 333, "y": 626.5, "shape": "rect", "capacity": 2, "number": 13},
            {"x": 485.5, "y": 626.5, "shape": "rect", "capacity": 2, "number": 14},
            {"x": 640, "y": 626.5, "shape": "rect", "capacity": 2, "number": 15},
        ]

        self.tables_only_4 = [
            {"x": 57, "y": 135, "shape": "round", "capacity": 4, "number": 4},
            {"x": 234.5, "y": 135, "shape": "round", "capacity": 4, "number": 5},
            {"x": 57, "y": 278, "shape": "round", "capacity": 4, "number": 6},
            {"x": 234.5, "y": 278, "shape": "round", "capacity": 4, "number": 7},
            {"x": 416, "y": 278, "shape": "round", "capacity": 4, "number": 8},
            {"x": 53, "y": 422, "shape": "round", "capacity": 4, "number": 9},
            {"x": 231.5, "y": 422, "shape": "round", "capacity": 4, "number": 10},
            {"x": 411, "y": 422, "shape": "round", "capacity": 4, "number": 11},
        ]

        self.setup_ui()
        self.set_filter_all()

    def load_images(self):
        """Адаптация шаблонов меню"""
        self.bg_all = self._load_image("BASE_ALL.png", (1250, 700))
        self.bg_only_2 = self._load_image("BASE_ONLY_2.png", (1250, 700))
        self.bg_only_4 = self._load_image("BASE_ONLY_4.png", (1250, 700))

        # Активные иконки (жёлтые маркеры)
        self.icon_2 = self._load_image("2_ON.png", (95, 40))  # прямоугольный
        self.icon_4 = self._load_image("4_ON.png", (161, 146))  # круглый

    def _load_image(self, name, size=None):
        """Загрузка шаблонов меню"""
        path = MEDIA_DIR / name
        if path.exists():
            img = Image.open(path)
            if size:
                img = img.resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        return None

    def setup_ui(self):
        """Окно меню с выбранными столиками"""
        self.canvas = tk.Canvas(self.root, width=1250, height=700)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Панель управления — фиксированная ширина
        frame = tk.Frame(self.root, width=200)
        frame.pack_propagate(False)  # ⚠️ Запрещаем изменять размер по содержимому
        frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        tk.Button(frame, text="✅ Все", command=self.set_filter_all).pack(
            pady=5, fill=tk.X
        )
        tk.Button(frame, text="🔵 Только на 2", command=self.set_filter_only_2).pack(
            pady=5, fill=tk.X
        )
        tk.Button(frame, text="🟣 Только на 4", command=self.set_filter_only_4).pack(
            pady=5, fill=tk.X
        )

        self.selected_label = tk.Label(
            frame, text="Выбрано: —", justify="left", anchor="nw"
        )
        self.selected_label.pack(pady=10, fill=tk.X)

        tk.Button(frame, text="Очистить", command=self.clear_selection).pack(
            pady=10, fill=tk.X
        )

        self.canvas.bind("<Button-1>", self.on_click)

    def format_selected_tables(self):
        """Формат отображения нумераций в меню"""
        if not self.selected_tables:
            return "Выбрано: —"
        nums = sorted(self.selected_tables)
        lines = []
        for i in range(0, len(nums), 4):
            group = nums[i:i + 4]
            lines.append(", ".join(map(str, group)))
        return "Выбрано:\n" + "\n".join(lines)

    def set_filter_all(self):
        """Шаблон всех столов, для динамического выбора"""
        self.current_filter = "all"
        self.current_tables = self.tables_all
        self.bg_image = self.bg_all
        self.redraw()

    def set_filter_only_2(self):
        """Шаблон столов по 2 места, для динамического выбора"""
        self.current_filter = "only_2"
        self.current_tables = self.tables_only_2
        self.bg_image = self.bg_only_2
        self.redraw()

    def set_filter_only_4(self):
        """Шаблон столов по 4 места, для динамического выбора"""
        self.current_filter = "only_4"
        self.current_tables = self.tables_only_4
        self.bg_image = self.bg_only_4
        self.redraw()

    def clear_selection(self):
        """Метод обнуления выбора"""
        for table_num in list(self.selected_tables):
            self.remove_marker(table_num)
        self.selected_tables.clear()
        self.redraw()

    def redraw(self):
        self.canvas.delete("all")
        # Фон
        if self.bg_image:
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_image)

        # Отрисовываем маркеры для выбранных столов
        for table in self.current_tables:  # noqa: F841
            x, y, shape, cap, num = (      # noqa: F841
                table["x"],
                table["y"],
                table["shape"],
                table["capacity"],
                table["number"],
            )
            if num in self.selected_tables:
                icon = self.icon_2 if cap == 2 else self.icon_4
                if icon:
                    marker_id = self.canvas.create_image(
                        x, y, anchor=tk.NW, image=icon, tags=("marker", f"marker_{num}")
                    )
                    self.marker_images[num] = marker_id

        # Обновляем метку
        self.selected_label.config(text=self.format_selected_tables())

    def remove_marker(self, table_num):
        if table_num in self.marker_images:
            self.canvas.delete(self.marker_images[table_num])
            del self.marker_images[table_num]

    def on_click(self, event):
        # Ищем, по какому столику кликнули
        clicked_table = None
        for table in self.current_tables:
            x, y, w, h = table["x"], table["y"], 80, 80  # примерный размер
            if x <= event.x <= x + w and y <= event.y <= y + h:
                clicked_table = table
                break

        if not clicked_table:
            return

        num = clicked_table["number"]

        if num in self.selected_tables:
            # Убираем маркер
            self.selected_tables.remove(num)
            self.remove_marker(num)
        else:
            # Добавляем маркер
            self.selected_tables.add(num)
            # Перерисовываем (чтобы добавить маркер)
            self.redraw()

        # Обновляем метку
        self.selected_label.config(text=self.format_selected_tables())


if __name__ == "__main__":
    root = tk.Tk()
    app = RestaurantHallMap(root)
    root.mainloop()
