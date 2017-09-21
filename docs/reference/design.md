Indigo Project Specification

2017/09/20

# ​1.​ Overview

Indigo's goal is to provide an open privacy preserving lost and found service framework. Some services built on top of the Indigo framework may be proprietary. One of Indigo's goals is to support operation in a decentralized environment using a form of distributed consensus to manage the service.

## ​1.1.​ Database

The first part of this specification outlines the data formats for persistent data. The minimal requirement for the database is that it be persistent (on disk) and provide a key-value store. The database selected is [LMDB](https://en.wikipedia.org/wiki/Lightning_Memory-Mapped_Database). While other key-value stores have the required features. LMDB was selected because of its unusually high performance, maturity, and support. LMDB supports asynchronous concurrent reads and ACID writes. Readers do not block writers or other readers. Writers do not block readers. No application level caching is required. The main reason that only a persistent key-value is required is that redundancy, availability, and consistency across multiple host copies of the database will be provided via a Byzantine Agreement algorithm. Consequently clustering and other availability features of databases are not useful. Each entry in the key-value store might be a single value or a more complex data structure as represented by a JSON object, often called a document. Other features of LMDB that an implementation of Indigo using LMDB can take advantage of are that it has an ordered map interface, that is, keys are always lexicographically sorted. This can simplify the generation of secondary indices as well as speed up iterated primary access. Another feature is that each database can be configured to support duplicate entries per key. This can simplify the creation of entry logs.

## ​1.2.​ Development Language and Environment

The code for the *backend* will be developed in Python version 3.6+ . The reason for this selection is that the primary developer is most proficient in Python and the Python eco-system provides a relatively rich set of libraries and tools that can be used for development. Python is also known for its ease and rapidity of development. Because this is a new project there are no legacy Python dependencies that need to be supported. Consequently the latest version of Python, that is 3.6 is the minimum version of Python to used for this project. Python 3.6 is stable and has some performance improvements in addition to language features. The C Python3 bindings for LMDB are stable and well supported [LMDB](http://lmdb.readthedocs.io/en/release/). The library is on PyPI [lmdb PyPI](https://pypi.python.org/pypi/lmdb) and can be installed with pip3. The current version is 0.92.

```bash
$ pip3 install lmdb
```

## ​1.3.​ Serialization Format

The serialization format for structured data will be [JSON](http://www.json.org) (JavaScript Object Notation) . JSON supports data key-value data often called dictionaries. JSON serializations map nicely to Python dicts. Round-trip conversion between python dict objects and JSON objects is well supported. The documentation protocol data and database entries will be provided in JSON format. JSON also supports both UTF-8 and ASCII safe encodings of non-ascii characters in strings.

## ​1.4.​ ReST Inteface

The backend will provide HTTP based ReST interfaces for both client-to-server and server-to-server communications. The ReST interface will use JSON as the document body format.

## ​1.5.​ Security and Privacy

The indigo system is meant to be used eventually in a decentralized environment, that is, not behind a firewall under the control of a single entity. This means that the default policy for Indigo is that communications are all cryptographically signed and data is cryptographically signed at rest. Thus any data used in the system can be verified as being tamper proof . Signed at rest means that persisted data has stored with it a cryptographic signature. Any user of the data can then verify that the data has not been tampered with since is was created and signed by the originator of the data. Some data is meant to be private. Private data is cryptographically encrypted before signing and is encrypted in transit and is also stored encrypted at rest.

## ​1.6.​ Cryptographic System

Indigo uses the [NaCL](https://nacl.cr.yp.to) library developed by Dan Bernstein to provide cryptographic signatures and encryption. A popular C library implementation is called [Libsodium](https://download.libsodium.org/doc/). NaCL (libsodium) is a state of the art, open standard, publically well vetted, highly performant library that uses ECC (Elliptic Curve Cryptography). The python wrappr libsodium used for Indigo is [LibNacl](https://github.com/saltstack/libnacl). It is documented here [LibNacl Doc](http://libnacl.readthedocs.io/en/latest/). The signature protocol in NaCL is [EdDSA](https://en.wikipedia.org/wiki/EdDSA) or more commonly known as Ed25519. The encryption library supports what is called crypto box encryption that uses asymmetric keys to provide encryption with a layer of authentication. the XSalsa20 stream cipher and the Poly1305 MAC. Encryption keys use the ECC [Curve25519](https://en.wikipedia.org/wiki/Curve25519) standard and are meant to be exchanged using an Elliptic Curve Diffie-Hellman key exchange protocol X25519.

## ​1.7.​ Identifiers

The security and privacy requirements for Indigo mean that both signing and encryption keys are needed to both transmit and store data. To make this more straightforward, identifiers used in the system for data resources, components, or other entities, are linked to cryptographic identifiers or cryptonyms. The components associated with the cryptonyms essentially have a type of identity within the system that could support authentication via cryptographic signing and verification. Once authenticated, these cryptonymous identifiers could then be the basis for authorization against a policy for operations in the system. Privacy comes from encryption using encryption/decryption keys associated with each entity. For a background discussion on cryptographic identity see [Identity](https://github.com/SmithSamuelM/Papers/blob/master/whitepapers/Identity-System-Essentials.pdf). The fundamental idea is that an identity consists of one or more identifiers and attributes that are associated with those identifiers.

Data security in the Indigo system is primarily to prevent or detect from tampering. Tamper protection is provided by cryptographic signatures. Data is signed with a signing key using the EdDSA signature scheme. In the signing scheme, a key pair is created. The key pair consists of a private *signing* key and a public *verification* key. A signature is created by the *keeper* of the private key who uses that key in a signature generation algorithm on some data. The private key is never shared. Anyone can use the verification key to verify that the data has not been tampered with.

In Indigo the entity that has access to or controls the private signing key is the *keeper* of the key pair. Likewise the entity that signs data with that key is known as the *signer*. The *keeper*/*signer* is also known as the *controller* of the signed data because only the *controller* is allowed to make changes to that data. The *controller* is the source of the data that is signed for verification and validation. To restate, the *controller* of a signed data resource is  the *signer* of the data resource and the *keeper* of the associated private signing key for that signed data and other readers of the data may verify the signature attached to that data. Consequently control of identifiers and the associated data resources belongs to the entities that sign the associated data resources denoted by those identifiers. The Indigo system enforces this policy of authorizing changes to data resources by the *signer*,  as authenticated by signed requests for making those changes.

### ​1.7.1.​ Primary

In a key-value store each entry can be acessed via a primary key. The term *key* here does not mean cryptographic key but merely a string of bytes used as the primary index for a given value in the database. Primary keys by definition are unique. In distributed systems, with distribued databases, it can be difficult to ensure that all primary database keys are globally unique. One way to ensure global uniqueness is to have a centrialized service issue identifiers. Using a centralized service can impose a significant performance and reliability penalty on a distributed system. Consequently many distributed systems instead use GUIDs (globally unique identifers). A GUID achieves collison resistance (uniqueness) using large random numbers. A large enough random number makes it extremely improbable that any other component of the system will select the same random number. Thus basing primary keys on large random numbers may provide a very high probability of uniqueness without encuring a performance penalty. Cyrptographic keys are also generated using large random numbers and therefore also ensure uniqueness. For cryptographically signed data it would be useful to associate each database primary key with an associated cryptographic key. Thus the holder of the cryptographic key becomes the *controller* of the database record. Likewise data transmitted over the wire that is signed controlled ty the *signer*. Linking the primary key identifier with the signing key allows easier lookup of the associated verification key.

The [DID](https://docs.google.com/document/d/1Z-9jX4PEWtyRFD5fEyyzEnWK_0ir0no1JJLuRu8O9Gs/edit#heading=h.4dabf3er5xg1) (Decentralized Identifier) specification is a standard for building identifiers that can serve as GUIDs for database primary keys but also have associated with them cryptonyms that can thereby be used for signing and/or encryption. The Indigo system uses a simplified version of the DID specification. In Indigo DIDs are used both as primary identifiers for database records and for the secure transmission of data.

The basic DID format is as follows:

<table>
  <tr>
    <td>did:method:idstring
</td>
  </tr>
</table>


The suggested DID format for Indigo is as follows:

<table>
  <tr>
    <td>did:igo:abcdefghijklmnopqurst=</td>
  </tr>
</table>


The  *method* is the three letter abbreviation *igo*.

The  *idstring* is a 44 character Base64 URL-File safe  encoding as per [RFC-4648](https://tools.ietf.org/html/rfc4648) with one trailing pad byte of the 32 byte public verification key for an EdDSA (Ed25519) signing key pair. Unless otherwise specified Base64 in this document refers to the URL-File safe version of Base64. The URL-File safe version of Base64 encoding replaces "+" with “-” and  “\” with  “_”. 

Using a public key in the *idstring* ensures that the *idstring* is generated with sufficient randomness that it is unique. It also enables one to validate the creator of a DID by challenging them to use the associated private key to sign some challenge text. EdDSA public keys are 32 binary bytes long or 64 Hex encoded characters or 44 Base64 URL-File safe encoded characters (with one  byte trailing pad). Base64 is a compromise between size and ease of use. Because very large binary numbers (> 16 bytes) can be difficult represent on different computing platforms, cryptographic keys are typically represented as character strings or byte strings. Moreover, because non-ASCII characters are often difficult to manage, representations will often use ascii only characters in their encoding. Three common are Hex (Base16), Base64, and Base58Check. Because Indigo also has a human friendly secondary identifier (see below) Base64 is used as a compact yet easily convertible representation.

A primary feature of a DID derives from the fact that there is a unique private key associated with the public key used in the generation of the DID’s  *idstring*. Only the *keeper* of the private key can sign a challenge that is verified against the public key. Therefore only the original generator of the DID can prove that they are the DID creator. This enables an entity to create globally unique immutable identifiers that do not depend on any centralized authority, but can be cryptographically verified by others as belonging to the creating entity. Thus DIDs are a type of self-certifying identifier.

One of the best practices for security is to periodically change or rotate cryptographic keys, consequently, the actual key pair used to sign and verify a data resource identified by a DID may not be the same as the key pair originally used to generate the DID. Thus any data resource associated with a DID must also have a public *signer* field whose value is a JSON object that provides the signer's DID and the actual EdDSA public verifier key in Base64 URL-File safe encoding.

Associated with each data resource may also be a *signature*. EdDSA (Ed25519) signatures are 64 bytes long or 128 Hex characters long or 88 Base64 characters long (with two trailing pad bytes). An example is shown below.

Example Base64 URL-File safe encoded EdDSA signature:

<table>
  <tr>
    <td>"0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwx=="</td>
  </tr>
</table>


A simple example of the JSON format of a data resource could appear as follows:

```json
{
  "did": "did:igo:abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQR",
  "signer": 
  {
    "id": "did:igo:abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "key": "abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVWXYZ"
  },
  "data": "Hello World",
}
```


A more compact way to represent the *signer* id and public verification key is to store the keys in another data resource whose primary key is the signer's DID and then merely provide the DID of the signer. A fragment identifier is used to denote which public verification key was used for this specific signature. The verification key is then looked up.

An example is shown below:

Signer's data resource with indexed keys: (Note the signer is self referential)

```json
{
    "did": "did:igo:abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "signer": "did:igo:abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVWXYZ#0",
    "keys": 
    [
      {
        "key": "abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "kind": "EdDSA",
      },
      {
        "key": "abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVW123",
        "kind": "EdDSA",
      }
    ]
}
```


Data resource "owned" by *signer* and signed with key at index 1:

```json
{
  "did": "did:igo:abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQR",
  "signer": "did:igo:abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVWXYZ#1",
  "name": "John Doe",
  "zip": "94088"
}
```


### ​1.7.2.​ Secondary

Beacause DIDs are long strings of random characters, they are not very easy to remember or use. They are not very human friendly. Consequently Indigo supports a secondary identifier type that is more human friendly. For short this is referred to as an HID (Human friendly ID). One of the problems with human friendly identifiers is that it is much more difficult to ensure uniqueness. Typically some centralized authority is responsible for issuing identifiers or identifier prefixes that are supposed to be unique. Because the number of human friendly identifiers of a given length is limited, the identifiers come as some rental cost and may be reassigned if rent is not paid. These problems with human friendly identifiers can be managed as long as the primary identifier is unique and immutable. Consequently Indigo uses DIDs for the primary identifiers but also supports more human friendly HIDs for the secondary identifiers. Each primary identifier may have associated with it one and only one HID secondary identifier. HIDs must be unique within the Indigo system. Indigo does not manage an HID namespace but depends on externally managed HID namespaces such as DNS, Telephone, or email.

The format for the HID secondary identifiers is as follows:

<table>
  <tr>
    <td>hid:kind:issuer#index</td>
  </tr>
</table>


The kind field refers to the type of externally manage identifier name space from which the issuer is drawn. Indigo will natively support a small subset of secondary identifier namespace/issuer kinds for the purpose of validating the prefix. The initial set of supported *kind* values are

<table>
  <tr>
    <td>['dns', 'phone', 'email']</td>
  </tr>
</table>


The *issuer* is some externally managed managed identifier space such as DNS (internet domain name), such as, generic.com or a phone number such as 18005551212 or email such as joe@generic.com. 

The *index* is a string of characters that should be unique relative to the prefix. Because the *index* by itself is not globally unique it may be short and therefore more human friendly.

And example HID is given below:

<table>
  <tr>
    <td>hid:dns:generic.com#01</td>
  </tr>
</table>


An example of a data resource with a secondary identifier (HID) is as follows:

```json
{
  "did": "did:igo:abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQR",
  "signer": 
  {
    "id": "did:igo:abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "key": "abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVWXYZ"
  },
  "hid": "hid:dns:generic.com#01",
  "data": "Hello World",
}
```


Example using indexed signer key:

```json
{
  "did": "did:igo:abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQR",
  "signer": "did:igo:abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVWXYZ#1",
  "hid": "hid:dns:generic.com#01",
  "data": "Hello World",
}
```


## ​1.8.​ Identities, Entities, Agents, and Roles

Everything in the system is a Data Resource. All Data Resources have DIDs. A data resource will likely include some additional fields i.e. attributes. Consequently, a data resource is a form of identity because it has an identifier and attributes. Associated with a data resource may an entity  that controls that data resource. Control is indicated by the presence of a *signer* field in the data resource. The *signer* field value is a DID that references either the same or a different data resource. Data resources that are the referenced via a signer fields represent an entity.  There are two classes of entities represented in Indigo. The first class are referred to as *Agents* and are self-signing, that is, the value of the  *signer* field of their associated data resource is the DID of that same data resource.  The second class are referred to as *Things* and are not self signing, that is, the value of  the *signer* field of their associated data resource is the DID of some other data resource, typically an *Agent*. *Agents* can therefore control *Things* and transfer control of *Things* to other *Agents*. 

Data resources with a signer field have a public key associated with them for which an outside entity holds the corresponding private key. These outside entities are referred to as *Keepers*. Using the associated private keys, entities can participate in secure transactions with other entities by signing messages or data resources. 

In addition to a *signer* field data resources that include encrypted data may have *encryptor* and *decryptor* fields.  These field values are each the DID of an Agent data resource that stores the associated public encryption/decryption keys and indicates which entities are the *Keepers* of the associated private keys.

Agents may participate or interact with each other in the Indigo system using different roles. These roles are as follows:

* Server
* Owner 
* Finder
* Aspirant
* Issuer


These roles primarily have to do with how *Agents* interact with each other in the control of *Things*. Indeed, the main purpose of Indigo to provide *lost and found* services for physical items or *things*, such as a camera or mobile phone or bicycle. These *Things* are owned by some entity that is a user of the Indigo system and is represented in the Indigo system as an *Agent*. The different roles are used to describe the various transaction types supported by the Indigo system.

A *Server* *Agent* is serves a special role. A *Server* is supported by a server application that runs on a computing device, i.e. a host of an instance of the Indigo service. The other four *Agent* roles act as *Clients* to a given *Server*.  *Clients* are supported by a client application that is run on a different computing device and communicates with one or more *Servers* over a network.  A *Server Agent’s* main role  is to act as a trusted party in transactions between a *Client Agent* and the *Server Agent* or as a trusted third party in transactions between two other *Client Agents*. A given *Client* entity may from time to time participate in one or more of all four *Client Agent* roles. Because a *Server* may act as a trusted third party in secure transactions between two other parties a *Server* needs to be the *Signer* of data resources involved in those secure transactions. The server might also provide other secure services such as messaging where the *Server* needs to be the *Signer* of data resources. Because a *Server* entity interacts with the client applications, it is involved in secure communications with the clients and therefore needs to be the *Signer* of data resources in transit as well as data resources at rest.

An *Owner* *Agent* acts as the controller of one or more *Things*. Because an *Owner* interacts with the service using a client application, it is involved in secure communications with the *Server* and therefore needs to be the *Signer* of data resources in transit as well as data resources at rest.

A *Finder* *Agent* acts to return a found *Thing* to its  *Owner*. A *Finder* is not the *Owner* of a *Thing* but might have the physical item corresponding to the *Thing* in his/her possession. Because a *Finder* might engage in a secure transaction with an *Owner* of a *Thing* in order to return that physical item to the *Owner*, the *Finder* might be a *Signer*, at least temporarity of data resources associated with the secure transaction. Because a *Finder* entity interacts with the service using a client application, it is involved in secure communications with the server and therefore needs to be the *Signer* of data resources in transit as well as data resources at rest.

An *Aspirant* Agent acts to transfer ownership of a *Thing* from the current *Owner* to itself. In other words, an is *Aspirant* wishes to become an *Owner* of a *Thing* currently controlled by a different *Owner*. Because the transfer of ownership is performed with a secure transaction, the *Aspirant* needs to be the *Signer* of data resources associated with the secure transfer of ownership. Because an *Aspirant* entity interacts with the service using a client application, it is involved in secure communications with the server and therefore needs to be the *Signer* of data resources in transit as well as data resources at rest.

An *Issuer* Agent acts to manage the HIDs associated with *Things*. An *Issuer* is a special class of *Agent* the not only owns things but also controls the issuance of HIDs associated with its *Things*. An* Issuer* might manufacture or distribute multiple *Things* to multiple final *Owners*. An *Issuer* controls the human friendly namespace for an HID (Human friendly Identifier) used as a secondary identifier for *Things* originating from that *Issuer*. Because an *Issuer* entity interacts with the service using a client application, it is involved in secure communications with the server and therefore needs to be the *Signer* of data resources in transit as well as data resources at rest.

## ​1.9.​ Serialization Issues

One of the limitation of JSON is that the field order of a serialized JavaScript object is not normative, that is, a valid JSON serialization does not guarantee the order of appearance of the fields within a JavaScript object (or Python dict) that results from the deserialization. Likewise whitespace in a JSON serialization is not normative. Consequently round trip serializations and deserializations may not be identical and therefore would not verify against the same cryptographic signature. The background section of the document provides more detail on the associated *canonicalization* problem. The solution to this problem supported by Indigo is that the data associated with a signature is only serialized once by the *Signer*. Users of the data may deserialize but never re-serialize unless they also re-sign. Any compliant JSON deserialization will produce an equivalent Javascript object (same field names and values but order and whitespace are ignored).

Another issue is that many JSON implementation raise an error if a deserialization attempt on a string does not consume all the characters in the string. Thus a hybrid data string that consists of a serialized JSON object followed by a signature string might be difficult to deserialize with some JSON implementations. A portable approach is to concatenate the signature separated by a unique string of characters that will not be produced by a JSON serializer. Readers of the data first extract the JSON portion by searching for the separator string and then extract the signature. One such human friendly separator string is the 4 character sequence of whitespace characters, CR LF CR LF, where CR represents the CarriageReturn character (ASCII 13) and LF represents the LineFeed character (ASCII 10). In escaped notation this string is "\r\n\r\n". If these characters appear within a quoted string they are escaped by a JSON serializer. A standard compact JSON serialization does not insert white space. Thus to ensure compatibility serialization to be signed should be compact not pretty printed. In Indigo signed JSON serializations consist of the JSON followed by "\r\n\r\n' and then a JSON string with the signature.

The following is an example signed JSON representation that is serialized and stored in Indigo.

The data resource to be signed is as follows:

```json
{
  "did": "did:igo:abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQR",
  "signer": "did:igo:abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVWXYZ#1",
  "changed": "2000-01-01T00:00:00+00:00",
  "name": "John Doe",
  "zip": "94088"
}
```

Because this *signer* field of this data resource uses an indexed key identifier there must also be an associated *signer* data resource such as:

```json
{
    "did": "did:igo:abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "signer": "did:igo:abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVWXYZ#0",
    "changed": "2000-01-01T00:00:00+00:00",
    "keys": 
    [
      {
        "key": "abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "kind": "EdDSA",
      },
      {
        "key": "abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVW123",
        "kind": "EdDSA",
      }
    ]
}
```


This JSON object is serialized and signed to produce a signature string.

<table>
  <tr>
    <td>"0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"</td>
  </tr>
</table>


These are combined into concatenated JSON chunks separated by '\r\n\r\n' called a signed serialization, as follows:

```json
{
  "did": "did:igo:abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQR",
  "signer": "did:igo:abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVWXYZ#1",
  "changed": "2008-09-15T15:53:00",
  "name": "John Doe",
  "zip": "94088"
}
\r\n\r\n
"0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
```

The signed serialization is then stored at the database location given by the primary key did string, that is:

<table>
  <tr>
    <td>"did:igo:abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQR"</td>
  </tr>
</table>


A user of the data would first extract the serialized JSON data object as delimited by the separator string and then extract the following signature. The user would then get the verification key from the *signer* field in the JSON data object and then verify against the *signer's* signature.

## ​1.10.​ Agent Data Resource

*Agents* that act in the roles *Server, Owner, Finder, Aspirant, *and* Issuer *all share a basic set of fields in the associated data resource for their identity. The *Issuer* *Agent* has some additional fields associated with managing HIDs. The baseline *Agent* data resource is primarily used to store the keys used as a *Signer *to control other data resources such as *Things* and to engage in secure messaging transactions with other *Agents*. Moreover, a secure transfer of ownership of a *Thing* is a three way transaction between an *Owner*, an *Aspirant*, and the *Server*, each with a set of signing keys. Keeping the control separated between *Owner*, *Aspirant*, *Server* and *Thing* allows for transfer of control without race conditions such as double transfer of the same *Thing*.

An example *Agent *data resource expressed as a* * JSON object is as follows:

```json
{
    "did": "did:igo:abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "signer": "did:igo:abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVWXYZ#0",
    "changed": "2000-01-01T00:00:00+00:00",
    "keys":
    [
      {
        "key": "abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "kind": "EdDSA",
      },
      {
        "key": "abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVW123",
        "kind": "EdDSA",
      }
    ]
}
```


This is actually stored in the database as a wrapped serialization with signature (see the section above on Serialization Issues).  Of note is that the data resource is self-controlling or self-signing, in that the primary key DID field and the *signer* field refer to the same base DID. The "keys" field holds an indexed list of public signing keys used to control (sign and/or encrypt) data resources. Lookup of a DID with a key fragment identifier allows one to find a given key and also allows for key rotation or other key management operations. 

The *changed*  field is used to prevent replay attacks. The *Signer* must  only update the data resource with a monotonically increasing *changed* date time stamp. This policy allows a Server to detect stale changes and discard them. The *changed* field value must use the ISO-8601 standard  time zone aware UTC date time stamp which has the form 2000-01-01T00:00:00+00:00.

The fields shown are the required fields. A given *Agent* may choose to add additional fields to its data resource.

## ​1.11.​ Issuer Data Resource

The data resource for *Issuer* *Agent* has the same base fields as other *Agents*  but includes in addition an *hids* field.  An example *Issuer* *Agent *data resource expressed as a* * JSON object is as follows:

```json
{
  "did": "did:igo:abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVWXYZ",
  "signer": "did:igo:abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVWXYZ#0",
  "changed": "2000-01-01T00:00:00+00:00",
  "keys":
  [
    {
      "key": "abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVWXYZ",
      "kind": "EdDSA",
    },
    {
      "key": "abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVW123",
      "kind": "EdDSA",
    }
  ]
  "hids":
  [
    {
      "kind": "dns",
      "issuer": "generic.com",
      "registered: "2000-01-01T00:00:00+00:00",
      "validationURL" : "https://generic.com/indigo"
    }
  ]
}
```


This is actually stored in the database as a wrapped serialization with signature (see the section above on Serialization Issues).  Of note is that the data resource is self-controlling or self-signing, in that the primary key DID field and the *signer* field refer to the same base DID. The "keys" field holds an indexed list of public signing keys used to control (sign and/or encrypt) data resources. Lookup of a DID with a key fragment identifier allows one to find a given key and also allows for key rotation or other key management operations.

The *hids* field is an array of HID types that the *Issuer* controls. Each HID type has a *kind* for the *issuer *field* *value, the *issuer *field* * itself ,and a *registered* field whose value is the datetime for when the prefix was registered by the *Issuer* with Indigo. The *registered* field uses the ISO-8601 time zone aware UTC standard which has the form 2000-01-01T00:00:00+00:00.

Externally managed namespaces used for public identifiers may  undergo a change of ownership or control and may not be immutable. Consequently *Issuers* must validate their control over each HID *issuer *value. Each issuer *kind* may have a different validation procedure. For example, a "*dns*" kind might validate by running a service at a *validationURL* that the Indigo system can challenge to see if the controller of the DNS domain has the signing key for the *Issuer*. An "email" kind might validate by sending a challenge email. A given *Agent* may choose to add additional fields to its data resource.​1.12.​ 

## ​1.12.​ Thing Data Resource

The data resource that represents a *Thing* is always controlled by another entity typically an *Agent * entity usually acting as an *Owner* or  *Issuer*. In addition to the DID, which serves as both the primary identifier and primary database key, each *Thing* resource also has an HID which serves as a human friendly secondary identifier. This allows more human friendly lookup of the *Thing’s* data. Consequently the database should have a secondary index whose keys are *Thing* HIDs and whose values are *Thing* DIDs. Moreover another secondary index could be used to associated HIDs to the original *Issuer* the created the *Thing* resource.

An example *Thing * data resource expressed as a* * JSON object is as follows:

```json
{
  "did": "did:igo:abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQR",
  "hid": "hid:dns:canon.com#01,
  "signer": "did:igo:abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVWXYZ#1",
  "changed": "2000-01-01T00:00:00+00:00",
  "data":
  {
    "keywords": ["Canon", "EOS Rebel T6", "251440"],
    "message": "If found call this number",
  }
}
```


This is actually stored in the database as a wrapped serialization with signature (see the section above on Serialization Issues). The *signer* field refers to the controlling *Agent* such as an *Owner* or *Issuer*.

The *data* field stores optional identifier information about the *Thing* that might be used by a client to further identify the physical item. 

If present the *message* field in the *data* field object will be displayed by the client application when an object is looked up by a Finder.

## ​1.13.​ Encrypted Data Resource

Encrypted data resources also require and encryption/decryption key. Best practices for secure encryption/decryption exchange between two parties is to use asymmetric keys that are exchanged using a Diffie-Hellman key exchange that adds a type of authentication to the encryption/ecryption. This provides additional security against exploits. The NaCL (libsodium) library provides support for such ECC based Diffie-Hellman authenticated encryption (ECDH) with its crypto box function. As mentioned previously NaCL keys use the *Curve25519* standard. These are different from *Ed25519* (*EdDSA*) signing keys. Consequently a separate key identifier for encrypted data is required by any entity that owns encrypted data resources. Curve25519 public keys are 32 binary bytes long or 64 Hex encoded characters or 44 Base64 encoded characters (with padding).

The entity data resource indexed key list needs to include its public assymetric encryption keys.

Example entity resource with public encryption key denoted by the key "kind" field with value "Curve25519" :

```json
{
  "did": "did:igo:abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVWXYZ",
  "signer": "did:igo:abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVWXYZ#0",
  "changed": "2000-01-01T00:00:00+00:00",
  "keys":
  [
    {
      "key": "abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVWXYZ",
      "kind": "EdDSA",
    },
    {
      "key": "abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVW123",
      "kind": "EdDSA",
    }
    {
      "key": "abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVWabc",
      "kind": "Curve25519",
    }
  ]
}
```


In the two party Diffie-Hellman key exchange the actual keys used for encryption and decryption are never transmitted. Instead the asymetric private key of the first party is combined with the asymetric public key of the second party to generate a "shared" key. Likewise the second party uses its private key and the first party's public key to generate an equivalent "shared" key. The shared key is not a symmetric key. This approach is used for the exchange of data between two entities within Indigo. To generate the *shared* key requires knowledge of both the encryptor and decryptor entity.

When an entity encrypts data it becomes the *encryptor* of the data. In a two party exchange of encrypted data using ECDH the recipient of the data is the *decryptor*. Both these entities need to be identified in order that both know how the associated ECDH *shared* key for encryption/decription is to be generated from the associated public/private keys.

Example encrypted data resource with signature:

```json
{
  "did": "did:igo:abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQR",
  "signer": "did:igo:abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVWXYZ#1",
  "changed": "2008-09-15T15:53:00",
  "encryptor":     "did:igo:abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVWXYZ#2",
  "decryptor": "did:igo:abcdefghijklmnopqrABCDEFGHIJKLMNOPQRSTUVWXYZ#2",
  "crypt": "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
}
\r\n\r\n
"0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
```


The *encryptor* field provides a reference to the entity and public key (via fragment key index) that encrypted the data.

The *decryptor* field provides a reference to the designated entity and public key (vis fragment key index) meant to decrypt the data.

The *crypt* field provides the encrypted "crypttext" encoded in Base64 URL-File safe including padding (to a multiple of 4 characters).

Suppose for example the encrypted data comes from the following source JSON object:

```json
{
  "name" : "John Smith",
  "city" : "San Jose",
  "zip" : "94088",
  "phone" : "8005551212"
}
```


To generate the *crypt* field value, the encryptor first serializes the source data using JSON to generate the plaintext. The encryptor then generates a *shared* key from the private key associated with the referenced *encryptor* public key and the *decryptor* public key. The encryptor then encrypts the JSON serialized string to generate the crypttext. The encryptor then Base64 URL-File safe encodes and pads to a multiple of 4 the crypttext to create the value of the *crypt* field. The encryptor then JSON serializes the full data resource and signs and attaches the signature.

The decryptor first verifies the full data resourse against the attached signature. The Decryptor then JSON deserializes the data resource and decodes the Base64 URL-File safe value of the *crypt* field. The decryptor then decrypts using a *shared* key generated from the encryptor's public key and the decryptor's private key associated with the referenced decryptor's public key. The resulting plaintext is a JSON serialized object. The decryptor then deserializes to get the source data.

When an entity wishes to encrypt data for its own consumption, that is, the entity is using Indigo to store private data, then the entity is both the encryptor and decryptor. There are two ways to accomplish this. One is to for the entity to use two keys pairs of its own to generate the *shared* key. This requires no additional support. The other is for Indigo to support secret key or symmetric key encryption. Initially the former will be supported.

# ​2.​ Operations

## ​2.1.​ Registration

Each of the *Keeper* entities much register with the Indigo service. Registration provides the signing and encryption key references needed to engage in secure transactions between entities. 

Non-server agent registration should also provides spam resistance through friction in the registration process such as Capta or Robot detection in the associated user interfaces of the client applications.

For each *Agent* the associated client application creates at least one EdDSA signing key pair. The app may later create additional key pairs for signing, encryption or other security uses. The python libnacl function to create the key pair is shown below.

```python
signing_key = nacl.signing.SigningKey.generate()
verify_key = signing_key.verify_key</td>
```


Comparable functions exist in all the libsodium implementations for different languages.

The private key is stored locally on the client application. 

The client application also creates a DID for the registered resource  as per the DID section of this document. 

The zeroth key in the key list in the registered resource must be the public key used to generate the DID. The original registration request must be signed with the associated private key. This allows the Server to verify that the creator of the data resource is the Keeper of the associated private key. This restricts registrations of Agent DIDs to the entities who created the DIDs  and prevent imposters from using DIDs for which they were not the creators. This adds additional friction to the registration process

 This is one of the useful  features of using DIDs for identifiers in  that one can challenge a user of a DID to proof that they were the creator by signing with the  private key belonging to the public key used to create the DID..

The client application creates the associated JSON data resource.(As specified in 2)

The client application then serializes and creates a digital signature. These are concatenated as per the section above on Data Resource format. 

The client application makes a registration request call to an Indigo server that includes the signed serialization. The server validates the registration request and adds the *Agent* record to the database as well as updating any secondary indices.

### ​2.1.1.​ Issuer Registration

In  addition to the registration steps in the previous section. Check for authorization to be issuer  (TBD)

Validate control of any HID namespaces that are included in the Issuer Registration. 

## ​2.2.​ Thing Registration

Has the additional requirement that the issuer who is making  the request. that the issuer signer is controls the HID namespace provide in the Thing Registration data.



# ​3.​ Background

This section includes background information the is relevant to some the architecture design choices made in Indigo.

## ​3.1.​ Terminology

There is some ambiguity in terminology in these types of applications because of the intersection of "web application" terminology and "crypto application" terminology.

In this specification the following terms are defined:

verification: A cryptographically signed piece of data has the cryptographic signature verified against public key of supposed signer of that data

authentication: A token or signature associated with an action/request is verified relative to the creator of the request. This is the first step in securing a transaction. abbreviated authn

authorization: An authenticated entity is allowed to perform a given action/request relative to a rule or set of permissions. Abbreviated authz

validation: has two common conflicting uses:

1. narrow: validation of fields types and data types ranges values formats etc. So a write request that is changing a field value would be validated against the type of data (int, float, string, etc)

2. broad: validation about a given transaction step. Where all the other requirements (such as verification, authn/authz) in addition to the data types are also satisfied. One way to remove ambiguity is to qualify the term such as full transaction validation, field validation etc

## ​3.2.​ Semantic Links

A semantic link or id is a predefined id of a record in the database that is deterministically derived from the id of some other associated item. This means that there is a well known way to search for a record for any semantically link item resourse by using the rules for deriving the associated ID. This is essentially namespacing IDs. This simplifies managment since the orginal item record does not need to be updated to include an explicit link to newly generated but related resource. Using explicit links can be problematic in three party transactions there is a transfer of ownership. For an explicit link to be added to the item record, there would either need to be a handshake between the parties owning the linked resource or the link would have to be metadata not signed by the holder.

The DID specification provides an example of how one could implement a semantic link using a DID path. This is analogous to a URI path section delimted with / . So for example

"did:igo:abcdefghijklment/transfer" could be the id in the database of a semantically linked resource for holding the proffer record for the resourse given by "did:igo:abcdefghijklmen".

The same semntic link derivation approach can be used for any guaranteed services provided by the Notary with respect to an item as well as by the Vendor with respect to items created by the Vendor.

Using explicit links within an item record would then be used only for information that is completly under the control of the owner. One reason to bifurcate a data structure into multiple linked records would be if the permissions were different of if the associated data is optional.

## ​3.3.​ Signed at Rest

In a "signed at rest" architecture, data canonicality is a critical issue. Also updates to a data record cannot happen in parts because that breaks the signature. So any set of fields that are wrapped in a signature must be updated in-toto as a single write request with all the data fields re-serialized (both the changed and unchanged) and resigned. An approach where data is stored in chunks based on what is wrapped by a signature makes sense in this approach. This maps to a ReSTful API using the rest verbs "POST" for initial creating and "PUT" for update. The "PATCH" verb for partial update would not be used. The PUT body would include the fully serialized and signed copy of the data.

One must be careful about having any metadata that is not included in the signature wrapping. For example one of the known vulnerabilities of BitCoin, called transaction malleability, resulted from not including some metadata in the hash wrappers.

Indexes are updated at the time of write by the server which verifies, deserializes, extracts the metadata needed for the index, updates the index, and then saves the original serialized signed data.

### ​3.3.1.​ Data Canonization

Data canonization means that there is a universally defined way of serializing the data that is to be cyptographically signed.

The are few typical approaches to achieving data canonization.

1. Store the serialization and signature as a chunk.

The simplest is that the signer is the only entity that actually serializes the data. All other users of the data only deserialize. This simplifies the work to guarantee canonization. For example JSON is the typical data format used to serialize key:value or structured data. But the JSON specifcation for ser/deser treats whitespace characters as semantically unimportant as well as the order of appearance of keys. For a dictionary (key:value) data structure the typical approach is to represent it internally as a hash table. Most hash algorithms do not store data ordered in any predictable way (Python and other languages have support for Ordered Dicts or Ordered hashes which can be used ameliorate this problem). But from the perspective of equavalence, key:value data structures are "dict" equal if they have the same set of keys with the same values for each key. Thus deserialization can produce uniform equivalent "dict equal" results from multiple but differing serializations (that differ in whitespace and order of appearance of fields). Unfortunately the signatures for the differing but equivalent serializations will not match.

So in this case, only the signer ever serializes the data. The signer's serialization is canonical wrt the signature. Users of the data merely need to use a "dict equal" deserialization which is provided by any compliant JSON deserializer. So no additional work is required to support it across multiple languages etc. If the associated data also needs to be stored unserialized then validation of the data is performed by first verifying the signature on the stored serialization and then deserializing in memory and comparing field by field to the stored but unserialized version for equivalence. This is the approach taken for "signed in motion" protocols and many "signed at rest" approaches.

1. Implement perfectly canonical universally reproducibly serialization.

In this approach the serialized data that is signed is not stored but all implementations of the protocol or service use the exact same serialization method including white space and field order so that they can reproduce the exact same serialization that the original signer created when originally signing the data. This is difficult to achieve with something like JSON across multiple languages. Its usually more work to implement and more work to support because it usually means writing from scratch conformant JSON implementations or at the very least having tight control of how white space and order occurs and ensuring accross updates that this does not change. But many standards are based on this approach.

1. Use binary data structures

With binary data structures the canonical form is well defined but it is also highly inflexible. The advantages of flexibility and modularity from key/value store serializations such as JSON usually makes 1) or 2) the preferred approach.

I think that if we are careful in the design we can actully start with 1)

## ​3.4.​ Privacy and Notifications

The worst case for protecting privacy is a malicious server that colludes with either the finder or holder in an exchange of data. Even though a server is a member of a BA pool, a single colluding server has access to all the server owned data. A malicious server could then share that data with either the Holder or Finder.

Consequently the only truly private data is data that is encrypted by either the Finder or Holder and the server never has access to the associated decryption keys.

This becomes an issue with notifications.

When a notification is push it requires an address of the destination. Hence for the server to push data out to a client it needs an address. This means the address is no longer private to the other party if the server is colluding.

For an IP protocol this means at least that the IP address of the client is known to the server and can be used to infer country, state, and city if not neighborhood of the client. This does not identify the exact client or the clients name or street address.

We could implement some sort of onion routing protocol to hide the ip addresses of the clients but third party services already provide such capability. Consequently Indigo would not preserve IP privacy but could suggest that the user could by using one of these IP anonymity services.

With mobile devices push notifications can happen is different ways. Both IOS and Android support a type of poll/push over ip where a mobile device registers for push when the app is either running in the foreground or background. Then the cloud services of the mobile OS now have a temporary IP address to push out notifications. Thus indigo's back end could plug into those cloud services notification APIs and push using IP only

Another approach is to use SMS Text and directly push notifications using the phone number of the device. This then exposes the phone number to the Server and allows a colluding server to publicize the phone number. This alternative should require user permissions.

Anther approach is to use email to push notifications. But once again this allows publication of the email. Likewise social messaging apps such as linkedin and facebook also could be used but at the cost of exposing the social identity.

The simplest approach is to use polling for notifications. This requires that the clients periodically access the server and send read requests to on their associated message queues. While not as performant as push it has the lowest privacy exposure risk. Over time it is probably worth while to plug into the cloud notification services for each mobile OS.

## ​3.5.​ Distributed Architecture and Decentralized Identifiers

The biggest trend in distributed application architecture, with good reason, is toward ReSTful micro services (with varying degrees of restive RPC). (This is by in large replacing the enterprise service bus architecture) One key aspect of this trend is to map elements of the application as resources that have public addresses expressed using the open standard URL/URI/URN schema with ReSTful micro services. Distributed application architecture is also enabled by the use of GUIDs (Globally Unique Identifiers) for internal or private data resources. The key feature of a GUID is that it can be generated in a decentralized fashion but still have collision resistance, that is, distributed components of the application can generate GUIDs and depend on the entropy/randomness to ensure that the GUID are globally unique without having to check with a central identifier repository or registry. The combination of GUIDs for private global decentralized identifiers and URIs for public global decentralized identifiers enable distributed applications to manage information across the application. combined with restful micro services there is a great degree of decoupling that allows flexible and modular construction of complex distributed applications.

The problem is that GUIDs assume that the distirbuted application is secure and operates behind a firewall. URI's depend on the security of the associated domain schema for security and suffer from the fact that it is not immutable. URN's by the way are supposed to be immutable identifiers but there is no universal mechanism to provide URN support. The missing feature for both GUIDs and URI/URL/URN is a cryptographically secure proof of ownership of the identifier and by association any data/resource represented by the identifier.

The solution is to use a decentralize public/private key pair for signing and verification of ownership of the decentralized identifier. The DID specification main goal is to provide such an identifier. It is a misnomer to think of DIDs as merely "identity system specific" identifiers. They are not. They are more general they are designed to replace or augment URI/URL/URNs and GUID with a single identifier that is collision resistant and cryptographically verifiable.

From the DID specifiction:

1.2. URIs, URLs, and URNs In September 2001, the W3C issued a note clarifying the terms URI (Uniform Resource Identifier), URL (Uniform Resource Locator), and URN (Uniform Resource Name). The key difference between these three categories of identifiers are:

URI is the term for any type of identifier used to identify a resource on the Web. URL is the term for any type of URI that can be resolved or de-referenced to locate a representation of a resource on the Web (e.g., Web page, file, image, etc.) URN is the term for a specific type of URI intended to persistently identify a resource, i.e., an identifier that will never change no matter how often the resource moves, changes names, changes owners, etc. URNs are intended to last forever.

1.3. Motivations for DIDs The growing need for decentralized identity has produced three specific requirements for a new type of URI that fits within the URI/URL/URN architecture, albeit in a less traditional way:

A URI that is persistent like a URN yet can be resolved or de-referenced to locate a resource like a URL. In essence, a DID is a URI that serves both functions. A URI that does not require a centralized authority to register, resolve, update, or revoke. The overwhelming majority of URIs today are based on DNS names or IP addresses that depend on centralized authorities for registration and ultimate control. DIDs can be created and managed without any such authority. A URI whose ownership and associated metadata, including public keys, can be cryptographically verified. Control of DIDs and DDOs leverages the same public/private key cryptography as distributed ledgers.

An architecture based on globally unique but verifiably owned identifiers (DIDs) enables distributed applications outside of firewalls. So building a system using DIDs instead of GUIDs is the first step. In a microservices schema that uses HTTPS one has to use URI/URL but those can be mapped to DIDs under the hood much the same way that current micro service applications map URIs to GUIDs.

So the archtitectual decision that needs to be made is: Do we roll our own DID like schema (providing verifiable ownership to a GUID) or do we leverage the existing momentum behind the DID specification.?

## ​3.6.​ Replay Attack Prevention

Although all resource write requests are signed by the client and therefore can not be created by anyone other than the Keeper of the associated private key, a malicious network device could record and resend prior requests in a different order (replay attack) and thereby change the state of the database. To prevent replay attacks on requests that change data resources a client needs to authenticate in a time sensitive manner with the server.  A simple way to do this is for the client to update the *changed* date time stamp field in the resource in a monotonically increasing manner. This way any replayed but stale write requests can be detected and refused by the Server. In other words the server will deny write requests whose *changed* field date time stamp is not later than the the *changed* field value of the pre-existing resource to be updated.

The typical approach to HTTP This is accomplished by the use of a challenge from the server to the client that includes a time stamp and  a random nonce. The standard approach for doing authentication in HTTP is to follow [RFC 7235](https://tools.ietf.org/html/rfc7235). Unfortunately RFC 7235 assumes password authentication not signatured based authentication. An approach that uses signatures is [RFC 7486](https://tools.ietf.org/html/rfc7486) HTTP Origin-Bound Authentication (HOBA). A simplified approach similar to HOBA but using EdDSA signatures will be used here for any requests that change the state of the data resources. These are POST, PUT, and DELETE.

The basic approach is as follows:

- Client makes request

- Server responds with 401 Status and with a WWW-Authenticate header with challenge text that includes a random nonce. The server stores the challenge for a limited time.

- Client signs the challenge text and responds with the addition of an Authorization header that includes the client signature to the challege in an auth-param named "result" as well as the original request body and headers.

- Server verifies signature in the Authorization header against the challenge and accepts the orginal request or if it is stale or fails verification denies the request with a 403 error status.


