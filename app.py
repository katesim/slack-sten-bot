from flask import Flask, request, make_response, Response
import requests
import json
import os
from slackclient import SlackClient
import time
from pprint import pprint

from WorksReportController import WorksReportController

app = Flask(__name__)

# Your app's Slack bot user token
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")

# Slack client for Web API requests
slack_client = SlackClient(SLACK_BOT_TOKEN)

# List of commands for bot
commands = ['/q', '/init']

questions = ["What did you do yesterday? :coffee:",
             "What are you planning do today?"]

BOT_USER = {}
_channel = "DHCLCG8DQ"

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
    # Dictionary of menu options which will be sent as JSON
    menu_options = works_report_controller.take_menu_options()

    # Load options dict as JSON and respond to Slack
    return Response(json.dumps(menu_options), mimetype='application/json')


# The endpoint Slack will send the user's menu selection to
@app.route("/slack/message_actions", methods=["POST"])
def message_actions():
    # Parse the request payload
    form_json = json.loads(request.form["payload"])
    print('\n\n\n\n', form_json["type"], '\n\n\n\n')
    pprint(form_json)
    if form_json["type"] == "interactive_message":
        if form_json['actions'][0]['name'] == str("short_answer_list"):

            # Check to see what the user's selection was and update the message accordingly
            selection = form_json["actions"][0]["selected_options"][0]["value"]
            short_answer = works_report_controller.take_short_answer(selection)

            response = slack_client.api_call(
                "chat.update",
                channel=form_json["channel"]["id"],
                ts=form_json["message_ts"],
                text="Your answer is {}  :coffee:".format(short_answer),
                attachments=[]  # empty `attachments` to clear the existing massage attachments
            )

            # Send an HTTP 200 response with empty body so Slack knows we're done here
            return make_response("", 200)

        if form_json['actions'][0]['name'] == "init_standup":
            open_dialog = slack_client.api_call(
                "dialog.open",
                trigger_id=form_json["trigger_id"],
                dialog={
                    "title": "Init new standUP",
                    "submit_label": "Submit",
                    "callback_id": form_json["channel"]["id"] + "coffee_order_form",
                    "elements": [
                        {
                            "label": "Coffee Type",
                            "type": "select",
                            "name": "meal_preferences",
                            "placeholder": "Select a time",
                            "options": [
                                {
                                    "label": "10.30",
                                    "value": "10.30"
                                },
                                {
                                    "label": "11.00",
                                    "value": "11.00"
                                }
                            ]
                        },
                        {
                            "label": "Post this message on",
                            "name": "channel_notify",
                            "type": "select",
                            "placeholder": "Select a channel",
                            "data_source": "conversations"
                        }
                    ]
                }
            )

            print(open_dialog)

            # Update the message to show that we're in the process of taking their order
            slack_client.api_call(
                "chat.update",
                channel=_channel,
                ts=form_json["message_ts"],
                text=":pencil: Noted your answers",
                attachments=[]
            )

            send_message(_channel, 'Whom to invite?')

            return make_response("", 200)

    elif form_json["type"] == "dialog_submission":

        pprint(form_json['response_url'])
        # coffee_order = BOT_USER[_channel]
        # # Update the message to show that we're in the process of taking their order
        # slack_client.api_call(
        #     "chat.update",
        #     channel=_channel,
        #     ts=coffee_order["message_ts"],
        #     text=":white_check_mark: Order received!",
        #     attachments=[]
        # )

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
    global works_report_controller

    if subtype != 'bot_message' and slack_event["event"].get("user"):
        if commands[0] in slack_event["event"].get("text"):
            print(commands[0], slack_event["event"].get("text"))
            send_message(channel_id=slack_event["event"]["channel"],
                         message='command q',
                         attachments_json=[])

            works_report_controller = WorksReportController()
            attachments = works_report_controller.answer_menu(works_report_controller.questions[0])
            send_message(channel_id=slack_event["event"]["channel"], message=attachments[0],
                         attachments_json=attachments[1])
            return True

        if commands[1] in slack_event["event"].get("text"):
            print(commands[1], slack_event["event"].get("text"))
            print('INPUT')
            print(slack_event["event"])
            _init_menu()
            print('OPEN')
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


def _send_report_init(slack_event, list_users, list_days):
    attachments = [
        {
            "fallback": "Upgrade your Slack client to use messages like these.",
            "color": "#3AA3E3",
            "attachment_type": "default",
            "title": "Report_init",
            "text": str("* list_users: " + str(list_users) + "* \n list_days: " + str(list_days) + "\n*"),
            "ts": time.time()
        }
    ]
    send_message(channel_id=slack_event["event"]["channel"], message='New report',
                 attachments_json=attachments)

def _event_handler(event_type, slack_event, subtype=None):
    global question_counter
    global inviter_list
    global days_list
    days_list = []
    inviter_list = []

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
                            attachments = works_report_controller.remember_answer(answer=current_message,
                                                                                  real_name_user=real_name_user)
                            send_message(channel_id=slack_event["event"]["channel"],
                                         message=attachments[0],
                                         attachments_json=attachments[1])

                        elif previous_message == 'Whom to invite?':
                            inviter_list = current_message
                            send_message(_channel, str(inviter_list))
                            send_message(_channel, 'Days?')

                        elif previous_message == 'Days?':
                            print('EEEEEEEEEEEE')
                            days_list = current_message
                            #     send_message(_channel, str(days_list))
                            #     send_message(_channel, 'Days?')
                            _send_report_init(slack_event, inviter_list, days_list)

                        else:
                            answer = None
                            # send_message(channel_id=slack_event["event"]["channel"], message="echo: " + current_message,
                            #              attachments_json=[])
                            return make_response("Message Sent", 200, )

                        return make_response("Message Sent", 200, )

    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return make_response(message, 200, {"X-Slack-No-Retry": 1})


def _init_menu(question="Init new standUP"):
    # A Dictionary of message attachment options
    attachments_json = [{
        "callback_id": _channel + "init_form",
        "text": "",
        "color": "#3AA3E3",
        "attachment_type": "default",
        "actions": [{
            "name": "init_standup",
            "text": ":coffee: Init new StandUP",
            "type": "button",
            "value": "init_standup"
        }]
    }]

    # Send a message with the above attachment, asking the user if they want coffee
    slack_client.api_call(
        "chat.postMessage",
        channel=_channel,
        text=question,
        attachments=attachments_json
    )


def _first_message():
    user_dm = slack_client.api_call(
        "chat.postMessage",
        channel=_channel,
        text=str('Hello! :hand: '
                 '\nAvailable commands:'
                 '\n *' + commands[0] + '* - _send questions_'
                                        '\n *' + commands[1] + '* - _init new task_'),
        attachments=[]
    )
    return user_dm


user_dm = _first_message()
BOT_USER[_channel] = {
    "order_channel": "DHCLCG8DQ",
    "message_ts": "",
    "order": {}
}
_init_menu()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, port=port, host='0.0.0.0')
