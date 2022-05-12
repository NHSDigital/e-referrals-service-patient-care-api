#!/usr/bin/env python3

import sys
import json

"""
Accepts WayFinder OpenAPI specification input from "standard in".
Adds AWS API Gateway integrations to Lambda backend
Output passed to "standard out"
"""


ServiceRequestIntegration = {
    "type": "AWS_PROXY",
    "httpMethod": "POST",
    "uri": "${service_request_lambda_invoke_arn}",
    "passthroughBehavior": "when_no_match",
    "payloadFormatVersion": "1.0"
}

HealthcareServiceIntegration = {
    "type": "AWS_PROXY",
    "httpMethod": "POST",
    "uri": "${healthcare_service_lambda_invoke_arn}",
    "passthroughBehavior": "when_no_match",
    "payloadFormatVersion": "1.0"
}


def main():
    """Main entrypoint"""
    openapi_spec = json.load(sys.stdin)

    paths = openapi_spec["paths"]
    paths["/FHIR/R4/ServiceRequest"]["get"]["x-amazon-apigateway-integration"] = ServiceRequestIntegration
    paths["/FHIR/R4/HealthcareService/{id}"]["get"]["x-amazon-apigateway-integration"] = HealthcareServiceIntegration

    sys.stdout.write(json.dumps(openapi_spec, indent=2))
    sys.stdout.close()


if __name__ == "__main__":
    main()
