const apiproxy_revision = context.getVariable('apiproxy.revision');

const healthcheck_status_code = context.getVariable('healthcheckResponse.status.code');
const healthcheck_request_url = context.getVariable('healthcheckRequest.url');
const healthcheck_failed = context.getVariable("servicecallout.ServiceCallout.CallHealthcheckEndpoint.failed");

function json_tryparse(raw) {
    try {
        return JSON.parse(raw);
    }
    catch (e) {
        return raw;
    }
}

const healthcheck_content = json_tryparse(context.getVariable('healthcheckResponse.content'));
const healthcheck_status = (healthcheck_status_code/100 === 2) ? "pass" : "fail";
const timeout = (healthcheck_status_code === null && healthcheck_failed) ? "true" : "false";

const final_status = (healthcheck_status !== "pass") ? "fail" : "pass";

const resp = {
    "status" : final_status,
    "version" : "{{ DEPLOYED_VERSION }}" ,
    "revision" : apiproxy_revision,
    "releaseId" : "{{ RELEASE_RELEASEID }}",
    "commitId": "{{ SOURCE_COMMIT_ID }}",
    "checks" : {
        "healthcheck" : {
            "status": healthcheck_status,
            "timeout" : timeout,
            "responseCode" : healthcheck_status_code,
            "outcome": healthcheck_content,
            "links" : {"self": healthcheck_request_url}
        }
    }
};

context.setVariable("status.response", JSON.stringify(resp));
context.setVariable("response.content", JSON.stringify(resp));
context.setVariable("response.header.Content-Type", "application/json");
