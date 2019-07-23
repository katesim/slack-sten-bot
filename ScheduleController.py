import schedule
import time


class ScheduleController:
    def __init__(self, slack_client, works_report_controller):
        self.slack_client = slack_client
        self.works_report_controller = works_report_controller

    def schedule_group_reminder(self, group_channel):
        # TODO some methods from DBController to get info from database
        # group_info = get_group_info(group_channel)
        # group_members_channels = group_info.get("members_channels")
        # time = group_info.get("time")
        
        print("FORM REMINDER")

        # сейчас хардкод =================
        group_members_channels = ["DL9QABUBT"]
        time = "16:20"
        #time=2
        weekday = 1
        # ================================

        if group_members_channels:
            for member_channel in group_members_channels:
                print("ADD SCHEDULE JOB")
                self.add_scheduled_job(time, weekday, self.send_reminder_message, member_channel)

    def schedule_group_report(self, group_channel):
        print("FORM REPORT")
        # get time and weekday from db

        # ====================хардкод====
        weekday = 2
        time = "12:00"
        group_channel = "CL67NCJ0J"
        # ====================хардкод====

        self.add_scheduled_job(time, weekday, self.send_report_message, group_channel)

    def schedule_group_questionnaire(self, group_channel):
        print("FORM QUESTIONNARE")

         # сейчас хардкод =================
        members_channels = ["DL9QABUBT"]
        time = "16:20"
        #time=2
        weekday = 3
        # ================================

        self.add_scheduled_job(time, weekday, self.send_question_messages, members_channels)

    def send_question_messages(self, members_channels):

        attachments = self.works_report_controller.answer_menu(self.works_report_controller.questions[0])
        for member_channel in members_channels:
            print("SEND QUESTION MESSAGE FOR MEMBER", member_channel)
                
            # works_report_controller = WorksReportController()
            self.slack_client.api_call("chat.postMessage",
                                    channel=member_channel,
                                    text=attachments[0],
                                    attachments=attachments[1])
        

    def send_report_message(self, group_channel):
        # get reports from data base
        # form attachment

        # ============= хардкод проверка что текст берется в момент отправки =====
        conversations_history = self.slack_client.api_call("conversations.history",
                                                    channel="DL9QABUBT",
                                                    latest=str(time.time()),
                                                    limit=2,
                                                    inclusive=True)
    
        report_message = "report message"
        if conversations_history.get("ok"):
            report_message = conversations_history['messages'][1]['text']
            print('REPORT MESSAGE:', report_message)

        # ============= хардкод проверка что текст берется в момент отправки =====
        
        return self.slack_client.api_call("chat.postMessage", 
                                            channel=group_channel, 
                                            text=report_message)

    def send_reminder_message(self, member_channel):
        reminder_message = "There's one hour left until the end of the StandUp."
        return self.slack_client.api_call("chat.postMessage", 
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
    def format_time(self, time):
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
        new_time = "{}:{}".format(hour, minute)
        return new_time


    # parse day number and start scheduler with job
    # could be used for different tasks
    def add_scheduled_job(self, time, day, job, *args):#method, channel, text="text", attachments=[]):
        assert 0 < day < 8, "invalid day value"
        
        # TODO change parser
        if day == 1:
            print("MONDAY JOB")
            #schedule.every().monday.at(time).do(job, method=method, channel=channel, text=text, attachments=attachments)
            schedule.every(5).seconds.do(job, *args)#method=method, channel=channel, text=text, attachments=attachments)
        elif day == 2:
            print("TUESDAY JOB")
            #schedule.every().tuesday.at(time).do(job,*args) 
            schedule.every(5).seconds.do(job, *args)
        elif day == 3:
            print("WENDSDAY JOB")
            #schedule.every().wednesday.at(time).do(job, *args)
            schedule.every(15).seconds.do(job, *args)
        elif day == 4:
            schedule.every().thursday.at(time).do(job, *args)
        elif day == 5:
            schedule.every().friday.at(time).do(job, *args)
        elif day == 6:
            schedule.every().saturday.at(time).do(job, *args)
        else:
            schedule.every().sunday.at(time).do(job, *args)