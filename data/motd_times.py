# Member of the Day: Times Configuration
# THANKS CHRIS
#

import json
from conf.logger import logger
import pathlib

DIR_PATH = str(pathlib.Path().absolute())

# global variables
servLstPath = DIR_PATH + '/data/motd_servers.json'
runTimes = [] # list of run times for looper
preTimes = [] # list of hour before times for looper

# gets the hour before a time str
def hourBefore(t):
    if t[:1] == '0':
        if t[:2] == '00':
            tNew = '23' + t[-3:]
        else:
            tNew = '0' + str(int(t[1]) - 1) + t[-3:]
    elif t[:2] == '10':
        tNew = '09' + t[-3:]
    else:
        tNew = str(int(t[:2]) - 1) + t[-3:]
    return tNew

# gets the hour after a time str
def hourAfter(t):
    if t[:1] == '0':
        if t[:2] == '09':
            tNew = '10' + t[-3:]
        else:
            tNew = '0' + str(int(t[1]) + 1) + t[-3:]
    elif t[:2] == '23':
        tNew = '00' + t[-3:]
    else:
        tNew = str(int(t[:2]) + 1) + t[-3:]
    return tNew

# runTimes functions
def runTimesInit():
    global runTimes
    global preTimes
    runTimes = []
    preTimes = []
    try:
        with open(servLstPath, "r") as read_file:
            data = json.load(read_file)
        for a,b in data.items():
            runTimes.append(b['timeStart'])
            logger.debug(f"Added {b['timeStart']} to runTimes list")
            preTimes.append(hourBefore(b['timeStart']))
            #logger.debug(f"Added {hourBefore(b['timeStart'])} to preTimes list")
        logger.debug(f'runTimes: {runTimes}')
        logger.debug(f'preTimes: {preTimes}')
    except:
        logger.debug('There are no servers in the database.')

def runTimesAdd(newTime):
    global runTimes
    global preTimes
    runTimes.append(newTime)
    preTimes.append(hourBefore(newTime))
    logger.info(f"Added {newTime} to runTimes list")
    logger.info(f"Added {hourBefore(newTime)} to preTimes list")
    logger.debug(f'runTimes: {runTimes}')
    logger.debug(f'runTimes: {runTimes}')

def runTimesDel(oldTime):
    global runTimes
    global preTimes
    runTimes.remove(oldTime)
    preTimes.remove(hourBefore(oldTime))
    logger.info(f"Removed {oldTime} from runTimes list")
    logger.info(f"Removed {hourBefore(oldTime)} from preTimes list")
    logger.debug(f'runTimes: {runTimes}')
    logger.debug(f'preTimes: {preTimes}')
