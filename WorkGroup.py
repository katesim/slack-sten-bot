from DBController import DBController


class WorkGroup(object):
    def __init__(self, obj: dict):
        self.channel = obj.get('channel', None)
        self.users = obj.get('users', None)
        self.times = obj.get('times', None)
        self.reports = obj.get('reports', {})
        self.ts_reports = obj.get('ts_reports', None)

    def serialize(self):
        return dict(channel=self.channel,
                    users=self.users,
                    times=self.times,
                    reports=self.reports,
                    ts_reports=self.ts_reports)

    def update_reports(self, report, ts_reports):
        self.reports.update(report)
        self.ts_reports = ts_reports
        DBController.update_reports(self.channel, self.reports, self.ts_reports)
