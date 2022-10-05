###
# bot.py
#
# Created by: Alvin Tsang
# Created on: Sept 16, 2022
#
###

import discord
from discord.ext import commands
import os
import datetime as dt
from datetime import timedelta
import notionDB
import json

#############
# CONSTANTS #
#############

months = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12
}

# colours
GREEN = 0x3bcc42
RED = 0xa83252
PURPLE = 0xaa50de
YELLOW = 0xFFFF00

####################
# GLOBAL VARIABLES #
####################

# Define the bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="$", intents=intents)

# tasks that are pending for deletion from Notion
deleteList = []

#list of all tag names
assignToNames = []
assignByNames = []
typeNames = []
tagNames = [assignToNames, assignByNames, typeNames]

####################
# HELPER FUNCTIONS #
####################


# Description: Read tags.json and format the names for each tag
# 			   into a list. In addition, update the global
#			   variable tagNames
def listTagNames():
    # load the json file contents
    notionDB.readDatabase()
    with open("./tags.json") as f:
        data = json.load(f)

# store names of assignToIDs
    list = data[0]["assignToIDs"]
    assignTo = "**Assign To**: \t"
    tagNames[0] = []
    for i in range(0, len(list)):
        assignTo = assignTo + list[i]["name"] + "\t|\t"
        tagNames[0].append(list[i]["name"])

# store names of assignByIDs
    list = data[1]["assignByIDs"]
    assignBy = "**Assign By**: \t"
    tagNames[1] = []
    for i in range(0, len(list)):
        assignBy = assignBy + list[i]["name"] + "\t|\t"
        tagNames[1].append(list[i]["name"])

# store names of taskIDs
    list = data[2]["typeIDs"]
    taskTypes = "**Task Types**: \t"
    tagNames[2] = []
    for i in range(0, len(list)):
        taskTypes = taskTypes + list[i]["name"] + "\t|\t"
        tagNames[2].append(list[i]["name"])

    return assignTo + "\n\n" + assignBy + "\n\n" + taskTypes


# Description: Create an embed for the caller function to post in a model
# @param taskName: Specific name of the task
# @param title: Title of the model
# @return: embed of the page information
# Pre-condition: Task name is guaranteed to be in the database
def displayTaskInfo_name(taskName, title):
    pageInfo = notionDB.getPage(taskName)

    # extract the page information
    taskName = pageInfo["name"]
    desc = pageInfo["description"]
    completion = "Yes" if pageInfo["completion"] == True else "No"
    dateTime = pageInfo["dateTime"]
    assignedTo = ", ".join(pageInfo["assignedTo"])
    assignedBy = ", ".join(pageInfo["assignedBy"])
    taskType = ", ".join(pageInfo["taskType"])
    url = pageInfo["url"]
    blank = " "
    task = ("Task Name:\t{6}{6}{6}{0}\n" + "Description:\t{6}{6}{1}\n" +
            "Date & Time:\t{6}{2}\n" + "Assigned To:\t{6}{3}\n" +
            "Assigned By:\t{4}\n" + "Task Type:\t\t{6}{5}\n" +
            "Completion: \t{7}\n" + "Link: \t\t{8}").format(
                taskName, desc, dateTime, assignedTo, assignedBy, taskType,
                blank, completion, url)

    return discord.Embed(title=title, description=task, color=PURPLE)


# Description: Create an embed for the caller function to post in a model
# @param data: String of data in the // format
# @param title: Title of the model
# @return: embed of the page information
# Pre-condition: data is guaranteed to be in teh correct format
def displayTaskInfo_str(data, title):
    # split the data into its components
    dataSplit = data.split("//")
    taskName = dataSplit[0].strip()
    desc = dataSplit[1].strip()
    dateTime = dataSplit[2].strip()
    assignedTo = dataSplit[3].strip()
    assignedBy = dataSplit[4].strip()
    taskType = dataSplit[5].strip()

    # create embed
    blank = " "
    task = ("Task Name:\t{6}{6}{6}{0}\n" + "Description:\t{6}{6}{1}\n" +
            "Date & Time:\t{6}{2}\n" + "Assigned To:\t{6}{3}\n" +
            "Assigned By:\t{4}\n" + "Task Type:\t\t{6}{5}").format(
                taskName, desc, dateTime, assignedTo, assignedBy, taskType,
                blank)
    return discord.Embed(title=title, description=task, color=GREEN)


