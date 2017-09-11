# BluePea Install MacOs

MacOs 10.12.x Sierra

--------------------------------
Install MacOs Command Line Tools
--------------------------------

Either install Xcode using the app store application or just install the command line tools using terminal.

Using terminal

```bash
$ xcode-select --install
```

--------------------------------
Install Homebrew
--------------------------------

```bash
$ ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
```

Now you can run homebrew using the "brew" command from terminal. Homebrew puts everything in /usr/local so it does not clobber Apple installed libraries and binaries.

You may have to to add /usr/local/bin to your bash shell path. You can do this by adding the following to your .bashrc file

```bash
#Add paths for non-interactive non-login shells such as ssh remote command

# /usr/local/sbin prepend
echo $PATH | grep -q -s "/usr/local/sbin"
if [ $? -eq 1 ] ; then
    PATH=/usr/local/sbin:${PATH}
    export PATH
fi

# /usr/local/bin prepend
echo $PATH | grep -q -s "/usr/local/bin"
if [ $? -eq 1 ] ; then
    PATH=/usr/local/bin:${PATH}
    export PATH
fi

echo $MANPATH | grep -q -s "/usr/local/share/man"
if [ $? -eq 1 ] ; then
    MANPATH=/usr/local/share/man:${MANPATH}
    export MANPATH
fi


# If not running interactively, don't do anymore just return so sftp works:
[ -z "$PS1" ] && return
```


Check homebrew installation.

```bash
$ brew doctor
```

Upgrade homebrew.

```bash
$ brew update
$ brew upgrade
$ brew doctor
```

-----------------
Install Python3.6
-----------------

This puts Python3.6 in /usr/local so it does not clobber the system installed python. However one may want to use a python virtual environment instead. (There are lots of good references on the web for installing into a python virtual environment)

```bash
$ brew install python3
$ brew linkapps python3
```

Now python3 is installed and can be run from the command line in terminal.

```bash
$ $ which python3
/usr/local/bin/python3

$ python3
Python 3.6.2 (default, Jul 17 2017, 16:44:45) 
[GCC 4.2.1 Compatible Apple LLVM 8.1.0 (clang-802.0.42)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> 
```

pip3 is also installed and will install packages to the newly installed Python3 in /usr/local/bin

Update pip and install tools

```bash
$ pip3 install --upgrade pip setuptools wheel
```

-------------------
Install libsodium
-------------------

```bash
$ brew install libsodium
```

----------------
Install git
-----------------

If git is not already installed you can install it with homebrew.

```bash
$ brew install git git-flow git-extras
$ git config --global credential.helper osxkeychain
$ brew install git-credential-manager
```

-------
Install python packages
--------

```bash
$ pip3 install libnacl
$ pip3 install simplejson
$ pip3 install falcon
$ pip3 install arrow
$ pip3 install pytest
$ pip3 install pytest-falcon
$ pip3 install lmdb
```

--------
Install ioflo
----------

Two choices:

The first is just to install the latest ioflo version as a package.

The second is to clone the git repo so you can get the latest changes.

If you are doing development install the second one.

1) Package install
```bash
$ pip3 install ioflo
```

2) Repo install

```bash
$ cd ~/code
$ git clone https://github.com/ioflo/ioflo.git
$ pip3 install -e ioflo
```
Once this is installed use git pull to get the latest from github

```bash
$ cd ioflo
$ git pull
```

------------
Install BluePea source
------------

```bash
$ cd ~/code
$ git clone git clone https://github.com/indigo-d/bluepea.git

$ pip3 install -e bluepea
```

Once installed pull to get the latest from github.

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