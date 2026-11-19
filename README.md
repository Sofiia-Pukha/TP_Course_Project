# SIPL Toolkit
Пуха Софія, ТК-31
Проєктна робота з дисципліни «Теорія програмування».

## Обрані завдання

| ID | Завдання | Бали |
|---|---|---|
| CORE-01 | Формальна граматика (`grammar/sipl.lark`, `grammar/sipl.ebnf`), 15 позитивних і 16 негативних тестів | 0.5 |
| CORE-02 | Парсер, власні AST-вузли з `SourceSpan`, діагностика синтаксичних помилок | 1.5 |
| CORE-03 | Інтерпретатор: стан, присвоювання, `;`, `if`, `while`, `begin/end`, `skip`, ліміт кроків | 2.0 |
| VIS-01 | Дерево синтаксичного виводу: текст, JSON, DOT; перевірка за листками | 1.5 |
| SEM-01 | Автоматична побудова семантичного терму (правила `sem_P/S/A/B`) | 2.0 |
| SEM-02 | Обчислення терму на стані та покрокове пояснення (формули `AF_*`) | 2.0 |
| REL-01 | CI (GitHub Actions): тести + перевірка покриття | 0.5 |
| | **Разом** | **10.0** |

Командний рядок (`sipl ...`) - допоміжний засіб для запуску, окремо як CORE-05 не заявляється.

## Встановлення

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Потрібен Python 3.9+. Без `[dev]` (lark, coverage) все працює, ці пакети потрібні лише для тестів.

## Використання

```bash
sipl parse examples/power.sipl                          # AST
sipl tree examples/power.sipl --check                   # дерево виводу + перевірка за листками
sipl tree examples/power.sipl --format json             # або dot
sipl term examples/power.sipl --rules                   # семантичний терм і застосовані правила
sipl run examples/power.sipl --state X=5,Y=2            # інтерпретатор
sipl eval examples/power.sipl --state X=5,Y=2 --steps   # обчислення терму з поясненням
```

Те саме без встановлення: `PYTHONPATH=src python -m sipl <команда> ...`

DOT можна перетворити на картинку: `sipl tree examples/power.sipl --format dot > t.dot && dot -Tsvg t.dot -o t.svg` (потрібен Graphviz).

Приклад виводу `sipl term examples/power.sipl`:

```
AS_R(1) · WH(S2(gr, Y⇒, 0), AS_R(S2(mult, R⇒, X⇒)) · AS_Y(S2(sub, Y⇒, 1)))
```

Як бібліотека:

```python
import sipl
from sipl.semantics import build_term
from sipl.evaluator import evaluate

src = open("examples/power.sipl").read()
program = sipl.parse(src)
term = build_term(program, src)
print(evaluate(term, {"X": 5, "Y": 2}).state)   # {'X': 5, 'Y': 0, 'R': 25}
```

## Приклади

У `examples/`: `power` (x^y), `div` (x ÷ y), `sum_arith` (2+4+...+2n), `parity`, `fib`,
`max` (з `if`), `divisible`, а також `loop_forever` (нескінченний цикл) і `broken` (синтаксична помилка).

## Тести

```bash
python -m unittest discover -t . -s tests -v
coverage run -m unittest discover -t . -s tests && coverage report --include="src/sipl/*"
```

Тести перевіряють: граматику (позитивні/негативні), пріоритети, позиції в тексті,
інтерпретатор, golden-терми (терм для x^y збігається з практикумом), узгодженість
інтерпретатора й обчислення терму на всіх прикладах, дерево виводу, CLI.
Тест на `grammar/sipl.lark` виконується, якщо встановлено `lark`.

## Структура

```
grammar/      sipl.lark, sipl.ebnf
src/sipl/     lexer, parser, parse_tree, ast, interpreter, semantics, evaluator, visualization, cli
examples/     програми SIPL
tests/        unittest
docs/         grammar.md (синтаксис і пріоритети), theory.md (теорія, на яку спирається реалізація)
```

Потік даних: текст -> токени -> дерево виводу (`parser`) -> AST (`ast.build_ast`) ->
семантичний терм (`semantics.build_term`) -> кінцевий стан (`evaluator.evaluate`).
Інтерпретатор виконує AST напряму і використовується для перевірки терму.

## Обмеження

- Мова строго за БНФ курсу: оператори порівняння лише `=` та `>`; `>=`, `<` треба виражати через `¬` та `∨`.
- Тіло `while` та гілки `if` - один оператор; кілька операторів беруться в `begin ... end`.
- Числа цілі без обмеження розміру. Ліміт кроків за замовчуванням 100000; при його перевищенні
  інтерпретатор повідомляє про помилку, а обчислення терму повертає «не визначено» (⊥).
- Змінна без значення в стані - помилка (в семантиці це невизначеність).
- Коментарів у мові немає (їх немає в БНФ).
- Завершуваність довільної програми не перевіряється (це алгоритмічно нерозв'язна задача), лише ліміт кроків.
