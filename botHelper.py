###
# botHelper.py
#
# Description: Helper function for the discord commands
# Created by: Alvin Tsang
# Created on: October 6, 2022
###

import discord
from discord.ext import commands
import os
import datetime as dt
from datetime import timedelta
import json
import notionDB

#############
# CONSTANTS #
#############

# colours
GREEN = 0x3bcc42
RED = 0xa83252
PURPLE = 0xaa50de
YELLOW = 0xFFFF00

####################
# HELPER FUNCTIONS #
####################


# Description: Read tags.json and format the names for each
# 			   tag into a list. In addition, update the
# 			   global variable tagNames
def listTagNames(tagNames):
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
async def displayTaskInfo_name(ctx, taskName, title):
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

    embed = discord.Embed(title=title, description=task, color=PURPLE)
    await ctx.send(embed=embed)


# Description: Create an embed for the caller function to post in a model
# @param data: String of data in the // format
# @param title: Title of the model
# @return: embed of the page information
# Pre-condition: data is guaranteed to be in teh correct format
async def displayTaskInfo_str(ctx, data, title):
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
    embed = discord.Embed(title=title, description=task, color=GREEN)
    await ctx.send(embed=embed)


# Description: Create an embed for an error
async def errorMessage(ctx, desc):
    embed = discord.Embed(title="Error!", description=desc, color=RED)
    await ctx.send(embed=embed)


# Description: Display all the tasks that have assigned to assignedTo
async def printPersonTasks(ctx, assignedTo):
    tasks = []
    with open("./pages.json") as f:
        pages = json.load(f)

    for page in pages:
        assignedList = page["properties"]["Assigned to"]["multi_select"]
        for tag in assignedList:
            if tag["name"] == assignedTo:
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

            taskName = (
                task["properties"]["Task"]["title"][0]["text"]["content"])
            desc = (task["properties"]["Description"]["rich_text"][0]["text"]
                    ["content"])
            completion = ("Yes" if
                          (task["properties"]["Completion"]["checkbox"])
                          == True else "No")
            dateTime = task["properties"]["Date"]["date"]["start"]
            assignedTo = ", ".join(assignedToList)
            assignedBy = ", ".join(assignedByList)
            taskType = ", ".join(typeList)
            url = task["url"]
            blank = " "
            t = ("**----- Task: {9} -----**\n>>> " +
                 "Task Name:\t{6}{6}{6}{0}\n" + "Description:\t{6}{6}{1}\n" +
                 "Date & Time:\t{6}{2}\n" + "Assigned To:\t{6}{3}\n" +
                 "Assigned By:\t{4}\n" + "Task Type:\t\t{6}{5}\n" +
                 "Completion: \t{7}\n" + "Link: \t\t{8}").format(
                     taskName, desc, dateTime, assignedTo, assignedBy,
                     taskType, blank, completion, url, index)
            await ctx.send(t)
            index += 1
