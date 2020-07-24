# Member of the Day: Events Configuration
#

import discord
from discord.ext import commands
import datetime
import time
import asyncio
import json
from conf.logger import logger
import conf.funcs as fs

# --- VARIABLES ---
# weekday to run events
dayToQuint = 5


### RESETS OLD AND CHECKS FOR NEW EVENTS ###
async def runEvents(servID,ctx):
    logger.debug('Resetting events...')
    await resetEvents(servID)
    logger.debug('Rolling for events...')
    await rollForEvent(servID,ctx)

### RESETS ALL EVENTS TO FALSE ###
async def resetEvents(servID): # server id
    serverEntry = await fs.getServerEntry(fs.serverPath,servID)
    currentEvents = serverEntry['currentEvents']
    logger.debug('Looping current events...')
    for event in currentEvents:
        currentEvents[event] = False
    logger.debug('All events set False...')
    await fs.updateServerVal(fs.serverPath,servID,'currentEvents',currentEvents)
    logger.info(f'  Reset all events')

### ROLLS FOR AN EVENT ###
async def rollForEvent(servID,ctx):
    today = datetime.datetime.now().weekday()
    if today == dayToQuint:
        await quintVotesDay(servID,ctx)
    else:
        return

### CHECKS STATUS FOR SINGLE EVENT TRUE/FALSE ###
async def eventStatus(servID,event):
    serverEntry = await fs.getServerEntry(fs.serverPath,servID)
    currentEvents = serverEntry['currentEvents']
    return currentEvents[event]


# ------- EVENT FUNCTIONS ---------------
# ---------------------------------------

### QUINTUPLE VOTE DAY - 5 VOTES FOR EVERYONE TO GIVE OUT ###
async def quintVotesDay(servID,ctx): # server id
    serverEntry = await fs.getServerEntry(fs.serverPath,servID)
    currentEvents = serverEntry['currentEvents']
    currentEvents['quintVotes'] = True
    await fs.updateServerVal(fs.serverPath,servID,'currentEvents',currentEvents)
    await ctx.send("**It's Quintuple Vote Day!** Everyone in the server now has **5** votes to give out!\n"
            "All votes will be reset during the next drawing tomorrow!")
    logger.info(f'  Started Quintuple Vote Day')
