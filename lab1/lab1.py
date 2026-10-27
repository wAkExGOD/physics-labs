# Лаба 1: заменяем производные конечными разностями и проверяем решение.
# task1 и task2 — последовательный расчёт по двум начальным значениям;
# task3 — одновременное решение системы уравнений для двумерной сетки.
from pathlib import Path

import matplotlib

# Agg сохраняет рисунки без графического окна: удобно для повторного запуска.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve


# Пути зависят от расположения скрипта, а не от текущего каталога терминала.
OUTPUT_DIR = Path(__file__).resolve().parent
# Выбираем установленный шрифт с кириллицей для подписей рисунков.
available_fonts = {font.name for font in font_manager.fontManager.ttflist}
russian_font = next(
    (
        name
        for name in ("Times New Roman", "DejaVu Sans", "Arial", "Liberation Sans")
        if name in available_fonts
    ),
    None,
)
if russian_font is None:
    raise RuntimeError(
        "Не найден "
        "шрифт с "
        "поддержкой "
        "кириллицы "
        "для подписей "
        "графиков."
    )
plt.rcParams.update(
    {
        "figure.figsize": (8, 4.8),
        "font.size": 10,
        "font.family": russian_font,
        "axes.unicode_minus": False,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "figure.constrained_layout.use": True,
    }
)


def save_figure(name):
    # Текущий рисунок записываем в PNG; close освобождает память перед следующим.
    plt.savefig(OUTPUT_DIR / name, dpi=180)
    plt.close()


def task1():
    # A*U''=B; U(0)=C; U'(0)=D. a,b,c,d соответствуют этим константам.
    a, b, c, d = 2.0, 3.0, 1.0, 3.14
    nodes = 50
    h = 1.0 / nodes
    # Как в примере PDF: 50 значений 0,...,49, поэтому последний x=0.98.
    # Это не сетка из 50 интервалов с включённым правым концом x=1.
    x = np.arange(nodes) * h
    u = np.empty_like(x)
    u[0] = c
    # (U1-U0)/h=D — односторонняя аппроксимация начальной производной.
    # В точном U(h) ещё есть (B/2A)*h²: её отсутствие порождает ошибку.
    u[1] = c + d * h
    # Центральная вторая разность: (U[i+1]-2U[i]+U[i-1])/h²=B/A.
    for i in range(1, nodes - 1):
        u[i + 1] = 2.0 * u[i] - u[i - 1] + (b / a) * h**2

    # Дважды интегрируем U''=B/A и подставляем начальные условия.
    exact = c + d * x + (b / (2.0 * a)) * x**2
    # Отклонение знаковое; модуль нужен для абсолютной и относительной ошибок.
    deviation = u - exact
    relative_error = np.abs(deviation) / np.abs(exact) * 100.0
    # Здесь графики производных построены по точным формулам, не через gradient.
    exact_first = d + (b / a) * x
    exact_second = np.full_like(x, b / a)

    plt.plot(
        x,
        u,
        label="Метод конечных "
        "разностей",
        linewidth=2,
    )
    plt.plot(
        x,
        exact,
        "--",
        label="Аналитическое "
        "решение",
        linewidth=1.5,
    )
    plt.xlabel("x")
    plt.ylabel("U(x)")
    plt.title("Задание 1: решение")
    plt.legend()
    save_figure("task1_solution.png")

    fig, axes = plt.subplots(2, 1, sharex=True)
    axes[0].plot(x, np.abs(deviation))
    axes[0].set_ylabel(r"$|U_{\mathrm{num}}-U_{\mathrm{exact}}|$")
    axes[0].set_title(
        "Задание 1: "
        "погрешность "
        "численного "
        "решения"
    )
    axes[1].plot(x, relative_error)
    axes[1].set_xlabel("x")
    axes[1].set_ylabel(
        "Относительная "
        "погрешность, %"
    )
    save_figure("task1_error.png")

    fig, axes = plt.subplots(2, 1, sharex=True)
    axes[0].plot(x, exact_first, label="U'(x)")
    axes[0].set_ylabel("U'(x)")
    axes[0].legend()
    axes[1].plot(x, exact_second, label="U''(x)", color="tab:orange")
    axes[1].set_xlabel("x")
    axes[1].set_ylabel("U''(x)")
    axes[1].legend()
    fig.suptitle(
        "Задание 1: "
        "производные "
        "решения"
    )
    save_figure("task1_derivatives.png")

    print(
        "TASK1",
        f"nodes={nodes}",
        f"h={h:.6g}",
        f"max_abs_error={np.max(np.abs(deviation)):.10g}",
        f"max_relative_error_percent={np.max(relative_error):.10g}",
        f"U1={u[1]:.10g}",
        f"U_end={u[-1]:.10g}",
        f"x_end={x[-1]:.10g}",
    )


