# Materyx — ASAP Analyzer

**Materyx — ASAP Analyzer** (коротко **mx-asap**) — кроссплатформенная программа для **анализа и конвертации** данных из **текстовых отчётов** прибора [Micromeritics](https://www.micromeritics.com/) **ASAP** 2400.

**Назначение:** оценка **удельной поверхности, объёма и распределения пор** у **дисперсных и пористых** материалов (в т.ч. **контроль качества** продукции) по методу **низкотемпературной сорбции азота (БЭТ)**. Входом служат **экспортированные в виде plain-text** файлы.

## Ветки и релизы

- Ветки: **`main`**, **`dev`**, **`prod`**. PR в `main` / `dev` / `prod` и пуши в эти ветки запускают **тесты** (GitHub Actions).
- **Сборка** бинарников (Windows / Linux / macOS) и **GitHub Release** с зип-архивами — только при **пуше в `prod`**. Перед мерджем в `prod` увеличьте поле **`version`** в `pyproject.toml` в той же ветке, иначе релиз с тем же тегом `v…` не создастся. Повторный тот же `version` на GitHub уже существующего релиза — ошибка в workflow.

## Разработка

Python ≥ 3.11, зависимости — в `pyproject.toml`. Тесты: `pytest tests/`. Сборка одного бинарника: `pip install -r requirements-build.txt` и `pyinstaller --noconfirm packaging/mx-asap.spec` (нужен GUI/Qt на целевой ОС).

**Запуск (после `pip install .` или из исходников):**

```bash
mx-asap
```

Точка входа CLI: `python3 -m source` (см. `pyproject.toml`).
