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
        im_channels = self.users_to_im_channels(users)
        self.schedule_group_questionnaire(im_channels, times)
        self.schedule_no_answer(group_channel, im_channels, times)
        self.schedule_group_report(group_channel, users, times)
    
    # TODO take channels from bd with users
    def users_to_im_channels(self, users):
        return [self.slack_client.api_call("im.open", user=user)['channel'].get('id') for user in users]
        
    # send reminder message if member didn't answer any question
    def schedule_no_answer(self, group_channel, im_channels, times): 
        print("FORM REMINDER")
        # add reminder for every report day
        for weekday in times.keys():
            # calculate time for reminder
            time, weekday = self.plus_hours(times[weekday], weekday, hour_shift=1)
            time = self.formatted_time(time)
            print("ADD SCHEDULE REMINDER JOB FOR DAY", weekday)
            self.add_scheduled_job(time, weekday, self.send_reminder_messages, group_channel, im_channels)

    def schedule_group_report(self, group_channel, users, times):
        print("FORM REPORT")
        # add report into group channel gor every report day
        for weekday in times.keys():
            time, weekday = self.plus_hours(times[weekday], weekday, hour_shift=3)
            time = self.formatted_time(time)
            print("ADD SCHEDULE REPORT JOB FOR DAY", weekday)
            self.add_scheduled_job(time, weekday, self.send_no_answer_report, group_channel, users)

    def schedule_group_questionnaire(self, im_channels, times):
        print("FORM QUESTIONNARE")
        # start questionnare in every report day
        for weekday in times.keys():
            time = self.formatted_time(times[weekday])
            print("ADD SCHEDULE QUESTIONNARE JOB FOR DAY", weekday)
            self.add_scheduled_job(time, weekday, self.send_question_messages, im_channels)

    def send_question_messages(self, im_channels):

        attachments = self.works_report_controller.answer_menu(self.works_report_controller.questions[0])
        for member_channel in im_channels:
            print("SEND QUESTION MESSAGE FOR MEMBER", member_channel)
                
            # works_report_controller = WorksReportController()
            self.slack_client.api_call("chat.postMessage",
                                    channel=member_channel,
                                    text=attachments[0],
                                    attachments=attachments[1])
        

    def send_no_answer_report(self, group_channel, users, work_group):
        # get reports from data base
        # TODO check if report empty or not
        # TODO add message to report message
        # if empty send no answer
        work_group = WorkGroup(DBController.get_group({'channel':group_channel}))
        report_message = "No answer"
        for user in users:
            if work_group.reports.get(user):
                self.slack_client.api_call("chat.postMessage", 
                                            channel=group_channel, 
                                            text=report_message)

        
    def send_reminder_messages(self, group_channel, im_channels):
        reminder_message = "There's one hour left until the end of the StandUp."
        # need actual info
        work_group = WorkGroup(DBController.get_group({'channel':group_channel}))
        for im_channel in im_channels:
            # if report is empty
            # TODO check empty
            # user is 
            #if work_group.reports.get(user):
            self.slack_client.api_call("chat.postMessage", 
                                            channel=im_channel, 
                                            text=reminder_message)

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
            0: lambda job, *args: schedule.every(5).seconds.do(job, *args), #schedule.every().monday.at(time).do(job, *args)
            1: lambda job, *args: schedule.every().tuesday.at(time).do(job,*args), 
            2: lambda job, *args: schedule.every().wednesday.at(time).do(job,*args), 
            3: lambda job, *args: schedule.every().thursday.at(time).do(job,*args),
            4: lambda job, *args: schedule.every().friday.at(time).do(job,*args), 
            5: lambda job, *args: schedule.every().saturday.at(time).do(job,*args), 
            6: lambda job, *args: schedule.every().sunday.at(time).do(job,*args) 
        }[day](job, *args)