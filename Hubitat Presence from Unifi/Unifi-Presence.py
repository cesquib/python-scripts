#imports
import csv
import json
import requests
import requests.utils
import requests.sessions
import urllib3
import sys
import traceback
import configparser
import logging

from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)


logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
config = configparser.ConfigParser()
config.read('config.ini')


def main():
    #open CSV file as configured in config.ini file.

    with open(config['common']['devicelist']) as csvfile:
        devices=csv.DictReader(csvfile)
    
        #iterate through each row of the CSV file; perforing necessary presence actions.
        for row in devices:
            logging.debug("Processing " + row['name'])
            wireless_connected = unifistatus(row['mac'])
            current_presence = getpresence(row['deviceid'])
            if wireless_connected == True and current_presence == 'not present':
                updated_presence = setpresence(row['deviceid'],'arrived')
            elif wireless_connected == False and current_presence == 'present':
                updated_presence = setpresence(row['deviceid'],'departed')


def unifisession():
    #Tested.
    logging.debug("Getting session for initial logon to unifi controller ")
    url = config['unifi']['baseurl'] + "/api/login"
    auth_header = {'username': config['unifi']['user'], 'password': config['unifi']['pass']}
    unifi_session = requests.Session()
    try:
        r = unifi_session.post(url,verify=False,data=json.dumps(auth_header))
    except requests.exceptions.RequestException as e:
        logging.error(e)
    return r
    
def unifistatus(deviceMAC):
    #Tested.
    #let's get our login session...
    session_unifi = unifisession()
    url = config['unifi']['baseurl'] + "/api/s/" + config['unifi']['site'] + "/stat/sta"
    logging.debug("Device MAC sent: " + deviceMAC)
    try:
        r = requests.get(url,verify=False,cookies=session_unifi.cookies)
    except requests.exceptions.RequestException as e:
        logging.error(e)
    json_result = r.json()
    status = any(sd['mac']==deviceMAC for sd in json_result['data'])
    session_unifi.cookies.clear()
    return status
    
def setpresence(deviceID,status):
    url = config['hubitat']['baseurl'] + '/' + config['hubitat']['maker_api'] + '/devices/' + deviceID + '/' + status + '?access_token=' + config['hubitat']['maker_token']
    try:
        r = requests.get(url,verify=False)
    except requests.exceptions.RequestException as e:
        logging.error(e)
    print(r.status_code)
    return True

def getpresence(deviceID):
    url = config['hubitat']['baseurl'] + '/' + config['hubitat']['maker_api'] + '/devices/' + deviceID + '?access_token=' + config['hubitat']['maker_token']
    try:
        r = requests.get(url,verify=False)
    except requests.exceptions.RequestException as e:
        logging.error(e)
    json_result = r.json()
    presence = json_result['attributes'][0]['currentValue']
    return presence

if __name__ == '__main__':
	main()