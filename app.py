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
from ScheduleController import ScheduleController, QueueController
from MessageHandler import MessageHandler
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
    form_json = json.loads(request.form["payload"])
    print(f'\n\n\nPAYLOAD:\n{form_json["type"]} \n\n\n\n')
    pprint(form_json)

    channel = form_json["channel"]["id"]
    user = form_json["user"]["id"]

    if form_json["type"] == "interactive_message":
        if form_json['actions'][0]['name'] == str("short_answer_list"):
            # Check to see what the user's selection was and update the message accordingly
            selection = form_json["actions"][0]["selected_options"][0]["value"]
            short_answer = message_handler.works_report_controller.take_short_answer(selection)
            attachments = message_handler.works_report_controller.remember_answer(
                question=message_handler.works_report_controller.questions[
                    message_handler.works_report_controller.question_counter],
                answer=short_answer,
                user_id=user,
                real_user_name=Utils.get_real_user_name(slack_client, user),
                ts_answer=time.time())

            current_channel = QueueController.get_current_channel(user)
            work_group = DBController.get_group({'channel': current_channel})
            work_group.update_reports(reports=message_handler.works_report_controller.reports)
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
                    
            QueueController.call_next_in_queue(user)
            # Send an HTTP 200 response with empty body so Slack knows we're done here
            return make_response("", 200)
        return make_response("", 200)


# bot mentioning in channel
@slack_events_adapter.on('app_mention')
def app_mention(event):
    print("APP MENTIONED\n")
    pprint(event)
    print("\n")
    channel = event["event"]["channel"]
    message_handler.first_message(channel)


# process direct bot message
@slack_events_adapter.on('message')
def message(event):
    print("MESSAGE")
    message_event = event["event"]
    channel_type = message_event.get("channel_type")
    subtype = message_event.get("subtype")
    pprint(message_event)
    print(f"SUBTYPE: {subtype} \n")

    # ============= MESSAGE FROM USER ============= #
    if subtype is None:  # != "bot_message":
        channel = message_event["channel"]
        if channel_type == "im":  # im means direct messages
            message = message_event.get("text")
            if str(BOT_MENTIONED) in message:
                print("BOT WAS MENTIONED IN DIRECT MESSAGE FROM USER", "\n")
                message_handler.command_handler(channel, message)
            else:
                print("DIRECT MESSAGE FROM USER TO BOT")
                message_handler.message_handler(message_event)
        else:
            print("CHANNEL MESSAGE FROM USER")
    if subtype == "bot_message" and message_event.get("attachments") is not None:
        print("BOT INTERACTIVE MESSAGE")


if __name__ == '__main__':
    DBController.check_db_status()
    message_handler = MessageHandler(slack_client)
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, port=port, host='0.0.0.0')
