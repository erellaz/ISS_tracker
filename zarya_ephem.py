from __future__ import division
from __future__ import print_function
# Control ascom telescope through Python
# See erellaz.com for more information
# 2018-04-02

#_______________________________________________________________
# If you do not have pyephem: Spyder -> Tools -> Open Command Prompt then: pip install pyephem
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import range
from past.utils import old_div
import ephem 
import datetime
import urllib.request, urllib.error, urllib.parse
import re
import numpy as np


SpaceStation='ISS'
#SpaceStation='TIANGONG'

#Satellite data in TLE for from Celestrack
station_list="https://www.celestrak.com/NORAD/elements/stations.txt"
GPS_list = 'http://www.celestrak.com/NORAD/elements/gps-ops.txt'
GPS2_list = 'http://www.tle.info/data/gps-ops.txt'
GLONASS_list = 'http://www.celestrak.com/NORAD/elements/glo-ops.txt'
GLONASS2_list = 'http://www.tle.info/data/glo-ops.txt'

# Location of observer in decimal degree
Longitude = -95.123 #East is +, West is -
Latitude = 29.123  #North is +, South is -
Elevation=10        #meters
Horizon='15:00'     #does not work with next_pass
steps=float(1)       #time step in second

stepd=old_div(steps,(3600*24))

# Create an observer instance
observer = ephem.Observer()
observer.long,observer.lat,observer.elevation,observer.horizon = str(Longitude),str(Latitude),Elevation,Horizon
observer.date = datetime.datetime.utcnow()
#use this to project next pass to a future date, unit is day, + is future - is past
#observer.date +=1 #<--------------------------------------------------------------------------------------------


# Check the time, time zone and UTC
print("UTC time:",observer.date)
print("Time zone:",datetime.datetime.utcnow()-datetime.datetime.now())
print("Local time:",ephem.localtime(observer.date))
print("Calculations for Observer at:")
print("Longitude (East +, West -):",observer.long)
print("Latitude (North +, South -):",observer.lat)
print("Elevation:",observer.elevation)
print("Using the following coordinates for calculations: Apparent Topocentric for epoch:",observer.epoch)

# Download the TLE from the web
print("\nDownloading TLE from:",station_list)
tles = urllib.request.urlopen(station_list).readlines()
tles = [item.strip() for item in tles]
tles = [(tles[i],tles[i+1],tles[i+2]) for i in range(0,len(tles)-2,3)]

print("TLE downloaded, calculating next pass...\n")

sat_time,sat_alt, sat_az = [], [], []
sat_ra, sat_dec = [], []
for tle in tles:
    if re.match(SpaceStation,tle[0]) is not None:
        try:
            sat = ephem.readtle(tle[0], tle[1], tle[2])
            # Next pass returns an array: Rise time, Rise azimuth, Maximum altitude time, Maximum altitude, Set time, Set azimuth     
            rt, ra, tt, ta, st, sa = observer.next_pass(sat)
    
            # We found the next pass        
            if rt is not None and st is not None:
                print("\nUsing Local time. \nNext Pass of:",tle[0],"\n rises at   ", ephem.localtime(rt),"\n transits at", ephem.localtime(tt), "\n sets at    ",ephem.localtime(st))
                duration=24*3600*(st-rt)          
                print("Total duration of pass:",duration,"seconds or", int(old_div(duration,60)),"mn",int(duration % 60),"s\n")

                
                # We calculate the complete trajectory of this pass, at a step of stepd
                observer.date = rt
                while observer.date < st:
                      sat.compute(observer)
                      #print sat.name,"at time:",ephem.localtime(observer.date),"RA:",sat.ra,"DEC:",sat.dec,"Range:",int(sat.range/1000),"Alt:",sat.alt,"Az:",sat.az,"Eclipsed:",sat.eclipsed
                      sat_time.append(ephem.localtime(observer.date))
                      sat_alt.append(np.rad2deg(sat.alt))
                      sat_az.append(np.rad2deg(sat.az))
                      sat_ra.append(np.rad2deg(sat.ra))
                      sat_dec.append(np.rad2deg(sat.dec))
                      observer.date+=stepd
                      
        except ValueError as e:
            print("Error reading the TLE of:",tle[0],e)
            
