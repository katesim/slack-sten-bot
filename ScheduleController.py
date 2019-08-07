import schedule
import time
import os
from queue import PriorityQueue
from collections import namedtuple

from time_metods import plus_time, minus_time, formatted_time
from DBController import DBController
from Utils import Utils
from WorksReportController import ReportState

UserQueue = namedtuple('UserQueue', 'user_queue current_channel')

class ScheduleController:
    reminder_message = "StandUp will be over soon."
    no_answer_message = "No answer"
    times_up_message = "StandUp time's up."
    questionnaire_header = "Hello, it's time for update on"

    def __init__(self, slack_client, works_report_controller):
        self.slack_client = slack_client
        self.works_report_controller = works_report_controller
        self.reminder_message = "There's one hour left until the end of the StandUp."
        self.no_answer_message = "No answer"
        self.times_up_message = "StandUp time's up."
        self.questionnaire_header = "Hello, it's time for update on"

    # activate schedule events for all StandUp activity for work group
    def schedule_StandUp(self, group_channel):
        work_group = DBController.get_group({'channel': group_channel})
        users = work_group.users
        # times = work_group.times
        # print("REAL TIME", times)
        times = ["13:41", "13:44", "13:47"]
        self.schedule_group_questionnaire(group_channel, users, times)
        self.schedule_group_reminder(group_channel, users, times)
        self.schedule_completion(group_channel, users, times)

    def delete_StandUp(self, group_channel):
        # delete all schedule messages with workgroup tag
        schedule.clear(group_channel)
        # delete group from db
        DBController.remove_groups({'channel': group_channel})
        # TODO delete from queue

    def update_StandUp(self, group_channel):
        self.delete_StandUp(group_channel)
        self.schedule_StandUp(group_channel)
        # TODO delete from queue

    # send reminder message if member didn't answer any question
    def schedule_group_reminder(self, group_channel, users, times):

        print("FORM REMINDER")
        # add reminder for every report day

        # code for test
        for time in times:#weekday in times.keys():  # time in times:
            # calculate time for reminder
            weekday="6"
            time = plus_time(time=time, weekday=int(weekday), minute_shift=1)[0]
            print("TIME!!!", time)
            time = formatted_time(time)

        # code for work
        # for weekday in times.keys():
        #     # calculate time for reminder
        #     time, weekday = plus_time(time=times[weekday], weekday=int(weekday), hour_shift=1)
        #     time = formatted_time(time)

            for user in users:
                print("ADD SCHEDULE REMINDER JOB FOR DAY {} FOR USER {}".format(weekday, user.user_id))
                # need to form schedule queue for every user
                self.add_scheduled_job(time, int(weekday), self.send_reminder_messages, [group_channel], user, group_channel)

        
    def send_reminder_messages(self, user, group_channel):
        # need actual info
        work_group = DBController.get_group({'channel': group_channel})
        reports = work_group.reports
        report_state = self.works_report_controller.get_report_state(reports.get(user.user_id))
        if report_state == ReportState.EMPTY or report_state == ReportState.INCOMPLETE:
            self.slack_client.api_call("chat.postMessage",
                                        channel=user.im_channel,
                                        text=self.reminder_message)

    def schedule_completion(self, group_channel, users, times):

        print("FORM REPORT")
        # add report into group channel for every report day
        for time in times:
            weekday="6"
            time = plus_time(time=time, weekday=int(weekday), minute_shift=2)[0]
            time = formatted_time(time)
        
        # for weekday in times.keys():  # time in times:
        #     time, weekday = plus_time(time=times[weekday], weekday=int(weekday), hour_shift=2)
        #     time = formatted_time(time)

            for user in users:
                    print("ADD SCHEDULE REPORT JOB FOR DAY {} FOR USER {}".format(weekday, user.user_id))
                    self.add_scheduled_job(time, int(weekday), self.finish_questionnaire, [group_channel], user, group_channel)


    def finish_questionnaire(self, user, group_channel):
        # if empty send no answer
        work_group = DBController.get_group({'channel': group_channel})
        reports = work_group.reports
        real_user_name = Utils.get_real_user_name(self.slack_client, user.user_id)
        report_state = self.works_report_controller.get_report_state(reports.get(user.user_id))
        # has answer
        if report_state == ReportState.INCOMPLETE:
            text, attachment = self.works_report_controller.create_report(real_user_name, user.user_id)
        if report_state == ReportState.EMPTY:
            text, attachment = self.works_report_controller.create_report(real_user_name, user.user_id,
                                                                            self.no_answer_message)
        if report_state == ReportState.INCOMPLETE or report_state == ReportState.EMPTY:
            self.slack_client.api_call("chat.postMessage",
                                        channel=user.im_channel,
                                        text=self.times_up_message)
            self.slack_client.api_call("chat.postMessage",
                                        channel=group_channel,
                                        text=text,
                                        attachments=attachment,
                                        thread_ts=work_group.ts_reports)
            QueueController.call_next_in_queue(user)

    def schedule_group_questionnaire(self, group_channel, users, times):

        print("FORM QUESTIONNARE")
        # start questionnare in every report day
        for time in times:
            weekday="6"
            time = formatted_time(time)
           
        # for weekday in times.keys():
        #     time = formatted_time(times[weekday])

            for user in users:
                print("ADD SCHEDULE QUESTIONNARE JOB FOR DAY {} FOR USER {}".format(weekday, user.user_id))
                self.add_scheduled_job(time, int(weekday), self.send_question_messages, [group_channel], user, group_channel)

    def send_question_messages(self, user, group_channel):

        attachments = self.works_report_controller.answer_menu(self.works_report_controller.questions[0])
        # delete all reports from db and from work controller before first question
        work_group = DBController.get_group({'channel': group_channel})
        Utils.clear_reports_work_group(self.slack_client, work_group)
        self.works_report_controller.clean_reports()
        group_channel_name = Utils.get_real_channel_name(self.slack_client, group_channel)
        print("SEND QUESTION MESSAGE FOR MEMBER", user.user_id)
        self.slack_client.api_call("chat.postMessage",
                                    channel=user.im_channel,
                                    text= self.questionnaire_header + group_channel_name + attachments[0],
                                    attachments=attachments[1])

    def stop_all(self):
        schedule.clear()

    # parse day number and start scheduler with job
    # could be used for different tasks
    def add_scheduled_job(self, time, day, job, tags, *args):
        assert 0 <= day < 7, "invalid day value"

        user_id = args[0]
        current_channel_id = args[1]
        user_queue = QueueController.get_user_queue(user_id)
        if not user_queue:
            user_queue = PriorityQueue()
        sort_field = "{},{}".format(day, time)
        #update channel
        {
            0: lambda job, *args: schedule.every().monday.at(time).do(user_queue.put, (sort_field, job, *args)).tag(*tags),
            1: lambda job, *args: schedule.every().tuesday.at(time).do(user_queue.put, (sort_field, job, *args)).tag(*tags),
            2: lambda job, *args: schedule.every().wednesday.at(time).do(user_queue.put, (sort_field, job, *args)).tag(*tags),
            3: lambda job, *args: schedule.every().thursday.at(time).do(user_queue.put, (sort_field, job, *args)).tag(*tags),
            4: lambda job, *args: schedule.every().friday.at(time).do(user_queue.put, (sort_field, job, *args)).tag(*tags),
            5: lambda job, *args: schedule.every().saturday.at(time).do(user_queue.put, (sort_field, job, *args)).tag(*tags),
            6: lambda job, *args: schedule.every().sunday.at(time).do(user_queue.put, (sort_field, job, *args)).tag(*tags)
        }[day](job, *args)

        QueueController.update_in_process(user_id, user_queue, current_channel_id)

