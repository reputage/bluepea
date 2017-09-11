# BluePea Install


Ubuntu 16.04

------------
Update distro
------------

```bash
$ sudo apt update  
$ sudo apt upgrade  
$ sudo apt full-upgrade  

$ sudo reboot now
```

------
install packages
--------

```bash
$ sudo apt install build-essential libc6-dev
$ sudo apt install libgdbm-dev
$ sudo apt install libncursesw5-dev 
$ sudo apt install libssl-dev openssl
$ sudo apt install libffi-dev
$ sudo apt install dnsutils
$ sudo apt install libevent-dev
$ sudo apt install python3-dev
$ sudo apt install python3-virtualenv
$ sudo apt install curl
$ sudo apt install netcat
$ sudo apt install nmap
$ sudo apt install tcpdump
$ sudo apt install dhcpdump
```

--------
set up git
--------

```bash
$ sudo apt install git

Enable git credential helper
$ git config --global credential.helper cache
$ git config --global credential.https://github.com.username  githubusername

$ git config --global user.name "githubusername"
$ git config --global user.email "useremail"
```

-------
Install Libsodium 13 from source
------------

```bash
$ cd ~/code

$ wget https://download.libsodium.org/libsodium/releases/libsodium-1.0.13.tar.gz  
$ tar -zxvf libsodium-1.0.13.tar.gz  
$ cd libsodium-1.0.13  
$ ./configure  
$ make && make check  
$ sudo make install  
```

-------
Install Python 3.6.X from source
------------

```bash
$ cd ~/code
$ wget https://www.python.org/ftp/python/3.6.2/Python-3.6.2.tgz
$ tar -zxvf Python-3.6.2.tgz
$ cd Python-3.6.2
$ ./configure
$ make
$ sudo make install

$ which python3
/usr/local/bin/python3
```
-------
Install python packages
--------

```bash
$ sudo -H pip3 install -U setuptools pip wheel
$ sudo -H pip3 install simplejson
$ sudo -H pip3 install falcon
$ sudo -H pip3 install arrow
$ sudo -H pip3 install pytest
$ sudo -H pip3 install pytest-falcon
$ sudo -H pip3 install lmdb
$ sudo -H pip3 install libnacl
```

--------
Install ioflo
----------

```bash
$ sudo -H pip3 install ioflo
```

or if want the latest source code

```bash
$ cd ~/code
$ git clone https://github.com/ioflo/ioflo.git
$ sudo -H pip3 install -e ioflo
```
If this is already installed pull to get the latest from github

```bash
$ cd ioflo
$ git pull
```

-------
Install BluePea source
------------

```bash
$ cd ~/code
$ git clone git clone https://github.com/indigo-d/bluepea.git

$ sudo -H pip3 install -e bluepea
```

If this is already installed pull to get the latest from github

```bash
$ cd ioflo
$ git pull

$ cd ~
```
Run bluepea

```bash
$  bluepead -v concise -r -p 0.0625 -n bluepea -f bluepea/src/bluepea/flo/main.flo -b bluepea.core
```

```bash
----------------------
Starting mission plan 'main.flo' from file:
    /home/odroid/code/bluepea/src/bluepea/flo/main.flo
Starting Skedder 'bluepea' ...
   Starting Framer 'setup' ...
To: setup<<startup> at 0.0
*** Starting Server ***
*** Starting Tracker ***
   Starting Framer 'server' ...
To: server<<server> at 0.0
Opened server 'main.server.valet' at '('127.0.0.1', 8080)'
   Starting Framer 'tracker' ...
To: tracker<<tracker> at 0.0

```

Test navigate browser to
http://127.0.0.1:8080/server

```json
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


```http
Parsed Request:
GET /server (1, 1)
lodict([('host', '10.0.2.84:8080'), ('upgrade-insecure-requests', '1'), ('accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'), ('user-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8'), ('accept-language', 'en-us'), ('accept-encoding', 'gzip, deflate'), ('connection', 'keep-alive')])
bytearray(b'')
```

To change from running in test mode to real mode change this line in main.flo

```
init main.server.test to True
```

To

```
init main.server.test to False
```