# Description: Create an embed for an error
def errorMessage(desc):
    return discord.Embed(title="Error!", description=desc, color=RED)


#############################
# Data Validation Functions #
#############################


# Description: Check that the given date and time is after
# 			   the current system date and time
# @param date_txt: The date and time as a string with format [01 Jan 22 1300]
# @return: If there are no errors, return a blank message, otherwise, return
# 		   an error message
def validDateTime(date_txt):
    noError = " "

    list = date_txt.split(" ")
    # check date_txt was inputted in the correct format
    if len(list) != 4:
        return ("Date and time components must be" +
                " seperated by 1 space [i.e. 01 Jan 22 0321]")

# split data into it's values
    day = int(list[0])
    month = list[1].lower()
    year = int("20" + list[2])
    time = list[3]

    # check if month exists
    if month not in months:
        return ("Incorrect month key name. " +
                "Month must be a three-letter abreviation")

# check that task datetime is after the current datetime
    currentDate = dt.datetime.today() + timedelta(
        hours=-7)  # account for pacific timezone
    taskDate = currentDate.replace(year,
                                   months[month],
                                   day,
                                   hour=int(time[:2]),
                                   minute=int(time[-2:]))

    if not currentDate < taskDate:
        return "Task date is not after current date"

    return noError


# Description: Check if the taskName exists within pages.json
# @param taskName: Name of a task
# @return: If taskName exists, return true, false otherwise
def taskNameExists(taskName):
    ret = False
    with open("./pages.json") as f:
        pages = json.load(f)

    for page in pages:
        if (page["properties"]["Task"]["title"][0]["text"]["content"].lower()
                == taskName.lower()):
            ret = True

    return ret


# Description Check if a given list of tags exists for that heading
# @param str_list: string of tags that are seperated by a single comma
# @param listNum: Enumeration of which list to accesss
#				  [{0: assignTo}, {1: assignBy}, {2: taskType}]
# @return: List of tags with a validation bit.
# 		   If the list is VALID, (index 0) == 0, and subsequent indices
#		   are the correct tags
# 		   If the list is INVALID, (index 0) == 1, and subsequent indices
#		   are the incorrect tags
# 		   If the tags list is empty from Notion, (index 0) == -1, and
#		   (index 1) == error message
# Pre-condition: listNum is within {0,1,2}
def listValidation(str_list, listNum):
    listTagNames()
    ret = [0]  # return list with a valid bit
    list = tagNames[listNum]

    # no tags from notion
    if len(list) == 0:
        ret[0] = -1
        ret.append("No valid tags")
    else:
        # isolate tags from str_list
        nameList = str_list.split(",")
        nameList = [name.strip() for name in nameList]
        nameList_lowered = [item.lower() for item in nameList]

        # check if tag is in the list
        for i in range(0, len(nameList_lowered)):
            inserted = False
            j = 0
            while j < len(list) and not inserted:
                # append to ret if name matches and valid bit
                if (nameList_lowered[i] == list[j].lower() and ret[0] == 0):
                    ret.append(list[j])
                    inserted = True
# mark the string as a match so it is not added to invalid ret
                elif (nameList_lowered[i] == list[j].lower() and ret[1] == 0):
                    inserted = True
                j += 1

# if ret is so far valid, but the current name
# is not in list, reset ret, give an invalid bit
# and append the invalid name
            if ret[0] == 0 and not inserted:
                ret = []
                ret.append(1)
                ret.append(nameList[i])

