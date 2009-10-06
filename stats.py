#!/usr/bin/python
#
# Copyright 2009, Robby Walker
#
# rss-shortener/stats.py
# Stats collection for the RSS Shortener server.


import tornado.escape
import tornado.web


class Collection(object):
	"""A collection of stats."""

	def __init__(self):
		self._statObjects = {}
		self._stats = {}

	def asJson(self):
		"""Outputs the collection as JSON."""
		return tornado.escape.json_encode(self._stats)

	def counter(self, name):
		"""Returns the simple counter with the given name."""
		if name not in self._statObjects:
			self._statObjects[name] = SimpleCounter(self, name)
		elif not isinstance(self._statObjects[name], SimpleCounter):
			raise "Redefinition of stat with a different type " + name

		return self._statObjects[name]
		
	def category(self, name):
		"""Returns the categorized counter with the given name."""
		if name not in self._statObjects:
			self._statObjects[name] = Category(self, name)
		elif not isinstance(self._statObjects[name], Category):
			raise "Redefinition of stat with a different type " + name

		return self._statObjects[name]

	def increment(self, statName, amount = 1):
		"""Increments the given stat by the given amount.  Should not be used directly."""
		if statName in self._stats:
			self._stats[statName] += amount
		else:
			self._stats[statName] = amount


class SimpleCounter(object):
	"""A simple stat counter that just counts one stat forever."""
	def __init__(self, collection, name):
		self._name = name
		self._collection = collection
		
	def increment(self, amount = 1):
		self._collection.increment(self._name, amount)


class Category(object):
	"""A stat type that counts related statistics."""
	def __init__(self, collection, name):
		self._name = name
		self._collection = collection

	def increment(self, subStat, amount = 1):
		self._collection.increment('%s:%s' % (self._name, subStat), amount)


class RequestHandler(tornado.web.RequestHandler):
	"""A handler to display the current collection of stats as JSON."""
	def __init__(self, application, request, statsCollection):
		tornado.web.RequestHandler.__init__(self, application, request)
		self._collection = statsCollection
	
	def get(self):
		self.write(self._collection.asJson())
