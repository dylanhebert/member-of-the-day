# Member of the Day - A Discord Bot

Once a day, a member randomly gets picked to be "Member of the Day". Members picked have the ability to post in the #member-of-the-day chat only accessible by people who are currently "Member of the Day". Also once a day, members can vote for other members to have a better chance at winning the next drawing. Members and their votes from others are only eligible to be picked if they are online during the drawing time for their Discord server.

## Basic Commands
Default prefix: !
```
vote {member}  - Once a day, give another member a better chance at being picked
score {member}  - See how many times a member has been picked
totalvotes  - See who has been voted for and how many times for the current day
hiscores  - See the top 15 picked members and how many times they've won
servertotals  - See total amount of picks and winners for the server
exemptedroles  - Show which roles are currently exempted from being picked
when  - Show what time MOTD will be picked
```

## Admin Commands
Default prefix: !
```
MOTDsetup {HH:MM}  - Set up MOTD or change the run time/announce channel
MOTDexempt {role}  - Exempt a role from being picked
MOTDallow {role}  - Allow a role that was exempted to be picked again
MOTDpause  - Pauses/unpauses the bot from running every day (toggleable)
MOTDreminder  - Enables/disables the reminder that happens an hour before (toggleable)
```
