from flask import Flask, request, make_response, Response
import requests
import json
import os
from slackclient import SlackClient
import time

app = Flask(__name__)

# Your app's Slack bot user token
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")

# Slack client for Web API requests
slack_client = SlackClient(SLACK_BOT_TOKEN)

# List of commands for bot
commands = ['/q']

questions = ["What did you do yesterday? :coffee:",
             "What are you planning do today?"]

global question_counter
question_counter = 0

global answers
answers = []


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


def _command_handler(slack_event, subtype=None):
    global question_counter

    if subtype != 'bot_message' and slack_event["event"].get("user"):
        if commands[0] in slack_event["event"].get("text"):
            print(commands[0], slack_event["event"].get("text"))
            message = 'command q'
            send_message(channel_id=slack_event["event"]["channel"], message=message,
                         attachments_json=[])
            _answer_menu(questions[0])
            question_counter = 0
            return True
        else:
            return False


def _take_answer(slack_event):
    conversations_history = requests.get(
        "https://slack.com/api/conversations.history?token=" + SLACK_BOT_TOKEN
        + "&channel=" + slack_event["event"]["channel"]
        + "&latest=" + str(time.time())
        + "&limit=2&inclusive=true").json()

    answer = conversations_history['messages'][0]['text']
    question = conversations_history['messages'][1]['text']
    print('Вопрос: ', question)
    print('Ответ: ', answer)
    return answer, question


def _send_report(slack_event, real_name_user, questions, answers):
    attachments = [
        {
            "fallback": "Upgrade your Slack client to use messages like these.",
            "color": "#3AA3E3",
            "author_name": real_name_user,
            "attachment_type": "default",
            "title": "Report",
            "text": str("*" + questions[0] + "* \n" + answers[0] + "\n*" + questions[1] + "* \n" + answers[1]),
            "ts": time.time()
        }
    ]
    send_message(channel_id=slack_event["event"]["channel"], message='New report',
                 attachments_json=attachments)


def _event_handler(event_type, slack_event, subtype=None):
    global question_counter

    print('\nevent_type: ', event_type)

    # TODO заготовка?
    if event_type == "message" and subtype == 'message_changed':
        if slack_event["event"].get('previous_message').get("text") in questions:
            # TODO если юзер выбрал короткий ответ, то больше не спрашивать его
            print('user selects short answer: ', slack_event["event"].get("message").get("text"))

    if event_type == "message" and subtype != 'bot_message':
        print('dict in event: \n', slack_event["event"])

        is_command = _command_handler(slack_event, subtype=None)
        if is_command:
            return make_response("Message Sent", 200, )

        else:
            if slack_event["event"].get("user"):
                users_list = requests.get("https://slack.com/api/users.list?token=" + SLACK_BOT_TOKEN).json()

                for member in users_list['members']:
                    if member.get("id") == slack_event["event"].get("user"):
                        real_name_user = member.get("profile").get("display_name")
                        user_id = member.get('id')
                        print('real_name :', real_name_user, 'user_id :', user_id)

                        # TODO предыдущее вопрос?
                        current_message, previous_message = _take_answer(slack_event)
                        if previous_message in questions:
                            answer = current_message
                        else:
                            answer = None
                            send_message(channel_id=slack_event["event"]["channel"], message="echo: " + current_message,
                                         attachments_json=[])
                            break

                        if answer:
                            answers.append(answer)
                            question_counter += 1

                        try:
                            _answer_menu(question=questions[question_counter])
                        except:
                            _send_report(slack_event, real_name_user, questions, answers)
                            question_counter = 0

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
