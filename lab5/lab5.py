"""Запуск приложения: python lab5.py. Расчёты отчёта: python lab5.py --generate."""
import argparse


def main():
    parser = argparse.ArgumentParser(description="Лабораторная 5: дифракция электронов")
    parser.add_argument("--generate", action="store_true", help="сохранить графики и данные отчёта без окна")
    parser.add_argument("--seed", type=int, default=20261101, help="seed для воспроизводимой серии")
    args = parser.parse_args()
    if not 0 <= args.seed <= 2**32-1:
        parser.error("seed должен быть от 0 до 4294967295")
    if args.generate:
        import matplotlib
        matplotlib.use("Agg")
        from lab5_report import generate
        generate(args.seed)
    else:
        from lab5_app import run
        run(args.seed)


if __name__ == "__main__":
    main()
