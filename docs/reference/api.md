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


/server GET  [ServerAgentRead](#Replay-Attack-Prevention)

/agent  POST  [AgentCreation](*Agent*-Creation)

/agent?did={did} GET

/agent/{did}  GET

/agent/{did}  PUT

/agent/{did}


/thing  POST

/thing?did={did} GET

/thing/{did}  GET
/thing/{did}  PUT



/agent/{did}/drop  POST
/agent/{did}/drop?from={did}&uid={muid}  GET



/thing/{did}/offer  POST
/thing/{did}/offer?uid={ouid}  GET

/thing/{did}/accept?uid={ouid}  POST


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

## Request

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

## Response

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

## Request

```http
GET /agent?did=did%3Aigo%3AQt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE%3D HTTP/1.1
Content-Type: application/json; charset=utf-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.1 (Macintosh; OS X/10.12.5) GCDHTTPRequest
```

## Response

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

Example requests and responses are shown below.

## Request

```http
POST /agent HTTP/1.1
Signature: signer="xZbsn-GqZQZmZX9UdhbG45EEGGj25o7WJ_t7yYI9UfXXseV7my3faYhn4slrxB-KuujOMjFmx_EJaZWgGb8HCg=="
Content-Type: application/json; charset=UTF-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.2 (Macintosh; OS X/10.12.5) GCDHTTPRequest
Content-Length: 477

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
      "issuer": "generic.com",
      "registered": "2000-01-01T00:00:00+00:00",
      "validationURL": "https://generic.com/indigo"
    }
  ]
}
```

## Response

```http
HTTP/1.1 201 Created
Location: /agent?did=did%3Aigo%3AdZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY%3D
Content-Length: 477
Content-Type: application/json; charset=UTF-8
Server: Ioflo WSGI Server
Date: Wed, 19 Jul 2017 16:21:25 GMT

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
      "issuer": "generic.com",
      "registered": "2000-01-01T00:00:00+00:00",
      "validationURL": "https://generic.com/indigo"
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
User-Agent: Paw/3.1.2 (Macintosh; OS X/10.12.5) GCDHTTPRequest
```

## Response

```http
HTTP/1.1 200 OK
Signature: signer="xZbsn-GqZQZmZX9UdhbG45EEGGj25o7WJ_t7yYI9UfXXseV7my3faYhn4slrxB-KuujOMjFmx_EJaZWgGb8HCg=="
Content-Type: application/json; charset=UTF-8
Content-Length: 477
Server: Ioflo WSGI Server
Date: Wed, 19 Jul 2017 16:21:29 GMT

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
      "issuer": "generic.com",
      "registered": "2000-01-01T00:00:00+00:00",
      "validationURL": "https://generic.com/indigo"
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

## Request

```http
GET /agent/did%3Aigo%3AQt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE%3D HTTP/1.1
Content-Type: application/json; charset=utf-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.1 (Macintosh; OS X/10.12.5) GCDHTTPRequest
```

## Response

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
User-Agent: Paw/3.1.2 (Macintosh; OS X/10.12.5) GCDHTTPRequest
```

## Response

```http
HTTP/1.1 200 OK
Signature: signer="P4CAY5_6Yh1-JbJRPLR11FcvFYcQZKscMeF9tsismbWZmRGSiqNpXcUAiV_zAaBtEOJl99UBR9v30XpGcUSDDw=="
Content-Type: application/json; charset=UTF-8
Content-Length: 573
Server: Ioflo WSGI Server
Date: Wed, 19 Jul 2017 16:21:57 GMT

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
      "issuer": "generic.com",
      "registered": "2000-01-01T00:00:00+00:00",
      "validationURL": "https://generic.com/indigo"
    }
  ]
}
```

## *Agent* Write (PUT) by DID

This Agent write request (PUT) overwrites a data resource corresponding to a given Agent as indicated by the *did* in the URL.
The request is made by sending an HTTP PUT to ```/agent/{did}``` with a *did* whose value is the desired DID. The brackets indicate substitution. This value needs to be URL encoded. Because a PUT can change the signer field in the data resource, the PUT request Signature header must have two signatures. The tag 'signer' signature is the signature using the key indicated by the new value that the data resource will have once the PUT is successful. The tag 'current' signature is the signature using the key indicated by the current value of the data resource before it is overwritten. This allows to server to verify that the request was made by the current signer and that the new signer signature is provided so that the resource is signed at rest.

A successful request will return status code 200. An unsuccessful request will return an error status code such as 400 Not Found.


Example request and response are shown below for adding another key and changing the signer field to reference the new key.

## Request

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

## Response

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

## Request

```http
PUT /agent/did%3Aigo%3AdZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY%3D HTTP/1.1
Signature: signer="P4CAY5_6Yh1-JbJRPLR11FcvFYcQZKscMeF9tsismbWZmRGSiqNpXcUAiV_zAaBtEOJl99UBR9v30XpGcUSDDw==";  current="yMyy2iEeecI_BtmuAEvLxhUywciPvDn6KHF85KmVuChNr1G3LiOUcxkjmJWNiNkhdcw-0nvFQ60YBCuQbZe_CA=="
Content-Type: application/json; charset=UTF-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.2 (Macintosh; OS X/10.12.5) GCDHTTPRequest
Content-Length: 573

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
      "issuer": "generic.com",
      "registered": "2000-01-01T00:00:00+00:00",
      "validationURL": "https://generic.com/indigo"
    }
  ]
}
```

## Response

```http
HTTP/1.1 200 OK
Signature: signer="P4CAY5_6Yh1-JbJRPLR11FcvFYcQZKscMeF9tsismbWZmRGSiqNpXcUAiV_zAaBtEOJl99UBR9v30XpGcUSDDw=="
Content-Type: application/json; charset=UTF-8
Content-Length: 573
Server: Ioflo WSGI Server
Date: Wed, 19 Jul 2017 16:21:54 GMT

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
      "issuer": "generic.com",
      "registered": "2000-01-01T00:00:00+00:00",
      "validationURL": "https://generic.com/indigo"
    }
  ]
}
```


## *Thing* Creation 

The *Thing* Registration creation request (POST) creates a data resource corresponding to a given *Thing*. This effectively registers the *Thing* with the Indigo service. A Thing resource is controlled or owned by an Agent data resource. Consequently the *signer* field references the controlling Agent's data resource. In other words a *Thing* data resourse is not self-signing. 

In order to create an *Thing* Registration request the client application needs to know the DID of the associated controlling Agent as well have access to the the priviate signing key of that Agent. In other words a Thing can only be created by a client application for an Agent controlled by the client application. 

Each *Thing* has a unique DID. The Server will also verify that the client application holds the associated private key used to create the Thing's DID. To create a DID the client application will first need to create an EdDSA signing keypair.

Each *Thing* may also have a unique human friendly identifier (HID). Currently each HID is unique to its associated DID. *Issuer* *Agents* control an HID name space called and *Issuant* from which the HIDs are generated.

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
Signature: signer="RtlBu9sZgqhfc0QbGe7IHqwsHOARrGNjy4BKJG7gNfNP4GfKDQ8FGdjyv-EzN1OIHYlnMBFB2Kf05KZAj-g2Cg==";did="kWZwPfepoAV9zyt9B9vPlPNGeb_POHlP9LL3H-PH71WWZzVJT1Ce64IKj1GmOXkNo2JaXrnIpQyfm2vynn7mCg=="
Content-Type: application/json; charset=UTF-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.1 (Macintosh; OS X/10.12.5) GCDHTTPRequest
Content-Length: 349

{
  "did": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
  "hid": "hid:dns:generic.com#02",
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

## Response

```http
HTTP/1.1 201 Created
Location: /thing?did=did%3Aigo%3A4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM%3D
Content-Length: 301
Content-Type: application/json; charset=UTF-8
Server: Ioflo WSGI Server
Date: Tue, 11 Jul 2017 01:07:39 GMT

{
  "did": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
  "hid": "hid:dns:generic.com#02",
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

## *Thing* Registration Read 

The *Thing* Registration read request (GET) retrieves a data resource corresponding to a given *Thing* as indicated by the *did* query parameter in the request. A Thing resource is controlled or owned by an Agent data resource. Consequently the signer field references the controlling Agent's data resource. In other words a Thing data resourse is not self-signing. In order to retrieve a Thing registration data resource the client application needs the DID for that resource. This is supplied in the *Location* header of the response to a successful Thing Registration creation request. The signature of the data resource is supplied in the Signature header of the response. The client application can verify that the data resource has not been tampered with by verifing the signature against the response body which contains the data resource which is a JSON serialization of the registration data.

The bluepea python library has a helper function,

```python
verify64u(signature, message, verkey)
```

in the

```python
bluepea.help.helping
```

module that shows how to verify a signature.


The request is made by sending an HTTP Get to ```/thing``` with a *did* query parameter whose value is the desired DID. This value needs to be URL encoded.
A successful request will return status code 200. An unsuccessful request will return an error status code such as 404 Not Found. 
If successful the response includes a custom "Signature" header whose *signer* field value is the signature.


Example requests and responses are shown below.

## Request

```http
GET /thing?did=did%3Aigo%3A4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM%3D HTTP/1.1
Content-Type: application/json; charset=utf-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.1 (Macintosh; OS X/10.12.5) GCDHTTPRequest
```

## Response

```http
HTTP/1.1 200 OK
Signature: signer="RtlBu9sZgqhfc0QbGe7IHqwsHOARrGNjy4BKJG7gNfNP4GfKDQ8FGdjyv-EzN1OIHYlnMBFB2Kf05KZAj-g2Cg=="
Content-Type: application/json; charset=UTF-8
Content-Length: 349
Server: Ioflo WSGI Server
Date: Tue, 11 Jul 2017 01:07:47 GMT

{
  "did": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
  "hid": "hid:dns:generic.com#02",
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
User-Agent: Paw/3.1.2 (Macintosh; OS X/10.12.5) GCDHTTPRequest
```

## Response

```http
HTTP/1.1 200 OK
Signature: signer="5SwnZroMIcOpx1vEYkcSajnU3BhrqBpovq0NnCwL43kuEs-GTfwd6bpQJ_L5bMhfRAZZEgkjVqFx4HCGGLc9DA=="
Content-Type: application/json; charset=UTF-8
Content-Length: 349
Server: Ioflo WSGI Server
Date: Sat, 15 Jul 2017 01:02:29 GMT

{
  "did": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
  "hid": "hid:dns:generic.com#02",
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
Signature: signer="5SwnZroMIcOpx1vEYkcSajnU3BhrqBpovq0NnCwL43kuEs-GTfwd6bpQJ_L5bMhfRAZZEgkjVqFx4HCGGLc9DA==";  current="3GhKWYXFL0JGTnhK3vB0087Rib4nhjfts12KjJMr5EOa2AO6uqyBZyziKVfa7WUK5mvFPyo-Hxjx4GPTV5AGBw=="
Content-Type: application/json; charset=UTF-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.2 (Macintosh; OS X/10.12.5) GCDHTTPRequest
Content-Length: 349

{
  "did": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
  "hid": "hid:dns:generic.com#02",
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
Signature: signer="5SwnZroMIcOpx1vEYkcSajnU3BhrqBpovq0NnCwL43kuEs-GTfwd6bpQJ_L5bMhfRAZZEgkjVqFx4HCGGLc9DA=="
Content-Type: application/json; charset=UTF-8
Content-Length: 349
Server: Ioflo WSGI Server
Date: Sat, 15 Jul 2017 00:54:46 GMT

{
  "did": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
  "hid": "hid:dns:generic.com#02",
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

- *uid*  is the unique message id. This must be monotonically increasing for any recipient. A useful ID scheme is the time based universal unique ID provided by the ```ioflo.aid.timing.tuuid()``` function. This uses time to order the UID up to microsecond intervals and then adds a random suffix to provide sub micro-second uniqueness. To generate a TUUID as in the examples use the function as follows:

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

For each receipient, The Indigo service will create a dedicated message queue for each sender. 

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

The Indigo service creates a dedicated message queue for each sender at each recipient.
The request is made by sending an HTTP Get to ```/agent/{did}/drop?from={did}&uid={muid}``` with the path parameter that is the DID of the recepient of a message. This value needs to be URL encoded. The request also has two query parameters. One with *tag* *from* query parameter whose value is the sender DID. This value needs to be URL encoded. The other with *tag* uid whose value is the unique message ID of the message. Other variants of the request will allow querying the first last or all of the messages from a given sender to a given recepient.

A successful request will return status code 200. An unsuccessful request will return an error status code such as 404 Not Found. 

If successful the response includes a custom "Signature" header whose *signer* field value is the signature.

Example requests and responses are shown below.

## Request

```http
GET /agent/did%3Aigo%3AdZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY%3D/drop?from=did%3Aigo%3AQt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE%3D&uid=m_00035d2976e6a000_26ace93 HTTP/1.1
Signature: signer="07u1OcQI8FUeWPqeiga3A9k4MPJGSFmC4vShiJNpv2Rke9ssnW7aLx857HC5ZaJ973WSKkLAwPzkl399d01HBA=="
Content-Type: application/json; charset=UTF-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.2 (Macintosh; OS X/10.12.5) GCDHTTPRequest
```

## Response

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

## Including Encrypted Data in a *Message*

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

In order to include encrypted data in a *Message* an *Agent* needs to first add an assymetric public encryption key to its *key* list in its data resource. The key kind is ```Curve25519```

Shown below is an example Agent resource with public encryption key denoted by the key "kind" field with value "Curve25519" :

```json
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
    },
    {
      "key": "HqbSyYiI__jkW1td1VZD3IJc2jU4ty4KXbns7gB9P3I=",
      "kind": "Curve25519",
    }

  ],
}
```

In the two party Diffie-Hellman key exchange the actual keys used for encryption and decryption are never transmitted. Instead the asymetric private key of the first party is combined with the asymetric public key of the second party to generate a "*shared*" key. Likewise the second party uses its private key and the first party's public key to generate an equivalent "*shared*" key. The shared key is not a symmetric key. This approach is used for the exchange of data between two entities within Indigo. To generate the shared key requires knowledge of both the encryptor and decryptor entity.

In order to indicate to another *Agent* which of its public encryption keys to use when communicating encrypted data, a given *Agent* must include a *cryptor* field in a message that it sends to another *Agent*. The value of this field is the given *Agent*'s key indexed DID where the fragment index indicates which of the keys in its data resource is to be used for encrypted exchange with the other *Agent*. The other agent may then reply with a message including a *cryptor* field with its own key indexed DID or may reply with a message that includes encrypted data with its public key provided in the *encryptor* field and the given Agent's previously recieved public encryption key in the *decryptor* field.  

- *cryptor* is the key indexed DID of the public encryption/decryption key by the Agent sending the message. The index indicates which Curve25519 key to use in the future.

An example message with a *cryptor* field is shown below:

```JSON
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
  "cryptor": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#2",
}
```

When an entity encrypts data it becomes the encryptor of the data. In a two party exchange of encrypted data using ECDH the recipient of the data is the decryptor. Both these entities need to be identified in order that both know how the associated ECDH shared key for encryption/decription is to be generated from the associated public/private keys.

In order to include encrypted data in a *Message* four fields must be added to the message, these are:  ```encryptor, decryptor, crypt, nonce```

- *encryptor* is the key indexed DID of the public encryption/decryption key by the encrypting Agent sending the message. The index indicates which Curve25519 key to use.

- *decryptor* is the key indexed DID of the public encryption/decryption key by the decrypting Agent receiving the message. The index indicates which Curve25519 key to use.

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
"encryptor": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#2"
"decryptor": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#2"
"crypt": "UaP_31Z1S8qfb99JnnvdfIRTCp-gL8L98IyWiT7GVvrO_0mfx6CV31ecP0dfKDg7wuWaDlR6T4LB5ofDRRM7FALDZ7Ao0BJtEV_nZTTAI9YVYUsozsUo3gVXnb6ukYrgI2ZeyNDbZbfkSIs="
"nonce": "K7z3nEc7LaLJUf2A2G7zK2b2P31ggnaf"
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
  "encryptor": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#2",
  "decryptor": "did:igo:dZ74MLZXD-1QHoa73w9pQ9GroAvxqFi2RTZWlkC0raY=#2",
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

## Request

```http
POST /thing/did%3Aigo%3A4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM%3D/offer HTTP/1.1
Signature: signer="EhsfS2_4LSVjDMo_QShvciNr6aYf5ut8NuFkBugxL748vlOs1YF971aPIckmtRRAFzby07hY0Ny-7xs27-wXCw=="
Content-Type: application/json; charset=UTF-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.2 (Macintosh; OS X/10.12.5) GCDHTTPRequest
Content-Length: 199

{
  "uid": "o_00035d2976e6a000_26ace93",
  "thing": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
  "aspirant": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
  "duration": 120.0
}

```

## Response

```http
HTTP/1.1 201 Created
Location: /thing/did%3Aigo%3A4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM%3D/offer?uid=o_00035d2976e6a000_26ace93
Content-Length: 675
Content-Type: application/json; charset=UTF-8
Server: Ioflo WSGI Server
Date: Thu, 27 Jul 2017 01:33:36 GMT

{
  "uid": "o_00035d2976e6a000_26ace93",
  "thing": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
  "aspirant": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
  "duration": 120.0,
  "expiration": "2017-07-27T01:35:36.895638+00:00",
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
User-Agent: Paw/3.1.2 (Macintosh; OS X/10.12.5) GCDHTTPRequest
```

#### Response

```http
HTTP/1.1 200 OK
Signature: signer="klcoeC_dztIDcCO2hkptCSGyoRURSI30EqqyQaUOihHGsR9suntOaRqZpbCJi4qRTGdfSEV880DfVo5iq726Bw=="
Content-Type: application/json; charset=UTF-8
Content-Length: 675
Server: Ioflo WSGI Server
Date: Thu, 27 Jul 2017 01:38:14 GMT

{
  "uid": "o_00035d2976e6a000_26ace93",
  "thing": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
  "aspirant": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
  "duration": 120.0,
  "expiration": "2017-07-27T01:35:36.895638+00:00",
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

## Request

```http
POST /thing/did%3Aigo%3A4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM%3D/accept?uid=o_00035d2976e6a000_26ace93 HTTP/1.1
Signature: signer="RtlBu9sZgqhfc0QbGe7IHqwsHOARrGNjy4BKJG7gNfNP4GfKDQ8FGdjyv-EzN1OIHYlnMBFB2Kf05KZAj-g2Cg=="
Content-Type: application/json; charset=UTF-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.2 (Macintosh; OS X/10.12.6) GCDHTTPRequest
Content-Length: 349

{
  "did": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
  "hid": "hid:dns:generic.com#02",
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

## Response

```http
HTTP/1.1 201 Created
Location: /thing/did%3Aigo%3A4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM%3D
Content-Length: 349
Content-Type: application/json; charset=UTF-8
Server: Ioflo WSGI Server
Date: Thu, 27 Jul 2017 22:16:15 GMT

{
  "did": "did:igo:4JCM8dJWw_O57vM4kAtTt0yWqSgBuwiHpVgd55BioCM=",
  "hid": "hid:dns:generic.com#02",
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