def task2():
    # ВАЖНО: считаем m*x''+x'=t². В PDF напечатано f(x)=x² — иная,
    # нелинейная модель. Здесь сохранена постановка уже выполненного отчёта;
    # различие пояснено в FAQ.md, раздел о задании 2.
    mass = 0.5
    nodes = 80
    h = 1.0 / nodes
    # 80 значений: 0,...,0.9875. Правый конец t=1 в эту сетку не входит.
    t = np.arange(nodes) * h
    position = np.empty_like(t)
    position[0] = 1.0
    # Начальная скорость 0.5 задаёт второй узел через прямую разность.
    position[1] = position[0] + 0.5 * h

    # m*(x[i+1]-2*x[i]+x[i-1])/h² + (x[i+1]-x[i])/h = t[i]².
    # Собираем члены с x[i+1] и выражаем следующее положение явно.
    mass_over_h2 = mass / h**2
    for i in range(1, nodes - 1):
        position[i + 1] = (
            t[i] ** 2
            + (2.0 * mass_over_h2 + 1.0 / h) * position[i]
            - mass_over_h2 * position[i - 1]
        ) / (mass_over_h2 + 1.0 / h)

    # При m=0.5 сначала решаем 0.5*v'+v=t²; v(0)=0.5.
    # Получаем v=t²-t+0.5, затем интегрируем с x(0)=1.
    analytic_position = 1.0 + t**3 / 3.0 - t**2 / 2.0 + t / 2.0
    analytic_velocity = t**2 - t + 0.5
    analytic_acceleration = 2.0 * t - 1.0

    deviation = position - analytic_position
    relative_error = np.abs(deviation) / np.abs(analytic_position) * 100.0
    # gradient дифференцирует численную координату: в середине центрально,
    # на концах односторонне со вторым порядком точности (edge_order=2).
    velocity = np.gradient(position, h, edge_order=2)
    # Ускорение берём из исходного уравнения, чтобы не дифференцировать дважды.
    acceleration = (t**2 - velocity) / mass

    plt.plot(
        t,
        position,
        label="Метод конечных "
        "разностей",
        linewidth=2,
    )
    plt.plot(
        t,
        analytic_position,
        "--",
        label="Аналитическое "
        "решение",
    )
    plt.xlabel("t")
    plt.ylabel("x(t)")
    plt.title("Задание 2: координата")
    plt.legend()
    save_figure("task2_solution.png")

    fig, axes = plt.subplots(2, 1, sharex=True)
    axes[0].plot(t, np.abs(deviation))
    axes[0].set_ylabel(r"$|x_{\mathrm{num}}-x_{\mathrm{exact}}|$")
    axes[0].set_title(
        "Задание 2: "
        "погрешность "
        "численного "
        "решения"
    )
    axes[1].plot(t, relative_error)
    axes[1].set_xlabel("t")
    axes[1].set_ylabel(
        "Относительная "
        "погрешность, %"
    )
    save_figure("task2_error.png")

    fig, axes = plt.subplots(2, 1, sharex=True)
    axes[0].plot(
        t,
        velocity,
        label="Метод конечных "
        "разностей",
    )
    axes[0].plot(
        t,
        analytic_velocity,
        "--",
        label="Аналитическая "
        "производная",
    )
    axes[0].set_ylabel("x'(t)")
    axes[0].legend()
    axes[1].plot(
        t,
        acceleration,
        label="Метод конечных "
        "разностей",
    )
    axes[1].plot(
        t,
        analytic_acceleration,
        "--",
        label="По дифференциальному "
        "уравнению",
    )
    axes[1].set_xlabel("t")
    axes[1].set_ylabel("x''(t)")
    axes[1].legend()
    fig.suptitle(
        "Задание 2: "
        "скорость и "
        "ускорение"
    )
    save_figure("task2_derivatives.png")

    print(
        "TASK2",
        f"nodes={nodes}",
        f"h={h:.6g}",
        f"max_abs_error={np.max(np.abs(deviation)):.10g}",
        f"max_relative_error_percent={np.max(relative_error):.10g}",
        f"x_end={position[-1]:.10g}",
        f"x_exact_end={analytic_position[-1]:.10g}",
        f"t_end={t[-1]:.10g}",
        f"v_end={velocity[-1]:.10g}",
        f"a_end={acceleration[-1]:.10g}",
        f"min_velocity={np.min(velocity):.10g}",
        f"min_acceleration={np.min(acceleration):.10g}",
        f"max_acceleration={np.max(acceleration):.10g}",
    )


