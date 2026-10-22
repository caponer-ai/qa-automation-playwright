# QA Automation: Playwright + pytest

Набір автотестів і парсер на Python + Playwright. Працює на публічних демо-сайтах, які створені саме для тренування автоматизації.

| Набір | Сайт | Що перевіряється |
|---|---|---|
| `ui` | [saucedemo.com](https://www.saucedemo.com) | логін (успіх, заблокований користувач, помилкові дані), доступ без логіну, вихід, каталог, 4 сортування, кошик, повний checkout з перевіркою суми і податку, валідація форми |
| `api` | [restful-booker](https://restful-booker.herokuapp.com) | CRUD бронювання через Playwright `APIRequestContext`, токен авторизації, 403 без токена, 404 після видалення |
| `scraper` | [books.toscrape.com](https://books.toscrape.com) | парсер каталогу з пагінацією, розбір ціни, рейтингу і наявності, експорт у CSV/JSON |

27 тестів.

## Структура

```
pages/          Page Object: локатори і дії сторінок окремо від тестів
scraper/        парсер books.toscrape.com (Playwright, CLI)
tests/ui        UI-тести
tests/api       API-тести
tests/scraper   тести парсера
conftest.py     спільні фікстури: логін один раз на воркер, base_url, data-test локатори
```

## Оптимізація прогону

- **Паралельний запуск** через pytest-xdist: `-n 4` скорочує прогін з 24.5 до 10.6 с (локальний замір, Windows, 27 тестів).
- **Логін один раз на воркер**: фікстура `auth_cookies` логіниться через форму один раз і передає cookie сесії в кожен тест. Форму логіну перевіряють лише тести логіну.
- **Стабільні локатори** через атрибут `data-test`, без CSS-ланцюжків і XPath.
- **Веб-асерти** `expect(...)` чекають стану самі, без `sleep`.
- **Парсер не вантажить картинки й шрифти** (`page.route` → `abort`).
- **Перезапуск** нестабільних зовнішніх API (`pytest-rerunfailures`) лише там, де падіння через мережу чужого сервера.

## Діагностика падінь

При падінні зберігаються скріншот і `trace.zip` у `test-results/`. У CI вони завантажуються як артефакт. Відкрити trace: `playwright show-trace test-results/<тест>/trace.zip`.

## Запуск

```bash
pip install -r requirements.txt
playwright install chromium

pytest -n 4              # усе паралельно
pytest -m ui             # лише UI
pytest -m api            # лише API
pytest --headed -m ui    # з видимим браузером

python -m scraper.books --pages 5 --out books.csv
```

Docker:

```bash
docker build -t qa-automation .
docker run --rm qa-automation
```

## CI

GitHub Actions: три набори (`ui`, `api`, `scraper`) паралельно в матриці, окремий job збирає Docker-образ і проганяє тести в ньому. Плюс щотижневий запуск за розкладом, щоб помітити зміни на демо-сайтах.
