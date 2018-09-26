# cursedboard
Ncurse based textboard for ssh. 
> ssh whisper.onthewifi.com

- Shitpost in style with markup 
- Browse with arrow keys and vim style commands 
- Sqlite3 backend scaling to the moon and beyond
- ~~Countryball~~ Countryletter posting
- File Browser, Image and Text Viewer for the full multimedia experience
- Customize your experience automatically via ssh\_config
- Fuelled by npyscreen

### User settings with ~/ssh\_config

```
   Match User bit Host whisper.onthewifi.com
       RemoteCommand jump_to_bottom=True
       RequestTTY force
```

Currently available settings:
- jump\_to\_bottom Automaticall scroll to bottom of thread


### Setup
Needs python3, npyscreen and GeoIP. Use pip3 install -r requirements or packages provided by your distribution 

1. Run git submodule init and git submodule update to get img2txt
2. Install dependencies
3. Change motd.py to your likening 
4. Create a dedicated unix user
5. Copy config.py-sample to config.py and adjust settings
6. Touch .hushlogin in the user directory to avoid an IP leak
7. Disable TCP Forwarding for the user in sshd\_config 
8. Disable the sftp Subsystem or make sure its not set to internal-sftp in sshd\_config
9. ???
10. Comfy Posting 