def task3():
    # Решаем U_xx+U_yy=1 на квадрате; снизу и слева U=1 (Дирихле).
    # Справа U_x=0.5, сверху U_y=0.5 (Нейман). Верхняя производная
    # в PDF обозначена U_x: здесь принята нормальная производная U_y,
    # как в готовом отчёте; это уточнение постановки, а не тождественная запись.
    intervals = 40
    h = 1.0 / intervals
    coordinates = np.linspace(0.0, 1.0, intervals + 1)
    # Сетка 41x41, но 1600 неизвестных: i,j=1,...,40.
    # Левые и нижние узлы известны заранее и в вектор неизвестных не входят.
    count = intervals**2
    # LIL удобно постепенно заполнять; почти все элементы матрицы равны нулю.
    matrix = lil_matrix((count, count), dtype=float)
    rhs = np.zeros(count, dtype=float)

    def index(i, j):
        # Перевод двумерного узла в номер элемента одномерного вектора.
        return (j - 1) * intervals + (i - 1)

    def add_term(row, i, j, coefficient):
        # Записываем коэффициент при U[i,j] в нужное уравнение системы.
        if i == 0 or j == 0:
            # Известное U=1 переносим вправо: rhs -= coefficient*1.
            rhs[row] -= coefficient
        else:
            matrix[row, index(i, j)] += coefficient

    for j in range(1, intervals + 1):
        for i in range(1, intervals + 1):
            row = index(i, j)
            if i < intervals and j < intervals:
                # Внутренний узел: центр -4/h² и четыре соседа +1/h².
                scale = 1.0 / h**2
                add_term(row, i, j, -4.0 * scale)
                add_term(row, i - 1, j, scale)
                add_term(row, i + 1, j, scale)
                add_term(row, i, j - 1, scale)
                add_term(row, i, j + 1, scale)
                rhs[row] += 1.0
            elif i == intervals and j == intervals:
                # В верхнем правом углу усредняем два уравнения Неймана:
                # U[N,N] - (U[N-1,N]+U[N,N-1])/2 = 0.5*h.
                add_term(row, i, j, 1.0)
                add_term(row, i - 1, j, -0.5)
                add_term(row, i, j - 1, -0.5)
                rhs[row] += 0.5 * h
            elif i == intervals:
                # Правая сторона: (U[N,j]-U[N-1,j])/h=0.5.
                add_term(row, i, j, 1.0)
                add_term(row, i - 1, j, -1.0)
                rhs[row] += 0.5 * h
            else:
                # Верхняя сторона: (U[i,N]-U[i,N-1])/h=0.5.
                add_term(row, i, j, 1.0)
                add_term(row, i, j - 1, -1.0)
                rhs[row] += 0.5 * h

    # CSR — формат для вычислений; spsolve решает A*u=rhs без плотной матрицы.
    values = spsolve(matrix.tocsr(), rhs)
    # Восстанавливаем поле; solution[j,i] означает U(x_i,y_j).
    solution = np.ones((intervals + 1, intervals + 1), dtype=float)
    for j in range(1, intervals + 1):
        for i in range(1, intervals + 1):
            solution[j, i] = values[index(i, j)]

    # meshgrid создаёт массивы координат для поверхности и линий уровня.
    x_grid, y_grid = np.meshgrid(coordinates, coordinates)
    fig = plt.figure(figsize=(8, 5.4))
    ax = fig.add_subplot(111, projection="3d")
    surface = ax.plot_surface(
        x_grid, y_grid, solution, cmap="viridis", edgecolor="none"
    )
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("U(x, y)")
    ax.set_title(
        "Задание 3: "
        "численное "
        "решение методом "
        "конечных разностей"
    )
    fig.colorbar(surface, ax=ax, shrink=0.65, label="U(x, y)")
    save_figure("task3_surface.png")

    plt.contourf(x_grid, y_grid, solution, levels=20, cmap="viridis")
    plt.colorbar(label="U(x, y)")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title(
        "Задание 3: "
        "линии уровня "
        "решения"
    )
    save_figure("task3_contour.png")

    print(
        "TASK3",
        f"h={h:.6g}",
        f"min={np.min(solution):.10g}",
        f"max={np.max(solution):.10g}",
        f"center={solution[intervals // 2, intervals // 2]:.10g}",
        f"top_right={solution[-1, -1]:.10g}",
        f"top_right_x_derivative={(solution[-1, -1] - solution[-1, -2]) / h:.10g}",
        f"top_right_y_derivative={(solution[-1, -1] - solution[-2, -1]) / h:.10g}",
    )


if __name__ == "__main__":
    # При прямом запуске выполняем все задания; при import расчёт не запускается.
    task1()
    task2()
    task3()
