#!/usr/bin/python
# message_database.py
#
# Copyright (C) 2008 Veselin Penev, https://bitdust.io
#
# This file (message_database.py) is part of BitDust Software.
#
# BitDust is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# BitDust Software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with BitDust Software.  If not, see <http://www.gnu.org/licenses/>.
#
# Please contact us if you have any questions at bitdust.io@gmail.com
#
#
#
#

"""
..

module:: message_database
"""

#------------------------------------------------------------------------------

from __future__ import absolute_import
from __future__ import print_function
from six.moves import map  # @UnresolvedImport
import six

#------------------------------------------------------------------------------

_Debug = False
_DebugLevel = 6

#------------------------------------------------------------------------------

import os
import json
import sqlite3

#------------------------------------------------------------------------------

if __name__ == '__main__':
    import sys
    import os.path as _p
    sys.path.insert(0, _p.abspath(_p.join(_p.dirname(_p.abspath(sys.argv[0])), '..')))

#------------------------------------------------------------------------------

from logs import lg

from lib import utime
from lib import strng

from main import settings

from userid import my_id

#------------------------------------------------------------------------------

_HistoryDB = None
_HistoryCursor = None
_LocalStorage = None

#------------------------------------------------------------------------------

MESSAGE_TYPES = {
    'message': 1,
    'private_message': 2,
    'group_message': 3,
}

MESSAGE_TYPE_CODES = {
    1: 'message',
    2: 'private_message',
    3: 'group_message',
}

#------------------------------------------------------------------------------

def init(filepath=None):
    """
    """
    global _HistoryDB
    global _HistoryCursor

    if not filepath:
        filepath = settings.ChatMessagesHistoryDatabaseFile()

    if _Debug:
        lg.args(_DebugLevel, filepath=filepath)

    sqlite3.register_adapter(dict, adapt_json)
    sqlite3.register_adapter(list, adapt_json)
    sqlite3.register_adapter(tuple, adapt_json)
    sqlite3.register_converter('JSON', convert_json)

    if not os.path.isfile(filepath):
        _HistoryDB = sqlite3.connect(filepath, timeout=1)
        _HistoryDB.execute('PRAGMA case_sensitive_like = 1;')
        _HistoryCursor = _HistoryDB.cursor()
        _HistoryCursor.execute('''CREATE TABLE IF NOT EXISTS "history" (
            "sender_glob_id" TEXT,
            "recipient_glob_id" TEXT,
            "payload_type" INTEGER,
            "payload_time" INTEGER,
            "payload_message_id" TEXT,
            "payload_body" JSON)''')
        _HistoryCursor.execute('CREATE INDEX "sender glob id" on history(sender_glob_id)')
        _HistoryDB.commit()
        _HistoryDB.close()

    _HistoryDB = sqlite3.connect(filepath, timeout=1)
    _HistoryDB.text_factory = str
    _HistoryDB.execute('PRAGMA case_sensitive_like = 1;')
    _HistoryCursor = _HistoryDB.cursor()


def shutdown():
    """
    """
    global _HistoryDB
    global _HistoryCursor
    _HistoryDB.commit()
    _HistoryDB.close()
    if _Debug:
        lg.dbg(_DebugLevel, '')

#------------------------------------------------------------------------------

def db(instance='current'):
    global _HistoryDB
    return _HistoryDB


def cur(instance='current'):
    global _HistoryCursor
    return _HistoryCursor

#------------------------------------------------------------------------------

def adapt_json(data):
    return (json.dumps(data, sort_keys=True)).encode()

def convert_json(blob):
    return json.loads(blob.decode())

#------------------------------------------------------------------------------

def build_json_message(data, message_id, message_time=None, sender=None, recipient=None, message_type=None, direction=None):
    """
    """
    if not sender:
        sender = my_id.getGlobalID(key_alias='master')
    if not recipient:
        recipient = my_id.getGlobalID(key_alias='master')
    new_json = {
        "payload": {
            "type": message_type or "message",
            "message_id": strng.to_text(message_id),
            "time": message_time or utime.utcnow_to_sec1970(),
            "data": data,
        },
        'sender': {
            'glob_id': sender,
        },
        'recipient': {
            'glob_id': recipient,
        },
        'direction': direction,
    }
    return new_json

#------------------------------------------------------------------------------

def insert(message_json):
    """
    """
    try:
        sender_glob_id = message_json['sender']['glob_id']
        recipient_glob_id = message_json['recipient']['glob_id']
        payload_type = MESSAGE_TYPES.get(message_json['payload']['type'], 1)
        payload_time = message_json['payload']['time']
        payload_message_id = message_json['payload']['message_id']
        payload_body =  message_json['payload']['data']
        # TODO: store "direction"
        direction = message_json['direction']
    except:
        lg.exc()
        return False
    if _Debug:
        lg.args(_DebugLevel, sender=sender_glob_id, recipient=recipient_glob_id, typ=payload_type, message_id=payload_message_id)
    cur().execute('''INSERT INTO history (
            sender_glob_id,
            recipient_glob_id,
            payload_type,
            payload_time,
            payload_message_id,
            payload_body
        ) VALUES  (?, ?, ?, ?, ?, ?)''', (
        sender_glob_id,
        recipient_glob_id,
        payload_type,
        payload_time,
        payload_message_id,
        payload_body,
    ))
    db().commit()
    return True


def query(sender_id=None, recipient_id=None, bidirectional=True, order_by_time=True, message_types=[], offset=None, limit=None):
    """
    """
    sql = 'SELECT * FROM history WHERE'
    params = []
    if bidirectional and sender_id and recipient_id:
        sql += ' sender_glob_id IN (?, ?) AND recipient_glob_id IN (?, ?)'
        params += [sender_id, recipient_id, sender_id, recipient_id, ]
    else:
        if sender_id:
            sql += ' sender_glob_id=?'
            params += [sender_id, ]
        if recipient_id:
            sql += ' recipient_glob_id=?'
            params += [recipient_id, ]
    if message_types:
        if params:
            sql += ' AND payload_type IN (%s)' % (','.join(['?', ] * len(message_types)))
        else:
            sql += ' payload_type IN (%s)' % (','.join(['?', ] * len(message_types)))
        params.extend([MESSAGE_TYPES.get(mt, 1) for mt in message_types])
    if order_by_time:
        sql += ' ORDER BY payload_time DESC'
    if limit is not None:
        sql += ' LIMIT ?'
        params += [limit, ]
    if offset is not None:
        sql += ' OFFSET ?'
        params += [offset, ]
    if _Debug:
        lg.args(_DebugLevel, sql=repr(sql), params=repr(params))
    for row in cur().execute(sql, params):
        yield build_json_message(
            data=json.loads(row[5]),
            message_id=row[4],
            message_time=row[3],
            sender=row[0],
            recipient=row[1],
        )

#------------------------------------------------------------------------------

def main():
    import pprint
    init()
    pprint.pprint(list(query(
        sender_id='master$alice@abc.com',
        recipient_id='master$bob@xyz.prg',
        # offset=4,
        # limit=3,
    )))
    shutdown()


if __name__ == "__main__":
    lg.set_debug_level(20)
    main()
