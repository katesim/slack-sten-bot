from collections import namedtuple

User = namedtuple('User', 'user_id im_channel')

class WorkGroup(object):
    def __init__(self, obj: dict):
        self.channel = obj.get('channel', None)
        self.users = [User(*user) for user in obj.get('users', None) if user]
        self.times = obj.get('times', None)
        self.reports = obj.get('reports', {})
        self.ts_reports = obj.get('ts_reports', None)

    def serialize(self):
        return dict(channel=self.channel,
                    users=self.users,
                    times=self.times,
                    reports=self.reports,
                    ts_reports=self.ts_reports)

    def update_reports(self, reports):
        self.reports.update(reports)

    def clean_reports(self):
        self.reports = {}

    def update_ts(self, ts_reports):
        self.ts_reports = ts_reports
