#!/usr/bin/env python
# routingtable.py
#
# Copyright (C) 2007-2008 Francois Aucamp, Meraka Institute, CSIR
# See AUTHORS for all authors and contact information.
#
# License: GNU Lesser General Public License, version 3 or later; see COPYING
#          included in this archive for details.
#
# This library is free software, distributed under the terms of
# the GNU Lesser General Public License Version 3, or any later version.
# See the COPYING file included in this archive
#
# The docstrings in this module contain epytext markup; API documentation
# may be created by processing this file with epydoc: http://epydoc.sf.net

from __future__ import absolute_import
from __future__ import print_function
import time
import random

from . import constants  # @UnresolvedImport
from . import kbucket  # @UnresolvedImport
from .protocol import TimeoutError  # @UnresolvedImport

_Debug = False


class RoutingTable(object):
    """
    Interface for RPC message translators/formatters.

    Classes inheriting from this should provide a suitable routing table
    for a parent Node object (i.e. the local entity in the Kademlia
    network)
    """
    def __init__(self, parentNodeID):
        """
        @param parentNodeID: The 160-bit node ID of the node to which this
                             routing table belongs
        @type parentNodeID: str
        """

    def addContact(self, contact):
        """
        Add the given contact to the correct k-bucket; if it already exists,
        its status will be updated.

        @param contact: The contact to add to this node's k-buckets
        @type contact: kademlia.contact.Contact
        """

    def distance(self, keyOne, keyTwo):
        """
        Calculate the XOR result between two string variables.

        @return: XOR result of two long variables
        @rtype: long
        """
        valKeyOne = int(keyOne, 16)
        valKeyTwo = int(keyTwo, 16)
        return valKeyOne ^ valKeyTwo

    def findCloseNodes(self, key, count, _rpcNodeID=None):
        """
        Finds a number of known nodes closest to the node/value with the
        specified key.

        @param key: the 160-bit key (i.e. the node or value ID) to search for
        @type key: str
        @param count: the amount of contacts to return
        @type count: int
        @param _rpcNodeID: Used during RPC, this is be the sender's Node ID
                           Whatever ID is passed in the parameter will get
                           excluded from the list of returned contacts.
        @type _rpcNodeID: str

        @return: A list of node contacts (C{kademlia.contact.Contact instances})
                 closest to the specified key.
                 This method will return C{k} (or C{count}, if specified)
                 contacts if at all possible; it will only return fewer if the
                 node is returning all of the contacts that it knows of.
        @rtype: list
        """

    def getContact(self, contactID):
        """
        Returns the (known) contact with the specified node ID.

        @raise ValueError: No contact with the specified contact ID is known
                           by this node
        """

    def getRefreshList(self, startIndex=0, force=False):
        """
        Finds all k-buckets that need refreshing, starting at the k-bucket with
        the specified index, and returns IDs to be searched for in order to
        refresh those k-buckets.

        @param startIndex: The index of the bucket to start refreshing at;
                           this bucket and those further away from it will
                           be refreshed. For example, when joining the
                           network, this node will set this to the index of
                           the bucket after the one containing it's closest
                           neighbour.
        @type startIndex: index
        @param force: If this is C{True}, all buckets (in the specified range)
                      will be refreshed, regardless of the time they were last
                      accessed.
        @type force: bool

        @return: A list of node ID's that the parent node should search for
                 in order to refresh the routing Table
        @rtype: list
        """

    def removeContact(self, contactID):
        """
        Remove the contact with the specified node ID from the routing table.

        @param contactID: The node ID of the contact to remove
        @type contactID: str
        """

    def touchKBucket(self, key):
        """
        Update the "last accessed" timestamp of the k-bucket which covers the
        range containing the specified key in the key/ID space.

        @param key: A key in the range of the target k-bucket
        @type key: str
        """


