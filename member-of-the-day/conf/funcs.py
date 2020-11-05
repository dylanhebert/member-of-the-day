# Member of the Day: Functions File
#

import discord
from discord.ext import commands
import datetime
import time
import asyncio
import json
from conf.logger import logger
import data.motd_times as rt
import pathlib

DIR_PATH = str(pathlib.Path().absolute())

# --- VARIABLES ---
# paths to json files
serverPath = DIR_PATH + '/data/motd_servers.json'
scorePath = DIR_PATH + '/data/motd_scores.json'
votePath = DIR_PATH + '/data/motd_voting.json'
# weekday to wipe all votes
dayToWipe = 6

# ------- NON-ASYNC FUNCTIONS -------
#------------------------------------

### SECS -> MINUTES CONVERTER ###
def timeMins(secs):
    minutes = secs * 60
    return minutes

### SECS -> HOURS CONVERTER ###
def timeHours(secs):
    minutes = secs * 60
    hours = minutes * 60
    hoursFix = hours - 30
    return hoursFix

# ------ BASIC ASYNC FUNCTIONS ------
#------------------------------------

### CHECK IF A MEMBER IS ADMIN ###
async def isAdmin(mem):
    if mem.guild_permissions.administrator == True:
        return True
    else:
        return False

### CHECK IF A MEMBER IS DYLAN ###
async def isDylan(mem):
    if mem.id == 134858274909585409:
        return True
    else:
        return False

# ------- JSON FILE FUNCTIONS -------
#------------------------------------

### OPEN JSON FILE ###
async def openJson(path):
    with open(path,"r") as f:
        return json.load(f)

### WRITE JSON FILE ###
async def writeJson(path,data):
    with open(path,"w") as f:
        json.dump(data, f, indent=4)



# ------- BASIC DATABASE FUNCTIONS --------
#------------------------------------------

### RETURN ONE SERVER AS DICT FROM DB ###
async def getServerEntry(path,servID):
    data = await openJson(path)
    for a in data.keys():
        if a == str(servID):
            return data[a]

### UPDATE ONE SERVER DICT ENTRY ###
async def updateServerEntry(path,servID,newEntry):
    data = await openJson(path)
    data[str(servID)] = newEntry
    await writeJson(path,data)

### RETURN ONE VALUE FROM SERVER ###
async def getServerVal(path,servID,key):
    data = await openJson(path)
    for a in data.keys():
        if a == str(servID):
            server = data[a]
            return server[key]

### UPDATE ONE VALUE FOR A SERVER ###
async def updateServerVal(path,servID,key,newVal):
    data = await openJson(path)
    server = data[str(servID)]
    server[key] = newVal
    data[str(servID)] = server
    await writeJson(path,data)

### DELETE A KEY FROM A SERVER ###
async def delServerKey(path,servID,key):
    data = await openJson(path)
    server = data[str(servID)]
    if str(key) in server:
        del server[str(key)]
        data[str(servID)] = server
        await writeJson(path,data)
        return True
    else:
        return False



# ------- MOTD JOIN/LEAVE FUNCTIONS ----------
#---------------------------------------------

### BOT ADDED TO NEW SERVER, POPULATE DATABASES ###
async def addServerDB(servID,servName,botRoleID):
    ## update serverPath DB ##
    dictServ = {
        servID: {
            'servName': servName,
            'chanName': None,
            'channelID': None,
            'timeStart': None,
            'motdRoleID': None,
            'secretChID': None,
            'botRoleID': botRoleID,
            'exemptRoles': [],
            'currentMOTD': None,
            'isPaused': False,
            'reminder': True,
            'currentEvents': {
                'quintVotes': False
            }
        }
    }
    try:
        # load existing json file
        dataSe = await openJson(serverPath)
    except:
        # no json file found
        await writeJson(serverPath,dictServ)
        newFileSe = True
    try:
        # append server to json file
        dataSe.update(dictServ)
        # write updated json file
        await writeJson(serverPath,dataSe)
        newFileSe = False
    except:
        logger.info(f'\nERROR ADDING SERVER TO SERVER DB: {servName} | {servID}')
    ## update scorePath DB ##
    dictScore = {
        servID: {}
    }
    try:
        # load existing json file
        dataSc = await openJson(scorePath)
    except:
        # no json file found
        await writeJson(scorePath,dictScore)
        newFileSc = True
    try:
        # check if server already has scores
        if str(servID) not in dataSc:
            # append server to json file
            dataSc.update(dictScore)
            # write updated json file
            await writeJson(scorePath,dataSc)
        else:
            pass
        newFileSc = False
    except:
        logger.info(f'\nERROR ADDING SERVER TO SCORE DB: {servName} | {servID}')
    ## update votePath DB ##
    dictVote = {
        servID: {
            'usedVotes': {},
            'voteCounts': {}
        }
    }
    try:
        # load existing json file
        dataV = await openJson(votePath)
    except:
        # no json file found
        await writeJson(votePath,dictVote)
        newFileV = True
    try:
        # append server to json file
        dataV.update(dictVote)
        # write updated json file
        await writeJson(votePath,dataV)
        newFileV = False
    except:
        logger.info(f'\nERROR ADDING SERVER TO VOTE DB: {servName} | {servID}')
    ## log results ##
    if newFileSe == True:
        logger.info(f'\nCreated json file: {serverPath}')
    if newFileSc == True:
        logger.info(f'\nCreated json file: {scorePath}')
    if newFileV == True:
        logger.info(f'\nCreated json file: {votePath}')
    logger.info(f'\nNew guild added to databases: {servName} | {servID}')

