from DBController import DBController
import uuid


class WorksGroup:
    def __init__(self, channel='DHCLCG8DQ', users=['UHTUFSFN2'], times='7:30'):
        self.channel = channel
        self.users = users
        self.times = times
        self.reports = []
        self.ts_reports = None
        DBController.first_setup()
        DBController.add_group(group=self.serialize(), uuid=str(uuid.uuid4()))

    def serialize(self):
        return dict(channel=self.channel,
                    users=self.users,
                    times=self.times,
                    reports=self.reports,
                    ts_reports=self.ts_reports)

    def update_reports(self, channel, report, ts_reports):
        if len(self.reports) == 0:
            self.reports.append(report)

        for odj in self.reports:
            if odj.get('id_user') == report.get('id_user'):
                odj['answers'] = report['answers']
            else:
                self.reports.append(report)
        DBController.update_reports(channel, self.reports, ts_reports)
        return self.reports
