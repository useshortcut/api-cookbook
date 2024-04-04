.PHONY : clean initialize lint setup setup-dev test

clean:
	rm -f data/states.csv data/users.csv data/shortcut_workflows.csv config.json

initialize:
	pipenv run python initialize.py

import: initialize
	pipenv run python pivotal_import.py

lint:
	./lint

setup:
	./setup

setup-dev:
	./setup --dev

test:
	./test
