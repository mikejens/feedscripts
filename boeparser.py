import csv
from lxml import etree
from datetime import datetime

OUTPUT = "feed_data/locality.xml"

w = open(OUTPUT, "a")

test = csv.reader(open("feed_data/OH_BOE.csv"))

linecounter = 1
boecounter = 0
boedata = []

state_id = "39"
ea_id = ""
for char in "EA":
	ea_id += str(ord(char))
eo_id = ""
for char in "EO":
	eo_id += str(ord(char))

for row in test:
	if linecounter % 9 == 0:
		linecounter += 1
		boecounter += 1
		continue
	elif linecounter % 9 == 1:
		prefix = str('%02d' % (boecounter+1)) 
		boedata.append({"name":row[6]})
		boedata[boecounter]["id"] = state_id + prefix 
		boedata[boecounter]["type"] = "county"
		boedata[boecounter]["state_id"] = state_id
		boedata[boecounter]["ea_id"] = prefix + ea_id
		boedata[boecounter]["eo_id"] = prefix + eo_id		
	elif linecounter % 9 == 2 and len(row[6]) > 0:
		boedata[boecounter]["physical_location_name"] = row[6]
	elif linecounter % 9 == 3:
		lineaddress = row[6].split(",")
		for i in range(len(lineaddress)):
			boedata[boecounter]["physical_line%d" % (i+1)] = lineaddress[i]
		if len(lineaddress) < 2:
			boedata[boecounter]["physical_line2"] = ""
	elif linecounter % 9 == 4:
		if len(row[6]) > 0:
			boedata[boecounter]["mailing_line1"] = row[6]
			boedata[boecounter]["mailing_line2"] = ""
		else:
			boedata[boecounter]["mailing_line1"] = boedata[boecounter]["physical_line1"]
			boedata[boecounter]["mailing_line2"] = boedata[boecounter]["physical_line2"]
	elif linecounter % 9 == 5:
		location = row[6].split(",")
		boedata[boecounter]["city"] = location[0]
		boedata[boecounter]["state"] = "OH"
		boedata[boecounter]["zip"] = location[1].strip().lstrip("OH").lstrip()
	elif linecounter % 9 == 6:
		boedata[boecounter]["hours"] = row[6].replace("Office Hours:", "").replace("&", "and").strip()
	elif linecounter % 9 == 7:
		numbers = row[6].split("/")
		boedata[boecounter]["phone"] = numbers[0].replace("Telephone:", "").strip()
		if len(numbers) > 1:
			boedata[boecounter]["fax"] = numbers[1].replace("Fax:", "").strip()
	elif linecounter % 9 == 8:
		webstuff = row[6].split("/")
		boedata[boecounter]["email"] = webstuff[0].lower().replace("e-mail:", "").strip()
		if len(webstuff) > 1:
			boedata[boecounter]["elections_url"] = webstuff[1].replace("Website:", "").strip()
		else:
			boedata[boecounter]["elections_url"] = ""
	linecounter += 1

template = open("tmpl/header.tmpl", "r").read()
headerdata = {}
headerdata["state_id"] = state_id
headerdata["state_name"] = "OHIO"
headerdata["organization_url"] = "http://www.sos.state.oh.us/SOS/voter.aspx"
headerdata["script_start"] = datetime.isoformat(datetime.today())[:-7]
headerdata["is_statewide"] = "Yes"
headerdata["polling_hours"] = "6:30 AM - 7:30 PM"
headerdata["registration_deadline"] = "2011-10-11" 
headerdata["election_id"] = "2011"
headerdata["election_date"] = "2011-11-08"
headerdata["election_type"] = "General"
element = etree.XML(template.format(**headerdata))
w.write(etree.tostring(element))


types = ["locality", "admin", "official"]
for i in range(len(types)):
	count = 0
	template = open("tmpl/" + types[i] + ".tmpl", "r").read()
	for j in range(len(boedata)):
		element = etree.XML(template.format(**boedata[j]))
	
		for parent in element[:]:
			for child in parent[:]:
				if child in parent and child.text is None and len(child) == 0:
					parent.remove(child)
			if parent in element and parent.text is None and len(parent) == 0:
				element.remove(parent)

		w.write(etree.tostring(element) + "\n")
		count += 1
	print "Wrote: " + str(count) + " " + str(types[i])
