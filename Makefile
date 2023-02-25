pip-tools:
	pip install pip-tools --upgrade

update: pip-tools
	pip-compile --resolver=backtracking --generate-hashes --allow-unsafe requirements.in
	pip-sync requirements.txt

install: pip-tools
	pip-sync requirements.txt

linters:
	flake8 airhockey
	flake8 airhockey_tests
	(cd airhockey && mypy --config-file=../mypy.ini .)
	(cd airhockey_tests && mypy --config-file=../mypy.ini .)

run-video:
	python -m airhockey video

run-capture:
	python -m airhockey capture

env:
	python3.11 -m venv airhockey-env
