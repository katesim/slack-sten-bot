import time
from collections import namedtuple
from pprint import pprint


class Report:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.report = {self.user_id: []}

    def add_answer(self, cell: namedtuple('Cell', 'question answer ts_answer')):
        self.report[self.user_id].append(cell)

    def __getitem__(self, index):
        return self.report[self.user_id][index]


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
        self.question_counter = 0
        self.real_name_user = None
        self.Cell = namedtuple('Cell', 'question answer ts_answer')
        self.is_finished = False
        self.ts_thread = None

    def clean_reports(self):
        self.reports = {}

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

    def remember_answer(self, question, answer, user_id, real_user_name, ts_answer):
        
        self.reports.update(Report(user_id=user_id))
        if not self.reports.get(user_id):
            self.reports[user_id] = [self.Cell(question, answer, ts_answer)]
        else:
            asked_questions = [cell[0][0] for cell in self.reports[user_id]]
            if question not in asked_questions:
                self.reports[user_id].append(self.Cell(question, answer, ts_answer))
        self.ts_report = None

        if answer in [short_answer[1] for short_answer in self.short_answers]:
            return self.create_report(real_user_name, user_id)
        try:
            return self.answer_menu(question=self.questions[len(self.reports[user_id])])
        except:
            return self.create_report(real_user_name, user_id)

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

    def forgot_old_report(self, user_id):
        del self.reports[user_id]

if __name__ == '__main__':
    ts = '12341234'
    Cell = namedtuple('Cell', 'question answer ts_answer')

    report = Report(user_id='1324')

    report.add_answer(Cell('What did you do yesterday?', 'work', ts))
    report.add_answer(Cell('What are you planning do today?', 'rest', ts))
    report.add_answer(Cell('Any problem?', 'No', ts))
    print(report)
