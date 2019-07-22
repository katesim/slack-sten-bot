from flask import Flask, request, make_response, Response
import requests
import json
import os
from slackclient import SlackClient
from slackeventsapi import SlackEventAdapter
import schedule
import time
from pprint import pprint

from WorksReportController import WorksReportController
from InitController import InitController

init_controller = InitController()

app = Flask(__name__)

# Your app's Slack bot user token
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SIGNING_SECRET = os.environ.get("SIGNING_SECRET")
# hotfix variable to catch bot mentioning
BOT_MENTIONED = os.environ.get("BOT_MENTIONED")
# Slack client for Web API requests
slack_client = SlackClient(SLACK_BOT_TOKEN)
# Slack event adapter API to process events
slack_events_adapter = SlackEventAdapter(SIGNING_SECRET, "/slack/events", app)

# List of commands for bot
commands = ['/q', '/init', '/schedule']

global inviter_list
global days_list
global works_report_controller

days_list = []
inviter_list = []
works_report_controller = WorksReportController()


@app.route('/', methods=['GET'])
def webhook():
    return Response('It works!')


# The endpoint Slack will load your menu options from
@app.route("/slack/message_options", methods=["POST"])
def message_options():
    global works_report_controller
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

    channel = form_json["channel"]["id"]
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
                channel=channel,
                ts=form_json["message_ts"],
                text=":pencil: Note your answers"
            )

            # send_message(_channel, 'Whom to invite?')
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text="Whom to invite?"
            )
            return make_response("", 200)

    elif form_json["type"] == "dialog_submission":
        print("FORM response_url", form_json['response_url'])
        submission = form_json.get("submission")
        time, group_channel = get_menu_answers(submission)
        return make_response("", 200)
    
def get_menu_answers(submission):
    time = None
    group_channel = None
    if submission:
        time = submission.get("meal_preferences")
        group_channel = submission.get("channel_notify")
    print("TIME:", time, "CHANNEL:", group_channel)
    return time, group_channel
                
def form_reminder(group_channel):
    # TODO some methods from DBController to get info from database
    # group_info = get_group_info(group_channel)
    # group_members_channels = group_info.get("members_channels")
    # time = group_info.get("time")
    
    # сейчас хардкод =================
    group_members_channels = ["DL9QABUBT"]
    reminder_message = "There's one hour left until the end of the StandUp."
    time = "16:40"
    day = 1
    # ================================

    if group_members_channels:
        for member_channel in group_members_channels:
            send_reminder_message(time=time, 
                                  day=day, 
                                  channel=member_channel, 
                                  text=reminder_message)
            # slack_client.api_call("chat.scheduleMessage",
            #                         channel=member,
            #                         post_at=
            #                         text=
            #                         )

def send_reminder_message(time, day, channel, text):
    # TODO change parser
    if day == 1:
        schedule.every().monday.at(time).do(slack_client.api_call("chat.postMessage",
                                                                       channel=channel,
                                                                       text=text))
    elif day == 2:
        schedule.every().tuesday.at(time).do(slack_client.api_call("chat.postMessage",
                                                                       channel=channel,
                                                                       text=text))
    elif day == 3:
        schedule.every().wednesday.at(time).do(slack_client.api_call("chat.postMessage",
                                                                       channel=channel,
                                                                       text=text))
    elif day == 4:
        schedule.every().thursday.at(time).do(slack_client.api_call("chat.postMessage",
                                                                       channel=channel,
                                                                       text=text))
    elif day == 5:
        schedule.every().friday.at(time).do(slack_client.api_call("chat.postMessage",
                                                                       channel=channel,
                                                                       text=text))
    elif day == 6:
        schedule.every().saturday.at(time).do(slack_client.api_call("chat.postMessage",
                                                                       channel=channel,
                                                                       text=text))
    elif day == 7:
        schedule.every().sunday.at(time).do(slack_client.api_call("chat.postMessage",
                                                                       channel=channel,
                                                                       text=text))
 
# parse day number and start scheduler with job
def day_manager(time, day, job):
    pass

def _command_handler(channel, user, message):
    global works_report_controller

    if commands[0] in message:
        print(commands[0], message)
        slack_client.api_call("chat.postMessage",
                              channel=channel,
                              text="command q")

        # works_report_controller = WorksReportController()
        attachments = works_report_controller.answer_menu(works_report_controller.questions[0])
        slack_client.api_call("chat.postMessage",
                              channel=channel,
                              text=attachments[0],
                              attachments=attachments[1])
        return True

    if commands[1] in message:
        print(commands[1], message)
        print('INPUT')

        slack_client.api_call("chat.postMessage",
                              channel=channel,
                              text="Init new standUP",
                              attachments=init_controller.init_menu(channel=channel))
        print('OPEN')
        return True

    if commands[2] in message:
        print(commands[2], message)
        print('SCHEDULE TEST')

        form_reminder(None)
        return True

    else:
        return False


