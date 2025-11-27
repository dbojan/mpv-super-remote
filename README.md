# mpv-super-remote
Remote for mpv player, uses python web server, works on linux. Use vlc for windows

2025-11-27-1

download files, start them. works on linux. requires python and mpv.

start by typing: python mpvs.py, or start linuxstart.sh  
chmod 755 scriptname.py first.  
or enable run in file manager  



**vlc**
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
