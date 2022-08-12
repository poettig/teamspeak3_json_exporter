# TeamSpeak 3 JSON Exporter
Exports the current state of a TeamSpeak 3 Server as easily parsable, hierarchical JSON

## Where do I get the WebQuery API token from?
To get the token, you have to login to your TeamSpeak3 ServerQuery via the Raw (default port 10011) or ssh (default port 10022) method. This works easiest with netcat. Once you are connected, login and request a token with `scope=manage` like shown below. This scope basically has admin rights on the server, but is necessary to get the server name. Yes, the TeamSpeak3 security concept is this stupid. `lifetime=0` sets the key lifetime to unlimited. This any other positive integer `x` sets the API key lifetime to `x` days.

```
$> netcat localhost 10011
TS3
Welcome to the TeamSpeak 3 ServerQuery interface, type "help" for a list of commands and "help <command>" for information on a specific command.
login serveradmin password
error id=0 msg=ok
apikeyadd scope=manage lifetime=0
apikey=<API-KEY-REDACTED> id=8 sid=0 cldbid=1 scope=manage time_left=unlimited created_at=1660261830 expires_at=1660261830
error id=0 msg=ok
apikeylist
id=8 sid=0 cldbid=1 scope=read time_left=unlimited created_at=1660261830 expires_at=1660261830
error id=0 msg=ok
quit
error id=0 msg=ok
```
