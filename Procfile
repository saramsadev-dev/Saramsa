backend: cd backend && if exist venv\\Scripts\\python.exe (venv\\Scripts\\python.exe -u manage.py runserver 127.0.0.1:8000) else (python -u manage.py runserver 127.0.0.1:8000)
celery: cd backend && if exist venv\\Scripts\\python.exe (venv\\Scripts\\python.exe -u -m celery -A apis worker -l info) else (python -u -m celery -A apis worker -l info)
celery-ops: cd backend && if exist venv\\Scripts\\python.exe (venv\\Scripts\\python.exe -u -m celery_ops serve -A apis --host 0.0.0.0 --port 9800) else (python -u -m celery_ops serve -A apis --host 0.0.0.0 --port 9800)
frontend: cd saramsa-ai && npm run dev
