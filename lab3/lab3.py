"""Вариант 4. Моделирование RC- и RLC-цепей.

Запуск: python lab3.py. Все вычисления проводятся в СИ;
миллисекунды, микрокулоны и миллиамперы используются только на графиках.
"""

from pathlib import Path
import csv
import json

import matplotlib

# Рисунки записываются в файлы без интерактивных окон.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import simpson, solve_ivp
from scipy.optimize import minimize_scalar


# Относительные пути считаются от скрипта: можно запускать из любого каталога.
ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
# Вариант 4: Ом, Гн, Ф, В. 180 мГн=0.18 Гн; 5 мкФ=5e-6 Ф.
R, L, C, U0 = 50.0, 180e-3, 5e-6, 10.0
# Q0 — начальный заряд, не добротность Q; OMEGA0 — угловая частота в рад/с.
Q0 = C * U0
OMEGA0 = 1 / np.sqrt(L * C)
T0 = 2 * np.pi / OMEGA0
RCR = 2 * np.sqrt(L / C)
# Эти R нужны для RC и резонанса; в задании 4 сопротивления другие: доли RCR.
RESISTANCES = (R / 2, R, 2 * R)
COLORS = ("#267d73", "#244c7a", "#b54838")


def write_csv(name, header, rows):
    with (RESULTS / name).open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


def save_figure(fig, name):
    # PDF — векторная версия для отчёта; PNG — для быстрого просмотра.
    fig.savefig(FIGURES / f"{name}.pdf")
    fig.savefig(FIGURES / f"{name}.png", dpi=180)
    plt.close(fig)


def interpolate_crossing(x, y, level):
    """Пересечения горизонтального уровня ломаной дискретного графика."""
    # Пересечение уровня y=level эквивалентно нулю z=y-level.
    z = y - level
    # Точное попадание в узел обрабатывается отдельно от смены знака.
    exact = list(x[z == 0])
    # Отрицательное произведение означает разные знаки в соседних узлах.
    indices = np.flatnonzero(z[:-1] * z[1:] < 0)
    # Между ними считаем кривую прямой: x*=xj-zj*dx/dz.
    roots = exact + [x[j] - z[j] * (x[j+1] - x[j]) / (z[j+1] - z[j])
                     for j in indices]
    return np.array(sorted(roots))


def rc_voltage(t, resistance=R, capacitance=C):
    # Точное решение RC*U'+U=0, U(0)=U0; exp применяется ко всему массиву t.
    return U0 * np.exp(-t / (resistance * capacitance))


def task_rc():
    # Задание 1: tau — спад в e раз, tau*ln(2) — спад в два раза.
    tau = R * C
    t = np.linspace(0, 5 * tau, 1001)
    u = rc_voltage(t)
    # Из графика ищем пересечения, не подставляем в ответ известные времена.
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

    # Задание 2. Общая ось покрывает 5 постоянных времени самой медленной кривой.
    t = np.linspace(0, 5 * (2 * R) * C, 2001)
    curves = [rc_voltage(t, r) for r in RESISTANCES]
    # (R,2C) и (2R,C) имеют одинаковое произведение RC и одинаковое U(t).
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
    # Задание 3: система первого порядка вместо L*q''+R*q'+q/C=0.
    # state=(q,i), а возвращаемый вектор=(dq/dt,di/dt).
    # i=dq/dt; при начальном разряде q убывает, поэтому ток отрицателен.
    q, current = state
    return (current, -(resistance * current + q / C) / L)


def positive_maximum(t, state, resistance):
    # Событие — нуль i. Параметры t и resistance нужны сигнатуре solve_ivp.
    return state[1]


# Отбираем переход i от плюса к минусу: q в этот момент имеет максимум.
# Минимумы тоже дают i=0, но имеют противоположное направление перехода.
positive_maximum.direction = -1