# if ret is the list of invalid names and the
#current name is invalid, add it invalid list
            elif ret[0] == 1 and not inserted:
                ret.append(nameList[i])

    return ret


######################
# Discord Bot events #
######################


# Description: Wait for the bot to be ready and read the notion database
@bot.event
async def on_ready():
    print("Logged in as {0.user}".format(bot))
    notionDB.readDatabase()


# Description: Capture a message sent by a user and do a action
#			   depending on the event
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith("!hello"):
        await message.channel.send("Hello!")

    if message.content.startswith("!see tags"):
        embed = discord.Embed(title="Avaliable Tags for Task Creation",
                              description=listTagNames(),
                              color=PURPLE)
        # print(tagNames)
        await message.channel.send(embed=embed)

    if message.content.startswith("!see fields"):
        embed = discord.Embed(title="Avaliable Fields",
                              description="1:\tTask Name\n" +
                              "2:\tDescription\n" + "3:\tDate & Time\n" +
                              "4:\tAssigned To\n" + "5:\tAssigned By\n" +
                              "6:\tTask Type\n" + "7:\tCompletion",
                              color=PURPLE)
        await message.channel.send(embed=embed)

    await bot.process_commands(message)


# Description: Validate and create a new task
# @param ctx: Where the event is happening
# @param data: information about the event delimitted by //.
# Pre-condition: data should follow the format -->
# 	$newTask "taskName//desc//01 jan 22 1400//assignTo, tags//assignBy, tags//taskType, tag"
# Post-condition: Append the new task to pendingList
# Post-condition: On success, post a model to the Discord channel. Otherwise, post the
# 				  reason why an error occured
@bot.command()
async def newTask(ctx, data):
    # split data into it's values
    dataSplit = data.split("//")
    taskName = dataSplit[0].strip()
    desc = dataSplit[1].strip()
    dateTime = dataSplit[2].strip()
    assignedTo = dataSplit[3].strip()
    assignedBy = dataSplit[4].strip()
    taskType = dataSplit[5].strip()

    ### data validation ###
    taskNameMsg = taskNameExists(taskName)
    dtMsg = validDateTime(dateTime)
    assignToValid = listValidation(assignedTo, 0) if assignedTo != "" else [0]
    assignByValid = listValidation(assignedBy, 1) if assignedBy != "" else [0]
    taskTypeValid = listValidation(taskType, 2) if taskType != "" else [0]

    if taskNameMsg == True:
        await ctx.send(embed=errorMessage(taskName +
                                          " is a name used for another task"))
    elif dtMsg != " ":
        await ctx.send(embed=errorMessage(dtMsg))
    elif assignToValid[0] == -1:
        await ctx.send(embed=errorMessage("No \"Assign To\" tags avaliable"))
    elif assignByValid[0] == -1:
        await ctx.send(embed=errorMessage("No \"Assign By\" tags avaliable"))
    elif taskTypeValid[0] == -1:
        await ctx.send(embed=errorMessage("No \"Task Type\" tags avaliable"))
    elif assignToValid[0] == 1:
        list = ", ".join(assignToValid[1:])
        await ctx.send(embed=errorMessage("The following \"Assign To\" tags" +
                                          " are incorrect: \t" + list))
    elif assignByValid[0] == 1:
        list = ", ".join(assignByValid[1:])
        await ctx.send(embed=errorMessage("The following \"Assign By\" tags" +
                                          " are incorrect: \t" + list))
    elif taskTypeValid[0] == 1:
        list = ", ".join(taskTypeValid[1:])
        await ctx.send(embed=errorMessage("The following \"Task Type\" tags" +
                                          " are incorrect: \t" + list))
    else:
        # parse dateTime
        dateTime = (dt.datetime.today().replace(int("20" + dateTime[7:9]),
                                                int(months[dateTime[3:6]]),
                                                int(dateTime[0:2]),
                                                hour=int(dateTime[10:12]),
                                                minute=int(dateTime[13:15]),
                                                microsecond=0).isoformat())
        assignedTo = ", ".join(assignToValid[1:])
        assignedBy = ", ".join(assignByValid[1:])
        taskType = ", ".join(taskTypeValid[1:])
        # parse assignTo tags
        assignToList = []
        list = assignedTo.split(",")
        list = [tag.strip() for tag in list]
        for tag in list:
            assignToList.append({"name": tag})

