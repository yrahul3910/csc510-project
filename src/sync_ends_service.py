# Standard library imports
import http.client
import json
import os
import re
import time
import ssl

from dotenv import load_dotenv

# Third party imports
from jsondiff import diff
from slack import WebClient
from slackeventsapi import SlackEventAdapter

ssl._create_default_https_context = ssl._create_unverified_context
load_dotenv()


def get_postman_collections(connection, api_key):
    """
    Input: Postman connection object, Postman API key of the user
    Description: To fetch all the collections present in the user's Postman account
    Returns all the collections in the user's Postman account
    """
    boundary = ''
    payload = ''
    headers = {
        'X-Api-Key': api_key,
        'Content-type': 'multipart/form-data; boundary={}'.format(boundary)
    }
    connection.request("GET", "/collections", payload, headers)
    response = connection.getresponse()
    if response.status == 200:
        return response
    else:
        raise Exception("Exited with status code " + str(response.status) +
                        '. ' + str(json.loads(response.read())['error']['message']))


def regex(value):
    """
    From the detected changes object, we check if there have been any change to the keys and values.
    We then check if there are any new deletions or insertions using regular expressions on the parsed object.
    """
    change_detection_regex = ["(?<='key': )[^,||}]*", "(?<='value': )[^,||}]*",
                              "(?<=delete: \[)[^]]+", "(?<=insert: \[)[^]]+"]
    return [re.findall(regex, value) for regex in change_detection_regex]


def get_selected_collection(collection_id, connection, api_key):
    """
    Input: Postman connection object, UUID of the collection chosen by the user, Postman API key of the user
    Description: To fetch details about all the APIs present in a specfic collection and to detect changes if any
    Returns the changes detected in the API schema
    """
    boundary = ''
    payload = ''
    headers = {
        'X-Api-Key': api_key,
        'Content-type': 'multipart/form-data; boundary={}'.format(boundary)
    }
    connection.request("GET", "/collections/" +
                       collection_id, payload, headers)
    response = connection.getresponse()
    if response.status == 200:
        data = json.loads(response.read())

        # For each collection, a separate text file is created to store the details related to the collection
        filepath = "./data/" + collection_id + ".txt"
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        if not os.path.exists(filepath):
            with open(filepath, "w") as f:
                f.write("{}")
                f.close()

        # Difference between the data received as part of the current API call and the data that previously existed in the .txt file
        # The difference is computed twice to detect changes w.r.t to addition as well as deletion of key value pairs
        with open(filepath, "r+") as f:
            old_value = diff(data, json.load(f))
            f.close()

        with open(filepath, "r+") as f:
            new_value = diff(json.load(f), data)
            f.close()

        # A list of changes in the existing API are determined
        changes_detected = [regex(str(value))
                            for value in [old_value, new_value]]

        # When changes are detected, the .txt file is updated according to the new API schema
        if changes_detected:
            with open(filepath, "w+") as f:
                json.dump(data, f)
                f.close()

        # Formatting the changes detected to make it user-friendly
        keys_old = "Old name of the query paramter: " + \
            ' '.join(changes_detected[0][0])
        keys_new = "Updated name of the query parameter: " + \
            ' '.join(changes_detected[1][0])
        keys_inserted = "Name of the query parameter newly added: " + \
            ' '.join(changes_detected[1][3])
        keys_deleted = "Name of the query paramter that is deleted " + \
            ' '.join(changes_detected[0][2])

        return keys_old + "\n" + keys_new + "\n" + keys_inserted + "\n" + keys_deleted
    else:
        raise Exception("Exited with status code " + str(response.status) +
                        '. ' + str(json.loads(response.read())['error']['message']))


