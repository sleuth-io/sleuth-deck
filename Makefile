.PHONY: run tunnel client help venv db db-migrate db-makemigrations format

SHELL := /bin/bash

include .secrets
export

# Help system from https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.DEFAULT_GOAL := help

help:
	@cat $(MAKEFILE_LIST)
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(firstword $(MAKEFILE_LIST)) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'


venv: ## Create python venv
	python3.12 -m venv venv
	venv/bin/pip install --upgrade pip setuptools wheel
	venv/bin/pip install pip-tools
	venv/bin/pip-compile
	venv/bin/pip install -r requirements.txt
	
format: ## Format the code
	venv/bin/black src
	venv/bin/reorder-python-imports --py12-plus `find src -name "*.py"` || venv/bin/black src --target-version py312

run: ## Run the app
	cd src && ../venv/bin/python -m sleuthdeck.cli work.py
