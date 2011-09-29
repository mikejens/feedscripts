import csv
from lxml import etree

test = csv.DictReader(open("feed_data/OH_Polling_Locations.csv"))

POLLING_FIELDS = {'directions':'LOCATION_DESCRIPTION','location_name':'LOCATION_NAME','line1':'LOCATION_ADDRESS','city':'LOCATION_CITY','zip':'LOCATION_ZIP_CO'}
OUTPUT = "feed_data/locality.xml"

w = open(OUTPUT, "a")
err = open(OUTPUT[:-3]+"err", "w")
template = open("tmpl/polling.tmpl","r").read()

count = 0

for row in test:
	output = {}
	polling_id = row["STATE_PRECINCT_CODE"][:2]
	pend  = row["STATE_PRECINCT_CODE"][2:]
	for char in pend:
		if char.isalpha():
			polling_id += str(ord(char))
	output["id"] = polling_id[:2] + polling_id
	for k, v in POLLING_FIELDS.items():
		output[k] = row[v]
	output["state"] = "OH"

	output["line1"] = output['line1'].replace('&', "and")
	output["directions"] = output['directions'].replace('&', "and")
	output["location_name"] = output['location_name'].replace('&', "and")
	if output["city"].endswith(" OH"):
		output["city"] = output["city"][:-3]
	elif output["city"].endswith(" OHIO"):
		output["city"] = output["city"][:-5]
	output["city"] = output["city"].strip()
	if output["directions"].startswith(output["line1"]):
		output["directions"] = ''

#	print output
	
	try:	
		element = etree.XML(template.format(**output))

		for parent in element[:]:
			for child in parent[:]:
				if child in parent and child.text is None and len(child) == 0:
					parent.remove(child)
			if parent in element and parent.text is None and len(parent) == 0:
				element.remove(parent)
	except:
		err.write(str(output) + "\n")
		continue

	w.write(etree.tostring(element) + "\n")
	
	count += 1

print "Wrote: " + str(count) + " polling locations"
