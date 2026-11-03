"""Обработка скриншотов выданного электронографа и подготовка отчёта.

Программа не генерирует электроны и не подменяет приложение-тестер.
Радиусы считываются с сохранённых электронограмм, статистика — из CSV,
перенесённого с экрана программы. Все пути отсчитываются от этого файла.
"""

from pathlib import Path
import argparse
import csv
import hashlib
import json
import math

import matplotlib

matplotlib.use("Agg")  # Обработка не требует окон и работает также на Mac.
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from scipy.signal import find_peaks

ROOT = Path(__file__).resolve().parent
RESULTS, FIGURES = ROOT / "results", ROOT / "figures"

# Константы именно из tasks.pdf; V далее в кВ, длины волн и d — в Å.
H, M, E, C = 6.63e-34, 0.911e-30, 1.602e-19, 2.998e8
L_MM, A_ANGSTROM = 757.0, 2.87
C1 = H * 1e10 / math.sqrt(2 * M * E * 1000)
C2 = E * 1000 / (2 * M * C**2)
VOLTAGES = (30, 37, 47, 61, 83, 120)
READING_MM = 0.2  # Порядок точности отсчёта по растровому изображению.


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_sources():
    """Не обрабатывать случайно изменённые скриншоты или чужую таблицу."""
    manifest = json.loads(
        (RESULTS / "capture_manifest.json").read_text(encoding="utf8")
    )
    if sha256(ROOT / manifest["application"]) != manifest["application_sha256"]:
        raise ValueError("Executable differs from the application used for capture")
    for name, digest in manifest["screenshots_sha256"].items():
        if sha256(ROOT / "screenshots" / name) != digest:
            raise ValueError(f"Screenshot has changed: {name}")
    origin = json.loads(
        (RESULTS / "statistics_provenance.json").read_text(encoding="utf8")
    )
    if sha256(ROOT / origin["screenshot"]) != origin["screenshot_sha256"]:
        raise ValueError(
            "Update the statistics CSV and its provenance after a new capture"
        )
    if sha256(RESULTS / "statistics_input.csv") != origin["csv_sha256"]:
        raise ValueError("Statistics CSV has changed; check it against the screenshot")
    return manifest


def wavelength(voltage_kv):
    """Релятивистская формула из теории с переводом кВ и ангстремов."""
    return C1 / math.sqrt(voltage_kv * (1 + C2 * voltage_kv))


def measure_rings(path):
    """Найти кольца на реальном снимке без использования расчётных радиусов.

    Центральная синяя линия задаёт центр; высокая риска линейки повторяется
    через 10 маленьких делений по 1 мм. Затем остаются только тёмные метки
    электронов. В радиальной гистограмме ищем семь пиков и оцениваем их
    положения. Число тёмных пикселей не интерпретируется как число электронов.
    """
    rgb = np.asarray(Image.open(path).convert("RGB"))
    height, width = rgb.shape[:2]
    cx, cy = width // 2, height // 2
    blue = (rgb[:, :, 2] > 160) & (rgb[:, :, 0] < 100) & (rgb[:, :, 1] < 100)
    if not np.argmax(blue.sum(axis=1)) == cy:
        raise ValueError(f"Expected a centered ruler in {path}")
    # На 7 пикселей выше оси видны только большие риски, а не вся линия.
    positions = np.flatnonzero(blue[cy - 7])
    groups = np.split(positions, np.flatnonzero(np.diff(positions) > 2) + 1)
    ticks = np.array([group.mean() for group in groups if len(group)])
    gaps = np.diff(ticks)
    gaps = gaps[(gaps > 40) & (gaps < 70)]
    if len(gaps) < 5:
        raise ValueError(f"Not enough scale ticks in {path}")
    pixel_per_mm = float(gaps.mean() / 10)
    yy, xx = np.indices((height, width))
    # Полосу линейки с цифрами исключаем, чтобы она не создавала ложные кольца.
    black = (rgb.max(axis=2) < 90) & (np.abs(yy - cy) > 14)
    radial_mm = np.hypot(xx[black] - cx, yy[black] - cy) / pixel_per_mm
    edges = np.arange(10, 85.05, 0.05)
    counts, _ = np.histogram(radial_mm, bins=edges)
    centers = (edges[:-1] + edges[1:]) / 2
    smoothed = np.convolve(counts, np.ones(7) / 7, mode="same")
    peaks, _ = find_peaks(smoothed, distance=35, prominence=1)
    # Семь наиболее выраженных пиков, упорядоченных по радиусу.
    peaks = sorted(sorted(peaks, key=lambda p: smoothed[p], reverse=True)[:7])
    if len(peaks) != 7:
        raise ValueError(f"Expected 7 ring peaks in {path}; found {len(peaks)}")
    radii = [
        float(radial_mm[np.abs(radial_mm - centers[p]) < 1.2].mean()) for p in peaks
    ]
    return {"pixel_per_mm": pixel_per_mm, "radii_mm": radii}


