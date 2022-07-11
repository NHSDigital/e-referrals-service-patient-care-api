from enum import Enum


class RenamedHeader(Enum):
    CORRELATION_ID = ("x-correlation-id", "nhsd-correlation-id")

    @property
    def original(self):
        return self.value[0]

    @property
    def renamed(self):
        return self.value[1]


class InternalHeader(Enum):
    """
    Headers populated by APIM policies and are internal for the communication with the backend
    """
    BASE_URL = "nhsd-ers-network-baseurl"
    APPLICATION_ID = "nhsd-application-id"
    NHS_NUMBER = "nhsd-nhs-number"
    ACCESS_TOKEN = "nhsd-access-token"

    @property
    def name(self):
        return self.value
