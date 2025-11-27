# mpv-super-remote
Remote for mpv player, uses python web server, works on linux. Use vlc for windows

2025-11-27-1

download files, start them. works on linux. requires python and mpv.

chmod 755 scriptname.py first.  
or enable run in file manager  
start by typing: python mpvs.py, or start linuxstart.sh  

open ip address in web browser on phone, ip is displayed in start script status.  
you should probably set static ip on pc first, so you can add bookmark to browser on phone.  
script should start mpv, by itself, do not close it, if you want to use remote.  

**VLC**

for windows use vlc. you can also use vlc remote on windows:

```
enable web interface in vlc:
vlc
tools/preferences
'all' at the bottom
interface/main interface
(DO NOT change 'inferface module' from 'Default' to 'http'!)
web=enable
interface/main interface/Lua
password=1
directory index=enable
port=80808

restart vlc

find ip of your pc:
command line: ipconfig /all
open ip in web browser in window
http://192.168.1.27:8080
do not enter user name, enter password: 1
```


todo, maybe:  
- sleep, shut down button on remote?
- close mpv button?
