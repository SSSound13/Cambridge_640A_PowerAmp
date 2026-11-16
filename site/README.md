# GitHub Pages / Сайт проекта

Сайт собирается из README, BOM и руководств в `doc/` и `production/`. Для русского и английского языков используются отдельные страницы с переключателем RU / EN. Генератор сохраняет ссылки на файлы проекта и производственный ZIP.

Локальная сборка: установить `markdown2`, выполнить `python scripts/build_site.py`. Результат — `_site/`. В GitHub Actions эта команда выполняется автоматически после изменений в main; готовый каталог публикуется через Pages artifact.

Для первого запуска в Settings → Pages выбрать Source: **GitHub Actions**. Настройка Pages требует административных прав и разрешения Pages write у используемого токена. После включения повторно запустить workflow **Publish project documentation**.

## English

The site is built from the repository README, BOM and guides under `doc/` and `production/`. Russian and English pages have a RU / EN switch. Document links and fabrication ZIP downloads are preserved.

Install `markdown2` and run `python scripts/build_site.py` to build `_site/`. The GitHub Actions workflow runs the same command on changes to main, uploads a Pages artifact and deploys it.

For the first deployment, select **GitHub Actions** as the source under Settings → Pages, then run **Publish project documentation**. Enabling Pages requires administrative access and Pages write permission on the token performing that operation.
