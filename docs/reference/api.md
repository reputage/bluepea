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



## Agent Registration

Agent Registration creates a data resource corresponding to a given Agent. This
is a self-signed or self-owned data resource in that the signer field value
references is the self-same data resource.

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

# registration is the body text for the registration request. It is a json serialization
# signature is the Base64 URL safe encoding of theEdDSA signature of registration body

```

It is the responsibility of the client application to store the private signing
key as it will be needed to make any future changes to the resultant agent data
resource.

The request is made by sending an HTTP POST to ```/Agent/Registration```

The request includes a custom "Signature" header whose value is the signature
produced above. The request body is the registration text produced above.

A successful request results in a response with the associated Agent data resource
in the JSON body of the response is and a location header
whose value is the URL to access the Agent Data Resource via a GET request.
This location value has already been URL encoded.

A successful request will return status code 201

An unsuccessful request will return status code 400.

Example requests and responses are shown below.

## Request

```http
POST /agent/register HTTP/1.1
Signature: B0Qc72RP5IOodsQRQ_s4MKMNe0PIAqwjKsBl4b6lK9co2XPZHLmzQFHWzjA2PvxWso09cEkEHIeet5pjFhLUDg==
Content-Type: text/html
Host: localhost:8080
Connection: close
User-Agent: Paw/3.1.1 (Macintosh; OS X/10.12.5) GCDHTTPRequest
Content-Length: 249

{
  "did": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
  "signer": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0",
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
Location: /agent/register?did=did%3Aigo%3AQt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE%3D
Content-Length: 215
Content-Type: application/json; charset=UTF-8
Server: Ioflo WSGI Server
Date: Thu, 29 Jun 2017 23:16:46 GMT

{
  "did": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
  "signer": "did:igo:Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=#0",
  "keys": [
    {
      "key": "Qt27fThWoNZsa88VrTkep6H-4HA8tr54sHON1vWl6FE=",
      "kind": "EdDSA"
    }
  ]
}
```
