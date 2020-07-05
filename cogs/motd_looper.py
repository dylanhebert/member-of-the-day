# Member of the Day: Looper File
#

import discord
from discord.ext import commands
import time
import datetime
import random
import asyncio
import json
from conf.logger import logger
import data.motd_times as rt
import conf.funcs as fs
import conf.events as ev


# ------------------ PRE MOTD ------------------------
# ----------------------------------------------------
async def preMOTD(bot,servID,postChanID,motdRoleID,exemptIDs):
    # gather all server-specific variables we need
    server = bot.get_guild(servID)
    channel = server.get_channel(postChanID)
    motdRole = discord.utils.get(server.roles, id = motdRoleID)
    rolesExempt = []
    for role in exemptIDs:
        rolesExempt.append(discord.utils.get(server.roles, id = role))
    rolesExempt = ', '.join(e.name for e in rolesExempt)
    await channel.send(f'One hour until I pick the {motdRole.name.upper()}! Use **!vote** on another member.')
    #if rolesExempt != None:
    #    await channel.send(f'Roles exempted from {motdRole.name}: **{rolesExempt}**')

# ------------------ RUN MOTD ------------------------
# ----------------------------------------------------
async def runMOTD(bot,servID,postChanID,motdRoleID,exemptIDs,currentMOTD):
    # gather all server-specific variables we need
    server = bot.get_guild(servID)
    channel = server.get_channel(postChanID)
    motdRole = discord.utils.get(server.roles, id = motdRoleID)

    if currentMOTD != None:
        try: # if member still in server
            prevMem = discord.utils.get(server.members, id = currentMOTD) # makes sure the same person doesn't get picked again
            memLeft = False
            logger.debug('Previous MOTD found in server...')
        except: # if member left server
            prevMem = None
            memLeft = True
            logger.debug('Previous MOTD not found in server...')
    else: # if no previous MOTD
        prevMem = None
        memLeft = False
        logger.debug('No previous MOTD...')
    logger.info(f'Picking MOTD for {server.name}...')
    await channel.send(f'Sup bitches lets pick the {motdRole.name.upper()}!!! @here')
    #await channel.send(f'Sup bitches lets pick the {motdRole.name.upper()}!!! here')
    await asyncio.sleep(6)

    # if no MOTD was picked last time
    if prevMem == None:
        if memLeft == False:
            await channel.send(f'There was no previous {motdRole.name} so anyone is eligible!')
        else:
            await channel.send(f'The previous {motdRole.name} left the server. Fuck them')

    # a MOTD was picked last time
    else:
        await channel.send(f'Bye bye **{prevMem.name}**!')
        # kick anyone currently in MOTD role
        for allMember in server.members:
            for allRole in allMember.roles:
                if allRole == motdRole:
                    await allMember.remove_roles(allRole)
        await asyncio.sleep(1)

    # gather all online members (besides prevMem & all bots)
    logger.debug('Gathering members...')
    onMembers = []
    if prevMem != None: 
        for i in server.members:
            logger.debug(f'Checking {i.name}...')
            logger.debug(f'Status: {i.status}...')
            if str(i.status) == 'online' and i.id != prevMem.id:
                if not i.bot:
                    if any(role.id in exemptIDs for role in i.roles):
                        logger.debug(f'Passed {i.name}...')
                        pass
                    else:
                        onMembers.append(i)
                        logger.debug(f'  Appended {i.name}!')

    # gather everyone (besides all bots) since there's no prevMem
    else: 
        for i in server.members:
            logger.debug(f'Checking {i.name}...')
            if str(i.status) == 'online':
                if not i.bot:
                    if any(role.id in exemptIDs for role in i.roles):
                        logger.debug(f'Passed {i.name}...')
                        pass
                    else:
                        onMembers.append(i)
                        logger.debug(f'  Appended {i.name}!')

    # append voted members
    logger.debug('Getting vote list...')
    for i in await fs.getVoteLst(server):
        logger.debug(f'checking {i.name}...')
        if str(i.status) == 'online' and i.id != prevMem.id:
            onMembers.append(i)
            logger.debug(f'  Appended {i.name}!')
    potentialMem = len(onMembers)

    # if at least 1 eligible 'online' member
    logger.debug('Picking member...')
    if onMembers:
        await asyncio.sleep(5)
        randomMemNumber = random.randint(0, (potentialMem -1))
        chosenMotdMember = onMembers[randomMemNumber]
        await chosenMotdMember.add_roles(motdRole)
        await fs.updateServerVal(fs.serverPath,server.id,'currentMOTD',chosenMotdMember.id)
        logger.debug('Updated currentMOTD...')
        await fs.updateScores(servID,chosenMotdMember.id)
        logger.debug('Updated score...')
        await fs.delVotesMotd(servID,chosenMotdMember.id)
        logger.debug('Updated votes...')
        logger.info(f'{chosenMotdMember.name} was chosen for {motdRole.name} in {server.name}.')
        await channel.send(f'Grats {chosenMotdMember.mention}, you are the {motdRole.mention} and you can now post in the secret chat!')
        #await channel.send(f'grats {chosenMotdMember.name}, youre the {motdRole.name} and you can now post in the secret chat')

    # if no eligible 'online' members
    else: 
        chosenMotdMember = None
        await fs.updateServerVal(fs.serverPath,server.id,'currentMOTD',None)
        await fs.delVotesMotd(servID,None)
        logger.info(f'No eligible {motdRole.name} in {server.name}.')
        await channel.send('There are no eligible members right now.')
        await asyncio.sleep(1)
        await channel.send(f'I will select a new {motdRole.name} tomorrow.')
    await asyncio.sleep(1)
    # wipe votes if correct day
    await fs.wipeVotesDay(server.id,channel)
    logger.debug('Checked for vote wipe...')
    # reset old and check for new events
    await ev.runEvents(server.id,channel)
    logger.debug('Reset old and checked for new events.')