# parse assignBy tags
        assignByList = []
        list = assignedBy.split(",")
        list = [tag.strip() for tag in list]
        for tag in list:
            assignByList.append({"name": tag})

# parse taskType tags
        taskTypeList = []
        list = taskType.split(",")
        list = [tag.strip() for tag in list]
        for tag in list:
            taskTypeList.append({"name": tag})

# post new task
        status = notionDB.createPage(taskName, desc, dateTime, assignToList,
                                     assignByList, taskTypeList)
        if status == 200:
            notionDB.readDatabase()
            title = "*" + taskName.capitalize() + "*" + " is posted to Notion"
            await ctx.send(embed=displayTaskInfo_str(data, title))
        else:
            desc = (taskName.capitalize() + " could not be posted. " +
                    "Ask ask CI Tsang for help or report it to" +
                    " the channel *bot-errors*")
            await ctx.send(embed=errorMessage(desc))


# Description: Get a task from the Notion database and display its contents
# @param taskName: Unique name of the task
@bot.command()
async def getTask(ctx, taskName):
    msg = taskNameExists(taskName)
    if msg == False:
        await ctx.send(embed=errorMessage("Task name does not exist"))
    else:
        embed = displayTaskInfo_name(taskName, "Task Request")
        await ctx.send(embed=embed)


# Description: Update a task that has already been added to Notion
# @param data: information about the event delimitted by //.
# Pre-condition: data should follow the format -->
# 	$newTask "taskName//field//info"
@bot.command()
async def updateTask(ctx, data):
    # split data into it's values
    dataSplit = data.split("//")
    taskName = dataSplit[0].strip()
    field = dataSplit[1].strip().lower()
    info = dataSplit[2].strip()

    # validate that the task name exists
    exists = taskNameExists(taskName)
    if exists == False:
        await ctx.send(embed=errorMessage("Task name does not exist"))
    else:
        # determine the field code and validate the data
        # field is enumerated such that:
        #	{1: Task}, {2: Description}, {3: Date},
        # 	{4: Assigned To}, {5: Assigned By},
        #	{6: Type}, {7: Completion}
        fieldCode = 0
        msg = ""
        if "name" in field:
            fieldCode = 1
            # validate data
            msg = taskNameExists(info)
            if msg == True:
                msg = "**" + info + "**" + " already exists for different task name"
                fieldCode = -1

        elif "desc" in field:
            fieldCode = 2
        elif "date" in field or "time" in field:
            fieldCode = 3
            msg = validDateTime(info)
            if msg != " ":
                fieldCode = -1
            else:
                # parse dateTime
                info = dt.datetime.today().replace(int("20" + info[7:9]),
                                                   int(months[info[3:6]]),
                                                   int(info[0:2]),
                                                   hour=int(info[10:12]),
                                                   minute=int(info[13:15]),
                                                   microsecond=0).isoformat()
        elif "to" in field:
            fieldCode = 4
            valid = listValidation(info, 0)
            if valid[0] == 1:
                fieldCode = -1
                list = ", ".join(valid[1:])
                msg = "The following \"Assign To\" tags are incorrect: " + list
            else:
                info = []
                list = valid[1:]
                list = [tag.strip() for tag in list]
                for tag in list:
                    info.append({"name": tag})

        elif "by" in field:
            fieldCode = 5
            valid = listValidation(info, 1)
            if valid[0] == 1:
                fieldCode = -1
                list = ", ".join(valid[1:])
                msg = "The following \"Assign By\" tags are incorrect: " + list
            else:
                info = []
                list = valid[1:]
                list = [tag.strip() for tag in list]
                for tag in list:
                    info.append({"name": tag})
        elif "type" in field:
            fieldCode = 6
            valid = listValidation(info, 2)
            if valid[0] == 1:
                fieldCode = -1
                list = ", ".join(valid[1:])
                msg = "The following \"Task Type\" tags are incorrect: " + list
            else:
                info = []
                list = valid[1:]
                list = [tag.strip() for tag in list]
                for tag in list:
                    info.append({"name": tag})
        elif "comp" in field:
            fieldCode = 7
            true = ["complete", "done", "true", "finish", "yes"]
            false = [
                "not done", "not complete", "undone", "undue", "false",
                "incomplete", "no"
            ]
            if info.lower() in true:
                info = True
            elif info.lower() in false:
                info = False
            else:
                fieldCode = -1
                msg = "Completion word is not recognized"

        if fieldCode == 0:
            desc = (
                "field name does not exist. " +
                "Use command \"$see field\" to see all possible field names")
            await ctx.send(embed=errorMessage(desc))
        elif fieldCode == -1:
            await ctx.send(embed=errorMessage(msg))
        else:
            notionDB.updatePage(taskName, fieldCode, info)
            notionDB.readDatabase()
            embed = displayTaskInfo_name(taskName, "Task Updated!")
            await ctx.send(embed=embed)


