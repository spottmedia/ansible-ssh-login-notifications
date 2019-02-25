"""
    Author        : Grzegorz Nowak (strange3studio@gmail.com)
    Date created  : 10/07/2018
    Python Version: 3.5
"""

import time
import utils
import socket
import datetime
import argparse

from slackclient import SlackClient


parser = argparse.ArgumentParser()

parser.add_argument('--token'  , help='Provide your Slack APP token')
parser.add_argument('--channel_logging', help='Provide you Slack logging notification channel (for known logins)')
parser.add_argument('--channel_alert'  , help='Provide you Slack alert notification channel (for unknown logins, can be same as for logging)')
parser.add_argument('--ip'     , help='IP address to verify')
parser.add_argument('--logfile', help='Log file with IP store')
parser.add_argument('--ts_threshold' , help='Expire stored IPs after this (amount in seconds)')
parser.add_argument('--known_ips'    , help='Provide a set of IPs that are known to be safe to ignore when reporting back')


args                  = parser.parse_args()
slack_token           = args.token
slack_channel_logging = args.channel_logging
slack_channel_alert   = args.channel_alert
log_file              = args.logfile
audit_ips             = [args.ip]  # sink into array for lisp-like approach further on
ts_threshold          = float(args.ts_threshold)


sc = SlackClient(slack_token)

LOGS_PER_CALL = 1000


def lookupIp(anIp):
	current_ts  = time.time()

	pages_query = sc.api_call(
		"team.accessLogs",
		count="1"
	)
	pagesTotal = pages_query['paging']['total'] // LOGS_PER_CALL # we will be getting that many docs per call

	def filterALog(a_log):
		return a_log['ip'] == anIp

	def withinThreshold(a_log):
		return current_ts < a_log['date_last'] + ts_threshold

	head     = None
	username = None
	for page in range(pagesTotal):
		logs_call = sc.api_call(
			"team.accessLogs",
			count=LOGS_PER_CALL,
			page=page
		)

		within_threshold = list(filter(withinThreshold, logs_call['logins']))
		head = next(iter(filter(filterALog,logs_call['logins'])), None)

		if head is not None or len(within_threshold) == 0:
			# either entry found, or we are past our threshold already - so just break
			break

	if head is not None:
		username  = head['username']

	return { 'ip' : anIp, 'username': username, 'extra': head }


def isUserFound(userData):
	return userData['username'] is not None


def processFound(user):
	sc.api_call(
		"chat.postMessage",
		channel=slack_channel_logging,
		text="A known person just logged in to one of our servers: *{}* (*{}*)".format(socket.gethostname(), utils.getPublicIp()), #Found this ip on slack {}, and it beongs to user {}".format(user['ip'], user['username']),
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
		channel=slack_channel_alert,
		text="Warning! An unknown person just logged in to one of our servers: *{}* *{}*".format(socket.gethostname(), utils.getPublicIp()), #Found this ip on slack {}, and it beongs to user {}".format(user['ip'], user['username']),
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


stored_ips       = utils.readIpFromStore(log_file, ts_threshold)
mapped_entries   = list(filter(lambda ip: utils.isInLogs(ip, stored_ips) or utils.isKnown(ip, known_ips), audit_ips))
unmapped_entries = list(set(audit_ips) - set(mapped_entries))

lookedup_ips  = [lookupIp(ip) for ip in unmapped_entries]
found_users   = filter(isUserFound, lookedup_ips)
unknown_users = filter(lambda x: not isUserFound(x), lookedup_ips)

[processFound(user)   for user in list(found_users)]
[processUnknown(user) for user in list(unknown_users)]

[utils.saveToStore(an_ip, log_file) for an_ip in unmapped_entries]
