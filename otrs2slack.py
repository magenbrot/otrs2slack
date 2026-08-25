#!/usr/bin/python3
#
# Post new OTRS tickets to Slack channel
#
# Oliver Völker <info@ovtec.it>
#

import json
import os
import pymysql
import requests
import sys


def get_required_env(var_name):
    """Return the value of a required environment variable, exiting if unset."""
    value = os.getenv(var_name)
    if value is None:
        print("Missing required environment variable: {}".format(var_name))
        sys.exit(1)
    return value


# Slack incoming webhook URL
#
# prod:
WEBHOOK_URL = get_required_env("WEBHOOK_URL")

# OTRS URL
OTRS_URL = get_required_env("OTRS_URL")

# MySQL settings
MYSQL_HOST = get_required_env("MYSQL_HOST")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = get_required_env("MYSQL_USER")
MYSQL_PASS = get_required_env("MYSQL_PASS")
MYSQL_DB = get_required_env("MYSQL_DB")

if len(sys.argv) < 3:
    print("too less arguments")
    sys.exit(1)

conn = pymysql.connect(
    host=MYSQL_HOST,
    port=MYSQL_PORT,
    user=MYSQL_USER,
    passwd=MYSQL_PASS,
    db=MYSQL_DB,
)
cur = conn.cursor()
sql = (
    "SELECT ticket.id, ticket.tn, ticket.title, "
    "CASE WHEN customer_company.name IS NOT NULL "
    "THEN customer_company.name ELSE ticket.customer_id END AS customer "
    "FROM ticket "
    "LEFT JOIN customer_company "
    "ON (ticket.customer_id = customer_company.customer_id) "
    "WHERE tn = %s"
)
cur.execute(sql, sys.argv[1])

if cur.rowcount:
    for row in cur:
        ticket_id = str(row[0])
        tn = row[1]
        title = row[2]
        customer = row[3]
else:
    # exit if no matching ticket was found
    cur.close()
    conn.close()
    sys.exit(0)

cur.close()
conn.close()

headers = {'Content-type': 'application/json'}
payload = {
    'text': 'New ticket #' + tn + ' from "' + customer + '" --> "' + title + '"\n'
    + OTRS_URL + ticket_id
}
r = requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=10)

if r.status_code != 200:
    raise ValueError(
        'Request to slack returned an error %s, the response is:\n%s'
        % (r.status_code, r.text)
    )
