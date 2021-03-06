#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import ovh
import json
import argparse


# -*- encoding: utf-8 -*-
import os
import sys
import re
import json
import ovh
import configparser
from pprint import pprint

config = configparser.ConfigParser()

if len(sys.argv) > 1:
    my_ovh_config_file = sys.argv[1]
else:
    my_ovh_config_file = 'ovh.conf'

# Parse args
parser = argparse.ArgumentParser()
parser.add_argument("--conf-file",
                    help="ovh.conf file",
                    default="ovh.conf",)
parser.add_argument("--plan-code",
                    help="Plan code to order, default is ip-v4-s28-ripe (/28 in RIPE (EU))",
                    default="ip-v4-s28-ripe",)
parser.add_argument("--country",
                    help="Country in which IP will be delivered, default is FR",
                    default="FR",)
args = parser.parse_args()


config.read(my_ovh_config_file)

def replace_in_file(filename, regex, replace):
    with open (filename, 'r' ) as f:
        content = f.read()
    content_new = re.sub(regex, replace, content, flags = re.M)

    with open("ovh.conf",'w') as w:
        w.write(content_new)

if not 'application_key' in config[config['default']['endpoint']]:
    print("Please visit https://eu.api.ovh.com/createApp/ to create an API key")
    application_key = raw_input('Please enter your Application Key: ')
    replace_in_file(my_ovh_config_file, r"(;application_key=.*)", r"application_key=" + application_key)
    application_secret = raw_input('Please enter your Application Secret: ')
    replace_in_file(my_ovh_config_file, r"(;application_secret=.*)", r"application_secret=" + application_secret)


# create a client using configuration
client = ovh.Client(config_file=my_ovh_config_file)

# Request RO, /me API access
ck = client.new_consumer_key_request()
ck.add_rules(ovh.API_READ_WRITE, "/*")

if not 'consumer_key' in config[config['default']['endpoint']]:
    # Request token
    validation = ck.request()
    print("Please visit %s to authenticate" % validation['validationUrl'])
    raw_input("and press Enter to continue...")
    print("Welcome", client.get('/me')['firstname'])
    print("Btw, your 'consumerKey' is '%s'" % validation['consumerKey'])
    replace_in_file('ovh.conf', r"(;consumer_key=.*)", r"consumer_key=" + validation['consumerKey'])



# Functions
def print_json(_json):
    print(
        json.dumps(
            _json,
            sort_keys=True,
            indent=2,
            separators=(',', ': ')
        )
    )





# Create a client
# It will read config from env vars.
# See https://github.com/ovh/python-ovh#configuration


# Create cart
cart = client.post(
    "/order/cart",
    ovhSubsidiary=args.country,
    description="IP block ordering",
)
client.post("/order/cart/{}/assign".format(cart['cartId']))

# Add IP block in the cart
item = client.post(
    "/order/cart/{}/ip".format(cart['cartId']),
    duration="P1M",
    planCode=args.plan_code,
    pricingMode="default",
    quantity=1,
)

# Add configuration
# Fuck this API
configuration = client.post(
    "/order/cart/{}/item/{}/configuration".format(
        cart['cartId'],
        item['itemId'],
    ),
    label='country',
    value=args.country,
)

# Checkout
order = client.post("/order/cart/{}/checkout".format(cart['cartId']))

print(
    "Please pay the BC {} --> {}".format(
        order['orderId'],
        order['url'],
    )
)

print('Done')