#______________________________________________________________________________
import matplotlib
import matplotlib.pyplot as plt

#fig = plt.figure(figsize=(8,6))
#ax = fig.add_subplot(111, projection="mollweide")
#ax.set_xticklabels(['14h','16h','18h','20h','22h','0h','2h','4h','6h','8h','10h'])
#ax.grid(True)

# Plot satellite tracks
plt.figure(1)
plt.subplot(211)
plt.plot(sat_time, sat_alt)
plt.ylabel("Altitude (deg)")
plt.xticks(rotation=25)
plt.subplot(212)
plt.plot(sat_time, sat_az)
plt.ylabel("Azimuth (deg)")
plt.xticks(rotation=25)
plt.show()

# Plot satellite track in polar coordinates
plt.figure(2)
plt.polar(np.deg2rad(sat_az), 90-np.array(sat_alt))
plt.ylim(0,90)
plt.show()

#______________________________________________________________________________
#Calculate the tracking rates
sat_rate_ra, sat_rate_dec = [], []

#Initial conditions in i=0
sat_rate_ra.append((sat_ra[1]-sat_ra[0]))
sat_rate_dec.append(old_div((sat_dec[1]-sat_dec[0]),2))   

ns=len(sat_time)

#derivative of position (=rate) safe from initial conditions
for i in range(1, ns-1):
    sat_rate_ra.append(old_div((sat_ra[i+1]-sat_ra[i-1]),2))
    sat_rate_dec.append(old_div((sat_dec[i+1]-sat_dec[i-1]),2))           

#Initial conditions in i=last sample
sat_rate_ra.append((sat_ra[ns-1]-sat_ra[ns-2]))
sat_rate_dec.append((sat_dec[ns-1]-sat_dec[ns-2]))

#print "\n\n\n------------------------\n\n\n"

#for i in range(0, ns-1):
#    print sat.name,"at time:",sat_time[i],"RA:",sat_ra[i],"DEC:",sat_dec[i],"Rate RA:",sat_rate_ra[i],"Rate DEC:",sat_rate_dec[i]

# Plot satellite tracking rates
plt.figure(3)
plt.subplot(211)
plt.plot(sat_rate_ra, sat_time)
plt.ylabel("Tracking RA rates in (deg/SR)")
plt.xticks(rotation=25)
plt.subplot(212)
plt.plot(sat_rate_ra, sat_time)
plt.ylabel("Tracking DEC rates (deg/SR)")
plt.xticks(rotation=25)
plt.show()

#______________________________________________________________________________
#Reconstruct position from tracking and QC
#print "\n\n\n------------------------\n\n\n"

rec_ra,rec_dec = [], []
rec_ra.append(sat_ra[0])
rec_dec.append(sat_dec[0])
for i in range(1, ns-1):
    rec_ra.append(sat_ra[i]+sat_rate_ra[i])
    rec_dec.append(sat_dec[i]+sat_rate_dec[i])
    #print "RA:",sat_ra[i],rec_ra[i],sat_ra[i]-rec_ra[i],"--DEC:",sat_dec[i],rec_dec[i],sat_dec[i]-rec_dec[i]

#______________________________________________________________________________
#Export a CSV file
import csv
csvfilename=SpaceStation+str(sat_time[i]).replace(" ","").replace(":","").replace(".","")+".csv"

with open(csvfilename,"wb") as csvfile:
    writer = csv.writer(csvfile,delimiter=',')
    writer.writerow(['Side','Time','RA','DEC','RA_Rate','DEC_Rate','Alt','Az'])
    for i in range(0, ns-1):
        if sat_az[i]<180:  #object is east of the meridian   
            side=0
        else:               #object is west of the meridian
            side=1
        writer.writerow([side,sat_time[i],sat_ra[i],sat_dec[i],sat_rate_ra[i],sat_rate_dec[i],sat_alt[i],sat_az[i]])
        
print("Tracking file writen to disk and ready to use.\n")      
        
        
        
        
        