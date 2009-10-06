#!/usr/bin/python
#
# Copyright 2009, Robby Walker
#
# rss-shortener/server.py
# The RSS shortener server.


import feedparser
import optparse
import tornado.httpclient
import tornado.httpserver
import tornado.ioloop
import tornado.web
import xml.sax
import xml.sax.saxutils

import stats


class RSSShortener(xml.sax.saxutils.XMLGenerator):
	"""SAX handler that only returns the first count RSS item elements."""
	def __init__(self, output, count):
		xml.sax.saxutils.XMLGenerator.__init__(self, output)
		self._item_count = 0
		self._max_count = count
		self._skip_depth = 0
		
	def startElement(self, name, attrs):
		if self._skip_depth:
			self._skip_depth += 1
			return
		elif name == 'item':
			if self._item_count < self._max_count:
				self._item_count += 1
			else:
				self._skip_depth = 1
				return
		xml.sax.saxutils.XMLGenerator.startElement(self, name, attrs)
		
	def startElementNS(self, name, qname, attrs):
		if self._skip_depth:
			self._skip_depth += 1
		else:
			xml.sax.saxutils.XMLGenerator.startElementNS(self, name, qname, attrs)
		
	def endElement(self, name):
		if self._skip_depth:
			self._skip_depth -= 1
		else:
			xml.sax.saxutils.XMLGenerator.endElement(self, name)
			
	def endElementNS(self, name, qname):
		if self._skip_depth:
			self._skip_depth -= 1
		else:
			xml.sax.saxutils.XMLGenerator.endElementNS(self, name, qname)
			
	def characters(self, content):
		if not self._skip_depth:
			xml.sax.saxutils.XMLGenerator.characters(self, content)		
	

class RSSShorteningProxyHandler(tornado.web.RequestHandler):
	"""Proxies requests from the given server and returns shortened versions of RSS."""
	def __init__(self, application, request, name, server, statsCollection):
		tornado.web.RequestHandler.__init__(self, application, request)

		self._errorMessageStats = statsCollection.category('errorMessage:' + name)
		self._errorPageStats = statsCollection.category('errorPage:' + name)
		self._errorStat = statsCollection.counter('errors')
		self._segmentedErrorStat = statsCollection.counter('errors:' + name)

		self._okStat = statsCollection.counter('oks')
		self._segmentedOkStat = statsCollection.counter('oks:' + name)
		self._okPageStats = statsCollection.category('okPage:' + name)

		self._server = server
	
	@tornado.web.asynchronous
	def get(self, path):
		http = tornado.httpclient.AsyncHTTPClient()
		http.fetch(self._server + path,
				callback=self.async_callback(self.on_response, path))
		
	def on_response(self, requestPath, response):
		if response.error:
			self._errorStat.increment()
			self._segmentedErrorStat.increment()
			self._errorMessageStats.increment(response.error)
			self._errorPageStats.increment(requestPath)

			raise tornado.web.HTTPError(500)
			
		xml.sax.parseString(response.body,
				RSSShortener(self, int(self.get_argument('count', default = 3))))

		self._okStat.increment()
		self._segmentedOkStat.increment()
		self._okPageStats.increment(requestPath)

		self.finish()


class StatusHandler(tornado.web.RequestHandler):
	"""Simple handler that returns ok, used to ensure the server is alive."""
	def get(self):
		self.write("ok")


if __name__ == "__main__":
	parser = optparse.OptionParser()
	parser.add_option("-p", "--port", dest="port", type="int", default=8888,
	                  help="start on port PORT", metavar="PORT")

	(options, args) = parser.parse_args()

	statsCollection = stats.Collection()
	application = tornado.web.Application([
		(r"/reddit/(.*)", RSSShorteningProxyHandler, {
			'name': 'reddit',
			'server': 'http://www.reddit.com/',
			'statsCollection': statsCollection
		}),
		(r"/yc/(.*)", RSSShorteningProxyHandler, {
			'name': 'yc',
			'server': 'http://news.ycombinator.com/',
			'statsCollection': statsCollection
		}),
		(r"/_/stats", stats.RequestHandler, {
			'statsCollection': statsCollection
		}),
		(r"/_/status", StatusHandler)
	])
	
	print "Listening on port " + str(options.port);
	http_server = tornado.httpserver.HTTPServer(application)
	http_server.listen(options.port)
	tornado.ioloop.IOLoop.instance().start()
