var isValid = false;
var b64decoded = null;
try{
  b64decoded = JSON.parse(context.getVariable("targetIdentifierDecoded"));

  if (b64decoded != null){
    var system = b64decoded.system
    var value = b64decoded.value

    if (system === "urn:ietf:rfc:3986" && value === "2b3b21fd-fe9f-403c-9682-10b8d8a4eaf3"){
        isValid = true;
    }
  }
}catch (e) {
  isValid = false;
}
context.setVariable("targetIdentifierValid", isValid);
