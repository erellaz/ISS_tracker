from __future__ import division
from __future__ import print_function
# Control ascom telescope through Python to track satellites
# See erellaz.com for more information
# 2018-07-20

#_______________________________________________________________
# Choose an Ascom Driver
from builtins import next
from builtins import str
from builtins import range
from past.utils import old_div
import win32com.client      #needed to load COM objects
import ephem
import datetime
import time
import winsound
import sys

#_______________________________________________________________
# Change only in this block

# your track file
csvfilename="ISS2018-10-01231332.csv" 
# if simulation mode is true (=1), a delay is calculated so the event is 
# transalted in time (future or past) to happen about now. Also RA in hours has to be 
#translated by the same fractional number of hours to match the Alt Az of the real pass. 
# If simulation is false (=0) there is no translation in time or RA.
simulation=1 

# Observer's position
Longitude = -95.123 #East is +, West is -
Latitude = 29.123  #North is +, South is -
Elevation=10        #meters
Horizon='15:00'
#_______________________________________________________________
# ASCOM chooser allows to choose your mount in a popup window.

#Use chooser
#x = win32com.client.Dispatch("ASCOM.Utilities.Chooser")
#x.DeviceType = 'Telescope'
#driverName=x.Choose("None")
#tel=win32com.client.Dispatch(driverName)

##OR use directly one of those
#tel = win32com.client.Dispatch("Celestron.Telescope")
#tel = win32com.client.Dispatch("ASCOM.Simulator.Telescope")
tel = win32com.client.Dispatch("AstroPhysicsV2.Telescope")

print("You have choosen the following driver:",tel)

#_______________________________________________________________
# Here we correct for a bugs and non compliance to ASCOM standard in various ASCOM drivers I tested
#if "AstroPhysicsV2" in tel:
#    print("Accounting for ASCOM AstroPhysicsV2 driver bug, correcting by applying a scalar to rates.")
#    polra=1
#    #poldec=15 #APV2 driver rates are wrong by a factor 15 (1 hour = 15degrees), Ray is confused between hours and degrees
#    polra=1
#elif "ASCOM.Simulator" in tel:
#    print("Accounting for ASCOM Simulator bug, correcting by applying a scalar to rates.")
#    polra=.25
#    poldec=.25
#else:
polra=1
poldec=1

#_______________________________________________________________
# Connect to the telescope
if tel.Connected:
    print("	->Telescope was already connected")
else:
    tel.Connected = True
    if tel.Connected:
        print("	Connected to telescope now")
    else:
        print("	Unable to connect to telescope, expect exception")

#_______________________________________________________________
# Querying telescope and setting the maximum tracking rates
tel.Tracking = True
print("Querying telescope:")
try:
    print("Can move axis RA Dec Rotator?", tel.CanMoveAxis(0), tel.CanMoveAxis(1), tel.CanMoveAxis(2))
    print("Axis rates count:",tel.AxisRates(0).count)
    print("Can set pier side:",tel.CanSetPierSide)
except:
    print("Your telescope mount may not use tracking rate.") 

try:    
    print("Axis rates 0-RA Max:",tel.AxisRates(0).Item(1).Maximum)
    print("Axis rates 0-RA Min:",tel.AxisRates(0).Item(1).Minimum)
    maxrarate=tel.AxisRates(0).Item(1).Maximum-0.05
except:
    print("Exception returned for RA max rate, trying default value.")
    maxrarate=4.95
try:
    print("Axis rates 1-DEC Max:",tel.AxisRates(0).Item(2).Maximum)
    print("Axis rates 1-DEC Min:",tel.AxisRates(0).Item(2).Minimum)
    maxdecrate=tel.AxisRates(0).Item(2).Maximum-0.05
except:
    print("Exception returned for DEC max rate, trying default value.")
    maxdecrate=4.95
    
print("Using the following: RA MAX rate", maxrarate,"DEC MAX rate:", maxdecrate)

#_______________________________________________________________
# Initializing telescope through ASCOM
print("\n\nInitializing telescope:")
tel.SiteLatitude  =Latitude
tel.SiteLongitude =Longitude
tel.SiteElevation =Elevation