def read_statistics():
    """Восстановить целые счётчики из трёхзнаковых долей экранной таблицы."""
    with (RESULTS / "statistics_input.csv").open(
        encoding="utf-8-sig", newline=""
    ) as stream:
        source = list(csv.DictReader(stream))
    result = []
    previous = (0, 0, 0)
    for row in source:
        n, k = int(row["released"]), int(row["diffracted_k"])
        counts = []
        for field in ("k1_over_k0", "k2_over_k0"):
            fraction = float(row[field])
            count = int(round(n * fraction))
            # Delphi и Python могут по-разному округлять точные середины.
            if abs(count / n - fraction) > 0.00050001:
                raise ValueError(f"Cannot recover an integer count: {row}")
            counts.append(count)
        if not 0 < k <= n or sum(counts) > k:
            raise ValueError(f"Invalid electron counts: {row}")
        current = (*counts, k)
        if any(a < b for a, b in zip(current, previous)):
            raise ValueError(f"Cumulative counts decrease: {row}")
        previous = current
        result.append(
            {
                "released_k0": n,
                "diffracted_k": k,
                "k1": counts[0],
                "k2": counts[1],
                "k1_over_k": counts[0] / k,
                "k2_over_k": counts[1] / k,
            }
        )
    if len(result) != 20 or result[-1]["released_k0"] != 1000:
        raise ValueError("Expected 20 measurements with step 50 up to 1000")
    return result


def fit_line(x, y):
    """МНК для R=A*X+B, а также отдельная проверка прямой через начало."""
    x, y = np.asarray(x), np.asarray(y)
    slope, intercept = np.linalg.lstsq(
        np.column_stack((x, np.ones(len(x)))), y, rcond=None
    )[0]
    residual = y - (slope * x + intercept)
    origin_slope = np.dot(x, y) / np.dot(x, x)
    return {
        "slope": float(slope),
        "intercept_mm": float(intercept),
        "R_squared": float(1 - np.sum(residual**2) / np.sum((y - y.mean()) ** 2)),
        "origin_slope": float(origin_slope),
        "origin_max_residual_mm": float(np.max(np.abs(y - origin_slope * x))),
    }


def write_csv(name, rows):
    with (RESULTS / name).open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def save_figure(fig, name):
    fig.savefig(FIGURES / (name + ".pdf"))
    fig.savefig(FIGURES / (name + ".png"), dpi=200)
    plt.close(fig)


def mosaic(paths, titles, shape, size, name):
    """Собрать исходные снимки рядом; физическое содержимое не изменяется."""
    fig, axes = plt.subplots(*shape, figsize=size, layout="constrained")
    for ax, path, title in zip(np.asarray(axes).reshape(-1), paths, titles):
        with Image.open(ROOT / path) as source:
            ax.imshow(source)
        ax.set_title(title, fontsize=10)
        ax.axis("off")
    save_figure(fig, name)


def tex_number(value, digits=3):
    return f"{value:.{digits}f}".replace(".", "{,}")


