const _ALLOWED_VECTORS_OF_TRUST = ["P9.Cp.Cd", "P9.Cp.Ck", "P9.Cm"]

function is_supported() {
    const current_vot = context.getVariable("jwt.DecodeJWT.DecodeIdToken.claim.vot");
    return _ALLOWED_VECTORS_OF_TRUST.indexOf(current_vot) > -1;
}

context.setVariable("apigee.has_required_vot", is_supported());