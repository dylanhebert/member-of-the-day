# Member of the Day: Commands File
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


# ----- START COG CLASS -----
class MOTDCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def on_ready(self):
        logger.debug('MOTD - COMMANDS Cog Ready')


    ### MAIN COMMAND TO SET UP MOTD ###
    @commands.command()
    @commands.cooldown(1, 15, commands.BucketType.guild)
    async def MOTDsetup(self, ctx, timeRun):
        if await fs.isAdmin(ctx.author) == True:
            # checks if bot's role is above all non-exempted hoisted roles & returns messages
            try:
                roleCheckResult = await fs.checkServRoles(ctx.guild)
                if roleCheckResult == 1:
                    await ctx.send('*Roles look OK...*')
                    pass # continues script
                elif roleCheckResult == 2:
                    await ctx.send(f'**Please move my role ({botRole.mention}) above the Member of the Day role**')
                    return # stops script
                elif roleCheckResult == 3:
                    await ctx.send(f'**Please move my role ({botRole.mention}) above all non-exempted hoisted roles**\n'
                            "It's also recommended (but not required) to move my role above all non-exempted colored roles\n"
                            'Use **!MOTDexempt** to exempt a role from Member of the Day (useful for admin roles)')
                    return # stops script
            except:
                await ctx.send('**An error occurred checking for my role position**')
                return # error stops script
            # gather variables from command
            serverEntry = await fs.getServerEntry(fs.serverPath,ctx.guild.id)
            botRole = discord.utils.get(ctx.guild.roles, id=serverEntry['botRoleID'])
            await asyncio.sleep(1)
            logger.info(f'!MOTDsetup started in {ctx.guild.name} by {ctx.author.name}')
            # create motd role if prev id not found in db, keep current if found
            for role in ctx.guild.role_hierarchy:
                if role.id == serverEntry['motdRoleID']:
                    motdRole = role
                    await ctx.send(f'*Found MOTD role: {motdRole.mention}...*')
                    break
            else:
                motdRole = await ctx.guild.create_role(name='Member of the Day',colour=discord.Color(0xe1ff39),mentionable=True)
                await ctx.send(f'*Created {motdRole.mention}...*')
                await asyncio.sleep(1.5)
            motdNewPos = botRole.position - 1
            # move position of motdRole to 1 below bot
            if motdRole.position != motdNewPos:
                await motdRole.edit(hoist=True,position = motdNewPos)
                await ctx.send(f'*New MOTD role position: {str(motdNewPos)}...*')
            else:
                await ctx.send(f'*MOTD role in correct position: {str(motdNewPos)}...*')
            # create secret channel if prev id not found in db, keep current if found
            for chan in ctx.guild.text_channels:
                if chan.id == serverEntry['secretChID']:
                    secretCh = chan
                    await ctx.send(f'*Found secret channel: {secretCh.mention}...*')
                    break
            else:
                secretCh = await ctx.guild.create_text_channel('member-of-the-day',
                        overwrites = { ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                                        motdRole: discord.PermissionOverwrite(read_messages=True),
                                        ctx.guild.me: discord.PermissionOverwrite(read_messages=True) })
                await secretCh.edit(position=0,topic='a secret text channel only for members of the day')
                await ctx.send(f'*Created secret channel: {secretCh.mention}...*')
            # display server, channel, & time info to be appended
            await ctx.send(f'```"{ctx.guild.name}" ID: {ctx.guild.id}\n#{ctx.channel.name} ID: {ctx.channel.id}\nTime chosen: {timeRun}```'
                            f'*Appending server info to database...*')
            # update server to json file
            try:
                await fs.updateServerMOTD(ctx.guild.id,ctx.guild.name,ctx.channel.name,ctx.channel.id,timeRun,motdRole.id,secretCh.id)
                await ctx.send(f'Successfully updated **{ctx.guild.name}** in the database! '
                                f'I will pick a winner at **{timeRun}** in **#{ctx.channel.name}** ')
            # if error occurs while updating server
            except:
                await ctx.send('**An error has occured while updating the database!!**')
        else:
            await ctx.send('**Only members with admin privilages can use this command!**')



    # help on how to set up MOTD
    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def MOTDhelp(self, ctx):
        await ctx.send( 'Use the **!MOTDsetup** command to set up Member of the Day. '
                        'In order to run Member of the Day on this server I will create a MOTD role '
                        'and secret text channel. I will also need a text channel to post announcements '
                        'in. This is determined by the text channel you run the setup command in. '
                        'Lastly, I will need a specified minute (CST) during the day to run the script '
                        'which should be formatted HRS:MINS after the command. '
                        'For example, If the following was posted in the #general chat, I will announce '
                        'a new member for the Member of the Day role at 10PM CST every day in #general: \n'
                        '**!MOTDsetup 22:00** <--- (you can copy and paste this if you want)')
        logger.info(f'!MOTDhelp called in {ctx.guild.name}')


    # get a list of servers w/ times running MOTD
    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def MOTDservs(self, ctx):
        if await fs.isAdmin(ctx.author):
            servLst = []
            logger.info(f'ServList DB query: {ctx.author.name} in {ctx.guild.name} ({ctx.guild.id})')
            try:
                data = await fs.openJson(fs.serverPath)
                for a,b in data.items():
                    servLst.append(f"{b['servName']}" +" | "+ f"#{b['chanName']}" +" | "+ f"{b['timeStart']}\n")
                servLst = "".join(servLst)
                await ctx.send('**Member of the Day - Server List & Run Times**\n'
                                '```' +servLst+ '```')
            except:
                await ctx.send('There are no servers in the database.')

    # output runTimes list from motd_times.py
    @commands.command()
    async def MOTDrts(self, ctx):
        if await fs.isAdmin(ctx.author):
            await ctx.send(f'runTimes: '+ str(rt.runTimes))

    # append a role to be exempted from MOTD to DB
    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def MOTDexempt(self, ctx, *, exemptingRole: discord.Role):
        if await fs.isAdmin(ctx.author):
            # checks if role is already in db
            serverEntry = await fs.getServerEntry(fs.serverPath,ctx.guild.id)
            motdRole = discord.utils.get(ctx.guild.roles, id = serverEntry['motdRoleID'])
            exemptRoles = serverEntry['exemptRoles']
            if exemptingRole == motdRole:
                await ctx.send('pls dont break my code')
                return
            elif exemptingRole.id in exemptRoles:
                # role already exempted
                await ctx.send(f'**{exemptingRole.name}** was already exempted from {motdRole.name}!')
            else:
                # add role to exemptions
                try:
                    exemptRoles.append(exemptingRole.id)
                    await fs.updateServerVal(fs.serverPath,ctx.guild.id,'exemptRoles',exemptRoles)
                    await ctx.send(f'**{exemptingRole.name}** is now exempted from {motdRole.name}.')
                    logger.info(f'\nServer List DB update: {ctx.guild.name} | Role exemption ADDED: {exemptingRole.name}')
                except:
                    await ctx.send('**An error occurred!**')

    # remove a role to be exempted from MOTD to DB
    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def MOTDallow(self, ctx, *, allowingRole: discord.Role):
        if await fs.isAdmin(ctx.author):
            # checks if role is already in db
            serverEntry = await fs.getServerEntry(fs.serverPath,ctx.guild.id)
            motdRole = discord.utils.get(ctx.guild.roles, id = serverEntry['motdRoleID'])
            exemptRoles = serverEntry['exemptRoles']
            if allowingRole == motdRole:
                await ctx.send('pls dont break my code')
                return
            elif allowingRole.id in exemptRoles:
                # remove role from exemptions
                try:
                    exemptRoles.remove(allowingRole.id)
                    await fs.updateServerVal(fs.serverPath,ctx.guild.id,'exemptRoles',exemptRoles)
                    await ctx.send(f'**{allowingRole.name}** is now allowed for {motdRole.name}.')
                    logger.info(f'\nServList DB update: {ctx.guild.name} | Role exemption REMOVED: {allowingRole.name}')
                except:
                    await ctx.send('**An error occurred!**')
            else:
                # role already allowed
                await ctx.send(f'**{allowingRole.name}** was already allowed for {motdRole.name}.\n'
                                f'Use **!exemptedroles** to get a list of all exempted roles.')

    # toggles between pausing the server in the loop
    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def MOTDpause(self, ctx):
        if await fs.isAdmin(ctx.author):
            serverEntry = await fs.getServerEntry(fs.serverPath,ctx.guild.id)
            try:
                if serverEntry['isPaused'] == False:
                    await fs.updateServerVal(fs.serverPath,ctx.guild.id,'isPaused',True)
                    await ctx.send(f'I am now **PAUSED** on *{ctx.guild.name}*!\n'
                                    'Use !MOTDpause again to unpause me!')
                    logger.info(f'\nServer List DB update: {ctx.guild.name} | isPaused: True')
                else:
                    await fs.updateServerVal(fs.serverPath,ctx.guild.id,'isPaused',False)
                    await ctx.send(f'I am now **UNPAUSED** on *{ctx.guild.name}*!\n'
                                    'Use !MOTDpause again to pause me!')
                    logger.info(f'\nServer List DB update: {ctx.guild.name} | isPaused: False')
            except:
                await ctx.send('**An error occurred!**')

    # toggles the reminder that sends an hour before
    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def MOTDreminder(self, ctx):
        if await fs.isAdmin(ctx.author):
            serverEntry = await fs.getServerEntry(fs.serverPath,ctx.guild.id)
            try:
                if serverEntry['reminder'] == True:
                    await fs.updateServerVal(fs.serverPath,ctx.guild.id,'reminder',False)
                    await ctx.send(f'I will **NOT** remind an hour before on *{ctx.guild.name}*!\n'
                                    'Use !MOTDreminder again to enable the reminder!')
                    logger.info(f'\nServer List DB update: {ctx.guild.name} | reminder: False')
                else:
                    await fs.updateServerVal(fs.serverPath,ctx.guild.id,'reminder',True)
                    await ctx.send(f'I **WILL** remind an hour before on *{ctx.guild.name}*!\n'
                                    'Use !MOTDreminder again to enable the reminder!')
                    logger.info(f'\nServer List DB update: {ctx.guild.name} | reminder: True')
            except:
                await ctx.send('**An error occurred!**')


    # see which roles are excluding
    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def when(self, ctx):
        # gather variables from command
        server = ctx.guild
        serverEntry = await fs.getServerEntry(fs.serverPath,ctx.guild.id)
        motdRole = discord.utils.get(ctx.guild.roles, id = serverEntry['motdRoleID'])
        await ctx.send(f"**{ctx.guild.name} - {motdRole.name}**\n"
                        f"**{serverEntry['timeStart']}** in *#{serverEntry['chanName']}*")
        logger.info(f'!when called by {ctx.author.name} in {ctx.guild.name}')

    # see which roles are excluding
    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def exemptedroles(self, ctx):
        # gather variables from command
        serverEntry = await fs.getServerEntry(fs.serverPath,ctx.guild.id)
        motdRole = discord.utils.get(ctx.guild.roles, id = serverEntry['motdRoleID'])
        exemptRoles = serverEntry['exemptRoles']
        if not exemptRoles:
            await ctx.send(f'There are no roles being exempted from {motdRole.name}')
        else:
            exemptNames = []
            for roleid in exemptRoles:
                role = discord.utils.get(ctx.guild.roles, id = roleid)
                exemptNames.append(f'**{role.name}**')
            exemptNames = ", ".join(exemptNames)
            await ctx.send(f'Roles exempted from {motdRole.name}:\n{exemptNames}')
        logger.info(f'!exemptedroles called by {ctx.author.name} in {ctx.guild.name}')

    # shows top members in motd_scores.json
    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def hiscores(self, ctx):
        topScoreLst = []
        serverEntry = await fs.getServerEntry(fs.serverPath,ctx.guild.id)
        motdRole = discord.utils.get(ctx.guild.roles, id = serverEntry['motdRoleID'])
        exemptRoles = serverEntry['exemptRoles']
        scoresEntry = await fs.getServerEntry(fs.scorePath,ctx.guild.id)
        try:
            counter = 0
            for k,v in scoresEntry.items():
                try:
                    mem = ctx.guild.get_member(int(k))
                    # check if member is exempted. if so, exclude from list
                    if any(role.id in exemptRoles for role in mem.roles):
                        pass
                    else:
                        topScoreLst.append(f"*{mem.name}*" +"  **|**  "+ f"{str(v)}\n")
                        counter += 1
                        if counter == 15: # how many members to show
                            break
                except:
                    logger.debug(f'Skipped {k} in !hiscores: {ctx.guild.name} - {ctx.guild.id}')
                    pass
            topScoreLst = "".join(topScoreLst)
            await ctx.send(f'**Top {str(counter)} Hiscores - {motdRole.name}**\n'+topScoreLst)
        except:
            await ctx.send('No servers in database.')
        logger.info(f'!hiscores called in {ctx.guild.name} by {ctx.author.name}')

    # shows score for a person from motd_scores.json
    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def score(self, ctx):
        # TEMP
        # await ctx.send(f'Scores are hidden right now!')
        # return
        # STARTS HERE
        serverEntry = await fs.getServerEntry(fs.serverPath,ctx.guild.id)
        votingEntry = await fs.getServerEntry(fs.votePath,ctx.guild.id)
        scoresEntry = await fs.getServerEntry(fs.scorePath,ctx.guild.id)
        motdRole = discord.utils.get(ctx.guild.roles, id = serverEntry['motdRoleID'])
        exemptRoles = serverEntry['exemptRoles']
        # check if user is looking up someone or themselves
        if ctx.message.content == '!score':
            memLookup = ctx.author
        else:
            splitContent = ctx.message.content.split(" ")
            delComm = '!score'
            allName = []
            for i in splitContent: # turns entire message list --> string
                if delComm in i:
                    pass
                else:
                    allName.append(i)
            allName_str = ' '.join(map(str, allName))
            # check if member exists
            try:
                memLookup = await commands.MemberConverter().convert(ctx, allName_str)
            except:
                await ctx.send(f"I can't find {allName_str}")
        # check if member is exempted. if so, dont display info
        if any(role.id in exemptRoles for role in memLookup.roles):
            await ctx.send(f'**{memLookup.name}** is exempted from {motdRole.name}')
            pass
        else:
            # check dictionary for member
            if str(memLookup.id) in scoresEntry:
                try:
                    # get WIN count
                    motdWins = scoresEntry[str(memLookup.id)]
                    # get RANKING from first instance of win count in dict
                    counter = 1
                    for k,v in scoresEntry.items():
                        if v == int(motdWins):
                            memRank = counter
                            break
                        else:
                            # check if k has role that is exempted
                            try:
                                notMem = await commands.MemberConverter().convert(ctx, k)
                                if any(role.id in exemptRoles for role in notMem.roles):
                                    logger.debug(f' -Skipped {notMem.name}')
                                    pass
                                else: # not memLookup or is not exempted, add rank counter
                                    counter += 1
                            except:
                                logger.debug(f' -Couldnt find a member with id: {k}')
                    # get member's current VOTES
                    votes = 0
                    for k,v in votingEntry.items():
                        if k == str(memLookup.id):
                            votes = v
                            break
                    # send message
                    await ctx.send(f"**{memLookup.name} - {motdRole.name}**\n"
                                    f"*Rank:*  {str(memRank)}  **|**  *Wins:*  {str(motdWins)}  **|**  *Current Votes:*  {str(votes)}")
                except:
                    await ctx.send('**An error occurred!**')
            else:
                await ctx.send(f'**{memLookup.name}** has never been chosen for {motdRole.name}')
        logger.info(f'!score called in {ctx.guild.name} by {ctx.author.name}: {ctx.message.content}')

    # show total MOTD picks & unique winners
    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def servertotals(self, ctx):
        serverEntry = await fs.getServerEntry(fs.serverPath,ctx.guild.id)
        scoresEntry = await fs.getServerEntry(fs.scorePath,ctx.guild.id)
        motdRole = discord.utils.get(ctx.guild.roles, id = serverEntry['motdRoleID'])
        # get counts
        try:
            counter1 = 0
            counter2 = 0
            for k,v in scoresEntry.items():
                counter1 += v
                counter2 += 1
            await ctx.send(f"**{ctx.guild.name} - {motdRole.name}**\n"
                            f"*Total Picks:*  {str(counter1)}  **|**  *Unique Winners:*  {str(counter2)}")
        except:
            await ctx.send(f'There have been no picks in {ctx.guild.name}')
        logger.info(f'!servertotals called in {ctx.guild.name} by {ctx.author.name}')

    # members vote for someone to have a better chance at MOTD
    @commands.command()
    @commands.cooldown(1, 0.5, commands.BucketType.guild)
    async def vote(self, ctx, *, member: discord.Member):
        # TEMP
        # await ctx.channel.purge(limit = 1)
        serverEntry = await fs.getServerEntry(fs.serverPath,ctx.guild.id)
        votingEntry = await fs.getServerEntry(fs.votePath,ctx.guild.id)
        currentMOTD = serverEntry['currentMOTD']
        exemptRoles = serverEntry['exemptRoles']
        usedVotes = votingEntry['usedVotes']
        voteCounts = votingEntry['voteCounts']
        motdRole = discord.utils.get(ctx.guild.roles, id = serverEntry['motdRoleID'])
        # TEMP
        #if member votes themselves
        if ctx.author.id == member.id:
            await ctx.author.edit(nick="I TRIED VOTING MYSELF")
            await ctx.send(f'You cannot vote for yourself!')
            return
        # if member votes a bot
        if member.bot:
            await ctx.send(f'You cannot vote for bots!')
            return
        # if member votes current MOTD
        elif member.id == currentMOTD:
            await ctx.send(f'This member is currently the {motdRole.name} and cannot be voted for today!')
            return
        # if member votes exempted member
        elif any(r.id in exemptRoles for r in member.roles):
            await ctx.send(f'This member is currently exempted from {motdRole.name} and cannot be voted for!')
            return
        # if member already voted
        elif str(ctx.author.id) in usedVotes:
            # check if event is active for more votes
            if await ev.eventStatus(ctx.guild.id,'quintVotes') != True:
                await ctx.send(f'You have used up all of your votes today!')
                return
            elif usedVotes[str(ctx.author.id)] >= 5:
                await ctx.send(f'You have used up all of your votes today!')
                return
        # if author hasnt voted today or has more votes to give
        try:
            # update usedVotes with author
            if str(ctx.author.id) in usedVotes:
                usedVotes[str(ctx.author.id)] += 1
            else:
                usedVotes[str(ctx.author.id)] = 1
            # update voteCounts with votee
            if str(member.id) in voteCounts:
                voteCounts[str(member.id)] += 1
            else:
                voteCounts[str(member.id)] = 1
            # update usedVotes + voteCounts dicts
            votingEntry['usedVotes'] = usedVotes
            votingEntry['voteCounts'] = voteCounts
            # write voting dict
            await fs.updateServerEntry(fs.votePath,ctx.guild.id,votingEntry)
            logger.info(f'\n{ctx.author.name} voted for {member.name} in {ctx.guild.name}.'
                        f'\nTotal votes: {voteCounts[str(member.id)]}')
            # TEMP
            await ctx.send(f'{ctx.author.name} voted for **{member.name}**. Total votes: **{voteCounts[str(member.id)]}**')
            # await ctx.send(f'{ctx.author.name} voted! Used votes: **{usedVotes[str(ctx.author.id)]}** out of 5')
        except:
            await ctx.send('**An error occurred!**')

    # shows people with votes in motd_voting.json
    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def totalvotes(self, ctx):
        # TEMP
        # await ctx.send(f'Total votes are hidden right now!')
        # return
        # STARTS HERE
        voteLst = []
        serverEntry = await fs.getServerEntry(fs.serverPath,ctx.guild.id)
        votingEntry = await fs.getServerEntry(fs.votePath,ctx.guild.id)
        motdRole = discord.utils.get(ctx.guild.roles, id = serverEntry['motdRoleID'])
        voteCounts = votingEntry['voteCounts']
        try:
            for k,v in voteCounts.items():
                try:
                    mem = ctx.guild.get_member(int(k))
                    voteLst.append(f"*{mem.name}*" +"  **|**  "+ f"{str(v)}\n")
                except:
                    logger.debug(f'Skipped {k} in !totalvotes')
                    pass
            voteLst = "".join(voteLst)
            await ctx.send(f'**Member Votes - {motdRole.name}**\n{voteLst}')
        except:
            await ctx.send('No members have been voted for.')
        logger.info(f'!totalvotes called in {ctx.guild.name} by {ctx.author.name}')


    # shows people with votes in motd_voting.json
    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def stuffballotbox(self, ctx):
        await ctx.send(f'The ballot has now been stuffed')

    
    '''# RANDOM
    @commands.command()
    async def randomstuff(self, ctx):
        memDict = {}
        for c in ctx.guild.text_channels:
            if c.id == 134858585669763072:
                chan = c
        print(chan)
        last = await chan.get_message(477310163611811860)
        async for mes in chan.history(limit=None, after=last):
            if 'grats' in mes.content:
                print('found match')
                print(mes.created_at)
                if mes.mentions != None:
                    for mem in mes.mentions:
                        memId = str(mem.id)
                        print(memId)
                        if memId in memDict:
                            memDict[memId] += 1
                        else:
                            memDict[memId] = 1
                        print(memDict[memId])
        sortedScores = {k: v for k, v in sorted(memDict.items(), key=lambda x: x[1], reverse=True)}
        with open(oldscoresPath, "w") as write_file:
                json.dump(sortedScores, write_file, indent=4)
        print('done!')'''

def setup(bot):
    bot.add_cog(MOTDCommands(bot))