def generate():
    manifest = verify_sources()
    FIGURES.mkdir(exist_ok=True)
    plt.rcParams.update(
        {"font.family": "Times New Roman", "font.size": 11, "axes.unicode_minus": False}
    )
    runs = manifest["runs"]
    # Обрабатываем только достаточно заполненные электронограммы.
    measured = []
    lookup = {}
    for run in runs:
        if run["count"] < 10000:
            continue
        measurement = measure_rings(ROOT / run["screen"])
        lookup[(run["task"], run["voltage_kv"])] = measurement
        for j, radius in enumerate(measurement["radii_mm"], 1):
            measured.append(
                {
                    "task": run["task"],
                    "voltage_kv": run["voltage_kv"],
                    "ring": j,
                    "radius_pixel_estimate_mm": radius,
                    "radius_report_mm": round(radius, 1),
                    "pixel_per_mm": measurement["pixel_per_mm"],
                    "screenshot": run["screen"],
                }
            )
    write_csv("measured_radii.csv", measured)
    statistics = read_statistics()
    write_csv("statistics.csv", statistics)

    voltage_rows = []
    for v in VOLTAGES:
        radii = lookup[("task2", v)]["radii_mm"]
        voltage_rows.append(
            {
                "voltage_kv": v,
                "lambda_a": wavelength(v),
                "X": 1 / math.sqrt(v * (1 + C2 * v)),
                "R2_mm": round(radii[1], 1),
                "R3_mm": round(radii[2], 1),
            }
        )
    write_csv("voltage.csv", voltage_rows)
    x = np.array([r["X"] for r in voltage_rows])
    fits = [
        {"ring": j, **fit_line(x, [r[f"R{j}_mm"] for r in voltage_rows])}
        for j in (2, 3)
    ]

    # Структура определяется по отдельной серии 30 кВ / 30 000 электронов.
    structure = []
    for j, raw_radius in enumerate(lookup[("task3", 30)]["radii_mm"][:5], 1):
        radius = round(raw_radius, 1)
        order = 2 if j == 4 else 1
        d = order * L_MM * wavelength(30) / radius
        squared_sum = (A_ANGSTROM / d) ** 2
        target = round(squared_sum)
        candidates = [
            (h, k, l)
            for h in range(math.isqrt(target), -1, -1)
            for k in range(h, -1, -1)
            for l in range(k, -1, -1)
            if h * h + k * k + l * l == target and (h + k + l) % 2 == 0
        ]
        if len(candidates) != 1:
            raise ValueError(f"Ambiguous Miller indices for ring {j}: {candidates}")
        structure.append(
            {
                "ring": j,
                "order": order,
                "R_mm": radius,
                "d_a": d,
                "reading_component_d_a": d * READING_MM / radius,
                "squared_sum": squared_sum,
                "rounded_sum": target,
                "hkl": "(" + "".join(map(str, candidates[0])) + ")",
            }
        )
    write_csv("structure.csv", structure)

    accumulation = [r for r in runs if r["task"] == "task1"]
    mosaic(
        [r["screen"] for r in accumulation],
        [
            f"{r['voltage_kv']} кВ · {r['count']:,} электронов".replace(",", " ")
            for r in accumulation
        ],
        (3, 3),
        (8, 7.5),
        "task1_accumulation",
    )
    mosaic(
        [f"screenshots/task1_speed{p}_40kV_1000_screen.png" for p in (1, 2)],
        [
            f"Темп {r['position']} · {r['elapsed_s']:.1f} с"
            for r in manifest["speed_runs"]
        ],
        (1, 2),
        (8, 3.8),
        "task1_speeds",
    )

    fig, ax = plt.subplots(figsize=(7, 3.8), layout="constrained")
    for j, color in ((1, "#216797"), (2, "#b44936")):
        ax.plot(
            [r["released_k0"] for r in statistics],
            [r[f"k{j}_over_k"] for r in statistics],
            "o-",
            color=color,
            markersize=3,
            label=rf"Кольцо {j}: $k_{j}/k$",
        )
    ax.set(
        xlabel=r"Выпущено электронов $k_0$",
        ylabel=r"Доля $k_j/k$",
        xlim=(0, 1000),
        ylim=(0, 1),
    )
    ax.grid(alpha=0.25)
    ax.legend()
    save_figure(fig, "task1_statistics")

    fig, ax = plt.subplots(figsize=(7, 4.3), layout="constrained")
    line = np.linspace(0, x.max() * 1.05, 200)
    for fit, color in zip(fits, ("#216797", "#b44936")):
        j = fit["ring"]
        y = [r[f"R{j}_mm"] for r in voltage_rows]
        ax.errorbar(
            x,
            y,
            yerr=READING_MM,
            fmt="o",
            color=color,
            capsize=3,
            label=f"Кольцо {j}: отсчёты по электронограммам",
        )
        ax.plot(line, fit["slope"] * line + fit["intercept_mm"], color=color)
        ax.plot(line, fit["origin_slope"] * line, color=color, linestyle=":", alpha=0.6)
    ax.set(
        xlabel=r"$X=[V(1+C_2V)]^{-1/2}$, кВ$^{-1/2}$",
        ylabel="R, мм",
        xlim=(0, line[-1]),
        ylim=(0, 49),
    )
    ax.plot([], [], color="0.4", label="Сплошная: R = AX + B")
    ax.plot([], [], color="0.4", linestyle=":", label="Пунктир: R = A₀X")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=9)
    save_figure(fig, "task2_voltage")
    voltage_runs = [r for r in runs if r["task"] == "task2"]
    mosaic(
        [r["screen"] for r in voltage_runs],
        [f"V = {r['voltage_kv']} кВ" for r in voltage_runs],
        (2, 3),
        (8, 5.4),
        "task2_electronograms",
    )

    values = {
        "ConstantOne": tex_number(C1, 6),
        "ConstantTwo": tex_number(C2, 8),
        "LambdaThirty": tex_number(wavelength(30), 6),
        "DiffractedCount": str(statistics[-1]["diffracted_k"]),
        "RingOneCount": str(statistics[-1]["k1"]),
        "RingTwoCount": str(statistics[-1]["k2"]),
        "RingOneFraction": tex_number(statistics[-1]["k1_over_k"], 4),
        "RingTwoFraction": tex_number(statistics[-1]["k2_over_k"], 4),
        "SpeedOneTime": tex_number(manifest["speed_runs"][0]["elapsed_s"], 1),
        "SpeedTwoTime": tex_number(manifest["speed_runs"][1]["elapsed_s"], 1),
    }
    for fit in fits:
        suffix = "Two" if fit["ring"] == 2 else "Three"
        for name, key, digits in (
            ("Slope", "slope", 2),
            ("Intercept", "intercept_mm", 2),
            ("RSquared", "R_squared", 5),
            ("OriginResidual", "origin_max_residual_mm", 2),
        ):
            values[name + suffix] = tex_number(fit[key], digits)
    (RESULTS / "values.tex").write_text(
        "% Generated by lab5.py\n"
        + "\n".join(
            rf"\newcommand{{\{name}}}{{{value}}}" for name, value in values.items()
        )
        + "\n",
        encoding="utf8",
    )
    voltage_tex = [
        " & ".join(
            [
                str(r["voltage_kv"]),
                tex_number(r["lambda_a"], 6),
                tex_number(r["X"], 6),
                tex_number(r["R2_mm"], 1),
                tex_number(r["R3_mm"], 1),
            ]
        )
        + r" \\"
        for r in voltage_rows
    ]
    (RESULTS / "voltage_rows.tex").write_text(
        "\n".join(voltage_tex) + "\n", encoding="utf8"
    )
    structure_tex = [
        " & ".join(
            [
                str(r["ring"]),
                str(r["order"]),
                tex_number(r["R_mm"], 1),
                tex_number(r["d_a"], 3),
                tex_number(r["squared_sum"], 3),
                str(r["rounded_sum"]),
                r["hkl"],
            ]
        )
        + r" \\"
        for r in structure
    ]
    (RESULTS / "structure_rows.tex").write_text(
        "\n".join(structure_tex) + "\n", encoding="utf8"
    )
    summary = {
        "source": "Supplied app-example/difraction.exe; real window screenshots",
        "constants": {"C1": C1, "C2_per_kV": C2, "L_mm": L_MM, "a_a": A_ANGSTROM},
        "reading_scale_mm": READING_MM,
        "statistics": statistics[-1],
        "voltage": voltage_rows,
        "fits": fits,
        "structure": structure,
        "speed_runs": manifest["speed_runs"],
    }
    (RESULTS / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
    )
    print(
        json.dumps(
            {"statistics": statistics[-1], "fits": fits, "structure": structure},
            ensure_ascii=True,
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify",
        action="store_true",
        help="verify source screenshots without regenerating",
    )
    args = parser.parse_args()
    if args.verify:
        verify_sources()
        print("Executable, screenshots and statistics provenance verified.")
    else:
        generate()