class TreeRoutingTable(RoutingTable):
    """
    This class implements a routing table used by a Node class.

    The Kademlia routing table is a binary tree whose leaves are k-buckets,
    where each k-bucket contains nodes with some common prefix of their IDs.
    This prefix is the k-bucket's position in the binary tree; it therefore
    covers some range of ID values, and together all of the k-buckets cover
    the entire 160-bit ID (or key) space (with no overlap).

    @note: In this implementation, nodes in the tree (the k-buckets) are
    added dynamically, as needed; this technique is described in the 13-page
    version of the Kademlia paper, in section 2.4. It does, however, use the
    C{PING} RPC-based k-bucket eviction algorithm described in section 2.2 of
    that paper.
    """
    def __init__(self, parentNodeID, **kwargs):
        """
        @param parentNodeID: The 160-bit node ID of the node to which this
                             routing table belongs
        @type parentNodeID: str
        """
        # Create the initial (single) k-bucket covering the range of the entire 160-bit ID space
        self._buckets = [
            kbucket.KBucket(rangeMin=0, rangeMax=2**160),
        ]
        self._parentNodeID = parentNodeID
        self._layerID = kwargs.get('layerID', 0)

    def __repr__(self, *args, **kwargs):
        return str(self)

    def __str__(self):
        return '<RTable(%d) %d buckets for %r>' % (self._layerID, len(self._buckets), self._parentNodeID)

    def totalContacts(self):
        counter = 0
        for bucket in self._buckets:
            counter += len(bucket._contacts)
        return counter

    def addContact(self, contact):
        """
        Add the given contact to the correct k-bucket; if it already exists,
        its status will be updated.

        @param contact: The contact to add to this node's k-buckets
        @type contact: kademlia.contact.Contact
        """
        if contact.id == self._parentNodeID:
            return

        bucketIndex = self._kbucketIndex(contact.id)
        try:
            self._buckets[bucketIndex].addContact(contact)
            if _Debug:
                print('[DHT RTABLE] layerID=%d   added %r to bucket %d' % (self._layerID, contact, bucketIndex))
        except kbucket.BucketFull:
            # The bucket is full; see if it can be split (by checking if its range includes the host node's id)
            if self._buckets[bucketIndex].keyInRange(self._parentNodeID):
                self._splitBucket(bucketIndex)
                # Retry the insertion attempt
                self.addContact(contact)
            else:
                # We can't split the k-bucket
                # NOTE:
                # In section 2.4 of the 13-page version of the Kademlia paper, it is specified that
                # in this case, the new contact should simply be dropped. However, in section 2.2,
                # it states that the head contact in the k-bucket (i.e. the least-recently seen node)
                # should be pinged - if it does not reply, it should be dropped, and the new contact
                # added to the tail of the k-bucket. This implementation follows section 2.2 regarding
                # this point.
                headContact = self._buckets[bucketIndex]._contacts[0]

                def replaceContact(failure):
                    """
                    Callback for the deferred PING RPC to see if the head node
                    in the k-bucket is still responding.

                    @type failure: twisted.python.failure.Failure
                    """
                    failure.trap(TimeoutError)
                    # Remove the old contact...
                    deadContactID = failure.getErrorMessage()
                    if _Debug:
                        print('[DHT RTABLE] layerID=%d   replacing dead contact %r' % (
                            self._layerID,
                            deadContactID,
                        ), )
                    try:
                        self._buckets[bucketIndex].removeContact(deadContactID)
                    except ValueError:
                        # The contact has already been removed (probably due to a timeout)
                        pass
                    # ...and add the new one at the tail of the bucket
                    self.addContact(contact)

                # Ping the least-recently seen contact in this k-bucket
                headContact = self._buckets[bucketIndex]._contacts[0]
                df = headContact.ping()
                # If there's an error (i.e. timeout), remove the head contact, and append the new one
                df.addErrback(replaceContact)

    def findCloseNodes(self, key, count, _rpcNodeID=None):
        """
        Finds a number of known nodes closest to the node/value with the
        specified key.

        @param key: the 160-bit key (i.e. the node or value ID) to search for
        @type key: str
        @param count: the amount of contacts to return
        @type count: int
        @param _rpcNodeID: Used during RPC, this is be the sender's Node ID
                           Whatever ID is passed in the paramater will get
                           excluded from the list of returned contacts.
        @type _rpcNodeID: str

        @return: A list of node contacts (C{kademlia.contact.Contact instances})
                 closest to the specified key.
                 This method will return C{k} (or C{count}, if specified)
                 contacts if at all possible; it will only return fewer if the
                 node is returning all of the contacts that it knows of.
        @rtype: list
        """
        # if key == self.id:
        #    bucketIndex = 0 #TODO: maybe not allow this to continue?
        # else:
        bucketIndex = self._kbucketIndex(key)

        if _Debug:
            print('[DHT RTABLE] layerID=%d   findCloseNodes %r   _rpcNodeID=%r   bucketIndex=%d buckets=%d' % (
                self._layerID,
                key,
                _rpcNodeID if _rpcNodeID else None,
                bucketIndex,
                len(self._buckets),
            ))

        closestNodes = self._buckets[bucketIndex].getContacts(constants.k, _rpcNodeID)
        # This method must return k contacts (even if we have the node with the specified key as node ID),
        # unless there is less than k remote nodes in the routing table
        i = 1
        canGoLower = bucketIndex - i >= 0
        canGoHigher = bucketIndex + i < len(self._buckets)
        # Fill up the node list to k nodes, starting with the closest neighbouring nodes known
        while len(closestNodes) < constants.k and (canGoLower or canGoHigher):
            if _Debug:
                print('[DHT RTABLE] layerID=%d  closestNodes=%r' % (
                    self._layerID,
                    closestNodes,
                ))
            # TODO: this may need to be optimized
            more_contacts = []
            if canGoLower:
                more_contacts = self._buckets[bucketIndex - i].getContacts(constants.k - len(closestNodes), _rpcNodeID)
                closestNodes.extend(more_contacts)
                canGoLower = bucketIndex - (i + 1) >= 0
            if canGoHigher:
                more_contacts = self._buckets[bucketIndex + i].getContacts(constants.k - len(closestNodes), _rpcNodeID)
                closestNodes.extend(more_contacts)
                canGoHigher = bucketIndex + (i + 1) < len(self._buckets)
            i += 1
            if _Debug:
                print('[DHT RTABLE] layerID=%d   canGoLower=%s canGoHigher=%s more_contacts=%r' % (
                    self._layerID,
                    canGoLower,
                    canGoHigher,
                    more_contacts,
                ))
        if _Debug:
            print('[DHT RTABLE] layerID=%d   result=%r' % (
                self._layerID,
                closestNodes,
            ))
        return closestNodes

    def getContact(self, contactID):
        """
        Returns the (known) contact with the specified node ID.

        @raise ValueError: No contact with the specified contact ID is known
                           by this node
        """
        bucketIndex = self._kbucketIndex(contactID)
        try:
            contact = self._buckets[bucketIndex].getContact(contactID)
        except ValueError:
            raise
        else:
            return contact

    def getRefreshList(self, startIndex=0, force=False):
        """
        Finds all k-buckets that need refreshing, starting at the k-bucket with
        the specified index, and returns IDs to be searched for in order to
        refresh those k-buckets.

        @param startIndex: The index of the bucket to start refreshing at;
                           this bucket and those further away from it will
                           be refreshed. For example, when joining the
                           network, this node will set this to the index of
                           the bucket after the one containing it's closest
                           neighbour.
        @type startIndex: index
        @param force: If this is C{True}, all buckets (in the specified range)
                      will be refreshed, regardless of the time they were last
                      accessed.
        @type force: bool

        @return: A list of node ID's that the parent node should search for
                 in order to refresh the routing Table
        @rtype: list
        """
        bucketIndex = startIndex
        refreshIDs = []
        for bucket in self._buckets[startIndex:]:
            if force or (int(time.time()) - bucket.lastAccessed >= constants.refreshTimeout):
                searchID = self._randomIDInBucketRange(bucketIndex)
                refreshIDs.append(searchID)
            bucketIndex += 1
        return refreshIDs

    def removeContact(self, contactID):
        """
        Remove the contact with the specified node ID from the routing table.

        @param contactID: The node ID of the contact to remove
        @type contactID: str
        """
        bucketIndex = self._kbucketIndex(contactID)
        try:
            self._buckets[bucketIndex].removeContact(contactID)
            if _Debug:
                print('[DHT RTABLE] layerID=%d   removeContact(%r) from bucket %d' % (self._layerID, contactID, bucketIndex))
        except ValueError:
            if _Debug:
                print('[DHT RTABLE] layerID=%d   removeContact(%r): Contact not in routing table bucketIndex=%r' % (self._layerID, contactID, bucketIndex))
            return

    def touchKBucket(self, key):
        """
        Update the "last accessed" timestamp of the k-bucket which covers the
        range containing the specified key in the key/ID space.

        @param key: A key in the range of the target k-bucket
        @type key: str
        """
        bucketIndex = self._kbucketIndex(key)
        self._buckets[bucketIndex].lastAccessed = int(time.time())

    def _kbucketIndex(self, key):
        """
        Calculate the index of the k-bucket which is responsible for the
        specified key (or ID)

        @param key: The key for which to find the appropriate k-bucket index
        @type key: str

        @return: The index of the k-bucket responsible for the specified key
        @rtype: int
        """
        valKey = int(key, 16)
        i = 0
        for bucket in self._buckets:
            if bucket.keyInRange(valKey):
                # if _Debug:
                #     print('[DHT RTABLE] _kbucketIndex  %r  %r  returning %r' % (key, valKey, i, ))
                return i
            else:
                i += 1
        # if _Debug:
        #     print('[DHT RTABLE] _kbucketIndex  %r  %r  finishing with %r' % (key, valKey, i, ))
        return i

    def _randomIDInBucketRange(self, bucketIndex):
        """
        Returns a random ID in the specified k-bucket's range.

        @param bucketIndex: The index of the k-bucket to use
        @type bucketIndex: int
        """
        idValue = random.randrange(self._buckets[bucketIndex].rangeMin, self._buckets[bucketIndex].rangeMax)
        randomID = hex(idValue)[2:]
        if randomID[-1] == 'L':
            randomID = randomID[:-1]
        if len(randomID) % 2 != 0:
            randomID = '0' + randomID
        randomID = (40 - len(randomID))*'0' + randomID
        return randomID

    def _splitBucket(self, oldBucketIndex):
        """
        Splits the specified k-bucket into two new buckets which together cover
        the same range in the key/ID space.

        @param oldBucketIndex: The index of k-bucket to split (in this table's
                               list of k-buckets)
        @type oldBucketIndex: int
        """
        # Resize the range of the current (old) k-bucket
        oldBucket = self._buckets[oldBucketIndex]
        oldCount = len(oldBucket)
        splitPoint = oldBucket.rangeMax - (oldBucket.rangeMax - oldBucket.rangeMin)/2
        # Create a new k-bucket to cover the range split off from the old bucket
        newBucket = kbucket.KBucket(splitPoint, oldBucket.rangeMax)
        oldBucket.rangeMax = splitPoint
        # Now, add the new bucket into the routing table tree
        self._buckets.insert(oldBucketIndex + 1, newBucket)
        # Finally, copy all nodes that belong to the new k-bucket into it...
        for contact in oldBucket._contacts:
            if newBucket.keyInRange(contact.id):
                newBucket.addContact(contact)
        # ...and remove them from the old bucket
        for contact in newBucket._contacts:
            oldBucket.removeContact(contact)
        if _Debug:
            print('[DHT RTABLE] layerID=%d   split bucket %d,    old: %d     new: %d / %d' % (
                self._layerID,
                oldBucketIndex,
                oldCount,
                len(oldBucket),
                len(newBucket),
            ))


