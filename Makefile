.PHONY: install run test lint smoke clean

install:
	python -m pip install -r requirements.txt

run:
	python -m app.main

test:
	pytest -q

lint:
	python -m compileall app

smoke:
	python smoke_test.py

clean:
	rm -rf .pytest_cache __pycache__ app/__pycache__ \
	       app/bot/__pycache__ app/db/__pycache__ \
	       app/domain/__pycache__ app/services/__pycache__ \
	       tests/__pycache__
