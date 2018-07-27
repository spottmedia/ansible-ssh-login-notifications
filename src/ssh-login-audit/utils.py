"""
    Author        : Grzegorz Nowak (strange3studio@gmail.com)
    Date created  : 10/07/2018
    Python Version: 3.5
"""

import time
import socket

## courtesy of @see https://stackoverflow.com/a/166589
def getPublicIp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    my_ip = s.getsockname()[0]
    s.close()
    return my_ip


def tooOld(line, ts_shreshold):
    split = line.split(' ')
    if len(split) > 0:
        saved_ts = float(split[1])
        return time.time() < saved_ts + ts_shreshold
    else:
        return True


"""
we need only those IPs whose timestamp is not too old
"""
def readIpFromStore(filepath, ts_threshold):
    text_file = open(filepath, "a+")  	# make sure we try creating the file if not there yet
    text_file.seek(0)  					# re-point to the beginning (since the `a` mode)
    lines = text_file.readlines()
    text_file.close()

    return list(filter(lambda line: tooOld(line, ts_threshold), lines))



def saveToStore(ip, logs):
    with open(logs, "a") as logfile:
        logfile.write("{} {}\n".format(ip, time.time()))



def isInLogs(ip, logs):
    return len(list(filter(lambda stored_ip: ip in stored_ip, logs))) > 0
