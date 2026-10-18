"""Вариант 4. Моделирование RC- и RLC-цепей.

Запуск: python lab3.py. Все вычисления проводятся в СИ;
миллисекунды, микрокулоны и миллиамперы используются только на графиках.
"""

from pathlib import Path
import csv
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import simpson, solve_ivp
from scipy.optimize import minimize_scalar


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
R, L, C, U0 = 50.0, 180e-3, 5e-6, 10.0
Q0 = C * U0
OMEGA0 = 1 / np.sqrt(L * C)
T0 = 2 * np.pi / OMEGA0
RCR = 2 * np.sqrt(L / C)
RESISTANCES = (R / 2, R, 2 * R)
COLORS = ("#267d73", "#244c7a", "#b54838")


def write_csv(name, header, rows):
    with (RESULTS / name).open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


def save_figure(fig, name):
    fig.savefig(FIGURES / f"{name}.pdf")
    fig.savefig(FIGURES / f"{name}.png", dpi=180)
    plt.close(fig)


def interpolate_crossing(x, y, level):
    """Пересечения горизонтального уровня ломаной дискретного графика."""
    z = y - level
    exact = list(x[z == 0])
    indices = np.flatnonzero(z[:-1] * z[1:] < 0)
    roots = exact + [x[j] - z[j] * (x[j+1] - x[j]) / (z[j+1] - z[j])
                     for j in indices]
    return np.array(sorted(roots))


def rc_voltage(t, resistance=R, capacitance=C):
    return U0 * np.exp(-t / (resistance * capacitance))


def task_rc():
    tau = R * C
    t = np.linspace(0, 5 * tau, 1001)
    u = rc_voltage(t)
    tau_graph = float(interpolate_crossing(t, u, U0 / np.e)[0])
    half_graph = float(interpolate_crossing(t, u, U0 / 2)[0])
    write_csv("task1_rc.csv", ["t_s", "U_V"], zip(t, u))
    fig, ax = plt.subplots(figsize=(7.2, 4.4), layout="constrained")
    ax.plot(t * 1e3, u, color=COLORS[1], linewidth=1.8, label=r"$U_0e^{-t/(RC)}$")
    for time, voltage, color, label in (
        (tau_graph, U0 / np.e, COLORS[2], r"$U_0/e$; $t=RC$"),
        (half_graph, U0 / 2, COLORS[0], r"$U_0/2$; $t=RC\ln2$"),
    ):
        ax.hlines(voltage, 0, time * 1e3, colors=color, linestyles="--")
        ax.vlines(time * 1e3, 0, voltage, colors=color, linestyles="--")
        ax.scatter(time * 1e3, voltage, color=color, zorder=3, label=label)
    ax.set(xlabel="t, мс", ylabel="U, В", xlim=(0, 5 * tau * 1e3), ylim=(0, 10.5))
    ax.legend()
    save_figure(fig, "task1_rc")

    # Общая временная ось позволяет непосредственно сравнить скорости разряда.
    t = np.linspace(0, 5 * (2 * R) * C, 2001)
    curves = [rc_voltage(t, r) for r in RESISTANCES]
    doubled_c = rc_voltage(t, R, 2 * C)
    write_csv("task2_rc_parameters.csv", ["t_s", "U_R25_V", "U_R50_V", "U_R100_V", "U_C10uF_V"],
              zip(t, *curves, doubled_c))
    fig, ax = plt.subplots(figsize=(7.2, 4.4), layout="constrained")
    for r, values, color in zip(RESISTANCES, curves, COLORS):
        ax.plot(t * 1e3, values, color=color, label=f"R = {r:g} Ом, C = 5 мкФ")
    ax.plot(t * 1e3, doubled_c, "--", color="black", linewidth=1.1,
            label="R = 50 Ом, C = 10 мкФ")
    ax.set(xlabel="t, мс", ylabel="U, В", xlim=(0, t[-1] * 1e3), ylim=(0, 10.5))
    ax.legend()
    save_figure(fig, "task2_rc_parameters")
    return {"tau_s": tau, "tau_graph_s": tau_graph, "half_time_s": tau * np.log(2),
            "half_graph_s": half_graph, "U_at_5tau_V": float(rc_voltage(5*tau)),
            "tau_double_C_s": R * 2 * C,
            "double_C_curve_difference_V": float(np.max(np.abs(doubled_c - curves[2])))}


def free_rhs(t, state, resistance):
    q, current = state
    return (current, -(resistance * current + q / C) / L)