print("UTC Time from telescope:",tel.UTCDate)
#print "Sideral Time from telescope:",tel.SiderealTime
print("Latitude:",tel.SiteLatitude)
print("Longitude:",tel.SiteLongitude)
print("Elevation:",tel.SiteElevation)
observer = ephem.Observer()
observer.long,observer.lat,observer.elevation,observer.horizon = str(Longitude),str(Latitude),Elevation,Horizon
observer.date = datetime.datetime.utcnow()

#_______________________________________________________________
# Loading the track file 
print("\n\nLoading the following track file:",csvfilename)
import csv
satco=[]
with open(csvfilename) as csvfile:
    reader=csv.reader(csvfile)
    next(reader)#skip header
    for r in reader:   
        satco.append(r)

print("Track file analysis:")
rt=ephem.Date(satco[0][1])
st=ephem.Date(satco[len(satco)-1][1])
duration=24*3600*(st-rt)          
print("Start at:",rt ,"local time.")
print("Ends at:",st ,"local time.")
print("Total duration of pass:",duration,"seconds or", int(old_div(duration,60)),"mn",int(duration % 60),"s\n")
#for i in range(len(satco)):
#    print satco[i]
 
#_______________________________________________________________
# Here we handle the delay both in time and RA, for doing dry runs 
# delay is positive for event in the future, negative for events in the past
# one hour is 0.042 delay units, because 24 hours x 0.042 = 1 day

delay=0.0 # No delay, this is the normal mode

# We want to simulate, so the delay should be such that the even is happening a few minutes from now
if simulation==1:
    delay=-1*(ephem.Date(ephem.localtime(observer.date))-rt)-0.0005
    
# Here we check if the user trying to run an old track file happening in the past or is the delay screwed up.
if (ephem.Date(ephem.localtime(observer.date))+delay)>st:
    #sys.exit("Track file happens in the past- exiting.\n" ) #exit gracefully and kill the console
    raise Exception("Track file happens in the past- exiting.\n") #or not

# Here we handle the delay to be applied to RA    
if delay != 0:
    print("WARNING - USING DELAY - DRY RUN ONLY\n")  
    print("Delay in days:", delay)  
    hh=int(delay*24)
    mm=int((delay*24-hh)*60)
    ss=delay*24*3600-(hh*3600+mm*60)
    print("Delay in hh:mm:ss",hh,":",mm,":",ss)
    # The problem is that a particular (ra, dec) will not be at the same sky position 
    # (alt, az) if the time is changed by mean of a delay, so RA also needs to be changed by an amount 
    # commensurate to the delay. Calulation happens in degree.
    rashift=(delay*24*15)%360 #convert from day to hours (x24 hours per day) then from hour to degrees (x15 degree per hour)    
    print("Delay in degrees to be applied to RA" ,rashift ,"\n\n") 
    for i in range(len(satco)):
        satco[i][2]=str((rashift+float(satco[i][2]))%360)
        #print  satco[i][2]           

#_______________________________________________________________
# Goto initial position
RA0=24*float(satco[0][2])/360
DEC0=float(satco[0][3])

td=ephem.Date(satco[0][1])-ephem.Date(ephem.localtime(observer.date))-delay
if td>0.0:
    print("Slewing to initial position:", RA0, DEC0)
    tel.SlewToCoordinates(RA0,DEC0) 
    tel.tracking=1 #because if we want to lock on the ra/dec where the sat will appear we better track    
    print("Slew to initial point completed - telescope waiting for satellite to appear - Ctrl C to interrupt...")
    print("Side of Pier, 0 is East to track West, 1 is West to track East",tel.SideOfPier) 
else:
    print("Skipping initial slew, going straight to tracking")

#_______________________________________________________________
# Waiting for the object to appear, while tracking at sideral rate
print("Current Local time:",ephem.localtime(observer.date))
print("Start Local time:",satco[0][1])
td=ephem.Date(satco[0][1])-ephem.Date(ephem.localtime(observer.date))-delay
print("Difference:" ,td,"\nInterrupt with Ctrl C\n")

