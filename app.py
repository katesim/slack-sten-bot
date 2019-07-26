from flask import Flask, request, make_response, Response
import json
import os
from slackclient import SlackClient
from slackeventsapi import SlackEventAdapter
import schedule
import time
from pprint import pprint
from collections import namedtuple

from WorksReportController import WorksReportController
from InitController import InitController
from DBController import DBController
from ScheduleController import ScheduleController

init_controller = InitController()

app = Flask(__name__)

# Your app's Slack bot user token
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SIGNING_SECRET = os.environ.get("SIGNING_SECRET")
# hotfix variable to catch bot mentioning
BOT_MENTIONED = os.environ.get("BOT_MENTIONED")
# hotfix TODO delete hardcode ids
YOUR_DIRECT_CHANNEL = os.environ.get("YOUR_DIRECT_CHANNEL")
YOUR_USER_ID = os.environ.get("YOUR_USER_ID")

# Slack client for Web API requests
slack_client = SlackClient(SLACK_BOT_TOKEN)
# Slack event adapter API to process events
slack_events_adapter = SlackEventAdapter(SIGNING_SECRET, "/slack/events", app)
schedule.run_continuously()

# List of commands for bot
commands = ['/q', '/init', '/start', '/stop']

global works_report_controller
global schedule_controller

works_report_controller = WorksReportController()
schedule_controller = ScheduleController(slack_client, works_report_controller)


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
    global time
    global works_report_controller
    form_json = json.loads(request.form["payload"])
    print('\n\n\nPAYLOAD:\n', form_json["type"], '\n\n\n\n')
    pprint(form_json)

    channel = form_json["channel"]["id"]
    user = form_json["user"]["id"]

    if form_json["type"] == "interactive_message":
        if form_json['actions'][0]['name'] == str("short_answer_list"):
            # Check to see what the user's selection was and update the message accordingly
            selection = form_json["actions"][0]["selected_options"][0]["value"]
            short_answer = works_report_controller.take_short_answer(selection)
            attachments = works_report_controller.remember_answer(
                question=works_report_controller.questions[works_report_controller.question_counter],
                answer=short_answer,
                user_id=user,
                real_user_name=get_real_user_name(user),
                ts_answer=time.time())

            work_group = DBController.get_group({'serial_id': 0})
            # print("WORK GROUP SHORT OLD")
            # pprint(work_group.reports)
            work_group.update_reports(reports=works_report_controller.reports)

            work_group.update_ts(ts_reports=works_report_controller.ts_report)
            # print("WORK GROUP SHORT NEW")
            # pprint(work_group.reports)
            DBController.update_reports(work_group)

            slack_client.api_call(
                "chat.update",
                channel=channel,
                ts=form_json["message_ts"],
                text="Your answer is {}  :coffee:".format(short_answer),
                attachments=[]  # empty `attachments` to clear the existing massage attachments
            )
            slack_client.api_call("chat.postMessage",
                                  channel= "CL67NCJ0J",#work_group.channel,  # TODO отправлять в тред РГ
                                  text=attachments[0],
                                  attachments=attachments[1],
                                  thread_ts=works_report_controller.ts_thread)
            #works_report_controller.forgot_old_report(user)

            # Send an HTTP 200 response with empty body so Slack knows we're done here
            return make_response("", 200)

        if form_json['actions'][0]['name'] == "init_standup":
            # open_dialog = slack_client.api_call(
            #     "dialog.open",
            #     trigger_id=form_json["trigger_id"],
            #     dialog=init_controller.create_dialog(form_json["channel"]["id"])
            # )
            #
            # print('\nopen_dialog: ', open_dialog)
            #
            # # Update the message to show that we're in the process of taking their order
            # slack_client.api_call(
            #     "chat.update",
            #     channel=channel,
            #     ts=form_json["message_ts"],
            #     text=":pencil: Note your answers"
            # )
            #
            # send_message(_channel, 'Whom to invite?')

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

