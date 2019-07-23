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