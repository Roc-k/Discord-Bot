from typing import Union, Dict
import time
from remind_utils import time_to_seconds, COLORS, REV_COLORS, DEFAULT_SERVER_SETTINGS


class Server():
    def __init__(self, server, allowed_roles:list[str] = DEFAULT_SERVER_SETTINGS['allowed_roles'], admin_roles: list[str] = DEFAULT_SERVER_SETTINGS['admin_roles'], react_emojis:list[str] = DEFAULT_SERVER_SETTINGS['react_emojis'], color:int = DEFAULT_SERVER_SETTINGS['color']):
        self.id = server
        self.allowed_roles = allowed_roles
        self.admin_roles = admin_roles
        self.reacts = react_emojis
        self.color = color

    def from_dict(server:str, contents: Dict[str, Union[int, list]]) -> "Server":
        try:
            allowed_roles = contents["allowed_roles"]
            admin_roles = contents["admin_roles"]
            reacts = contents["react_emojis"]
            color = contents["color"]
        except KeyError:
            raise(ValueError)
        
        return Server(server, allowed_roles, admin_roles, reacts, color)
    

    def toDict(self):
        return {
                'allowed_roles' : self.allowed_roles,
                'admin_roles' : self.admin_roles,
                'react_emojis' : self.reacts,
                'color' : self.color,
                }

    

class Reminder():
    def __init__(self, server:Union[Server, str], title:str, message:str, channel:int, time_between:Union[str,int] = 0, first_message:Union[str,int] = 0, single_shot:bool = False):
        if(isinstance(first_message,str)):
                    first_message = time_to_seconds(first_message)

        if first_message == 0:
            next_message = time.time()
        else:
            next_message = time.time() + first_message
        
        if(isinstance(time_between,str)):
            time_between = time_to_seconds(time_between)

        if(time_between == 0):
            time_between = 604800

        self.time_between = int(time_between)
        self.next_message = int(next_message)


        self.title = title
        self.message = message
        self.channel = channel
        self.single_shot = single_shot

        # only used when calling from_dict
        if(isinstance(server, Server)):
            self.server_id = server.id
            self.color = server.color
            self.reacts = server.reacts



    def from_dict(server:str, title:str, contents: Dict[str,Union[str, int, bool, list]]) -> "Reminder":
        '''
        server is a string because we are directly loading all data from the dict
        '''
        try:
            message = contents["message"]
            channel = contents['channel']
            time_between = contents['time_between']
            next_message = contents['next_message']
            single_shot = contents['single_shot']
        except KeyError:
            raise(ValueError)
        
        rem = Reminder(server, title, message, channel, time_between, 0, single_shot)

        try:
            rem.color = contents['color']
            rem.reacts = contents['reacts']
            rem.next_message = next_message
            rem.server_id = server
        except KeyError:
            raise(ValueError)
        
        return rem


    def toDict(self):
        return {
                    "message" : self.message,
                    "channel" : self.channel,
                    "time_between" : self.time_between, 
                    "next_message" : self.next_message,
                    "single_shot" : self.single_shot,
                    "color" : self.color,
                    "reacts" : self.reacts,
                }
    