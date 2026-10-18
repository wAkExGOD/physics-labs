from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve


OUTPUT_DIR = Path(__file__).resolve().parent
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
        "\u041d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d "
        "\u0448\u0440\u0438\u0444\u0442 \u0441 "
        "\u043f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u043e\u0439 "
        "\u043a\u0438\u0440\u0438\u043b\u043b\u0438\u0446\u044b "
        "\u0434\u043b\u044f \u043f\u043e\u0434\u043f\u0438\u0441\u0435\u0439 "
        "\u0433\u0440\u0430\u0444\u0438\u043a\u043e\u0432."
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
    plt.savefig(OUTPUT_DIR / name, dpi=180)
    plt.close()


def task1():
    a, b, c, d = 2.0, 3.0, 1.0, 3.14
    nodes = 50
    h = 1.0 / nodes
    x = np.arange(nodes) * h
    u = np.empty_like(x)
    u[0] = c
    u[1] = c + d * h
    for i in range(1, nodes - 1):
        u[i + 1] = 2.0 * u[i] - u[i - 1] + (b / a) * h**2

    exact = c + d * x + (b / (2.0 * a)) * x**2
    deviation = u - exact
    relative_error = np.abs(deviation) / np.abs(exact) * 100.0
    exact_first = d + (b / a) * x
    exact_second = np.full_like(x, b / a)

    plt.plot(
        x,
        u,
        label="\u041c\u0435\u0442\u043e\u0434 \u043a\u043e\u043d\u0435\u0447\u043d\u044b\u0445 "
        "\u0440\u0430\u0437\u043d\u043e\u0441\u0442\u0435\u0439",
        linewidth=2,
    )
    plt.plot(
        x,
        exact,
        "--",
        label="\u0410\u043d\u0430\u043b\u0438\u0442\u0438\u0447\u0435\u0441\u043a\u043e\u0435 "
        "\u0440\u0435\u0448\u0435\u043d\u0438\u0435",
        linewidth=1.5,
    )
    plt.xlabel("x")
    plt.ylabel("U(x)")
    plt.title("\u0417\u0430\u0434\u0430\u043d\u0438\u0435 1: \u0440\u0435\u0448\u0435\u043d\u0438\u0435")
    plt.legend()
    save_figure("task1_solution.png")

    fig, axes = plt.subplots(2, 1, sharex=True)
    axes[0].plot(x, np.abs(deviation))
    axes[0].set_ylabel(r"$|U_{\mathrm{num}}-U_{\mathrm{exact}}|$")
    axes[0].set_title(
        "\u0417\u0430\u0434\u0430\u043d\u0438\u0435 1: "
        "\u043f\u043e\u0433\u0440\u0435\u0448\u043d\u043e\u0441\u0442\u044c "
        "\u0447\u0438\u0441\u043b\u0435\u043d\u043d\u043e\u0433\u043e "
        "\u0440\u0435\u0448\u0435\u043d\u0438\u044f"
    )
    axes[1].plot(x, relative_error)
    axes[1].set_xlabel("x")
    axes[1].set_ylabel(
        "\u041e\u0442\u043d\u043e\u0441\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f "
        "\u043f\u043e\u0433\u0440\u0435\u0448\u043d\u043e\u0441\u0442\u044c, %"
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
        "\u0417\u0430\u0434\u0430\u043d\u0438\u0435 1: "
        "\u043f\u0440\u043e\u0438\u0437\u0432\u043e\u0434\u043d\u044b\u0435 "
        "\u0440\u0435\u0448\u0435\u043d\u0438\u044f"
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
    mass = 0.5
    nodes = 80
    h = 1.0 / nodes
    t = np.arange(nodes) * h
    position = np.empty_like(t)
    position[0] = 1.0
    position[1] = position[0] + 0.5 * h

    mass_over_h2 = mass / h**2
    for i in range(1, nodes - 1):
        position[i + 1] = (
            t[i] ** 2
            + (2.0 * mass_over_h2 + 1.0 / h) * position[i]
            - mass_over_h2 * position[i - 1]
        ) / (mass_over_h2 + 1.0 / h)

    analytic_position = 1.0 + t**3 / 3.0 - t**2 / 2.0 + t / 2.0
    analytic_velocity = t**2 - t + 0.5
    analytic_acceleration = 2.0 * t - 1.0

    deviation = position - analytic_position
    relative_error = np.abs(deviation) / np.abs(analytic_position) * 100.0
    velocity = np.gradient(position, h, edge_order=2)
    acceleration = (t**2 - velocity) / mass

    plt.plot(
        t,
        position,
        label="\u041c\u0435\u0442\u043e\u0434 \u043a\u043e\u043d\u0435\u0447\u043d\u044b\u0445 "
        "\u0440\u0430\u0437\u043d\u043e\u0441\u0442\u0435\u0439",
        linewidth=2,
    )
    plt.plot(
        t,
        analytic_position,
        "--",
        label="\u0410\u043d\u0430\u043b\u0438\u0442\u0438\u0447\u0435\u0441\u043a\u043e\u0435 "
        "\u0440\u0435\u0448\u0435\u043d\u0438\u0435",
    )
    plt.xlabel("t")
    plt.ylabel("x(t)")
    plt.title("\u0417\u0430\u0434\u0430\u043d\u0438\u0435 2: \u043a\u043e\u043e\u0440\u0434\u0438\u043d\u0430\u0442\u0430")
    plt.legend()
    save_figure("task2_solution.png")

    fig, axes = plt.subplots(2, 1, sharex=True)
    axes[0].plot(t, np.abs(deviation))
    axes[0].set_ylabel(r"$|x_{\mathrm{num}}-x_{\mathrm{exact}}|$")
    axes[0].set_title(
        "\u0417\u0430\u0434\u0430\u043d\u0438\u0435 2: "
        "\u043f\u043e\u0433\u0440\u0435\u0448\u043d\u043e\u0441\u0442\u044c "
        "\u0447\u0438\u0441\u043b\u0435\u043d\u043d\u043e\u0433\u043e "
        "\u0440\u0435\u0448\u0435\u043d\u0438\u044f"
    )
    axes[1].plot(t, relative_error)
    axes[1].set_xlabel("t")
    axes[1].set_ylabel(
        "\u041e\u0442\u043d\u043e\u0441\u0438\u0442\u0435\u043b\u044c\u043d\u0430\u044f "
        "\u043f\u043e\u0433\u0440\u0435\u0448\u043d\u043e\u0441\u0442\u044c, %"
    )
    save_figure("task2_error.png")

    fig, axes = plt.subplots(2, 1, sharex=True)
    axes[0].plot(
        t,
        velocity,
        label="\u041c\u0435\u0442\u043e\u0434 \u043a\u043e\u043d\u0435\u0447\u043d\u044b\u0445 "
        "\u0440\u0430\u0437\u043d\u043e\u0441\u0442\u0435\u0439",
    )
    axes[0].plot(
        t,
        analytic_velocity,
        "--",
        label="\u0410\u043d\u0430\u043b\u0438\u0442\u0438\u0447\u0435\u0441\u043a\u0430\u044f "
        "\u043f\u0440\u043e\u0438\u0437\u0432\u043e\u0434\u043d\u0430\u044f",
    )
    axes[0].set_ylabel("x'(t)")
    axes[0].legend()
    axes[1].plot(
        t,
        acceleration,
        label="\u041c\u0435\u0442\u043e\u0434 \u043a\u043e\u043d\u0435\u0447\u043d\u044b\u0445 "
        "\u0440\u0430\u0437\u043d\u043e\u0441\u0442\u0435\u0439",
    )
    axes[1].plot(
        t,
        analytic_acceleration,
        "--",
        label="\u041f\u043e \u0434\u0438\u0444\u0444\u0435\u0440\u0435\u043d\u0446\u0438\u0430\u043b\u044c\u043d\u043e\u043c\u0443 "
        "\u0443\u0440\u0430\u0432\u043d\u0435\u043d\u0438\u044e",
    )
    axes[1].set_xlabel("t")
    axes[1].set_ylabel("x''(t)")
    axes[1].legend()
    fig.suptitle(
        "\u0417\u0430\u0434\u0430\u043d\u0438\u0435 2: "
        "\u0441\u043a\u043e\u0440\u043e\u0441\u0442\u044c \u0438 "
        "\u0443\u0441\u043a\u043e\u0440\u0435\u043d\u0438\u0435"
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
    intervals = 40
    h = 1.0 / intervals
    coordinates = np.linspace(0.0, 1.0, intervals + 1)
    count = intervals**2
    matrix = lil_matrix((count, count), dtype=float)
    rhs = np.zeros(count, dtype=float)

    def index(i, j):
        return (j - 1) * intervals + (i - 1)

    def add_term(row, i, j, coefficient):
        if i == 0 or j == 0:
            rhs[row] -= coefficient
        else:
            matrix[row, index(i, j)] += coefficient

    for j in range(1, intervals + 1):
        for i in range(1, intervals + 1):
            row = index(i, j)
            if i < intervals and j < intervals:
                scale = 1.0 / h**2
                add_term(row, i, j, -4.0 * scale)
                add_term(row, i - 1, j, scale)
                add_term(row, i + 1, j, scale)
                add_term(row, i, j - 1, scale)
                add_term(row, i, j + 1, scale)
                rhs[row] += 1.0
            elif i == intervals and j == intervals:
                add_term(row, i, j, 1.0)
                add_term(row, i - 1, j, -0.5)
                add_term(row, i, j - 1, -0.5)
                rhs[row] += 0.5 * h
            elif i == intervals:
                add_term(row, i, j, 1.0)
                add_term(row, i - 1, j, -1.0)
                rhs[row] += 0.5 * h
            else:
                add_term(row, i, j, 1.0)
                add_term(row, i, j - 1, -1.0)
                rhs[row] += 0.5 * h

    values = spsolve(matrix.tocsr(), rhs)
    solution = np.ones((intervals + 1, intervals + 1), dtype=float)
    for j in range(1, intervals + 1):
        for i in range(1, intervals + 1):
            solution[j, i] = values[index(i, j)]

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
        "\u0417\u0430\u0434\u0430\u043d\u0438\u0435 3: "
        "\u0447\u0438\u0441\u043b\u0435\u043d\u043d\u043e\u0435 "
        "\u0440\u0435\u0448\u0435\u043d\u0438\u0435 \u043c\u0435\u0442\u043e\u0434\u043e\u043c "
        "\u043a\u043e\u043d\u0435\u0447\u043d\u044b\u0445 \u0440\u0430\u0437\u043d\u043e\u0441\u0442\u0435\u0439"
    )
    fig.colorbar(surface, ax=ax, shrink=0.65, label="U(x, y)")
    save_figure("task3_surface.png")

    plt.contourf(x_grid, y_grid, solution, levels=20, cmap="viridis")
    plt.colorbar(label="U(x, y)")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title(
        "\u0417\u0430\u0434\u0430\u043d\u0438\u0435 3: "
        "\u043b\u0438\u043d\u0438\u0438 \u0443\u0440\u043e\u0432\u043d\u044f "
        "\u0440\u0435\u0448\u0435\u043d\u0438\u044f"
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
    task1()
    task2()
    task3()