class QueueController:


    in_process = {}
    # def __init__(self):
    #     # {user: [user_queue, current_channel]}
    #     self.in_process = {}

    @classmethod
    def get_user_queue(cls, user):
        return cls.in_process.get(user)

    @classmethod
    def get_current_channel(cls, user):
        user_in_process = cls.in_process.get(user)
        if user_in_process:
            return user_in_process.current_channel
        print("THERE IS NO USER ", user)

    # @classmethod
    # def parse_queue_obj(cls, user_queue):
    #     sort_field, job, *args = user_queue

    @classmethod
    def call_next_in_queue(cls, user):
        user_queue = cls.get_user_queue(user)
        if not user_queue.empty():
            sort_field, job, *args = user_queue.get()
            current_channel = args[1]
            print("SORT TIME: ", sort_field)
            print("PRINT JOB ARGS: ", *args)
            job(*args)
            user_queue.task_done()
        cls.update_in_process(user, user_queue, current_channel)


    @classmethod
    def update_in_process(cls, user, user_queue, current_channel):
        print("UPDATE USER IN PROCESS")
        cls.in_process[user] = UserQueue(user_queue, current_channel)

    # @classmethod
    # def update_current_channel(cls, user, current_channel):
    #     user_in_process = cls.in_process.get(user)
    #     if user_in_process:
    #         # is it ok use tuple for changed data?
    #         user_in_process.current_channel = current_channel
    #         return
    
    # def update_user_queue(self, user, user_queue):
    #     user_in_process = self.in_process.get(user)
    #     if user_in_process:
    #         # is it ok use tuple for changed data
    #         user_in_process.user_queue = user_queue
    #         return
