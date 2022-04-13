SHELL := /bin/bash
dirname := $(notdir $(patsubst %/,%,$(CURDIR)))

list:
	@grep '^[^#[:space:]].*:' Makefile

build:
	docker build -t e-referrals-service-patient-care-api-sandbox .

run:
	docker run -p 9000:9000 e-referrals-service-patient-care-api-sandbox:latest

clean:
	rm -rf ./node_modules
	docker stop $$(docker ps -a | awk '$$2 ~ /e-referrals-service-patient-care-api-sandbox/ {print $$1}') || /bin/true
	docker rm $$(docker ps -a | awk '$$2 ~ /e-referrals-service-patient-care-api-sandbox/ {print $$1}') || /bin/true
	docker rmi e-referrals-service-patient-care-api-sandbox || /bin/true

install:
	npm install --dev

update:
	npm update

test:
	NODE_ENV=test npx mocha --reporter spec

test-report:
	NODE_ENV=test npx mocha --reporter mocha-junit-reporter --reporter-options mochaFile=../../reports/tests/$(dirname).xml || true
