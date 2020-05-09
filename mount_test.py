# Test ascom driver compliance with standards
# See erellaz.com for more information
# 2018-07-15

#_______________________________________________________________
# Choose an Ascom Driver
import win32com.client      #needed to load COM objects
import ephem
import datetime
import time
import winsound
import sys


csvfilename="ISS2018-07-15223152000006.csv" # your track file
#csvfilename="ISS2018-05-26184614000005.csv" # your track file
#one hour is 0.042
#delay is positive for event in the future
#negative for events in the past
simulation=1 # if simulation mode is true, a delay is calculated so the event is transalted in time to happen now. 
delay=0.0 # Used to advance the clock to perform dry runs and test without waiting for the actual pass

Longitude = -95.123 #East is +, West is -
Latitude = 29.123  #North is +, South is -
Elevation=10        #meters
Horizon='15:00'

#Use chooser
#x = win32com.client.Dispatch("ASCOM.Utilities.Chooser")
#x.DeviceType = 'Telescope'
#driverName=x.Choose("None")
#tel=win32com.client.Dispatch(driverName)

#OR use directly one of those
#tel = win32com.client.Dispatch("Celestron.Telescope")
#tel = win32com.client.Dispatch("ASCOM.Simulator.Telescope")
tel = win32com.client.Dispatch("AstroPhysicsV2.Telescope")
print("You have choosen the following driver:",tel)

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
# Querying telescope
tel.Tracking = True
print("Querying telescope:")
print("Can move axis RA Dec Rotator?", tel.CanMoveAxis(0), tel.CanMoveAxis(1), tel.CanMoveAxis(2))
print("Axis rates count:",tel.AxisRates(0).count)
print("Axis rates 0-RA Max:",tel.AxisRates(0).Item(1).Maximum)
print("Axis rates 0-RA Min:",tel.AxisRates(0).Item(1).Minimum)
print("Axis rates 1-DEC Max:",tel.AxisRates(1).Item(1).Maximum)
print("Axis rates 1-DEC Min:",tel.AxisRates(1).Item(1).Minimum)

#_______________________________________________________________
# Initializing telescope through ASCOM
print("\n\nInitializing telescope:")
tel.SiteLatitude  =Latitude
tel.SiteLongitude =Longitude
tel.SiteElevation =Elevation

print("UTC Time from telescope:",tel.UTCDate)
#print("Sideral Time from telescope:",tel.SiderealTime)
print("Latitude:",tel.SiteLatitude)
print("Longitude:",tel.SiteLongitude)
print("Elevation:",tel.SiteElevation)
observer = ephem.Observer()
observer.long,observer.lat,observer.elevation,observer.horizon = str(Longitude),str(Latitude),Elevation,Horizon
observer.date = datetime.datetime.utcnow()

#_______________________________________________________________
#Testing
RA0=float(20)
DEC0=float(20)
print("Slewing to initial position:", RA0, DEC0)
tel.SlewToCoordinates(RA0,DEC0) 

print("Moving about axis 0-RA at 2 degree per second:")        
tel.MoveAxis(0, 0.0)   #degree per second
tel.MoveAxis(1, 0.0)  #degree per second
for i in range(1):
     tel.MoveAxis(0, 2)   #degree per second     
     print(datetime.datetime.now(),"RA:",tel.RightAscension,"Dec:",tel.Declination)
     sys.stdout.flush()     
     time.sleep(1)

print("Moving about axis 1-DEC at 4.5 degree per second:")         
tel.MoveAxis(0, 0.0)   #degree per second
tel.MoveAxis(1, 0.0)  #degree per second
for i in range(10):
     tel.MoveAxis(1, 4.5)   #degree per second     
     print(datetime.datetime.now(),"RA:",tel.RightAscension,"Dec:",tel.Declination) 
     sys.stdout.flush()     
     time.sleep(1)
     
tel.MoveAxis(0, 0.0)   #degree per second
tel.MoveAxis(1, 0.0)  #degree per second