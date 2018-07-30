"""
    Author        : Grzegorz Nowak
    Date created  : 10/07/2018
    Python Version: 3.5
"""
import time
import socket
import datetime
import argparse

from slackclient import SlackClient


parser = argparse.ArgumentParser()

parser.add_argument('--token'  , help='Provide your Slack APP token')
parser.add_argument('--channel', help='Provide you Slack notification channel')
parser.add_argument('--ip'     , help='IP address to verify')
parser.add_argument('--logfile', help='Log file with IP store')

args          = parser.parse_args()
slack_token   = args.token
slack_channel = args.channel
log_file      = args.logfile
audit_ips     = [args.ip]  # sink into array for lisp-like approach further on


sc = SlackClient(slack_token)

LOGS_PER_CALL = 1000

def lookupIp(anIp):
	pages_query = sc.api_call(
		"team.accessLogs",
		count="1"
	)
	pagesTotal = pages_query['paging']['total'] // LOGS_PER_CALL # we will be getting that many docs per call
	def filterALog(aLog):
		return aLog['ip'] == anIp

	head     = None
	username = None
	for page in range(pagesTotal):
		logs_call = sc.api_call(
			"team.accessLogs",
			count=LOGS_PER_CALL,
			page=page
		)
		head = next(iter(filter(filterALog,logs_call['logins'])), None)
		if head is not None:
			break

	if head is not None:
		username  = head['username']

	return { 'ip' : anIp, 'username': username, 'extra': head }


def isUserFound(userData):
	return userData['username'] is not None


## courtesy of @see https://stackoverflow.com/a/166589
def getPublicIp():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("8.8.8.8", 80))
	my_ip = s.getsockname()[0]
	s.close()
	return my_ip


def processFound(user):
	sc.api_call(
		"chat.postMessage",
		channel=slack_channel,
		text="A known person just logged in to one of our servers: *{}* (*{}*)".format(socket.gethostname(), getPublicIp()), #Found this ip on slack {}, and it beongs to user {}".format(user['ip'], user['username']),
		as_user=False,
		attachments=[{
			'text': "Found this ip on slack *{}*, and it belongs to *{}*".format(user['ip'], user['username']),
			'color': 'good',
			'mrkdwn_in': ['text'],
			'fields': [
				{ 'title': 'Date'   , 'value': str(datetime.datetime.now()), 'short': True },
				{ 'title': 'User IP', 'value': user['ip'], 'short': True },
				{ 'title': 'Agent'  , 'value': user['extra']['user_agent'] }
			]
		}]
	)


def processUnknown(user):
	sc.api_call(
		"chat.postMessage",
		channel=slack_channel,
		text="Warning! An unknown person just logged in to one of our servers: *{}* *{}*".format(socket.gethostname(), getPublicIp()), #Found this ip on slack {}, and it beongs to user {}".format(user['ip'], user['username']),
		as_user=False,
		attachments=[{
			'text': "NOT found this ip on slack *{}*".format(user['ip']),
			'color': 'danger',
			'mrkdwn_in': ['text'],
			'fields': [
				{ 'title': 'Date', 'value': str(datetime.datetime.now()), 'short': True },
				{ 'title': 'User IP', 'value': user['ip'], 'short': True }
			]
		}]
	)


def readIpFromStore(filepath):
	text_file = open(filepath, "a+")  	# make sure we try creating the file if not there yet
	text_file.seek(0)  					# re-point to the beginning (since the `a` mode)
	lines = text_file.readlines()
	text_file.close()
	return lines


def isInLogs(ip, logs):
	return len(list(filter(lambda stored_ip: ip in stored_ip, logs))) > 0


def saveToStore(ip, logs):
	with open(logs, "a") as logfile:
		logfile.write("{} {}\n".format(ip, time.time()))



stored_ips       = readIpFromStore(log_file)
mapped_entries   = list(filter(lambda ip: isInLogs(ip, stored_ips), audit_ips)) # [next(iter(filter(lambda stored_ip: audit_ip in stored_ip, stored_ips)), None) for audit_ip in audit_ips]
unmapped_entries = list(set(audit_ips) - set(mapped_entries))

lookedup_ips  = [lookupIp(ip) for ip in unmapped_entries]
found_users   = filter(isUserFound, lookedup_ips)
unknown_users = filter(lambda x: not isUserFound(x), lookedup_ips)

[processFound(user)   for user in list(found_users)]
[processUnknown(user) for user in list(unknown_users)]

[saveToStore(an_ip, log_file) for an_ip in unmapped_entries]
