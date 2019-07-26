import schedule
import time
import os

from WorkGroup import WorkGroup
from DBController import DBController

YOUR_DIRECT_CHANNEL = os.environ.get("YOUR_DIRECT_CHANNEL")
YOUR_USER_ID = os.environ.get("YOUR_USER_ID")

class ScheduleController:
    def __init__(self, slack_client, works_report_controller):
        self.slack_client = slack_client
        self.works_report_controller = works_report_controller

    # activate schedule events for all StandUp activity for work group
    def schedule_StandUp(self, group_channel):
        work_group = WorkGroup(DBController.get_group({'channel':group_channel}))
        users = work_group.users
        times = work_group.times
        self.schedule_group_questionnaire(group_channel, users, times)
        self.schedule_group_reminder(group_channel, users, times)
        self.schedule_no_answer(group_channel, users, times)
        
    # send reminder message if member didn't answer any question
    def schedule_group_reminder(self, group_channel, users, times): 
        
        print("FORM REMINDER")
        # add reminder for every report day
        for weekday in times.keys():
            # calculate time for reminder
            time, weekday = self.plus_hours(times[weekday], int(weekday), hour_shift=1)
            #weekday=1
            time = self.formatted_time(time)
            print("ADD SCHEDULE REMINDER JOB FOR DAY", weekday)
            self.add_scheduled_job(time, int(weekday), self.send_reminder_messages, group_channel, users)

    def send_reminder_messages(self, group_channel, users):
        reminder_message = "There's one hour left until the end of the StandUp."
        # need actual info
        work_group = WorkGroup(DBController.get_group({'channel':group_channel}))
        reports = work_group.reports
        for user in users:
            # if report is empty  
            if not reports.get(user.user_id):
                self.slack_client.api_call("chat.postMessage", 
                                                channel=user.im_channel, 
                                                text=reminder_message)

    def schedule_no_answer(self, group_channel, users, times):

        print("FORM REPORT")
        # add report into group channel gor every report day
        for weekday in times.keys():
            time, weekday = self.plus_hours(times[weekday], int(weekday), hour_shift=3)
            #weekday=2
            time = self.formatted_time(time)
            print("ADD SCHEDULE REPORT JOB FOR DAY", weekday)
            self.add_scheduled_job(time, int(weekday), self.send_no_answer_report, group_channel, users)

    def send_no_answer_report(self, group_channel, users):
        
        report_message = "No answer"
        # if empty send no answer
        work_group = WorkGroup(DBController.get_group({'channel':group_channel}))
        reports = work_group.reports
        
        for user in users:
            if not reports.get(user.user_id):
                # TODO thread report message 
                self.slack_client.api_call("chat.postMessage", 
                                            channel=group_channel, 
                                            text=report_message)

    def schedule_group_questionnaire(self, group_channel, users, times):

        print("FORM QUESTIONNARE")
        # start questionnare in every report day
        for weekday in times.keys():
            time = self.formatted_time(times[weekday])
            print("ADD SCHEDULE QUESTIONNARE JOB FOR DAY", weekday)
            self.add_scheduled_job(time, int(weekday), self.send_question_messages, users)

    def send_question_messages(self, users):

        attachments = self.works_report_controller.answer_menu(self.works_report_controller.questions[0])
        for user in users:
            print("USER", user)
            print("SEND QUESTION MESSAGE FOR MEMBER", user.user_id)
                
            # works_report_controller = WorksReportController()
            self.slack_client.api_call("chat.postMessage",
                                    channel=user.im_channel,
                                    text=attachments[0],
                                    attachments=attachments[1])

    def stop_all(self):
        schedule.clear()

    # calculate time for reminder message (1 hour earlier)
    def minus_hours(self, time, weekday, hour_shift=1):
        assert ":" in time, "time format should be hh:mm or h:mm"
        assert hour_shift < 24, "too much time shift"

        hour, minute = [int(value) for value in time.split(":")]
        new_hour = (hour - hour_shift)%24
        if new_hour > hour:
            weekday = (weekday - 1)%7
        new_time = "{}:{}".format(new_hour, minute)
        return new_time, weekday

    # calculate time for report message (n hour later)
    def plus_hours(self, time, weekday, hour_shift=3):
        assert ":" in time, "time format should be hh:mm or h:mm"
        assert hour_shift < 24, "too much time shift"

        hour, minute = [int(value) for value in time.split(":")]
        new_hour = (hour + hour_shift)%24
        if new_hour < hour:
            weekday = (weekday + 1)%7
        new_time = "{}:{}".format(new_hour, minute)
        return new_time, weekday

    # formatting time for schedule 
    def formatted_time(self, time):
        assert ":" in time, "time format should be hh:mm or h:mm"

        hour, minute = time.split(":")
        len_hour = len(hour)
        len_minute = len(minute)
        assert 3 > len_hour > 0, "invalid hour format"
        assert 3 > len_minute > 0, "invalid minute format"
        if len_hour < 2:
            hour = "0{}".format(hour)
        if len_minute < 2:
            minute = "0{}".format(minute)
        return "{}:{}".format(hour, minute)


    # parse day number and start scheduler with job
    # could be used for different tasks
    def add_scheduled_job(self, time, day, job, *args):
        assert 0 <= day < 7, "invalid day value"
        # Now monday day for tests
        {
            0: lambda job, *args: schedule.every(15).seconds.do(job, *args), # schedule.every().monday.at(time).do(job, *args)
            1: lambda job, *args: schedule.every().tuesday.at(time).do(job,*args), # schedule.every(20).seconds.do(job, *args), #
            2: lambda job, *args: schedule.every().wednesday.at(time).do(job,*args), # schedule.every(25).seconds.do(job, *args),
            3: lambda job, *args: schedule.every().thursday.at(time).do(job,*args),
            4: lambda job, *args: schedule.every().friday.at(time).do(job,*args), 
            5: lambda job, *args: schedule.every().saturday.at(time).do(job,*args), 
            6: lambda job, *args: schedule.every().sunday.at(time).do(job,*args) 
        }[day](job, *args)