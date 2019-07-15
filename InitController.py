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