def positive_maximum(t, state, resistance):
    return state[1]


positive_maximum.direction = -1


def integrate_free(resistance, times, with_events=False):
    solution = solve_ivp(
        free_rhs, (0, float(times[-1])), (Q0, 0.0), args=(resistance,),
        method="DOP853", t_eval=times, rtol=1e-10, atol=(1e-14, 1e-12),
        max_step=T0 / 100, events=positive_maximum if with_events else None,
    )
    if not solution.success:
        raise RuntimeError(solution.message)
    return solution


def analytic_free(t, resistance):
    """Заряд и ток для трёх режимов при q(0)=Q0, i(0)=0."""
    gamma = resistance / (2 * L)
    if np.isclose(gamma, OMEGA0, rtol=1e-12, atol=0):
        exp = np.exp(-OMEGA0 * t)
        return Q0 * (1 + OMEGA0 * t) * exp, -Q0 * OMEGA0**2 * t * exp
    if gamma < OMEGA0:
        wd = np.sqrt(OMEGA0**2 - gamma**2)
        exp = np.exp(-gamma * t)
        q = Q0 * exp * (np.cos(wd * t) + gamma / wd * np.sin(wd * t))
        current = -Q0 * OMEGA0**2 / wd * exp * np.sin(wd * t)
        return q, current
    # Сумма убывающих экспонент не даёт переполнения cosh и sinh.
    kappa = np.sqrt(gamma**2 - OMEGA0**2)
    s1, s2 = -gamma + kappa, -gamma - kappa
    q = Q0 * ((gamma + kappa) * np.exp(s1*t) - (gamma - kappa) * np.exp(s2*t)) / (2*kappa)
    current = -Q0 * OMEGA0**2 * (np.exp(s1*t) - np.exp(s2*t)) / (2*kappa)
    return q, current


def task_free():
    gamma = R / (2 * L)
    wd = np.sqrt(OMEGA0**2 - gamma**2)
    td = 2 * np.pi / wd
    t = np.linspace(0, 6 * td, 6001)
    solution = integrate_free(R, t, with_events=True)
    q, current = solution.y
    qa, ia = analytic_free(t, R)
    # События i=0 с отрицательным направлением — положительные максимумы q.
    maxima = solution.t_events[0]
    maxima = maxima[maxima > td / 2]  # Начальную точку t=0 не используем.
    period_num = float(np.mean(np.diff(maxima)))
    energy = q**2 / (2*C) + L * current**2 / 2
    initial_energy = C * U0**2 / 2
    lost_energy = simpson(R * current**2, x=t)
    error_q = float(np.max(np.abs(q-qa)))
    error_i = float(np.max(np.abs(current-ia)))
    balance = float(abs(energy[-1] + lost_energy - initial_energy) / initial_energy)
    write_csv("task3_free.csv", ["t_s", "q_C", "i_A", "q_analytic_C", "i_analytic_A", "energy_J"],
              zip(t, q, current, qa, ia, energy))
    write_csv("task3_positive_maxima.csv", ["maximum_number", "t_s"], enumerate(maxima, 1))
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 6.0), sharex=True, layout="constrained")
    for ax, numeric, exact, scale, ylabel in (
        (axes[0], q, qa, 1e6, "q, мкКл"), (axes[1], current, ia, 1e3, "i, мА"),
    ):
        ax.plot(t*1e3, numeric*scale, color=COLORS[1], linewidth=1.6, label="Численное решение")
        ax.plot(t[::75]*1e3, exact[::75]*scale, "o", markersize=3, markerfacecolor="none",
                color=COLORS[2], label="Аналитическое решение")
        ax.axhline(0, color="0.5", linewidth=0.7)
        ax.set(ylabel=ylabel, xlim=(0, t[-1]*1e3))
    axes[0].legend()
    axes[1].set_xlabel("t, мс")
    save_figure(fig, "task3_free")
    return {"gamma_s_inv": gamma, "omega_d_rad_s": wd, "Td_s": td,
            "period_numerical_s": period_num, "T0_s": T0,
            "period_increase_percent": 100*(td/T0 - 1), "time_end_s": float(t[-1]),
            "max_q_error_C": error_q, "max_i_error_A": error_i,
            "energy_initial_J": initial_energy, "energy_balance_relative_error": balance}


