"""Физическая модель и статистика; не зависят от графического интерфейса.

Использованы округлённые константы из tasks.pdf. Координаты экрана — мм,
напряжение на входе — кВ, длина волны возвращается в ангстремах.
Модель кинематическая: положения колец физические, их веса — учебный выбор.
"""
from dataclasses import asdict, dataclass
from pathlib import Path
import csv
import json
import math

import numpy as np


H = 6.63e-34
M = 0.911e-30
E = 1.602e-19
C = 2.998e8
CAMERA_MM = 757.0
LATTICE_A = 2.87
C1 = H * 1e10 / math.sqrt(2*M*E*1000)
C2 = E * 1000 / (2*M*C**2)

# Четвёртое кольцо записано как второй порядок семейства (110),
# что эквивалентно первому порядку отражения (220).
HKL = ((1, 1, 0), (2, 0, 0), (2, 1, 1), (1, 1, 0), (3, 1, 0), (2, 2, 2), (3, 2, 1))
ORDERS = np.array([1, 1, 1, 2, 1, 1, 1])
SPACINGS_A = np.array([LATTICE_A/math.sqrt(sum(i*i for i in hkl)) for hkl in HKL])
# Нулевой канал — прямой пучок. Сумма вероятностей всех 8 каналов равна 1.
# Веса не являются рассчитанными интенсивностями реального железа.
CHANNEL_PROBABILITIES = np.array([0.35, 0.18, 0.13, 0.10, 0.08, 0.065, 0.05, 0.045])
CONDITIONAL_PROBABILITIES = CHANNEL_PROBABILITIES[1:] / CHANNEL_PROBABILITIES[1:].sum()
VOLTAGES_KV = (30, 37, 47, 61, 83, 120)
DEFAULT_SEED = 20261101


def finite_number(value, name, low, high):
    """Принимаем точку или десятичную запятую; не подменяем неверный ввод нулями."""
    try:
        number = float(str(value).strip().replace(",", "."))
    except (ValueError, TypeError):
        raise ValueError(f"{name}: введите число") from None
    if not math.isfinite(number) or not low <= number <= high:
        raise ValueError(f"{name}: допустимо от {low:g} до {high:g}")
    return number


def integer_number(value, name, low, high):
    number = finite_number(value, name, low, high)
    if number != int(number):
        raise ValueError(f"{name}: требуется целое число")
    return int(number)


def voltage_variable(voltage_kv):
    """X(V)=1/sqrt[V*(1+C2*V)], V в кВ; именно эту ось требует упражнение 2."""
    v = np.asarray(voltage_kv, dtype=float)
    if not np.isfinite(v).all() or np.any(v <= 0):
        raise ValueError("Ускоряющее напряжение должно быть конечным и положительным")
    return 1/np.sqrt(v*(1+C2*v))


def wavelength_a(voltage_kv):
    # h/p; p²=2*m*e*V*(1+e*V/(2*m*c²)). C1,C2 уже учитывают кВ и Å.
    return C1 * voltage_variable(voltage_kv)


def ring_radii_mm(voltage_kv):
    # Малые углы: R=L*tan(2theta) ≈ L*n*lambda/d.
    return CAMERA_MM * float(wavelength_a(voltage_kv)) * ORDERS / SPACINGS_A


@dataclass(frozen=True)
class Configuration:
    voltage_kv: float = 40.0
    seed: int = DEFAULT_SEED
    radial_sigma_mm: float = 0.22
    center_sigma_mm: float = 0.65

    def __post_init__(self):
        finite_number(self.voltage_kv, "Напряжение, кВ", 1, 300)
        integer_number(self.seed, "Seed", 0, 2**32-1)
        finite_number(self.radial_sigma_mm, "Ширина кольца, мм", 0.001, 1)
        finite_number(self.center_sigma_mm, "Ширина прямого пучка, мм", 0.001, 2)


