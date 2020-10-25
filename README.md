# <img src="./etc/bot.png" height="42" width="42"/> Sync Ends

## End development overheads

Software Engineering Project for CSC 510

[![Support Slack](https://img.shields.io/badge/support-slack-red.svg)](https://join.slack.com/t/seng20/shared_invite/zt-hmikwiec-KDQVndRqN5DvGEFql0ehIw)
[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
![GitHub contributors](https://img.shields.io/github/contributors/varsha5595/csc510-project)
[![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](https://lbesson.mit-license.org/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4042286.svg)](https://doi.org/10.5281/zenodo.4042286)

Sync Ends is an automated bridge to sync service owners and service consumers. Every team has a single postman collection that they use to test their APIs and share it across in their documentations. The backend team has to register their service on our application and we take care of the rest. Everytime there is a change in the way the api is called, we parse the changes and inform the consumers. This way all the team members are informed about the changes and know exactly what to edit in their product. The [Slack](https://slack.com/) framework lets you concentrate on the `core` functionality you want to build without worrying about integration overheads.

[![Watch the video](https://github.com/varsha5595/csc510-project/blob/master/etc/thumbnail.PNG)](https://youtu.be/SeNdRiI1axA)

[![Watch the video](https://github.com/JialinC/csc510-project/blob/master/etc/demo.png)](https://www.youtube.com/watch?v=aam-1JBTSUM)

# Architecture Diagram
<img src="./etc/architecture.PNG" height="500" width="800"/>

## Features
|Feature|Description  |
|--|--|
|API Change Notification  |```Changes made to the API in postman```
|API Changes  |```Automated detailed diff of the changes```|
|Slack Bot Subscription   |```Subscribe to a list of APIs based on your preference``` , ``` Set frequency and method of update``` |
|Configurable Ping |```Choose the ping interval to detect changes in a collection```  |
|Testing  |```Polling service to test API uptime```  |
|API history and change logs  |```Tracking the list of changes all the way from V1```  |
| | |

## Setup

### Postman 
1. Sign in to [Postman](https://identity.getpostman.com/login)
2. If you do not have any pre-exiting collections on Postman, import this sample [collection](https://www.getpostman.com/collections/dfa93d217bf211237c8f)
3. To integrate with the Sync Ends service, a Postman API key is required. Generate API key by visiting this [page](https://web.postman.co/settings/me/api-keys)
4. Copy the generated API key. This is required during the time of execution
5. Add the key to `.env` as `POSTMAN_TOKEN`.

### Create a slack team and slackbot(You can skip this section if you already have a slack bot API token) 

Follow the below steps to create a slack team and then a slack bot. You can skip this step if you already have a team and are the admin.

### Creating Slack team
1. Open https://slack.com/
2. Provide your email ID. Select Create New workspace. 
3. Check your email and enter the code to verify your email.
4. Provide your name and set a password
5. Add some details to your team in the next page
6. Provide a company name
7. Team URL should be unique - Also remember this URL - this is what is used to login to your slack instance
8. Agree with the terms
9. Skip the invite step
10. You are up and running with your own instance of Slack.

Now that team is created, let us create a slack bot

### Creating Slack bot
1. Open your {team-URL}/apps (the one you created above). Ex: https://test-visual.slack.com/apps
2. Search for bot in the search bar and select `bots`
3. In the bots landing page click on Add configuration
4. Provide a bot name. Ex: wolfpack-bot and click on Add Bot integration
5. In the Setup instruction page: `Copy and store the API Token`. Ex: xoxb-22672546-n1X9APk3D0tfksr81NJj6VAM
6. Save the integration

# Execution

In line #133 of src/sync_ends_service.py, replace `<slackbot token>` with your bot token after bot creation: [Creating Slack Bot](https://github.com/varsha5595/csc510-project/wiki)

```
cd src
python3 sync_ends_service.py
```
## Authors

* Rahul Yedida
* Shuzheng Wang
* Jialin Cui
* Adithya Raghu Ganesh
* Meghana Ravindra Vasist
* Shivaprakash Balasubramanian
* Surbhi Jha
* Varsha Anantha Ramu Sharma

## License

This project is licensed under the MIT License.

# Known issue
While the PyPI package is called slackclient, you import the module using the name slack:
```
from slack import WebClient
```
You may find this not work on your first try, before you change moudle name or try to get the old version of slackclient, simply uninstall slackclient then install it again may give you a easy fix.

The current app 'bots' we are using does not have the right to create a channel, so I crate my own app and give it the right to create channel. The link is here https://api.slack.com/apps After go to this page just click Create New App, give it whatever name you want and a workplace you want to add it. Then I selected Permission to add the permission we need. Simply give this link  https://slack.com/oauth/v2/authorize as the Redirect URLs. After this in the Bots Token Scope section choose add an OAuth scope.
Based on the api we are using:
conversations.list needs: channels:read  groups:read  im:read mpim:read
conversations.create needs: channels:manage  groups:write  im:write  mpim:write
chat.postMessage needs: chat:write
We can add more along the way when we need new scope.
After add all these permissions, just choose install app, and you will get a token that can be used.