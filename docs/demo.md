# Demo media

Capture a short demo for the README:

1. `pip install -e .[test] && python manage.py migrate && python manage.py seed_corpus data/words.csv`
2. `python manage.py runserver`
3. Open http://127.0.0.1:8000/search/
4. Type `py`, `da`, `tr` — show ranked suggestions and keyboard navigation
5. Save a GIF or PNG as `docs/demo.gif` (or `docs/demo.png`) and link from README

Until media is added, the architecture diagram in [`architecture.md`](architecture.md) serves as the visual overview.
