"""Лаба 4. Интерференция, поляризация и дифракция света.

Запуск: python lab4.py. Внутри расчётов используются метры и радианы.
Интенсивности относительные; их нормировка подписана на каждом рисунке.
"""

from pathlib import Path
import csv
import json

import matplotlib

matplotlib.use("Agg")  # Рисуем в файлы; открывать окна не требуется.
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
from scipy.special import j1, jn_zeros


ROOT = Path(__file__).resolve().parent
FIGURES, RESULTS = ROOT / "figures", ROOT / "results"
WAVELENGTH = 550e-9  # Длина волны в воздухе, а не внутри плёнки.
I0 = 1.0
SCREEN = 2.0  # Расстояние до экрана, м.
SEPARATION = 0.20e-3  # Между точечными источниками / центрами щелей, м.
SLIT_WIDTH = 50e-6
APERTURE_RADIUS = 0.10e-3
FILM_THICKNESS = 2e-6
COLORS = ("#246c9c", "#b54738", "#27816a")


def save(fig, name):
    """PDF нужен отчёту, PNG — для просмотра отдельно от LaTeX."""
    fig.savefig(FIGURES / f"{name}.pdf")
    fig.savefig(FIGURES / f"{name}.png", dpi=180)
    plt.close(fig)


def csv_file(name, columns, rows):
    with (RESULTS / name).open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(columns)
        writer.writerows(rows)


def two_beam(phase, i1=I0, i2=I0):
    # Складываются поля; квадрат суммы даёт интерференционный член.
    # Формула предполагает когерентность и параллельную поляризацию.
    return i1 + i2 + 2 * np.sqrt(i1 * i2) * np.cos(phase)


def task1():
    """Контраст, ширина полос и влияние длины волны."""
    period = WAVELENGTH * SCREEN / SEPARATION
    # Параксиальная модель: разность хода = d*x/L, фаза = 2*pi*d*x/(lambda*L).
    # Число точек выбрано так, чтобы экстремумы не все совпали с узлами сетки.
    x = np.linspace(-5 * period, 5 * period, 5002)
    phase = 2 * np.pi * SEPARATION * x / (WAVELENGTH * SCREEN)
    ratios = (1.0, 0.25, 0.01)
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 6.1), layout="constrained")
    summary = []
    curves = []
    for ratio, color in zip(ratios, COLORS):
        intensity = two_beam(phase, 1, ratio)
        curves.append(intensity)
        imax, imin = float(intensity.max()), float(intensity.min())
        visibility = (imax - imin) / (imax + imin)
        v_theory = 2 * np.sqrt(ratio) / (1 + ratio)
        # Период измеряем по соседним максимумам дискретной кривой.
        # Максимум не ниже правого соседа и выше левого; при плоской паре
        # выбирается один узел. Здесь этого достаточно: кривые гладкие, без шума.
        maxima = (
            np.flatnonzero(
                (intensity[1:-1] > intensity[:-2]) & (intensity[1:-1] >= intensity[2:])
            )
            + 1
        )
        spacing_graph = float(np.diff(x[maxima]).mean())
        summary.append(
            {
                "I1": 1.0,
                "I2": ratio,
                "Imax_theory": (1 + np.sqrt(ratio)) ** 2,
                "Imin_theory": (1 - np.sqrt(ratio)) ** 2,
                "visibility_theory": float(v_theory),
                "visibility_grid": visibility,
                "visibility_abs_error": float(abs(visibility - v_theory)),
                "visibility_relative_error_percent": float(
                    100 * abs(visibility / v_theory - 1)
                ),
                "spacing_grid_m": spacing_graph,
                "spacing_theory_m": period,
                "spacing_relative_error_percent": float(
                    100 * abs(spacing_graph / period - 1)
                ),
            }
        )
        axes[0].plot(x * 1e3, intensity, color=color, label=f"I₁ = 1; I₂ = {ratio:g}")
    axes[0].set(
        xlabel="x, мм", ylabel="I / I₁", xlim=(-3 * period * 1e3, 3 * period * 1e3)
    )
    axes[0].legend(ncol=3, fontsize=10)
    wavelengths = (450e-9, WAVELENGTH, 650e-9)
    for wave, color in zip(wavelengths, ("#3366b5", "#27816a", "#b54738")):
        intensity = two_beam(2 * np.pi * SEPARATION * x / (wave * SCREEN)) / 4
        axes[1].plot(x * 1e3, intensity, color=color, label=f"λ = {wave * 1e9:.0f} нм")
    axes[1].set(
        xlabel="x, мм", ylabel="I / (4I₀)", xlim=(-2 * period * 1e3, 2 * period * 1e3)
    )
    axes[1].legend(ncol=3, fontsize=10)
    save(fig, "task1_visibility")
    csv_file(
        "task1_interference.csv",
        ["x_m", "I_equal", "I2_0.25", "I2_0.01"],
        zip(x, *curves),
    )
    return {
        "cases": summary,
        "grid_step_m": float(x[1] - x[0]),
        "wavelengths_nm": [450, 550, 650],
        "fringe_widths_m": [float(wave * SCREEN / SEPARATION) for wave in wavelengths],
    }


