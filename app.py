from flask import Flask, request, make_response, Response
import requests
import json
import os
from slackclient import SlackClient

app = Flask(__name__)

# Your app's Slack bot user token
SLACK_BOT_TOKEN = os.environ["SLACK_TOKEN"]

# Slack client for Web API requests
slack_client = SlackClient(SLACK_BOT_TOKEN)


def send_message(channel_id, message, attachments_json=[]):
    slack_client.api_call(
        "chat.postMessage",
        channel=channel_id,
        text=message,
        icon_emoji=':robot_face:',
        attachments=attachments_json
    )


def _event_handler(event_type, slack_event):
    if event_type == "message":

        if slack_event["event"].get("user"):
            r = requests.get("https://slack.com/api/users.list?token=" + SLACK_BOT_TOKEN).json()

            for user in [r["members"][i]["user"] for i in range(0, len(r["members"]))]:
                if user == slack_event["event"].get("user"):

                    attachments = [
                        {
                            "fallback": "Upgrade your Slack client to use messages like these.",
                            "color": "#3AA3E3",
                            "author_name": user["real_name"],
                            "attachment_type": "default",
                            "title": "Report",
                            "text": slack_event["event"]["text"],
                            "ts": 123456789
                        }
                    ]

                    message = 'New report'
                    send_message(channel_id=slack_event["event"]["channel"], message=message, attachments_json=attachments)
                    return make_response("Message Sent", 200, )

    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return make_response(message, 200, {"X-Slack-No-Retry": 1})


@app.route('/slack', methods=['POST'])
def inbound():
    if request.form.get('token') == SLACK_BOT_TOKEN:
        channel = request.form.get('channel_name')
        username = request.form.get('user_name')
        text = request.form.get('text')
        inbound_message = username + " in " + channel + " says: " + text
        print(inbound_message)
    return Response(), 200


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
        # Then handle the event by event_type and have your bot respond
        return _event_handler(event_type, slack_event)
    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})


@app.route('/', methods=['GET'])
def test():
    return Response('It works!')


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


# Send a Slack message on load. This needs to be _before_ the Flask server is started

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
    text="What did you do yesterday? :coffee:",
    attachments=attachments_json
)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, port=port, host='0.0.0.0')

    # app.run()
