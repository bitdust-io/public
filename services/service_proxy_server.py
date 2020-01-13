#!/usr/bin/python
# service_proxy_server.py
#
# Copyright (C) 2008 Veselin Penev, https://bitdust.io
#
# This file (service_proxy_server.py) is part of BitDust Software.
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

module:: service_proxy_server
"""

from __future__ import absolute_import
from services.local_service import LocalService


def create_service():
    return ProxyServerService()


class ProxyServerService(LocalService):

    service_name = 'service_proxy_server'
    config_path = 'services/proxy-server/enabled'

    def dependent_on(self):
        return [
            'service_p2p_hookups',
        ]

    def enabled(self):
        from main import settings
        if settings.transportIsEnabled('proxy'):
            return False
        return settings.enableProxyServer()

    def start(self):
        from logs import lg
        from services import driver
        from main import events
        from transport.proxy import proxy_router
        proxy_router.A('init')
        proxy_router.A('start')
        if driver.is_on('service_entangled_dht'):
            self._do_connect_proxy_routers_dht_layer()
        else:
            lg.warn('service service_entangled_dht is OFF')
        events.add_subscriber(self._on_dht_layer_connected, event_id='dht-layer-connected')
        return True

    def stop(self):
        from services import driver
        from main import events
        from transport.proxy import proxy_router
        events.remove_subscriber(self._on_dht_layer_connected, event_id='dht-layer-connected')
        proxy_router.A('stop')
        proxy_router.A('shutdown')
        if driver.is_on('service_entangled_dht'):
            from dht import dht_service
            from dht import dht_records
            dht_service.suspend(layer_id=dht_records.LAYER_PROXY_ROUTERS)
        return True

    def request(self, json_payload, newpacket, info):
        from transport.proxy import proxy_router
        proxy_router.A('request-route-received', (json_payload, newpacket, info, ))
        return True

    def cancel(self, json_payload, newpacket, info):
        from transport.proxy import proxy_router
        proxy_router.A('cancel-route-received', (json_payload, newpacket, info, ))
        return True

    def _do_connect_proxy_routers_dht_layer(self):
        from logs import lg
        from dht import dht_service
        from dht import dht_records
        from dht import known_nodes
        known_seeds = known_nodes.nodes()
        d = dht_service.connect(
            seed_nodes=known_seeds,
            layer_id=dht_records.LAYER_PROXY_ROUTERS,
            attach=True,
        )
        d.addCallback(self._on_dht_proxy_routers_layer_connected)
        d.addErrback(lambda *args: lg.err(str(args)))

    def _on_dht_proxy_routers_layer_connected(self, ok):
        from logs import lg
        from dht import dht_service
        from dht import dht_records
        from userid import my_id
        lg.info('connected to DHT layer for proxy routers: %r' % ok)
        if my_id.getLocalID():
            dht_service.set_node_data('idurl', my_id.getLocalID().to_text(), layer_id=dht_records.LAYER_PROXY_ROUTERS)
        return 

    def _on_dht_layer_connected(self, evt):
        if evt.data['layer_id'] == 0:
            self._do_connect_proxy_routers_dht_layer()
