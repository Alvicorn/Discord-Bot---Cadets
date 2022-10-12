# Discord Task Bot

## 1. Overview
This Discord bot is designed to work with a small team in a Discord server to help manage tasks. It takes commands with data with in the command line of Discord and records the information in a Notion database. 

## 2. Working with a Notion Database
Notion is an application that has a shared workspace for scheduling tasks, making events and taking notes. We take advantage of the Notion API and its relational database to help organize tasks. In the current version, the database has the following format: 

|Task| Description | Date | Assigned To | Assigned By | Type | Completion
|----|---|---|---|---|---|---|

## 3. Workflow
```
```

## 4. Bot Commands
All commands are prefixed with ```$``` followed by the command name and parameters in quotations. Within the parameters, each parameter is delimited by double slash ```//```.

<details>
    <summary>Create a new task</summary>

```shell
$newTask "taskName//desc//date//assignTo//assignBy//type"
```

|Parameter Name|Explanation| Data Validation | 
|--------------|-----------|-----------------| 
| ```taskName``` | Name of the task. | Task name must be unique.|
| ```desc``` | Short description of the task. | N/A |
| ```date``` | Due date of the task. | Date is in standard military format (DD MMM YY HHMM). i.e. *01 Jan 22 2100*| 
| ```assignTo``` | Who the task is assigned to. Each name is separated by a coma. | All names must be tags already created in Notion | 
| ```assignBy``` | Who the task is assigned by. Each name is separated by a comma. | All names must be tags already created in Notion |
| ```type``` | Type/category of the task. Each type name is separated by a coma. | All type names must be tags already created in Notion | 

Create a new task and add it to the pending list for approval.

```shell
# Example: New task with all fields filled
>>> $newTask "Task 1//A short description about the task//20 sep 22 1400//FSgt Lee//CI Tsang//Ops"

# Example: New task with no Description
>>> $newTask "Task 1////20 sep 22 1400//FSgt Lee//CI Tsang//Ops"

```
___
</details>

<details>
    <summary>View a task from Notion</summary>

```shell
$getTask "taskName"
```
|Parameter Name|Explanation| Data Validation | 
|--------------|-----------|-----------------| 
| ```taskName``` | Name of the task. | Task name must be exist within the Notion database.|

Retrieve a task from the Notion database and display it for the user.

``` shell
# Example: Get the info in "Task 1"
>>> $getTask "Task 1"
```
___
</details>

<details>
    <summary>Update a task</summary>

``` shell
$updateTask "taskName//field//info"
```
|Parameter Name|Explanation| Data Validation | 
|--------------|-----------|-----------------| 
| ```taskName``` | Name of the task. | Task name must exist within the Notion database. |
| ```field``` | Which header of the task will be edited | Field must define one of the following: "Task", "Description", "Date", "Assigned To", "Assigned By", "Type", "Completion"| 
| ```info``` | The updated data for the field. |

Update a task's information from the Notion database and display the update to the user.

 
``` shell
# Example: Change Assigned By tags
>>> $updateTask "Task 1//Assigned By//CI Tsang"

# Example: Change Type tags
>>> $updateTask "Task 1//Type//Lesson,Admin"

# Example: Change Description to blank
>>> $updateTask "Task 1//Description//"
```
___
</details>
<details>
    <summary>Mark a task as complete</summary>

``` shell
$completeTask "taskName"
```
|Parameter Name|Explanation| Data Validation | 
|--------------|-----------|-----------------| 
| ```taskName``` | Name of the task. | Task name must exist within the Notion database.|

Mark a task as completed

``` shell
# Example: Mark Task 1 as complete
>>> $completeTask "Task 1"
```
___
</details>
<details>
    <summary>Mark a task for deletion</summary>

```shell
$deleteTask "taskName"
```
|Parameter Name|Explanation| Data Validation | 
|--------------|-----------|-----------------| 
| ```taskName``` | Name of the task. | Task name must exist within the Notion database.|

Add the task to delete list if the task exists within the Notion database. If it does not exist, throw an error for the user.
 
``` Shell
# Example: Mark Task 1 for deletion
>>> $deleteTask "Task 1"
```
___
</details>
<details>
    <summary>Delete a task from Notion</summary>

```Shell
$confirmDeleteTask "taskName"
```
|Parameter Name|Explanation| Data Validation | 
|--------------|-----------|-----------------| 
| ```taskName``` | Name of the task. | Task name must have been added to the delete list |

Remove the task with the same ```taskName``` from the delete list if it exists. If it does not exist, throw an error for the user.

``` shell
# Example: Delete Task 1 from Notion
>>> $confirmDeleteTask "Task 1"
```
___
</details>
<details>
    <summary>List all tasks that are marked for deletion</summary>

```Shell 
$listDeleteTasks
```
List out each task that is pending deletion. 


``` shell
# Example
>>> $listDeleteTasks
```
___
</details>
<details>
    <summary>List each Notion header</summary>

```Shell 
$listFields
```
List out each available header from the Notion Database.

``` Shell
# Example
>>> $listFields
```
___
</details>
<details>
    <summary>List all possible tags</summary>

```Shell 
$listTags
```
List out each available tag under the headers **Assigned To**, **Assigned By** and **Type** from the Notion Database.

``` shell
# Example
>>> $listTags
```
___
</details>
<details>
    <summary>List all tasks assigned to a specific person</summary>

```Shell
$listTasks "assignedTo"
```
|Parameter Name|Explanation| Data Validation | 
|--------------|-----------|-----------------| 
| ```assignedTo``` | Who the task is assigned by. Each name is separated by a comma. | All names must be tags already created in Notion. Names should also match the Discord Server nickname(s) |

List all tasks that have a matching ```assignedTo``` tag.

``` Shell
# Example: Display tasks assigned to CI Tsang
>>> $listTasks "CI Tsang"
```
___
</details>
<details>
    <summary>List my tasks</summary>

```Shell
>>> $listMyTasks
```

List all of the tasks assigned to the user who entered this command

``` Shell
# Example: Display tasks assigned to me
>>> $listMyTasks
```
___
</details>
<details>
    <summary>List bot commands</summary>

```Shell
>>> $listCommands
```

List all commands recogized by the bot

``` Shell
# Example: List all bot commands
>>> $listCommands
```
___
</details>






## 5. Dependencies
1.  discord.py
3. Notion Account
3. Notion API

## 6. Limitations
1. When retrieving data from Notion, there is a maximum of 100 pages that can be retrieved.