def _message_handler(message_event):
    global inviter_list
    global days_list
    global works_report_controller

    subtype = message_event.get("subtype")
    channel = message_event.get("channel")
    message = message_event.get("text")
    user = message_event.get("user")
    message_before_change = None
    if message_event.get("previous_message"):
        message_before_change = message_event.get("previous_message").get("text")

    if subtype == 'message_changed':
        if message_before_change in WorksReportController().questions:
            print('USER SELECTED SHORT ANSWER: ', message)

    if user:
        real_user_name = get_real_user_name(user)
        
        # предыдущее вопрос?
        current_message, previous_message = _take_answer(message_event)
        print('current_message, previous_message', current_message, previous_message)
        if previous_message in WorksReportController().questions:
            attachments = works_report_controller.remember_answer(answer=current_message,
                                                                  question=previous_message,
                                                                  real_user_name=real_user_name)
            slack_client.api_call("chat.postMessage",
                                  channel=channel,
                                  text=attachments[0],
                                  attachments=attachments[1])
        # TODO продумать нормальный init бота
        elif previous_message == 'Whom to invite?':
            inviter_list.append(current_message)
            slack_client.api_call("chat.postMessage",
                                  channel=channel,
                                  text=str(inviter_list))
            slack_client.api_call("chat.postMessage",
                                  channel=channel,
                                  text='Days?')

        elif previous_message == 'Days?':
            days_list.append(current_message)
            slack_client.api_call("chat.postMessage",
                                  channel=channel,
                                  text='Init',
                                  attachments=init_controller.create_report_init(inviter_list, days_list))
            inviter_list = []
            days_list = []
    return make_response("Message Sent", 200, )

    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    # message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    #return make_response(message, 200, {"X-Slack-No-Retry": 1})

def get_real_user_name(user_id):
    user_info = slack_client.api_call("users.info", user=user_id)
    real_user_name = "user"
    if user_info.get("ok"):
        real_user_name = user_info.get("user").get("real_name")
        print('REAL NAME :', real_user_name, 'USER ID :', user_id)
    return real_user_name

def _take_answer(slack_event):
    channel = slack_event["channel"]
    answer = None
    question = None
    conversations_history = slack_client.api_call("conversations.history",
                                                    channel=channel,
                                                    latest=str(time.time()),
                                                    limit=2,
                                                    inclusive=True)
    
    if conversations_history.get("ok"):
        answer = conversations_history['messages'][0]['text']
        question = conversations_history['messages'][1]['text']
        print('Вопрос: ', question)
        print('Ответ: ', answer)
    return answer, question


def _first_message(channel):
    return slack_client.api_call("chat.postMessage",
                                 channel=channel,
                                 text=str('Hello! :hand: '
                                          '\nAvailable commands:'
                                          '\n *' + commands[0] + '* - _send questions_'
                                          '\n *' + commands[1] + '* - _init new task_'))


# bot mentioning in channel
@slack_events_adapter.on('app_mention')
def app_mention(event):
    print("APP MENTIONED\n", event)
    print("\n")
    channel = event["event"]["channel"]
    _first_message(channel)
    # slack_client.api_call("chat.postMessage",
    #             channel = channel,
    #             text="Привет, я StenBot!\n" +\
    #                  "Напиши мне, чтобы создать опрос\n")


# process direct bot message
@slack_events_adapter.on('message')
def message(event):
    print("MESSAGE")
    message_event = event["event"]
    channel_type = message_event.get("channel_type")
    subtype = message_event.get("subtype")

    pprint(event)
    print("\n")
    # ============= MESSAGE FROM USER ============= #

    if subtype == None:#!= "bot_message":

        channel = message_event["channel"]
        # im means direct messages
        # ============= DIRECT MESSAGE FROM USER ============= #
        if channel_type == "im":

            user = message_event.get("user")
            message = message_event.get("text")

            # bot mentioning implies command
            # ============= USER MENTIONED BOT IN DIRECT MESSAGE TO BOT ============= #
            if str(BOT_MENTIONED) in message:
                print("BOT WAS MENTIONED IN DIRECT MESSAGE FROM USER", "\n")
                _command_handler(channel, user, message)
            # ============= SIMPLE DIRECT MESSAGE FROM USER ============= #
            else:
                print("DIRECT MESSAGE FROM USER TO BOT")
                _message_handler(message_event)
        # ============= CHANNEL MESSAGE FROM USER ============= #
        else:
            print("CHANNEL MESSAGE FROM USER")

    # ============= MESSAGE FROM BOT ============= #
    if subtype == "bot_message" and message_event.get("attachments") != None:
        print("BOT INTERACTIVE MESSAGE")
        # pprint(event)
        # _bot_interactive_message_handler(message_event)


@slack_events_adapter.on('bot_added')
def bot_added(event):
    print("BOT ADDED")
    pprint(event)
    print("\n")
    channel = event["event"]["channel"]
    _first_message(channel)


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, port=port, host='0.0.0.0')