@bot.command()
async def deleteTask(ctx, taskName):
    msg = taskNameExists(taskName)
    if msg == False:
        await ctx.send(embed=errorMessage("Task name does not exist"))
    else:
        deleteList.append(taskName)
        embed = displayTaskInfo_name(taskName, taskName + " Pending Deletion")
        await ctx.send(embed=embed)


@bot.command()
async def confirmDeleteTask(ctx, taskName):
    if len(deleteList) < 1:  # pendingList is empty
        await ctx.send(embed=errorMessage("No tasks are pending deletion"))
    elif taskNameExists(taskName) == False:
        await ctx.send(
            embed=errorMessage("Task name does not exist\n" +
                               "Use `$listDeleteTask` to view" +
                               " the list of tasks that are pending deletion"))
    else:
        if taskName not in deleteList:
            await ctx.send(
                embed=errorMessage(taskName=" is not pending for deletion.\n" +
                                   "use `$deleteTask \"task name\"` to put" +
                                   " the task up for deletion"))
        else:  # Delete task from Notion
            title = "Task Removed from Notion"
            e = displayTaskInfo_name(taskName, title)

            res = notionDB.deletePage(taskName)
            if res == 200:
                deleteList.remove(taskName)
                notionDB.readDatabase()
                await ctx.send(embed=e)
            else:
                desc = (taskName + " could not be deleted from Notion. " +
                        "Ask ask CI Tsang for help or report it to" +
                        " the channel *bot-errors*")
                await ctx.send(embed=errorMessage(desc))


# Description: List all tasks that are pending deletion
@bot.command()
async def listDeleteTasks(ctx):
    # pendingList is empty
    if len(deleteList) < 1:
        await ctx.send(embed=errorMessage("No tasks pending deletion!"))
    # display on items in the pendingList
    else:
        index = 1
        await ctx.send("**__Pending Deletion Task List__**")
        for taskName in deleteList:
            pageInfo = notionDB.getPage(taskName)

            # extract the page information
            taskName = pageInfo["name"]
            desc = pageInfo["description"]
            completion = "Yes" if pageInfo["completion"] == True else "No"
            dateTime = pageInfo["dateTime"]
            assignedTo = ", ".join(pageInfo["assignedTo"])
            assignedBy = ", ".join(pageInfo["assignedBy"])
            taskType = ", ".join(pageInfo["taskType"])
            url = pageInfo["url"]
            blank = " "
            task = ("**----- Task: {9} -----**\n>>> " +
                    "Task Name:\t{6}{6}{6}{0}\n" +
                    "Description:\t{6}{6}{1}\n" + "Date & Time:\t{6}{2}\n" +
                    "Assigned To:\t{6}{3}\n" + "Assigned By:\t{4}\n" +
                    "Task Type:\t\t{6}{5}\n" + "Completion: \t{7}\n" +
                    "Link: \t\t{8}").format(taskName, desc, dateTime,
                                            assignedTo, assignedBy, taskType,
                                            blank, completion, url, index)
            await ctx.send(task)
            index += 1


