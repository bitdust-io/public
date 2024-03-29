#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2011-2013 Codernity (http://codernity.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from gevent.lock import RLock  # @UnresolvedImport

from bitdust_forks.CodernityDB3.env import cdb_environment

cdb_environment['mode'] = "gevent"
cdb_environment['rlock_obj'] = RLock


# from CodernityDB3.database import Database
from bitdust_forks.CodernityDB3.database_safe_shared import SafeDatabase


class GeventDatabase(SafeDatabase):
    pass
