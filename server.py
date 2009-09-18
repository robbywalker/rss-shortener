#!/usr/bin/python

import feedparser
import xml.sax
import xml.sax.saxutils
import tornado.httpclient
import tornado.httpserver
import tornado.ioloop
import tornado.web

class RSSShortener(xml.sax.saxutils.XMLGenerator):
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
	def __init__(self, application, request, server):
		tornado.web.RequestHandler.__init__(self, application, request)
		self._server = server
	
	@tornado.web.asynchronous
	def get(self, path):
		http = tornado.httpclient.AsyncHTTPClient()
		http.fetch(self._server + path,
				callback=self.async_callback(self.on_response))
		
	def on_response(self, response):
		if response.error:
			raise tornado.web.HTTPError(500)
		xml.sax.parseString(response.body,
				RSSShortener(self, int(self.get_argument('count', default = 3))))
		self.finish()		

application = tornado.web.Application([
	(r"/reddit/(.*)", RSSShorteningProxyHandler, {'server': 'http://www.reddit.com/'}),
	(r"/yc/(.*)", RSSShorteningProxyHandler, {'server': 'http://news.ycombinator.com/'}),
])

if __name__ == "__main__":
	http_server = tornado.httpserver.HTTPServer(application)
	http_server.listen(8888)
	tornado.ioloop.IOLoop.instance().start()