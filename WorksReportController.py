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

    def __str__(self):
        res = ''
        # for text in ["*" + a.question + "* \n " + a.answer + "\n" for a in self.report[self.user_id]]:
        for text in self.report[self.user_id]:
            res += text.question
        return res


class WorksReportController:
    def __init__(self, questions=None, short_answers=None):
        if questions is None:
            questions = ["What did you do yesterday? :coffee:",
                         "What are you planning to do today?"]
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

    def create_report(self, real_name_user, user_id):
        self.ts_report = time.time()
        return ('New report', [
            {
                "fallback": "Upgrade your Slack client to use messages like these.",
                "color": "#3AA3E3",
                "author_name": real_name_user,
                "attachment_type": "default",
                "title": "Report",
                "text": str(self.reports[user_id]),
                "ts": self.ts_report
            }
        ])


if __name__ == '__main__':
    ts = '12341234'
    Cell = namedtuple('Cell', 'question answer ts_answer')

    report = Report(user_id='1324')

    report.add_answer(Cell('What did you do yesterday?', 'work', ts))
    report.add_answer(Cell('What are you planning do today?', 'rest', ts))
    report.add_answer(Cell('Any problem?', 'No', ts))

    # print('first answer:', report.cells[0].answer)
    print('reports:')
    pprint(report.serialize())
