import time
from collections import namedtuple
from pprint import pprint


class WorksReportController:
    def __init__(self, questions=None, short_answers=None):
        if questions is None:
            questions = ["What did you do yesterday? :coffee:",
                         "What are you planning to do today?",
                         "Any problems?"]
        if short_answers is None:
            short_answers = [("same_as_yesterday", "Same as yesterday"),
                             ("busy", "I'm busy right now"),
                             ("vacation", "I'm on vacation")]

        self.questions = questions
        self.short_answers = short_answers
        self.reports = {}
        self.ts_report = None
        self.Cell = namedtuple('Cell', 'question answer ts_answer')
        self.question_counter = 0

    def remember_answer(self, question, answer, user_id, real_user_name, ts_answer):
        self.question_counter += 1
        if not self.reports.get(user_id):
            self.reports[user_id] = [self.Cell(question, answer, ts_answer)]
        else:
            asked_questions = [cell[0][0] for cell in self.reports[user_id]]
            if question not in asked_questions:
                self.reports[user_id].append(self.Cell(question, answer, ts_answer))
        self.ts_report = None

        if answer in [short_answer[1] for short_answer in self.short_answers]:
            self.question_counter = 0
            return self.create_report(real_user_name, user_id)
        try:
            return self.answer_menu(question=self.questions[len(self.reports[user_id])])
        except:
            self.question_counter = 0
            return self.create_report(real_user_name, user_id)

    def create_report(self, real_name_user, user_id, message=""):
        self.ts_report = time.time()
        if not message:
            for text in ["*{}* \n {} \n".format(report.question, report.answer) for report in self.reports[user_id]]:
                message += text

        return ('New report', [
            {
                "fallback": "Upgrade your Slack client to use messages like these.",
                "color": "#3AA3E3",
                "author_name": real_name_user,
                "attachment_type": "default",
                "title": "Report",
                "text": message,
                "ts": self.ts_report
            }
        ])

    def get_report_status(self, reports):
        print("REPORTS FOR USER", reports)
        short_answers = [pair[1] for pair in self.short_answers]
        if reports:
            print("FIRST REPORT", reports[0][1])
            print("SHORT ANSWERS", self.short_answers)
            if len(reports) != len(self.questions):
                if reports[0][1] in short_answers:
                    print("STATUS short")
                    return "short"
                else:
                    print("STATUS incomplete")
                    return "incomplete"
            else:
                print("STATUS complete")
                return "complete"
        else:
            print("STATUS empty")
            return "empty"

    def clean_reports(self):
        self.reports = {}

    def forgot_old_report(self, user_id):
        del self.reports[user_id]

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

    @staticmethod
    def answer_menu(question="What did you do yesterday? :coffee:"):
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
