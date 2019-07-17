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
