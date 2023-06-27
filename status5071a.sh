#!/bin/bash
#
# status5071a.sh
# query hp/agilent/symmetricon/microsemi/microchip 5071a cesium reference clock for status report
# ref https://ww1.microchip.com/downloads/en/DeviceDoc/5071A-Primary-Frequency-Standard-Users-Guide-DS50003249.pdf
# see section 5.5.1.1
# note that the 5071a is DTE so serial connection with a pc/server requires crossing tx/rx  
# 
# uses grabserial  https://elinux.org/Grabserial && https://github.com/tbird20d/grabserial
# for help, grabserial -h
#
# note also the user must have permission to access DEVICE as defined below; this is most easily
# implemented by adding the user to the group which DEVICE belongs to, as follows:
# [jds@fpga2-1a170]$ ls -sl "/dev/ttyUSB0"
# 0 crw-rw---- 1 root dialout 188, 0 Jun  6 15:01 /dev/ttyUSB0
# [jds@fpga2-1a170]$ sudo usermod -a -G dialout jds
#
# todo: does grabserial ever return nonzero output codes? 
# todo: there is no cooperative lock mechanism for preventing serial port access collision.
# todo: the MJD calculation wrt the Unix epoch might be off by half a day; the Julian calendar day starts at noon, not midnight.
# note: https://en.wikipedia.org/wiki/Julian_day#Variants
# note: https://stackoverflow.com/questions/466321/convert-unix-timestamp-to-julian

VERSION="1.2 13jun2023"
DEVICE="/dev/ttyUSB0"
BAUD="9600"

# change this to non-zero in order to set the 5071a to the localhost clock; use care to do this in an atomic manner, 
# such that any competing access to the serial port doesn't write random data to random places in the 5071a memory.
SETCURRENTDATETIME=0

# leave LOCALTIMEZONE null if current locale is correct and desired
LOCALTIMEZONE="TZ=US/Eastern"
LOCALTIMEZONE=""

# see https://ww1.microchip.com/downloads/en/DeviceDoc/5071A-Primary-Frequency-Standard-Users-Guide-DS50003249.pdf
CMDCLEAR="*CLS"
CMDIDENTIFY="*IDN?"
CMDSTATUS="SYST:PRINT?"
PROMPT="scpi >"

grabserial -d ${DEVICE} -b ${BAUD} -C -c "${CMDCLEAR}" -q "${PROMPT}" -e 5
grabserial -d ${DEVICE} -b ${BAUD} -C -c "${CMDCLEAR}" -q "${PROMPT}" -e 5

# the assumption here is that the localhost has the correct (e.g. NTP-derived) time.
if [ ${SETCURRENTDATETIME} -eq "1" ]
then
  echo "info: setting date and time on 5071a..."
  grabserial -d ${DEVICE} -b ${BAUD} -C -c "${CMDCLEAR}" -q "${PROMPT}" -e 5
  grabserial -d ${DEVICE} -b ${BAUD} -C -c "SYST:REM ON" -q "${PROMPT}" -e 5
  MJD=`echo $(($(date "+%s")/86400+40587))`
  grabserial -d ${DEVICE} -b ${BAUD} -C -c "SOUR:PTIM:MJD ${MJD}" -q "${PROMPT}" -e 5
  NOWSCPIFORMAT=`date -u ++%H,+%M,+%S`
  grabserial -d ${DEVICE} -b ${BAUD} -C -c "SOUR:PTIM:TIME ${NOWSCPIFORMAT}" -q "${PROMPT}" -e 5 
  grabserial -d ${DEVICE} -b ${BAUD} -C -c "SYST:REM OFF" -q "${PROMPT}" -e 5
fi  

echo -n "NOW_UTC: "
TIMESTAMP=`date -u`
echo "${TIMESTAMP}"
echo -n "NOW_LOC: "
if [ -z "${LOCALTIMEZONE}" ]
then
  date -d "${TIMESTAMP}"
else
  TZ="${LOCALTIMEZONE}" date -d "${TIMESTAMP}"
fi

MJD=`echo $(($(date "+%s")/86400+40587))`
echo -n "NOW_MJD: "
echo "MJD ${MJD}"

echo -n "NOW_UNIX: "
echo $(date +%s)
echo

grabserial -d ${DEVICE} -b ${BAUD} -C -c "${CMDCLEAR}" -q "${PROMPT}" -e 5
grabserial -d ${DEVICE} -b ${BAUD} -C -c "${CMDIDENTIFY}" -q "${PROMPT}" -e 5 | sed 's/^/EUT_IDN: /'
grabserial -d ${DEVICE} -b ${BAUD} -C -c "${CMDSTATUS}" -q "${PROMPT}" -e 10 | sed 's/^MJD    /EUT_MJD: /'

exit 0

# also note
# see section 5.5.1.2
#
# scpi > DIAGNOSTIC:LOG:PRINT?
# Log status: Empty
#
#
# scpi > DIAGNOSTIC:LOG:COUNT?
# +0