while td>0:
    observer.date = datetime.datetime.utcnow()
    td=ephem.Date(satco[0][1])-ephem.Date(ephem.localtime(observer.date))-delay       
    hh=int(td*24)
    mm=int((td*24-hh)*60)
    ss=td*24*3600-(hh*3600+mm*60)
    if hh>=0 and mm>0 and (int(ss)%10)==0:     
        print(td,"Start satellite tracking in:",hh,"h",mm,"mm",int(ss),"s")#,"currently at RA:",tel.RightAscension,"Dec:",tel.declination
        sys.stdout.flush()        
        time.sleep(1)
    elif hh==0 and mm==0:
        print(td,"Start satellite tracking in:",hh,"h",mm,"mm",ss,"s")
        sys.stdout.flush()        
        winsound.Beep(2500-30*int(ss), 100)
    else:
        time.sleep(.5)

#_______________________________________________________________        
# Tracking
print("Tracking NOW...")
(era,edec)=(0.0,0.0)#errors

for i in range(len(satco)):
    observer.date = datetime.datetime.utcnow() 
    td=ephem.Date(satco[i][1])-ephem.Date(ephem.localtime(observer.date))-delay 
    
    if td<0.0: # we likely started tracking while the pass was occuring... move to current instruction
        print("Continue through", i)        
        continue
    
    RA=old_div(float(satco[i][2]),15)                    #RA in hours (as needed for slews)
    DEC=float(satco[i][3])                      #DEC in degree
    side=tel.SideOfPier                         #From ASCOM doc: Astronomy software often needs to know which pointing state the mount is in. Examples include setting guiding polarities 
    era=(15*(tel.RightAscension-RA))             # RA error in degrees (as needed for rates)
    edec=tel.Declination-DEC                     # in degree
    #Wait for the clock to match the instruction time
    while td>0:
        #time.sleep(.05)
        observer.date = datetime.datetime.utcnow() 
        td=ephem.Date(satco[i][1])-ephem.Date(ephem.localtime(observer.date))-delay
        #print "Wait at",i
    
    # the precalculated rate is adjusted from the tracking error, this becomes the actual rate sent to the telescope
    rarate=polra*float(satco[i][4]) #-.5*era    #degree for rates
    decrate=poldec*float(satco[i][5])# -.5*edec #degree for rates
    # we also make sure the rate is smaller in absolute value than the maximum rate the mount can achieve
    rasaferate=min(abs(rarate),maxrarate)*rarate/abs(rarate) #degree for rates
    decsaferate=min(abs(decrate),maxdecrate)*decrate/abs(decrate) #degree for rates
    
    #The error is too big (telescope too far from target), 
    #let's issue a slew command
    if abs(era)>2 or abs(edec)>2: #Both in degrees as needed for rates
        if i+2<len(satco):    
            RA=old_div(float(satco[i+2][2]),15) #in hour as needed for slew
            DEC=float(satco[i+2][3])   #in degree as needed for slew
        print("Slew command at",i,"Side",side, satco[i][0],"Tracking error:","E RA",era,"E Dec",edec,"RA", RA,"=",tel.RightAscension,"DEC",DEC,"=",tel.Declination,"rates",rasaferate,decsaferate)     
        sys.stdout.flush()        
        #tel.MoveAxis(0, 0.0)   #degree per second
        #tel.MoveAxis(1, 0.0)  #degree per second        
        tel.SlewToCoordinates(RA,DEC)
        tel.MoveAxis(0,rasaferate)   #degree per second
        tel.MoveAxis(1,decsaferate)  #degree per second    
    
    #The error is small, let's use variable rates for a smooth track of the target
    else:
        tel.MoveAxis(0,rasaferate)   
        tel.MoveAxis(1,decsaferate)   
        print("Move Axis",i,"Side",side, satco[i][0],"Tracking error:","E RA",era,"E Dec",edec,"RA", RA,"=",tel.RightAscension,"DEC",DEC,"=",tel.Declination,"rates",rasaferate,decsaferate)
        sys.stdout.flush()    
        #print "Target RA DEC:",RA,DEC
    
    
#_______________________________________________________________
# Stop
tel.MoveAxis(0, 0.0)   #degree per second
tel.MoveAxis(1, 0.0)  #degree per second
print("Telescope stopped...")