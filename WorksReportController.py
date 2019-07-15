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

    def take_short_answer(self, selection=str):

        for answer in self.short_answers:
            if selection == answer[0]:
                message_text = answer[1]
        return message_text
