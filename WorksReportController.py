import time
from collections import namedtuple
from pprint import pprint


class Report:
    def __init__(self, user_id: str):
        self.id_user = user_id
        self.cells = []

    def add_answer(self, cell: namedtuple('Cell', 'question answer ts_answer')):
        self.cells.append(cell)

    def serialize(self):
        return {'id_user': self.id_user,
                'answers': self.cells}

    def __getitem__(self, index):
        return self.cells[index]

    def __len__(self):
        return len(self.cells)

    def __str__(self):
        res = ''
        for text in ["*" + a.question + "* \n " + a.answer + "\n" for a in self.cells]:
            res += text
        return res


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
        self.report = Report(user_id='')
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

    def remember_answer(self, question, answer, real_name_user, ts_answer=None):
        self.report.add_answer(self.Cell(question, answer, ts_answer))
        self.question_counter += 1
        try:
            return self.answer_menu(question=self.questions[self.question_counter])
        except:
            self.question_counter = 0
            return self.create_report(real_name_user)

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

    def create_report(self, real_name_user):
        print("real_name_user", real_name_user)
        return ('New report', [
            {
                "fallback": "Upgrade your Slack client to use messages like these.",
                "color": "#3AA3E3",
                "author_name": real_name_user,
                "attachment_type": "default",
                "title": "Report",
                "text": str(self.report),
                "ts": time.time()
            }
        ])


if __name__ == '__main__':
    ts = '12341234'
    Cell = namedtuple('Cell', 'question answer ts_answer')

    report = Report(user_id='1324')

    report.add_answer(Cell('What did you do yesterday?', 'work', ts))
    report.add_answer(Cell('What are you planning do today?', 'rest', ts))
    report.add_answer(Cell('Any problem?', 'No', ts))

    print('first answer:', report.cells[0].answer)
    print('reports:')
    pprint(report.serialize())