class ElectronSimulation:
    """Независимые попадания с азимутально симметричной плотностью.

    Каждому электрону выделено ровно 4 случайных числа. Поэтому изменение
    размера порций, темпа и пауз НЕ меняет последовательность при данном seed.
    Масштаб вообще не входит в физическое состояние модели.
    """
    def __init__(self, config=None):
        self.config = config or Configuration()
        self.rng = np.random.default_rng(self.config.seed)
        self.points = np.empty((0, 3), dtype=float)  # x_mm, y_mm, номер канала 0...7

    def add(self, count):
        count = integer_number(count, "Количество электронов", 0, 1_000_000)
        if len(self.points)+count > 1_000_000:
            raise ValueError("В одной серии поддерживается до 1 000 000 электронов")
        u = self.rng.random((count, 4))
        channel = np.searchsorted(np.cumsum(CHANNEL_PROBABILITIES), u[:, 0])
        phi = 2*np.pi*u[:, 1]
        # Box–Muller: нормальная случайная величина для радиального размытия.
        z = np.sqrt(-2*np.log(np.maximum(u[:, 2], np.finfo(float).tiny))) * np.cos(2*np.pi*u[:, 3])
        centers = np.r_[0.0, ring_radii_mm(self.config.voltage_kv)]
        radial = np.maximum(0.0, centers[channel]+self.config.radial_sigma_mm*z)
        central = channel == 0
        radial[central] = self.config.center_sigma_mm*np.sqrt(-2*np.log(np.maximum(u[central, 2], np.finfo(float).tiny)))
        new = np.column_stack((radial*np.cos(phi), radial*np.sin(phi), channel))
        self.points = np.concatenate((self.points, new))
        return new

    @property
    def total(self):
        return len(self.points)

    def counts(self):
        return np.bincount(self.points[:, 2].astype(int), minlength=8)

    def history(self, step=25):
        """k_j/k при k=sum(k1...k7), НЕ k_j/k0. При k=0 доля неопределена."""
        step = integer_number(step, "Шаг статистики", 5, 50)
        if not self.total:
            return np.empty((0, 4))
        locations = np.unique(np.r_[np.arange(step, self.total+1, step), self.total])
        channels = self.points[:, 2].astype(int)
        diffracted = np.cumsum(channels != 0)[locations-1]
        columns = [locations, diffracted]
        for ring in (1, 2):
            hits = np.cumsum(channels == ring)[locations-1]
            fractions = np.full(len(locations), np.nan)
            np.divide(hits, diffracted, out=fractions, where=diffracted != 0)
            columns.append(fractions)
        return np.column_stack(columns)

    def save(self, filename):
        data = {"schema": "electron-lab-v1", "config": asdict(self.config),
                "points": self.points.tolist(), "rng_state": self.rng.bit_generator.state}
        Path(filename).write_text(json.dumps(data, ensure_ascii=False, allow_nan=False), encoding="utf-8")

    @classmethod
    def load(cls, filename):
        path = Path(filename)
        if path.stat().st_size > 160_000_000:
            raise ValueError("Слишком большой файл серии")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("schema") != "electron-lab-v1":
                raise ValueError("Неизвестный формат серии")
            config_data = data["config"]
            # Явно приводим и проверяем типы данных из внешнего JSON.
            config = Configuration(
                finite_number(config_data["voltage_kv"], "Напряжение", 1, 300),
                integer_number(config_data["seed"], "Seed", 0, 2**32-1),
                finite_number(config_data["radial_sigma_mm"], "Ширина кольца", 0.001, 1),
                finite_number(config_data["center_sigma_mm"], "Ширина центра", 0.001, 2))
            points = np.asarray(data["points"], dtype=float)
            if points.size == 0:
                points = np.empty((0, 3))
            if points.ndim != 2 or points.shape[1] != 3 or len(points) > 1_000_000 or not np.isfinite(points).all():
                raise ValueError("Некорректный массив координат")
            if np.any(points[:, 2] != np.floor(points[:, 2])) or np.any((points[:, 2] < 0) | (points[:, 2] > 7)):
                raise ValueError("Некорректный номер канала")
            if np.max(np.abs(points[:, :2]), initial=0) > 10_000:
                raise ValueError("Координаты вне допустимого диапазона")
            simulation = cls(config)
            if data["rng_state"].get("bit_generator") != "PCG64":
                raise ValueError("Неизвестный генератор случайных чисел")
            simulation.rng.bit_generator.state = data["rng_state"]
            simulation.points = points
            return simulation
        except (KeyError, TypeError, IndexError, OverflowError) as error:
            raise ValueError("Повреждённый файл серии") from error

    def export_csv(self, filename):
        write_csv(filename, ["electron", "x_mm", "y_mm", "channel_0_direct_1_7_rings"],
                  ((i+1, *point) for i, point in enumerate(self.points)))


def write_csv(filename, header, rows):
    with Path(filename).open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


def measured_radii(simulation):
    """Средние радиусы в непересекающихся кольцевых областях.

    Для оценки используем координаты, не скрытые номера каналов. Границы
    областей выбираются посередине между ожидаемыми кольцами модели.
    Возвращаем R, стандартную ошибку среднего и число точек в каждом кольце.
    """
    centers = ring_radii_mm(simulation.config.voltage_kv)
    boundaries = np.r_[centers[0]/2, (centers[:-1]+centers[1:])/2,
                        centers[-1]+(centers[-1]-centers[-2])/2]
    radii = np.hypot(simulation.points[:, 0], simulation.points[:, 1])
    result = []
    for j in range(7):
        values = radii[(radii >= boundaries[j]) & (radii < boundaries[j+1])]
        if len(values) < 2:
            result.append({"ring": j+1, "radius_mm": None, "sem_mm": None, "count": len(values)})
        else:
            result.append({"ring": j+1, "radius_mm": float(values.mean()),
                           "sem_mm": float(values.std(ddof=1)/np.sqrt(len(values))), "count": len(values)})
    return result


