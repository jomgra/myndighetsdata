#!/usr/bin/python3

import sqlite3
from datetime import date
from webexport import chartjs, site
import os.path, sys


toplist = True # False = bottomlist
maxyears = 3 # Max number of years
n = 15 # Number of cases listed +-


#  SET OUTPUT PATH =============

path = os.path.dirname(os.path.realpath(__file__))

if len(sys.argv) > 1:
	opath = sys.argv[1]
else:
	opath = path + "/../minasiffror/html"
#	opath = path + "/"


f = path + '/myndata.db'

if not os.path.isfile(f):
	print("No database")
	sys.exit()

#  GENERATE DATA ===============


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

#  CHART SETUP  =================

chart = chartjs("bar")

lbl, data, clr = [], [], []
cnt, max = 10, 0
for s in sortedindex[:n]:
	val = index[s][len(index[s])-1]
	max = val if val > max else max
	data.append(val)
	lbl.append(s)
	cnt += int(89/n)
	clr.append("#2fa0" + str(cnt))

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

#  SITE SETUP  ===================

minasiffror = site(opath)

minasiffror.addPage(
	100,
	"vaxtverket",
	"Växtverket",
	f"Myndigheter växer och krymper över tid. Figuren visar den procentuella ökning av årsarbetskrafter hos de myndigheter som växt mest. Utvecklingen avser perioden {basey}-{y}. Siffrorna hämtas automatiskt från ESV."
	)

minasiffror.save()
