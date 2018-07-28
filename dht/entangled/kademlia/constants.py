#!/usr/bin/env python
# constants.py
#
# Copyright (C) 2008-2018 Veselin Penev, https://bitdust.io
#
# This file (constants.py) is part of BitDust Software.
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
# This library is free software, distributed under the terms of
# the GNU Lesser General Public License Version 3, or any later version.
# See the COPYING file included in this archive
#
# The docstrings in this module contain epytext markup; API documentation
# may be created by processing this file with epydoc: http://epydoc.sf.net

"""
This module defines the charaterizing constants of the Kademlia network.

C{checkRefreshInterval} and C{udpDatagramMaxSize} are implementation-
specific constants, and do not affect general Kademlia operation.
"""

######### KADEMLIA CONSTANTS ###########

#: Small number Representing the degree of parallelism in network calls
alpha = 3

#: Maximum number of contacts stored in a bucket; this should be an even number
k = 8

#: Timeout for network operations (in seconds)
rpcTimeout = 5

# Delay between iterations of iterative node lookups (for loose parallelism)  (in seconds)
iterativeLookupDelay = rpcTimeout / 2

#: If a k-bucket has not been used for this amount of time, refresh it (in seconds)
refreshTimeout = 3600  # 1 hour
#: The interval at which nodes replicate (republish/refresh) data they are holding
replicateInterval = refreshTimeout
# The time it takes for data to expire in the network; the original publisher of the data
# will also republish the data at this time if it is still valid
dataExpireTimeout = 86400  # 24 hours
# Default value for all records to be expired
dataExpireSecondsDefaut = 60 * 60 * 12  # 12 hours

######## IMPLEMENTATION-SPECIFIC CONSTANTS ###########

#: The interval in which the node should check its whether any buckets need refreshing,
#: or whether any data needs to be republished (in seconds)
checkRefreshInterval = refreshTimeout / 5

#: Max size of a single UDP datagram, in bytes. If a message is larger than this, it will
#: be spread accross several UDP packets.
udpDatagramMaxSize = 8192  # 8 KB
