"""Воспроизводимые модельные серии, графики и таблицы отчёта."""
from pathlib import Path
import json

import matplotlib.pyplot as plt
import numpy as np

from lab5_model import (
    Configuration, ElectronSimulation, DEFAULT_SEED, C1, C2, CAMERA_MM, LATTICE_A,
    CONDITIONAL_PROBABILITIES, CHANNEL_PROBABILITIES, SPACINGS_A, wavelength_a,
    voltage_experiment, structure_experiment, measured_radii, write_csv,
)

ROOT = Path(__file__).resolve().parent
FIGURES, RESULTS = ROOT / "figures", ROOT / "results"


def save_figure(fig, name):
    fig.savefig(FIGURES / f"{name}.pdf")
    fig.savefig(FIGURES / f"{name}.png", dpi=180)
    plt.close(fig)


def num(value, digits=3):
    return f"{value:.{digits}f}".replace(".", "{,}")


def scatter_panel(ax, points, title):
    ax.set_facecolor("#081a29")
    ax.scatter(points[:, 0], points[:, 1], s=0.8, c="#b3e3ff", linewidths=0, rasterized=True)
    ax.set(xlim=(-78, 78), ylim=(-78, 78), aspect="equal", title=title,
           xticks=(-60, 0, 60), yticks=(-60, 0, 60))
    ax.grid(alpha=0.12)


def generate(seed=DEFAULT_SEED):
    FIGURES.mkdir(exist_ok=True)
    RESULTS.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "Times New Roman", "font.size": 11,
                         "axes.unicode_minus": False})
    fig, axes = plt.subplots(3, 3, figsize=(8, 7.5), layout="constrained", sharex=True, sharey=True)
    snapshot_summary = []
    for i, voltage in enumerate((40, 60, 120)):
        simulation = ElectronSimulation(Configuration(voltage, (seed+i) % 2**32))
        simulation.add(10000)
        for j, count in enumerate((10, 1000, 10000)):
            scatter_panel(axes[i, j], simulation.points[:count], f"{voltage} кВ · {count} электронов")
            if i == 2:
                axes[i, j].set_xlabel("x, мм")
            if j == 0:
                axes[i, j].set_ylabel("y, мм")
        snapshot_summary.append({"voltage_kv": voltage, "lambda_a": float(wavelength_a(voltage)),
                                 "counts": simulation.counts().tolist()})
        simulation.export_csv(RESULTS / f"electrons_{voltage}kV.csv")
        if voltage == 40:
            simulation.save(RESULTS / "demo_40kV.json")
    save_figure(fig, "task1_accumulation")

    simulation = ElectronSimulation(Configuration(40, (seed+20) % 2**32))
    simulation.add(1000)
    history = simulation.history(25)
    write_csv(RESULTS / "task1_statistics.csv", ["released_k0", "diffracted_k", "k1_over_k", "k2_over_k"], history)
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 5.2), sharex=True, layout="constrained")
    for j, (ax, color) in enumerate(zip(axes, ("#216797", "#b44936"))):
        p = CONDITIONAL_PROBABILITIES[j]
        sigma = np.sqrt(p*(1-p)/history[:, 1])
        ax.fill_between(history[:, 0], np.maximum(0, p-2*sigma), np.minimum(1, p+2*sigma),
                        color=color, alpha=0.12, label="Ориентир ±2σ")
        ax.plot(history[:, 0], history[:, j+2], "o-", color=color, markersize=2.5, label=f"k{j+1}/k")
        ax.axhline(p, color="0.35", linestyle="--", label="Вероятность модели")
        ax.set(ylabel=f"k{j+1}/k", ylim=(0, 0.55))
        ax.grid(alpha=0.25)
        ax.legend(fontsize=9, ncol=3)
    axes[-1].set(xlabel="Выпущено электронов k₀", xlim=(0, 1000))
    save_figure(fig, "task1_statistics")
    stats = {"released": 1000, "step": 25, "diffracted": int(simulation.counts()[1:].sum()),
             "fractions": [float(value) for value in history[-1, 2:]],
             "conditional_probabilities": CONDITIONAL_PROBABILITIES[:2].tolist()}
    simulation.add(9000)
    extended = simulation.history(25)
    stats["fractions_at_10000"] = extended[-1, 2:].tolist()
    write_csv(RESULTS / "task1_statistics_extended.csv", ["released_k0", "diffracted_k", "k1_over_k", "k2_over_k"], extended)

    voltage = voltage_experiment(seed=seed)
    keys = list(voltage["rows"][0])
    write_csv(RESULTS / "task2_voltage.csv", keys, [[row[key] for key in keys] for row in voltage["rows"]])
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 5.5), sharex=True,
                             gridspec_kw={"height_ratios": (3, 1)}, layout="constrained")
    x = np.array([row["X"] for row in voltage["rows"]])
    line = np.linspace(0, x.max()*1.05, 200)
    for fit, color in zip(voltage["fits"], ("#216797", "#b44936")):
        ring = fit["ring"]
        y = np.array([row[f"R{ring}_mm"] for row in voltage["rows"]])
        axes[0].errorbar(x, y, yerr=[row[f"sem{ring}_mm"] for row in voltage["rows"]],
                         fmt="o", color=color, markersize=4, capsize=3, label=f"Кольцо {ring}")
        axes[0].plot(line, fit["slope"]*line+fit["intercept_mm"], color=color)
        axes[1].plot(x, (y-fit["slope"]*x-fit["intercept_mm"])*1e3, "o-", color=color, markersize=3)
    axes[0].set(ylabel="R, мм", ylim=(0, None))
    axes[0].legend()
    axes[1].axhline(0, color="0.4", linewidth=0.7)
    axes[1].set(xlabel=r"$X=[V(1+C_2V)]^{-1/2}$, кВ$^{-1/2}$", ylabel="Остаток,\nмкм", xlim=(0, x.max()*1.05))
    for ax in axes:
        ax.grid(alpha=0.25)
    save_figure(fig, "task2_debroglie")

    structure = structure_experiment(seed=seed)
    keys = ("ring", "order", "radius_mm", "spacing_a", "squared_sum", "rounded_sum", "allowed_bcc")
    write_csv(RESULTS / "task3_structure.csv", keys, [[row[key] for key in keys] for row in structure["rows"]])
    simulation = ElectronSimulation(Configuration(30, (seed+100) % 2**32))
    simulation.add(structure["count"])
    simulation.export_csv(RESULTS / "electrons_30kV.csv")
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.8), layout="constrained")
    scatter_panel(axes[0], simulation.points, "30 кВ · 30 000 электронов")
    axes[0].set(xlabel="x, мм", ylabel="y, мм")
    radial = np.hypot(simulation.points[:, 0], simulation.points[:, 1])
    axes[1].hist(radial[radial > 5], bins=350, range=(5, 75), color="#3177a1")
    axes[1].set(xlabel="r, мм", ylabel="Число попаданий", title="Радиальный профиль")
    for row in structure["rows"]:
        axes[1].axvline(row["radius_mm"], color="#b44936", linestyle=":", linewidth=0.8)
    save_figure(fig, "task3_structure")

    # Темп — только планирование выдачи точек; проверяем равенство траекторий
    # при одинаковом seed и разных размерах порций, имитирующих разную скорость.
    a = ElectronSimulation(Configuration(40, seed))
    b = ElectronSimulation(Configuration(40, seed))
    a.add(10000)
    for _ in range(100):
        b.add(100)
    rate_invariant = bool(np.array_equal(a.points, b.points))
    assert rate_invariant
    summary = {"seed": seed, "C1": C1, "C2_per_kV": C2, "L_mm": CAMERA_MM,
               "a_angstrom": LATTICE_A, "model_probabilities": CHANNEL_PROBABILITIES.tolist(),
               "radial_sigma_mm": 0.22, "rate_invariant": rate_invariant,
               "task1_snapshots": snapshot_summary, "task1_statistics": stats,
               "task2": voltage, "task3": structure,
               "limitations": "Synthetic kinematic model. Ring weights prescribed; not a measured electronogram."}
    (RESULTS / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, allow_nan=False, indent=2)+"\n", encoding="utf-8")
    export_tex(summary)
    print(json.dumps({"C1": C1, "C2": C2, "statistics": stats, "fits": voltage["fits"],
                      "structure": structure["rows"], "rate_invariant": rate_invariant}, ensure_ascii=True, indent=2))


