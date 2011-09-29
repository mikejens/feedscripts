import json, subprocess, csv, sys, sqlite3, os, re
import time
from lxml import etree

STREETSEG_FIELDS = ["id", "city", "zip", "street", "street_type", "prefix", "house_number", "sec_unit_type", "sec_unit_number", "precinct_code", "precinct_name"]
STREET_FILES = ["feed_data/SWVF_1_44.TXT", "feed_data/SWVF_45_88.TXT"]
DATABASE = "feed_data/test.db"
TEMPLATE = "tmpl/street.tmpl"
OUTPUT = "feed_data/locality.xml"
QUERYSTRING = "id INTEGER PRIMARY KEY, city TEXT, zip TEXT, street TEXT, street_type TEXT, prefix TEXT, house_number TEXT, sec_unit_type TEXT, sec_unit_number INTEGER, precinct_code TEXT, precinct_name TEXT, UNIQUE (city, zip, street, street_type, prefix, house_number, sec_unit_type, sec_unit_number)"
INVALID_PRECINCTS = ["DEERFIELD A","HAMILTON B","HAMILTON E","HAMILTON C","CLEARCREEK A","TURTLECREEK A","CARLISLE A","HAMILTON D","HAMILTON A","NEW HAVEN TWP 2","GENOA R","POWELL I","POWELL J","CLEARCREEK B","COLUMBUS CITY E","CONCORD H","ORANGE P","ORANGE Q","CAREY B","LONDON 1-D","UNION EAST","UNION WEST","CHOCTAW LAKE WEST","STOKES","SOMERFORD","SOUTH SOLON","RANGE","CHOCTAW LAKE EAST","PIKE","MT. STERLING SOUTH","PLEASANT WEST","MIDWAY","MT. STERLING NORTH","PLEASANT EAST","W JEFFERSON 4","HAM26WD1","PRECINCT DEERFIELD A","PRECINCT HAMILTON B","PRECINCT HAMILTON E","PRECINCT HAMILTON C","PRECINCT CLEARCREEK A","PRECINCT TURTLECREEK A","PRECINCT CARLISLE A","PRECINCT HAMILTON D","PRECINCT HAMILTON A","PRECINCT NEW HAVEN TWP 2","PRECINCT GENOA R","PRECINCT POWELL I","PRECINCT POWELL J","PRECINCT CLEARCREEK B","PRECINCT COLUMBUS CITY E","PRECINCT CONCORD H","PRECINCT ORANGE P","PRECINCT ORANGE Q","PRECINCT CAREY B","PRECINCT LONDON 1-D","PRECINCT UNION EAST","PRECINCT UNION WEST","PRECINCT CHOCTAW LAKE WEST","PRECICNT STOKES","PRECINCT SOMERFORD","PRECINCT SOUTH SOLON","PRECINCT RANGE","PRECINCT CHOCTAW LAKE EAST","PRECINCT PIKE","PRECINCT MT. STERLING SOUTH","PRECINCT PLEASANT WEST","PRECINCT MIDWAY","PRECICNT MT. STERLING NORTH","PRECINCT PLEASANT EAST","PRECINCT W JEFFERSON 4","PRECINCT HAM26WD1"]

class Database(object):

	def __init__(self):
		
		connection = sqlite3.connect(DATABASE)
		c = connection.cursor()

		c.execute('DROP TABLE IF EXISTS people')
		c.execute('DROP TABLE IF EXISTS precincts')
		c.execute('CREATE TABLE people (%s)' % QUERYSTRING)
		c.execute('CREATE TABLE precincts (id TEXT PRIMARY KEY, name TEXT)')

		connection.commit()
		connection.close()

	def uploadStreetSegments(self, fname):

		connection = sqlite3.connect(DATABASE)
		c = connection.cursor()

		filename = fname[:fname.find(".")] + "cleandata.txt"
	
		print "opening " + filename	
	
		test = csv.DictReader(open(filename))

		print "insert data into database " + DATABASE
		
		counter = 0
		start = time.time()

		for row in test:

			insertList = []

			for i in range(len(STREETSEG_FIELDS)):
				if STREETSEG_FIELDS[i] in row:
					if STREETSEG_FIELDS[i] == "id":
						row["id"] = int(row["id"][2:])
					insertList.append(row[STREETSEG_FIELDS[i]])
				else:
					print row

			c.execute('insert or ignore into people values (?,?,?,?,?,?,?,?,?,?,?)', insertList)
			c.execute('insert or ignore into precincts values (?,?)', (insertList[9], insertList[10]))
	
			counter += 1

		end = time.time()
		totaltime = end - start

		connection.commit()
		connection.close()

		print "Total insert time: " + str(totaltime) + " to insert: " + str(counter) + " records"

class CreateXML(object):
	
	def __init__(self):

		connection = sqlite3.connect(DATABASE)

		c = connection.cursor()
		
	#	self.createPrecincts(c)
		self.createStreetSegments(c)

		connection.close()
	
	def createPrecincts(self, c):
	
		c.execute("select * from precincts")

		template = open("tmpl/precinct.tmpl","r").read()

		w = open(OUTPUT, "a")

		count = 0

		for row in c:
			line = {'name':row[1],'number':row[0],'locality_id':("39" + row[0][:2])}
			if len(line["name"]) <= 0:
				continue
			precinctid = row[0][:2]
			pend = row[0][2:] 
			for char in pend:
				if char.isalpha():
					precinctid += str(ord(char))
			line['id'] = precinctid
			line['polling_location_id'] = precinctid[:2] + precinctid
			
			line["name"] = line['name'].replace('&', "and")
			line["name"] = line["name"].replace("PRECINCT ", "")

			element = etree.XML(template.format(**line))

			w.write(etree.tostring(element) + "\n")
	
			count += 1
		
		print "Wrote: " + str(count) + " precinct lines to " + OUTPUT 


	def createStreetSegments(self, c):
	
		c.execute("select * from people")

		template = open(TEMPLATE,"r").read()

		w = open(OUTPUT, "a")
		err = open(OUTPUT + ".err","w")

		count = 0
		errcount = 0

		for row in c:
			if row[10] in INVALID_PRECINCTS:
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
				err.write("Invalid row, house number not an integer: " + str(row) + "\n")
				errcount += 1
				continue

			line = {'id':("9"+str(row[0])),'start_number':row[6],'end_number':row[6],'odd_even_both':'both','start_apartment_number':row[8],'end_apartment_number':row[8],'street_name':(row[5] + " " + row[3] + " " + row[4]).strip(),'state':'OH','city':row[1],'zip':row[2],'precinct_split_id':''}
			
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

			w.write(etree.tostring(element) + "\n")
	
			count += 1
		
		print "Wrote: " + str(count) + " street segment lines to " + OUTPUT 
		print "Invalid street segments: " + str(errcount)
	
def main():

	#db = Database()	

	#for f in STREET_FILES:
	#	print "processing: " + f
		
	#	db.uploadStreetSegments(f)
	
	CreateXML()	
	
	#fileCleanup()

def fileCleanup():
	for f in FILE_LIST:
		cleanfile = f[:f.find(".")] + "cleandata.txt"
		errorfile = f[:f.find(".")] + "cleandata.err"
		os.remove(cleanfile)
		if os.path.getsize(errorfile) == 0:
			os.remove(errorfile)
	os.remove(DATABASE)

if __name__ == "__main__":
	main()
