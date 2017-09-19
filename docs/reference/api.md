# Indigo Service API

2017/07/21

## Installing Service

The sourcecode for the Indigo service is in the GitHub repo
```bash
https://github.com/indigo-d/bluepea
```

To install the code clone the repo as follows:

```bash
$ git clone https://github.com/indigo-d/bluepea
```

This will create a bluepea directory. The source code is written in Python and
can be installed with Python3.6 or later using pip. First navigate to the directory
with the bluepea directory and then install with pip3.


```bash
$ pip3 install -e bluepea
```

The Indigo micro web service is run via the bluepead  (bluepea daemon) that is
installed with the pip3 install above.

To run the daemon, execute the following from the command line after first changing
the -f argument to point to the appropriate location on your disk.

```bash
$ bluepead -v concise -r -p 0.0625 -n bluepea -f /Data/Code/private/indigo/bluepea/src/bluepea/flo/main.flo -b bluepea.core

```

## Signature Header

Indigo service requests or responses may require a custom *Signature* header that provides one or more signatures of the request/response body text.

The format of the custom Signature header follows the conventions of [RFC 7230](https://tools.ietf.org/html/rfc7230)

Signature header has format:

```http
Signature: headervalue

Headervalue:
  tag = "signature"
or
  tag = "signature"; tag = "signature"  ...
  
where tag is replaced with a unique string for each signature value
```

An example is shown below where one *tag* is the string *signer* and the other *tag* is the string *current*.

```http
Signature: signer="Y5xTb0_jTzZYrf5SSEK2f3LSLwIwhOX7GEj6YfRWmGViKAesa08UkNWukUkPGuKuu-EAH5U-sdFPPboBAsjRBw=="; current="Xhh6WWGJGgjU5V-e57gj4HcJ87LLOhQr2Sqg5VToTSg-SI1W3A8lgISxOjAI5pa2qnonyz3tpGvC2cmf1VTpBg=="
```


Where tag is the name of a field in the body of the request whose value
is a DID from which the public key for the signature can be obtained.
If the same tag appears multiple times then only the last occurrence is used.

Each signature value is a doubly quoted string ```""``` that contains the actual signature
in Base64 url safe format. By default the signatures are 64 byte EdDSA (Ed25519) signatures that have been encoded into BASE64 url-file safe format. The encoded signatures are 88 characters in length and include two trailing pad characters ```=```.

An optional *tag* name = *kind* with values *EdDSA* or *Ed25519* may be present.
The *kind* tag field value specifies the type of signature. All signatures within the header
must be of the same kind.

The two tag field values currently supported are *did* and *signer*.

The bluepea python library has a helper function,

```python
parseSignatureHeader(signature)
```

in the

```python
bluepea.help.helping
```

that parses *Signature* header values and returns a python dictionary keyed by tags and whose values are the signatures provided in the header.


Example valid *Signature* headers are shown below:

```http
Signature: did="B0Qc72RP5IOodsQRQ_s4MKMNe0PIAqwjKsBl4b6lK9co2XPZHLmzQFHWzjA2PvxWso09cEkEHIeet5pjFhLUDg=="

```

```http
Signature: signer="B0Qc72RP5IOodsQRQ_s4MKMNe0PIAqwjKsBl4b6lK9co2XPZHLmzQFHWzjA2PvxWso09cEkEHIeet5pjFhLUDg=="; 

```

```http
Signature: signer="B0Qc72RP5IOodsQRQ_s4MKMNe0PIAqwjKsBl4b6lK9co2XPZHLmzQFHWzjA2PvxWso09cEkEHIeet5pjFhLUDg=="; did="B0Qc72RP5IOodsQRQ_s4MKMNe0PIAqwjKsBl4b6lK9co2XPZHLmzQFHWzjA2PvxWso09cEkEHIeet5pjFhLUDg=="

```

```http
Signature: signer="B0Qc72RP5IOodsQRQ_s4MKMNe0PIAqwjKsBl4b6lK9co2XPZHLmzQFHWzjA2PvxWso09cEkEHIeet5pjFhLUDg=="; did="B0Qc72RP5IOodsQRQ_s4MKMNe0PIAqwjKsBl4b6lK9co2XPZHLmzQFHWzjA2PvxWso09cEkEHIeet5pjFhLUDg=="; kind="EdDSA"

```

## Replay Attack Prevention

Although all resource write requests are signed by the client and therefore can not be created by anyone other than the Keeper of the associated private key, a malicious network device could record and resend prior requests in a different order (replay attack) and thereby change the state of the database. To prevent replay attacks on requests that change data resources a client needs to authenticate in a time sensitive manner with the server.  A simple way to do this is for the client to update the *changed* date time stamp field in the resource in a monotonically increasing manner. This way any replayed but stale write requests can be detected and refused by the Server. In other words the server will deny write requests whose *changed* field date time stamp is not later than the the *changed* field value of the pre-existing resource to be updated.

## Endpoint URL Summary

The API consists of several ReST endpoints grouped according to the type of data resource that is being manipulated by the API. Each resource has HTTP verbs that do the manipulation.

/server GET    [api](#server-agent-read)  

/agent  POST   [api](#agent-creation)             
/agent?did={did} GET

/agent/{did}  GET  
/agent/{did}  PUT


/thing  POST  [api](#thing-creation)  
/thing?did={did} GET  [api](#thing-read-query)  
/thing?hid={hid} GET  [api](#thing-read-query)  

/thing/{did}  GET  
/thing/{did}  PUT  


/agent/{did}/drop  POST  
/agent/{did}/drop?from={did}&uid={muid}  GET  


/thing/{did}/offer  POST  
/thing/{did}/offer?uid={ouid}  GET  

/thing/{did}/accept?uid={ouid}  POST


/track  POST  
/track?eid={eid}  GET  




## *Server* *Agent* Read

A special *Agent* is the *Server* *Agent*. This Agent is created automatically by the Indigo *Server* and acts as a trusted party in various exchanges between other Agents. This endpoint allows clients to get the DID and verification key for the Server Agent. The Agent Server read request (GET) retrieves a data resource corresponding to a Server Agent. This is a self-signed or self-owned data resource in that the signer field value references is the self-same data resource. The signature of the data resource is supplied in the Signature header of the response. The client application can verify that the data resource has not been tampered with by verifing the signature against the response body which contains the data resource which is a JSON serialization of the registration data.

The bluepea python library has a helper function,

```python
verify64u(signature, message, verkey)
```

in the

```python
bluepea.help.helping
```

module that shows how to verify a signature.


The request is made by sending an HTTP Get to ```/server```.
A successful request will return status code 200. An unsuccessful request will return an error status code such as 404 Not Found.
If successful the response includes a custom "Signature" header whose *signer* field value is the signature.


Example requests and responses are shown below.

#### Request

```http
GET /server HTTP/1.1
Content-Type: application/json; charset=utf-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.1 (Macintosh; OS X/10.12.5) GCDHTTPRequest
```

#### Response

```http
HTTP/1.1 200 OK
Signature: signer="u72j9aKHgz99f0K8pSkMnyqwvEr_3rpS_z2034L99sTWrMIIJGQPbVuIJ1cupo6cfIf_KCB5ecVRYoFRzAPnAQ=="
Content-Type: application/json; charset=UTF-8
Content-Length: 291
Server: Ioflo WSGI Server
Date: Tue, 11 Jul 2017 01:07:56 GMT

{
  "did": "did:igo:Xq5YqaL6L48pf0fu7IUhL0JRaU2_RxFP0AL43wYn148=",
  "signer": "did:igo:Xq5YqaL6L48pf0fu7IUhL0JRaU2_RxFP0AL43wYn148=#0",
  "changed": "2000-01-01T00:00:00+00:00",
  "keys": [
    {
      "key": "Xq5YqaL6L48pf0fu7IUhL0JRaU2_RxFP0AL43wYn148=",
      "kind": "EdDSA"
    }
  ]
}
```

## *Agent* Creation

The Agent creation request (POST) creates a data resource corresponding to a given Agent. This
is a self-signed or self-owned data resource in that the signer field value
references is the self-same data resource. This registers the Agent with the Indigo service.

In order to create an Agent Registration request the client application needs
to produce a unique EdDSA signing keypair using the libsodium library.

The bluepea python library has a helper function,

```python
makeSignedAgentReg(vk, sk)
```

in the

```python
bluepea.help.helping
```

module.

The example code below shows how to
create this key pair and the associated agent registration plain text
using the python libnacl bindings for libsodium and the helper function.

```python
import libnacl
from bluepea.help.helping import makeSignedAgentReg

seed = libnacl.randombytes(libnacl.crypto_sign_SEEDBYTES)

verkey, sigkey = libnacl.crypto_sign_seed_keypair(seed)
# verkey is the public verification key
# sigkey is the private signing key

signature, registration = makeSignedAgentReg(verkey, sigkey)

# registration is the json serialized body text for the registration request
# signature is the Base64 URL safe encoding of the EdDSA signature of the registration body text

```

It is the responsibility of the client application to store the private signing
key as it will be needed to make any future changes to the resultant agent data
resource.

The request is made by sending an HTTP POST to ```/agent```

The request includes a custom "Signature" header whose value is the signature
produced above. The *tag* value is *signer*.  

The request body is the registration text produced above.

A successful request results in a response with the associated Agent data resource
in the JSON body of the response is and a location header
whose value is the URL to access the Agent Data Resource via a GET request.
This location value has already been URL encoded.

A successful request will return status code 201

An unsuccessful request will return status code 400.

Example requests and responses are shown below.

#### Request

```http
POST /agent HTTP/1.1
Signature: signer="AeYbsHot0pmdWAcgTo5sD8iAuSQAfnH5U6wiIGpVNJQQoYKBYrPPxAoIc1i5SHCIDS8KFFgf8i0tDq8XGizaCg=="
Content-Type: application/json; charset=UTF-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.1 (Macintosh; OS X/10.12.5) GCDHTTPRequest
Content-Length: 291

{
  "did": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
  "signer": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0",
  "changed": "2000-01-01T00:00:00+00:00",
  "keys": [
    {
      "key": "Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
      "kind": "EdDSA"
    }
  ]
}
```

#### Response

```http
HTTP/1.1 201 Created
Location: /agent?did=did%3Aigo%3AQt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE%3D
Content-Length: 255
Content-Type: application/json; charset=UTF-8
Server: Ioflo WSGI Server
Date: Tue, 11 Jul 2017 01:14:58 GMT

{
  "did": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
  "signer": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0",
  "changed": "2000-01-01T00:00:00+00:00",
  "keys": [
    {
      "key": "Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
      "kind": "EdDSA"
    }
  ]
}
```


## *Agent* Read 

The Agent read request (GET) retrieves a data resource corresponding to a given Agent as indicated by the *did* query parameter in the request. This
is a self-signed or self-owned data resource in that the signer field value
references is the self-same data resource. In order to retrieve an agent registration data resource the client application needs the DID for that resource. This is supplied in the *Location* header of the response to a successful Agent Registration creation request. The signature of the data resource is supplied in the Signature header of the response. The client application can verify that the data resource has not been tampered with by verifing the signature against the response body which contains the data resource which is a JSON serialization of the registration data.

The bluepea python library has a helper function,

```python
verify64u(signature, message, verkey)
```

in the

```python
bluepea.help.helping
```

module that shows how to verify a signature.


The request is made by sending an HTTP Get to ```/agent``` with a *did* query parameter whose value is the desired DID. This value needs to be URL encoded.
A successful request will return status code 200. An unsuccessful request will return an error status code such as 404 Not Found.
If successful the response includes a custom "Signature" header whose *signer* field value is the signature.


Example requests and responses are shown below.

#### Request

```http
GET /agent?did=did%3Aigo%3AQt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE%3D HTTP/1.1
Content-Type: application/json; charset=utf-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.1 (Macintosh; OS X/10.12.5) GCDHTTPRequest
```

#### Response

```http
HTTP/1.1 200 OK
Signature: signer="AeYbsHot0pmdWAcgTo5sD8iAuSQAfnH5U6wiIGpVNJQQoYKBYrPPxAoIc1i5SHCIDS8KFFgf8i0tDq8XGizaCg=="
Content-Type: application/json; charset=UTF-8
Content-Length: 291
Server: Ioflo WSGI Server
Date: Tue, 11 Jul 2017 01:17:11 GMT

{
  "did": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
  "signer": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0",
  "changed": "2000-01-01T00:00:00+00:00",
  "keys": [
    {
      "key": "Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
      "kind": "EdDSA"
    }
  ]
}
```


## *Issuer* *Agent* Creation 

When the Agent Registration creation request includes an *issuants* field for registering control of human friendly identifier (*HID*) name spaces then the data resource represents an *Issuer* agent. This effectively registers the *Issuer* with the Indigo service. The creation request will also validate control of the associated *Issuant* *HID* name spaces.  The *issuants* field is a list of one or more *issuant* json objects. Each object contains information about a namespace used by the *Issuer* to generate HIDs:

```json
"issuants":
[
  {
    "kind": "dns",
    "issuer": "generic.com",
    "registered": "2000-01-01T00:00:00+00:00",
    "validationURL": "https://generic.com/indigo"
  }
]
```

*Issuer* *Agents* control *Things* and may issue  a unique human friendly identifier (HID) for the *Things* they control out of the Issuant HID name spaces they also control. Currently each HID is unique to the associated DID for the *Thing*. 

The format for an associated hid is as follows:

```
hid:{kind}:{issuer}#{index}
```

* the *kind* element indicates what type of Issuant name space. Currently only *dns* is suppported. This is the value of the *kind* field in the associated *issuant* in the *issuants* field of the issuing *Agent*'s  resource.

* the *issuer* element is the value of the *issuer* field in the associated *issuant* in the *issuants* field of the issuing *Agent*'s  resource.

* the *index* element is unique to a given *issuer* value.

An example hid given the issuant above is as follows:

```
"hid:dns:generic.com#02
```

Each issuing *Agent* must provide a service at the *validationURL* indicated for each *issuant*. The service must respond to HTTP GET requests on that URL. The GET request will have two query parameters, *did* and *check*. The value of the *did* query parameter is the DID of the issuing *Agent*. The value of the *check* query parameter is a string that serves as a challenge that the service must sign with a signing key of the issuing Agent. The response includes the signature of the *check* value in the *Signature* header of the response. The body of the response is a serialized JSON object with two fields, namely, *signer* and *check*. The value of the *signer* field is the indexed key of the issuing *Agent* used to create the *check* signature. The value of the *check* field is just a copy of the *check* query string from the request.

The format of the check string is as follows:

```
{did}|{issuer}|{date}
```

* the did element is the DID of the issuing Agent.

* the issuer element is the value of the associated issuer field from the issuant

* the date element is an ISO-8601 encoded datetime when the challenge was created.

An example check value is shown below. This value must be URL encoded when included as a query string argument.

```
did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=|generic.com|2000-01-01T00:00:00+00:00
```

Example check request and response are shown below:

#### Request

```http
GET /demo/check?check=did%3Aigo%3A3syVH2woCpOvPF0SD9Z0bu_OxNe2ZgxKjTQ961LlMnA%3D%7Clocalhost%7C2000-01-03T00%3A00%3A00%2B00%3A00&did=did%3Aigo%3A3syVH2woCpOvPF0SD9Z0bu_OxNe2ZgxKjTQ961LlMnA%3D HTTP/1.1
Content-Type: application/json; charset=utf-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.3 (Macintosh; OS X/10.12.6) GCDHTTPRequest
```

#### Response

```http
HTTP/1.1 200 OK
Signature: signer="efIU4jplMtZzjgaWc85gLjJpmmay6QoFvApMuinHn67UkQZ2it17ZPebYFvmCEKcd0weWQONaTO-ajwQxJe2DA=="
Content-Type: application/json; charset=UTF-8
Content-Length: 175
Server: Ioflo WSGI Server
Date: Wed, 30 Aug 2017 18:01:42 GMT

{
  "signer": "did:igo:3syVH2woCpOvPF0SD9Z0bu_OxNe2ZgxKjTQ961LlMnA=#0",
  "check": "did:igo:3syVH2woCpOvPF0SD9Z0bu_OxNe2ZgxKjTQ961LlMnA=|localhost|2000-01-03T00:00:00+00:00"
}
```



Example requests and responses for creating an issuing *Agent* are shown below. The examples use a demo version of the HID validation service that is running on localhost.

#### Request

```http
POST /agent HTTP/1.1
Signature: signer="jc3ZXMA5GuypGWFEsxrGVOBmKDtd0J34UKZyTIYUMohoMYirR8AgH5O28PSHyUB-UlwfWaJlibIPUmZVPTG1DA=="
Content-Type: application/json; charset=UTF-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.3 (Macintosh; OS X/10.12.6) GCDHTTPRequest
Content-Length: 481

{
  "did": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",
  "signer": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#0",
  "changed": "2000-01-01T00:00:00+00:00",
  "keys": [
    {
      "key": "dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",
      "kind": "EdDSA"
    }
  ],
  "issuants": [
    {
      "kind": "dns",
      "issuer": "localhost",
      "registered": "2000-01-01T00:00:00+00:00",
      "validationURL": "http://localhost:8080/demo/check"
    }
  ]
}
```

#### Response

```http
HTTP/1.1 201 Created
Content-Type: application/json; charset=UTF-8
Location: /agent?did=did%3Aigo%3AdZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY%3D
Server: Ioflo WSGI Server
Date: Tue, 29 Aug 2017 17:16:27 GMT
Transfer-Encoding: chunked

{
  "did": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",
  "signer": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#0",
  "changed": "2000-01-01T00:00:00+00:00",
  "keys": [
    {
      "key": "dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",
      "kind": "EdDSA"
    }
  ],
  "issuants": [
    {
      "kind": "dns",
      "issuer": "localhost",
      "registered": "2000-01-01T00:00:00+00:00",
      "validationURL": "http://localhost:8080/demo/check"
    }
  ]
}
```

## *Issuer* *Agent* Read 

The *Issuer* Agent Registration read request (GET) is the same as the generic Agent read request. The only differece is that an *Issuer* Agent with have an *hids* field in its data resource. 
Example requests and responses are shown below.

## Request

```http
GET /agent?did=did%3Aigo%3AdZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY%3D HTTP/1.1
Content-Type: application/json; charset=utf-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.3 (Macintosh; OS X/10.12.6) GCDHTTPRequest
```

## Response

```http
HTTP/1.1 200 OK
Signature: signer="jc3ZXMA5GuypGWFEsxrGVOBmKDtd0J34UKZyTIYUMohoMYirR8AgH5O28PSHyUB-UlwfWaJlibIPUmZVPTG1DA=="
Content-Type: application/json; charset=UTF-8
Content-Length: 481
Server: Ioflo WSGI Server
Date: Tue, 29 Aug 2017 17:20:50 GMT

{
  "did": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",
  "signer": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#0",
  "changed": "2000-01-01T00:00:00+00:00",
  "keys": [
    {
      "key": "dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",
      "kind": "EdDSA"
    }
  ],
  "issuants": [
    {
      "kind": "dns",
      "issuer": "localhost",
      "registered": "2000-01-01T00:00:00+00:00",
      "validationURL": "http://localhost:8080/demo/check"
    }
  ]
}
```

## *Agent* Read (GET) by DID

This Agent read request (GET) retrieves a data resource corresponding to a given Agent as indicated by the *did* in the URL. This is functionally the same as the Agent Read above except that it at a different endpoint.
The request is made by sending an HTTP Get to ```/agent/{did}``` with a *did* whose value is the desired DID. The brackets indicate substitution. This value needs to be URL encoded.
A successful request will return status code 200. An unsuccessful request will return an error status code such as 404 Not Found.
If successful the response includes a custom "Signature" header whose *signer* field value is the signature.


Example requests and responses are shown below.

#### Request

```http
GET /agent/did%3Aigo%3AQt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE%3D HTTP/1.1
Content-Type: application/json; charset=utf-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.1 (Macintosh; OS X/10.12.5) GCDHTTPRequest
```

#### Response

```http
HTTP/1.1 200 OK
Signature: signer="AeYbsHot0pmdWAcgTo5sD8iAuSQAfnH5U6wiIGpVNJQQoYKBYrPPxAoIc1i5SHCIDS8KFFgf8i0tDq8XGizaCg=="
Content-Type: application/json; charset=UTF-8
Content-Length: 291
Server: Ioflo WSGI Server
Date: Tue, 11 Jul 2017 19:58:06 GMT

{
  "did": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
  "signer": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0",
  "changed": "2000-01-01T00:00:00+00:00",
  "keys": [
    {
      "key": "Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
      "kind": "EdDSA"
    }
  ]
}
```

Below is an example for an *Issuer* *Agent*

## Request

```http
GET /agent/did%3Aigo%3AdZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY%3D HTTP/1.1
Content-Type: application/json; charset=utf-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.3 (Macintosh; OS X/10.12.6) GCDHTTPRequest
```

## Response

```http
HTTP/1.1 200 OK
Signature: signer="o9yjuKHHNJZFi0QD9K6Vpt6fP0XgXlj8z_4D-7s3CcYmuoWAh6NVtYaf_GWw_2sCrHBAA2mAEsml3thLmu50Dw=="
Content-Type: application/json; charset=UTF-8
Content-Length: 577
Server: Ioflo WSGI Server
Date: Tue, 29 Aug 2017 17:23:24 GMT

{
  "did": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",
  "signer": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#1",
  "changed": "2000-01-02T00:00:00+00:00",
  "keys": [
    {
      "key": "dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",
      "kind": "EdDSA"
    },
    {
      "key": "0UX5tP24WPEmAbROdXdygGAM3oDcvrqb3foX4EyayYI=",
      "kind": "EdDSA"
    }
  ],
  "issuants": [
    {
      "kind": "dns",
      "issuer": "localhost",
      "registered": "2000-01-01T00:00:00+00:00",
      "validationURL": "http://localhost:8080/demo/check"
    }
  ]
}
```

## *Agent* Write (PUT) by DID

This Agent write request (PUT) overwrites a data resource corresponding to a given Agent as indicated by the *did* in the URL.
The request is made by sending an HTTP PUT to ```/agent/{did}``` with a *did* whose value is the desired DID. The brackets indicate substitution. This value needs to be URL encoded. Because a PUT can change the signer field in the data resource, the PUT request Signature header must have two signatures. The tag 'signer' signature is the signature of the new data resources using the key indicated by the new value that the data resource will have once the PUT is successful. The tag 'current' signature is the signature of the new resource using the key indicated by the current value of the data resource before it is overwritten. To clarify, both signatures generated by signing the new value of the Agent resource. The signature tagged "*current*" is with the key indicated by the current resource's *signer* field. The signature tagged "*signer*" is with the key indicated by new resource's *signer* field. In the event that the *signer* field value stays the same then the *current* and *signer* tagged signatures will be the same. the new  allows to server to verify that the request was made by the current signer and that the new signer signature is provided so that the resource is signed at rest.

A successful request will return status code 200. An unsuccessful request will return an error status code such as 400 Not Found.


Example request and response are shown below for adding another key and changing the signer field to reference the new key.

#### Request

```http
PUT /agent/did%3Aigo%3AQt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE%3D HTTP/1.1
Signature: signer="Y5xTb0_jTzZYrf5SSEK2f3LSLwIwhOX7GEj6YfRWmGViKAesa08UkNWukUkPGuKuu-EAH5U-sdFPPboBAsjRBw=="; current="Xhh6WWGJGgjU5V-e57gj4HcJ87LLOhQr2Sqg5VToTSg-SI1W3A8lgISxOjAI5pa2qnonyz3tpGvC2cmf1VTpBg=="
Content-Type: application/json; charset=UTF-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.1 (Macintosh; OS X/10.12.5) GCDHTTPRequest
Content-Length: 387

{
  "did": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
  "signer": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#1",
  "changed": "2000-01-02T00:00:00+00:00",
  "keys": [
    {
      "key": "Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
      "kind": "EdDSA"
    },
    {
      "key": "FsSQTQnp_W-6RPkuvULH8h8G5u_4qYl61ec9-k-2hKc=",
      "kind": "EdDSA"
    }
  ]
}
```

#### Response

```http
HTTP/1.1 200 OK
Signature: signer="Y5xTb0_jTzZYrf5SSEK2f3LSLwIwhOX7GEj6YfRWmGViKAesa08UkNWukUkPGuKuu-EAH5U-sdFPPboBAsjRBw=="
Content-Type: application/json; charset=UTF-8
Content-Length: 387
Server: Ioflo WSGI Server
Date: Wed, 12 Jul 2017 00:47:00 GMT

{
  "did": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
  "signer": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#1",
  "changed": "2000-01-02T00:00:00+00:00",
  "keys": [
    {
      "key": "Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
      "kind": "EdDSA"
    },
    {
      "key": "FsSQTQnp_W-6RPkuvULH8h8G5u_4qYl61ec9-k-2hKc=",
      "kind": "EdDSA"
    }
  ]
}
```

Below is an example for an *Issuer* *Agent*

#### Request

```http
PUT /agent/did%3Aigo%3AdZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY%3D HTTP/1.1
Signature: signer="o9yjuKHHNJZFi0QD9K6Vpt6fP0XgXlj8z_4D-7s3CcYmuoWAh6NVtYaf_GWw_2sCrHBAA2mAEsml3thLmu50Dw==";  current="bTGB92MvNmb65Ka0BD7thquxw1BGEcJRf1c8GpTvcF5Qe-tm0v28qMGKfYQ3EYeVI1VdLWRMtyFApnyAB07yCQ=="
Content-Type: application/json; charset=UTF-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.3 (Macintosh; OS X/10.12.6) GCDHTTPRequest
Content-Length: 577

{
  "did": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",
  "signer": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#1",
  "changed": "2000-01-02T00:00:00+00:00",
  "keys": [
    {
      "key": "dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",
      "kind": "EdDSA"
    },
    {
      "key": "0UX5tP24WPEmAbROdXdygGAM3oDcvrqb3foX4EyayYI=",
      "kind": "EdDSA"
    }
  ],
  "issuants": [
    {
      "kind": "dns",
      "issuer": "localhost",
      "registered": "2000-01-01T00:00:00+00:00",
      "validationURL": "http://localhost:8080/demo/check"
    }
  ]
}
```

#### Response

```http
HTTP/1.1 200 OK
Content-Type: application/json; charset=UTF-8
Signature: signer="o9yjuKHHNJZFi0QD9K6Vpt6fP0XgXlj8z_4D-7s3CcYmuoWAh6NVtYaf_GWw_2sCrHBAA2mAEsml3thLmu50Dw=="
Server: Ioflo WSGI Server
Date: Tue, 29 Aug 2017 17:22:38 GMT
Transfer-Encoding: chunked

{
  "did": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",
  "signer": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#1",
  "changed": "2000-01-02T00:00:00+00:00",
  "keys": [
    {
      "key": "dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",
      "kind": "EdDSA"
    },
    {
      "key": "0UX5tP24WPEmAbROdXdygGAM3oDcvrqb3foX4EyayYI=",
      "kind": "EdDSA"
    }
  ],
  "issuants": [
    {
      "kind": "dns",
      "issuer": "localhost",
      "registered": "2000-01-01T00:00:00+00:00",
      "validationURL": "http://localhost:8080/demo/check"
    }
  ]
}
```


## *Thing* Creation 

The *Thing* Registration creation request (POST) creates a data resource corresponding to a given *Thing*. This effectively registers the *Thing* with the Indigo service. A Thing resource is controlled or owned by an Agent data resource. Consequently the *signer* field references the controlling Agent's data resource. In other words a *Thing* data resourse is not self-signing. 

In order to create an *Thing* Registration request the client application needs to know the DID of the associated controlling Agent as well have access to the the priviate signing key of that Agent. In other words a Thing can only be created by a client application for an Agent controlled by the client application. 

Each *Thing* has a unique DID. The Server will also verify that the client application holds the associated private key used to create the Thing's DID. To create a DID the client application will first need to create an EdDSA signing keypair.

Each *Thing* may also have a unique human friendly identifier (HID). Currently each HID is unique to its associated DID. *Issuer* *Agents* control an HID name space called and *Issuant* from which the HIDs are generated. 
Suppose an issuing Agent might has the following issuant in its resource.

```json
{
    "kind": "dns",
    "issuer": "generic.com",
    "registered": "2000-01-01T00:00:00+00:00",
    "validationURL": "https://generic.com/indigo"
  }
```

The format for an associated hid is as follows:

```
hid:{kind}:{issuer}#{index}
```

* the *kind* element indicates what type of Issuant name space. Currently only *dns* is suppported. This is the value of the *kind* field in the associated *issuant* in the *issuants* field of the issuing *Agent*'s  resource.

* the *issuer* element is the value of the *issuer* field in the associated *issuant* in the *issuants* field of the issuing *Agent*'s  resource.

* the *index* element is unique to a given *issuer* value.

An example hid given the issuant above is as follows:

```
"hid:dns:generic.com#02
```


To produce a unique EdDSA signing keypair using the libsodium library.

The bluepea python library has a helper function,

```python
makeSignedThingReg(dvk, dsk, ssk, signer, changed=None, hid=None, **kwa)
```

in the

```python
bluepea.help.helping
```

module.

The example code below shows how to
create this key pair and the associated agent registration plain text
using the python libnacl bindings for libsodium and the helper function.

```python
import libnacl
from bluepea.help.helping import makeSignedAgentReg

seed = libnacl.randombytes(libnacl.crypto_sign_SEEDBYTES)

dvk, dsk = libnacl.crypto_sign_seed_keypair(seed)
# dvk is the public verification key
# dsk is the private signing key

dsignature, ssignature, registration = makeSignedThingReg(dvk, dsk, ssk, signer

# ssk is the controlling agents private signing key

# registration is the json serialized body text for the registration request
# dsignature is the Base64 URL safe encoding of the EdDSA signature of the registration body text given dsk
# ssignature is the Base64 URL safe encoding of the EdDSA signature of the registration body text given ssk the controlling agent (signer) private signing key

```

It is the responsibility of the client application to store the private signing
key for the DID as it will be needed to verify any future challenges as the creator of the thing DID.

The request is made by sending an HTTP POST to ```/thing```

The request includes a custom "Signature" header whose value has both signatures. The *tag* value *signer* is the *ssignature* returned above and the *tag* value *did* is the *dsignature* returned above. Both signatures allows the Server to verify that the client both created the Thing DID and controls the Signing Agent.

The request body is the registration text produced above.

A successful request results in a response with the associated Agent data resource
in the JSON body of the response is and a location header
whose value is the URL to access the Agent Data Resource via a GET request.
This location value has already been URL encoded.

A successful request will return status code 201

An unsuccessful request will return status code 400.

Example requests and responses are shown below.

## Request

```http
POST /thing HTTP/1.1
Signature: signer="FGRHzSNS70LIjwcSTAxHx5RahDwAet090fYSnsReMco_WvpTVpvfEygWDXslCBh0TqBoEOMLQ78-kN8fj6NFAg=="; did="bzJDEvEprraZc9aOLYS7WaPi5UB_px0EH9wu76rFPrbRgjAUO9JJ4roMpQrD31v3WlbHHTG8WzB5L8PE6v3BCg=="
Content-Type: application/json; charset=UTF-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.3 (Macintosh; OS X/10.12.6) GCDHTTPRequest
Content-Length: 347

{
  "did": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
  "hid": "hid:dns:localhost#02",
  "signer": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#0",
  "changed": "2000-01-01T00:00:00+00:00",
  "data": {
    "keywords": [
      "Canon",
      "EOS Rebel T6",
      "251440"
    ],
    "message": "If found please return."
  }
}
```

## Response

```http
HTTP/1.1 201 Created
Content-Type: application/json; charset=UTF-8
Location: /thing?did=did%3Aigo%3A4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM%3D
Server: Ioflo WSGI Server
Date: Tue, 29 Aug 2017 17:24:08 GMT
Transfer-Encoding: chunked

{
  "did": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
  "hid": "hid:dns:localhost#02",
  "signer": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#0",
  "changed": "2000-01-01T00:00:00+00:00",
  "data": {
    "keywords": [
      "Canon",
      "EOS Rebel T6",
      "251440"
    ],
    "message": "If found please return."
  }
}
```

## *Thing* Read Query

The *Thing* Registration read request (GET) retrieves a data resource corresponding to a given *Thing* as indicated by provided the value of URL query parameters in the request URL. The two query parameters supported are *did* and *hid*. 

In order to retrieve a *Thing* registration data resource the client application needs the DID for that thing resource. The DID is a field in the orginal resource created for the *Thing*. The DID is also supplied in the *Location* header of the response to a successful *Thing* creation request. The Location header value is just a URL that includes the *did* as a query parameter.

For *Things* that have an HID the system creates an index table entry that allows lookup of the associated Thing's DID by its HID. The query is just a GET request with a query parameter *hid* whose value is the Thing's HID.

It is important to remember that a Thing resource is controlled or owned by an Agent data resource. Consequently the *Thing's* *signer* field references the controlling Agent's data resource. In other words a Thing data resourse is not self-signing. The signature of the data resource is supplied in the Signature header of the response. The client application can verify that the data resource has not been tampered with by verifing the signature against the response body which contains the data resource which is a JSON serialization of the thing resource data. 

The bluepea python library has a helper function,

```python
verify64u(signature, message, verkey)
```

in the

```python
bluepea.help.helping
```

module that shows how to verify a signature.


The request for a Thing by querying the DID is made by sending an HTTP Get to ```/thing``` with a *did* query parameter whose value is the associated DID. This value needs to be URL encoded.

A successful request will return status code 200. An unsuccessful request will return an error status code such as 404 Not Found. 
If successful the response includes a custom "Signature" header whose *signer* field value is the signature.


Example requests and responses are shown below.

## Request

```http
GET /thing?did=did%3Aigo%3A4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM%3D HTTP/1.1
Content-Type: application/json; charset=utf-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.3 (Macintosh; OS X/10.12.6) GCDHTTPRequest
```

## Response

```http
HTTP/1.1 200 OK
Signature: signer="FGRHzSNS70LIjwcSTAxHx5RahDwAet090fYSnsReMco_WvpTVpvfEygWDXslCBh0TqBoEOMLQ78-kN8fj6NFAg=="
Content-Type: application/json; charset=UTF-8
Content-Length: 347
Server: Ioflo WSGI Server
Date: Tue, 29 Aug 2017 17:25:37 GMT

{
  "did": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
  "hid": "hid:dns:localhost#02",
  "signer": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#0",
  "changed": "2000-01-01T00:00:00+00:00",
  "data": {
    "keywords": [
      "Canon",
      "EOS Rebel T6",
      "251440"
    ],
    "message": "If found please return."
  }
}
```

The request for a Thing by querying the HID is made by sending an HTTP Get to ```/thing``` with an *hid* query parameter whose value is the associated HID. This value needs to be URL encoded.

A successful request will return status code 200. An unsuccessful request will return an error status code such as 404 Not Found. 
If successful the response includes a custom "Signature" header whose *signer* field value is the signature.


Example requests and responses are shown below.

## Request

```http
GET /thing?hid=hid%3Adns%3Alocalhost%2302 HTTP/1.1
Content-Type: application/json; charset=utf-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.3 (Macintosh; OS X/10.12.6) GCDHTTPRequest
```

## Response

```http
HTTP/1.1 200 OK
Signature: signer="FGRHzSNS70LIjwcSTAxHx5RahDwAet090fYSnsReMco_WvpTVpvfEygWDXslCBh0TqBoEOMLQ78-kN8fj6NFAg=="
Content-Type: application/json; charset=UTF-8
Content-Length: 347
Server: Ioflo WSGI Server
Date: Fri, 15 Sep 2017 19:51:54 GMT

{
  "did": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
  "hid": "hid:dns:localhost#02",
  "signer": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#0",
  "changed": "2000-01-01T00:00:00+00:00",
  "data": {
    "keywords": [
      "Canon",
      "EOS Rebel T6",
      "251440"
    ],
    "message": "If found please return."
  }
}
```

## *Thing* Read (GET) by DID

This Thing read request (GET) retrieves a data resource corresponding to a given Thing as indicated by the *did* in the URL. This is functionally the same as the Thing Read above except that it at a different endpoint.
The request is made by sending an HTTP Get to ```/thing/{did}``` with a *did* whose value is the desired DID. The brackets indicate substitution. This value needs to be URL encoded.
A successful request will return status code 200. An unsuccessful request will return an error status code such as 404 Not Found.
If successful the response includes a custom "Signature" header whose *signer* field value is the signature.


Example requests and responses are shown below.

## Request

```http
GET /thing/did%3Aigo%3A4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM%3D HTTP/1.1
Content-Type: application/json; charset=utf-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.3 (Macintosh; OS X/10.12.6) GCDHTTPRequest
```

## Response

```http
HTTP/1.1 200 OK
Signature: signer="4IMop_e8vDbsot2kqJaZin8_xPsayWKbpsXL2qJZc3NrB6254UNi9x5VRwk-OgYn0zQPvKwtTE8GjtYZAHaKAQ=="
Content-Type: application/json; charset=UTF-8
Content-Length: 347
Server: Ioflo WSGI Server
Date: Tue, 29 Aug 2017 17:26:50 GMT

{
  "did": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
  "hid": "hid:dns:localhost#02",
  "signer": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#1",
  "changed": "2000-01-02T00:00:00+00:00",
  "data": {
    "keywords": [
      "Canon",
      "EOS Rebel T6",
      "251440"
    ],
    "message": "If found please return."
  }
}
```

## *Thing* Write (PUT) by DID

This Thing write request (PUT) overwrites a data resource corresponding to a given Thing as indicated by the *did* in the URL.
The request is made by sending an HTTP PUT to ```/thing/{did}``` with a *did* whose value is the desired DID. The brackets indicate substitution. This value needs to be URL encoded. Because a PUT can change the signer field in the data resource, the PUT request Signature header must have two signatures. The *tag* *signer* signature is the signature using the key indicated by the new value that the data resource will have once the PUT is successful. The *tag* *current* signature is the signature using the key indicated by the current value of the data resource before it is overwritten. This allows to server to verify that the request was made by the current signer and that the new signer signature is provided so that the resource is signed at rest.

A successful request will return status code 200. An unsuccessful request will return an error status code such as 400 Not Found.

Example request and response are shown below for adding another key and changing the signer field to reference the new key.

## Request

```http
PUT /thing/did%3Aigo%3A4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM%3D HTTP/1.1
Signature: signer="4IMop_e8vDbsot2kqJaZin8_xPsayWKbpsXL2qJZc3NrB6254UNi9x5VRwk-OgYn0zQPvKwtTE8GjtYZAHaKAQ==";  current="fuSvUsNtFDzaYm5bX65SAgrZpNKEek2EJFqf-j-_QRWNXhSWpTFGIeg4AHOVaD7MHuIj6QsnjPg-jyBDiUAmCw=="
Content-Type: application/json; charset=UTF-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.3 (Macintosh; OS X/10.12.6) GCDHTTPRequest
Content-Length: 347

{
  "did": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
  "hid": "hid:dns:localhost#02",
  "signer": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#1",
  "changed": "2000-01-02T00:00:00+00:00",
  "data": {
    "keywords": [
      "Canon",
      "EOS Rebel T6",
      "251440"
    ],
    "message": "If found please return."
  }
}
```

## Response

```http
HTTP/1.1 200 OK
Content-Type: application/json; charset=UTF-8
Signature: signer="4IMop_e8vDbsot2kqJaZin8_xPsayWKbpsXL2qJZc3NrB6254UNi9x5VRwk-OgYn0zQPvKwtTE8GjtYZAHaKAQ=="
Server: Ioflo WSGI Server
Date: Tue, 29 Aug 2017 17:26:06 GMT
Transfer-Encoding: chunked

{
  "did": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
  "hid": "hid:dns:localhost#02",
  "signer": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#1",
  "changed": "2000-01-02T00:00:00+00:00",
  "data": {
    "keywords": [
      "Canon",
      "EOS Rebel T6",
      "251440"
    ],
    "message": "If found please return."
  }
}
```

## Sending a *Message* from One *Agent* to Another 

The request is made by sending an HTTP POST to ```/agent/{did}/drop```

The path paramater indicated by ```{did}``` is the DID of destination agent for the message. This value must be URL encoded.

The request includes a custom "Signature" header whose value has the signature of the sender. The *tag* value *signer* is the *signature* of the message by the sender/signer. The signature allows the Server to verify that the sending client exists as and Agent and also created the message.

The request body is a JSON serialized dict object with several required fields.
An example is shown below:

```JSON
{
  "uid": "m_00035d2976e6a000_26ace93",
  "kind": "found",
  "signer": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0",
  "date": "2000-01-03T00:00:00+00:00",
  "to": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",
  "from": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
  "thing": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
  "subject": "Lose something?",
  "content": "Look what I found"
}
```

All the fields in the example above are required except for ```thing```.

The fields descriptions are as follows:

- *uid*  is the unique message id. This must be unique for any paring of sender and recipient to insure that there are no collisions between messages stored in the database. A useful ID scheme is the time based universal unique ID provided by the ```ioflo.aid.timing.tuuid()``` function. This uses time to order the UID up to microsecond intervals and then adds a random suffix to provide sub micro-second uniqueness. A sender can then ensure that it does not generate duplicate message ids. Each destinatation Agent has a single incoming message queue (dropbox or inbox). The messages are keyed by a combination of the source Agent DID and the message UID. Thus even if two senders happen to use the same message uid there will not be a collision and each sender's message will be stored in a different location.

To generate a TUUID as in the examples use the function as follows:

```python
from ioflo.aid.timing import tuuid

muid = tuuid(prefix="m")
```

For a specific datetime not just the current time one may use it as follows:

```python
import datetime
from ioflo.aid.timing import tuuid

dt =datetime.datetime(2017,7,4,tzinfo=datetime.timezone.utc)
muid = tuuid(stamp=dt.timestamp(), prefix="m")
```

- *kind* is the message kind. This allows the client applications to know how to handle special messages such as encryption key exchange messages. Currently the special kinds  are ``` "exchange"``` for key exchange. Values that do not have special meaning are ignored.

- *signer* is the indexed DID of the signer Agent sending the message. The index fragment indicates which of the signing *Agent*'s keys to use.

- *date* is an ISO-8601 datetime which may be used by the client applications for filtering messages by date

- *to* is the destination Agent's DID. This must match the DID used in the POST URL

- *from* is the sending Agent's DID. This must match the DID used in the *signer* field.

- *thing* is an optional field that has the DID of a *Thing*. This is to enable the client application to differentially display messages about particular things. 

- *subject* is the subject text of the message.

- *content* is the content text of the message.

A successful request results in a response with the associated Agent data resource
in the JSON body of the response is and a location header
whose value is the URL to access the Agent Data Resource via a GET request.
This location value has already been URL encoded.

A successful request will return status code 201

An unsuccessful request will return status code 400.

Example requests and responses are shown below.

## Request

```http
POST /agent/did%3Aigo%3AdZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY%3D/drop HTTP/1.1
Signature: signer="07u1OcQI8FUeWPqeiga3A9k4MPJGSFmC4vShiJNpv2Rke9ssnW7aLx857HC5ZaJ973WSKkLAwPzkl399d01HBA=="
Content-Type: application/json; charset=UTF-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.2 (Macintosh; OS X/10.12.5) GCDHTTPRequest
Content-Length: 432

{
  "uid": "m_00035d2976e6a000_26ace93",
  "kind": "found",
  "signer": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0",
  "date": "2000-01-03T00:00:00+00:00",
  "to": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",
  "from": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
  "thing": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
  "subject": "Lose something?",
  "content": "Look what I found"
}
```

## Response

```http
HTTP/1.1 201 Created
Location: /agent/did%3Aigo%3AdZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY%3D/drop?from=did%3Aigo%3AQt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE%3D&uid=m_00035d2976e6a000_26ace93
Content-Length: 432
Content-Type: application/json; charset=UTF-8
Server: Ioflo WSGI Server
Date: Tue, 18 Jul 2017 19:50:57 GMT

{
  "uid": "m_00035d2976e6a000_26ace93",
  "kind": "found",
  "signer": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0",
  "date": "2000-01-03T00:00:00+00:00",
  "to": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",
  "from": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
  "thing": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
  "subject": "Lose something?",
  "content": "Look what I found"
}
```

## Reading a *Message* from One *Agent* to Another

The Indigo service creates a dedicated message queue (dropbox or inbox) for each recipient Agent DID. In order to prevent collisions due to different senders using the same message uid, the full database key includes the sender's DID in addition to the message UID.

The request is made by sending an HTTP Get to ```/agent/{did}/drop?from={did}&uid={muid}``` with the path parameter that is the DID of the recepient of a message. This value needs to be URL encoded. The request also has two query parameters. One with *tag* *from* query parameter whose value is the sender DID. This value needs to be URL encoded. The other with *tag* uid whose value is the unique message ID of the message. Other variants of the request will allow querying the first last or all of the messages to a given receipient as well as all messages from a given sender to a given recepient.

A successful request will return status code 200. An unsuccessful request will return an error status code such as 404 Not Found. 

If successful the response includes a custom "Signature" header whose *signer* field value is the signature.

Example requests and responses are shown below.

#### Request

```http
GET /agent/did%3Aigo%3AdZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY%3D/drop?from=did%3Aigo%3AQt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE%3D&uid=m_00035d2976e6a000_26ace93 HTTP/1.1
Signature: signer="07u1OcQI8FUeWPqeiga3A9k4MPJGSFmC4vShiJNpv2Rke9ssnW7aLx857HC5ZaJ973WSKkLAwPzkl399d01HBA=="
Content-Type: application/json; charset=UTF-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.2 (Macintosh; OS X/10.12.5) GCDHTTPRequest
```

#### Response

```http
HTTP/1.1 200 OK
Signature: signer="07u1OcQI8FUeWPqeiga3A9k4MPJGSFmC4vShiJNpv2Rke9ssnW7aLx857HC5ZaJ973WSKkLAwPzkl399d01HBA=="
Content-Type: application/json; charset=UTF-8
Content-Length: 432
Server: Ioflo WSGI Server
Date: Tue, 18 Jul 2017 19:53:16 GMT

{
  "uid": "m_00035d2976e6a000_26ace93",
  "kind": "found",
  "signer": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0",
  "date": "2000-01-03T00:00:00+00:00",
  "to": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",
  "from": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
  "thing": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
  "subject": "Lose something?",
  "content": "Look what I found"
}
```

### *Drop* Read List Query

The *Drop*  read list request (GET) query retrieves a list of the messages in the message queue (inbox, dropbox) for a given *Agent* DID. Each entry in the list includes the sending *Agent's* DID as the value of the *from* field and the message UID as the value of the *uid* field. An example message list is shown below:

```json
[
  {
    "from": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
    "uid": "m_00035d2976e6a000_26ace93"
  },
  {
    "from": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
    "uid": "m_00035d3d94be0000_15aabb5"
  }
]
```

In order to retrieve a list of all the messages in an Agent's message queue use the query parameter *all* with value *true*, that is, *all=true*. Example request and response is shown below:

#### Request

```http
GET /agent/did%3Aigo%3AdZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY%3D/drop?all=true HTTP/1.1
Content-Type: application/json; charset=UTF-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.4 (Macintosh; OS X/10.12.6) GCDHTTPRequest
```

#### Response

```http
HTTP/1.1 200 OK
Content-Type: application/json; charset=UTF-8
Content-Length: 119
Server: Ioflo WSGI Server
Date: Tue, 19 Sep 2017 21:07:09 GMT

[
  {
    "from": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
    "uid": "m_00035d2976e6a000_26ace93"
  }
]
```

With the information from an entry in the message list, a client can then request a specific message using the message query with query parameters *from* and *uid* as shown in the previous section. 


### Including Encrypted Data in a *Message*

Encrypted data requires an encryption/decryption key pair. Best practices for secure encryption/decryption exchange between two parties is to use asymmetric keys that are exchanged using a Diffie-Hellman key exchange that adds a type of authentication to the encryption/decryption. This provides additional security against exploits. The NaCL (libsodium) library provides support for such ECC based Diffie-Hellman authenticated encryption (ECDH) with its crypto box function. As mentioned previously NaCL keys use the Curve25519 standard. These are different from Ed25519 (EdDSA) signing keys. Consequently a separate key identifier for encrypted data is required. Curve25519 public keys are 32 binary bytes long or 64 Hex encoded characters or 44 Base64 encoded characters (with padding).

The python libnacl call for creating a public/private encryption key pair is as follows:

```python
import libnacl

pubkey, prikey = libnacl.crypto_box_keypair()
```

The following function allows one to regenerate a public key from a saved private key.

```python
import libnacl

pubkey = libnacl.crypto_scalarmult_base(prikey)
```

In the two party Diffie-Hellman key exchange the actual keys used for encryption and decryption are never transmitted. Instead the asymetric private key of the first party is combined with the asymetric public key of the second party to generate a "*shared*" key. Likewise the second party uses its private key and the first party's public key to generate an equivalent "*shared*" key. The shared key is not a symmetric key. This approach is used for the exchange of data between two entities within Indigo. To generate the shared key requires knowledge of both the encryptor and decryptor entity and which public encryption key each is to combin with the other to generate a shared key between the two.

In order to indicate to another *Agent* which public encryption key is to be used to generate the shared communicating encrypted data, a given *Agent* must include a *cryptor* field in a message that it sends to another *Agent*. The value of this field is a dict. The dict has two fields. One is the *key* field with the base64 url file safe encoded public part of the key. The other is the *kind* field with a string indicating the type of key.

For example:

```json
{
  "key": "dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",
  "kind": "Curve25519"
}
```

The other agent may then reply with a message including a *cryptor* field with its own key or may reply with a message that includes encrypted data with its public key provided in the *encryptor* field and the given Agent's previously recieved public encryption key in the *decryptor* field.  

- *cryptor* is the the public encryption/decryption key by the Agent sending the message. The field indicates which Curve25519 key to use in the future.

An example message with a *cryptor* field is shown below:

```json
{
  "uid": "m_00035d2976e6a000_26ace93",
  "kind": "key",
  "signer": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0",
  "date": "2000-01-03T00:00:00+00:00",
  "to": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",
  "from": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
  "thing": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
  "subject": "Public encryption key",
  "content": "Use the enclosed key to create shared encryption key",
  "cryptor": 
  {
    "key": "dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",
    "kind": "Curve25519"
  }
}
```

When an entity encrypts data it becomes the encryptor of the data. In a two party exchange of encrypted data using ECDH the recipient of the data is the decryptor. Both these entities need to be identified in order that both know how the associated ECDH shared key for encryption/decription is to be generated from the associated public/private keys.

In order to include encrypted data in a *Message* four fields must be added to the message, these are:  ```encryptor, decryptor, crypt, nonce```

- *encryptor* is a dict with the public encryption/decryption key by the encrypting Agent sending the message. It indicates which Curve25519 key to use.

- *decryptor* is dict with the public encryption/decryption key by the decrypting Agent receiving the message. It indicates which Curve25519 key to use.

- *crypt* is the Base64 url/file safe encoded crypt text that has been encrypted with the shared key generated as described above.

- *nonce* is the Base64 url/file safe encoded nonce. The nonce is a random 24 byte string used in the encryption.


Given the following JSON serialized data to be sent encrypted

```json
{
  "name" : "John Smith",
  "city" : "San Jose",
  "zip" : "94088",
  "phone" : "8005551212"
}

```

Then with suitable encryption keys the added fields for sending the data would appear as follows:

Example encryption fields :

```json
{
    "encryptor": 
    {
      "key": "dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",
      "kind": "Curve25519"
    },
    "decryptor": 
    {
      "key": "0UX5tP24WPEmAbROdXdygGAM3oDcvrqb3foX4EyayYI=",
      "kind": "EdDSA"
    },
    "crypt": "UaP_31Z1S8qfb99JnnvdfIRTCp-gL8L98IyWiT7GVvrO_0mfx6CV31ecP0dfKDg7wuWaDlR6T4LB5ofDRRM7FALDZ7Ao0BJtEV_nZTTAI9YVYUsozsUo3gVXnb6ukYrgI2ZeyNDbZbfkSIs=",
    "nonce": "K7z3nEc7LaLJUf2A2G7zK2b2P31ggnaf"
}
```

An example of a full message with encrypted data is as follows:

```JSON
{
    "uid": "m_00035d2976e6a000_26ace93",
    "kind": "found",
    "signer": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0",
    "date": "2000-01-03T00:00:00+00:00",
    "to": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",
    "from": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
    "thing": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
    "subject": "Lose something?",
    "content": "Look what I found",
    "encryptor": 
    {
      "key": "dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=",
      "kind": "Curve25519"
    },
    "decryptor": 
    {
      "key": "0UX5tP24WPEmAbROdXdygGAM3oDcvrqb3foX4EyayYI=",
      "kind": "EdDSA"
    },
    "crypt": "UaP_31Z1S8qfb99JnnvdfIRTCp-gL8L98IyWiT7GVvrO_0mfx6CV31ecP0dfKDg7wuWaDlR6T4LB5ofDRRM7FALDZ7Ao0BJtEV_nZTTAI9YVYUsozsUo3gVXnb6ukYrgI2ZeyNDbZbfkSIs=",
    "nonce": "K7z3nEc7LaLJUf2A2G7zK2b2P31ggnaf"
    }
```

The python ```libnacl``` library provides functions for encrypting and decrypting data. The following code snippet provides and example.

```python
import libnacl
import libnacl.utils
import base64
from collections import OrderedDict as ODict

data = ODict(name="John Smith", city="San Jose", zip="94088", phone="8005551212")
msg = json.dumps(data, indent=2)  # serialize the data

# Ann sending msg data to Bob

# create Ann's keys
aPubKey, aPriKey = libnacl.crypto_box_keypair()

# create Bob's keys
bPubKey, bPriKey = libnacl.crypto_box_keypair()

# create nonce
nonce = libnacl.utils.rand_nonce()

# now Ann encrypts msg and nonce with Ann's private key and Bob's public key
crypt = libnacl.crypto_box(msg.encode("utf-8"), nonce, bPubKey, aPriKey)

# now Bob decrypts box and nonce with Ann's public key and Bob's private key
clear = libnacl.crypto_box_open(crypt, nonce, aPubKey, bPriKey)

# now Bob deserializes the clear text to get back the dict
stuff = json.loads(clear.decode("utf-8", object_pairs_hook=ODict)

```

The code above used raw bytes values for the data and keys. To include in Indigo messages the raw bytes values need to be converted to and from Base64 url safe unicode strings and bytes. The code snippet below shows how to do this

```python
import base64

# convert Ann's public key from a bytes to Base64 url unicode str
aPubKey64u = base64.urlsafe_b64encode(aPubKey).decode("utf-8")
# convert Ann's public key from a Base64 url unicode str to a bytes
aPubKey = base64.urlsafe_b64decode(aPubKey64u.encode("utf-8"))

# convert nonce
nonce64u = base64.urlsafe_b64encode(aPubKey).decode("utf-8")
nonce = base64.urlsafe_b64decode(nonce64u.encode("utf-8"))

# convert crypt text
crypt64u = base64.urlsafe_b64encode(crypt).decode("utf-8")
crypt = base64.urlsafe_b64decode(crypt64u.encode("utf-8"))

```

## Transferring Control/Ownership of a *Thing* from one *Agent* to Another

Transfer of control of a *Thing* from one *Agent* to another requires several steps.
These steps are to prevent the controlling *Agent* from transferring control to more than one other *Agent* at a time. The *Server* *Agent* acts as a trusted third party to ensure that the *Agent* transferring control only transfers once and that there are no race conditions.

### *Offer* to Tranfer Control Creation Request

The first step if for the current controller *Agent* or *Offerer* to POST an *offer* to transfer control to another *Agent*. This other Agent is called the *Aspirant* as this other *Agent* aspires to be the new controlling agent of the *Thing*.  This *offer* is signed by the *Offerer* *Agent*.  

The request is made by sending an HTTP POST to ```/thing/{did}/offer```

The path paramater indicated by ```{did}``` is the DID of *Thing* that is being offered.  This value must be URL encoded.

The request includes a custom "Signature" header whose value has the signature of the Offerer. The *tag* value *signer* is the *signature* of the message by the sender/signer. The signature allows the Server to verify that the sending client exists as an *Agent*, is the controlling *Agent* of the *Thing* and also created the offer and no other offers are still in effect or open.

The request body is offer a JSON serialized dict object with several required fields.
An example is shown below:

```json
{
    "uid": "o_00035d2976e6a000_26ace93",
    "thing": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
    "aspirant": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
    "duration": 360.0,
}
```

- *uid* is the unique Id of the offer as a time based unique identifier
- *thing* is the DID of the Thing
- *aspirant* is the DID of the Aspirant Agent
- *duration* is the length of time in seconds that the offer is open to be accepted by the Aspirant.

Only one offer for a given thing can be open at any time.

Given that the offer is valid. The server then adds an *expiration* field and the Server's signer field  as well as a copy of the serialized offer request and the signature of the orginal offer and puts it in the database.

An example is shown below


```JSON
{
    "uid": "o_00035d2976e6a000_26ace93",
    "thing": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
    "aspirant": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
    "duration": 360.0,
    "expiration": "2017-07-25T18:33:57.424839+00:00",
    "signer" : "did:igo:Xq5YqaL6L48pf0fu7IUhL0JRaU2_RxFP0AL43wYn148=#0",
    "offerer": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#0",
    "offer": "ewogICJ1aWQiOiAib18wMDAzNWQyOTc2ZTZhMDAwXzI2YWNlOTMiLAogICJ0aGluZyI6ICJkaWQ6aWdvOjRKQ004ZEpXd19PNTd2TTRrQXRUdDB5V3FTZ0J1d2lIcFZnZDU1QmlvQ009IiwKICAiYXNwaXJhbnQiOiAiZGlkOmlnbzpRdDI3ZlRoV29OWnNhODhWclRrZXA2SC00SEE4dHI1NHNIT04xdldsNkZFPSIsCiAgImR1cmF0aW9uIjogMTIwLjAKfQ=="
}
```

The fields descriptions are as follows:

- *uid* is the unique Id of the offer as a time based unique identifier
- *thing* is the DID of the Thing
- *aspirant* is the DID of the Aspirant Agent
- *duration* is the length of time in seconds that the offer is open to be accepted by the Aspirant.
- *expiration* is the ISO-8601 datetime of the expiration of the offer. It is duration seconds after current datetime of the server when it received the the offer request.
- *signer* is the key indexed DID of the signing key of the Server.
- *offerer* is the key indexed DID of the signing key of the Offerer
- *offer* is the base64 url/file safe encoding of the offer request body

A successful request results in a response with the associated *Server* signed offer data resource in the JSON body of the response is and a location header
whose value is the URL to access the offer Data Resource via a GET request.
This location value has already been URL encoded.

A successful request will return status code 201

An unsuccessful request will return status code 400.

Example requests and responses are shown below.

#### Request

```http
POST /thing/did%3Aigo%3A4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM%3D/offer HTTP/1.1
Signature: signer="EhsfS2_4LSVjDMo_QShvciNr6aYf5ut8NuFkBugxL748vlOs1YF971aPIckmtRRAFzby07hY0Ny-7xs27-wXCw=="
Content-Type: application/json; charset=UTF-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.3 (Macintosh; OS X/10.12.6) GCDHTTPRequest
Content-Length: 199

{
  "uid": "o_00035d2976e6a000_26ace93",
  "thing": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
  "aspirant": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
  "duration": 120.0
}
```

#### Response

```http
HTTP/1.1 201 Created
Location: /thing/did%3Aigo%3A4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM%3D/offer?uid=o_00035d2976e6a000_26ace93
Content-Length: 675
Content-Type: application/json; charset=UTF-8
Server: Ioflo WSGI Server
Date: Tue, 29 Aug 2017 21:59:18 GMT

{
  "uid": "o_00035d2976e6a000_26ace93",
  "thing": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
  "aspirant": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
  "duration": 120.0,
  "expiration": "2017-08-29T22:01:18.303646+00:00",
  "signer": "did:igo:Xq5YqaL6L48pf0fu7IUhL0JRaU2_RxFP0AL43wYn148=#0",
  "offerer": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#0",
  "offer": "ewogICJ1aWQiOiAib18wMDAzNWQyOTc2ZTZhMDAwXzI2YWNlOTMiLAogICJ0aGluZyI6ICJkaWQ6aWdvOjRKQ004ZEpXd19PNTd2TTRrQXRUdDB5V3FTZ0J1d2lIcFZnZDU1QmlvQ009IiwKICAiYXNwaXJhbnQiOiAiZGlkOmlnbzpRdDI3ZlRoV29OWnNhODhWclRrZXA2SC00SEE4dHI1NHNIT04xdldsNkZFPSIsCiAgImR1cmF0aW9uIjogMTIwLjAKfQ=="
}
```

### *Offer* to Transfer Control Read Request

The *Offer*  read request (GET) retrieves an offer for a given *Thing* DID with a given *Offer* UID by the *uid* query parameter in the request. In order to retrieve an *Offer* data resource the client application needs the DID for the corresponding Thing as well as the UID for the specific *Offer*.  This is supplied in the *Location* header of the response to a successful *Offer* creation request. The signature of the data resource is supplied in the Signature header of the response. The client application can verify that the data resource has not been tampered with by verifing the signature against the response body which contains the data resource which is a JSON serialization of the *Offer* data. Successfully created Offers are signed by the *Server* *Agent*.


The request is made by sending an HTTP Get to ```/thing/{did}/offer?uid={ouid}``` where the did path parameter is the DID of the thing and the *uid* query parameter is the Offer unique ID. This did needs to be URL encoded.

A successful request will return status code 200. An unsuccessful request will return an error status code such as 404 Not Found. 
If successful the response includes a custom "Signature" header whose *signer* field value is the signature.


Example requests and responses are shown below.

#### Request

```http
GET /thing/did%3Aigo%3A4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM%3D/offer?uid=o_00035d2976e6a000_26ace93 HTTP/1.1
Content-Type: application/json; charset=utf-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.3 (Macintosh; OS X/10.12.6) GCDHTTPRequest
```

#### Response

```http
HTTP/1.1 200 OK
Signature: signer="DDvBCSLxGLsMrN-c-3-1LKVoo-D-zES1-6fmMsQkXSd14nNeVgQ1M5TW-ON3gB1kdA1GelBUTZ-7I5m03l1ECw=="
Content-Type: application/json; charset=UTF-8
Content-Length: 675
Server: Ioflo WSGI Server
Date: Tue, 29 Aug 2017 22:00:43 GMT

{
  "uid": "o_00035d2976e6a000_26ace93",
  "thing": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
  "aspirant": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
  "duration": 120.0,
  "expiration": "2017-08-29T22:01:18.303646+00:00",
  "signer": "did:igo:Xq5YqaL6L48pf0fu7IUhL0JRaU2_RxFP0AL43wYn148=#0",
  "offerer": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#0",
  "offer": "ewogICJ1aWQiOiAib18wMDAzNWQyOTc2ZTZhMDAwXzI2YWNlOTMiLAogICJ0aGluZyI6ICJkaWQ6aWdvOjRKQ004ZEpXd19PNTd2TTRrQXRUdDB5V3FTZ0J1d2lIcFZnZDU1QmlvQ009IiwKICAiYXNwaXJhbnQiOiAiZGlkOmlnbzpRdDI3ZlRoV29OWnNhODhWclRrZXA2SC00SEE4dHI1NHNIT04xdldsNkZFPSIsCiAgImR1cmF0aW9uIjogMTIwLjAKfQ=="
}
```

### *Offer* to Transfer Control Accept Request

Once an Offer to transfer control has been created the next step if for the *Aspirant* *Agent* named in the offer to accept the request. The acceptance URL includes the Thing DID and the Offer UID as a query parameter. The Aspirant *Agent* then POSTs an *accept* to take over control of the *Thing*. The POST body includes the new *Thing* serialized data resource with one of the *Aspirant* keys as *signer*. The *Signature* header includes the *Aspirant* signature of the POST body.  
The request is made by sending an HTTP POST to ```/thing/{did}/offer?uid={ouid}```
The ```did``` path parameter is the DID of the *Thing*. This DID needs to be URL encoded. The ```uid``` query parameter is the *Offer* unique ID. 

The request includes a custom *Signature* header whose value has the signature of the *Aspirant*. The *tag* value *signer* is the *signature* of the message by the sender/signer. The signature allows the Server to verify that the sending client exists as an *Agent*, is the Aspirant *Agent* of for the Offer and also offer is still in effect or open.

A successful request results in a response with the associated *Thing* data resource with the *Aspirant* now as the new controlling *signer*. The *Thing* data resource in the JSON body of the response. The value of the *location* header in the response s the URL to access the *Thing* data resource via a GET request. This *location* value has already been URL encoded.

A successful request will return status code 201
An unsuccessful request will return status code 400.

Example requests and responses are shown below.

#### Request

```http
POST /thing/did%3Aigo%3A4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM%3D/accept?uid=o_00035d2976e6a000_26ace93 HTTP/1.1
Signature: signer="c04xu10KP_O8gfWoVvHRw8sO7ww9WrQ91BT_HXNGtSEMTf_BsKikxSUyQz0ASxjscEJVvV6E7yaldQ0dECQgAQ=="
Content-Type: application/json; charset=UTF-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.3 (Macintosh; OS X/10.12.6) GCDHTTPRequest
Content-Length: 314

{
  "did": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
  "signer": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0",
  "changed": "2000-01-01T00:00:00+00:00",
  "data": {
    "keywords": [
      "Canon",
      "EOS Rebel T6",
      "251440"
    ],
    "message": "If found please return."
  }
}
```

#### Response

```http
HTTP/1.1 201 Created
Content-Type: application/json; charset=UTF-8
Location: /thing/did%3Aigo%3A4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM%3D
Server: Ioflo WSGI Server
Date: Tue, 29 Aug 2017 21:59:25 GMT
Transfer-Encoding: chunked

{
  "did": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
  "signer": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0",
  "changed": "2000-01-01T00:00:00+00:00",
  "data": {
    "keywords": [
      "Canon",
      "EOS Rebel T6",
      "251440"
    ],
    "message": "If found please return."
  }
}
```

### *Offer* Read List Query

The *Offer*  read request (GET) retrieves an offer for a given *Thing* DID with a given *Offer* UID by the *uid* query parameter in the request. In order to retrieve an *Offer* data resource the client application needs the DID for the corresponding Thing as well as the UID for the specific *Offer*. 

The offer uid can be obtained by either querying for a list of all offers for a given Thing DID or a list of just the latest offer for a Thing DID. The list contains json objects (dicts) one for each offer. Each object has two fields, *uid* whose value is the offer uid and *expire* whose value is the expiration date of the offer. If there are no offers then the list is empty. Using the returned offer uid another request can be made using an *Offer* Read Request (see above).

An example is shown below:

```json
[
  {
     "offer": "o_00035d2976e6a000_26ace93",
    "expire": "2017-09-15T21:02:41.686546+00:00"
  }
]

```

To request all offers use the query parameter *all* with value *true*, such as *all=true*.
The list is sorted with the latest offer last in the list. To request just the latest offer use the query parameter *latest* with the value *true*, such as, *latest=true*.

The request for *all* is made by sending an HTTP Get to ```/thing/{did}/offer?all=true``` where the did path parameter is the DID of the thing. This did needs to be URL encoded.

The request for *latest* is made by sending an HTTP Get to ```/thing/{did}/offer?latest=true``` where the did path parameter is the DID of the thing. This did needs to be URL encoded.

A successful request will return status code 200. An unsuccessful request will return an error status code such as 404 Not Found. 

Example requests and responses are shown below.

#### Request

```http
GET /thing/did%3Aigo%3A4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM%3D/offer?all=true HTTP/1.1
Content-Type: application/json; charset=utf-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.4 (Macintosh; OS X/10.12.6) GCDHTTPRequest
```

#### Response

```http
HTTP/1.1 200 OK
Content-Type: application/json; charset=UTF-8
Content-Length: 101
Server: Ioflo WSGI Server
Date: Mon, 18 Sep 2017 14:00:40 GMT

[
  {
    "expire": "2017-09-18T14:02:33.998738+00:00",
    "uid": "o_00035d2976e6a000_26ace93"
  }
]
```

#### Request

```http
GET /thing/did%3Aigo%3A4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM%3D/offer?latest=true HTTP/1.1
Content-Type: application/json; charset=utf-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.4 (Macintosh; OS X/10.12.6) GCDHTTPRequest
```

#### Response

```http
HTTP/1.1 200 OK
Content-Type: application/json; charset=UTF-8
Content-Length: 101
Server: Ioflo WSGI Server
Date: Mon, 18 Sep 2017 14:00:43 GMT

[
  {
    "expire": "2017-09-18T14:02:33.998738+00:00",
    "uid": "o_00035d2976e6a000_26ace93"
  }
]
```

## Anonymous Message Creation

The anonymous messaging service can be used for short messages. Messages are ephemeral in that they are deleted after 24 hours. The service can be used to store limited amounts of information as messages for short periods of time. Each message content may be upto 256 characters. The only ID used is the message UID. Each message UID may be up to 32 characters. Because there is no identification of either the sender or receiver they are effectively anonymous.  

Another application of this service is to store location beacon data that is augmented with the gateway location that received the beacon. 
The posted data includes a unique message ID (UID). The UID may be up to 32 characters in length. 
When used for tracking this is also called an ephemerial ID (EID). In the case when the EID is binary it may be up to 16 binary bytes in length but must be converted to Base64 url/file safe encoding for transmission. When used for beacon tracking the EID is generated using a shared cryptographic key and is an encrypted version of the date time of when the beacon was sent.  The beacon generates a 16 byte EID. The upper 8 bytes are used as the EID or key to store the track and the lower 8 bytes to XOR with the location in order to encrypt or obscure the location.  With a synchronized clock and a copy of the shared key, a user can estimate the EID at any point in time in the future. The client application can then request track data by EID and if found retreive the location of the gateway as well as a datetime stamp. Base64 encoding increased the length by 4/3. So an 8 byte binary EID becomes a 12 char base64  string with padding. Likewise for the location. 


The request is made by sending an HTTP POST to ```/anon```. There are three fields in the request body data: "*uid*", "*content*", and "*date*". The uid is the unique message id (up to 32 characters). The content field is the message content (up to 256 characters). The *date* field is the iso8601 datetime stamp of the gateway at the time it received the beacon and assigned the location or message into the *content* field.
An example is shown below:

```json
{
   uid: "AQIDBAoLDA0=",  # base64 url safe of 8 byte eid
   content: "EjRWeBI0Vng=", # base64 url safe of 8 byte location
   date: "2000-01-01T00:36:00+00:00", # ISO-8601 creation date of anon gateway time
}
```

A successful request results in a response with anonymous message data stored in the database. The response data includes the message data from the request in the *anon* field as well as a timestamp in field *create* in server time when the data was stored in the database  and a timestamp in field *expire* in server time when the data becomes stale and will be deleted from the database. The timestamps are in microseconds since the Unix epoch. An example of the data stored in the database is as follows:

```json
{
    create: 1501774813367861, # creation in server time microseconds since epoch
    expire: 1501818013367861, # expiration in server time microseconds since epoch
    anon:
    {
        uid: "AQIDBAoLDA0=",  # base64 url safe of 8 byte eid
        content: "EjRWeBI0Vng=", # base64 url safe of 8 byte location
        date: "2000-01-01T00:36:00+00:00", # ISO-8601 creation date of anon gateway time
    }
}
```


The value of the *location* header in the response is the URL to access the msg data resource via a GET request. This *location* value has already been URL encoded.

A successful request will return status code 201
An unsuccessful request will return status code 400.

Example requests and responses are shown below.

#### Request

```http
POST /anon HTTP/1.1
Content-Type: application/json; charset=UTF-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.3 (Macintosh; OS X/10.12.6) GCDHTTPRequest
Content-Length: 95

{
  "uid": "AQIDBAoLDA0=",
  "content": "EjRWeBI0Vng=",
  "date": "2000-01-01T00:30:05+00:00"
}
```

#### Response

```http
HTTP/1.1 201 Created
Location: /anon?uid=AQIDBAoLDA0%3D
Content-Length: 177
Content-Type: application/json; charset=UTF-8
Server: Ioflo WSGI Server
Date: Tue, 29 Aug 2017 19:03:46 GMT

{
  "create": 1504033426628350,
  "expire": 1504033436628350,
  "anon": {
    "uid": "AQIDBAoLDA0=",
    "content": "EjRWeBI0Vng=",
    "date": "2000-01-01T00:30:05+00:00"
  }
}
```

## Anonymous Message Read

The anonymous messaging service stores messages, or when used for tracking, location beacon data that is augmented with the gateway location that received the beacon. The anonymous message data includes an unique message ID (UID). 

When used for tracking beacons this UID/EID is generated using a shared cryptographic key and is an encrypted version of the date time of when the beacon was sent.  The beacon generates a 16 byte EID. The upper 8 bytes are used as the EID or key to store the track and the lower 8 bytes to XOR with the location in order to encrypt or obscure the location.  With a synchronized clock and a copy of the shared key, a user can estimate the EID at any point in time in the future. The client application can then request track data by EID and if found retreive the location of the gateway as well as a datetime stamp.


The read request is made by sending an HTTP GET to ```/anon?uid={uid}```. The UID in query argument is the message ID. When used for tracking the UID is  base64 url safe encoded version of the EID. Base64 encoding increased the length by 4/3. So an 8 byte binary EID becomes a 12 char base64  string with padding. 

A successful request results in the response a JSON encoded list with all the message data for a given UID stored in the database. A single UID may have more than one message associated with it. Each item in the response data includes the message data from the request in the *anon* field as well as the datetime (in iso8601 format) on the server when the data was stored in the database in field *create* and the datetime when the data becomes stale and will be deleted from the database in field *expire*. 

A successful request will return status code 200
An unsuccessful request will return an error code.

Example requests and responses are shown below.

#### Request

```http
GET /anon?uid=AQIDBAoLDA0%3D HTTP/1.1
Content-Type: application/json; charset=UTF-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.3 (Macintosh; OS X/10.12.6) GCDHTTPRequest
```

#### Response

```http
HTTP/1.1 200 OK
Content-Type: application/json; charset=UTF-8
Content-Length: 593
Server: Ioflo WSGI Server
Date: Tue, 29 Aug 2017 19:03:49 GMT

[
  {
    "create": 1504033424899903,
    "expire": 1504033434899903,
    "anon": {
      "uid": "AQIDBAoLDA0=",
      "content": "EjRWeBI0Vng=",
      "date": "2000-01-01T00:30:05+00:00"
    }
  },
  {
    "create": 1504033425815548,
    "expire": 1504033435815548,
    "anon": {
      "uid": "AQIDBAoLDA0=",
      "content": "EjRWeBI0Vng=",
      "date": "2000-01-01T00:30:05+00:00"
    }
  },
  {
    "create": 1504033426628350,
    "expire": 1504033436628350,
    "anon": {
      "uid": "AQIDBAoLDA0=",
      "content": "EjRWeBI0Vng=",
      "date": "2000-01-01T00:30:05+00:00"
    }
  }
]
```