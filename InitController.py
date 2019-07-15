import time


class InitController:
    def __init__(self):
        times = [(str(hour), str(minut)) for hour in range(7, 21) for minut in range(0, 60, 15)]
        self.time_string = [x[0] + '.' + x[1] for x in times]


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

    def create_report_init(self, inviter_list, list_days):
        print('inviter_list', inviter_list)
        return [
            {
                "fallback": "Upgrade your Slack client to use messages like these.",
                "color": "#3AA3E3",
                "attachment_type": "default",
                "title": "Report_init",
                "text": str("* list_users: " + str(inviter_list) + "* \n list_days: " + str(list_days) + "\n*"),
                "ts": time.time()
            }
        ]

    def create_dialog(self, channel_id):
        options = []
        for time in self.time_string:
            options.append(dict(
                label=time,
                value=time
            ))

        return {
            "title": "Init new standUP",
            "submit_label": "Submit",
            "callback_id": channel_id + "coffee_order_form",
            "elements": [
                {
                    "label": "Select time",
                    "type": "select",
                    "name": "meal_preferences",
                    "placeholder": "Select a time",
                    "options": options
                },
                {
                    "label": "Post this message on",
                    "name": "channel_notify",
                    "type": "select",
                    "placeholder": "Select a channel",
                    "data_source": "conversations"
                }
            ]
        }
