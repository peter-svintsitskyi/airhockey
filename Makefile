linters:
	flake8 airhockey
	flake8 airhockey_tests
	(cd airhockey && mypy --config-file=../mypy.ini .)
	(cd airhockey_tests && mypy --config-file=../mypy.ini .)
