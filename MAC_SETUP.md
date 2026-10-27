# Запуск лабораторных на MacBook M4 Pro

Для **сборки имеющихся `.tex` в PDF** нужны MacTeX, шрифты и все файлы
отчётов. Python требуется только для повторного расчёта таблиц и графиков.
PowerShell на Mac устанавливать не нужно: есть Bash-скрипты.

## 1. Перенести проект целиком

Скопируйте папку `physics` на Mac, например в `~/Projects/physics`.
Нужны `lab1`, `lab2`, `lab3`, корневой `build_pdf.sh` и этот файл.
Не переносите только `.tex`: отчёты используют внешние рисунки и таблицы.

| Лаба | Что требуется для сборки |
|---|---|
| lab1 | `lab1.tex` и все `task*.png` рядом с ним |
| lab2 | `lab2.tex`, `figures/`, `results/` |
| lab3 | `lab3.tex`, `figures/`, `results/` |

Скрипты `.py` и исходные данные нужны для пересчёта.
Windows-окружения `.venv`, временные `.tools` и каталоги `build` переносить
не требуется. Готовые PDF можно просто открыть на Mac без установки программ.

## 2. Один раз установить MacTeX и шрифты

1. Скачайте полный **MacTeX** с [официального сайта TeX Users Group](https://www.tug.org/mactex/mactex-download.html)
   и запустите установщик `.pkg`. Он работает нативно на Apple Silicon;
   отдельная версия для M4 и Rosetta не требуются. Полная поставка содержит
   XeLaTeX и используемые в отчётах пакеты.
2. Полностью закройте и снова откройте Terminal. Проверьте:

   ```bash
   xelatex --version
   ```

   Если команда не найдена, добавьте каталог MacTeX в текущую сессию:

   ```bash
   export PATH="/Library/TeX/texbin:$PATH"
   xelatex --version
   ```

   Чтобы сохранить настройку для стандартной оболочки zsh:

   ```bash
   echo 'export PATH="/Library/TeX/texbin:$PATH"' >> ~/.zprofile
   ```

   `/Library/TeX/texbin` — [официальный путь к активным программам MacTeX](https://www.tug.org/mactex/multipletexdistributions.html).
3. В приложении **«Шрифты» / Font Book** проверьте **Times New Roman**
   и **Consolas**. Первый нужен всем отчётам, второй — кодовым вставкам lab2
   и lab3. Если их нет, установите доступные вам файлы этих шрифтов,
   например из вашей установки Microsoft Office. Нужны обычное, полужирное,
   курсивное и полужирное курсивное начертания Times New Roman.
   Файлы `.ttf`/`.otf` открываются двойным щелчком → «Установить»:
   [инструкция Apple](https://support.apple.com/guide/font-book/fntbk1000/mac).

Если Consolas недоступен, для сборки на Mac можно заменить **только** строку
`\setmonofont{Consolas}` на `\setmonofont{Menlo}` в `lab2.tex` и `lab3.tex`,
предварительно проверив наличие Menlo в Font Book. Это меняет шрифт кода.
Основной `\setmainfont{Times New Roman}` оставьте: он требуется заданием.

## 3. Собрать PDF — Python не нужен

Откройте Terminal в папке проекта:

```bash
cd ~/Projects/physics
bash build_pdf.sh
```

Будут обновлены:

- `lab1/lab1.pdf`;
- `lab2/lab2.pdf`;
- `lab3/lab3.pdf`.

Одна выбранная работа:

```bash
bash build_pdf.sh 1
bash build_pdf.sh 2
bash build_pdf.sh 3
```

Либо из каталога соответствующей лабы: `bash build.sh`.
Скрипты выполняют два прохода XeLaTeX, проверяют ссылки и оглавление
(оно есть в lab2 и lab3), затем копируют итоговый PDF рядом с `.tex`.
Старые конфликтующие `.aux/.toc/.out` переносятся в `build/previous-root`.
У lab1 оглавления в исходнике нет — это нормально.

Открыть результат:

```bash
open lab1/lab1.pdf
open lab2/lab2.pdf
open lab3/lab3.pdf
```

## 4. Если нужно заново рассчитать таблицы и графики

Установите Python 3.13 или 3.14 для macOS с [python.org](https://www.python.org/downloads/macos/).
Официальный `universal2`-установщик работает нативно на Apple Silicon:
[документация Python](https://docs.python.org/3/using/mac.html).
После установки откройте новый Terminal.

Из корня проекта создайте **новое окружение на Mac**:

```bash
cd ~/Projects/physics
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r lab1/requirements.txt -r lab2/requirements.txt -r lab3/requirements.txt
```

Проверьте импорты и наличие шрифта для графиков:

```bash
python -c "import numpy, scipy, matplotlib, xlrd; print('Библиотеки установлены')"
python -c "from matplotlib.font_manager import findfont; print(findfont('Times New Roman', fallback_to_default=False))"
```

Пересчитайте нужные работы и соберите отчёты:

```bash
python lab1/lab1.py
python lab2/lab2.py
python lab3/lab3.py
bash build_pdf.sh
```

При последующих запусках достаточно `source .venv/bin/activate`, затем
команд расчёта и сборки. Python создаёт рисунки, CSV и LaTeX-вставки;
**сам PDF создаёт XeLaTeX**. Исходные Excel/PDF не меняются.
Дополнительные `pypdf` и PyMuPDF для основных расчётов не нужны.

## 5. Если что-то не работает

| Сообщение/ситуация | Что сделать |
|---|---|
| `xelatex: command not found` | Открыть новый Terminal; проверить PATH из шага 2 |
| `fontspec: font ... cannot be found` | Установить указанный шрифт; перезапустить сборку |
| `fontspec requires XeTeX or LuaTeX` | Использовать `xelatex`, а не `pdflatex` |
| `File ... not found` | Проверить перенос рисунков/таблиц и запуск через скрипт |
| `ModuleNotFoundError` | Активировать `.venv` и установить `requirements.txt` |
| Ошибка сертификата при скачивании через Python | Выполнить `Install Certificates.command` из папки установленного Python в `/Applications` |
| Старый PDF в просмотрщике | Закрыть и снова открыть файл; проверить время его изменения |
| Пустое оглавление lab2/lab3 | Запустить `bash build_pdf.sh 2 3`, а не копировать результат неудачной сборки |

При ошибке XeLaTeX читайте **первое сообщение об ошибке** в
`labN/build/labN.log`. Скрипт не заменяет итоговый PDF при неуспешной сборке.
Если используете редактор, выберите XeLaTeX и каталог вывода `build`.