### BOT REMOVED FROM SERVER, REMOVE FROM DATABASES ###
async def delServerDB(servID,servName):
    dataSe = await openJson(serverPath)
    dataV = await openJson(votePath)
    # delete server in server DB
    if str(servID) in dataSe:
        del dataSe[str(servID)]
    # delete server in voting DB
    if str(servID) in dataV:
        del dataV[str(servID)]
    await writeJson(serverPath,dataSe)
    await writeJson(votePath,dataV)
    logger.info(f'\nGuild removed from databases: {servName} | {servID}')



# ------- MOTD COMMANDS FUNCTIONS ------------
#---------------------------------------------

### CHECKS ROLE HIERARCHY FOR CORRECT POSITION OF BOT ROLE ###
async def checkServRoles(serv): # (server object, channel object)
    serverEntry = await getServerEntry(serverPath,serv.id)
    servRoles = serv.role_hierarchy
    botRole = discord.utils.get(serv.roles, id=serverEntry['botRoleID'])
    exRoles = serverEntry['exemptRoles']
    for role in servRoles:
        if role == botRole:
            return 1
        elif role.id == serverEntry['motdRoleID']:
            return 2
        elif role.hoist == True:
            if role.id not in exRoles:
                return 3

### UPDATE MAIN MOTD VALUES FOR SERVER ###
async def updateServerMOTD(servID,servName,chanName,chanID,timeRun,motdRoleID,secretChID):
    # open server list
    serverEntry = await getServerEntry(serverPath,servID)
    # adjust runTimes list in motd_times.py
    oldTime = serverEntry['timeStart']
    if oldTime in rt.runTimes:
        rt.runTimesDel(oldTime)
        rt.runTimesAdd(timeRun)
        pass
    else:
        rt.runTimesAdd(timeRun)
        pass
    # replace values
    serverEntry['servName'] = servName
    serverEntry['chanName'] = chanName
    serverEntry['channelID'] = chanID
    serverEntry['timeStart'] = timeRun
    serverEntry['motdRoleID'] = motdRoleID
    serverEntry['secretChID'] = secretChID
    # update server list
    await updateServerEntry(serverPath,servID,serverEntry)
    logger.info(f'\nServList DB update: {servName} | #{chanName} | {timeRun}\n'
                f' *Updated run-time entry: {oldTime} --> {timeRun}')



# ------- MOTD LOOPER FUNCTIONS -------------
#--------------------------------------------

### UPDATE SCORES IN DB ###
async def updateScores(servID,motdID):
    scoresEntry = await getServerEntry(scorePath,servID)
    # if member has been picked before
    if str(motdID) in scoresEntry:
        scoresEntry[str(motdID)] += 1
        sortedScores = {k: v for k, v in sorted(scoresEntry.items(), key=lambda x: x[1], reverse=True)}
        logger.info(f'Score added to ID {motdID}')
    # if member has NOT been picked before
    else:
        scoresEntry[str(motdID)] = 1
        sortedScores = scoresEntry
        #sortedScores = {k: v for k, v in sorted(scoresEntry.items(), key=lambda x: x[1], reverse=True)}
        logger.info(f'ID {motdID} added to score dict')
    await updateServerEntry(scorePath,servID,sortedScores)

#### GET LIST OF CURRENT VOTES ###
async def getVoteLst(serv): # server object
    voteLst = []
    votingEntry = await getServerEntry(votePath,serv.id)
    voteCounts = votingEntry['voteCounts']
    badIDs = []
    # get member objects from keys
    for k,v in voteCounts.items():
        mem = serv.get_member(int(k))
        # append number of mems to list based on value amount
        if mem != None:
            for i in range(v):
                voteLst.append(mem)
        else:
            badIDs.append(k)
    # if we cant get member, remove bad entry from our json
    if badIDs:
        for memID in badIDs:
            del voteCounts[memID]
        votingEntry['voteCounts'] = voteCounts
        await updateServerEntry(votePath,serv.id,votingEntry)
        logger.info(f'Bad member IDs in vote list! Deleted: {k}!')
    return voteLst


#### GET DICT OF CURRENT VOTES ###
async def getVoteDict(serv): # server object
    votingEntry = await getServerEntry(votePath,serv.id)
    voteCounts = votingEntry['voteCounts']
    return voteCounts

#### DEL MOTD VOTES IF VOTED ###
async def delVotesMotd(servID,motdID): # server id, motd id
    votingEntry = await getServerEntry(votePath,servID)
    voteCounts = votingEntry['voteCounts']
    # reset people who voted
    votingEntry['usedVotes'] = {}
    # del new motd from list if votes exist
    if motdID != None: # if no one was pick for motd
        if str(motdID) in voteCounts:
            del voteCounts[str(motdID)]
            votingEntry['voteCounts'] = voteCounts
    await updateServerEntry(votePath,servID,votingEntry)

#### DEL ALL MOTD VOTES ON A CERTAIN WEEKDAY ###
async def wipeVotesDay(servID,ctx): # server id, ctx to send to
    if datetime.datetime.now().weekday() == dayToWipe:
        logger.debug('Correct day to wipe...')
        await updateServerVal(votePath,servID,'voteCounts',{})
        await ctx.send('All votes have been reset!')
    else:
        return

