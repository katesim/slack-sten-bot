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
        users_list = work_group.users
        times = work_group.times
        im_channels = self.users_to_im_channels(users_list)
        self.schedule_group_questionnaire(group_channel, im_channels, times)
        self.schedule_group_reminder(group_channel, im_channels, times)
        self.schedule_group_report(group_channel, times)
    
    def users_to_im_channels(self, users_list):
        return [self.slack_client.api_call("im.open", user=user)['channel'].get('id') for user in users_list]
        

    def schedule_group_reminder(self, group_channel, im_channels, times):
        
        print("FORM REMINDER")

        for weekday in times.keys():
            time, weekday = self.minus_hours(times[weekday], weekday)
            time = self.formatted_time(time)
            print("ADD SCHEDULE JOB FOR DAY", weekday)
            self.add_scheduled_job(time, weekday, self.send_reminder_messages, im_channels)

    def schedule_group_report(self, group_channel, time):
        print("FORM REPORT")
        # get time and weekday from db

        for weekday in times.keys():
            time, weekday = self.plus_hours(times[weekday], weekday)
            time = self.formatted_time(time)
            print("ADD SCHEDULE JOB FOR DAY", weekday)
            self.add_scheduled_job(time, weekday, self.send_report_message, group_channel)

    def schedule_group_questionnaire(self, group_channel, im_channels):
        print("FORM QUESTIONNARE")

        for weekday in times.keys():
            time = self.formatted_time(times[weekday])
            print("ADD SCHEDULE JOB FOR DAY", weekday)
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
        

    def send_report_message(self, group_channel):
        # get reports from data base
        # TODO check if report empty or not
        # if empty send no answer

        # ============= хардкод проверка что текст берется в момент отправки =====
        conversations_history = self.slack_client.api_call("conversations.history",
                                                    channel=str(YOUR_DIRECT_CHANNEL),
                                                    latest=str(time.time()),
                                                    limit=2,
                                                    inclusive=True)
    
        report_message = "report message"
        if conversations_history.get("ok"):
            report_message = conversations_history['messages'][1]['text']
            print('REPORT MESSAGE:', report_message)

        # ============= хардкод проверка что текст берется в момент отправки =====
        
        self.slack_client.api_call("chat.postMessage", 
                                        channel=group_channel, 
                                        text=report_message)

    def send_reminder_messages(self, members_channels):
        reminder_message = "There's one hour left until the end of the StandUp."
        
        for member_channel in members_channels:
            # if report is empty
            if DBController.reports
            self.slack_client.api_call("chat.postMessage", 
                                            channel=member_channel, 
                                            text=reminder_message)



    def stop_all(self):
        schedule.clear()

    # calculate time for reminder message (1 hour earlier)
    def minus_hours(self, time, weekday, hour_shift=1):
        assert ":" in time, "time format should be hh:mm or h:mm"

        hour, minute = [int(value) for value in time.split(":")]
        new_hour = (hour - hour_shift)%24
        if new_hour > hour:
            weekday = (weekday - 1)%7
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