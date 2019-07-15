import time


class InitController:
    def __init__(self):
        pass

    def init_menu(self, channel):
        return [{
            "callback_id": channel + "init_form",
            "text": "",
            "color": "#3AA3E3",
            "attachment_type": "default",
            "actions": [{
                "name": "init_standup",
                "text": ":coffee: Init new StandUP",
                "type": "button",
                "value": "init_standup"
            }]
        }]

    def create_report_init(self, list_users, list_days):
        return [
            {
                "fallback": "Upgrade your Slack client to use messages like these.",
                "color": "#3AA3E3",
                "attachment_type": "default",
                "title": "Report_init",
                "text": str("* list_users: " + str(list_users) + "* \n list_days: " + str(list_days) + "\n*"),
                "ts": time.time()
            }
        ]
