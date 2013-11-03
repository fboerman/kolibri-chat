kolibri-chat
============

chatserver en client written in python using socketserver module

use the -h or --help argument in commandline to see on how to use

changelog
---------
v0.6:
* global broadcast for new users
* user can now be an admin
* admins can kick users from server (only if they are in the same room)
* some code optimalizations
* server console now supports commands say and help

v0.5
* added switching chatrooms and some code optimalization

v0.4
* added chatrooms -> extra parmeter for server: number of chatrooms

v0.3
* added user authentication

v0.2
* added message authentication
* added proper error handling for both server and client

v0.1
* basic networking