def task2():
    """Угловая картина двух точечных когерентных источников."""
    theta = np.deg2rad(np.linspace(-0.85, 0.85, 5001))
    intensity = two_beam(2 * np.pi * SEPARATION * np.sin(theta) / WAVELENGTH)
    orders = np.arange(-5, 6)
    angles = np.arcsin(orders * WAVELENGTH / SEPARATION)
    fig, ax = plt.subplots(figsize=(7.2, 4.1), layout="constrained")
    ax.plot(np.rad2deg(theta), intensity / 4, color=COLORS[0])
    ax.scatter(
        np.rad2deg(angles),
        np.ones(len(angles)),
        color=COLORS[1],
        s=20,
        label=r"$d\sin\theta=m\lambda$",
        zorder=3,
    )
    ax.set(xlabel="θ, градусы", ylabel="I / (4I₀)", xlim=(-0.85, 0.85), ylim=(0, 1.15))
    ax.legend()
    save(fig, "task2_sources")
    csv_file(
        "task2_sources.csv", ["theta_rad", "I_over_4I0"], zip(theta, intensity / 4)
    )
    csv_file(
        "task2_maxima.csv", ["order", "theta_deg"], zip(orders, np.rad2deg(angles))
    )
    return {
        "first_maximum_deg": float(np.rad2deg(np.arcsin(WAVELENGTH / SEPARATION))),
        "orders": orders.tolist(),
        "maxima_deg": np.rad2deg(angles).tolist(),
    }


def film_profile(theta_inside, index, thickness=FILM_THICKNESS):
    # Модель воздух–плёнка–воздух, два луча равной амплитуды.
    # Ровно одно из отражений даёт скачок pi как при n>1, так и при n<1.
    # Поэтому I/(4*I_ref)=sin²(2*pi*n*t*cos(theta)/lambda).
    # Это нормированная форма картины, а НЕ коэффициент отражения всей плёнки.
    propagation_phase = (
        4 * np.pi * index * thickness * np.cos(theta_inside) / WAVELENGTH
    )
    return np.sin(propagation_phase / 2) ** 2


