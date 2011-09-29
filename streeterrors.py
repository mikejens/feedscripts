import sqlite3
from lxml import etree

DATABASE = "feed_data/test.db"
OUTPUT = "feed_data/streetfixes.xml"
ERRORFILE = "feed_data/streeterrors.txt"
TEMPLATE = "tmpl/street.tmpl"
INVALID_PRECINCTS = ["DEERFIELD A","HAMILTON B","HAMILTON E","HAMILTON C","CLEARCREEK A","TURTLECREEK A","CARLISLE A","HAMILTON D","HAMILTON A","NEW HAVEN TWP 2","GENOA R","POWELL I","POWELL J","CLEARCREEK B","COLUMBUS CITY E","CONCORD H","ORANGE P","ORANGE Q","CAREY B","LONDON 1-D","UNION EAST","UNION WEST","CHOCTAW LAKE WEST","STOKES","SOMERFORD","SOUTH SOLON","RANGE","CHOCTAW LAKE EAST","PIKE","MT. STERLING SOUTH","PLEASANT WEST","MIDWAY","MT. STERLING NORTH","PLEASANT EAST","W JEFFERSON 4","HAM26WD1","PRECINCT DEERFIELD A","PRECINCT HAMILTON B","PRECINCT HAMILTON E","PRECINCT HAMILTON C","PRECINCT CLEARCREEK A","PRECINCT TURTLECREEK A","PRECINCT CARLISLE A","PRECINCT HAMILTON D","PRECINCT HAMILTON A","PRECINCT NEW HAVEN TWP 2","PRECINCT GENOA R","PRECINCT POWELL I","PRECINCT POWELL J","PRECINCT CLEARCREEK B","PRECINCT COLUMBUS CITY E","PRECINCT CONCORD H","PRECINCT ORANGE P","PRECINCT ORANGE Q","PRECINCT CAREY B","PRECINCT LONDON 1-D","PRECINCT UNION EAST","PRECINCT UNION WEST","PRECINCT CHOCTAW LAKE WEST","PRECICNT STOKES","PRECINCT SOMERFORD","PRECINCT SOUTH SOLON","PRECINCT RANGE","PRECINCT CHOCTAW LAKE EAST","PRECINCT PIKE","PRECINCT MT. STERLING SOUTH","PRECINCT PLEASANT WEST","PRECINCT MIDWAY","PRECICNT MT. STERLING NORTH","PRECINCT PLEASANT EAST","PRECINCT W JEFFERSON 4","PRECINCT HAM26WD1"]

connection = sqlite3.connect(DATABASE)
c = connection.cursor()

c.execute("SELECT * FROM people")

err = open(ERRORFILE, "w")
out = open(OUTPUT, "a")
template = open(TEMPLATE,"r").read()

count = 0
invalid = 0
errcount = 0

for row in c:
	if row[10] in INVALID_PRECINCTS:
		invalid += 1	
		continue
	if len(row[6]) <= 0 or row[6] == "0":
		err.write("Missing start house number: " + str(row) + "\n")
		errcount += 1
		continue
	if len(row[9]) <= 0:
		err.write("Missing precint info: " + str(row) + "\n")			
		errcount += 1
		continue
	if (len((row[5]+row[3]+row[4]).strip())) <= 0:
		err.write("Missing street name: " + str(row) + "\n")
		errcount += 1
		continue
	if len(row[2]) <= 0 or len(row[1]) <= 0:
		err.write("Missing city or zip: " + str(row) + "\n")
		errcount += 1
		continue
	try:
		int(row[6])
		if len(row[8]) > 0:
			int(row[8])
	except:
		if row[6].find("-") >= 0:
			if row[6].endswith("-"):
				housenum = row[6].rstrip("-")
				suffix = row[3][:1]
				stname = row[3][1:].strip()
			else:
				suffix = row[6][-1:] + "/" + row[3][:1]
				housenum = row[6][:-1].rstrip("-")
				stname = row[3][1:].strip()
			
			line = {'id':("9"+str(row[0])),'start_number':housenum,'end_number':housenum,'odd_even_both':'both','start_apartment_number':row[8],'end_apartment_number':row[8],'street_name':(row[5] + " " + stname + " " + row[4]).strip(),'state':'OH','city':row[1],'zip':row[2],'precinct_split_id':'','suffix':suffix}
			
			precinctid = row[9][:2]
			pend = row[9][2:] 
			for char in pend:
				if char.isalpha():
					precinctid += str(ord(char))
			line["precinct_id"] = precinctid

			element = etree.XML(template.format(**line))
			
			for parent in element[:]:
				for child in parent[:]:
					if child in parent and child.text is None and len(child) == 0:
						parent.remove(child)
				if parent in element and parent.text is None and len(parent) == 0:
					element.remove(parent)

			out.write(etree.tostring(element) + "\n")
	
			count += 1

		else:
			err.write("Invalid row, house number not an integer: " + str(row) + "\n")
			errcount += 1
			continue
	continue

print "Wrote: " + str(count) + " street segment lines to " + OUTPUT 
print "Invalid street segments: " + str(errcount)
print "People with invalid precincts: " + str(invalid)
