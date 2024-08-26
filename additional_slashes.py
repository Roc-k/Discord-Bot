import discord
from discord.commands import option
'''
This file will hold all eventual utility/server specific commands that I add
'''


def add_verify(bot:discord.Bot, servers:list[str]):
    '''
    Created for NUrobotics, so that names can be set for users
    The server using must have a "verified" role, I will try to add access to be able to change the verification role eventually
    '''
    @bot.slash_command(
            guild_ids=servers,
            decscription = "verify yourself with /verify <first> <last>")
    @option(
        "first",
        str,
        required = True,
        description = "Your first name",
    )
    @option(
        "last",
        str,
        required = True,
        description = "Your last name",
    )
    async def verify(ctx, first:str, last:str):

        verified = discord.utils.get(ctx.guild.roles, name = "verified")

        if(verified in ctx.user.roles):
            await ctx.respond("You are already verified,\nif you have questions please contact a Moderator", ephemeral=True)
        else:
            try:
                await ctx.user.add_roles(verified)
            except:
                await ctx.respond(f"Unable to set role, please contact a moderator", ephemeral = True)
            else:
                try:
                    await ctx.user.edit(nick = first + " " + last)
                except:
                    await ctx.respond(f"Unable to set Name, please contact a moderator\n(You may be more powerful than the bot)", ephemeral = True)
                else:
                    await ctx.respond(f"Verified! {first} {last}")
            # except:
            #     await ctx.respond("Bot Fail,\nPlease Contact a Developer(Roc-k on github)\nAfter Confirming that \"verified\" role exists", ephemeral=True)
