import schedule


class ScheduleController:
    def __init__(self, slack_client):
        self.slack_client = slack_client

    def schedule_group_reminder(self, group_channel):
        # TODO some methods from DBController to get info from database
        # group_info = get_group_info(group_channel)
        # group_members_channels = group_info.get("members_channels")
        # time = group_info.get("time")
        
        print("FORM REMINDER")
        # сейчас хардкод =================
        group_members_channels = ["DL9QABUBT"]
        reminder_message = "There's one hour left until the end of the StandUp."
        time = "16:20"
        #time=2
        day = 1
        # ================================

        if group_members_channels:
            for member_channel in group_members_channels:
                print("ADD SCHEDULE JOB")
                self.add_scheduled_job(time, day, self.slack_client.api_call, 
                                                "chat.postMessage", 
                                                member_channel, 
                                                reminder_message)

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
    def add_scheduled_job(self, time, day, job, method, channel, text, attachments=[]):
        assert 0 < day < 8, "invalid day value"
        
        # TODO change parser
        if day == 1:
            print("MONDAY JOB")
            #schedule.every().monday.at(time).do(job, method=method, channel=channel, text=text, attachments=attachments)
            schedule.every(10).seconds.do(job, method=method, channel=channel, text=text, attachments=attachments)
        elif day == 2:
            schedule.every().tuesday.at(time).do(job, method=method, channel=channel, text=text, attachments=attachments)
        elif day == 3:
            schedule.every().wednesday.at(time).do(job, method=method, channel=channel, text=text, attachments=attachments)
        elif day == 4:
            schedule.every().thursday.at(time).do(job, method=method, channel=channel, text=text, attachments=attachments)
        elif day == 5:
            schedule.every().friday.at(time).do(job, method=method, channel=channel, text=text, attachments=attachments)
        elif day == 6:
            schedule.every().saturday.at(time).do(job, method=method, channel=channel, text=text, attachments=attachments)
        else:
            schedule.every().sunday.at(time).do(job, method=method, channel=channel, text=text, attachments=attachments)