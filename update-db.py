import sqlite3
import read5071a
import subprocess
import os.path

# dict to build up by parsing result string
result_dict = {}
# note: you can use rm.list_resources() to find the resource string for your 5071a
RESOURCE = 'ASRL/dev/ttyUSB0::INSTR'
# result string from querying 5071a
result = read5071a.get_output(RESOURCE)

# keys of result_dict, predefined by 5071a output
# they are in the reverse order of the 5071a output because it is parsed starting from the end
keys = ['Thermometer', '+5V  supply', '-12V supply', '+12V supply', 'uP Clock PLL', '87MHz PLL', 'DRO Tuning', 'SAW Tuning', 'Mass spec', 'HW Ionizer', 'Ion Pump', 'Osc. Oven', 'CBT Oven Err', 'CBT Oven', 'Signal Gain', 'E-multiplier', 'C-field curr', 'Zeeman Freq', 'RF amplitude 2', 'RF amplitude 1', 'Osc. control', 'Freq Offset', 'Log status', 'Power source', 'Status summary', 'CBT ID', 'EUT_MJD', 'EUT_IDN', 'NOW_UNIX', 'NOW_MJD', 'NOW_LOC', 'NOW_UTC']

# parse result string and build up result_dict
# div means divider index between different key value pairs in result string
div = 0
prev_div = len(result)

# iterate through the keys list to get key value pairs and build result_dict
for key in keys:
	# div is start of key value pair, prev_div is end of key value pair
	div = result.index(key)
	keyval = result[div : prev_div]
	# cut off key and colon, strip away whitespace
	val = keyval[len(key) + 1 : ].strip()
	# add value to result_dict
	result_dict[key] = val
	# current div is next key's prev_div
	prev_div = div

# form database filepath using Cesium Beam Tube (CBT) ID to allow monitoring multiple clocks simultaneously
db_filepath = './clock-data-' + result_dict['CBT ID'].replace('(', '').replace(')', '') + '.db'
# establish connection to database file (and create it if it doesn't exist yet)
con = sqlite3.connect(db_filepath)
cur = con.cursor()

# create the database table if it doesn't exist yet
# need to add column names to this string before executing command
create_table = 'CREATE TABLE IF NOT EXISTS data ('

# create comma separated list of column names
cols_str = ''
# using keys list instead of dict for this to make sure order is consistent
for key in keys:
	# square brackets allow column names to contain special characters
	cols_str += '[' + key + ']' + ','

# get rid of final comma after last column name
cols_str = cols_str[:-1]

# finish creating string for create table command
create_table += cols_str + ')'

# execute the command to create the database table if it doesn't exist yet
cur.execute(create_table)
con.commit()

# create placeholder string to insert data into table
# comma separated list of as many question marks as there are values to insert
placeholder = '('
placeholder += '?,' * len(keys)
placeholder = placeholder[:-1] + ')'

# create tuple of values to add to the database
value_tuple = ()
for key in keys:
	value_tuple += (result_dict[key],)

# execute command to add the data
cur.execute('INSERT INTO data(' + cols_str + ') VALUES ' + placeholder, value_tuple)
con.commit()

# update csv file with most recent row to show it on the confluence page
# this is not necessary for grafana so I am leaving it out of the github
if os.path.isfile('./update-csv.py'):
	subprocess.run(['python3', './update-csv.py', db_filepath])
