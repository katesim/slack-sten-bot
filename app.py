from flask import Flask, request, make_response, Response
import requests
import json
import os
from slackclient import SlackClient
import time
from pprint import pprint

from WorksReportController import WorksReportController
from InitController import InitController

init_controller = InitController()

app = Flask(__name__)

# Your app's Slack bot user token
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")

# Slack client for Web API requests
slack_client = SlackClient(SLACK_BOT_TOKEN)

# List of commands for bot
commands = ['/q', '/init']

BOT_USER = {}
_channel = "DHCLCG8DQ"


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
    print('\n\n\nPAYLOAD:\n', form_json["type"], '\n\n\n\n')
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
                dialog=init_controller.create_dialog(form_json["channel"]["id"])
            )

            print('\nopen_dialog: ', open_dialog)

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
        print("FORM response_url", form_json['response_url'])
        return make_response("", 200)


'''

___BLOCK FOR INNER FUNCS___

'''


def _command_handler(slack_event, subtype=None):
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

            send_message(channel_id=_channel,
                         message='Init new standUP',
                         attachments_json=init_controller.init_menu(channel=_channel))

            print('OPEN')
            return True

        else:
            return False


def _event_handler(event_type, slack_event, subtype=None):
    global inviter_list
    global days_list
    global works_report_controller
    days_list = []
    inviter_list = []

    print('\nevent_type: ', event_type)

    # TODO заготовка?
    if event_type == "message" and subtype == 'message_changed':
        if slack_event["event"].get('previous_message').get("text") in WorksReportController().questions:
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
                        if previous_message in WorksReportController().questions:
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
                            send_message(channel_id=_channel,
                                         message='Init',
                                         attachments_json=init_controller.create_report_init(inviter_list, days_list))
                        return make_response("Message Sent", 200, )

    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return make_response(message, 200, {"X-Slack-No-Retry": 1})


def send_message(channel_id, message, attachments_json=[]):
    slack_client.api_call(
        "chat.postMessage",
        channel=channel_id,
        text=message,
        icon_emoji=':robot_face:',
        attachments=attachments_json
    )


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


def _first_message():
    return slack_client.api_call(
        "chat.postMessage",
        channel=_channel,
        text=str('Hello! :hand: '
                 '\nAvailable commands:'
                 '\n *' + commands[0] + '* - _send questions_'
                                        '\n *' + commands[1] + '* - _init new task_'),
        attachments=[]
    )


user_dm = _first_message()
BOT_USER[_channel] = {
    "order_channel": "DHCLCG8DQ",
    "message_ts": "",
    "order": {}
}

send_message(channel_id=_channel,
             message='Init new standUP',
             attachments_json=init_controller.init_menu(channel=_channel))

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, port=port, host='0.0.0.0')
