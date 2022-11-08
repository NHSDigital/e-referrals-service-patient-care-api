#!/usr/bin/env python3
"""
populate_placeholder.py

Reads an openapi spec on stdin and substitutes placeholders with values stored in dictionary,
then prints it on stdout.
"""
import sys


def main():
    """Main entrypoint"""
    substitutes_dict = {
        "[[HYPERLINK_A001]]": "[Retrieve referral requests for a patient](#api-Default-a001-retrieve-referral-requests)",
        "[[HYPERLINK_A002]]": "[Retrieve heathcare service](#api-Default-a002-retrieve-healthcare-service)",
        "[[HYPERLINK_ERS]]": "[e-Referral Service (e-RS)](https://digital.nhs.uk/services/e-referral-service)",
        "[[HYPERLINK_NHS_LOGIN]]": "[NHS login](https://digital.nhs.uk/services/nhs-login/nhs-login-for-partners-and-developers)",
        "[[HYPERLINK_PATIENT_ACCESS]]": "[Patient access](https://digital.nhs.uk/developer/guides-and-documentation/security-and-authorisation#user-restricted-apis)",
        "[[HYPERLINK_ERS_FHIR_API]]": "[e-Referral Service - FHIR API](https://digital.nhs.uk/developer/api-catalogue/e-referral-service-fhir#top)",
        "[[HYPERLINK_SERVICE_LEVELS]]": "[service levels](https://digital.nhs.uk/developer/guides-and-documentation/reference-guide#service-levels)",
        "[[HYPERLINK_RESTFUL]]": "[RESTful](https://digital.nhs.uk/developer/guides-and-documentation/api-technologies-at-nhs-digital#basic-rest)",
        "[[HYPERLINK_FHIR]]": "[FHIR](https://digital.nhs.uk/developer/guides-and-documentation/api-technologies-at-nhs-digital#fhir)",
        "[[HYPERLINK_FHIR_UK_CORE]]": "[FHIR UK Core](https://digital.nhs.uk/services/fhir-uk-core)",
        "[[HYPERLINK_FHIR_UK_CORE_STU1]]": "[fhir.r4.ukcore.stu1](https://simplifier.net/packages/fhir.r4.ukcore.stu1)",
        "[[HYPERLINK_FHIR_R4]]": "[FHIR R4 (v4.0.1)](https://hl7.org/fhir/r4/)",
        "[[HYPERLINK_STABLE]]": "[stable](https://digital.nhs.uk/developer/guides-and-documentation/reference-guide#statuses)",
        "[[HYPERLINK_IN_PROD_BETA]]": "[In production, beta](https://digital.nhs.uk/developer/guides-and-documentation/reference-guide#statuses)",
        "[[HYPERLINK_PDS]]": "[Personal Demographic Service (PDS)](https://digital.nhs.uk/developer/api-catalogue/personal-demographics-service-fhir)",
        "[[HYPERLINK_PROOFING_LEVEL]]": "[identity proofing level](https://nhsconnect.github.io/nhslogin/vectors-of-trust/)",
        "[[HYPERLINK_NETWORK_ACCESS]]": "[Network access for APIs](https://digital.nhs.uk/developer/guides-and-documentation/network-access-for-apis)",
        "[[HYPERLINK_USER_RESTRICTED]]": "[user-restricted](https://digital.nhs.uk/developer/guides-and-documentation/security-and-authorisation#user-restricted-apis)",
        "[[HYPERLINK_USER_RESTRICTED_SEPARATE_AUTHENTICATION]]": "[User-restricted RESTful API - NHS login separate authentication and authorisation]"
        "(https://digital.nhs.uk/developer/guides-and-documentation/security-and-authorisation/user-restricted-restful-apis-nhs-login-separate-authentication-and-authorisation)",
        "[[HYPERLINK_USER_RESTRICTED_COMBINED_AUTHENTICATION]]": "[User-restricted RESTful API - NHS login combined authentication and authorisation]"
        "(https://digital.nhs.uk/developer/guides-and-documentation/security-and-authorisation/user-restricted-restful-apis-nhs-login-combined-authentication-and-authorisation)",
        "[[HYPERLINK_INTERNAL_USE_ONLY]]": "[internal use only](https://digital.nhs.uk/developer/guides-and-documentation/reference-guide#statuses)",
        "[[HYPERLINK_CAPABILITIES]]": "[capabilities](http://hl7.org/fhir/R4/http.html#capabilities)",
        "[[HYPERLINK_LIBRARIES_AND_SDKS]]": "[libraries and SDKs](https://digital.nhs.uk/developer/guides-and-documentation/api-technologies-at-nhs-digital#fhir-libraries-and-sdks)",
        "[[HYPERLINK_HSCN]]": "[Health and Social Care Network (HSCN)](https://digital.nhs.uk/services/health-and-social-care-network)",
        "[[HYPERLINK_MANAGE_REFERRAL]]": "[NHS Manage Your Referral](https://www.nhs.uk/nhs-services/hospitals/book-an-appointment/)",
        "[[HYPERLINK_PC_AGGREGATOR]]": "[Patient Care Aggregator](https://digital.nhs.uk/developer/api-catalogue/patient-care-aggregator-fhir)",
        "[[HYPERLINK_IN_PROD_BETA_INTERNAL]]": "[in production, beta but internal](https://digital.nhs.uk/developer/guides-and-documentation/reference-guide#statuses)",
    }

    data = sys.stdin.read()

    for key, value in substitutes_dict.items():
        data = data.replace(key, value)

    sys.stdout.write(data)
    sys.stdout.close()


if __name__ == "__main__":
    main()
