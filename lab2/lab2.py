"""Обработка координат броуновской частицы: python lab2.py.

Зависимости: numpy, matplotlib, xlrd (см. requirements.txt).
Все пути отсчитываются от файла скрипта; исходный Excel не изменяется.
"""

from pathlib import Path
import csv
import json
import re

import matplotlib

# Сохраняем графики в файлы без открытия окон.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xlrd


# Все входные/выходные пути задаём относительно скрипта, а не терминала.
ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "tablitsa_pyltsa_lr.xls"
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
# Лаг k — сколько шагов записи между сравниваемыми положениями; t=k*tau.
MAX_LAG = 9


def read_coordinates(path):
    """Читаем первый лист; пустые пары пропускаем, неполные отвергаем."""
    sheet = xlrd.open_workbook(str(path)).sheet_by_index(0)
    # C1 содержит 'dt=4 s.': регулярное выражение извлекает шаг в секундах.
    match = re.fullmatch(r"dt\s*=\s*([\d.]+)\s*s\.?", str(sheet.cell_value(0, 2)))
    if match is None or float(match[1]) <= 0:
        raise ValueError("Не распознан положительный шаг времени в ячейке C1")
    tau = float(match[1])
    rows, skipped = [], []
    # Первые две строки — заголовки; фактические координаты начинаются с третьей.
    for row in range(2, sheet.nrows):
        number, x, y = sheet.row_values(row)[:3]
        if x == "" and y == "":
            # Пустые позиции 98–100 не превращаем в точки (0,0).
            skipped.append(row + 1)
            continue
        if any(not isinstance(v, (int, float)) for v in (number, x, y)):
            raise ValueError(f"Неполная или нечисловая запись: строка Excel {row + 1}")
        rows.append((number, x, y))
    # Столбцы data: номер, x, y. Для наших данных остаётся 97 полных строк.
    data = np.asarray(rows, dtype=float)
    if len(data) <= MAX_LAG or not np.isfinite(data).all():
        raise ValueError("Недостаточно координат или имеются нечисловые значения")
    # Пропуск внутри записи нарушил бы соответствие лага физическому времени.
    if not np.array_equal(data[:, 0], np.arange(1, len(data) + 1)):
        raise ValueError("Номера измерений должны идти подряд, начиная с 1")
    # xy имеет форму (97,2): каждая строка — положение одной частицы.
    return data[:, 1:], tau, skipped


def calculate_msd(xy, tau):
    """Все перекрывающиеся пары (i, i+k), как в таблице методички."""
    summary, pairs = [], []
    for lag in range(1, MAX_LAG + 1):
        # xy[k:] содержит позиции k,...,n-1; xy[:-k] — 0,...,n-k-1.
        # Их разность даёт все n-k векторов смещения через одинаковое время.
        delta = xy[lag:] - xy[:-lag]
        # axis=1 складывает по двум координатам: dx²+dy² для каждой пары.
        squared = np.sum(delta**2, axis=1)
        # Среднее по парам, а не квадрат среднего вектора и не длина пути.
        summary.append((lag, lag * tau, len(squared), squared.sum(), squared.mean()))
        for i, (dx, dy) in enumerate(delta):
            # Для ручной проверки сохраняем номера пары с единицы,
            # dx,dy, модуль смещения hypot(dx,dy) и его квадрат.
            pairs.append(
                (
                    lag,
                    lag * tau,
                    i + 1,
                    i + lag + 1,
                    dx,
                    dy,
                    np.hypot(dx, dy),
                    squared[i],
                )
            )
    return np.asarray(summary), pairs


