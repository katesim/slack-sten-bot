import time
from flask import make_response
from collections import namedtuple

from ScheduleController import ScheduleController, QueueController
from DBController import DBController
from WorksReportController import WorksReportController
from Utils import Utils


class MessageHandler:
    commands = ['/q', '/init', '/stop']

    def __init__(self, slack_client):
        self.works_report_controller = WorksReportController()
        self.slack_client = slack_client

    def _start_questionnaire(self, work_group_id=0):
        attachments = WorksReportController.answer_menu(WorksReportController().questions[0])

        work_group = DBController.get_group({'serial_id': work_group_id})
        # delete all reports from db and from work controller before first question
        Utils.clear_reports_work_group(self.slack_client, work_group)

        self.works_report_controller.clean_reports()
        for u in work_group.users:
            self.slack_client.api_call("chat.postMessage",
                                       channel=u.im_channel,
                                       text=attachments[0],
                                       attachments=attachments[1])

    @staticmethod
    def get_qa(conversations_history):
        if len(conversations_history['messages']) < 2:
            return '', ''
        Message = namedtuple('Message', 'text subtype')
        messages = [Message(message['text'], message.get('subtype')) for message in conversations_history['messages']]
        # TODO check it in message handler
        if messages[0].subtype == "bot_message":
            return '', ''
        answer = messages[0].text
        if messages[1].text in WorksReportController().questions and messages[1].subtype == 'bot_message':
            return messages[1].text, answer
        if messages[1].text == ScheduleController.reminder_message and messages[1].subtype == 'bot_message':
            try:
                if messages[2].text in WorksReportController().questions and messages[2].subtype == 'bot_message':
                    return messages[2].text, answer
            except:
                return '', ''
        return '', ''

    def command_handler(self, channel, message):
        schedule_controller = ScheduleController(self.slack_client, self.works_report_controller)
        message_words = message.split()
        if self.commands[0] in message_words:
            print(self.commands[0], message)
            self.slack_client.api_call("chat.postMessage",
                                       channel=channel,
                                       text="command q")
            self._start_questionnaire()
            return make_response("", 200)

        if self.commands[1] in message_words:
            print(self.commands[1], message)
            if not DBController.get_group({'serial_id': 0}):
                # TODO заполнить из странички-админки
                DBController.add_group(dict(
                    channel="CL67NCJ0J",  # test channel
                    #users=[('UHTJL2NKZ', self.slack_client.api_call("im.open", user='UHTJL2NKZ')['channel'].get('id')),
                    users=[('UL4D3C0HG', self.slack_client.api_call("im.open", user='UL4D3C0HG')['channel'].get('id'))],
                    times={'6': '17:00'}))

                self.slack_client.api_call("chat.postMessage",
                                           channel=channel,
                                           text="Add group to database and Init new standUP"
                                           )

                # INIT STANDUP SCHEDULE FOR WORKGROUP
                work_group = DBController.get_group({'serial_id': 0})
                schedule_controller.schedule_StandUp(group_channel=work_group.channel)
            return make_response("", 200)

        if self.commands[2] in message_words:
            print(self.commands[2], message, '\nSCHEDULE STOP')
            if "all" in message_words:
                schedule_controller.stop_all()
                return make_response("", 200)
            if "CL67NCJ0J" in message_words:
                schedule_controller.delete_StandUp("CL67NCJ0J")
            return make_response("", 200)

        else:
            return make_response("", 200)

    def message_handler(self, message_event):
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
            conversations_history = self.slack_client.api_call("conversations.history",
                                                               channel=channel,
                                                               latest=str(time.time()),
                                                               limit=3,
                                                               inclusive=True)

            question, answer = self.get_qa(conversations_history)
            print('QUESTION: ', question, 'ANSWER: ', answer)

            if question in self.works_report_controller.questions:
                attachments = self.works_report_controller.remember_answer(answer=answer,
                                                                           question=question,
                                                                           user_id=user,
                                                                           real_user_name=Utils.get_real_user_name(
                                                                               self.slack_client,
                                                                               user),
                                                                           ts_answer=time.time())

                current_channel = QueueController.get_current_channel(user)
                work_group = DBController.get_group({'channel': current_channel})
                work_group.update_reports(reports=self.works_report_controller.reports)
                DBController.update_reports(work_group)

                if 'New report' == attachments[0]:

                    self.slack_client.api_call("chat.postMessage",
                                               channel=channel,
                                               text="Thank you! I made notes! :pencil:",
                                               attachments=[])

                    self.slack_client.api_call("chat.postMessage",
                                               channel=work_group.channel,
                                               text=attachments[0],
                                               attachments=attachments[1],
                                               thread_ts=work_group.ts_reports)

                    QueueController.call_next_in_queue(user)

                else:
                    self.slack_client.api_call("chat.postMessage",
                                               channel=channel,  # отправлять следующий вопрос в личку
                                               text=attachments[0],
                                               attachments=attachments[1])
        return make_response("Message Sent", 200, )

    def first_message(self, channel):
        message = f'Hello! :hand:\nAvailable commands:*{self.commands[0]}* ' \
            f'- _send questions_\n*{self.commands[1]}* - _init new task'
        return self.slack_client.api_call("chat.postMessage", channel=channel, text=message)
