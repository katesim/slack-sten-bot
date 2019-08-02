import schedule
import time
import os

from time_metods import plus_time, minus_time, formatted_time
from DBController import DBController
from Utils import Utils
from WorksReportController import ReportState

YOUR_DIRECT_CHANNEL = os.environ.get("YOUR_DIRECT_CHANNEL")
YOUR_USER_ID = os.environ.get("YOUR_USER_ID")


class ScheduleController:
    reminder_message = "There's one hour left until the end of the StandUp."
    no_answer_message = "No answer"
    times_up_message = "StandUp time's up."

    def __init__(self, slack_client, works_report_controller):
        self.slack_client = slack_client
        self.works_report_controller = works_report_controller
        self.reminder_message = "There's one hour left until the end of the StandUp."
        self.no_answer_message = "No answer"
        self.times_up_message = "StandUp time's up."

    # activate schedule events for all StandUp activity for work group
    def schedule_StandUp(self, group_channel):
        work_group = DBController.get_group({'channel': group_channel})
        users = work_group.users
        times = work_group.times
        # print("REAL TIME", times)
        # times = ["21:4", "21:7", "21:10"]
        self.schedule_group_questionnaire(group_channel, users, times)
        self.schedule_group_reminder(group_channel, users, times)
        self.schedule_completion(group_channel, users, times)

    # send reminder message if member didn't answer any question
    def schedule_group_reminder(self, group_channel, users, times):

        print("FORM REMINDER")
        # add reminder for every report day
        for weekday in times.keys():  # time in times:
            # calculate time for reminder
            time, weekday = plus_time(time=times[weekday], weekday=int(weekday), hour_shift=1, minute_shift=0)
            # weekday="0"
            # time = self.plus_minutes(time, 1)
            time = formatted_time(time)
            print("ADD SCHEDULE REMINDER JOB FOR DAY", weekday)
            self.add_scheduled_job(time, int(weekday), self.send_reminder_messages, group_channel, users)

    def send_reminder_messages(self, group_channel, users):
        # need actual info
        work_group = DBController.get_group({'channel': group_channel})
        reports = work_group.reports
        for user in users:
            report_status = self.works_report_controller.get_report_status(reports.get(user.user_id))
            if report_status == ReportState.EMPTY or report_status == ReportState.INCOMPLETE:
                self.slack_client.api_call("chat.postMessage",
                                           channel=user.im_channel,
                                           text=self.reminder_message)

    def schedule_completion(self, group_channel, users, times):

        print("FORM REPORT")
        # add report into group channel for every report day
        for weekday in times.keys():  # time in times:
            time, weekday = plus_time(time=times[weekday], weekday=int(weekday), hour_shift=2, minute_shift=0)
            # weekday="0"
            # time = self.plus_minutes(time, 2)
            time = formatted_time(time)
            print("ADD SCHEDULE REPORT JOB FOR DAY", weekday)
            self.add_scheduled_job(time, int(weekday), self.finish_questionnaire, group_channel, users)

    def finish_questionnaire(self, group_channel, users):
        # if empty send no answer
        work_group = DBController.get_group({'channel': group_channel})
        reports = work_group.reports
        for user in users:
            real_user_name = Utils.get_real_user_name(self.slack_client, user.user_id)
            report_status = self.works_report_controller.get_report_status(reports.get(user.user_id))
            # has answer
            if report_status == ReportState.INCOMPLETE:
                text, attachment = self.works_report_controller.create_report(real_user_name, user.user_id)
                self.slack_client.api_call("chat.postMessage",
                                           channel=user.user_id,
                                           text=self.times_up_message)
                self.slack_client.api_call("chat.postMessage",
                                           channel=group_channel,
                                           text=text,
                                           attachments=attachment,
                                           thread_ts=work_group.ts_reports)
            if report_status == ReportState.EMPTY:
                text, attachment = self.works_report_controller.create_report(real_user_name, user.user_id,
                                                                              self.no_answer_message)
                self.slack_client.api_call("chat.postMessage",
                                           channel=user.user_id,
                                           text=self.times_up_message)
                self.slack_client.api_call("chat.postMessage",
                                           channel=group_channel,
                                           text=text,
                                           attachments=attachment,
                                           thread_ts=work_group.ts_reports)

    def schedule_group_questionnaire(self, group_channel, users, times):

        print("FORM QUESTIONNARE")
        # start questionnare in every report day
        for weekday in times.keys():  # time in times:#
            # weekday="0"
            time = formatted_time(times[weekday])
            # time = self.formatted_time(time)
            print("ADD SCHEDULE QUESTIONNARE JOB FOR DAY", weekday)
            self.add_scheduled_job(time, int(weekday), self.send_question_messages, group_channel, users)

    def send_question_messages(self, group_channel, users):

        attachments = self.works_report_controller.answer_menu(self.works_report_controller.questions[0])
        # delete all reports from db and from work controller before first question
        work_group = DBController.get_group({'channel': group_channel})
        Utils.clear_reports_work_group(self.slack_client, work_group)
        self.works_report_controller.clean_reports()

        for user in users:
            print("USER", user)
            print("SEND QUESTION MESSAGE FOR MEMBER", user.user_id)

            self.slack_client.api_call("chat.postMessage",
                                       channel=user.im_channel,
                                       text=attachments[0],
                                       attachments=attachments[1])

    def stop_all(self):
        schedule.clear()

    # parse day number and start scheduler with job
    # could be used for different tasks
    def add_scheduled_job(self, time, day, job, *args):
        assert 0 <= day < 7, "invalid day value"
        # Now monday day for tests
        {
            0: lambda job, *args: schedule.every().monday.at(time).do(job, *args),
            # schedule.every(20).seconds.do(job, *args), #
            1: lambda job, *args: schedule.every().tuesday.at(time).do(job, *args),
            2: lambda job, *args: schedule.every().wednesday.at(time).do(job, *args),
            3: lambda job, *args: schedule.every().thursday.at(time).do(job, *args),
            4: lambda job, *args: schedule.every().friday.at(time).do(job, *args),
            5: lambda job, *args: schedule.every().saturday.at(time).do(job, *args),
            6: lambda job, *args: schedule.every().sunday.at(time).do(job, *args)
        }[day](job, *args)
