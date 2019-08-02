from flask import Flask, request, make_response, Response
import json
import os
from slackclient import SlackClient
from slackeventsapi import SlackEventAdapter
import schedule
import time
from pprint import pprint

from WorksReportController import WorksReportController
from DBController import DBController
from ScheduleController import ScheduleController
from Utils import Utils

app = Flask(__name__)

# Your app's Slack bot user token
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SIGNING_SECRET = os.environ.get("SIGNING_SECRET")
# TODO delete hotfix variable to catch bot mentioning
BOT_MENTIONED = os.environ.get("BOT_MENTIONED")

# Slack client for Web API requests
slack_client = SlackClient(SLACK_BOT_TOKEN)
# Slack event adapter API to process events
slack_events_adapter = SlackEventAdapter(SIGNING_SECRET, "/slack/events", app)
schedule.run_continuously()

# List of commands for bot
commands = ['/q', '/init', '/stop']

global works_report_controller
works_report_controller = WorksReportController()


@app.route('/', methods=['GET'])
def webhook():
    return Response('It works!')


# The endpoint Slack will load your menu options from
@app.route("/slack/message_options", methods=["POST"])
def message_options():
    # Dictionary of menu options which will be sent as JSON
    menu_options = WorksReportController().take_menu_options()
    # Load options dict as JSON and respond to Slack
    return Response(json.dumps(menu_options), mimetype='application/json')


# The endpoint Slack will send the user's menu selection to
@app.route("/slack/message_actions", methods=["POST"])
def message_actions():
    global time
    global works_report_controller
    form_json = json.loads(request.form["payload"])
    print(f'\n\n\nPAYLOAD:\n{form_json["type"]} \n\n\n\n')
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
                real_user_name=Utils.get_real_user_name(slack_client, user),
                ts_answer=time.time())

            work_group = DBController.get_group({'serial_id': 0})
            work_group.update_reports(reports=works_report_controller.reports)
            DBController.update_reports(work_group)
            # work_group.update_ts(ts_reports=works_report_controller.ts_report)

            slack_client.api_call("chat.update",
                                  channel=channel,
                                  ts=form_json["message_ts"],
                                  text="Your answer is {}  :coffee:".format(short_answer),
                                  attachments=[]  # empty `attachments` to clear the existing massage attachments
                                  )
            slack_client.api_call("chat.postMessage",
                                  channel=work_group.channel,
                                  text=attachments[0],
                                  attachments=attachments[1],
                                  thread_ts=work_group.ts_reports)
            # Send an HTTP 200 response with empty body so Slack knows we're done here
            return make_response("", 200)
        return make_response("", 200)


def start_questionnaire(work_group_id=0):
    attachments = WorksReportController.answer_menu(WorksReportController().questions[0])

    work_group = DBController.get_group({'serial_id': work_group_id})
    # delete all reports from db and from work controller before first question
    Utils.clear_reports_work_group(slack_client, work_group)

    works_report_controller.clean_reports()
    for u in work_group.users:
        slack_client.api_call("chat.postMessage",
                              channel=u.im_channel,
                              text=attachments[0],
                              attachments=attachments[1])


