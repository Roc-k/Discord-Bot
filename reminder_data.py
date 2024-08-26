import json
from typing import Dict, Union
import asyncio
from reminder_class import Reminder, Server



class ReminderDataLoader():
    ''' 
    Handles all writing and reading to files so that we don't have to worry about async race errors
    May not be coded well enough to actually avoid race errors
    '''
    def __init__(self):
        # Create a lock object so that certain commands only run one at a time
        self.lock = asyncio.Lock()
        self.load_initial_reminders()
        self.load_initial_servers()

    def load_initial_reminders(self):
    
        with open('reminders.json', 'a+') as openfile:
            pass
        with open('reminders.json', 'r') as openfile:
            try:
                self.reminderDict = json.load(openfile)
            except json.decoder.JSONDecodeError:
                self.reminderDict = {}


    def load_initial_servers(self):
        with open('servers.json', 'a+') as openfile:
            pass
        with open('servers.json', 'r') as openfile:
            try:
                self.serverDict = json.load(openfile)
            except json.decoder.JSONDecodeError:
                self.serverDict = {}
        with open('servers.txt', 'r') as openfile:
            servers = openfile.readlines()
            self.servers = [line.strip('\n') for line in servers]
        
        update = False
        for i in self.servers:
            if str(i) not in self.serverDict:
                self.serverDict[str(i)] = Server(str(i))
                update = True
        if(update):
            asyncio.run(self._updateServers())


    
    async def _updateReminders(self):
    # Serializing json
        json_object = json.dumps(self.reminderDict, indent=4)
        with open("reminders.json", "w") as outfile:
            outfile.write(json_object)

    async def get_all_reminders(self) -> Dict[str, Dict[str,any]]:
        async with self.lock:
            return self.reminderDict
        
    async def get_reminder(self, guild:str, title:str) -> Reminder:
        rem = Reminder.from_dict(guild, title, (await self.get_all_reminders())[guild][title])
        return rem

    async def add_Reminder_Dict(self, server:str, title: str, reminder: Dict[str,Union[str, int, bool, list]]):
        async with self.lock:
            try:
                self.reminderDict[server] is None
            except KeyError:
                self.reminderDict[server] = {}
            # print(reminder)
            print(server)
            self.reminderDict[server][title] = reminder
            await self._updateReminders()

    async def add_Reminder(self, reminder: "Reminder"):
        await self.add_Reminder_Dict(reminder.server_id, reminder.title, reminder.toDict())

    async def remove_Reminder(self, server:str, title: str):
        async with self.lock:
            if(title in self.reminderDict[server]):
                self.reminderDict[server].pop(title)
                await self._updateReminders()


    async def _updateServers(self):
    # Serializing json
        json_object = json.dumps(self.serverDict, indent=4)
        with open("servers.json", "w") as outfile:
            outfile.write(json_object)

    async def add_server(self, server: Server):
        async with self.lock:
            self.serverDict[server.id] = server.toDict()
            await self._updateServers()


    async def get_all_servers(self):
        async with self.lock:
            return self.serverDict
        
    async def get_server(self, guild:str) -> Server:
        serv = Server.from_dict(guild, (await self.get_all_servers())[guild])
        return serv

