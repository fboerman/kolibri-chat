kolibri-chat
============

chatserver en client written in python using socketserver module

use the -h or --help argument in commandline to see on how to use

the example users have as password the same as username (ie admin1 admin1, etch)

changelog
---------

v0.9:
* list command now gives users for all rooms if your admin
* added adduser command for both client and server
* added command admin to set adminlevel of user for both client and server
* added reload command to reload the database from from file
* added savedb command to save database to file for server
* passwords are now hashed
* added changepass command to change the password of a user for both client an server
* added changeownpass command to change your own password for client

v0.8:
* adminlevels
* adminlevel 1 cant kick fellow admins
* added commands for ipban en userban for both server and client, requires admin level 2 on clientside
* added unban commands for these actions, same rules aply
* added server commmand userlist and ipbanlist

v0.7:
* serverconsole can now kick user
* new command: list gives a list of connected users both on server and client
* new command: whipser user message : sends message to specified user only
* added a exe package for the client, for users who dont have python installed. needs to be called from commandline

v0.6:
* global broadcast for events such as connecting user
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