def integrate_free(resistance, times, with_events=False):
    # DOP853 выбирает внутренний шаг адаптивно; t_eval — точки выдачи решения.
    # rtol ограничивает относительную ошибку; atol задаёт шкалу около нуля.
    # Для q и i абсолютные допуски разные, поскольку различаются их единицы.
    solution = solve_ivp(
        free_rhs, (0, float(times[-1])), (Q0, 0.0), args=(resistance,),
        method="DOP853", t_eval=times, rtol=1e-10, atol=(1e-14, 1e-12),
        max_step=T0 / 100, events=positive_maximum if with_events else None,
    )
    # Если интегратор не завершился, не строим график частичного результата.
    if not solution.success:
        raise RuntimeError(solution.message)
    return solution


def analytic_free(t, resistance):
    """Заряд и ток для трёх режимов при q(0)=Q0, i(0)=0."""
    gamma = resistance / (2 * L)
    # Сравниваем с допуском, поскольку RCR вычислено с округлением float.
    if np.isclose(gamma, OMEGA0, rtol=1e-12, atol=0):
        # Критический режим: кратный корень, поэтому перед exp есть (1+omega0*t).
        exp = np.exp(-OMEGA0 * t)
        return Q0 * (1 + OMEGA0 * t) * exp, -Q0 * OMEGA0**2 * t * exp
    if gamma < OMEGA0:
        # Колебательный режим; синусная добавка обеспечивает i(0)=0.
        wd = np.sqrt(OMEGA0**2 - gamma**2)
        exp = np.exp(-gamma * t)
        q = Q0 * exp * (np.cos(wd * t) + gamma / wd * np.sin(wd * t))
        current = -Q0 * OMEGA0**2 / wd * exp * np.sin(wd * t)
        return q, current
    # Апериодический режим: корни s1,s2 вещественные и отрицательные.
    # Сумма убывающих экспонент не даёт переполнения cosh и sinh.
    kappa = np.sqrt(gamma**2 - OMEGA0**2)
    s1, s2 = -gamma + kappa, -gamma - kappa
    q = Q0 * ((gamma + kappa) * np.exp(s1*t) - (gamma - kappa) * np.exp(s2*t)) / (2*kappa)
    current = -Q0 * OMEGA0**2 * (np.exp(s1*t) - np.exp(s2*t)) / (2*kappa)
    return q, current


def task_free():
    # Свободная частота wd ниже omega0; характерный период Td длиннее T0.
    gamma = R / (2 * L)
    wd = np.sqrt(OMEGA0**2 - gamma**2)
    td = 2 * np.pi / wd
    # Показываем шесть затухающих периодов, что заведомо больше пяти T0.
    t = np.linspace(0, 6 * td, 6001)
    solution = integrate_free(R, t, with_events=True)
    # solution.y[0] — массив зарядов, solution.y[1] — массив токов.
    q, current = solution.y
    qa, ia = analytic_free(t, R)
    # События i=0 с отрицательным направлением — положительные максимумы q.
    maxima = solution.t_events[0]
    maxima = maxima[maxima > td / 2]  # Начальную точку t=0 не используем.
    # diff берёт интервалы максимум-максимум: это полный период, не полупериод.
    period_num = float(np.mean(np.diff(maxima)))
    # W = энергия конденсатора + энергия катушки. Потери мощности равны R*i².
    energy = q**2 / (2*C) + L * current**2 / 2
    initial_energy = C * U0**2 / 2
    # simpson численно интегрирует мощность по времени и даёт потери энергии.
    lost_energy = simpson(R * current**2, x=t)
    error_q = float(np.max(np.abs(q-qa)))
    error_i = float(np.max(np.abs(current-ia)))
    # Проверка W(конец)+тепловые потери=W(начало), нормированная на W(начало).
    balance = float(abs(energy[-1] + lost_energy - initial_energy) / initial_energy)
    write_csv("task3_free.csv", ["t_s", "q_C", "i_A", "q_analytic_C", "i_analytic_A", "energy_J"],
              zip(t, q, current, qa, ia, energy))
    write_csv("task3_positive_maxima.csv", ["maximum_number", "t_s"], enumerate(maxima, 1))
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 6.0), sharex=True, layout="constrained")
    for ax, numeric, exact, scale, ylabel in (
        (axes[0], q, qa, 1e6, "q, мкКл"), (axes[1], current, ia, 1e3, "i, мА"),
    ):
        # Только при рисовании переводим секунды в мс, Кл в мкКл, А в мА.
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
    # Задание 4: меняем R относительно критического, сохраняя L,C и q(0),i(0).
    t = np.linspace(0, 16 / OMEGA0, 4001)
    fig, ax = plt.subplots(figsize=(7.2, 4.6), layout="constrained")
    labels = (r"$R=0{,}5R_{кр}$: колебания", r"$R=R_{кр}$: критический",
              r"$R=2R_{кр}$: апериодический")
    table = []
    for multiplier, color, label in zip((0.5, 1.0, 2.0), COLORS, labels):
        # Это примерно 189.737, 379.473, 758.947 Ом, а не 25,50,100 Ом.
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
    # Задание 5: установившийся ток, не переходный процесс после включения.
    # hypot(R,X)=sqrt(R²+X²) — модуль импеданса, X=omega*L-1/(omega*C).
    return U0 / np.hypot(resistance, omega*L - 1/(omega*C))


