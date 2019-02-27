"""
    Author        : Grzegorz Nowak (strange3studio@gmail.com)
    Date created  : 10/07/2018
    Python Version: 3.5
"""

import json
import utils
import socket
import requests
import argparse

parser = argparse.ArgumentParser()

parser.add_argument('--keys'         , help='Provide the Audit App API keys')
parser.add_argument('--channel_logging', help='Provide you Slack logging notification channel (for known logins)')
parser.add_argument('--channel_alert', help='Provide you Slack alert notification channel (for unknown logins, can be same as for logging)')
parser.add_argument('--ip'           , help='IP address to verify')
parser.add_argument('--logfile'      , help='Log file with IP store')
parser.add_argument('--endpoint'     , help='Audit App endpoint')
parser.add_argument('--reporting_key', help='Separate report API key [optional]')
parser.add_argument('--ts_threshold' , help='Expire stored IPs after this (amount in seconds)')
parser.add_argument('--known_ips'    , help='Provide a set of IPs that are known to be safe to ignore when reporting back')


args                  = parser.parse_args()
keys                  = args.keys
slack_channel_logging = args.channel_logging
slack_channel_alert   = args.channel_alert
log_file              = args.logfile
audit_ips             = [args.ip]  # sink into array for lisp-like approach further on
reporting_key         = args.reporting_key
API_ENDPOINT          = args.endpoint
ts_threshold          = float(args.ts_threshold)
known_ips             = args.known_ips.split(',')


def callTheApp(ip):
	# data to be sent to api
	data = {
		'keys'           : keys.split(','),
		'ip'             : ip,
		'channel_logging': slack_channel_logging.split(','),
		'channel_alert'  : slack_channel_alert.split(','),
		'reporting_key'  : reporting_key,
		'public_ip'      : utils.getPublicIp(),
		'hostname'       : socket.gethostname(),
		'ts_threshold'   : ts_threshold
	}
	print(data)

	headers = {'content-type': 'application/json'}

	r = requests.post(url=API_ENDPOINT, data=json.dumps(data), headers=headers)
	print(r)


stored_ips       = utils.readIpFromStore(log_file, ts_threshold)
mapped_entries   = list(filter(lambda ip: utils.isInLogs(ip, stored_ips) or utils.isKnown(ip, known_ips), audit_ips))
unmapped_entries = list(set(audit_ips) - set(mapped_entries))

lookedup_ips  = [callTheApp(ip) for ip in unmapped_entries]


[utils.saveToStore(an_ip, log_file) for an_ip in unmapped_entries]