def main():
    try:
        postman_connection = http.client.HTTPSConnection("api.getpostman.com")

        print("\nWelcome to Sync Ends! End your development overheads today!")
        print("-----------------------------------------------------------")

        # The Postman API key is required to access all the postman collections in a user's account
        api_key = os.getenv('POSTMAN_TOKEN')
        # To get the collections present in a user's Postman account
        collections_response = get_postman_collections(
            postman_connection, api_key)
        all_collections = json.loads(collections_response.read())

        while True:
            print("\nChoose a collection you would like to integrate:")
            # A list of all the postman collection name to be used latter
            collection_list = []
            # User selects a specfic collection to be linked to the sync ends service
            for index, collection in enumerate(all_collections['collections'], 1):
                print(str(index) + '. ' + str(collection['name']))
                collection_list.append(str(collection['name']))
            collection_choice = input("\nEnter your choice: ")

            if 1 <= int(collection_choice) <= len(all_collections['collections']):
                break

        selected_collection = all_collections['collections'][int(
            collection_choice) - 1]

        collection_name = str(
            all_collections['collections'][int(collection_choice) - 1]['name'])

        while True:
            # Get the changes that need to be sent to slack
            changes_detected = get_selected_collection(
                selected_collection['uid'], postman_connection, api_key)

            # Create a slack client to use slack API
            slack_web_client = WebClient(token=os.getenv('SLACK_BOT_TOKEN'))


            # Create a slack event adapter to responds to slack event API
            slack_events_adapter = SlackEventAdapter(signing_secret=os.getenv('SLACK_SIGNING_SECRET'), endpoint="/slack/events")
            backup_channel_list = slack_web_client.conversations_list(types="public_channel")
            name_id = []
            for channel in range(len(backup_channel_list.data['channels'])):
                name_id.append((backup_channel_list.data['channels'][channel]['name'], backup_channel_list.data['channels'][channel]['id']))
            # responder to user's greeting messages
            @slack_events_adapter.on("message")
            def handle_message(event_data):
                message = event_data["event"]
                # If the incoming message contains "hi" and "sync ends service", 
                # then respond with a "Hello" message and give user choices aboutcollections
                if message.get("subtype") is None and "hi" in message.get('text') and "sync ends service" in message.get('text'):
                    channel = message["channel"]
                    message = "Hello <@%s>! :tada:" % message["user"]
                    slack_web_client.chat_postMessage(channel=channel, text=message)
            
            # responder to channel_rename event
            @slack_events_adapter.on("channel_created")
            def handle_channel_created(event_data):
                message = event_data["event"]
                new_name = message["channel"]["name"]
                channel_id = message["channel"]["id"]
                name_id.append((new_name,channel_id))
            
            # responder to channel_rename event
            @slack_events_adapter.on("channel_rename")
            def handle_channel_rename(event_data):
                message = event_data["event"]
                new_name = message["channel"]["name"]
                channel_id = message["channel"]["id"]
                for channel in range(len(backup_channel_list.data['channels'])):
                    if channel_id == backup_channel_list.data['channels'][channel]['id']:
                        old_name = backup_channel_list.data['channels'][channel]['name']
                    if "general" == backup_channel_list.data['channels'][channel]['name']:
                        general_id = backup_channel_list.data['channels'][channel]['id']
                text = "New channel name: %s detected, the old name is %s if this is a postman collection channel we do not suggest you to change the channel name" % (new_name, old_name)
                slack_web_client.chat_postMessage(channel=general_id, text=text)
            
            # responder to app_uninstalled
            @slack_events_adapter.on("app_uninstalled")
            def handle_app_uninstalled(event_data):
                #app is uninstalled, exits.
                exit(0)

            # responder to user's request on collection information
            @slack_events_adapter.on("app_mention")
            def handle_app_mention(event_data):
                # slack event, dictionary obj
                message = event_data["event"]
                # get the channel that the bot is @ in
                current_channel = message["channel"]
                # the text user send
                text = message.get("text")
                # if key word in text then we consider to send info about a certein colletion
                if "show" in text:
                    for name in collection_list:
                        if name in text:
                            # Check if this channel already existed, if not create a new one
                            # Therefore, we have a channel in Slack for every collection
                            # created in Postman.
                            channel_list = slack_web_client.conversations_list(
                                types="public_channel")
                            existed = False
                            for channel in range(len(channel_list.data['channels'])):
                                if name.lower().replace(" ", "_") == channel_list.data['channels'][channel]['name']:
                                    existed = True

                            dic = '{\'name\':\'' + \
                                name.lower().replace(" ", "_")+'\'}'
                            dic = eval(dic)

                            if not existed:
                                response = slack_web_client.api_call(
                                    api_method='conversations.create',
                                    json=dic
                                )

                            # Slack Channel to post the message
                            channel = name.lower().replace(" ", "_")

                            # Get the onboarding message payload
                            message = {
                                "channel": channel,
                                "blocks": [{
                                    "type": "section",
                                    "text": {
                                        "type": "plain_text",
                                        "text": changes_detected
                                    }
                                }],
                            }

                            # Post the onboarding message in Slack
                            slack_web_client.chat_postMessage(**message)
                            message["channel"] = current_channel
                            slack_web_client.chat_postMessage(**message)

            # Error events
            @slack_events_adapter.on("error")
            def error_handler(err):
                print("ERROR: " + str(err))

            # Check if this channel already existed, if not create a new one
            channel_list = slack_web_client.conversations_list(
                types="public_channel")
            existed = False
            for channel in range(len(channel_list.data['channels'])):
                if collection_name.lower().replace(" ", "_") == channel_list.data['channels'][channel]['name']:
                    existed = True

            dic = '{\'name\':\''+collection_name.lower().replace(" ", "_")+'\'}'
            dic = eval(dic)
            print(existed)
            if not existed:
                response = slack_web_client.api_call(
                    api_method='conversations.create',
                    json=dic
                )

            # Slack Channel to post the message
            channel = collection_name.lower().replace(" ", "_")

            # Get the onboarding message payload
            message = {
                "channel": channel,
                "blocks": [
                    {"type": "section", "text": {
                        "type": "plain_text", "text": changes_detected}}
                ],
            }

            # Post the onboarding message in Slack
            slack_web_client.chat_postMessage(**message)
            # Start the server to listen to event
            slack_events_adapter.start(port=3000)
            time.sleep(3600)
    except Exception as e:
        print(e)


if __name__ == '__main__':
    main()
