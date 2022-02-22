#!/usr/bin/python3

import sqlite3
from datetime import date, datetime
from webexport import chartjs, site
import os.path, sys


toplist = True # False = bottomlist
maxyears = 3 # Max number of years
n = 15 # Number of cases listed +-

jobstatdays = 100 # Num of days


#  SET OUTPUT PATH =============

path = os.path.dirname(os.path.realpath(__file__))

if len(sys.argv) > 1:
	opath = sys.argv[1]
else:
	opath = path + "/../minasiffror/html"
#	opath = path + "/"

f = path + '/myndata.db'

db_job = path + "/jobdata.db"

if not os.path.isfile(f):
	print("No database")
	sys.exit()

#  GENERATE DATA 1 ===============


def create_connection(db_file):
	conn = None
	try:
		conn = sqlite3.connect(db_file)
	except Error as e:
		print(e)
	
	return conn


y = int(date.today().strftime("%Y"))

ok = True
cnt = 0
myn = {}

conn = create_connection(f)
cursor = conn.cursor()

while ok and cnt<maxyears:
	try:
		sql = f"SELECT * FROM 'esv{y-cnt}'"
		d = cursor.execute(sql).fetchall()
		for m in d:
			if m[0] not in myn:
				myn[m[0]] = [m[4]]
			else:
				myn[m[0]].append(m[4])
		cnt += 1
	except:
		ok = False

conn.close()

basey = y - cnt
y -= 1

index = {}
for m in myn:
	values = []
	if 0 not in myn[m] and None not in myn[m]:
		for i in range(len(myn[m])-1, -1, -1):
			values.append(int(myn[m][i]/myn[m][len(myn[m])-1]*100)-100)
		index[m] = values
	
sortedindex = sorted(index, key=lambda x: index[x][len(index[x])-1], reverse = toplist)

#  CHART SETUP 1 =================

chart = chartjs("bar")

lbl, data, clr = [], [], []
cnt, max = 10, 0
for s in sortedindex[:n]:
	val = index[s][len(index[s])-1]
	max = val if val > max else max
	data.append(val)
	lbl.append([s, f"{myn[s][0]} åa / {myn[s][-1]} åa"])
	cnt += 7
	hexa = "00"[0:2-len(hex(cnt)[2:])] + hex(cnt)[2:]
	clr.append("#FFBA" + hexa)
#2fa0
chart.addDataset(f"Procentuell förändring mellan {basey}-{y}", data, clr)
chart.addLabels(lbl)

chart.options["plugins"]["legend"] = { "display": False }
chart.options["tension"] = 0

chart.options["scales"] = {
		"y": {
			"grid": {
				"color": "#444"	
			},
			"max": int(str(max+100)[0])*100
		},
		"x": {
			"grid": {
				"display": False
			}
		}

	}
	
chart.save(opath, "vaxtverket")

#  GENERATE DATA 2 ===============

try:
	conn = create_connection(db_job)
	cur = conn.cursor()
	sql = f"SELECT * FROM 'myndighetsjobb' ORDER BY datum ASC"
	log = cur.execute(sql).fetchall()
	conn.close()
except:
	print(f"Error reading database: {db_job}")
	sys.exit()
	
m = None
today, fromdate = date.today(), None
stat = {}


for l in log:
	date = datetime.strptime(l[0][0:10],"%Y-%m-%d").date()
	if (today-date).days <= jobstatdays:
		if fromdate is None:
			fromdate = date 
		for e in d:
			if e[1].replace("-","").strip() == l[1]:
				m = e
				break
		
		if m is not None and m[3] is not None and m[3] > 0:
			if m[0] in stat:
				stat[m[0]][0] += l[2]
			else:
				stat[m[0]] = [l[2], m[3]]

span = (today-fromdate).days + 7
#print(f"Period: last {span} days")
l = {}
for m in stat:
	stat[m].append(round((stat[m][0]/stat[m][1])*100, 2))
	l[m] = f" {stat[m][0]} pa / {stat[m][1]} an"
	

sortedstat = sorted(stat, key=lambda x: stat[x][2], reverse = True)

chart = chartjs("bar")
lbl, data, clr, cnt = [], [], [], 185

for s in sortedstat[:n]:
	lbl.append([s, l[s]])
	data.append(stat[s][2])
	cnt += 3
	hexa = "00"[0:2-len(hex(cnt)[2:])] + hex(cnt)[2:]
	clr.append("#288F" + hexa)


chart.addDataset(f"", data, clr)
chart.addLabels(lbl)

chart.options["plugins"]["legend"] = { "display": False }
chart.options["tension"] = 0

chart.options["scales"] = {
		"y": {
			"grid": {
				"color": "#444"	
			},
			"max": data[0]+25
		},
		"x": {
			"grid": {
				"display": False
			}
		}

	}
	
chart.save(opath, "rekryterarna")

#  SITE SETUP  ===================

minasiffror = site(opath)

minasiffror.addPage(
	102,
	"vaxtverket",
	"Växtverket",
	f"Myndigheterna vuxit mest de senadte åren. Figuren visar den procentuella ökning av årsarbetskrafter (åa) hos de myndigheter som vuxit mest. Utvecklingen avser perioden {basey}-{y}. Siffrorna hämtas automatiskt från ESV."
	)
	
minasiffror.addPage(
	105,
	"rekryterarna",
	"Rekryterarna",
	f"Myndigheterna som rekryterar mest i   förhållande till sin storlek. Figuren visar myndighetens platsannonser (pa) de senaste {span} dagarna i förhållande till antalet andtällda (an).  Siffrorna hämtas automatiskt från ESV och Arbetsförmedlingen."
	)
minasiffror.save()
