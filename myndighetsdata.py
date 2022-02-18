#!/usr/bin/python3

import requests as req
import os.path, os, sys
import sqlite3
import hashlib  # Needed for cache
import time
from bs4 import BeautifulSoup
from datetime import date

cache = True
db = 'myndata.db'

def create_connection(db_file):
	
	conn = None
	try:
		conn = sqlite3.connect(db_file)
	except Error as e:
		print(e)
	
	return conn


def create_table(db, y):
	year = str(y)
	conn = create_connection(db)
	cursor = conn.cursor()
	sql = f'''
	CREATE TABLE "esv{year}" (
		"myndighetsnamn"	TEXT,
		"orgnr"	TEXT,
		"departement"	TEXT,
		"anställda"	INTEGER,
		"årsarbetare"	INTEGER,
		PRIMARY KEY("orgnr")
		)
	'''
	cursor.execute(sql)
	conn.close()


def tableexist(db, tbl):
	conn = create_connection(db)
	cursor = conn.cursor()
	sql = f"SELECT name FROM sqlite_master WHERE type='table' AND name='esv{tbl}'"
	res = cursor.execute(sql).fetchall()
	conn.close()
	return len(res)>0

def load(url):
	cpath = "./cache/"
	hash = hashlib.md5(url.encode()).hexdigest()
	
	if os.path.isfile(cpath + hash) and cache:
		with open(cpath + hash, "r", encoding="utf-8") as f:
			r = f.read()
	else:
		time.sleep(3)
		web = req.get(url)
		r = web.text
		with open(cpath + hash, "w", encoding="utf-8") as f:
			f.write(r)
	return r

def yearexistESV(y):
	year = str(y)
	html = load("https://www.esv.se/myndigheter/")
	soup1= BeautifulSoup(html, 'html.parser')
	options = soup1.findAll("option", text="2020")
	return (len(options)==1)

def getdataESV(y):
	year = str(y)
	html = load("https://www.esv.se/myndigheter/")
	soup1= BeautifulSoup(html, 'html.parser')
	resp1 = soup1.findAll("td", {"class": "tbl-myndighet"})
	
	myndigheter = []
	
	for r1 in resp1:
		attr = {}
		attr["namn"] = r1.text.strip()
		lnk = r1.find("a")["href"][0:-4]
		lnk += year
		facts = r1.find_next_siblings("td", limit=3)
		attr["orgnr"] = facts[2].text.strip()
		
		url = "https://www.esv.se" + lnk
		html = load(url)
		soup2 = BeautifulSoup(html,'html.parser')
		resp2 = soup2.findAll("label")
		
		for r2 in resp2:
			a = r2.parent.text.split(":")
			if len(a) > 1:
				typ = a[0].strip().lower()
				val = a[1].strip().lower()
				if typ.find("departement") >= 0:
					attr["departement"] = val
				elif typ.find("anställda") >= 0:
					if val.isnumeric():
						attr["anställda"] = int(val)
					else:
						attr["anställda"] = "null"
				elif typ.find("årsarbetskraft") >= 0:
					if val.isnumeric():
						attr["åa"] = int(val)
					else:
						attr["åa"] = "null"
		
		myndigheter.append(attr)
	return myndigheter
	

y = int(date.today().strftime("%Y"))

if len(sys.argv) > 1:
	arg = sys.argv[1]
	if arg.isnumeric():
		y = int(arg)

if not yearexistESV(y):
	print(f"ESV har inte myndighetsdata för {y} ännu.")
	sys.exit()

if not tableexist(db, y):
	print(f"Uppdaterar med data för {y}...")
	create_table(db, y)
	data = getdataESV(y)
	if len(data) > 0:
		conn = create_connection(db)
		cursor = conn.cursor()
		for d in data:
			sql = f'''
			INSERT INTO "esv{y}" (
				myndighetsnamn,
				orgnr,
				departement,
				anställda,
				årsarbetare
				)
			VALUES(
				"{d['namn']}",
				"{d['orgnr']}",
				"{d['departement'] if 'departement' in d else '' }",
				{d['anställda'] if 'anställda' in d else 'null'}, 
				{d['åa'] if 'åa' in d else 'null'}
				)
			'''
			cursor.execute(sql)
			conn.commit()

		conn.close()
		print("Klar")
else:
	print(f"Databasen innehåller redan data för {y}. Ingen åtgärd.")