@bot.command()
async def completeTask(ctx, taskName):
    # check task completion
    pageInfo = notionDB.getPage(taskName)
    completion = pageInfo["completion"]
    if completion:
        desc = taskName + " was already completed"
        embed = discord.Embed(title="Task is Complete",
                              description=desc,
                              color=PURPLE)
        await ctx.send(embed=embed)
    else:
        notionDB.updatePage(taskName, 7, True)
        notionDB.readDatabase()
        embed = displayTaskInfo_name(taskName, "Task Updated!")
        await ctx.send(embed=embed)


@bot.command()
async def listFields(ctx):
    embed = discord.Embed(title="Avaliable Fields",
                          description="1:\tTask Name\n" + "2:\tDescription\n" +
                          "3:\tDate & Time\n" + "4:\tAssigned To\n" +
                          "5:\tAssigned By\n" + "6:\tTask Type\n" +
                          "7:\tCompletion",
                          color=PURPLE)
    await ctx.send(embed=embed)


# Description: List all tasks assigned to a specfic person
@bot.command()
async def listTasks(ctx, assignedTo):
    notionDB.readDatabase()
    # validate if assignedTo tag exists
    valid = listValidation(assignedTo, 0)
    if (valid[0] != 0):
        list = ", ".join(valid[1:])
        await ctx.send(embed=errorMessage("The following \"Assign To\" tags" +
                                          " are incorrect: \t" + list))


# print all tasks assigned to the assignedTo
    else:
        tasks = []
        with open("./pages.json") as f:
            pages = json.load(f)

        for page in pages:
            assignedList = page["properties"]["Assigned to"]["multi_select"]
            for tag in assignedList:
                print(tag["name"])
                if tag["name"] == assignedTo:
                    print("here")
                    tasks.append(page)

        if len(tasks) == 0:
            message = discord.Embed(title="Tasks for " + assignedTo + ":",
                                    description="No tasks! Congradulations!",
                                    color=GREEN)
            await ctx.send(embed=message)

        else:
            index = 1
            for task in tasks:
                assignedToList = []
                assignedByList = []
                typeList = []

                for tag in task["properties"]["Assigned to"]["multi_select"]:
                    assignedToList.append(tag["name"])

                for tag in task["properties"]["Assigned by"]["multi_select"]:
                    assignedByList.append(tag["name"])

                for tag in task["properties"]["Type"]["multi_select"]:
                    typeList.append(tag["name"])

                taskName = task["properties"]["Task"]["title"][0]["text"][
                    "content"]
                desc = task["properties"]["Description"]["rich_text"][0][
                    "text"]["content"]
                completion = "Yes" if task["properties"]["Completion"][
                    "checkbox"] == True else "No"
                dateTime = task["properties"]["Date"]["date"]["start"]
                assignedTo = ", ".join(assignedToList)
                assignedBy = ", ".join(assignedByList)
                taskType = ", ".join(typeList)
                url = task["url"]
                blank = " "
                t = ("**----- Task: {9} -----**\n>>> " +
                     "Task Name:\t{6}{6}{6}{0}\n" +
                     "Description:\t{6}{6}{1}\n" + "Date & Time:\t{6}{2}\n" +
                     "Assigned To:\t{6}{3}\n" + "Assigned By:\t{4}\n" +
                     "Task Type:\t\t{6}{5}\n" + "Completion: \t{7}\n" +
                     "Link: \t\t{8}").format(taskName, desc, dateTime,
                                             assignedTo, assignedBy, taskType,
                                             blank, completion, url, index)

                await ctx.send(t)
                index += 1

bot.run(os.getenv("TOKEN"))
