import requests
import json
import os

#############
# CONSTANTS #
#############
headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "Authorization": "Bearer " + os.getenv("NOTION_API_KEY"),
    "Notion-Version": "2022-06-28"
}

payload = {"page_size": 100}

####################
# HELPER FUNCTIONS #
####################

# Return the page ID given the task name
# Guaranteed that task name exists
def getPageID(taskName):
	with open("./pages.json") as f:
		pages = json.load(f)
	
	for page in pages:
		if page["properties"]["Task"]["title"][0]["text"]["content"].lower() == taskName.lower():
			return page["id"]


############################
# NOTION MANAGER FUNCTIONS #
############################

	
# Get primary information about the database
# header: headers for get request
def readDatabase():
    url = "https://api.notion.com/v1/databases/{0}".format(
        os.getenv("DATABASE_ID"))

    response = requests.get(url, headers=headers)
    if (response.status_code == 200):
        print("Notion database connected")
    else:
        print("Notion database not connected")
    # store the database information in db.json
    data = json.loads(response.text)
    with open("./db.json", "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    updateTags(data)
    queryDatabase()


# Get and update the tags for the database
# data: string with json data from db.json
def updateTags(data):

    assignToIDs = []
    assignByIDs = []
    typeIDs = []

    list = data["properties"]

    # get 'assigned to' tags
    for item in list["Assigned to"]["multi_select"]["options"]:
        assignToIDs.append({"name": item["name"], "id": item["id"]})

    # get 'assigned by' tags
    for item in list["Assigned by"]["multi_select"]["options"]:
        assignByIDs.append({"name": item["name"], "id": item["id"]})

    # get 'type' tags
    for item in list["Type"]["multi_select"]["options"]:
        typeIDs.append({"name": item["name"], "id": item["id"]})

    tags = [{
        "assignToIDs": assignToIDs
    }, {
        "assignByIDs": assignByIDs
    }, {
        "typeIDs": typeIDs
    }]

    # save tags in tags.json
    with open("./tags.json", "w", encoding="utf8") as f:
        json.dump(tags, f, ensure_ascii=False, indent=4)


def createPage(task, description, dueDate, assignedTo, assignedBy, taskType):
    readDatabase()
    url = "https://api.notion.com/v1/pages"

    newPageData = {
        "parent": {
            "database_id": os.getenv("DATABASE_ID")
        },
        "properties": {
            "Task": {
                "title": [{
                    "text": {
                        "content": task
                    }
                }]
            },
            "Description": {
                "rich_text": [{
                    "type": "text",
                    "text": {
                        "content": description
                    }
                }]
            },
            "Date": {
                "date": {
                    "start": dueDate
                }
            },
            "Assigned to": {
                "multi_select": assignedTo
            },
            "Assigned by": {
                "multi_select": assignedBy
            },
            "Type": {
                "multi_select": taskType
            }
        }
    }

    data = json.dumps(newPageData)
    res = requests.post(url, headers=headers, data=data)
    print("New task status code:", res.status_code)
    return res.status_code


# Find the page ID given the task name
# Task name must be unique, otherwise, the first task in the list will be given
def getPage(taskName):
    queryDatabase()
    pageInfo = {}
    with open("./pages.json") as f:
        pages = json.load(f)

    # find page id given page name
    for page in pages:
	    if page["properties"]["Task"]["title"][0]["text"]["content"].lower() == taskName.lower():
		    desc = page["properties"]["Description"]["rich_text"][0]["text"]["content"]
		    completion = page["properties"]["Completion"]["checkbox"]
		    dateTime = page["properties"]["Date"]["date"]["start"]
		    assignedTo = [tag["name"] for tag in page["properties"]["Assigned to"]["multi_select"]]
		    assignedBy = [tag["name"] for tag in page["properties"]["Assigned by"]["multi_select"]]
		    taskType = [tag["name"] for tag in page["properties"]["Type"]["multi_select"]]
		    url = page["url"]
		    id = page["id"]
			
		    pageInfo.update({"name": taskName}) 
		    pageInfo.update({"description": desc})
		    pageInfo.update({"completion": completion})
		    pageInfo.update({"dateTime": dateTime})
		    pageInfo.update({"assignedTo": assignedTo})
		    pageInfo.update({"assignedBy": assignedBy})
		    pageInfo.update({"taskType": taskType})
		    pageInfo.update({"url": url})
		    pageInfo.update({"pageID": id})
    
    # print(pageInfo)		
    return pageInfo



# limited to 100 pages
def queryDatabase():
    url = "https://api.notion.com/v1/databases/{0}/query".format(
        os.getenv("DATABASE_ID"))

    response = requests.post(url, json=payload, headers=headers)
    # print(response.text)

    jsonFile = json.loads(response.text)["results"]
    # filter unnessary keys
    for object in jsonFile:
        del object["created_time"]
        del object["last_edited_time"]
        del object["last_edited_by"]
        del object["created_by"]
        del object["cover"]
        del object["icon"]

        # store pages details into pages.json
    with open("./pages.json", "w", encoding="utf8") as f:
        json.dump(jsonFile, f, ensure_ascii=False, indent=4)


# get a page and update a specific field
# task name is guaranteed to exist
# field is enumerated such that: 
#	{1: Task}, {2: Description}, {3: Date}, {4: Assigned To},
#	{5: Assigned By}, {6: Type}, {7: Completion}

		
def updatePage(taskName, field, data):
	#get page ID
	queryDatabase()
	id = getPageID(taskName)
	url = "https://api.notion.com/v1/pages/{0}".format(id)

	# update file info
	updateData = None
	if field == 1: # update title
		updateData = {
			"properties": {
            	"Task": {
                	"title": [{
                    	"text": {"content": data}
                	}]
				}
			}
		}
	elif field == 2: # update description
		updateData = {
			"properties": {
				"Description": {
                	"rich_text": [{
                    	"type": "text",
                    	"text": {"content": data}
                	}]
            	}
			}
		}
	elif field == 3: # update date
		updateData = {
			"properties": {
				"Date": {
                	"date": {"start": data}
            	}
			}
		}
	elif field == 4: # update assign to tags
		updateData = {
			"properties": {
				"Assigned to": {"multi_select": data}
			}
		}
	elif field == 5: # update assign by tags
		updateData = {
			"properties": {
				"Assigned by": {"multi_select": data}
			}
		}
	elif field == 6: # update type tags
		updateData = {
			"properties": {
				"Type": {"multi_select": data}
			}
		}
	elif field == 7: # update completion checkbox
		updateData = {
			"properties": {
				"Completion": {
					"checkbox": data
				}
			}
		}

	jsonData = json.dumps(updateData)
	response = requests.patch(url, headers=headers, data=jsonData)
	
	# print(response.status_code)
	return response.status_code


# Delete a page given the task name
# task name is guaranteed to exist
def deletePage(taskName):
	queryDatabase()
	id = getPageID(taskName)
	url = "https://api.notion.com/v1/pages/{0}".format(id)
	
	updateData = {"archived": True}

	jsonData = json.dumps(updateData)
	response = requests.patch(url, headers=headers, data=jsonData)
	
	# print(response.status_code)
	return response.status_code

# readDatabase()
# deletePage("test task")
# readDatabase()

# createPage("Test Task", "Some description", "2022-10-03T21:42:51",
#            [{
#                "name": "FSgt Lee"
#            }, {
#                "name": "CI Tsang"
#            }], [{
#                "name": "FSgt Lee"
#            }, {
#                "name": "CI Tsang"
#            }], [{
#                "name": "Ops"
#            }, {
#                "name": "Lesson"
#            }])



