# Member of the Day: Main File
# Written by: Dylan Hebert (The Green Donut)
# Bot permissions: 268545040
#

import discord
from discord.ext import commands
import datetime
import os
import sys, traceback
from conf.logger import logger
import data.motd_times as rt
import conf.funcs as fs
import time
import asyncio

botInfo = open("_bot_info.txt", "r")
botToken = botInfo.readline()

#gavinRoleColor = discord.Color(0x62dbff)

# set prefix
def get_prefix(bot, message):
    prefixes = ['!']
    if not message.guild:
        return '!'
    return commands.when_mentioned_or(*prefixes)(bot, message)

# create bot object
bot = commands.Bot( command_prefix = get_prefix, 
                    description = 'Member of the Day by Green Donut',
                    pm_help = True)
gamePlaying = discord.Game(name='!vote | !score')
# gamePlaying = discord.Streaming(name='!vote | !score',
#                                 url='https://www.twitch.tv/thegreendonut')

# define extensions
#cogsLoc = '/home/pi/code_pi/gavinbot/cogs/'
initial_extensions =    [
                        'cogs.motd_cmds',
                        'cogs.motd_looper'
                        ]

# load extensions
if __name__ == '__main__':
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
            logger.info(f'Loaded extension {extension}.')
        except Exception as e:
            logger.warning(f'Failed to load extension {extension}.')
            traceback.print_exc()

# bot main start
@bot.event
async def on_ready():
    logger.info(f'\n** BOT STARTED: {bot.user.name} - {bot.user.id} **')
    # gather run times from server db
    rt.runTimesInit()
    await bot.change_presence(activity = gamePlaying)

# --- ERROR & COOLDOWN RESPONSES
@bot.event
async def on_command_error(ctx, error):
    channel = ctx.message.channel
    if isinstance(error, commands.errors.CommandNotFound):
        pass
    if isinstance(error, commands.errors.CommandOnCooldown):
	    pass

### BOT JOINS SERVER ###
@bot.event
async def on_guild_join(guild):
    sysChan = False
    if guild.system_channel != None:
        sysChan = True
        await guild.system_channel.send(f'Thanks for having me, {guild.name}\n'
                                'Use **!MOTDhelp** to learn how to start Member of the Day\n'
                                'Use **!help** to get a list of all my functions')  
    logger.info('\n---------------------------------------\n'
            f'Joined {guild.name} with {guild.member_count} users!\n'
            f' System channel = {sysChan}\n'
            '---------------------------------------')
    await asyncio.sleep(1)
    botRole = discord.utils.get(guild.roles, name='MOTD Bot')
    await fs.addServerDB(guild.id,guild.name,botRole.id)
    if guild.system_channel != None:
        await guild.system_channel.send(f'Move my role ({botRole.mention}) above all hoisted roles to use Member of the Day!')

### BOT LEAVES SERVER ###
@bot.event
async def on_guild_remove(guild):
    serverEntry = await fs.getServerEntry(fs.serverPath,guild.id)
    # delete server run time in rt.runTimes
    delRuntime = serverEntry['timeStart']
    # only try to delete run time if its not None in db
    if delRuntime != None:
        if delRuntime in rt.runTimes:
            rt.runTimesDel(delRuntime)
            pass
    # delete server from DBs
    await fs.delServerDB(guild.id,guild.name)
    logger.info(f'\nServer List DB update: bot removed from {guild.name} | {guild.id}\n')
            

bot.run(botToken, bot=True)