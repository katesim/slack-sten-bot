import pymongo
from pymongo import MongoClient
import uuid
from pprint import pprint

from WorkGroup import WorkGroup


class DBController:
    mongo_client = MongoClient('mongo-db', 27017)
    db = mongo_client.worksgroups
    groups = db.groups
    counters = db.counters

    group_serial_id_sequence_key = 'group_serial_id'

    @classmethod
    def first_setup(cls):
        cls.counters.insert_one({'_id': cls.group_serial_id_sequence_key,
                                 'seq': 0}
                                )

    @classmethod
    def get_next_number_in_sequence(cls, name: str):
        number = cls.counters.find_one_and_update({'_id': name}, {'$inc': {'seq': 1}},
                                                  upsert=True, return_document=pymongo.ReturnDocument.AFTER)
        return number['seq']

    @classmethod
    def add_group(cls, group):
        cls.groups.insert_one({**group,
                               '_id': str(uuid.uuid4()),
                               'serial_id': 0}
                              )

    @classmethod
    def get_group(cls, filtered_field: dict) -> WorkGroup:
        if cls.groups.find_one(filtered_field):
            return WorkGroup(cls.groups.find_one(filtered_field))
        else:
            return None

    @classmethod
    def get_all_groups(cls, filter_fields=None):
        filter_fields = filter_fields if filter_fields else dict()
        groups = cls.groups.find(filter_fields).sort('serial_id', pymongo.ASCENDING)
        return groups

    @classmethod
    def remove_groups(cls, filter_fields=None):
        filter_fields = filter_fields if filter_fields else dict()
        cls.groups.remove(filter_fields)

    @classmethod
    def update_reports(cls, work_group: WorkGroup):
        cls.groups.update_one(
            {
                'channel': work_group.channel,
            },
            {'$set': {
                'reports': work_group.reports,
                'ts_reports': work_group.ts_reports
            },
            }
        )
        print('UPD REPORTS IN DB')

    @staticmethod
    def check_db_status():
        db_len = 0
        for _ in DBController.get_all_groups():
            db_len += 1
        if db_len == 0:
            print('First setup database...')
            DBController.first_setup()


if __name__ == '__main__':
    DBController.first_setup()
    DBController.add_group(group={})
    pprint(DBController.get_group({'serial_id':0}))
