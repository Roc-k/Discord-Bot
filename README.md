To use the bot, create a file called "key.txt" which contains the bot key, and a file called "servers.txt" which contains all servers the bot will be used on seperated by a newline and run rob_ot.py, this should automatically create servers.json and reminders.json

You will also need to configure your user and admin roles, which is doable if you have one of the following roles:
 ["admin", "owner", "Admin", "Owner"], or edit the servers.json file directly


Currently some of the features crash out when given invalid keys, the bot still works, but I'll be trying to fix these once I have time 

If you want to use the bot and don't want the verify feature (it's very server specific), just comment out the line add_verify(bot, servers)
in rob_ot.py


If you want to fork(or want me to think about adding specific features), let me know, I'd love to hear your thoughts on the bot