def export_tex(summary):
    values = {"SimulationSeed": str(summary["seed"]), "ConstantOne": num(C1, 6), "ConstantTwo": num(C2, 8),
              "LambdaThirty": num(wavelength_a(30), 6), "LambdaOneTwenty": num(wavelength_a(120), 6),
              "RingOneP": num(CONDITIONAL_PROBABILITIES[0], 4), "RingTwoP": num(CONDITIONAL_PROBABILITIES[1], 4),
              "RingOneFraction": num(summary["task1_statistics"]["fractions"][0], 4),
              "RingTwoFraction": num(summary["task1_statistics"]["fractions"][1], 4),
              "RingOneLong": num(summary["task1_statistics"]["fractions_at_10000"][0], 4),
              "RingTwoLong": num(summary["task1_statistics"]["fractions_at_10000"][1], 4),
              "DiffractedCount": str(summary["task1_statistics"]["diffracted"])}
    for fit in summary["task2"]["fits"]:
        suffix = "Two" if fit["ring"] == 2 else "Three"
        values["Slope"+suffix] = num(fit["slope"], 3)
        values["Intercept"+suffix] = num(fit["intercept_mm"], 5)
        values["RSquared"+suffix] = num(fit["R2"], 7)
    (RESULTS / "values.tex").write_text("% Generated by lab5.py --generate\n"+"\n".join(
        rf"\newcommand{{\{key}}}{{{value}}}" for key, value in values.items())+"\n", encoding="utf-8")
    voltage_rows = [" & ".join([str(row["voltage_kv"]), num(row["lambda_a"], 6), num(row["X"], 6),
                                num(row["R2_mm"], 3), num(row["R3_mm"], 3)])+r" \\"
                    for row in summary["task2"]["rows"]]
    (RESULTS / "voltage_rows.tex").write_text("\n".join(voltage_rows)+"\n", encoding="utf-8")
    structure_rows = []
    for row in summary["task3"]["rows"]:
        hkl = row["allowed_bcc"][0]
        structure_rows.append(" & ".join([str(row["ring"]), str(row["order"]), num(row["radius_mm"], 2),
                                          num(row["spacing_a"], 4), num(row["squared_sum"], 4),
                                          str(row["rounded_sum"]), "("+"".join(map(str, hkl))+")"])+r" \\")
    (RESULTS / "structure_rows.tex").write_text("\n".join(structure_rows)+"\n", encoding="utf-8")
