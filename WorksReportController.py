import time


class WorksReportController:
    def __init__(self, questions=None, short_answers=None):
        if questions is None:
            questions = ["What did you do yesterday? :coffee:",
                         "What are you planning do today?"]
        if short_answers is None:
            short_answers = [("same_as_yesterday", "Same as yesterday"),
                             ("busy", "I'm busy right now"),
                             ("vacation", "I'm on vacation")]

        self.questions = questions
        self.short_answers = short_answers
        self.answers = []
        self.question_counter = 0
        self.real_name_user = None

    def take_short_answer(self, selection=str):
        for answer in self.short_answers:
            if selection == answer[0]:
                message_text = answer[1]
        return message_text

    def take_menu_options(self):
        menu_options = dict(options=[])
        for answer in self.short_answers:
            menu_options['options'].append(dict(text=answer[1], value=answer[0]))
        return menu_options

    def remember_answer(self, answer, real_name_user):
        self.answers.append(answer)
        self.question_counter += 1
        try:
            return self.answer_menu(question=self.questions[self.question_counter])
        except:
            self.question_counter = 0
            return self.create_report(real_name_user, self.questions, self.answers)

    def answer_menu(self, question="What did you do yesterday? :coffee:"):
        return (question, [
            {
                "fallback": "Upgrade your Slack client to use messages like these.",
                "color": "#3AA3E3",
                "attachment_type": "default",
                "callback_id": "menu_options_2319",
                "actions": [
                    {
                        "name": "short_answer_list",
                        "text": "Pick a variant...",
                        "type": "select",
                        "data_source": "external"
                    }
                ]
            }
        ])

    def create_report(self, real_name_user, questions, answers):
        print("real_name_user", real_name_user)
        return ('New report', [
            {
                "fallback": "Upgrade your Slack client to use messages like these.",
                "color": "#3AA3E3",
                "author_name": real_name_user,
                "attachment_type": "default",
                "title": "Report",
                "text": str("*" + questions[0] + "* \n" + answers[0] + "\n*" + questions[1] + "* \n" +
                            answers[1]),
                "ts": time.time()
            }
        ])
