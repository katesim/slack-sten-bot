from flask import Flask, request, make_response, Response
import requests
import json
import os
from slackclient import SlackClient

app = Flask(__name__)

# Your app's Slack bot user token
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")

# Slack client for Web API requests
slack_client = SlackClient(SLACK_BOT_TOKEN)

# List of commands for bot
commands = ['/q']


@app.route('/', methods=['GET'])
def webhook():
    return Response('It works!')


@app.route('/slack/events', methods=['POST'])
def events():
    """
    This route listens for incoming events from Slack and uses the event
    handler helper function to route events to our Bot.
    """
    slack_event = request.get_json()

    # ============= Slack URL Verification ============ #
    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                                 "application/json"
                                                             })

    # ====== Process Incoming Events from Slack ======= #
    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        event_subtype = slack_event["event"].get("subtype")
        # Then handle the event by event_type and have your bot respond
        return _event_handler(event_type, slack_event, subtype=event_subtype)
    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})


'''

___BLOCK FOR INTERACTIVE MENU___

'''

# The endpoint Slack will load your menu options from
@app.route("/slack/message_options", methods=["POST"])
def message_options():
    # Parse the request payload
    form_json = json.loads(request.form["payload"])

    # Dictionary of menu options which will be sent as JSON
    menu_options = {
        "options": [
            {
                "text": "Same as yesterday",
                "value": "same_as_yesterday"
            },
            {
                "text": "I'm busy right now",
                "value": "busy"
            },
            {
                "text": "I'm on vacation",
                "value": "vacation"
            }
        ]
    }
    # Load options dict as JSON and respond to Slack
    return Response(json.dumps(menu_options), mimetype='application/json')


# The endpoint Slack will send the user's menu selection to
@app.route("/slack/message_actions", methods=["POST"])
def message_actions():
    # Parse the request payload
    form_json = json.loads(request.form["payload"])

    # Check to see what the user's selection was and update the message accordingly
    selection = form_json["actions"][0]["selected_options"][0]["value"]

    if selection == "same_as_yesterday":
        message_text = "Same as yesterday"
    elif selection == "busy":
        message_text = "I'm busy right now"
    else:
        message_text = "I'm on vacation"

    response = slack_client.api_call(
        "chat.update",
        channel=form_json["channel"]["id"],
        ts=form_json["message_ts"],
        text="Your answer is {}  :coffee:".format(message_text),
        attachments=[]  # empty `attachments` to clear the existing massage attachments
    )

    # Send an HTTP 200 response with empty body so Slack knows we're done here
    return make_response("", 200)


'''

___BLOCK FOR INNER FUNCS___

'''


def send_message(channel_id, message, attachments_json=[]):
    slack_client.api_call(
        "chat.postMessage",
        channel=channel_id,
        text=message,
        icon_emoji=':robot_face:',
        attachments=attachments_json
    )


def _event_handler(event_type, slack_event, subtype=None):
    print('\nevent_type: ', event_type)

    if event_type == "message":
        print('dict in event: \n', slack_event["event"])
        if subtype != 'bot_message' and slack_event["event"].get("user"):
            print(commands[0], slack_event["event"].get("text"))
            if commands[0] in slack_event["event"].get("text"):
                message = 'command q'
                send_message(channel_id=slack_event["event"]["channel"], message=message,
                             attachments_json=[])
                _answer_menu()
                return make_response("Message Sent", 200, )

            elif slack_event["event"].get("user"):
                r = requests.get("https://slack.com/api/users.list?token=" + SLACK_BOT_TOKEN).json()

                for user in [r["members"][i]["id"] for i in range(0, len(r["members"]))]:
                    if user == slack_event["event"].get("user"):
                        print(user)
                        attachments = [
                            {
                                "fallback": "Upgrade your Slack client to use messages like these.",
                                "color": "#3AA3E3",
                                "author_name": "kek",
                                "attachment_type": "default",
                                "title": "Report",
                                "text": slack_event["event"]["text"],
                                "ts": 123456789
                            }
                        ]

                        message = 'New report'
                        send_message(channel_id=slack_event["event"]["channel"], message=message,
                                     attachments_json=attachments)
                        return make_response("Message Sent", 200, )

    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return make_response(message, 200, {"X-Slack-No-Retry": 1})


def _answer_menu(question="What did you do yesterday? :coffee:"):
    # A Dictionary of message attachment options
    attachments_json = [
        {
            "fallback": "Upgrade your Slack client to use messages like these.",
            "color": "#3AA3E3",
            "attachment_type": "default",
            "callback_id": "menu_options_2319",
            "actions": [
                {
                    "name": "bev_list",
                    "text": "Pick a beverage...",
                    "type": "select",
                    "data_source": "external"
                }
            ]
        }
    ]

    # Send a message with the above attachment, asking the user if they want coffee
    slack_client.api_call(
        "chat.postMessage",
        channel="DHCLCG8DQ",
        text=question,
        attachments=attachments_json
    )


def _first_message():
    slack_client.api_call(
        "chat.postMessage",
        channel="DHCLCG8DQ",
        text=str('Hello! :hand: '
                 '\nAvailable commands:'
                 '\n *' + commands[0] + '* - _send questions_'),
        attachments=[]
    )


_first_message()
_answer_menu()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, port=port, host='0.0.0.0')