class OptimizedTreeRoutingTable(TreeRoutingTable):
    """
    A version of the "tree"-type routing table specified by Kademlia, along
    with contact accounting optimizations specified in section 4.1 of of the
    13-page version of the Kademlia paper.
    """
    def __init__(self, parentNodeID):
        TreeRoutingTable.__init__(self, parentNodeID)
        # Cache containing nodes eligible to replace stale k-bucket entries
        self._replacementCache = {}

    def addContact(self, contact):
        """
        Add the given contact to the correct k-bucket; if it already exists,
        its status will be updated.

        @param contact: The contact to add to this node's k-buckets
        @type contact: kademlia.contact.Contact
        """

        if contact.id == self._parentNodeID:
            return

        # Initialize/reset the "successively failed RPC" counter
        contact.failedRPCs = 0

        bucketIndex = self._kbucketIndex(contact.id)
        if _Debug:
            print('[DHT RTABLE]   addContact %r at %r' % (contact.id, bucketIndex))
        try:
            self._buckets[bucketIndex].addContact(contact)
        except kbucket.BucketFull:
            if _Debug:
                print('[DHT RTABLE]    BucketFull!')
            # The bucket is full; see if it can be split (by checking if its range includes the host node's id)
            if self._buckets[bucketIndex].keyInRange(self._parentNodeID):
                self._splitBucket(bucketIndex)
                # Retry the insertion attempt
                self.addContact(contact)
            else:
                # We can't split the k-bucket
                # NOTE: This implementation follows section 4.1 of the 13 page version
                # of the Kademlia paper (optimized contact accounting without PINGs
                #- results in much less network traffic, at the expense of some memory)

                # Put the new contact in our replacement cache for the corresponding k-bucket (or update it's position if it exists already)
                if bucketIndex not in self._replacementCache:
                    self._replacementCache[bucketIndex] = []
                if contact in self._replacementCache[bucketIndex]:
                    self._replacementCache[bucketIndex].remove(contact)
                # TODO: Using k to limit the size of the contact replacement cache - maybe define a seperate value for this in constants.py?
                elif len(self._replacementCache) >= constants.k:
                    self._replacementCache.pop(0)
                self._replacementCache[bucketIndex].append(contact)

    def removeContact(self, contactID):
        """
        Remove the contact with the specified node ID from the routing table.

        @param contactID: The node ID of the contact to remove
        @type contactID: str
        """
        bucketIndex = self._kbucketIndex(contactID)
        try:
            contact = self._buckets[bucketIndex].getContact(contactID)
        except ValueError:
            # print 'removeContact(): Contact not in routing table'
            return
        contact.failedRPCs += 1
        if contact.failedRPCs >= 5:
            self._buckets[bucketIndex].removeContact(contactID)
            # Replace this stale contact with one from our replacemnent cache, if we have any
            if bucketIndex in self._replacementCache:
                if len(self._replacementCache[bucketIndex]) > 0:
                    self._buckets[bucketIndex].addContact(self._replacementCache[bucketIndex].pop())
