#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Register a Macintosh Asset in Snipe-IT
# The script will take the user's email as input to perform the following actions:
# - Register model in the system if it doesn't exist
# - Create asset in the system
# - Checkout the equipment

import json
import requests
import os
import subprocess
import argparse

api_token = '0xDEADBEEF'
headers = {'Content-Type': 'application/json',
           'Authorization': 'Bearer {0}'.format(api_token)}
base_url = 'https://snipeit.yourcompany.com'

def get_mac_model():
    file = os.path.expanduser('~/Library/Preferences/com.apple.SystemProfiler.plist')
    try:
        f = open(file)
        f.close()
    except FileNotFoundError:
        print("It seems like your forgot to click on the Apple logo at the top-left of your screen and click on About This Mac. After this please re-run this script.")
        exit()

    cmd = '''defaults read ~/Library/Preferences/com.apple.SystemProfiler.plist 'CPU Names' | cut -sd '"' -f 4 | uniq'''
    result = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True, check=True)
    model = result.stdout.strip().decode('utf-8')
    return model

def get_mac_serial_number():
    cmd = "system_profiler SPHardwareDataType | grep 'Serial Number' | awk '{print $4}'"
    result = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True, check=True)
    serial_number = result.stdout.strip().decode('utf-8')
    return serial_number

def process_model():
    url = base_url + '/api/v1/models'
    payload = { 'search': model }
    response = requests.get(url, headers=headers, json=payload)
    data = response.json()
    total = data['total']

    if "iMac" in model:
        category_id = 3 # desktop
    else:
        category_id = 2 # laptop

    # if this model doesn't exist create it
    if total == 0:
        model_data = {
            'name': model,
            'manufacturer_id': 1,
            'category_id': category_id
        }
        response = requests.post(url, headers=headers, json=model_data)
        if response.status_code == 200:
            print("=> Successfully registered your PC model in the system")
        else:
            print("<!> There was a problem registering your asset")

def get_model_id():
    url = base_url + '/api/v1/models'
    payload = { 'search': model }
    response = requests.get(url, headers=headers, json=payload)
    data = response.json()
    model_id = data['rows'][0]['id']
    return model_id

def get_user_id(email):
    url = base_url + '/api/v1/users'
    payload = { 'search': email }
    response = requests.get(url, headers=headers, json=payload)
    data = response.json()
    total = data['total']
    if total > 0:
        user_id = data['rows'][0]['id']
        return user_id
    else:
        print("<!> Your user {} was not found in the system.".format(email))
        exit()

def get_user_name(email):
    url = base_url + '/api/v1/users'
    payload = { 'search': email }
    response = requests.get(url, headers=headers, json=payload)
    data = response.json()
    first_name = data['rows'][0]['first_name']
    last_name = data['rows'][0]['last_name']
    name = first_name + ' ' + last_name
    return name

def get_model_id():
    url = base_url + '/api/v1/models'
    payload = { 'search': model }
    response = requests.get(url, headers=headers, json=payload)
    data = response.json()
    model_id = data['rows'][0]['id']
    return model_id

def checkout_asset(email):
    url = base_url + '/api/v1/hardware/'
    asset_name = user_name + "'s " + " ".join(model.split()[:1])
    payload = { 'search': asset_name }
    response = requests.post(url, headers=headers, json=payload)
    data = response.json()
    asset_id = data['rows'][0]['id']
    assigned_to = data['rows'][0]['assigned_to']

    if assigned_to == None:
        url = base_url + '/api/v1/hardware/' + str(asset_id) + '/checkout'
        payload = { 'assigned_user': user_id, 'checkout_to_type': 'user' }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print("=> Successfully assigned your {0} to {1}".format(model, email))
        else:
            print("<!> There was a problem assigning your asset to this user")
    else:
        print("<!> There was a problem checking out your asset {}".format(asset_name))
        exit()

def create_asset():
    model_id = get_model_id()
    serial = get_mac_serial_number()

	# asset_name will be a string like 'Foo Bar's MacBook' 
    asset_name = user_name + "'s " + " ".join(model.split()[:1])

    url = base_url + '/api/v1/hardware'
    payload = { 'search': asset_name }
    response = requests.get(url, headers=headers, json=payload)
    data = response.json()
    total = data['total']

    if total == 0:
        payload = {
            'name': asset_name,
            #'assigned_to': user_id, # this seemed to be broken in the API, hence checkout_asset()
            'company_id': 1,
            'model_id': model_id,
            'serial': serial,
            'status_id': 4, # 4 is Deployed
            'requestable': 0
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print("=> Successfully registered your computer in our inventory")
        else:
            print("<!> There was a problem registering your asset")
    else:
        print("Your asset is already being tracked in the system. Thanks!")
        exit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--email', help='Your email address', required=True)
    args = parser.parse_args()

    model = get_mac_model()
    user_id = get_user_id(args.email)
    user_name = get_user_name(args.email)

    process_model()
    create_asset()
    checkout_asset(args.email)
