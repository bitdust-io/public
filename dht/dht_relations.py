#!/usr/bin/python
# dht_relations.py
#
# Copyright (C) 2008-2018 Veselin Penev, https://bitdust.io
#
# This file (dht_relations.py) is part of BitDust Software.
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
.. module:: dht_relations

"""

#------------------------------------------------------------------------------

from __future__ import absolute_import

#------------------------------------------------------------------------------

_Debug = True
_DebugLevel = 8

#------------------------------------------------------------------------------

from twisted.internet.defer import Deferred  # @UnresolvedImport

#------------------------------------------------------------------------------

from logs import lg

from lib import strng

from dht import dht_records

from contacts import contactsdb

#------------------------------------------------------------------------------

def read_customer_suppliers(customer_idurl):
    result = Deferred()

    def _do_verify(dht_value):
        try:
            _ecc_map = dht_value['ecc_map']
            _customer_idurl = strng.to_bin(dht_value['customer_idurl'])
            _suppliers_list = list(map(strng.to_bin, dht_value['suppliers']))
            _revision = dht_value.get('revision')
            _publisher = dht_value.get('publisher')
            _timestamp = dht_value.get('timestamp')
        except:
            lg.exc()
            result.callback(None)
            return None
        ret = {
            'suppliers': _suppliers_list,
            'ecc_map': _ecc_map,
            'customer_idurl': _customer_idurl,
            'revision': _revision,
            'publisher': _publisher,
            'timestamp': _timestamp,
        }
        contactsdb.set_suppliers(_suppliers_list, customer_idurl=customer_idurl)
        contactsdb.save_suppliers(customer_idurl=customer_idurl)
        if _Debug:
            lg.out(_DebugLevel, 'dht_relations.read_customer_suppliers  %r  returned %r' % (customer_idurl, ret, ))
        result.callback(ret)
        return None

    def _on_error(err):
        if _Debug:
            lg.out(_DebugLevel, 'dht_relations.read_customer_suppliers  %r  failed with %r' % (customer_idurl, err, ))
        result.callback(None)
        return None

    d = dht_records.get_suppliers(customer_idurl)
    d.addCallback(_do_verify)
    d.addErrback(_on_error)
    return result


def write_customer_suppliers(customer_idurl, suppliers_list, ecc_map=None, revision=None, publisher=None, ):
    contactsdb.set_suppliers(suppliers_list, customer_idurl=customer_idurl)
    contactsdb.save_suppliers(customer_idurl=customer_idurl)
    return dht_records.set_suppliers(
        customer_idurl=customer_idurl,
        suppliers_list=suppliers_list,
        ecc_map=ecc_map,
        revision=revision,
        publisher=publisher,
    )
