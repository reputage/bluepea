# Indigo Service API

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
```

Where tag is the name of a field in the body of the request whose value
is a DID from which the public key for the signature can be obtained.
If the same tag appears multiple times then only the last occurrence is used.

Each signature value is a doubly quoted string ```""``` that contains the actual signature
in Base64 url safe format. By default the signatures are 64 byte EdDSA (Ed25519) signatures that have been encoded into BASE64 url-file safe format. The encoded signatures are 88 characters in length and include two trailing pad characters ```=```.

An optional tag name = *kind* with values *EdDSA* or *Ed25519* may be present.
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

```http
/server GET

/agent  POST
/agent?did={did} GET

/agent/{did}  GET
/agent/{did}  PUT

/thing  POST
/thing?did={did} GET

/thing/{did}  GET
/thing/{did}  PUT
```

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

## Request

```http
GET /server HTTP/1.1
Content-Type: application/json; charset=utf-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.1 (Macintosh; OS X/10.12.5) GCDHTTPRequest
```

## Response

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

## *Agent* Write (PUT) by DID

This Agent write request (PUT) overwrites a data resource corresponding to a given Agent as indicated by the *did* in the URL.
The request is made by sending an HTTP PUT to ```/agent/{did}``` with a *did* whose value is the desired DID. The brackets indicate substitution. This value needs to be URL encoded. Because a PUT can change the signer field in the data resource, the PUT request Signature header must have two signatures. The tag 'signer' signature is the signature using the key indicated by the new value that the data resource will have once the PUT is successful. The tag 'current' signature is the signature using the key indicated by the current value of the data resource before it is overwritten. This allows to server to verify that the request was made by the current signer and that the new signer signature is provided so that the resource is signed at rest.

A successful request will return status code 200. An unsuccessful request will return an error status code such as 404 Not Found.


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

## *Issuer* *Agent* Creation 

When the Agent Registration creation request includes an *hids* field then the  data resource represents an *Issuer* agent. This effectively registers the *Issuer* with the Indigo service. The creation request will also validate control of the associated *hid* namespaces.  The *hids* field is a list of one or more HID json objects. Each object contains information about a namespace used by the *Issuer* to generate HIDs:

```json
"hids":
[
  {
    "kind": "dns",
    "issuer": "generic.com",
    "registered": "2000-01-01T00:00:00+00:00",
    "validationURL": "https://generic.com/indigo"
  }
]
```

Example requests and responses are shown below.

## Request

```http
POST /agent HTTP/1.1
Signature: signer="f2w1L6XtU8_GS5N8UwX0d77aw2kR0IM5BVdBLOaoIyR9nzra6d4JgVV7TlJrEx8WhJlgBRpyInRZgdnSf_WQAg=="
Content-Type: application/json; charset=UTF-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.1 (Macintosh; OS X/10.12.5) GCDHTTPRequest
Content-Length: 473

{
  "did": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
  "signer": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0",
  "changed": "2000-01-01T00:00:00+00:00",
  "keys": [
    {
      "key": "Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
      "kind": "EdDSA"
    }
  ],
  "hids": [
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
Location: /agent?did=did%3Aigo%3AQt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE%3D
Content-Length: 397
Content-Type: application/json; charset=UTF-8
Server: Ioflo WSGI Server
Date: Tue, 11 Jul 2017 01:07:26 GMT

{
  "did": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
  "signer": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0",
  "changed": "2000-01-01T00:00:00+00:00",
  "keys": [
    {
      "key": "Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
      "kind": "EdDSA"
    }
  ],
  "hids": [
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
GET /agent?did=did%3Aigo%3AQt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE%3D HTTP/1.1
Content-Type: application/json; charset=utf-8
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.1 (Macintosh; OS X/10.12.5) GCDHTTPRequest
```

## Response

```http
HTTP/1.1 200 OK
Signature: signer="f2w1L6XtU8_GS5N8UwX0d77aw2kR0IM5BVdBLOaoIyR9nzra6d4JgVV7TlJrEx8WhJlgBRpyInRZgdnSf_WQAg=="
Content-Type: application/json; charset=UTF-8
Content-Length: 473
Server: Ioflo WSGI Server
Date: Tue, 11 Jul 2017 01:19:04 GMT

{
  "did": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
  "signer": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0",
  "changed": "2000-01-01T00:00:00+00:00",
  "keys": [
    {
      "key": "Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
      "kind": "EdDSA"
    }
  ],
  "hids": [
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

Each Thing has a unique DID. The Server will also verify that the client application holds the associated private key used to create the Thing's DID. To create a DID the client application will first need to create an EdDSA signing keypair.

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