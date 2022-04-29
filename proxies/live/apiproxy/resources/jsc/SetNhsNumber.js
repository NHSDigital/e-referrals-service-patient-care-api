var id_token_nhs_number = context.getVariable('jwt.DecodeJWT.DecodeIdToken.claim.nhs_number');
context.setVariable('apigee.request.nhs_number', id_token_nhs_number);