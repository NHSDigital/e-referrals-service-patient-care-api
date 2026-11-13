SHELL=/bin/bash -euo pipefail

install-python:
	poetry lock
	poetry install

install-node:
	npm install
	cd sandbox && npm install

.git/hooks/pre-commit:
	cp scripts/pre-commit .git/hooks/pre-commit
	chmod u+x .git/hooks/pre-commit

install: install-node install-python .git/hooks/pre-commit

lint: copy-examples
	npm run lint
	find . -name '*.py' -not -path '**/.venv/*' | xargs poetry run flake8
	poetry check
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

PROXYGEN_ENV ?= internal-dev
PROXYGEN_BASE_PATH ?= e-referrals-service-patient-care-api-proxygen
INCLUDE_PATHS ?= false

proxygen-spec: publish
	poetry run python scripts/build_proxygen_spec.py $(PROXYGEN_ENV) --base-path $(PROXYGEN_BASE_PATH) \
		$(if $(filter true,$(INCLUDE_PATHS)),--include-paths)

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
	cp -R macros dist

test:
#	this target should be used for local unit tests ..  runs as part of the build pipeline
	make --no-print-directory -C sandbox test

smoketest:
#	this target is for end to end smoketests this would be run 'post deploy' to verify an environment is working
	poetry run pytest -v --junitxml=smoketest-report.xml -s -m smoketest
integrationtest:
#	this target is for end to end integration tests this would be run 'post deploy' to verify the environment has integration with e-RS
	poetry run pytest -v tests/integration --junitxml=tests/ers-test-integration-report.xml
proxygen-test:
#	this target tests an instance deployed by Proxygen (internal-dev by default), settings are in tests/proxygen/conftest.py
	poetry run pytest -v -rs tests/proxygen --junitxml=proxygen-test-report.xml

setup-environment:
	@if [ -e /usr/bin/yum ]; then \
		scripts/rhel_setup_environment.sh; \
	elif [ -e /opt/homebrew/bin/brew ]; then \
		scripts/macos_setup_environment.sh; \
	elif [ -e /usr/local/bin/brew ]; then \
		echo "Intel based Macs are not currently supported."; \
	elif [ -e /usr/bin/apt ]; then \
		scripts/ubuntu_setup_environment.sh; \
	else \
		echo "Environment not Mac or RHEL or Ubuntu"; \
	fi

clean-environment:
	@if [ -e /usr/bin/yum ]; then \
		scripts/rhel_clean_environment.sh; \
	elif [ -e /opt/homebrew/bin/brew ]; then \
		scripts/macos_clean_environment.sh; \
	elif [ -e /usr/local/bin/brew ]; then \
		echo "Intel based Macs are not currently supported."; \
	elif [ -e /usr/bin/apt ]; then \
    	scripts/ubuntu_clean_environment.sh; \
	else \
		echo "Environment not Mac or RHEL or Ubuntu"; \
	fi

.PHONY: setup-environment clean-environment
