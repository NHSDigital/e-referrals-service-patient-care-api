# e-referrals-service-patient-care-api

![Build](https://github.com/NHSDigital/e-referrals-service-patient-care-api/workflows/Build/badge.svg?branch=master)

This is a specification for the *e-referrals-service-patient-care-api* API.

* `specification/` This [Open API Specification](https://swagger.io/docs/specification/about/) describes the endpoints, methods and messages exchanged by the API. Use it to generate interactive documentation; the contract between the API and its consumers.
* `sandbox/` This NodeJS application implements a mock implementation of the service. Use it as a back-end service to the interactive documentation to illustrate interactions and concepts. It is not intended to provide an exhaustive/faithful environment suitable for full development and testing.
* `scripts/` Utilities helpful to developers of this specification.
* `proxies/` Live (connecting to another service) and sandbox (using the sandbox container) Apigee API Proxy definitions.

Consumers of the API will find developer documentation on the [NHS Digital Developer Hub](https://digital.nhs.uk/developer).

## Contributing
Contributions to this project are welcome from anyone, providing that they conform to the [guidelines for contribution](https://github.com/NHSDigital/e-referrals-service-patient-care-api/blob/master/CONTRIBUTING.md) and the [community code of conduct](https://github.com/NHSDigital/e-referrals-service-patient-care-api/blob/master/CODE_OF_CONDUCT.md).

New branches and pull requests should always be created from the **develop** branch.

All Pull Requests **must** be approved and merged only by one of the members of the [e-RS team](https://github.com/orgs/NHSDigital/teams/e-referrals).

Merging to the **master** branch is part of our release process and should only ever be done by one of the members of the [e-RS team](https://github.com/orgs/NHSDigital/teams/e-referrals).

### Licensing
This code is dual licensed under the MIT license and the OGL (Open Government License). Any new work added to this repository must conform to the conditions of these licenses. In particular this means that this project may not depend on GPL-licensed or AGPL-licensed libraries, as these would violate the terms of those libraries' licenses.

The contents of this repository are protected by Crown Copyright (C).

## Development

### Requirements
* make
* nodejs + npm/yarn
* [poetry](https://github.com/python-poetry/poetry)

### Environment setup
Currently, automation for setting up the right environment is only available for machines based on RedHatEnterpriseLinux (RHEL).
Running the following will ensure your environment is ready for development.
It will install [pyenv](https://github.com/pyenv/pyenv), Python 3.10.8 and its dependencies (yum), create a virtual environment (named apigee), and ensure poetry is installed under it.
```
$ make setup-environment
```
>Activating apigee is now done by the file .python-version, so cd'ing into the repository directory will suffice to use the virtual environment.

If you wish to remove all changes made by setup-environment, you can run the following:
```
$ make clean-environment
```
> This will erase your ~/.pyenv directory, where pyenv stores the different Python versions, and will revert ~/.bashrc and ~./bash_profile. You may want to logout/login for changes to take effect.

### Install
```
$ make install
```

#### Updating hooks
You can install some pre-commit hooks to ensure you can't commit invalid spec changes by accident. These are also run
in CI, but it's useful to run them locally too.

```
$ make install-hooks
```

### Environment Variables
Various scripts and commands rely on environment variables being set. These are documented with the commands.

:bulb: Consider using [direnv](https://direnv.net/) to manage your environment variables during development and maintaining your own `.envrc` file - the values of these variables will be specific to you and/or sensitive.

### Make commands
There are `make` commands that alias some of this functionality:
 * `lint` -- Lints the spec and code
 * `publish` -- Outputs the specification as a **single file** into the `build/` directory
 * `serve` -- Serves a preview of the specification in human-readable format
 * `setup-environment` -- installs python env for the project
 * `clean-environment` -- clears the setup-environment

### Testing
Each API and team is unique. We encourage you to use a `test/` folder in the root of the project, and use whatever testing frameworks or apps your team feels comfortable with. It is important that the URL your test points to be configurable. We have included some stubs in the Makefile for running tests.

### VS Code Plugins

 * [openapi-lint](https://marketplace.visualstudio.com/items?itemName=mermade.openapi-lint) resolves links and validates entire spec with the 'OpenAPI Resolve and Validate' command
 * [OpenAPI (Swagger) Editor](https://marketplace.visualstudio.com/items?itemName=42Crunch.vscode-openapi) provides sidebar navigation


### Emacs Plugins

 * [**openapi-yaml-mode**](https://github.com/esc-emacs/openapi-yaml-mode) provides syntax highlighting, completion, and path help

### Redocly CLI

> [Redocly CLI](https://redocly.com/redocly-cli) *Bring versatile OpenAPI validation, linting & bundling to your command line (and VS Code!) with this open-source Swiss knife.*

Redocly CLI does the lifting for the following npm scripts:

 * `test` -- Lints the definition
 * `publish` -- Outputs the specification as a **single file** into the `build/` directory
 * `serve` -- Serves a preview of the specification in human-readable format

(Workflow detailed in a [post](https://developerjack.com/blog/2018/maintaining-large-design-first-api-specs/) on the *developerjack* blog.)

:bulb: The `publish` command is useful when uploading to Apigee which requires the spec as a single file.

### Caveats

#### Swagger UI
Swagger UI unfortunately doesn't correctly render `$ref`s in examples, so use `speccy serve` instead.

#### Apigee Portal
The Apigee portal will not automatically pull examples from schemas, you must specify them manually.

### Platform setup

As currently defined in your `proxies` folder, your proxies do pretty much nothing.
Telling Apigee how to connect to your backend requires a *Target Server*, which you should call named `e-referrals-service-patient-care-api-target`.
Our *Target Servers* defined in the [api-management-infrasture](https://github.com/NHSDigital/api-management-infrastructure) repository.

:bulb: For Sandbox-running environments (`test`) these need to be present for successful deployment but can be set to empty/dummy values.
