#!/usr/bin/python
#
# Copyright 2009, Robby Walker
#
# rss-shortener/server.py
# Watchdog for the RSS shortener server.


from email.mime.text import MIMEText
import optparse
import smtplib
import subprocess


COMMAND_TEMPLATE = "service rss-shortener %s"

def status():
	return subprocess.call(COMMAND_TEMPLATE % "status")

def start():
	return subprocess.call(COMMAND_TEMPLATE % "start")

class GmailServer(object):
	def __init__(self, fromAddress, password):
		self._fromAddress = fromAddress
		
		self._mailServer = smtplib.SMTP('smtp.gmail.com', 587)
		self._mailServer.ehlo()
		self._mailServer.starttls()
		self._mailServer.ehlo()
		self._mailServer.login(fromAddress, password)

	def send(self, to, subject, text):
		msg = MIMEText(text)
		msg['Subject'] = subject
		msg['From'] = self._fromAddress
		msg['To'] = to
		
		self._mailServer.sendmail(self._fromAddress, [to], msg.as_string())
	
	def close(self):
		self._mailServer.close()


if __name__ == "__main__":
	parser = optparse.OptionParser()
	parser.add_option("-f", "--from", dest="fromAddress", type="string", default=None,
	                  help="send email from FROM", metavar="FROM")
	parser.add_option("-p", "--password", dest="password", type="string", default=None,
	                  help="login to gmail with PASSWORD", metavar="PASSWORD")
	parser.add_option("-t", "--to", dest="to", type="string", default=None,
	                  help="send email to TO", metavar="TO")
	(options, args) = parser.parse_args()

	message = []
	if not status():
		message.append('Server is not running.')
		if start():
			message.append('Restarted successfully')
		else:
			message.append('Server would not restart')

	if len(message):
		server = GmailServer(options.fromAddress, options.password)
		server.send(options.to, 'rss-shortener watchdog', '\n'.join(message))