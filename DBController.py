import pymongo
from pymongo import MongoClient
import uuid
from pprint import pprint


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
    def add_group(cls, group, uuid):
        cls.groups.insert_one({**group,
                               '_id': uuid,
                               'serial_id': 0}
                              )

    @classmethod
    def get_group(cls, serial_id) -> dict:
        return cls.groups.find_one({'serial_id': serial_id})

    @classmethod
    def get_all_groups(cls, filter_fields=None):
        filter_fields = filter_fields if filter_fields else dict()
        groups = cls.groups.find(filter_fields).sort('serial_id', pymongo.ASCENDING)
        return groups


if __name__ == '__main__':
    DBController.first_setup()

    ts = '12341234'
    group = {'channel': '111',
             'users': ['Kate', 'Liza'],
             'times': {"weekdays": ['Fr', 'Mon'],
                       "times": '10.00'},
             "reports": [{'id_user': 'str',
                          'answers': [('What did you do yesterday?', 'work', ts),
                                      ('What are you planning do today?', 'rest', ts),
                                      ('Any promlem?', 'No', ts)
                                      ]
                          },
                         {'id_user': 'str',
                          'answers': [('What did you do yesterday?', 'love', ts),
                                      ('What are you planning do today?', 'work', ts),
                                      ('Any promlem?', 'No', ts)
                                      ]
                          }
                         ],
             "ts_report": '45674567'
             }

    DBController.add_group(group, str(uuid.uuid4()))
    pprint(DBController.get_group(0))