# ----------------------------------------------------
# ----------------------------------------------------


# --- START CLASS ---
class MOTDLooper(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        # create the background task and run it in the background
        self.bot.bg_task = self.bot.loop.create_task(self.looperTask())

    async def on_ready(self):
        logger.debug('MOTD - LOOPER Cog Ready')

    async def looperTask(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(1.5)

        # --- START LOOPER ---
        logger.info('MOTD loop started!')
        while not self.bot.is_closed():
            
            logger.debug('Checking for matches...')
            nowTime = datetime.datetime.now().strftime("%H:%M")
            # loop runTimes in motd_times.py
            for runTime in rt.runTimes:
                if runTime == nowTime:
                    logger.info('Run time match!')
                    # open server list if runTime match
                    data = await fs.openJson(fs.serverPath)
                    logger.debug('Found data...')
                    # loop through all server entries and their run times
                    for a,b in data.items():
                        if b['timeStart'] == runTime:
                            # check server preferences
                            if b['isPaused'] == False:

                                # run main script
                                logger.debug('Running main method...')
                                try:
                                    await runMOTD(self.bot,int(a),b['channelID'],b['motdRoleID'],b['exemptRoles'],b['currentMOTD'])
                                except Exception as e:
                                    logger.info(f'ERROR WITH LOOP: {e}')
                                    server = self.bot.get_guild(int(a))
                                    channel = server.get_channel(b['channelID'])
                                    dylan = server.get_member(134858274909585409)
                                    await channel.send(f'ERROR ERROR ERROR: {e} || {dylan.mention}\nSkipping pick for today!')
                    
                    await asyncio.sleep(4)
                    logger.info('Run time match done!')
                    break

            # loop preTimes in motd_times.py
            for preTime in rt.preTimes:
                if preTime == nowTime:
                    for runTime in rt.runTimes:
                        if runTime == rt.hourAfter(nowTime):
                            logger.info('Pre time match.')
                            # open server list if runTime match
                            data = await fs.openJson(fs.serverPath)
                            # loop through all server entries and their run times
                            for a,b in data.items():
                                if b['timeStart'] == runTime:
                                    # check server preferences
                                    if b['isPaused'] == False:
                                        if b['reminder'] == True:
                                            # run preMOTD script
                                            logger.debug('Running pre method...')
                                            await preMOTD(self.bot,int(a),b['channelID'],b['motdRoleID'],b['exemptRoles'])
                            await asyncio.sleep(10)
                            logger.info('Pre time match done!')
                            break
                    break
            await asyncio.sleep(54)

            # TESTING!!
            """
            data = await fs.openJson(fs.serverPath)
            for a,b in data.items():
                try:
                    await runMOTD(self.bot,int(a),b['channelID'],b['motdRoleID'],b['exemptRoles'],b['currentMOTD'])
                except Exception as e:
                    logger.info(f'ERROR WITH LOOP: {e}')
                    server = self.bot.get_guild(int(a))
                    channel = server.get_channel(b['channelID'])
                    dylan = server.get_member(134858274909585409)
                    await channel.send(f'ERROR ERROR ERROR: {e} || {dylan.mention}\nSkipping pick for today!')
                await asyncio.sleep(10)
                break
            """

        


def setup(bot):
    bot.add_cog(MOTDLooper(bot))