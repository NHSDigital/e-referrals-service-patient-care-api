SHELL=/bin/bash -euo pipefail

install-python:
	poetry install

install-node:
	npm install
	cd sandbox && npm install

.git/hooks/pre-commit:
	cp scripts/pre-commit .git/hooks/pre-commit

install: install-node install-python .git/hooks/pre-commit

lint: copy-examples
	npm run lint
	find . -name '*.py' -not -path '**/.venv/*' | xargs poetry run flake8
	@printf "\nLinting passed.\n\n"

clean: 
	rm -rf build
	rm -rf dist
	rm -rf specification/components/examples

publish: clean copy-examples
	mkdir -p build
	npm run publish 2> /dev/null
	poetry run python scripts/validate_oas_examples.py

publish-aws: clean copy-examples
	mkdir -p build
	npm run publish-aws 2> /dev/null

publish-all: clean copy-examples
	mkdir -p build
	npm run publish 2> /dev/null
	npm run publish-aws 2> /dev/null

serve:
	npm run serve

check-licenses:
	npm run check-licenses
	scripts/check_python_licenses.sh

copy-examples:
	scripts/copy_examples_from_sandbox.sh

format:
	poetry run black **/*.py

start-sandbox:
	cd sandbox && npm run start

build-proxy:
	scripts/build_proxy.sh

_dist_include="pytest.ini poetry.lock poetry.toml pyproject.toml Makefile build/. tests"

release: clean publish build-proxy
	mkdir -p dist
	for f in $(_dist_include); do cp -r $$f dist; done
	cp ecs-proxies-deploy.yml dist/ecs-deploy-sandbox.yml
	cp ecs-proxies-deploy.yml dist/ecs-deploy-internal-qa-sandbox.yml
	cp ecs-proxies-deploy.yml dist/ecs-deploy-internal-dev-sandbox.yml

test:
#	this target should be used for local unit tests ..  runs as part of the build pipeline
	make --no-print-directory -C sandbox test

smoketest:
#	this target is for end to end smoketests this would be run 'post deploy' to verify an environment is working
	poetry run pytest -v --junitxml=smoketest-report.xml -s -m smoketest

setup-environment:
	@if [ -e /usr/bin/yum ]; then \
		scripts/rhel_setup_environment.sh; \
	elif [ -e /usr/local/bin/brew ]; then \
		echo "TODO is Mac"; \
	else \
		echo "Environment not Mac or RHEL"; \
	fi

clean-environment:
	@if [ -e /usr/bin/yum ]; then \
		scripts/rhel_clean_environment.sh; \
	elif [ -e /usr/local/bin/brew ]; then \
		echo "TODO is Mac"; \
	else \
		echo "Environment not Mac or RHEL"; \
	fi

.PHONY: setup-environment clean-environment
