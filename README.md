# MESHTASTIC scripts

A collection of python scripts for meshtastic devices.
## Installation

Need to install meshtastic and pubsub python library
`pip3 install meshtastic pubsub`

On mac you need to create venv
```
python3 -m venv meshtastic
cd meshtastic
source ./bin/activate
pip3 install meshtastic
pip3 install pubsub
```
Or you can:
```
python3 -m venv meshtastic
cd meshtastic
source ./bin/activate
pip install -r requirements.txt
```



## Commands ping_pong_network.py

From your another meshtastic device you write message to device which is controlled by this scripts.

Now is there three commands you can send.

```
ping
info
infotest
```
### PING

When the script recieve message "ping" it will answer with ```pong - current time```

### INFO


### INFOTEST
## TODO

- [x]  Write basic README
- [ ]  Write README for all commands

