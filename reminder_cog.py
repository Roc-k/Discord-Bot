import discord
import time
from discord.ext import tasks, commands
from discord.commands import option
from typing import Union
from remind_utils import time_to_seconds, COLORS, REV_COLORS, DEFAULT_SERVER_SETTINGS
from reminder_data import ReminderDataLoader
from reminder_class import Reminder, Server
import asyncio

    



class reminderCog(commands.Cog):
    def __init__(self, bot:discord.Bot):
        '''
        intialized data loader and printer(runs the check reminders command)
        We need a single data loader so that multiple async classes dont run at the same time breaking the dicts
        '''
        self.bot = bot
        self.data_loader = ReminderDataLoader()
        self.connect_reminders(bot)
        self.printer.start()    
        

    def cog_unload(self):
        self.printer.cancel()

    @tasks.loop(seconds=60.0)
    async def printer(self):
        await self.checkReminders()


    @printer.before_loop
    async def before_printer(self):
        print('waiting...')
        await self.bot.wait_until_ready()


    async def checkReminders(self):
        '''
        Fetches all current reminders in all current servers, 
        outputs ones whose reminder time is before the current time
        deletes single_shot reminders
        '''
        currentTime = time.time()
        print('checking Reminders')
        rems = await self.data_loader.get_all_reminders()
        for guild, reminders in rems.items():
            # serv = await self.data_loader.get_server(guild)
            for name,contents in reminders.items():
                rem:Reminder = Reminder.from_dict(guild, name, contents)

                if(rem.next_message < currentTime):

                    # send message
                    channel = self.bot.get_channel(rem.channel)
                    embedVar = discord.Embed(title=name, description= rem.message, color = rem.color)

                    msg = await channel.send(embed = embedVar)

                    for emoji in rem.reacts:
                        await msg.add_reaction(emoji)

                    new_time = rem.next_message

                    # loop time
                    while(new_time < currentTime):
                        new_time += rem.time_between
                    rem.next_message =  new_time

                    await self.data_loader.add_Reminder(rem)

                    # remove single shots
                    if(rem.single_shot):
                            await self.data_loader.remove_Reminder(guild, name)

        print("finished checking")

    
    async def allowed(self, ctx:discord.context, admin=False):
        '''
        Checks if a role is allowed to use a specified command, admin=True for admin only commands
        '''
        if(not admin):
            allowed_roles = (await self.data_loader.get_server(str(ctx.guild.id))).allowed_roles
        else:
            allowed_roles = (await self.data_loader.get_server(str(ctx.guild.id))).admin_roles
        roles = [discord.utils.get(ctx.guild.roles, name = i) for i in allowed_roles]
        allowed = any(r in ctx.user.roles for r in roles)
        return allowed


    def connect_reminders(self, bot:discord.bot):
        '''
        Connects all reminder related slash commands to the bot, this uncludes
        delete_reminder

        '''
        guilds = self.data_loader.servers

        @bot.slash_command(
                guild_ids=guilds,
                description = 'Allows Admins to delete reminders')
        @option(
            "title",
            str,
            required = True,
            description = "The title of the reminder you want to delete",
        )
        async def delete_reminder(ctx,title):
            '''
            deletes a reminder from the reminders list
            '''
            if(await self.allowed(ctx)):
                await ctx.respond('loading', ephemeral=True)
                await self.data_loader.remove_Reminder(str(ctx.guild.id), title)
                await ctx.respond(content = f'deleted {title}', ephemeral=True)
            else:
                await ctx.respond('you dont have permission', ephemeral=True)



        @bot.slash_command(
                guild_ids=guilds,
                description = 'Allows Admins to set reminders'
                        )
        @option(
            "first_message",
            what = Union[int, str],
            required = False,
            default = 0,
            description = "Send in how long?\nDefault is now\nPlease type like this(each input is optional): 1w 2d 3h 5m",
        )
        @option(
            "single_shot",
            bool,
            description = "Fire only once?",
            choices = [True,False],
            required = False,
            default = False
        )
        @option(
            "title",
            str,
            description = "Message Title",
            required = True,
            )
        @option(
            "message",
            str,
            description = "Message Contents",
            required = True,
            )
        @option(
            "time_between",
            what = Union[int,str],
            description = "How often to send\ndefault is 1 week\nPlease type like this(each input is optional): 1w 2d 3h 5m",
            required = False,
            default = 604800
            )
        async def set_reminder(ctx:discord.context, title, message, first_message, time_between, single_shot):
            '''
            Sets a reminder using the specified inputs, and defauly server options for color and reacts

            #TODO Current sets them for the year 2079, so please double check
            '''
            if(await self.allowed(ctx)):
                await ctx.respond('loading', ephemeral=True)
                if(isinstance(first_message,str)):
                    first_message = time_to_seconds(first_message)

                if first_message == 0:
                    first_message = time.time()
                else:
                    first_message = time.time() + first_message
                
                if(isinstance(time_between,str)):
                    time_between = time_to_seconds(time_between)

                if(time_between == 0):
                    time_between = 604800

                serv = await self.data_loader.get_server(str(ctx.guild.id))
                rem = Reminder(serv, title, message, int(ctx.channel.id), int(time_between), int(first_message), bool(single_shot))
                
                await self.data_loader.add_Reminder(rem)

                await ctx.respond(f'added {title}', ephemeral=True)
            else:
                await ctx.respond('you dont have permission', ephemeral=True)

        @bot.slash_command(
                guild_ids=guilds,
                description = 'Allows Admins to list current reminders'
                        )
        async def list_reminders(ctx:discord.context):
            '''
            Lists the name of all active reminders in a server
            '''
            if(await self.allowed(ctx)):
                await ctx.respond(list((await self.data_loader.get_all_reminders())[str(ctx.guild.id)]), ephemeral=True)
            else:
                await ctx.respond('you dont have permission',ephemeral=True)
            
        @bot.slash_command(
                guild_ids=guilds,
                description = 'Allows Admins to View Reminder Info'
        )
        @option(
            "title",
            str,
            description = "Message Title",
            required = True,
            )
        async def reminder_info(ctx:discord.context, title):
            '''
            gives info on a specific reminder in a human readable reply
            '''
            if(await self.allowed(ctx)):
                try:
                    reminder:"Reminder" = await self.data_loader.get_reminder(str(ctx.guild.id), title)
                    content = reminder.message
                    next_message = "<t:" + str(reminder.next_message) + ":f>"
                    time_between = reminder.time_between
                    color = REV_COLORS[reminder.color]
                    reacts = reminder.reacts
                    single = reminder.single_shot
                    channel = reminder.channel

                    message = f'''content : {content}\nnext message : {next_message}\nseconds between : {time_between}\ncolor : {color}\nreactions : {reacts}\nchannel : {channel}\ndeleted after? : {single}'''


                except KeyError:
                    message = "Not a valid reminder"
                
                await ctx.respond(message, ephemeral=True)
            else:
                await ctx.respond('you dont have permission', ephemeral=True)
        


        @bot.slash_command(
                        guild_ids=guilds,
                        description = 'Allows Admins to change Reminder Color'
                )
        @option(
            "title",
            str,
            description = "Message Title",
            required = True,
            )
        async def change_color(ctx:discord.context, title):
            '''
            opens up an interactive menu to change the reminder color
            '''
            if(await self.allowed(ctx)):
                await ctx.respond("Loading", ephemeral=True)

                msg = await ctx.followup.send("Select Color by reacting")
                for emoji in list(COLORS.keys()):
                    await msg.add_reaction(emoji)


                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in COLORS.keys() and reaction.message.id == msg.id

                try:
                    reaction = await bot.wait_for("reaction_add", check = check, timeout = 60)
                except asyncio.TimeoutError:
                    await msg.delete()
                    await ctx.respond("Reaction Not Receieved in Time", ephemeral=True)
                else:
                    rem:"Reminder" = await self.data_loader.get_reminder(str(ctx.guild.id), title)
                    rem.color = COLORS[reaction[0].emoji]
                    try:
                        await self.data_loader.add_Reminder(rem)
                        await ctx.respond("Color Changed", ephemeral=True)
                    except KeyError:
                        await ctx.respond("Invalid Reminder Name", ephemeral=True)
                    await msg.delete()
            else:
                await ctx.respond('you dont have permission', ephemeral=True)


        @bot.slash_command(
                        guild_ids=guilds,
                        description = 'Allows Admins to adjust Next Send Time'
                )
        @option(
            "title",
            str,
            description = "Message Title",
            required = True,
            )
        @option(
            "change",
            what = str,
            required = True,
            description = "+/- followed by how much you want the change to be: 1w 2d 3h 5m(each unit is optional)",
        )
        async def adjust_send_time(ctx:discord.context, title, change):
            '''
            changes the next time a reminder will send
            '''
            if(await self.allowed(ctx)):

                sign = change[0]
                if(sign not in ["+", "-"]):
                    await ctx.respond("Invalid First Character", ephemeral=True)
                else:
                    if(sign == "+"):
                        mult = 1
                    else:
                        mult = -1
                    change = time_to_seconds(change)

                    rem:"Reminder" = await self.data_loader.get_reminder(str(ctx.guild.id), title)

                    rem.next_message += mult * change
                    new_time = rem.next_message
                    await self.data_loader.add_Reminder(rem)
                    await ctx.respond(f"Message will now send <t:{new_time}:f>", ephemeral=True)
            else:
                await ctx.respond('you dont have permission', ephemeral=True)


        @bot.slash_command(
                        guild_ids=guilds,
                        description = 'Allows Admins to adjust time between'
                )
        @option(
            "title",
            str,
            description = "Message Title",
            required = True,
            )
        @option(
            "time_between",
            what = Union[int,str],
            description = "How often to send\ndefault is 1 week\nPlease type like this(each input is optional): 1w 2d 3h 5m",
            required = True,
            )
        async def adjust_time_between(ctx:discord.context, title, time_between):
            if(await self.allowed(ctx)):
                change = time_to_seconds(time_between)
                rem:"Reminder" = await self.data_loader.get_reminder(str(ctx.guild.id), title)
                rem.time_between = change
                await self.data_loader.add_Reminder(rem)
                await ctx.respond("Updated", ephemeral=True)
            else:
                await ctx.respond('you dont have permission', ephemeral=True )


        @bot.slash_command(
                        guild_ids=guilds,
                        description = 'Allows Admins to add administrator roles'
                )
        @option(
            "role",
            str,
            description = "role added",
            required = True,
            )
        async def add_adminstrator_role(ctx:discord.context, role):
            if(await self.allowed(ctx, admin = True)):
                serv:"Server" = await self.data_loader.get_server(str(ctx.guild.id))
                serv.admin_roles.append(role)
                await self.data_loader.add_server(serv)
                await ctx.respond("updated",  ephemeral=True)

        @bot.slash_command(
                        guild_ids=guilds,
                        description = 'Allows Admins to remove administrator roles'
                )
        @option(
            "role",
            str,
            description = "role removed",
            required = True,
            )
        async def remove_adminstrator_role(ctx:discord.context, role):
            '''
            TODO add error handling for not in list, currently the bot just refuses to respond
            '''
            if(await self.allowed(ctx, admin = True)):
                if(role not in DEFAULT_SERVER_SETTINGS["admin_roles"]):
                    serv:"Server" = await self.data_loader.get_server(str(ctx.guild.id))
                    serv.admin_roles.remove(role)
                    await self.data_loader.add_server(serv)
                    await ctx.respond("updated",  ephemeral=True)
                else:
                    await ctx.respond("role cannot be removed because it is a default allowed role",  ephemeral=True)

        @bot.slash_command(
                        guild_ids=guilds,
                        description = 'Allows Admins to add user roles'
                )
        @option(
            "role",
            str,
            description = "role added",
            required = True,
            )
        async def add_user_role(ctx:discord.context, role):
            if(await self.allowed(ctx, admin = True)):
                serv:"Server" = await self.data_loader.get_server(str(ctx.guild.id))
                serv.allowed_roles.append(role)
                await self.data_loader.add_server(serv)
                await ctx.respond("updated",  ephemeral=True)


        @bot.slash_command(
                        guild_ids=guilds,
                        description = 'Allows Admins to remove user roles'
                )
        @option(
            "role",
            str,
            description = "role removed",
            required = True,
            )
        async def remove_user_role(ctx:discord.context, role):
            '''
            TODO add error handling for not in list, currently the bot just refuses to respond
            '''
            if(await self.allowed(ctx, admin = True)):
                if(role not in DEFAULT_SERVER_SETTINGS["allowed_roles"]):
                    serv:"Server" = await self.data_loader.get_server(str(ctx.guild.id))
                    serv.allowed_roles.remove(role)
                    await self.data_loader.add_server(serv)
                    await ctx.respond("updated",  ephemeral=True)
                else:
                    await ctx.respond("role cannot be removed because it is a default allowed role", ephemeral=True )


        @bot.slash_command(
                guild_ids=guilds,
                description = 'Allows Users to list current permission roles'
                        )
        async def list_permissions(ctx:discord.context):
            if(await self.allowed(ctx)):
                serv:"Server" = await self.data_loader.get_server(str(ctx.guild.id))
                await ctx.respond("Admins:" + str(serv.admin_roles) + "\nUsers:" + str(serv.allowed_roles), ephemeral=True)
            else:
                await ctx.respond('you dont have permission', ephemeral=True )


        @bot.slash_command(
                        guild_ids=guilds,
                        description = 'Allows Users to remove Reactions'
                )
        @option(
            "title",
            str,
            description = "Reminder Title",
            required = True,
            )
        async def remove_reminder_reaction(ctx:discord.context, title):
            '''
            TODO add error handling for not a real reminder, currently the bot just refuses to respond
            '''
            if(await self.allowed(ctx)):
                await ctx.respond("Loading", ephemeral=True)
                rem:"Reminder" = await self.data_loader.get_reminder(str(ctx.guild.id), title)
                
                msg = await ctx.followup.send("React the Reaction to Remove")
                for emoji in rem.reacts:
                    await msg.add_reaction(emoji)


                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in rem.reacts and reaction.message.id == msg.id

                try:
                    reaction = await bot.wait_for("reaction_add", check = check, timeout = 60)
                except asyncio.TimeoutError:
                    await msg.delete()
                    await ctx.respond("Reaction Not Receieved in Time", ephemeral=True)
                else:
                    rem.reacts.remove(reaction[0].emoji)
                    await self.data_loader.add_Reminder(rem)
                    await ctx.respond("Reaction Removed", ephemeral=True)
                    await msg.delete()
            else:
                await ctx.respond('you dont have permission', ephemeral=True )

        @bot.slash_command(
                        guild_ids=guilds,
                        description = 'Allows Users to add Reactions'
                )
        @option(
            "title",
            str,
            description = "Reminder Title",
            required = True,
            )
        async def add_reminder_reaction(ctx:discord.context, title):
            '''
            TODO add error handling for not a real reminder, currently the bot just refuses to respond
            '''
            if(await self.allowed(ctx)):
                await ctx.respond("Loading", ephemeral=True)
                msg = await ctx.followup.send("React the Reaction to Add")

                def check(reaction, user):
                    return user == ctx.author and reaction.message.id == msg.id

                try:
                    reaction = await bot.wait_for("reaction_add", check = check, timeout = 60)
                except asyncio.TimeoutError:
                    await msg.delete()
                    await ctx.respond("Reaction Not Receieved in Time", ephemeral=True)
                else:
                    rem:"Reminder" = await self.data_loader.get_reminder(str(ctx.guild.id), title)
                    rem.reacts.append(reaction[0].emoji)
                    try:
                        await self.data_loader.add_Reminder(rem)
                        await ctx.respond("Reaction Added", ephemeral=True)
                    except KeyError:
                        await ctx.respond("Invalid Reminder Name", ephemeral=True)
                    await msg.delete()
            else:
                await ctx.respond('you dont have permission', ephemeral=True )

    
        @bot.slash_command(
                        guild_ids=guilds,
                        description = 'Allows Users to remove Reactions'
                )
        @option(
            "title",
            str,
            description = "Reminder Title",
            required = True,
            )
        async def remove_default_reaction(ctx:discord.context, title):
            if(await self.allowed(ctx, admin = True)):
                await ctx.respond("Loading", ephemeral=True)
    
                serv:"Server" = await self.data_loader.get_server(str(ctx.guild.id))

                msg = await ctx.followup.send("React the Reaction to Remove")
                for emoji in serv.reacts:
                    await msg.add_reaction(emoji)


                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in serv.reacts and reaction.message.id == msg.id

                try:
                    reaction = await bot.wait_for("reaction_add", check = check, timeout = 60)
                except asyncio.TimeoutError:
                    await msg.delete()
                    await ctx.respond("Reaction Not Receieved in Time", ephemeral=True)
                else:
                    serv.reacts.remove(reaction[0].emoji)
                    await self.data_loader.add_server(serv)
                    await ctx.respond("Reaction Removed", ephemeral=True)
                    await msg.delete()
            else:
                await ctx.respond('you dont have permission', ephemeral=True )

        @bot.slash_command(
                        guild_ids=guilds,
                        description = 'Allows Users to add Reactions'
                )
        @option(
            "title",
            str,
            description = "Reminder Title",
            required = True,
            )
        async def add_default_reaction(ctx:discord.context, title):
            if(await self.allowed(ctx, admin = True)):
                await ctx.respond("Loading", ephemeral=True)

                msg = await ctx.followup.send("React the Reaction to Add")

                def check(reaction, user):
                    return user == ctx.author and reaction.message.id == msg.id

                try:
                    reaction = await bot.wait_for("reaction_add", check = check, timeout = 60)
                except asyncio.TimeoutError:
                    await msg.delete()
                    await ctx.respond("Reaction Not Receieved in Time", ephemeral=True)
                else:
                    
                    serv:"Server" = await self.data_loader.get_server(str(ctx.guild.id))
                    serv.reacts.append(reaction[0].emoji)
                    await self.data_loader.add_Reminder(serv)
                    await ctx.respond("Reaction Added", ephemeral=True)
                    await msg.delete()
            else:
                await ctx.respond('you dont have permission', ephemeral=True )