def _command_handler(channel, message):
    global works_report_controller

    schedule_controller = ScheduleController(slack_client, works_report_controller)
    message_words = message.split()
    if commands[0] in message_words:
        print(commands[0], message)
        slack_client.api_call("chat.postMessage",
                              channel=channel,
                              text="command q")
        start_questionnaire()

        return True

    if commands[1] in message_words:
        print(commands[1], message)
        if not DBController.get_group({'serial_id': 0}):
            # TODO заполнить из странички-админки
            DBController.add_group(dict(
                channel="CL67NCJ0J",  # test channel
                users=[('UHTJL2NKZ', slack_client.api_call("im.open", user='UHTJL2NKZ')['channel'].get('id'))],
                # ('UL4D3C0HG', slack_client.api_call("im.open", user='UL4D3C0HG')['channel'].get('id'))],
                times={'0': '17:00'}))

            slack_client.api_call("chat.postMessage",
                                  channel=channel,
                                  text="Add group to database and Init new standUP"
                                  )

            # INIT STANDUP SCHEDULE FOR WORKGROUP
            work_group = DBController.get_group({'serial_id': 0})
            schedule_controller.schedule_StandUp(group_channel=work_group.channel)
        return True

    if commands[2] in message_words:
        print(commands[2], message, '\nSCHEDULE STOP')
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
        print("USER ID", user)
        conversations_history = slack_client.api_call("conversations.history",
                                                      channel=channel,
                                                      latest=str(time.time()),
                                                      limit=3,
                                                      inclusive=True)

        question, answer = get_qa(conversations_history)
        print('QUESTION: ', question, 'ANSWER: ', answer)
        
        if question in works_report_controller.questions:
            attachments = works_report_controller.remember_answer(answer=answer,
                                                                  question=question,
                                                                  user_id=user,
                                                                  real_user_name=Utils.get_real_user_name(slack_client,
                                                                                                          user),
                                                                  ts_answer=time.time())

            work_group = DBController.get_group({'serial_id': 0})
            work_group.update_reports(reports=works_report_controller.reports)
            DBController.update_reports(work_group)

            if 'New report' == attachments[0]:

                slack_client.api_call("chat.postMessage",
                                      channel=channel,
                                      text="Thank you! I made notes! :pencil:",
                                      attachments=[])

                slack_client.api_call("chat.postMessage",
                                      channel=work_group.channel,
                                      text=attachments[0],
                                      attachments=attachments[1],
                                      thread_ts=work_group.ts_reports)

            else:
                slack_client.api_call("chat.postMessage",
                                      channel=channel,  # отправлять следующий вопрос в личку
                                      text=attachments[0],
                                      attachments=attachments[1])
    return make_response("Message Sent", 200, )


def get_qa(conversations_history):
    if len(conversations_history['messages']) < 2:
        return '', ''
    messages = [(message['text'], message.get('subtype')) for message in conversations_history['messages']]
    if messages[1][0] in WorksReportController().questions and messages[1][1] == 'bot_message':
        return messages[1][0], messages[0][0]
    if messages[1][0] == ScheduleController.reminder_message and messages[1][1] == 'bot_message':
        try:
            if messages[2][0] in WorksReportController().questions and messages[2][1] == 'bot_message':
                return messages[2][0], messages[0][0]
        except:
            return '', ''
    return '', ''


def _first_message(channel):
    message = f'Hello! :hand:\nAvailable commands:*{commands[0]}* - _send questions_\n*{commands[1]}* - _init new task'
    return slack_client.api_call("chat.postMessage",
                                 channel=channel,
                                 text=message)


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

    print(f"SUBTYPE: {subtype} \n")

    # ============= MESSAGE FROM USER ============= #
    if subtype is None:  # != "bot_message":
        channel = message_event["channel"]
        if channel_type == "im":  # im means direct messages
            message = message_event.get("text")
            if str(BOT_MENTIONED) in message:
                print("BOT WAS MENTIONED IN DIRECT MESSAGE FROM USER", "\n")
                _command_handler(channel, message)
            else:
                print("DIRECT MESSAGE FROM USER TO BOT")
                _message_handler(message_event)
        else:
            print("CHANNEL MESSAGE FROM USER")
    if subtype == "bot_message" and message_event.get("attachments") is not None:
        print("BOT INTERACTIVE MESSAGE")


@slack_events_adapter.on('bot_added')
def bot_added(event):
    print("BOT ADDED")
    pprint(event)
    print("\n")
    channel = event["event"]["channel"]
    _first_message(channel)


if __name__ == '__main__':
    DBController.check_db_status()
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, port=port, host='0.0.0.0')