def phase(omega, resistance):
    # phi = phi_voltage - phi_current; i(t)=I0*sin(omega*t-phi).
    # При X<0 фаза отрицательна: ток опережает напряжение; при X>0 отстаёт.
    return np.arctan2(omega*L - 1/(omega*C), resistance)


def task_resonance():
    # Задания 5–7: одна частотная сетка для амплитуды, фазы и ширины полосы.
    omega = np.linspace(0.4*OMEGA0, 1.8*OMEGA0, 4001)
    fig_amp, ax_amp = plt.subplots(figsize=(7.2, 4.6), layout="constrained")
    fig_phi, ax_phi = plt.subplots(figsize=(7.2, 4.6), layout="constrained")
    fig_width, ax_width = plt.subplots(figsize=(7.2, 4.8), layout="constrained")
    summary = []
    for resistance, color in zip(RESISTANCES, COLORS):
        current = amplitude(omega, resistance)
        phi = phase(omega, resistance)
        # argmax даёт индекс на сетке; истинный максимум может лежать между узлами.
        peak_index = np.argmax(current)
        omega_grid = float(omega[peak_index])
        # Максимизируем I, минимизируя -I; x=omega/omega0 — безразмерная частота.
        # Не подставляем omega0 в качестве численного ответа заранее.
        optimum = minimize_scalar(lambda x: -amplitude(x*OMEGA0, resistance),
                                  bounds=(0.8, 1.2), method="bounded", options={"xatol": 1e-13})
        if not optimum.success:
            raise RuntimeError("Не удалось найти максимум резонансной кривой")
        omega_peak = float(optimum.x * OMEGA0)
        imax = float(amplitude(omega_peak, resistance))
        # Уровень Imax/sqrt(2), поскольку мощность пропорциональна квадрату тока.
        # Определяем две частоты линейной интерполяцией точек графика.
        crossings = interpolate_crossing(omega, current, imax/np.sqrt(2))
        # Для измерения ширины нужны обе границы внутри выбранного диапазона.
        if len(crossings) != 2:
            raise RuntimeError("Частотный диапазон не содержит две границы половинной мощности")
        w1, w2 = map(float, crossings)
        gamma = resistance/(2*L)
        # Аналитические границы получаются из |omega*L-1/(omega*C)|=R.
        # Их вычисляем отдельно: это проверка интерполяции, не её входные данные.
        w1_exact = np.hypot(OMEGA0, gamma) - gamma
        w2_exact = np.hypot(OMEGA0, gamma) + gamma
        width = w2-w1
        # Q=omega0*L/R=omega0/DeltaOmega; увеличение R расширяет полосу.
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
    # Русская десятичная запятая в математическом режиме LaTeX.
    return f"{value:.{decimals}f}".replace(".", "{,}")


def export_tex(rc, free, damping, resonance):
    # Сохраняем числа и строки таблиц: отчёт подключает их через input.
    # Это оформление результатов, физические расчёты находятся в task_*.
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
    # Последовательность: RC -> свободный RLC -> три режима -> резонанс -> экспорт.
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