def task_damping():
    t = np.linspace(0, 16 / OMEGA0, 4001)
    fig, ax = plt.subplots(figsize=(7.2, 4.6), layout="constrained")
    labels = (r"$R=0{,}5R_{кр}$: колебания", r"$R=R_{кр}$: критический",
              r"$R=2R_{кр}$: апериодический")
    table = []
    for multiplier, color, label in zip((0.5, 1.0, 2.0), COLORS, labels):
        resistance = multiplier * RCR
        solution = integrate_free(resistance, t)
        q, current = solution.y
        qa, ia = analytic_free(t, resistance)
        table.append({"R_over_Rcr": multiplier, "R_ohm": resistance,
                      "max_q_error_C": float(np.max(np.abs(q-qa))),
                      "max_i_error_A": float(np.max(np.abs(current-ia)))})
        write_csv(f"task4_damping_{multiplier:g}.csv", ["t_s", "q_C", "i_A", "q_analytic_C"],
                  zip(t, q, current, qa))
        ax.plot(t*1e3, q*1e6, color=color, label=label)
    ax.axhline(0, color="0.5", linewidth=0.7)
    ax.set(xlabel="t, мс", ylabel="q, мкКл", xlim=(0, t[-1]*1e3))
    ax.legend()
    save_figure(fig, "task4_damping")
    return {"Rcr_ohm": RCR, "cases": table}


def amplitude(omega, resistance):
    return U0 / np.hypot(resistance, omega*L - 1/(omega*C))


def phase(omega, resistance):
    # phi = phi_voltage - phi_current; i(t)=I0*sin(omega*t-phi).
    return np.arctan2(omega*L - 1/(omega*C), resistance)


def task_resonance():
    omega = np.linspace(0.4*OMEGA0, 1.8*OMEGA0, 4001)
    fig_amp, ax_amp = plt.subplots(figsize=(7.2, 4.6), layout="constrained")
    fig_phi, ax_phi = plt.subplots(figsize=(7.2, 4.6), layout="constrained")
    fig_width, ax_width = plt.subplots(figsize=(7.2, 4.8), layout="constrained")
    summary = []
    for resistance, color in zip(RESISTANCES, COLORS):
        current = amplitude(omega, resistance)
        phi = phase(omega, resistance)
        peak_index = np.argmax(current)
        omega_grid = float(omega[peak_index])
        optimum = minimize_scalar(lambda x: -amplitude(x*OMEGA0, resistance),
                                  bounds=(0.8, 1.2), method="bounded", options={"xatol": 1e-13})
        if not optimum.success:
            raise RuntimeError("Не удалось найти максимум резонансной кривой")
        omega_peak = float(optimum.x * OMEGA0)
        imax = float(amplitude(omega_peak, resistance))
        # Определяем две частоты линейной интерполяцией точек графика.
        crossings = interpolate_crossing(omega, current, imax/np.sqrt(2))
        if len(crossings) != 2:
            raise RuntimeError("Частотный диапазон не содержит две границы половинной мощности")
        w1, w2 = map(float, crossings)
        gamma = resistance/(2*L)
        w1_exact = np.hypot(OMEGA0, gamma) - gamma
        w2_exact = np.hypot(OMEGA0, gamma) + gamma
        width = w2-w1
        quality = OMEGA0*L/resistance
        summary.append({"R_ohm": resistance, "omega_grid_rad_s": omega_grid,
                        "omega_peak_rad_s": omega_peak, "omega_peak_relative_error": abs(omega_peak/OMEGA0-1),
                        "Imax_A": imax, "I_half_power_A": imax/np.sqrt(2), "Q": quality,
                        "omega1_graph_rad_s": w1, "omega2_graph_rad_s": w2,
                        "omega1_exact_rad_s": float(w1_exact), "omega2_exact_rad_s": float(w2_exact),
                        "width_graph_rad_s": width, "width_exact_rad_s": resistance/L,
                        "width_relative_error": abs(width/(resistance/L)-1),
                        "Q_from_graph": OMEGA0/width})
        write_csv(f"tasks5_7_frequency_R{resistance:g}.csv", ["omega_rad_s", "frequency_Hz", "I0_A", "phi_rad", "I0_over_Imax"],
                  zip(omega, omega/(2*np.pi), current, phi, current/imax))
        label = f"R = {resistance:g} Ом"
        ax_amp.plot(omega, current*1e3, color=color, label=label)
        ax_phi.plot(omega, np.rad2deg(phi), color=color, label=label)
        ax_width.plot(omega, current/imax, color=color, label=label)
        ax_width.scatter([w1, w2], [1/np.sqrt(2)]*2, color=color, s=30, zorder=3)
    for ax in (ax_amp, ax_phi, ax_width):
        ax.axvline(OMEGA0, color="0.4", linestyle=":", linewidth=1)
        ax.set(xlabel=r"$\omega$, рад/с", xlim=(omega[0], omega[-1]))
        ax.legend()
    ax_amp.set(ylabel=r"$I_0$, мА", ylim=(0, None))
    ax_phi.axhline(0, color="0.5", linewidth=0.7)
    ax_phi.set(ylabel=r"$\varphi=\varphi_U-\varphi_I$, градусы", ylim=(-90, 90))
    ax_width.axhline(1/np.sqrt(2), color="0.4", linestyle="--", label=r"$1/\sqrt{2}$")
    ax_width.set(ylabel=r"$I_0/I_{\max}$", ylim=(0, 1.06))
    ax_width.legend()
    save_figure(fig_amp, "task5_resonance")
    save_figure(fig_phi, "task6_phase")
    save_figure(fig_width, "task7_bandwidth")
    return summary


