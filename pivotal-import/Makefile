.PHONY : clean delete delete-apply import import-apply initialize lint setup setup-dev test

clean:
	./clean

delete:
	pipenv run python delete_imported_entities.py

delete-apply:
	pipenv run python delete_imported_entities.py --apply

import: initialize
	pipenv run python pivotal_import.py

import-apply: initialize
	pipenv run python pivotal_import.py --apply

initialize: setup
	pipenv run python initialize.py

lint:
	./lint

setup:
	./setup

setup-dev:
	pipenv install --dev

test:
	./test
