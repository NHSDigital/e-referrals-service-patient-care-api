SHELL := /bin/bash
dirname := $(notdir $(patsubst %/,%,$(CURDIR)))

list:
	@grep '^[^#[:space:]].*:' Makefile

build:
	docker build .

clean:
	rm -rf ./node_modules

install:
	npm install --dev

update:
	npm update

test:
	NODE_ENV=test npx mocha --reporter spec

test-report:
	NODE_ENV=test npx mocha --reporter mocha-junit-reporter --reporter-options mochaFile=../../reports/tests/$(dirname).xml || true