def number(value, decimals=3):
    return f"{value:.{decimals}f}".replace(".", "{,}")


def export_tex(rc, free, damping, resonance):
    base = resonance[1]
    values = {
        "TauMs": number(rc["tau_s"]*1e3), "TauGraphMs": number(rc["tau_graph_s"]*1e3, 6),
        "HalfMs": number(rc["half_time_s"]*1e3, 6), "HalfGraphMs": number(rc["half_graph_s"]*1e3, 6),
        "OmegaZero": number(OMEGA0), "FreqZero": number(OMEGA0/(2*np.pi)),
        "PeriodZeroMs": number(T0*1e3, 6), "GammaBase": number(free["gamma_s_inv"]),
        "OmegaDamped": number(free["omega_d_rad_s"]), "PeriodDampedMs": number(free["Td_s"]*1e3, 6),
        "PeriodNumericMs": number(free["period_numerical_s"]*1e3, 6),
        "PeriodIncrease": number(free["period_increase_percent"], 4),
        "CriticalR": number(RCR), "FreeTimeEndMs": number(free["time_end_s"]*1e3),
        "QualityBase": number(base["Q"], 4), "WidthBase": number(base["width_exact_rad_s"]),
        "VoltageReactive": number(base["Q"]*U0),
        "MaxWidthErrorPercent": number(100*max(v["width_relative_error"] for v in resonance), 5),
        "MaxPeakErrorPercent": number(100*max(v["omega_peak_relative_error"] for v in resonance), 7),
    }
    (RESULTS / "values.tex").write_text("% Generated by lab3.py.\n" + "\n".join(
        rf"\newcommand{{\{key}}}{{{value}}}" for key, value in values.items()) + "\n", encoding="utf-8")
    rows = [f"{r:g} & {number(r*C*1e3)} & {number(r*C*np.log(2)*1e3, 6)} " + r"\\"
            for r in RESISTANCES]
    (RESULTS / "rc_rows.tex").write_text("\n".join(rows)+"\n", encoding="utf-8")
    peak_rows = [f"{v['R_ohm']:g} & {number(v['omega_grid_rad_s'])} & {number(v['omega_peak_rad_s'])} & {number(v['Imax_A']*1e3, 2)} " + r"\\"
                 for v in resonance]
    (RESULTS / "resonance_rows.tex").write_text("\n".join(peak_rows)+"\n", encoding="utf-8")
    width_rows = [" & ".join([f"{v['R_ohm']:g}", number(v["Q"], 4),
                              number(v["omega1_graph_rad_s"]), number(v["omega2_graph_rad_s"]),
                              number(v["width_graph_rad_s"]), number(v["width_exact_rad_s"])]) + r" \\"
                  for v in resonance]
    (RESULTS / "bandwidth_rows.tex").write_text("\n".join(width_rows)+"\n", encoding="utf-8")


def main():
    RESULTS.mkdir(exist_ok=True)
    FIGURES.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "Times New Roman", "font.size": 12,
                         "axes.grid": True, "grid.alpha": 0.23, "axes.unicode_minus": False})
    rc = task_rc()
    free = task_free()
    damping = task_damping()
    resonance = task_resonance()
    export_tex(rc, free, damping, resonance)
    summary = {"variant": 4, "parameters_SI": {"R_ohm": R, "L_H": L, "C_F": C, "U0_V": U0},
               "omega0_rad_s": float(OMEGA0), "f0_Hz": float(OMEGA0/(2*np.pi)),
               "rc": rc, "free": free, "damping": damping, "resonance": resonance}
    (RESULTS / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
