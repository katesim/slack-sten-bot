from DBController import DBController


class WorkGroup(object):
    def __init__(self, obj: dict):
        self.channel = obj.get('channel', None)
        self.users = obj.get('users', None)
        self.direct_id = obj.get('direct_id', None)
        self.times = obj.get('times', None)
        self.reports = obj.get('reports', [])
        self.ts_reports = obj.get('ts_reports', None)

    def serialize(self):
        return dict(channel=self.channel,
                    users=self.users,
                    direct_id=self.direct_id,
                    times=self.times,
                    reports=self.reports,
                    ts_reports=self.ts_reports)

    def update_reports(self, report, ts_reports):
        if not self.reports:
            self.reports.append(report)
        self.ts_reports = ts_reports

        for obj in self.reports:
            if obj.get('id_user') == report.get('id_user'):
                obj['answers'] = report['answers']
            else:
                self.reports.append(report)
        DBController.update_reports(self.channel, self.reports, self.ts_reports)

    def set_direct_id(self, direct_id):
        self.direct_id = direct_id