def task3():
    """Тонкая плёнка: фаза оптического пути и отражений."""
    theta = np.deg2rad(np.linspace(0, 40, 4001))
    # Для n=1.5 при освещении из воздуха theta_inside <= arcsin(1/1.5).
    # Общий диапазон 0...40° физически доступен обоим рассматриваемым n.
    fig, ax = plt.subplots(figsize=(7.2, 4.2), layout="constrained")
    data, summary = [], []
    for index, color in zip((1.5, 0.8), COLORS):
        profile = film_profile(theta, index)
        # Закон Снеллиуса: sin(alpha_incident)=n*sin(theta_inside), n_air=1.
        incident = np.arcsin(index * np.sin(theta))
        data.append(profile)
        optical_order = 2 * index * FILM_THICKNESS / WAVELENGTH
        integer_orders = np.arange(0, int(np.floor(optical_order)) + 1)
        zeros = np.arccos(np.clip(integer_orders / optical_order, 0, 1))
        zeros = zeros[(zeros >= 0) & (zeros <= theta[-1])]
        summary.append(
            {
                "index": index,
                "theta_max_deg": 40.0,
                "incident_max_deg": float(np.rad2deg(incident[-1])),
                "dark_angles_deg": np.rad2deg(zeros).tolist(),
            }
        )
        ax.plot(np.rad2deg(theta), profile, color=color, label=f"n = {index:g}")
    ax.set(
        xlabel="θ внутри плёнки, градусы",
        ylabel="Нормированная интенсивность отражённых лучей",
        xlim=(0, 40),
        ylim=(0, 1.05),
    )
    ax.legend()
    save(fig, "task3_film")
    csv_file(
        "task3_film.csv",
        ["theta_inside_rad", "I_norm_n1.5", "I_norm_n0.8"],
        zip(theta, *data),
    )
    return {
        "thickness_m": FILM_THICKNESS,
        "outside_index": 1.0,
        "model": "two equal reflected amplitudes, one relative pi shift; not reflectance",
        "cases": summary,
    }


def task4():
    """Закон Малюса — квадрат проекции электрического поля на ось анализатора."""
    alpha = np.linspace(0, np.pi, 1001)
    theory = np.cos(alpha) ** 2
    # Независимая запись через скалярное произведение двух единичных векторов.
    e_in = np.array([1.0, 0.0])
    analyzer_axis = np.column_stack((np.cos(alpha), np.sin(alpha)))
    projected_intensity = (analyzer_axis @ e_in) ** 2
    fig, ax = plt.subplots(figsize=(7.2, 4.1), layout="constrained")
    ax.plot(np.rad2deg(alpha), theory, color=COLORS[0], label=r"$\cos^2\alpha$")
    ax.plot(
        np.rad2deg(alpha[::50]),
        projected_intensity[::50],
        "o",
        markersize=4,
        markerfacecolor="none",
        color=COLORS[1],
        label="Квадрат проекции поля",
    )
    ax.set(
        xlabel="α, градусы",
        ylabel="I / I₀",
        xlim=(0, 180),
        xticks=np.arange(0, 181, 30),
    )
    ax.legend()
    save(fig, "task4_malus")
    csv_file(
        "task4_malus.csv",
        ["alpha_rad", "I_cos2", "I_projection"],
        zip(alpha, theory, projected_intensity),
    )
    return {
        "max_difference": float(np.max(np.abs(theory - projected_intensity))),
        "angles_deg": [0, 30, 45, 60, 90],
        "values": [1, 0.75, 0.5, 0.25, 0],
    }


def single_slit(x, width=SLIT_WIDTH):
    # В параксиальной дальней зоне beta=pi*a*x/(lambda*L).
    # np.sinc(z)=sin(pi*z)/(pi*z), поэтому передаём beta/pi, а не beta.
    # В центре np.sinc(0)=1 — устранимая неопределённость обработана библиотекой.
    return np.sinc(width * np.asarray(x) / (WAVELENGTH * SCREEN)) ** 2


def airy(r):
    z = 2 * np.pi * APERTURE_RADIUS * np.asarray(r) / (WAVELENGTH * SCREEN)
    amplitude = np.ones_like(z, dtype=float)
    # В центре lim 2*J1(z)/z=1; деление выполняем только при z!=0.
    np.divide(2 * j1(z), z, out=amplitude, where=z != 0)
    return amplitude**2


