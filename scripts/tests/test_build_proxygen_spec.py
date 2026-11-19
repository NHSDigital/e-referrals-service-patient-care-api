import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import build_proxygen_spec  # noqa: E402

PUBLISHED = {
    "openapi": "3.0.0",
    "info": {"title": "Patient Care - FHIR API", "version": "1.0.0"},
    "servers": [
        {"url": "https://int.api.service.nhs.uk/e-referrals-service-patient-care-api"},
        {"url": "https://api.service.nhs.uk/e-referrals-service-patient-care-api"},
    ],
    "paths": {
        "/FHIR/R4/ServiceRequest": {
            "get": {"security": [{"bearerAuth": []}], "responses": {}}
        }
    },
    "components": {
        "securitySchemes": {"bearerAuth": {"type": "http", "scheme": "bearer"}},
        "schemas": {"Thing": {"type": "object"}},
    },
}
OVERLAY = {"x-nhsd-apim": {"temporary": False, "monitoring": False, "target": None}}


def build(include_paths, env="internal-dev", base_path="pca-proxygen"):
    return build_proxygen_spec.build(PUBLISHED, OVERLAY, env, base_path, include_paths)


def test_sets_proxygen_openapi_version_single_server_and_overlay():
    spec = build(include_paths=False)

    assert spec["openapi"] == "3.0.3"
    assert spec["servers"] == [
        {"url": "https://internal-dev.api.service.nhs.uk/pca-proxygen"}
    ]
    assert spec["x-nhsd-apim"] == OVERLAY["x-nhsd-apim"]


def test_without_paths_removes_paths_and_security_schemes():
    spec = build(include_paths=False)

    assert spec["paths"] == {}
    assert "securitySchemes" not in spec["components"]
    assert spec["components"]["schemas"] == PUBLISHED["components"]["schemas"]


def test_with_paths_maps_bearer_auth_to_proxygen_nhs_login_p9():
    spec = build(include_paths=True)

    operation = spec["paths"]["/FHIR/R4/ServiceRequest"]["get"]
    assert operation["security"] == [{"nhs-login-p9": []}]
    assert spec["components"]["securitySchemes"] == {
        "nhs-login-p9": {
            "$ref": "https://proxygen.ptl.api.platform.nhs.uk/components/securitySchemes/nhs-login-p9"
        }
    }


def test_prod_platform_environments_use_prod_proxygen_and_hosts():
    spec = build(include_paths=True, env="prod", base_path="a_b")

    assert spec["servers"] == [{"url": "https://api.service.nhs.uk/a/b"}]
    ref = spec["components"]["securitySchemes"]["nhs-login-p9"]["$ref"]
    assert ref.startswith("https://proxygen.prod.api.platform.nhs.uk/")


def test_does_not_mutate_published_spec():
    before = json.dumps(PUBLISHED, sort_keys=True)
    build(include_paths=True)
    build(include_paths=False)
    assert json.dumps(PUBLISHED, sort_keys=True) == before


def test_rejects_base_path_with_slash(tmp_path):
    published = tmp_path / "spec.json"
    published.write_text(json.dumps(PUBLISHED))

    with pytest.raises(SystemExit, match="_"):
        build_proxygen_spec.main(
            ["internal-dev", "--base-path", "a/b", "--input", str(published)]
        )
