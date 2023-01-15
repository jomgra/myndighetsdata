import pandas as pd
import requests as req # Endast för mynscb2df


def mynesv2df():
	url = 'https://www.esv.se/myndigheter/ExportExcelAllaArMyndigheter/'
	xl = pd.ExcelFile(url)
	y = []
	for s in xl.sheet_names:
		if s.isnumeric():
			y.append(int(s))
	df = xl.parse(str(max(y)))
	df.rename(lambda x: str(x).lower(), axis='columns', inplace=True)
	return df	

def mynscb2df():
	url = 'https://myndighetsregistret.scb.se/myndighet/download?myndgrupp=Statliga%20förvaltningsmyndigheter&format=True'
	web = req.get(url)
	web.encoding = web.apparent_encoding
	df = pd.read_excel(web.content)
	df.rename(lambda x: str(x).lower(), axis='columns', inplace=True)
	df.rename(columns={"organisationsnr": "orgnr"}, inplace=True)
	return df
	

#print(mynesv2df())

#print(mynscb2df())


