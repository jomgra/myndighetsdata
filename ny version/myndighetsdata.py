import requests as req
import os.path
import pygsheets
import pandas as pd

gsheet = 'myndigheter'

scb_url = 'https://myndighetsregistret.scb.se/myndighet/download?myndgrupp=Statliga%20förvaltningsmyndigheter&format=True'

esv_url = 'https://www.esv.se/myndigheter/ExportExcelAllaArMyndigheter/'

path = os.path.dirname(os.path.realpath(__file__))

gsheetapi = path + '/gsheets.json'

def getwks(file, wksnum):
	gc = pygsheets.authorize(service_file = gsheetapi)	
	sh = gc.open(file)
	w = sh[wksnum]
	return w	

def webload(url):
	web = req.get(url)
	web.encoding = web.apparent_encoding
	return web.content

print(f'Laddar ner gsheet ({gsheet})...')
wks = getwks(gsheet, 0)

print('Laddar ner SBC:s myndighetsregister...')
df_scb = pd.read_excel(webload(scb_url))
df_scb.rename(lambda x: str(x).lower(), axis='columns', inplace=True)
df_scb.rename(columns={"organisationsnr": "orgnr"}, inplace=True)

print('Laddar ner ESV:s myndighetsregister...')
df_esv = pd.read_excel(webload(esv_url))
sheets_dict = pd.read_excel(webload(esv_url), sheet_name=None)

print('Skapar nytt myndighetsregister...')
years = []
for name, sheet in sheets_dict.items():
	if name.isnumeric():
		years.append(int(name))
		ans = 'ans_' + name
		åa = 'åa_' + name
		sheet.rename(lambda x: str(x).lower(), axis='columns', inplace=True)
		sheet.rename(columns = {"anställda": ans, "årsarbetskrafter": åa}, inplace=True)
		df_scb = pd.merge(df_scb,sheet[['orgnr',ans, åa]],on='orgnr', how='left')

print('Laddar upp nytt myndighetsregister...')
y = str(max(years))
sheet = sheets_dict[y]
sheet.rename(columns = {"ans_" + y: "ans", "åa_" + y: "åa"}, inplace=True)
df_scb = pd.merge(df_scb,sheet[['orgnr','ans', 'åa', 'löpnr', 'myndid', 'departement', 'myndighet']],on='orgnr', how='left')

wks.set_dataframe(df_scb,(1,1),fit=True, nan="")