def fit_msd(t, msd):
    """Обычный МНК с константой и физическая модель через начало координат.

    R² — центрированный показатель только для модели с константой.
    Ошибки параметров не вычисляем: лаговые оценки MSD коррелированы.
    """
    # Столбцы [t,1] задают M=a*t+c; lstsq находит минимум суммы квадратов.
    # [0] выбирает вектор коэффициентов из нескольких результатов lstsq.
    slope, intercept = np.linalg.lstsq(
        np.column_stack((t, np.ones_like(t))), msd, rcond=None
    )[0]
    # Для M=A*t без константы решение МНК: A=sum(t*M)/sum(t²).
    slope_zero = np.dot(t, msd) / np.dot(t, t)
    # Остаток — экспериментальное среднее минус значение соответствующей модели.
    residual = msd - (slope * t + intercept)
    residual_zero = msd - slope_zero * t
    # Наклон делим на 4: камера наблюдает две координаты, M=4*D*t.
    # RMSE имеет единицы MSD (пиксель²), но не является ошибкой D.
    return {
        "slope_px2_s": float(slope),
        "intercept_px2": float(intercept),
        "D_free_px2_s": float(slope / 4),
        "R2_free": float(
            1 - np.dot(residual, residual) / np.sum((msd - msd.mean()) ** 2)
        ),
        "rmse_free_px2": float(np.sqrt(np.mean(residual**2))),
        "slope_zero_px2_s": float(slope_zero),
        "D_zero_px2_s": float(slope_zero / 4),
        "rmse_zero_px2": float(np.sqrt(np.mean(residual_zero**2))),
        "max_relative_residual_zero_percent": float(
            100 * np.max(np.abs(residual_zero) / msd)
        ),
    }


def write_csv(name, header, rows):
    with (RESULTS / name).open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


def tex_number(value, decimals=2):
    # {,} не позволяет LaTeX добавить математический пробел после запятой.
    return f"{value:.{decimals}f}".replace(".", "{,}")


