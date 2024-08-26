import discord
from typing import Union
from additional_slashes import add_verify

from reminder_cog import reminderCog

# Create Bot
bot = discord.Bot()
# Intilaize Reminders Module
reminders = reminderCog(bot)
bot.add_cog(reminders)
# reminders.connect_reminders(bot)

# Get the Servers we care about from the data loader
servers = reminders.data_loader.servers

# Add Verify because this is the configuration we want for the default use case
add_verify(bot, servers)

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")


@bot.slash_command(
        guild_ids=servers,
        decscription = "Test Command to see if the bot is online"
                   )
async def ping(ctx):
    await ctx.respond("pong", ephemeral=True)






# fetch our token
f = open('key.txt')
TOKEN = f.read()
f.close()

bot.run(TOKEN)


# should never run
print('made it here')

