import pyvisa # for serial communication with 5071a
import time # to get current unix timestamp
from datetime import datetime, timezone # to get UTC and local times
from astropy.time import Time as aptime # to get MJD
import pytz # to get local time

# set the local timezone
LOCALTIMEZONE = 'US/Eastern'

# define variables for scpi commands
CMDCLEAR = '*CLS'
CMDIDENTIFY = '*IDN?'
CMDSTATUS = 'SYST:PRINT?'

# function to read instrument and return True if it throws an error
# it will throw an error when there is nothing left to read
def read_throws_error(inst):
	try:
		inst.read()
		return False
	except:
		return True

# function to clear the buffer
def clear_buffer(inst):
	# clear any errors from the queue
	inst.query(CMDCLEAR)

	# keep reading instrument until there is nothing left to read
	while not read_throws_error(inst):
		pass

# function to create and return output
def get_output(resource):
	# set up serial connection to 5071a
	# note: you can use rm.list_resources() to find what string to input into rm.open_resource()
	rm = pyvisa.ResourceManager()
	inst = rm.open_resource(resource)

	# pyvisa will insert the write termination at the end of writes and queries
	inst.write_termination = '\r\n'
	# pyvisa will stop reading once it finds the read termination string
	inst.read_termination = 'scpi >'

	# output string to return at the end
	output = ''

	# get current unix timestamp
	now_unix = time.time()

	# get current MJD
	astrotime = aptime(now_unix, format = 'unix')
	now_mjd = astrotime.mjd

	# define datetime format
	DATETIMEFORMAT = '%a %b %d %I:%M:%S %p %Z %Y'

	# get current UTC and local times
	now_utc_obj = datetime.fromtimestamp(now_unix, tz = timezone.utc)
	now_utc = now_utc_obj.strftime(DATETIMEFORMAT)
	now_loc_obj = now_utc_obj.astimezone(pytz.timezone(LOCALTIMEZONE))
	now_loc = now_loc_obj.strftime(DATETIMEFORMAT)

	# add times to output string
	output += 'NOW_UTC: ' + now_utc + '\n'
	output += 'NOW_LOC: ' + now_loc + '\n'
	output += 'NOW_MJD: MJD ' + str(now_mjd) + '\n'
	output += 'NOW_UNIX: ' + str(now_unix) + '\n\n'

	# clear the buffer
	clear_buffer(inst)

	# get equipment under test identification and add it to output
	eut_idn = inst.query(CMDIDENTIFY).strip()[len(CMDIDENTIFY):].strip()
	output += 'EUT_IDN: ' + eut_idn + '\n\n'

	# get measurements from 5071a and add it to output
	measurements = inst.query(CMDSTATUS).strip()[len(CMDSTATUS):].strip().replace('MJD    ', 'EUT_MJD: ')
	output += measurements

	# clear the buffer again to make sure we didn't leave anything on it
	clear_buffer(inst)

	# close connection to instrument
	inst.close()

	return output