def grating(theta, count, period):
    # Суммируем N комплексных полей. Между соседними щелями сдвиг фазы 2*beta.
    # Деление амплитуды на N нормирует главный пик к 1 и устраняет 0/0
    # формулы sin(N*beta)/sin(beta) в главных максимумах.
    phase = 2 * np.pi * period * np.sin(np.asarray(theta)) / WAVELENGTH
    field = np.exp(1j * np.arange(count)[:, None] * phase.ravel()[None, :]).mean(axis=0)
    return (np.abs(field) ** 2).reshape(np.shape(theta))


def task5():
    """Четыре случая дифракции Фраунгофера."""
    x = np.linspace(-0.060, 0.060, 12001)
    fig, ax = plt.subplots(figsize=(7.2, 4.2), layout="constrained")
    for width, color in zip((25e-6, SLIT_WIDTH, 100e-6), COLORS):
        ax.plot(
            x * 1e3,
            single_slit(x, width),
            color=color,
            label=f"a = {width * 1e6:g} мкм",
        )
    first_zero = WAVELENGTH * SCREEN / SLIT_WIDTH
    ax.set(xlabel="x, мм", ylabel="I / I₀", xlim=(-60, 60))
    ax.legend()
    save(fig, "task5a_single_slit")
    csv_file("task5a_single_slit.csv", ["x_m", "I_norm_a50um"], zip(x, single_slit(x)))

    r = np.linspace(0, 0.028, 6001)
    first_bessel_zero = float(jn_zeros(1, 1)[0])
    airy_radius = (
        first_bessel_zero * WAVELENGTH * SCREEN / (2 * np.pi * APERTURE_RADIUS)
    )
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.9), layout="constrained")
    axes[0].plot(r * 1e3, airy(r), color=COLORS[0])
    axes[0].axvline(
        airy_radius * 1e3, color=COLORS[1], linestyle="--", label="Первое тёмное кольцо"
    )
    axes[0].set(xlabel="r, мм", ylabel="I / I₀", xlim=(0, 28))
    axes[0].legend(fontsize=10)
    coordinate = np.linspace(-0.020, 0.020, 601)
    xx, yy = np.meshgrid(coordinate, coordinate)
    image = axes[1].imshow(
        airy(np.hypot(xx, yy)),
        extent=(-20, 20, -20, 20),
        origin="lower",
        cmap="inferno",
        norm=LogNorm(vmin=1e-4, vmax=1),
    )
    axes[1].set(xlabel="x, мм", ylabel="y, мм", title="Карта: логарифмическая шкала")
    fig.colorbar(image, ax=axes[1], label="I / I₀", shrink=0.85)
    save(fig, "task5b_airy")
    csv_file("task5b_airy.csv", ["r_m", "I_norm"], zip(r, airy(r)))

    fig, ax = plt.subplots(figsize=(7.2, 4.2), layout="constrained")
    envelope = single_slit(x)
    ax.plot(x * 1e3, envelope, "--", color="0.3", label="Огибающая одной щели")
    for separation, color in zip((SEPARATION, 2 * SEPARATION), COLORS):
        # I0 здесь — центральная интенсивность ДВУХ щелей; поэтому нет множителя 4.
        profile = envelope * np.cos(np.pi * separation * x / (WAVELENGTH * SCREEN)) ** 2
        ax.plot(x * 1e3, profile, color=color, label=f"d = {separation * 1e3:g} мм")
        csv_file(
            f"task5c_double_d{separation * 1e6:g}um.csv",
            ["x_m", "I_norm", "envelope"],
            zip(x, profile, envelope),
        )
    ax.set(xlabel="x, мм", ylabel="I / I₀", xlim=(-35, 35))
    ax.legend(fontsize=10)
    save(fig, "task5c_double_slit")

    period = 10e-6
    theta = np.deg2rad(np.linspace(-8, 8, 16001))
    fig, ax = plt.subplots(figsize=(7.2, 4.4), layout="constrained")
    grating_summary = []
    for count, color in zip((5, 10, 20), COLORS):
        profile = grating(theta, count, period)
        ax.plot(
            np.rad2deg(theta), profile, color=color, label=f"N = {count}", linewidth=1.1
        )
        # Расстояние между первыми нулями по обе стороны центрального максимума.
        full_width = 2 * np.arcsin(WAVELENGTH / (count * period))
        grating_summary.append(
            {"N": count, "central_zero_to_zero_deg": float(np.rad2deg(full_width))}
        )
        csv_file(
            f"task5d_grating_N{count}.csv", ["theta_rad", "I_norm"], zip(theta, profile)
        )
    ax.set(xlabel="θ, градусы", ylabel="I / I(0)", xlim=(-8, 8), ylim=(0, 1.08))
    ax.legend()
    save(fig, "task5d_grating")
    return {
        "single_slit_first_zero_m": first_zero,
        "single_slit_central_width_m": 2 * first_zero,
        "airy_radius_m": airy_radius,
        "bessel_first_zero": first_bessel_zero,
        "double_slit_separations_m": [SEPARATION, 2 * SEPARATION],
        "double_slit_fringe_widths_m": [
            float(WAVELENGTH * SCREEN / d) for d in (SEPARATION, 2 * SEPARATION)
        ],
        "grating_period_m": period,
        "grating_first_order_deg": float(np.rad2deg(np.arcsin(WAVELENGTH / period))),
        "grating": grating_summary,
    }