def export_results(xy, tau, skipped, summary, pairs, fit):
    # CSV — данные для проверки; JSON — параметры; .tex — вставки в отчёт.
    # Обновление этих .tex избавляет от ручного переноса и округления результатов.
    write_csv(
        "coordinates.csv",
        ["i", "time_s", "x_px", "y_px"],
        [(i + 1, i * tau, *point) for i, point in enumerate(xy)],
    )
    write_csv(
        "displacements.csv",
        ["k", "lag_s", "i", "j", "dx_px", "dy_px", "ds_px", "ds2_px2"],
        pairs,
    )
    write_csv(
        "msd.csv", ["k", "lag_s", "pair_count", "sum_ds2_px2", "msd_px2"], summary
    )
    diagnostic = {
        "source": SOURCE.name,
        "sheet": "Часица 1",
        "n": len(xy),
        "tau_s": tau,
        "duration_s": (len(xy) - 1) * tau,
        "skipped_excel_rows": skipped,
        "pair_count_total": len(pairs),
        # Это смещение между концами записи / время, а не доказанный дрейф.
        "endpoint_velocity_px_s": ((xy[-1] - xy[0]) / ((len(xy) - 1) * tau)).tolist(),
        **fit,
    }
    (RESULTS / "fit.json").write_text(
        json.dumps(diagnostic, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    commands = {
        "NPoints": str(len(xy)),
        "TimeStep": tex_number(tau, 0),
        "Duration": tex_number((len(xy) - 1) * tau, 0),
        "SlopeFree": tex_number(fit["slope_px2_s"]),
        "InterceptFree": tex_number(fit["intercept_px2"]),
        "DiffusionFree": tex_number(fit["D_free_px2_s"]),
        "RSquared": tex_number(fit["R2_free"], 4),
        "SlopeZero": tex_number(fit["slope_zero_px2_s"]),
        "DiffusionZero": tex_number(fit["D_zero_px2_s"]),
        "RmseFree": tex_number(fit["rmse_free_px2"]),
        "RmseZero": tex_number(fit["rmse_zero_px2"]),
        "MaxRelativeResidual": tex_number(fit["max_relative_residual_zero_percent"], 1),
    }
    (RESULTS / "values.tex").write_text(
        "% Generated by lab2.py; do not edit.\n"
        + "\n".join(
            rf"\newcommand{{\{key}}}{{{value}}}" for key, value in commands.items()
        )
        + "\n",
        encoding="utf-8",
    )
    table = [
        f"{int(k)} & {int(t)} & {int(count)} & {int(total)} & {tex_number(mean)} "
        + r"\\"
        for k, t, count, total, mean in summary
    ]
    (RESULTS / "msd_rows.tex").write_text("\n".join(table) + "\n", encoding="utf-8")


def make_figures(xy, summary, fit):
    # Первый рисунок — сама траектория; второй — усреднённые квадраты смещений.
    plt.rcParams.update(
        {
            "font.family": "Times New Roman",
            "font.size": 12,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "axes.unicode_minus": False,
        }
    )
    fig, ax = plt.subplots(figsize=(7.2, 5.2), layout="constrained")
    ax.plot(xy[:, 0], xy[:, 1], color="#346b91", linewidth=0.9, alpha=0.85)
    ax.scatter(xy[:, 0], xy[:, 1], c=np.arange(len(xy)), cmap="viridis", s=13)
    ax.scatter(
        *xy[0], marker="o", s=80, facecolors="none", edgecolors="black", label="Начало"
    )
    ax.scatter(*xy[-1], marker="x", s=65, color="#b53232", label="Конец")
    ax.set(xlabel="x, пиксель", ylabel="y, пиксель", aspect="equal")
    ax.invert_yaxis()  # Экранные координаты исходной таблицы: y растёт вниз.
    ax.legend()
    fig.savefig(FIGURES / "trajectory.pdf")
    fig.savefig(FIGURES / "trajectory.png", dpi=180)
    plt.close(fig)

    # Столбцы summary: k, t, число пар, сумма квадратов, средний квадрат.
    t, msd = summary[:, 1], summary[:, 4]
    line_t = np.linspace(0, t[-1], 200)
    fig, axes = plt.subplots(
        2,
        1,
        figsize=(7.2, 6.4),
        sharex=True,
        height_ratios=(3, 1),
        layout="constrained",
    )
    axes[0].scatter(t, msd, s=34, color="#203c5b", label="Эксперимент", zorder=3)
    axes[0].plot(
        line_t,
        fit["slope_zero_px2_s"] * line_t,
        color="#b53232",
        label=r"МНК: $\langle\Delta s^2\rangle = At$",
    )
    axes[0].plot(
        line_t,
        fit["slope_px2_s"] * line_t + fit["intercept_px2"],
        "--",
        color="#267c68",
        label=r"МНК: $\langle\Delta s^2\rangle = at + c$",
    )
    axes[0].set(ylabel=r"$\langle\Delta s^2\rangle$, пиксель²", ylim=(0, None))
    axes[0].legend(loc="upper left")
    # Остатки относительно прямой через начало показывают отклонение от 4Dt.
    axes[1].axhline(0, color="0.4", linewidth=0.8)
    axes[1].plot(
        t, msd - fit["slope_zero_px2_s"] * t, "o-", color="#b53232", markersize=4
    )
    axes[1].set(
        xlabel="t = kτ, с", ylabel="Остаток,\nпиксель²", xticks=np.arange(0, 37, 4)
    )
    fig.savefig(FIGURES / "msd.pdf")
    fig.savefig(FIGURES / "msd.png", dpi=180)
    plt.close(fig)


def main():
    # Поток обработки: чтение -> MSD -> две аппроксимации -> таблицы -> графики.
    RESULTS.mkdir(exist_ok=True)
    FIGURES.mkdir(exist_ok=True)
    xy, tau, skipped = read_coordinates(SOURCE)
    summary, pairs = calculate_msd(xy, tau)
    fit = fit_msd(summary[:, 1], summary[:, 4])
    export_results(xy, tau, skipped, summary, pairs, fit)
    make_figures(xy, summary, fit)
    print(json.dumps({"n": len(xy), "tau_s": tau, **fit}, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
