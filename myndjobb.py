#!/usr/bin/env 

import os, sys
import requests
import json
import sqlite3
import configparser
from datetime import datetime, date
import time


path = os.path.dirname(os.path.realpath(__file__))
db_myn = path + "/myndata.db"
db_job = path + "/jobdata.db"

configfile = path + "/default.ini"

cfg = configparser.ConfigParser()
cfg.read(configfile)

try :
	api_key = cfg["jobtechdev"]["apikey"]
	url = cfg["jobtechdev"]["url"]
	mail_to = cfg["mail"]["default_to"]

except :	
	print("Missing configuration")
	exit()


def create_connection(fn):
	conn = None
	try:
		conn = sqlite3.connect(fn)
	except:
		print("Connection error")
	return conn


def create_database(fn):
	conn = create_connection(fn)
	with conn:
		cursor = conn.cursor()
		sql = '''
		CREATE TABLE 'myndighetsjobb' (
			'datum' TEXT,
			'orgnr' TEXT,
			'antal' INTEGER,
			PRIMARY KEY(datum, orgnr)
			)
		'''
		cursor.execute(sql)


def get_ads(params):
	time.sleep(4)
	headers = {'api-key': api_key, 'accept': 'application/json'}	
	response = requests.get(url, headers=headers, params=params)
	response.raise_for_status()  # check for http errors
	return json.loads(response.content.decode('utf8'))
	

def addtodatabase(db, item):
	conn = create_connection(db)
	with conn:
		cursor = conn.cursor()
		try:
			sql = '''
				INSERT INTO myndighetsjobb (
					datum,
					orgnr,
					antal )
				values (?,?,?)
			'''
			cursor.execute(sql, item)
			conn.commit()
			r = True
		except sqlite3.IntegrityError:
			r = False
	return r

	
if not os.path.isfile(db_myn):
	print(f"No database: {db_myn}")
	sys.exit()

if not os.path.isfile(db_job):
	print(f"Creating database: {db_job}")
	create_database(db_job)

try:
	conn = create_connection(db_job)
	cur = conn.cursor()
	sql = f"SELECT * FROM 'myndighetsjobb' ORDER BY datum DESC"
	log = cur.execute(sql).fetchall()
	conn.close()
except:
	print("Error reading database: {db_job}")
	sys.exit()

y = int(date.today().strftime("%Y"))	
cnt, myn = 0, None

while myn is None and y-cnt>2020:	
	try:
		conn = create_connection(db_myn)
		cur = conn.cursor()
		sql = f"SELECT * FROM 'esv{y}'"
		myn = cur.execute(sql).fetchall()
		conn.close()
	except:
		cnt += 1

if myn is None:
	print("Error loading database")
	sys.exit()

tot = 0

for m in myn:
	orgnr = m[1].replace("-","").strip()
	print(f"\n{m[0]}")
	
	pa = "2022-01-01T00:00:01"
	
	for l in log:
		if l[1] == orgnr:
			print(f" Previous search: {l[0][0:10]}")
			pa = l[0]
			break

	search_params = {
		'limit': 0,
		'employer': [orgnr],
		'published-after': pa
		}
	
	positions = get_ads(search_params)['positions']
	tot += positions
	d = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
	entry = [d, orgnr, positions]
	if addtodatabase(db_job, entry):
		print(f" {positions} new job(s) saved")
	
print(f"\nFinished.\n{tot} new jobs saved.")


