"""Локальный интерфейс Tkinter: данные в мм отделены от масштаба и таймера."""
from pathlib import Path
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from lab5_model import (
    Configuration, ElectronSimulation, DEFAULT_SEED, CONDITIONAL_PROBABILITIES,
    finite_number, integer_number, measured_radii, ring_radii_mm, wavelength_a,
    voltage_experiment, structure_experiment, analyze_structure, write_csv,
)


ROOT = Path(__file__).resolve().parent


class LabApplication:
    def __init__(self, root, seed=DEFAULT_SEED):
        self.root = root
        self.root.title("Лабораторная 5 · Дифракция электронов")
        self.root.geometry("1320x920")
        self.root.minsize(1040, 760)
        self.root.configure(background="#f3f6fa")
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure(".", font=("Arial", 10), background="#f3f6fa")
        style.configure("TButton", padding=(10, 7))
        style.configure("Accent.TButton", background="#164f79", foreground="white")
        style.map("Accent.TButton", background=[("active", "#236b9e")])
        style.configure("TNotebook.Tab", padding=(18, 10))
        style.configure("Treeview", rowheight=25, background="white", fieldbackground="white")
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

        self.voltage = tk.StringVar(value="40")
        self.seed = tk.StringVar(value=str(seed))
        self.batch = tk.StringVar(value="1000")
        self.step = tk.StringVar(value="25")
        self.zoom = tk.StringVar(value="4")
        self.rate = tk.DoubleVar(value=1500)
        self.rate_text = tk.StringVar(value="1500 электронов/с")
        self.status = tk.StringVar(value="Новая серия. Нажмите «Пуск / добавить» или «Сразу».")
        self.counter = tk.StringVar()
        self.measurement = tk.StringVar(value="Щелчок по электронограмме измеряет радиус в мм.")
        self.runs = {}
        self.sim = ElectronSimulation(Configuration(40, seed))
        self.runs[40.0] = self.sim
        self.active = False
        self.target = 0
        self.timer = None
        self.credit = 0.0
        self.last_tick = time.monotonic()
        self.last_draw = 0.0
        self.voltage_result = None
        self.structure_result = None

        header = tk.Frame(root, background="#123851")
        header.pack(fill="x")
        tk.Label(header, text="Дифракция электронов", font=("Arial", 19, "bold"),
                 background="#123851", foreground="white", anchor="w").pack(fill="x", padx=20, pady=(14, 3))
        tk.Label(header, text="Один электрон — одна точка. Много электронов — закономерная картина.",
                 font=("Arial", 10), background="#123851", foreground="#cde5f5", anchor="w").pack(fill="x", padx=20, pady=(0, 13))
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=10)
        self.stat_tab, self.voltage_tab, self.structure_tab, self.help_tab = [ttk.Frame(self.notebook, padding=10) for _ in range(4)]
        for tab, title in zip((self.stat_tab, self.voltage_tab, self.structure_tab, self.help_tab),
                              ("1 · Накопление и статистика", "2 · Длина волны", "3 · Структура железа", "Как работать")):
            self.notebook.add(tab, text=title)
        self._build_statistics()
        self._build_voltage()
        self._build_structure()
        self._build_help()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.redraw()

    def guarded(self, action):
        """Ошибки ввода показываем пользователю, состояние серии не подменяем."""
        try:
            action()
        except (ValueError, OSError, TypeError) as error:
            messagebox.showerror("Проверьте данные", str(error), parent=self.root)

    def button(self, parent, text, action, accent=False):
        button = ttk.Button(parent, text=text, command=lambda: self.guarded(action),
                            style="Accent.TButton" if accent else "TButton")
        button.pack(side="left", padx=(0, 6))
        return button

    @staticmethod
    def entry(parent, label, variable, width=9):
        ttk.Label(parent, text=label).pack(side="left", padx=(0, 4))
        item = ttk.Entry(parent, textvariable=variable, width=width)
        item.pack(side="left", padx=(0, 12))
        return item

    @staticmethod
    def make_table(parent, headings, height=7):
        table = ttk.Treeview(parent, columns=[str(i) for i in range(len(headings))], show="headings", height=height)
        for i, heading in enumerate(headings):
            table.heading(str(i), text=heading)
            table.column(str(i), width=115, minwidth=70, anchor="center")
        return table

    @staticmethod
    def show_rows(table, rows):
        table.delete(*table.get_children())
        for row in rows:
            table.insert("", "end", values=row)

    def _build_statistics(self):
        self.stat_tab.columnconfigure(0, weight=1)
        self.stat_tab.rowconfigure(3, weight=1)
        controls = ttk.Frame(self.stat_tab)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Label(controls, text="V, кВ").pack(side="left", padx=(0, 4))
        self.voltage_box = ttk.Combobox(controls, textvariable=self.voltage, width=7,
                                       values=(30, 37, 40, 47, 60, 61, 83, 120))
        self.voltage_box.pack(side="left", padx=(0, 12))
        self.voltage_box.bind("<<ComboboxSelected>>", lambda event: self.guarded(self.select_voltage))
        self.voltage_box.bind("<Return>", lambda event: self.guarded(self.select_voltage))
        self.entry(controls, "Порция k₀", self.batch)
        self.entry(controls, "Seed", self.seed, 12)
        self.entry(controls, "Шаг графика", self.step, 5).bind("<Return>", lambda event: self.guarded(self.redraw))
        ttk.Label(controls, text="Масштаб ×").pack(side="left", padx=(0, 4))
        zoom_box = ttk.Combobox(controls, textvariable=self.zoom, values=(1, 2, 3, 4), state="readonly", width=4)
        zoom_box.pack(side="left")
        zoom_box.bind("<<ComboboxSelected>>", lambda event: self.guarded(self.redraw))

        actions = ttk.Frame(self.stat_tab)
        actions.grid(row=1, column=0, sticky="ew", pady=(0, 5))
        self.button(actions, "Пуск / добавить", self.start, True)
        self.button(actions, "Пауза", self.pause)
        self.button(actions, "Сразу", self.finish_now)
        self.button(actions, "Новая серия", self.reset)
        ttk.Scale(actions, from_=1, to=20000, variable=self.rate, command=self.rate_changed,
                  length=180).pack(side="left", padx=(12, 8))
        ttk.Label(actions, textvariable=self.rate_text).pack(side="left")
        ttk.Label(self.stat_tab, textvariable=self.counter, font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=4)

        self.stat_figure = Figure(figsize=(11, 4), dpi=100, layout="constrained")
        self.screen_ax, self.fraction_ax = self.stat_figure.subplots(1, 2, gridspec_kw={"width_ratios": [1.05, 1]})
        self.stat_canvas = FigureCanvasTkAgg(self.stat_figure, self.stat_tab)
        self.stat_canvas.get_tk_widget().configure(height=220)
        self.stat_canvas.get_tk_widget().grid(row=3, column=0, sticky="nsew")
        self.stat_canvas.mpl_connect("button_press_event", self.measure_click)
        self.stat_table = self.make_table(self.stat_tab, ("Кольцо", "Попаданий kⱼ", "kⱼ / k (без центра)", "kⱼ / k₀ (все электроны)"), 7)
        self.stat_table.grid(row=4, column=0, sticky="ew", pady=(6, 2))
        footer = ttk.Frame(self.stat_tab)
        footer.grid(row=5, column=0, sticky="ew")
        self.button(footer, "Сохранить серию", self.save_session)
        self.button(footer, "Открыть серию", self.load_session)
        self.button(footer, "CSV точек", self.export_points)
        self.button(footer, "PNG графиков", lambda: self.export_figure(self.stat_figure))
        ttk.Label(self.stat_tab, textvariable=self.measurement).grid(row=6, column=0, sticky="w", pady=(4, 0))
        ttk.Label(self.stat_tab, textvariable=self.status, foreground="#164f79", wraplength=1000).grid(row=7, column=0, sticky="w", pady=(3, 0))

    def _build_voltage(self):
        ttk.Label(self.voltage_tab, text="Серия при 30, 37, 47, 61, 83 и 120 кВ · L = 757 мм · масштаб ×4",
                  font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 8))
        ttk.Label(self.voltage_tab, text="X = 1 / √[V(1 + C₂V)]. Радиусы получаем из модельных попаданий, затем строим R₂(X) и R₃(X).").pack(anchor="w")
        bar = ttk.Frame(self.voltage_tab)
        bar.pack(fill="x", pady=12)
        self.voltage_count = tk.StringVar(value="20000")
        self.entry(bar, "Электронов на напряжение", self.voltage_count, 10)
        self.button(bar, "Выполнить серию", self.run_voltage, True)
        self.button(bar, "CSV результатов", self.export_voltage)
        self.button(bar, "PNG графика", lambda: self.export_figure(self.voltage_figure))
        self.voltage_table = self.make_table(self.voltage_tab, ("V, кВ", "λ, Å", "X, 1/√кВ", "R₂, мм", "R₃, мм"), 6)
        self.voltage_table.pack(fill="x")
        self.voltage_figure = Figure(figsize=(10, 4), dpi=100, layout="constrained")
        self.voltage_ax = self.voltage_figure.add_subplot(111)
        self.voltage_ax.set(xlabel="X, 1/√кВ", ylabel="R, мм")
        self.voltage_canvas = FigureCanvasTkAgg(self.voltage_figure, self.voltage_tab)
        self.voltage_canvas.get_tk_widget().pack(fill="both", expand=True, pady=8)
        self.voltage_note = tk.StringVar(value="Нажмите «Выполнить серию». Увеличение V уменьшает длину волны и радиусы колец.")
        ttk.Label(self.voltage_tab, textvariable=self.voltage_note, wraplength=1150).pack(anchor="w", pady=8)

    def _build_structure(self):
        ttk.Label(self.structure_tab, text="Железо · V = 30 кВ · L = 757 мм · a = 2,87 Å",
                  font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 8))
        ttk.Label(self.structure_tab, text="Введите радиусы по осям электронограммы в мм. Для кольца №4 задан порядок n = 2, для остальных n = 1.").pack(anchor="w")
        bar = ttk.Frame(self.structure_tab)
        bar.pack(fill="x", pady=12)
        self.radius_vars = [tk.StringVar() for _ in range(5)]
        for j, variable in enumerate(self.radius_vars, 1):
            self.entry(bar, f"R{j}, мм", variable, 8)
        actions = ttk.Frame(self.structure_tab)
        actions.pack(fill="x", pady=(0, 10))
        self.button(actions, "Измерить модельную серию", self.structure_demo, True)
        self.button(actions, "Вычислить d и индексы", self.calculate_structure)
        self.button(actions, "CSV результатов", self.export_structure)
        self.structure_table = self.make_table(self.structure_tab, ("Кольцо", "n", "R, мм", "d, Å", "S = (a/d)²", "Округл. S", "(h k l)"), 5)
        self.structure_table.pack(fill="x")
        self.structure_note = tk.StringVar(value="Можно измерить новую модельную серию из 30 000 электронов или ввести свои значения. Пустые поля не заменяются нулями.")
        ttk.Label(self.structure_tab, textvariable=self.structure_note, wraplength=1150).pack(anchor="w", pady=10)
        self.structure_figure = Figure(figsize=(10, 3.8), dpi=100, layout="constrained")
        self.structure_ax = self.structure_figure.add_subplot(111)
        self.structure_ax.set(xlabel="r, мм", ylabel="Число попаданий")
        self.structure_canvas = FigureCanvasTkAgg(self.structure_figure, self.structure_tab)
        self.structure_canvas.get_tk_widget().pack(fill="both", expand=True)

    def _build_help(self):
        text = tk.Text(self.help_tab, wrap="word", font=("Arial", 12), background="white",
                       foreground="#17384e", relief="flat", padx=22, pady=18)
        text.pack(fill="both", expand=True)
        text.insert("1.0", """КАК ВЫПОЛНИТЬ РАБОТУ

1. Накопление. Выберите 40 кВ и порцию 10, 100, 1000 или 10 000 электронов.
«Новая серия» очищает только выбранное напряжение; «Пуск / добавить» добавляет порцию.
Ползунок темпа действует сразу. «Пауза» сохраняет точки, «Сразу» завершает текущую порцию.
Повторите при 60 и 120 кВ. Напряжения имеют отдельные серии: их точки не смешиваются.

2. Статистика. Для упражнения 1.3 установите порцию 1000 и шаг графика 5–50.
На графике показаны k₁/k и k₂/k, где k — попадания в семь колец БЕЗ прямого пучка.
Пунктир — заданные вероятности модели. При k = 0 доля не определена и не рисуется.

3. Длина волны. На второй вкладке одна кнопка выполняет серию всех шести напряжений,
измеряет второе и третье кольца и строит графики. Увеличение ×4 не меняет радиусы в мм.

4. Структура. На третьей вкладке измерьте модельную серию или введите пять радиусов.
Рассчитываются d = nLλ/R, S = (a/d)² и все комбинации индексов для округлённого S.
У четвёртого кольца n = 2: плоскость (110) эквивалентна отражению (220) первого порядка.
Предупреждение при несогласованных данных не заменяет их автоматически «правильными».

МАСШТАБ И СОХРАНЕНИЕ

Оси электронограммы размечены в миллиметрах. Щелчок измеряет расстояние от центра.
Масштаб можно менять во время накопления: он не стирает данные и не меняет статистику.
PNG сохраняет вид; CSV — координаты; JSON — всю серию и состояние генератора.
После загрузки JSON можно точно продолжить ту же случайную последовательность.
Seed меняется кнопкой «Новая серия», а не при каждом добавлении.

ФИЗИЧЕСКИЙ СМЫСЛ

Электрон регистрируется целиком в одной точке. Волновая функция определяет
вероятности попаданий; при накоплении точек проявляются кольца.
Темп вылета меняет время ожидания, но не вероятности и радиусы.
Большое ускоряющее напряжение даёт больший импульс и меньшую длину волны.

Это учебная модель: центры колец рассчитаны по Брэггу и де Бройлю,
вероятности и радиальное размытие заданы явно. Реальный эксперимент она не заменяет.
Краткая теория и ответы на контрольные вопросы находятся в FAQ.md.
""")
        text.configure(state="disabled")

    def rate_changed(self, value):
        self.rate_text.set(f"{float(value):.0f} электронов/с")

    def select_voltage(self):
        voltage = finite_number(self.voltage.get(), "Напряжение, кВ", 1, 300)
        if voltage == self.sim.config.voltage_kv:
            return
        seed = integer_number(self.seed.get(), "Seed", 0, 2**32-1)
        self.pause(redraw=False)
        if voltage not in self.runs:
            self.runs[voltage] = ElectronSimulation(Configuration(voltage, seed))
        self.sim = self.runs[voltage]
        self.seed.set(str(self.sim.config.seed))
        self.target = self.sim.total
        self.status.set(f"Серия {voltage:g} кВ: сохранено {self.sim.total} точек. Другие напряжения доступны в списке.")
        self.redraw()

    def reset(self):
        voltage = finite_number(self.voltage.get(), "Напряжение, кВ", 1, 300)
        seed = integer_number(self.seed.get(), "Seed", 0, 2**32-1)
        self.pause(redraw=False)
        self.sim = ElectronSimulation(Configuration(voltage, seed))
        self.runs[voltage] = self.sim
        self.target = 0
        self.status.set(f"Новая серия {voltage:g} кВ, seed = {seed}.")
        self.redraw()

    def request_count(self):
        step = integer_number(self.step.get(), "Шаг статистики", 5, 50)
        count = integer_number(self.batch.get(), "Размер порции", 1, 100000)
        if self.sim.total+count > 1_000_000:
            raise ValueError("В одной серии поддерживается до 1 000 000 электронов")
        return count

    def start(self):
        self.select_voltage()
        count = self.request_count()
        if self.active:
            self.status.set("Серия уже идёт. Темп можно изменить ползунком; «Сразу» завершит порцию.")
            return
        if self.target <= self.sim.total:
            self.target = self.sim.total+count
        self.active = True
        self.credit = 0
        self.last_tick = time.monotonic()
        self.status.set("Накопление идёт. Масштаб и темп можно менять без потери точек.")
        self.timer = self.root.after(25, self.tick)

    def tick(self):
        self.timer = None
        if not self.active:
            return
        now = time.monotonic()
        self.credit += (now-self.last_tick)*self.rate.get()
        self.last_tick = now
        count = min(int(self.credit), self.target-self.sim.total, 5000)
        if count:
            self.sim.add(count)
            self.credit -= count
        if now-self.last_draw >= 0.15 or self.sim.total >= self.target:
            # Изменённый текст шага не должен останавливать и разрушать серию.
            try:
                self.redraw()
            except ValueError:
                self.step.set("25")
                self.redraw()
            self.last_draw = now
        if self.sim.total >= self.target:
            self.active = False
            self.status.set("Порция завершена. Точки и графики сохранены; можно добавить следующую.")
        else:
            self.timer = self.root.after(25, self.tick)

    def pause(self, redraw=True):
        self.active = False
        if self.timer is not None:
            self.root.after_cancel(self.timer)
            self.timer = None
        self.status.set("Пауза. Повторный пуск продолжит текущую порцию.")
        if redraw:
            self.redraw()

    def finish_now(self):
        self.select_voltage()
        count = self.request_count()
        pending = self.target-self.sim.total
        self.pause(redraw=False)
        self.sim.add(pending if pending > 0 else count)
        self.target = self.sim.total
        self.status.set("Порция завершена без анимации. Физическая последовательность та же.")
        self.redraw()

    def redraw(self):
        step = integer_number(self.step.get(), "Шаг статистики", 5, 50)
        zoom = integer_number(self.zoom.get(), "Масштаб", 1, 4)
        counts = self.sim.counts()
        k = int(counts[1:].sum())
        self.counter.set(f"V = {self.sim.config.voltage_kv:g} кВ    λ = {float(wavelength_a(self.sim.config.voltage_kv)):.5f} Å    "
                         f"Выпущено k₀ = {self.sim.total}    В кольцах k = {k}    Прямой пучок = {counts[0]}")
        ax = self.screen_ax
        ax.clear()
        ax.set_facecolor("#091825")
        if self.sim.total:
            ax.scatter(self.sim.points[:, 0], self.sim.points[:, 1], s=2, c="#99d7f5", alpha=0.8, linewidths=0, rasterized=True)
        extent = 320/zoom
        ax.set(xlim=(-extent, extent), ylim=(-extent, extent), xlabel="x, мм", ylabel="y, мм",
               title=f"Электронограмма · ×{zoom}", aspect="equal")
        ax.grid(alpha=0.12)
        self.fraction_ax.clear()
        history = self.sim.history(step)
        for j, color in enumerate(("#216797", "#b44936")):
            if len(history):
                self.fraction_ax.plot(history[:, 0], history[:, j+2], color=color, label=f"k{j+1}/k")
            self.fraction_ax.axhline(CONDITIONAL_PROBABILITIES[j], color=color, linestyle="--", alpha=0.7)
        self.fraction_ax.set(xlabel="Выпущено электронов k₀", ylabel="Доля среди попаданий в кольца",
                             title="Статистика · кольца 1 и 2", ylim=(0, 1), xlim=(0, max(1000, self.sim.total)))
        self.fraction_ax.grid(alpha=0.25)
        if len(history):
            self.fraction_ax.legend()
        self.show_rows(self.stat_table, [(j, int(counts[j]), f"{counts[j]/k:.4f}" if k else "—",
                                         f"{counts[j]/self.sim.total:.4f}" if self.sim.total else "—") for j in range(1, 8)])
        self.stat_canvas.draw_idle()

    def measure_click(self, event):
        if event.inaxes is self.screen_ax and event.xdata is not None and event.ydata is not None:
            radius = np.hypot(event.xdata, event.ydata)
            self.measurement.set(f"Измерено от центра: R = {radius:.2f} мм. Масштаб ×{self.zoom.get()} уже учтён осями.")

    def save_session(self):
        filename = filedialog.asksaveasfilename(parent=self.root, defaultextension=".json", filetypes=[("Серия", "*.json")])
        if filename:
            self.sim.save(filename)
            self.status.set(f"Серия и состояние генератора сохранены: {Path(filename).name}")

    def load_session(self):
        filename = filedialog.askopenfilename(parent=self.root, filetypes=[("Серия", "*.json")])
        if filename:
            simulation = ElectronSimulation.load(filename)  # Сначала проверяем, затем меняем UI.
            self.pause(redraw=False)
            self.sim = simulation
            self.runs[self.sim.config.voltage_kv] = self.sim
            self.voltage.set(f"{self.sim.config.voltage_kv:g}")
            self.seed.set(str(self.sim.config.seed))
            self.target = self.sim.total
            self.status.set("Серия загружена. Можно продолжать добавление с сохранённого состояния генератора.")
            self.redraw()

    def export_points(self):
        filename = filedialog.asksaveasfilename(parent=self.root, defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if filename:
            self.sim.export_csv(filename)

    def export_figure(self, figure):
        filename = filedialog.asksaveasfilename(parent=self.root, defaultextension=".png", filetypes=[("PNG", "*.png")])
        if filename:
            figure.savefig(filename, dpi=180)

    def run_voltage(self):
        count = integer_number(self.voltage_count.get(), "Электронов на напряжение", 100, 200000)
        seed = integer_number(self.seed.get(), "Seed", 0, 2**32-1)
        self.voltage_result = voltage_experiment(count, seed)
        rows = self.voltage_result["rows"]
        self.show_rows(self.voltage_table, [(r["voltage_kv"], f"{r['lambda_a']:.5f}", f"{r['X']:.6f}",
                                           f"{r['R2_mm']:.3f}", f"{r['R3_mm']:.3f}") for r in rows])
        self.voltage_ax.clear()
        x = np.array([r["X"] for r in rows])
        for fit, color in zip(self.voltage_result["fits"], ("#216797", "#b44936")):
            ring = fit["ring"]
            self.voltage_ax.errorbar(x, [r[f"R{ring}_mm"] for r in rows], yerr=[r[f"sem{ring}_mm"] for r in rows],
                                    fmt="o", color=color, label=f"Кольцо {ring}")
            line = np.array([0, x.max()*1.05])
            self.voltage_ax.plot(line, fit["slope"]*line+fit["intercept_mm"], color=color)
        self.voltage_ax.set(xlabel=r"$X=[V(1+C_2V)]^{-1/2}$, кВ$^{-1/2}$", ylabel="R, мм", xlim=(0, x.max()*1.05))
        self.voltage_ax.grid(alpha=0.25)
        self.voltage_ax.legend()
        self.voltage_canvas.draw_idle()
        self.voltage_note.set(";  ".join(f"Кольцо {r['ring']}: R = {r['slope']:.3f} X + {r['intercept_mm']:.4f}, R² = {r['R2']:.7f}"
                                         for r in self.voltage_result["fits"])+". Это проверка учебной модели, а не независимое доказательство закона.")

    def export_voltage(self):
        if self.voltage_result is None:
            raise ValueError("Сначала выполните серию напряжений")
        filename = filedialog.asksaveasfilename(parent=self.root, defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if filename:
            rows = self.voltage_result["rows"]
            write_csv(filename, list(rows[0]), [list(r.values()) for r in rows])

    def structure_demo(self):
        seed = integer_number(self.seed.get(), "Seed", 0, 2**32-1)
        result = structure_experiment(seed=seed)
        for variable, row in zip(self.radius_vars, result["rows"]):
            variable.set(f"{row['radius_mm']:.2f}")
        self.calculate_structure()
        # Для гистограммы воспроизводим ту же серию; это не меняет вкладку 1.
        sim = ElectronSimulation(Configuration(30, (seed+100) % 2**32))
        sim.add(result["count"])
        self.structure_ax.clear()
        radial = np.hypot(sim.points[:, 0], sim.points[:, 1])
        self.structure_ax.hist(radial[radial > 5], bins=400, range=(5, 75), color="#3177a1")
        self.structure_ax.set(xlabel="r, мм", ylabel="Число попаданий", title="Радиальный профиль модельной серии, 30 кВ")
        self.structure_canvas.draw_idle()
        self.structure_note.set("Радиусы измерены по координатам 30 000 модельных попаданий и записаны до 0,01 мм. "
                                "Кольцо 4: плоскости (110), n=2; эквивалентное отражение (220), n=1.")

    def calculate_structure(self):
        result = analyze_structure([variable.get() for variable in self.radius_vars])
        self.structure_result = result
        self.show_rows(self.structure_table, [(r["ring"], r["order"], f"{r['radius_mm']:.2f}", f"{r['spacing_a']:.4f}",
                                               f"{r['squared_sum']:.4f}", r["rounded_sum"],
                                               ", ".join("("+" ".join(map(str, hkl))+")" for hkl in r["allowed_bcc"]) or "нет") for r in result])
        warnings = [f"Кольцо {r['ring']}: {r['warning']}" for r in result if r["warning"]]
        self.structure_note.set("; ".join(warnings) if warnings else "Расчёт выполнен. Для кольца 4 учтён второй порядок; индексы найдены перебором целых чисел.")

    def export_structure(self):
        if self.structure_result is None:
            raise ValueError("Сначала вычислите межплоскостные расстояния")
        filename = filedialog.asksaveasfilename(parent=self.root, defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if filename:
            keys = ("ring", "order", "radius_mm", "spacing_a", "squared_sum", "rounded_sum", "allowed_bcc", "warning")
            write_csv(filename, keys, [[row[key] for key in keys] for row in self.structure_result])

    def close(self):
        self.pause(redraw=False)
        self.root.destroy()


def run(seed=DEFAULT_SEED):
    root = tk.Tk()
    LabApplication(root, seed)
    root.mainloop()