def miller_candidates(squared_sum):
    """Перебор h>=k>=l>=0 для кубического кристалла, не готовый ответ по номеру кольца."""
    # Для первых пяти колец S<=10. Ограничение защищает интерфейс от
    # огромного перебора при заведомо неверном вводе радиуса.
    if not 1 <= squared_sum <= 200:
        return []
    limit = int(math.sqrt(squared_sum))
    return [(h, k, l) for h in range(limit+1) for k in range(h+1) for l in range(k+1)
            if h*h+k*k+l*l == squared_sum and h+k+l > 0]


def analyze_structure(radii_mm, voltage_kv=30):
    if len(radii_mm) != 5:
        raise ValueError("Нужны радиусы первых пяти колец")
    voltage_kv = finite_number(voltage_kv, "Напряжение, кВ", 1, 300)
    radii = np.array([finite_number(value, f"Радиус кольца {i+1}, мм", 0.01, 2000)
                      for i, value in enumerate(radii_mm)])
    if np.any(np.diff(radii) <= 0):
        raise ValueError("Радиусы колец должны строго возрастать")
    wave = float(wavelength_a(voltage_kv))
    rows = []
    for j, radius in enumerate(radii):
        order = int(ORDERS[j])
        spacing = order*CAMERA_MM*wave/radius
        squared_sum = (LATTICE_A/spacing)**2
        rounded = int(np.floor(squared_sum+0.5))
        candidates = miller_candidates(rounded)
        allowed = [hkl for hkl in candidates if sum(hkl) % 2 == 0]
        warning = []
        if abs(squared_sum-rounded) > 0.25:
            warning.append("S далеко от целого: проверьте радиус или порядок")
        if rounded > 200:
            warning.append("S > 200: вне диапазона поиска для первых колец, проверьте радиус")
        elif not allowed:
            warning.append("Нет допустимых индексов для ОЦК Fe")
        rows.append({"ring": j+1, "order": order, "radius_mm": float(radius),
                     "spacing_a": float(spacing), "squared_sum": float(squared_sum),
                     "rounded_sum": rounded, "candidates": candidates, "allowed_bcc": allowed,
                     "warning": "; ".join(warning)})
    return rows


def voltage_experiment(count=20_000, seed=DEFAULT_SEED):
    """Серия упражнения 2; R определён по точкам, не скопирован из формулы."""
    count = integer_number(count, "Число электронов на напряжение", 100, 200_000)
    rows = []
    for i, voltage in enumerate(VOLTAGES_KV):
        simulation = ElectronSimulation(Configuration(voltage, (seed+i+10) % 2**32))
        simulation.add(count)
        measured = measured_radii(simulation)
        if any(measured[j]["radius_mm"] is None for j in (1, 2)):
            raise ValueError("Недостаточно попаданий во второе или третье кольцо")
        rows.append({"voltage_kv": voltage, "X": float(voltage_variable(voltage)),
                     "lambda_a": float(wavelength_a(voltage)),
                     "R2_mm": measured[1]["radius_mm"], "R3_mm": measured[2]["radius_mm"],
                     "sem2_mm": measured[1]["sem_mm"], "sem3_mm": measured[2]["sem_mm"]})
    x = np.array([row["X"] for row in rows])
    fits = []
    for ring in (2, 3):
        y = np.array([row[f"R{ring}_mm"] for row in rows])
        slope, intercept = np.linalg.lstsq(np.column_stack((x, np.ones_like(x))), y, rcond=None)[0]
        residual = y-(slope*x+intercept)
        fits.append({"ring": ring, "slope": float(slope), "intercept_mm": float(intercept),
                     "R2": float(1-np.sum(residual**2)/np.sum((y-y.mean())**2)),
                     "slope_theory": float(CAMERA_MM*C1/SPACINGS_A[ring-1])})
    return {"count_each": count, "seed": seed, "rows": rows, "fits": fits}


def structure_experiment(count=30_000, seed=DEFAULT_SEED):
    simulation = ElectronSimulation(Configuration(30, (seed+100) % 2**32))
    simulation.add(count)
    measured = measured_radii(simulation)[:5]
    if any(row["radius_mm"] is None for row in measured):
        raise ValueError("Недостаточно попаданий для измерения первых пяти колец")
    # Запись с шагом 0.01 мм имитирует конечную точность отсчёта, не идеальный ответ.
    radii = [round(row["radius_mm"], 2) for row in measured]
    return {"count": count, "rows": analyze_structure(radii), "measurements": measured}