def _command_handler(channel, user, message):
    global works_report_controller
    global schedule_controller

    message_words = message.split()
    if commands[0] in message_words:
        print(commands[0], message)
        slack_client.api_call("chat.postMessage",
                              channel=channel,
                              text="command q")

        # ================================================
        work_group = DBController.get_group({'serial_id': 0})
        ts = set_report_ts(work_group.channel)
        
        #work_group.ts_reports = ts
        #DBController.update_reports(work_group)
        works_report_controller.ts_thread = ts
        # works_report_controller = WorksReportController()

        attachments = works_report_controller.answer_menu(works_report_controller.questions[0])
        # delete all reports from db and from work controller before first question
        work_group = DBController.get_group({'serial_id': 0})
        work_group.clean_reports()
        # print("REMOVE WG ")
        # pprint(work_group.reports)
        DBController.update_reports(work_group)
        work_group = DBController.get_group({'serial_id': 0})
        # print("WORK GROUP CLEAN IN DB")
        # pprint(work_group.reports)
        works_report_controller.clean_reports()
        for u in work_group.users:
            slack_client.api_call("chat.postMessage",
                                  channel=u.im_channel,
                                  text=attachments[0],
                                  attachments=attachments[1])
        return True

    if commands[1] in message_words:
        print(commands[1], message)
        # TODO заполнить из странички-админки
        DBController.add_group(dict(
            channel="CL67NCJ0J", # test channel
            users=[('UL4D3C0HG', slack_client.api_call("im.open", user='UL4D3C0HG')['channel'].get('id')),
             ('UHTJL2NKZ', slack_client.api_call("im.open", user='UHTJL2NKZ')['channel'].get('id'))],
            times={'0': '7:30'}))

        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text="Add group to database"
        )

        slack_client.api_call("chat.postMessage",
                              channel=channel,
                              text="Init new standUP",
                              attachments=[])
        return True

    if commands[2] in message_words:
        print(commands[2], message)
        print('SCHEDULE START')
        # TODO take group channel
        work_group = DBController.get_group({'serial_id': 0})
        schedule_controller.schedule_StandUp(group_channel=work_group.channel)
        return True

    if commands[3] in message_words:
        print(commands[3], message)
        print('SCHEDULE STOP')
        schedule_controller.stop_all()
        return True

    else:
        return False


def _message_handler(message_event):
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
            print("USER SELECTED SHORT ANSWER")

    if user:
        real_user_name = get_real_user_name(user)
        print("USER ID", user)
        # предыдущее вопрос?
        current_message, previous_message = _take_answer(message_event)
        #print('current_message, previous_message', current_message, previous_message)
        if previous_message in WorksReportController().questions:
            print("BEFORE REMEMBER ANSWER")
            pprint(works_report_controller.reports)
            attachments = works_report_controller.remember_answer(answer=current_message,
                                                                  question=previous_message,
                                                                  user_id=user,
                                                                  real_user_name=real_user_name,
                                                                  ts_answer=time.time())
            # print("AFTER REMEMBER ANSWER")
            # pprint(works_report_controller.reports)
            work_group = DBController.get_group({'serial_id': 0})
            # print("WORK GROUP REPORTS OLD")
            # pprint(work_group.reports)
            work_group.update_reports(reports=works_report_controller.reports)
            # print("WORK GROUP REPORTS NEW")
            # pprint(work_group.reports)

            DBController.update_reports(work_group)
            if 'New report' == attachments[0]:
                slack_client.api_call("chat.postMessage",
                                  channel=work_group.channel,
                                  text=attachments[0],
                                  attachments=attachments[1],
                                  thread_ts = works_report_controller.ts_thread)
                #works_report_controller.forgot_old_report(user)
            else:
                slack_client.api_call("chat.postMessage",
                                    channel=channel,  # отправлять следующий вопрос в личку
                                    text=attachments[0],
                                    attachments=attachments[1])
    return make_response("Message Sent", 200, )

def set_report_ts(output_channel):
    response = slack_client.api_call("chat.postMessage",
                                channel = output_channel,
                                text = "Update for {} WorkGroup".format(output_channel))
    ts = response["message"]["ts"]
    return ts

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

# process direct bot message
@slack_events_adapter.on('message')
def message(event):
    print("MESSAGE")
    message_event = event["event"]
    channel_type = message_event.get("channel_type")
    subtype = message_event.get("subtype")

    #pprint(event)
    print("\n")
    # ============= MESSAGE FROM USER ============= #
    if subtype == None:#!= "bot_message":

        channel = message_event["channel"]
        # im means direct messages
        if channel_type == "im":

            user = message_event.get("user")
            message = message_event.get("text")

            # bot mentioning implies command
            if str(BOT_MENTIONED) in message:
                print("BOT WAS MENTIONED IN DIRECT MESSAGE FROM USER", "\n")
                _command_handler(channel, user, message)
            else:
                print("DIRECT MESSAGE FROM USER TO BOT")
                _message_handler(message_event)
        else:
            print("CHANNEL MESSAGE FROM USER")

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


def check_db_status():
    db_len = 0
    for _ in DBController.get_all_groups():
        db_len += 1
    if db_len == 0:
        print('First setup database...')
        DBController.first_setup()


if __name__ == '__main__':
    check_db_status()
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, port=port, host='0.0.0.0')