def tex_number(value, digits=3):
    return f"{value:.{digits}f}".replace(".", "{,}")


def export_tex(summary):
    first, diffract = summary["task1"], summary["task5"]
    values = {
        "FringeWidth": tex_number(WAVELENGTH * SCREEN / SEPARATION * 1e3),
        "SourceAngle": tex_number(summary["task2"]["first_maximum_deg"], 6),
        "SingleZero": tex_number(diffract["single_slit_first_zero_m"] * 1e3),
        "SingleWidth": tex_number(diffract["single_slit_central_width_m"] * 1e3),
        "AiryRadius": tex_number(diffract["airy_radius_m"] * 1e3),
        "GratingAngle": tex_number(diffract["grating_first_order_deg"], 6),
        "VisibilityError": tex_number(
            max(v["visibility_relative_error_percent"] for v in first["cases"]), 5
        ),
        "SpacingError": tex_number(
            max(v["spacing_relative_error_percent"] for v in first["cases"]), 4
        ),
    }
    (RESULTS / "values.tex").write_text(
        "% Generated by lab4.py.\n"
        + "\n".join(
            rf"\newcommand{{\{name}}}{{{value}}}" for name, value in values.items()
        )
        + "\n",
        encoding="utf-8",
    )
    rows = [
        " & ".join(
            tex_number(v[key], digits)
            for key, digits in (
                ("I2", 2),
                ("Imax_theory", 2),
                ("Imin_theory", 2),
                ("visibility_theory", 4),
                ("visibility_grid", 4),
            )
        )
        + " & "
        + tex_number(v["spacing_grid_m"] * 1e3, 4)
        + r" \\"
        for v in first["cases"]
    ]
    (RESULTS / "visibility_rows.tex").write_text(
        "\n".join(rows) + "\n", encoding="utf-8"
    )


def main():
    FIGURES.mkdir(exist_ok=True)
    RESULTS.mkdir(exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": "Times New Roman",
            "font.size": 12,
            "axes.grid": True,
            "grid.alpha": 0.22,
            "axes.unicode_minus": False,
        }
    )
    summary = {
        "parameters_SI": {
            "wavelength_m": WAVELENGTH,
            "I0": I0,
            "screen_m": SCREEN,
            "separation_m": SEPARATION,
            "slit_width_m": SLIT_WIDTH,
            "aperture_radius_m": APERTURE_RADIUS,
        },
        "task1": task1(),
        "task2": task2(),
        "task3": task3(),
        "task4": task4(),
        "task5": task5(),
    }
    export_tex(summary)
    (RESULTS / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
