#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   Copyright (C) 2026  Andrew Bauer

#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License along
#   with this program.  If not, see <https://www.gnu.org/licenses/>.

# Skyfield functions for Planetary Phenomena charts

###### Standard library imports ######
import datetime
#import math
import os
import sys
import errno
import socket
from urllib.request import urlopen

###### Third party imports ######
from skyfield import VERSION
from skyfield import almanac
from skyfield.api import pi, tau, wgs84, N, S, E, W
from skyfield.api import Loader
from skyfield.api import Topos
from skyfield.nutationlib import iau2000b
from skyfield.magnitudelib import planetary_magnitude
import scipy.optimize

###### Local application imports ######
import config

#---------------------------
#   Module initialization
#---------------------------

hour_of_day3 = [0, 12, 24]
hour_of_day5 = [0, 6, 12, 18, 24]
hour_of_day = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
next_hour_of_day = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
hour_of_day26 = [-2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
degree_sign= u'\N{DEGREE SIGN}'

def SkyfieldVersion(version2):      # compare Skyfield version to version2
    versions2 = [int(v) for v in version2.split(".")]
    for i in range(max(len(VERSION),len(versions2))):
        v1 = VERSION[i]   if i < len(VERSION)   else 0
        v2 = versions2[i] if i < len(versions2) else 0
        if   v1 > v2: return 1
        elif v1 < v2: return -1
    return 0

def compareVersion(version1, version2):     # compare two versions
    versions1 = [int(v) for v in version1.split(".")]
    versions2 = [int(v) for v in version2.split(".")]
    for i in range(max(len(versions1),len(versions2))):
        v1 = versions1[i] if i < len(versions1) else 0
        v2 = versions2[i] if i < len(versions2) else 0
        if v1 > v2:
            return 1
        elif v1 < v2:
            return -1
    return 0

def isConnected():
    try:
        # connect to the host -- tells us if the host is actually reachable
        sock = socket.create_connection(("www.iers.org", 80))
        if sock is not None: sock.close
        return True
    except OSError:
        pass
    # try alternate source if above server is down ...
    try:
        # connect to the host -- tells us if the host is actually reachable
        sock = socket.create_connection(("maia.usno.navy.mil", 80))
        if sock is not None: sock.close
        return True
    except OSError:
        pass
    return False    # if neither is reachable

# NOTE: the IERS server was unavailable due to maintenance work in the first 3 weeks of April 2022
#       and although the USNO server currently works, it was previously down for 2.5 years!
#       So it is still best to try using the IERS server as first oprion, and USNO as second.

def testIERSserver(filename):
    url = "ftp://ftp.iers.org/products/eop/rapid/standard/" + filename
    try:
        connection2 = urlopen(url)
    except Exception as e:
        e2 = IOError('cannot download {0} because {1}'.format(url, e))
        e2.__cause__ = None
#        raise e2
        return False
    return True     # server works

def downloadUSNO(path, filename):
    print("Downloading EOP data from USNO...", end ="")
    filepath = os.path.join(path, filename)
    url = "https://maia.usno.navy.mil/ser7/" + filename
    connection = urlopen(url)
    blocksize = 128*1024

    # Claim our own unique download filename.

    tempbase = tempname = path + filename + '.download'
    flags = getattr(os, 'O_BINARY', 0) | os.O_CREAT | os.O_EXCL | os.O_RDWR
    i = 1
    while True:
        try:
            fd = os.open(tempname, flags, 0o666)
        except OSError as e:  # "FileExistsError" is not supported by Python 2
            if e.errno != errno.EEXIST:
                raise
            i += 1
            tempname = '{0}{1}'.format(tempbase, i)
        else:
            break

    # Download to the temporary filename.

    with os.fdopen(fd, 'wb') as w:
        try:
            length = 0
            while True:
                data = connection.read(blocksize)
                if not data:
                    break
                w.write(data)
                length += len(data)
            w.flush()
        except Exception as e:
            raise IOError('error getting {0} - {1}'.format(url, e))

    # Rename the temporary file to the destination name.

    if os.path.exists(filepath):
        os.remove(filepath)
    try:
        os.rename(tempname, filepath)
    except Exception as e:
        raise IOError('error renaming {0} to {1} - {2}'.format(tempname, filepath, e))

    print("done.")

def pp_init_sf(spad):
    global ts, pandasDF, eph, earth, moon, sun, venus, mars, jupiter, saturn, mercury, objects, object_name
    
    load = Loader(spad)         # spad = folder to store the downloaded files
    EOPdf  = "finals2000A.all"  # Earth Orientation Parameters data file
    dfIERS = spad + EOPdf

    if config.useIERS:
        if SkyfieldVersion("1.31") >= 0:
            if os.path.isfile(dfIERS):
                if load.days_old(EOPdf) > float(config.ageIERS):
                    if isConnected():
                        if testIERSserver(EOPdf): load.download(EOPdf)
                        else: downloadUSNO(spad,EOPdf)
                    else: print("NOTE: no Internet connection... using existing '{}'".format(EOPdf))
                ts = load.timescale(builtin=False)	# timescale object
            else:
                if isConnected():
                    if testIERSserver(EOPdf): load.download(EOPdf)
                    else: downloadUSNO(spad,EOPdf)
                    ts = load.timescale(builtin=False)	# timescale object
                else:
                    print("NOTE: no Internet connection... using built-in UT1-tables")
                    ts = load.timescale()	# timescale object with built-in UT1-tables
        else:
            ts = load.timescale()	# timescale object with built-in UT1-tables
    else:
        ts = load.timescale()	# timescale object with built-in UT1-tables

    if config.ephndx in set([0, 1, 2, 3, 4]):

        eph = load(config.ephemeris[config.ephndx][0])	# load chosen ephemeris
        #print(eph)
        sun     = eph['sun']
        mercury = eph['mercury']
        venus   = eph['venus']
        earth   = eph['earth']
        moon    = eph['moon']
        if config.ephndx >= 3:
            mars    = eph['mars barycenter']
        else:
            mars    = eph['mars']
        jupiter = eph['jupiter barycenter']
        saturn  = eph['saturn barycenter']
        uranus  = eph['uranus barycenter']
        neptune = eph['neptune barycenter']

        objects = [sun, mercury, venus, mars, jupiter, saturn, uranus, neptune]
        object_name = ['sun', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'Sunrise', 'Sunset']

    return ts

#------------------------
#   internal functions
#------------------------

def get_object_name(obj):
    if obj is None: return ""
    if not (0 <= obj < len(object_name)): return ""
    return object_name[obj]

def norm(delta):
    # normalize the angle between 0° and 360°
    # (usually delta is roughly 15 degrees)
    while delta < 0:
        delta += 360.0
    while delta >= 360.0:
        delta -= 360.0
    return delta

def GHAcolong(gha):
    # return the colongitude, e.g. 270° returns 90°
    coGHA = gha + 180
    while coGHA > 360:
        coGHA = coGHA - 360
    return coGHA

def fmtgha(gst, ra):
    # formats angle (hours) to that used in the nautical almanac. (ddd°mm.m)
    sha = (gst - ra) * 15
    if sha < 0:
        sha = sha + 360
    return fmtdeg(sha)

def gha2deg(gst, ra):
    # convert GHA (hours) to degrees of arc
    sha = (gst - ra) * 15
    while sha < 0:
        sha = sha + 360
    return sha

def fmtdeg(deg, fixedwidth=1):
    # formats the angle (deg) to that used in the nautical almanac (ddd°mm.m)
	# the optional argument specifies the minimum width for the degrees
    theminus = ""
    if deg < 0:
    	theminus = '-'
    df = abs(deg)
    di = int(df)
    mf = round((df-di)*60, 1)	# minutes (float), rounded to 1 decimal place
    mi = int(mf)			# minutes (integer)
    if mi == 60:
        mf -= 60
        di += 1
        if di == 360:
            di = 0
    # Python 3 requires a raw string to avoid a syntax warning on 3 of the following lines...
    if fixedwidth == 2:
        gm = r"{}{:02d}$^\circ${:04.1f}".format(theminus,di,mf)
    else:
        if fixedwidth == 3:
            gm = r"{}{:03d}$^\circ${:04.1f}".format(theminus,di,mf)
        else:
            gm = r"{}{}$^\circ${:04.1f}".format(theminus,di,mf)
    return gm


#-----------------------------------------
#   Aries & planet transit calculations
#-----------------------------------------

def ariesSHA(d):            # at 00h (midnight UTC)
    t = ts.utc(d.year, d.month, d.day, 0, 0, 0)
    sha = 360 - (t.gast * 15)
    return sha

# def ariesSHA24(d, seek_SHA):    # per hour of day
# # this must be called on the day that the initial
# #     (hh = 0)SHA is higher than the value sought.
    # prev_SHA = None
    # t = ts.utc(d.year, d.month, d.day, hour_of_day, 0, 0)
    # for i in range(24):
        # sha = 360 - (t.gast[i] * 15)
        # print("  ",i,sha)
    # for i in range(24):
        # sha = 360 - (t.gast[i] * 15)
        # if sha < seek_SHA:
            # return i-1, prev_SHA
        # prev_SHA = sha
    # return 23, sha


#-------------------------------------------------------------
#   Sun and Moon calculations  (Planetary Phenomena charts)
#-------------------------------------------------------------

# def sun_declinations(d00, dmax, sf):
# # Create bspline curve coordinates in cm to plot

    # sun_XY = []          # sun bspline coordinates per day in cm
    # d_inc = d00
    # x = 0

    # while x <= dmax:
        # # compute sun's DEC at 0h of day

        # t = ts.utc(d_inc.year, d_inc.month, d_inc.day, 0, 0, 0)
        # position = earth.at(t).observe(sun)
        # #ra = position.apparent().radec(epoch='date')[0]
        # dec = position.apparent().radec(epoch='date')[1]
        # y = dec.degrees     # declination in degrees
        # xy  = "(%04.3f, %04.3f)" %(x*sf/30, y*sf/10)

        # sun_XY.append(xy)

        # x += 1
        # d_inc += datetime.timedelta(days=1)

    # return sun_XY

# def sun_merpass12(d00, dmax, sf):
# # Create bspline curve coordinates in cm to plot

    # sun_XY = []          # sun bspline coordinates per day in cm
    # d_inc = d00
    # x = 0

    # while x <= dmax:
        # # compute sun's MerPass at 12h of day

        # t12 = ts.utc(d_inc.year, d_inc.month, d_inc.day, 12, 0, 0)  # EoT at 12h
        # position = earth.at(t12).observe(sun)
        # ra = position.apparent().radec(epoch='date')[0]
        # #dec = position.apparent().radec(epoch='date')[1]
        # gha12 = gha2deg(t12.gast, ra.hours)
        # mpa12 = gha_mpa(gha12)

        # xy  = "(%04.3f, %04.3f)" %(x*sf/10, mpa12*sf)

        # sun_XY.append(xy)

        # x += 1
        # d_inc += datetime.timedelta(days=1)

    # return sun_XY


#---------------------------------------------------------
#   Twilight calculations  (Planetary Phenomena charts)
#---------------------------------------------------------

def rise_set(t, y, lats):
    # analyse the return values from the 'find_discrete' method...
    # return a list of rise and set datetimes (if any)
    # 'finalstate' is True if above horizon; False if below horizon; None if unknown
    dt0 = dt1 = dt2 = None
    dt_rise = []
    dt_set  = []
    finalstate = None

    if len(t) == 2:     # this happens most often
        dt0 = t[0].utc_datetime()
        dt1 = t[1].utc_datetime()
        if y[0] and not(y[1]):
            dt_rise.append(dt0)
            dt_set.append(dt1)
            finalstate = False
        elif not(y[0]) and y[1]:
            dt_set.append(dt0)
            dt_rise.append(dt1)
            finalstate = True
        else:
            # this should never get here!
            rise_set_error(y,lats,dt0)
    elif len(t) == 1:     # this happens ocassionally
        dt0 = t[0].utc_datetime()
        if y[0]:
            dt_rise.append(dt0)
            finalstate = True
        else:
            dt_set.append(dt0)
            finalstate = False
    elif len(t) == 3:       # this happens rarely (in high latitudes mid-year)
        dt0 = t[0].utc_datetime()
        dt1 = t[1].utc_datetime()
        dt2 = t[2].utc_datetime()
        if y[0] and not(y[1]) and y[2]:
            dt_rise.append(dt0)
            dt_set.append(dt1)
            dt_rise.append(dt2)
            finalstate = True
        elif not(y[0]) and y[1] and not(y[2]):
            dt_set.append(dt0)
            dt_rise.append(dt1)
            dt_set.append(dt2)
            finalstate = False
        else:
            # this should never get here!
            rise_set_error(y,lats,dt0)
    elif len(t) > 3:
        rise_set_error(y,lats,dt0)

    return dt_rise, dt_set, finalstate

def rise_set_error(y, lats, dt0):
    # unexpected rise/set values - format message line
    lns = 'N' if lats >= 0.0 else 'S'
    msg = "rise_set {} values for {:4.1f}°{}: {}".format(len(y),abs(lats),lns,y[0])
    # msg = "rise_set {} values for {}: {}".format(len(y),lats, y[0])
    if len(y) > 1:
        msg = msg + " {}".format(y[1])
    if len(y) > 2:
        msg = msg + " {}".format(y[2])
    if len(y) > 3:
        msg = msg + " {}".format(y[3])
    # print to console
    if dt0 is not None:
        print("{}   {}".format(dt0.isoformat(), msg))
    else:
        print(msg)
    sys.exit(0)

def sunrise_set(d, sun_Y, dmax, params, sf):
# calculate Sunrise/Sunset/Dawn/Dusk times at chosen latitude

    # For the given month offset within the chosen year, return these values
    #   pertaining to sunrise/sunset times at 51.5°N 0.0°E:
    # ndx           = day offset within year (= dayofyear - 1)
    # sunAM         = sunrise scaled XY coordinates as text
    # sunPM         = sunset  scaled XY coordinates as text
    # sunriseY      = sunrise Y coordinate (unscaled)
    # sunsetY       = sunset  Y coordinate (unscaled)
    # civil_twiAM   = civil dawn scaled XY coordinates as text
    # civil_twiPM   = civil dusk scaled XY coordinates as text
    # civilY_AM     = civil dawn Y coordinate (unscaled)
    # civilY_PM     = civil dusk Y coordinate (unscaled)

    dt = datetime.datetime(d.year, d.month, d.day, 0, 0, 0)  # convert to datetime
    sunAM = []
    sunPM = []
    sunriseY = []
    sunsetY  = []
    civil_twiAM = []
    civil_twiPM = []
    civilY_AM = []
    civilY_PM = []
    durationAM_min = None   # in minutes of time
    durationAM_max = None   # in minutes of time
    durationPM_min = None   # in minutes of time
    durationPM_max = None   # in minutes of time
    # lats = "51.5 N"
    lats, dbh = params  # tuple: latitude and twilight value (degrees below horizon)
    hemisph = 'N' if lats >= 0 else 'S'
    locn = Topos("{:3.1f} {}".format(abs(lats),hemisph), "0.0 E")
    # locn = Topos(lats, "0.0 E")

    t0 = None
    idx = 0
    while idx <= dmax:      # includes 1st Jan of next year
        if t0 is None:
            t0 = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        t1 = ts.utc(dt.year, dt.month, dt.day+1, dt.hour, dt.minute, dt.second)

        # Sunrise/Sunset time...
        #   (the standard refraction angle is 0.56667 = 34 arcminutes,
        #    by which the image of the object is raised at the horizon.
        #    Solar radius = 0.26663 degrees = 16 arcminutes)
        event0, y = almanac.find_discrete(t0, t1, daylength(locn, 0.8333))
        dt_rise, dt_set, finalstate = rise_set(event0, y, lats)

        for dt0 in dt_rise:
            hoursAM = dt0.hour + dt0.minute/60 + dt0.second/3600
            sunriseY.append(hoursAM)
            if config.orthogonal:
                xy_txt  = "(%04.3f, %04.3f)" %(idx*sf/10, hoursAM*sf)
            else:
                x = idx + (hoursAM/24.0)
                xy_txt  = "(%04.3f, %04.3f)" %(x*sf/10, hoursAM*sf)
            sunAM.append(xy_txt)    # XY scaled coordinates of sunrise

        for dt1 in dt_set:
            hoursPM = dt1.hour + dt1.minute/60 + dt1.second/3600
            sunsetY.append(hoursPM)
            if config.orthogonal:
                xy_txt  = "(%04.3f, %04.3f)" %(idx*sf/10, hoursPM*sf)
            else:
                x = idx + (hoursPM/24.0)
                xy_txt  = "(%04.3f, %04.3f)" %(x*sf/10, hoursPM*sf)
            sunPM.append(xy_txt)     # XY scaled coordinates of sunset

        # Civil Twilight duration...
        event1, y = almanac.find_discrete(t0, t1, daylength(locn, dbh))
        dt_rise, dt_set, finalstate = rise_set(event1, y, lats)

        for dt0 in dt_rise:
            # note: sun's Meridian Passage 'sun_Y' is pre-calculated
            hours2 = dt0.hour + dt0.minute/60 + dt0.second/3600
            duration2 = hoursAM - hours2     # sunrise time - civil twilight AM
            y_AM = sun_Y[idx] - duration2
            civilY_AM.append(y_AM)
            if config.orthogonal:
                xy_txt  = "(%04.3f, %04.3f)" %(idx*sf/10, y_AM*sf)
            else:
                x = idx + (y_AM/24.0)
                xy_txt  = "(%04.3f, %04.3f)" %(x*sf/10, y_AM*sf)
            civil_twiAM.append(xy_txt)  # XY scaled coordinates of civil twilight AM offset

        for dt1 in dt_set:
            hours3 = dt1.hour + dt1.minute/60 + dt1.second/3600
            duration3 = hours3 - hoursPM     # civil twilight PM - sunset time
            y_PM = sun_Y[idx] + duration3
            civilY_PM.append(y_PM)
            if config.orthogonal:
                xy_txt  = "(%04.3f, %04.3f)" %(idx*sf/10, y_PM*sf)
            else:
                x = idx + (y_PM/24.0)
                xy_txt  = "(%04.3f, %04.3f)" %(x*sf/10, y_PM*sf)
            civil_twiPM.append(xy_txt)  # XY scaled coordinates of civil twilight PM offset

        if False:
            # statistics: collect min/max civil twilight duration AM/PM in year
            dur2 = duration2 * 60.0
            if durationAM_min is None:
                durationAM_min = dur2
            else:
                if dur2 < durationAM_min: durationAM_min = dur2
            if durationAM_max is None:
                durationAM_max = dur2
            else:
                if dur2 > durationAM_max: durationAM_max = dur2

            dur3 = duration3 * 60.0
            if durationPM_min is None:
                durationPM_min = dur3
            else:
                if dur3 < durationPM_min: durationPM_min = dur3
            if durationPM_max is None:
                durationPM_max = dur3
            else:
                if dur3 > durationPM_max: durationPM_max = dur3

        t0 = t1
        idx += 1
        dt += datetime.timedelta(days=1)

    if False:
        print("civil twilight AM lasts from {:.2f} to {:.2f} minutes in {}".format(durationAM_min, durationAM_max,d.year))
        print("civil twilight PM lasts from {:.2f} to {:.2f} minutes in {}".format(durationPM_min, durationPM_max,d.year))

    return sunAM, sunPM, sunriseY, sunsetY, civil_twiAM, civil_twiPM, civilY_AM, civilY_PM

def daylength(topos, degBelowHorizon):
    # Build a function of time that returns the daylength.
    topos_at = (earth + topos).at

    def is_sun_up_at(t):
        """The function that this returns will expect a single argument that is a 
		:class:`~skyfield.timelib.Time` and will return ``True`` if the sun is up
		or twilight has started, else ``False``."""
        t._nutation_angles = iau2000b(t.tt)
        # Return `True` if the sun has risen by time `t`.
        return topos_at(t).observe(sun).apparent().altaz()[0].degrees > -degBelowHorizon

    is_sun_up_at.rough_period = 0.5  # twice a day
    return is_sun_up_at

#-----------------------------------------------------
#   Twilight calculations  (Planet Visibility charts)
#-----------------------------------------------------

# NOTE:
#   A planet can have multiple rise & set times per day, e.g. Saturn
#     rises:  2015-03-20T00:03:10.584306+00:00
#     rises:  2015-03-20T23:59:10.736361+00:00
#     sets:   2015-07-26T00:01:28.261903+00:00
#     sets:   2015-07-26T23:57:28.934374+00:00
#   thus objriseY/objsetY can be a single value or a list of values

def objrise_set3(d, dmax, params):
# collect planet rise/set times at latitude 'lats'
    # idx   = day offset within year (= dayofyear - 1)
    # seg   = graph curve segment number
    # i     - index within segment

    # For the given year, return a list of tuples per day with these values
    #   idx             = day offset within year (= dayofyear - 1)
    #   riseset_time    = list of (True and False) event times per day
    #   isrise          = list of the Rise or Set value per event
    #   isTrue          = list of the True/False value per event

    obj, lats, orthogonal = params      # tuple: planet, the latitude and orthogonal data (True/False)
    dt = datetime.datetime(d.year, d.month, d.day, 0, 0, 0)  # convert to datetime
    planet = objects[obj]
    topos = wgs84.latlon(lats, 0.0, elevation_m=0.0)
    observer = earth + topos

# calculate planet rise/set times at latitude 'lats' for a month offset (0 to 11)

    t0 = None
    idx = 0
    data_per_year = []         # data to return

    while idx < dmax:       # includes 1st Jan of next year (for an orthogonal data plot only)
        if t0 is None:
        # do NOT use 'ts.ut1' as the date returned can be outside the requested boundary
        #   e.g. Saturn 2042 Feb 13 60°N returns RISE at 14 Feb 00:00:00
            t0 = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        t1 = ts.utc(dt.year, dt.month, dt.day+1, dt.hour, dt.minute, dt.second)

        planetrise, iR = almanac.find_risings(observer, planet, t0, t1)
        planetset,  iS = almanac.find_settings(observer, planet, t0, t1)

        lenR = len(planetrise); lenS = len(planetset)
        no_events = False
        riseset_time = []; isrise = []; isTrue = []     # clear these lists every day

        if (lenR + lenS) > 0:
            # assemble events in chronological order storing the data in 3 separate lists
            ndxR = ndxS = 0
            while ndxR < lenR or ndxS < lenS:
                if ndxR < lenR and ndxS < lenS:
                    if planetrise[ndxR] < planetset[ndxS]:
                        riseset_time.append(planetrise[ndxR]); isrise.append(True); isTrue.append(iR[ndxR])
                        riseset_time.append(planetset[ndxS]); isrise.append(False); isTrue.append(iS[ndxS])
                    else:
                        riseset_time.append(planetset[ndxS]); isrise.append(False); isTrue.append(iS[ndxS])
                        riseset_time.append(planetrise[ndxR]); isrise.append(True); isTrue.append(iR[ndxR])
                    ndxR += 1; ndxS += 1
                elif ndxR < lenR:
                    riseset_time.append(planetrise[ndxR]); isrise.append(True); isTrue.append(iR[ndxR])
                    ndxR += 1
                elif ndxS < lenS:
                    riseset_time.append(planetset[ndxS]); isrise.append(False); isTrue.append(iS[ndxS])
                    ndxS += 1
            # ----------------------------------------- end of 'while'

        # collect RISE/SET data per day...
        data_per_year.append((idx, riseset_time, isrise, isTrue))

        t0 = t1
        idx += 1
        dt += datetime.timedelta(days=1)

    # ----------------------------------------- end of 'while'

    return data_per_year


def sunrise_set2(d, dmax, params, sf):  # called from ppc_buildchart3.py
# calculate Sunrise/Sunset/Dawn/Dusk times at chosen latitude

    # For the given year, return these values
    #   pertaining to sunrise/sunset times at 51.5°N 0.0°E:
    # ndx           = day offset within year (= dayofyear - 1)
    # sunAM         = sunrise scaled XY coordinates as text
    # sunPM         = sunset  scaled XY coordinates as text
    # sunriseY      = sunrise Y coordinate (unscaled)
    # sunsetY       = sunset  Y coordinate (unscaled)
    # civil_twiAM   = civil dawn scaled XY coordinates as text
    # civil_twiPM   = civil dusk scaled XY coordinates as text
    # civilY_AM     = civil dawn Y coordinate (unscaled)
    # civilY_PM     = civil dusk Y coordinate (unscaled)

    dt = datetime.datetime(d.year, d.month, d.day, 0, 0, 0)  # convert to datetime
    sunAM = []
    sunPM = []
    sunriseY = []
    sunsetY  = []
    civil_twiAM = []
    civil_twiPM = []
    civilY_AM = []
    civilY_PM = []
    durationAM_min = None   # in minutes of time
    durationAM_max = None   # in minutes of time
    durationPM_min = None   # in minutes of time
    durationPM_max = None   # in minutes of time
    # lats = "51.5 N"
    lats, dbh, orthogonal = params  # tuple: latitude, twilight value (degrees below horizon) and orthogonal data (True/False)
    # hemisph = lats[-1]
    hemisph = 'N' if lats >= 0 else 'S'
    locn = Topos("{:3.1f} {}".format(abs(lats),hemisph), "0.0 E")

    t0 = None
    idx = 0
    while idx < dmax:      # includes 1st Jan of next year (for an orthogonal data plot only)
        hoursAM = hoursPM = None
        if t0 is None:
            t0 = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        t1 = ts.utc(dt.year, dt.month, dt.day+1, dt.hour, dt.minute, dt.second)

        # Sunrise/Sunset time...
        event0, y = almanac.find_discrete(t0, t1, daylength(locn, 0.8333))
        dt_rise, dt_set, finalstate0 = rise_set(event0, y, lats)

        if len(dt_rise) > 0:
            for dt0 in dt_rise:
                hoursAM = dt0.hour + dt0.minute/60 + dt0.second/3600
                sunriseY.append(hoursAM)
                if orthogonal:
                    xy_txt  = "(%04.3f, %04.3f)" %(idx*sf/10, hoursAM*sf)
                else:
                    x = idx + (hoursAM/24.0)
                    xy_txt  = "(%04.3f, %04.3f)" %(x*sf/10, hoursAM*sf)
                sunAM.append(xy_txt)    # XY scaled coordinates of sunrise
        else:
            sunriseY.append(None)
            sunAM.append(None)

        if len(dt_set) > 0:
            for dt1 in dt_set:
                hoursPM = dt1.hour + dt1.minute/60 + dt1.second/3600
                sunsetY.append(hoursPM)
                if orthogonal:
                    xy_txt  = "(%04.3f, %04.3f)" %(idx*sf/10, hoursPM*sf)
                else:
                    x = idx + (hoursPM/24.0)
                    xy_txt  = "(%04.3f, %04.3f)" %(x*sf/10, hoursPM*sf)
                sunPM.append(xy_txt)     # XY scaled coordinates of sunset
        else:
            sunsetY.append(None)
            sunPM.append(None)

        # Civil Twilight duration...
        event1, y = almanac.find_discrete(t0, t1, daylength(locn, dbh))
        ct_rise, ct_set, finalstate1 = rise_set(event1, y, lats)

        if len(ct_rise) > 0:
            for dt0 in ct_rise:
                y_AM = dt0.hour + dt0.minute/60 + dt0.second/3600
                if hoursAM is None:
                    hoursAM = y_AM if finalstate0 else 12.0
                duration2 = hoursAM - y_AM  # sunrise time - civil twilight AM
                civilY_AM.append(y_AM)
                if orthogonal:
                    xy_txt  = "(%04.3f, %04.3f)" %(idx*sf/10, y_AM*sf)
                else:
                    x = idx + (y_AM/24.0)
                    xy_txt  = "(%04.3f, %04.3f)" %(x*sf/10, y_AM*sf)
                civil_twiAM.append(xy_txt)  # XY scaled coordinates of civil twilight AM offset
        else:
            civilY_AM.append(None)
            civil_twiAM.append(None)

        if len(ct_set) > 0:
            for dt1 in ct_set:
                y_PM = dt1.hour + dt1.minute/60 + dt1.second/3600
                if hoursPM is None:
                    hoursPM = y_PM if finalstate0 else 12.0
                duration3 = y_PM - hoursPM  # civil twilight PM - sunset time
                civilY_PM.append(y_PM)
                if orthogonal:
                    xy_txt  = "(%04.3f, %04.3f)" %(idx*sf/10, y_PM*sf)
                else:
                    x = idx + (y_PM/24.0)
                    xy_txt  = "(%04.3f, %04.3f)" %(x*sf/10, y_PM*sf)
                civil_twiPM.append(xy_txt)  # XY scaled coordinates of civil twilight PM offset
        else:
            civilY_PM.append(None)
            civil_twiPM.append(None)

        if True:
            # statistics: collect min/max civil twilight duration AM/PM in year
            dur2 = duration2 * 60.0
            if durationAM_min is None:
                durationAM_min = dur2
            else:
                if dur2 < durationAM_min: durationAM_min = dur2
            if durationAM_max is None:
                durationAM_max = dur2
            else:
                if dur2 > durationAM_max: durationAM_max = dur2

            dur3 = duration3 * 60.0
            if durationPM_min is None:
                durationPM_min = dur3
            else:
                if dur3 < durationPM_min: durationPM_min = dur3
            if durationPM_max is None:
                durationPM_max = dur3
            else:
                if dur3 > durationPM_max: durationPM_max = dur3

        t0 = t1
        idx += 1
        dt += datetime.timedelta(days=1)

    if True:
        print("civil twilight AM lasts from {:.2f} to {:.2f} minutes in {}".format(durationAM_min, durationAM_max,d.year))
        print("civil twilight PM lasts from {:.2f} to {:.2f} minutes in {}".format(durationPM_min, durationPM_max,d.year))

    return sunAM, sunPM, sunriseY, sunsetY, civil_twiAM, civil_twiPM, civilY_AM, civilY_PM

def midnightsun(d, hemisph):
    # simple way to fudge whether the sun is up or down when there's no
    # sunrise or sunset on date 'dt' depending on the hemisphere only.

    sunup = False
    n = d.month
    if n > 3 and n < 10:    # if April to September inclusive
        sunup = True
    if hemisph == 'S':
        sunup = not(sunup)
    return sunup

#---------------------------------------------------------------------------------------
#   Venus, Mars, Jupiter, Saturn & Mercury calculations  (Planetary Phenomena charts)
#---------------------------------------------------------------------------------------

def planet_elevation(obj, dtX, lats):
    # return planet elevation at specified datetime

    planet = objects[obj]
    topos = wgs84.latlon(lats, 0.0 * E, elevation_m=0.0)
    observer = earth + topos
    degBelowHorizon = 34.0 / 60         # 34' atmospheric refraction in degrees
    # planet_elev = planet elevation in degrees
    planet_elev = observer.at(dtX).observe(planet).apparent().altaz()[0].degrees
    above_horizon = (planet_elev > -degBelowHorizon)

    return planet_elev, above_horizon

def planet_altitude(obj, d00, lats):
    
    planet = objects[obj]
    dt = datetime.datetime(d00.year, d00.month, d00.day, 0, 0, 0)  # convert to datetime
    topos = wgs84.latlon(lats, 0.0 * E, elevation_m=0.0)
    observer = earth + topos

    # check each hour on Jan 1 for an altitude that is >= 3° above or below the horizon
    # (because altitude angles close to 0.0 degrees can be misleading)
    for hr in range(24):
        t5 = ts.utc(dt.year, dt.month, dt.day, dt.hour+hr, dt.minute, dt.second)
        astro = observer.at(t5).observe(planet)
        app = astro.apparent()
        alt, az, distance = app.altaz('standard')   # compensate for refraction using standard temperature and pressure
        if abs(alt.degrees) > 3.0: break
        if hr == 23:
            objn = config.objnames[obj-1]
            lns = 'N' if lats >= 0.0 else 'S'

            print("Altitude could not be determined for {} in {} at latitude {}°{}".format(objn,d00.year,abs(lats),lns)); sys.exit(0)

    return True if alt.degrees > 0.0 else False     # True if planet above the horizon

def planet_declinations(obj, d00, dmax, sf):
# Create bspline curve coordinates in cm to plot

    planet = objects[obj]
    planet_XY = []      # planet plot coordinates per day in cm
    planet_Y  = []      # planet declination (degrees) per day at 0h
    d_inc = d00
    x = 0

    while x <= dmax:
        # compute sun's/planet's DEC at 0h of day

        t = ts.utc(d_inc.year, d_inc.month, d_inc.day, 0, 0, 0)
        position = earth.at(t).observe(planet)
        #ra = position.apparent().radec(epoch='date')[0]
        dec = position.apparent().radec(epoch='date')[1]
        y = dec.degrees     # declination in degrees
        xy  = "(%04.3f, %04.3f)" %(x*sf/30, y*sf/10)

        planet_Y.append(y)
        planet_XY.append(xy)

        x += 1
        d_inc += datetime.timedelta(days=1)

    return object_name[obj], planet_XY, planet_Y

def gha00_mpa(gha, prev_mpa):
    # return the hour angle as 'Mer. Pass' hours float
    new_curve = False
    if gha > 180:
        gha = 360 - gha
        mpa = gha / 15.0        # (gha * 4.0)/60.0
    else:
        mpa = 24 - (gha / 15.0) # 24 - (gha * 4.0)/60.0

    if prev_mpa is not None:
        if abs(mpa - prev_mpa) > 20: new_curve = True
    #print("gha {:.2f} mpa {:.1f} {}".format(gha,mpa,new_curve))

    return mpa, new_curve

def MerPass(obj, d00, dmax, sf, AppPos=False):      # for ppc_build.py (and optionally ppc_buildchart2.py)
# calculate sun or planet mertidian passage times
    # idx   = day offset within year (= dayofyear - 1)
    # seg   = graph curve segment number
    # i     - index within segment

    # For the given year, return these values for the sun (no segments!)
    # object_Y[idx]       - sun's  Meridian Passage Y coordinate (unscaled)
    # object_XY_txt[idx]  - sun's Meridian Passage scaled XY coordinates as text
    # object_name         - 'sun'
    # object_xidx         - empty list (no data)
    # sunUP_XY            - XY scaled coordinates 45 minutes above Sun's MerPass
    # sunDN_XY            - XY scaled coordinates 45 minutes below Sun's MerPass

    # For the given year, return these values for a planet
    # object_Y[idx]         - planet Meridian Passage Y coordinate (unscaled) or list
    # object_XY_txt[seg][i] - planet Meridian Passage scaled XY coordinates as text
    # object_name           - the planet name
    # object_xidx           - idx when mpa00 goes below 0h or above 24h
    # mp_offset             - starting date offset per 'object_XY_txt' segment

    if obj == 0:    # if SUN
        sunUP_XY = []   # XY scaled coordinates 45 minutes above Sun's MerPass
        sunDN_XY = []   # XY scaled coordinates 45 minutes below Sun's MerPass
    planet = objects[obj]
    object_Y = []       # object curve coordinates per day in units '1 hour / 10 days'
    # daily object curve coordinates per segment (3 max) as text:
    object_XY_txt = [[] for i in range(3)]  # object_XY_txt[0 to 2][0 to 364/365]
    app_pos = []        # list of apparent positions at 00h per day
    mp_offset = []      # starting date offset per 'object_XY_txt' segment

    # collect a list of days on which the LMTMP crosses over the 0h/24h border...
    # normally we expect zero or one crossing, notably for Jupiter and Saturn,
    # however as the period is close to one year, we must be prepared that there
    # may be two border crossings in one year. Hence a list is initialised below.
    object_xidx = []    # idx when mpa00 goes below 0h or above 24h
                        # note: idx-1 is before switch; idx is after

    d_inc = datetime.datetime(d00.year, d00.month, d00.day, 0, 0, 0)  # convert to datetime
    idx = 0
    mp_offset.append(idx)
    n = 0       # count curve segments

    t0 = None
    prev_mpas = None
    new_curve = False
    # m2h = 1.0 / 60.0
    # s2h = 1.0 / 3600.0
    lats = 0.0     # default latitude (any will do)
    topos = wgs84.latlon(lats, 0.0 * E, elevation_m=0.0)
    observer = earth + topos

    while idx < dmax:       # includes 1st Jan of next year (for an orthogonal data plot only)
        # compute sun's/planet's MerPass at 00h of day

        if t0 is None:              # initialize t0 if Jan 1
            t0 = ts.utc(d_inc.year, d_inc.month, d_inc.day, d_inc.hour, d_inc.minute, d_inc.second)
        t1 = ts.utc(d_inc.year, d_inc.month, d_inc.day+1, d_inc.hour, d_inc.minute, d_inc.second)
        if AppPos:      # if apparent positions at t0 required
            position = earth.at(t0).observe(planet)    # astrometric position
            apparent = position.apparent()
            app_pos.append(apparent)

        t_all = almanac.find_transits(observer, planet, t0, t1)
        for t in t_all:     # for each transit time within 1 day
            # t_utc = t.utc    # calendar tuple in UTC (i.e. year, month, day, hour, minute, second)
            t_utc = t.utc_datetime()    # python datetime
            # mpas = t_utc.timestamp()
            # t_utc = t_utc.time()
            mpas = t_utc.hour + t_utc.minute/60.0 + t_utc.second/3600.0     #TEMPORARY#
            #mpas = t_utc.hour + t_utc.minute/60.0 + (t_utc.second + t_utc.microsecond/1000000.0)/3600.0
            # print(mpas)
            if prev_mpas is not None:
                new_curve = True if abs(mpas - prev_mpas) > 20 else False
            prev_mpas = mpas

        if new_curve:
            n += 1    # new curve segment
            object_xidx.append(idx-1)   # append the *previous* date offset
            mp_offset.append(idx)

        object_Y.append(mpas)     # one list of Y coordinates; without scaling factor
        if config.orthogonal:
            xy_txt  = "(%04.3f, %04.3f)" %(idx*sf/10, mpas*sf)
        else:
            x = idx + (mpas/24.0)
            xy_txt  = "(%04.3f, %04.3f)" %(x*sf/10, mpas*sf)
        object_XY_txt[n].append(xy_txt) # XY scaled coordinates of sun/planet

        if obj == 0:
           xyUP =  "(%04.3f, %04.3f)" %(idx*sf/10, (mpas+0.75)*sf)
           xyDN =  "(%04.3f, %04.3f)" %(idx*sf/10, (mpas-0.75)*sf)
           sunUP_XY.append(xyUP)
           sunDN_XY.append(xyDN)

        t0 = t1
        idx += 1
        d_inc += datetime.timedelta(days=1)

    if obj == 0:
        return object_Y, object_XY_txt, object_name[obj], object_xidx, sunUP_XY, sunDN_XY
    if AppPos:
        return object_Y, object_XY_txt, object_name[obj], object_xidx, mp_offset, app_pos
    else:
        return object_Y, object_XY_txt, object_name[obj], object_xidx, mp_offset

# MerPass (above) is more accurate than 'merpass00' (below) however 'merpass00'
#   is nearly 3 times faster (20 sec vs 55 sec)
def merpass00(obj, d00, dmax, sf):      # used by ppc_buildchart2.py
# Create bspline daily curve coordinates to plot in units '1 hour / 10 days'

# NOTE: this is NOT a Meridian Passage calculation precise to the millisecond ...
#       the planet's position is taken at 00h and then the earth is effectively
#       rotated until the planet's upper meridian is overhead ... then convert
#       the rotation angle into time. This assumes that the planet is stationary
#       for up to 24 hours, which is obviously not the case.
#       However on a plot spanning a whole year the discrepancy is negligible.

    if obj == 0:    # if SUN
        sunUP_XY = []   # XY scaled coordinates 45 minutes above Sun's MerPass
        sunDN_XY = []   # XY scaled coordinates 45 minutes below Sun's MerPass
    planet = objects[obj]
    object_Y = []       # object curve coordinates per day in units '1 hour / 10 days'
    # daily object curve coordinates per segment (3 max) as text:
    object_XY_txt = [[] for i in range(3)]  # object_XY_txt[0 to 2][0 to 364/365]
    app_pos = []        # list of apparent positions at 00h per day
    mp_offset = []      # starting date offset per 'object_XY_txt' segment

    # collect a list of days on which the LMTMP crosses over the 0h/24h border...
    # normally we expect zero or one crossing, notably for Jupiter and Saturn,
    # however as the period is close to one year, we must be prepared that there
    # may be two border crossings in one year. Hence a list is initialised below.
    object_xidx = []    # idx when mpa00 goes below 0h or above 24h
                        # note: idx-1 is before switch; idx is after

    d_inc = d00
    idx = 0
    mp_offset.append(idx)
    n = 0       # count curve segments
    prev_mpa = None

    while idx <= dmax:
        # compute sun's/planet's MerPass at 00h of day

        t00 = ts.utc(d_inc.year, d_inc.month, d_inc.day, 0, 0, 0)  # at 00h
        position = earth.at(t00).observe(planet)    # astrometric position
        apparent = position.apparent()
        app_pos.append(apparent)
        ra = apparent.radec(epoch='date')[0]
        #dec = apparent.radec(epoch='date')[1]
        gha00 = gha2deg(t00.gast, ra.hours)
        mpa00, new_curve = gha00_mpa(gha00, prev_mpa)
        prev_mpa = mpa00
        if new_curve:
            n += 1    # new curve segment
            object_xidx.append(idx-1)   # append the *previous* date offset
            mp_offset.append(idx)

        object_Y.append(mpa00)     # one list of Y coordinates; without scaling factor
        xy_txt  = "(%04.3f, %04.3f)" %(idx*sf/10, mpa00*sf)
        object_XY_txt[n].append(xy_txt) # XY scaled coordinates of sun/planet

        if obj == 0:
           xyUP =  "(%04.3f, %04.3f)" %(idx*sf/10, (mpa00+0.75)*sf)
           xyDN =  "(%04.3f, %04.3f)" %(idx*sf/10, (mpa00-0.75)*sf)
           sunUP_XY.append(xyUP)
           sunDN_XY.append(xyDN)

        idx += 1
        d_inc += datetime.timedelta(days=1)

    if obj == 0:
        return object_Y, object_XY_txt, object_name[obj], object_xidx, sunUP_XY, sunDN_XY
    return object_Y, object_XY_txt, object_name[obj], object_xidx, mp_offset, app_pos


# ------------ ECLIPTIC COORDINATES (source: Brandon Rhodes) ------------
# Ecliptic coordinates are measured from the plane of the Earth’s orbit. 
# They are useful when making maps and diagrams of the Solar System and
# when exploring the properties of orbits around the Sun, because they
# place the orbits of the major planets nearly flat against the xy-plane
# — unlike right ascension and declination, which twist the Solar System
# up at a 23° angle because of the tilt of the Earth’s axis.
#
#          xy-plane: Ecliptic plane (plane of Earth’s orbit)
#          x-axis: March equinox
#          z-axis: North ecliptic pole
#          ↕ Latitude ±90° above or below the ecliptic
#          ↔ Longitude 0°–360° measured east from March equinox
# -----------------------------------------------------------------------

# NOT USED ...
def ecliptic_lon(obj, d00, dmax):
# Obtain ecliptic longitude of a solar system body per day of year
# Obtain magnitude of a solar system body per day of year
# 'obj' can be the sun or any solar system planet

    planet = objects[obj]
    planet_lon = []     # list of angles in radians
    planet_mag = []     # list of magnitudes
    d_inc = d00
    x = 0

    while x < dmax:
        # compute ecliptic latitide/longitude per day

        t00 = ts.utc(d_inc.year, d_inc.month, d_inc.day, 0, 0, 0)   # at 0h
        position = earth.at(t00).observe(planet)
        lat, lon, distance = position.apparent().ecliptic_latlon()
        mag = None
        if obj != 0:    # exclude the sun
            mag = planetary_magnitude(position)     # planetary magnitude

        planet_lon.append(lon.radians)
        planet_mag.append(mag)

        x += 1
        d_inc += datetime.timedelta(days=1)

    return planet_lon, planet_mag

def planet_mag(obj, d, h=0):
# Obtain magnitude of a solar system body on date 'd' and hour 'h' (default 0h)
# 'obj' can be the sun or any solar system planet

    planet = objects[obj]
    t00 = ts.utc(d.year, d.month, d.day, h, 0, 0)   # at 'h' hours
    position = earth.at(t00).observe(planet)
    #lat, lon, distance = position.apparent().ecliptic_latlon()
    planet_mag = planetary_magnitude(position)     # planetary magnitude

    return planet_mag

# used in ppc_buildchart2.chart2page2
def planets_near(objA, objB, dmax, degsep, planet_app_pos):
# return date offset ranges within a year as tuples when planet separation is < degsep

    x = 0
    close = False
    x_fr = None
    close_tup = []
    
    while x < dmax:
        # 0 <= sep <= 180 below...
        sep = planet_app_pos[objA-1][x].separation_from(planet_app_pos[objB-1][x]).degrees
        if sep < degsep:
            if not close:
                close = True
                x_fr = x
        else:
            if close:
                close = False
                close_tup.append((x_fr, x-1))
                x_fr = None
        x += 1

    # terminate range if close at end of year
    if close:
        close_tup.append((x_fr, x-1))
    
    return close_tup

# used in ppc_buildchart2.chart2page2  (Venus & Jupiter)
def relative_lon(objA, objB, dstart, dmax):
# Obtain relative ecliptic longitude of two solar system bodies per day
# 'objA/objB' can be the sun or any solar system planet

    planetA = objects[objA]
    planetB = objects[objB]
    rel_lon = []        # list of angles in radians
    d_inc = dstart
    x = 0

    while x <= dmax:
        # compute ecliptic latitide/longitude per day

        t00 = ts.utc(d_inc.year, d_inc.month, d_inc.day, 0, 0, 0)   # at 0h
        positionA = earth.at(t00).observe(planetA)
        latA, lonA, distanceA = positionA.apparent().ecliptic_latlon()
        positionB = earth.at(t00).observe(planetB)
        latB, lonB, distanceB = positionB.apparent().ecliptic_latlon()

        relative_lon = (lonB.radians - lonA.radians + pi) % tau - pi

        rel_lon.append(relative_lon)

        x += 1
        d_inc += datetime.timedelta(days=1)

    return rel_lon

# NOT USED ...
def relative_RAlon(objA, objB, dstart, dmax):
# Obtain relative RA longitude of two solar system bodies per day
# 'objA/objB' can be the sun or any solar system planet

    planetA = objects[objA]
    planetB = objects[objB]
    rel_lon = []        # list of angles in radians
    d_inc = dstart
    x = 0

    while x <= dmax:
        # compute RA latitide/longitude per day

        t00 = ts.utc(d_inc.year, d_inc.month, d_inc.day, 0, 0, 0)   # at 0h
        positionA = earth.at(t00).observe(planetA)
        lonA = positionA.apparent().radec(epoch='date')[0]
        positionB = earth.at(t00).observe(planetB)
        lonB = positionB.apparent().radec(epoch='date')[0]

        relative_lon = (lonB.radians - lonA.radians + pi) % tau - pi

        rel_lon.append(relative_lon)

        x += 1
        d_inc += datetime.timedelta(days=1)

    return rel_lon

# used in ppc_buildchart2.planet_visible()
def relative_lon_jdt(objA, objB, jdt):
# Obtain relative ecliptic longitude of two solar system bodies at a julian datetime
# 'objA/objB' can be the sun or any solar system planet

    planetA = objects[objA]
    planetB = objects[objB]

    # compute ecliptic latitide/longitude per day

    tt = ts.tt(jd=jdt)
    positionA = earth.at(tt).observe(planetA)
    latA, lonA, distanceA = positionA.apparent().ecliptic_latlon()
    positionB = earth.at(tt).observe(planetB)
    latB, lonB, distanceB = positionB.apparent().ecliptic_latlon()

    relative_lon = (lonB.radians - lonA.radians + pi) % tau - pi

    return relative_lon     # return angle in radians

#---------------------------------------------------------------
#   Conjunctions and Oppositions (Planetary Phenomena charts)
#---------------------------------------------------------------

conjunctions = []
oppositions = []

def fEL(jd,j,k):
    # Compute how far away in ecliptic longitude the two celestial objects are.
    t = ts.tt(jd=jd)
    e = earth.at(t)
    lat, lon, distance = e.observe(objects[j]).ecliptic_latlon()
    lonA = lon.radians
    lat, lon, distance = e.observe(objects[k]).ecliptic_latlon()
    lonB = lon.radians
    relative_lon = (lonB - lonA + pi) % tau - pi
    return relative_lon

def fRA(jd,j,k):
    # Compute how far away in RA longitude the two celestial objects are.
    t = ts.tt(jd=jd)
    e = earth.at(t)
    position = e.observe(objects[j])
    ra = position.apparent().radec(epoch='date')[0]
    lonA = ra.radians
    position = e.observe(objects[k])
    ra = position.apparent().radec(epoch='date')[0]
    lonB = ra.radians
    relative_lon = (lonB - lonA + pi) % tau - pi
    return relative_lon

def conjunctions_oppositions(yy):
# Find conjunctions of 5 celestial objects within a given year
#    ... and oppositions of the 3 superior planets

    # Process weekly starting points spanning the chosen year
    # NOTE: with monthly start/end points some conjunctions can easily be missed!
    # NOTE: with weekly start/end points, incorrect years must be filtered out!
    #t = ts.utc(yy, range(1, 14))           # 13 monthly start/end points
    t = ts.utc(yy, 1, range(1, 54*7, 7))    # 53 weekly start/end points
    #t = ts.utc(yy, 1, range(1, 368))       # 367 daily start/end points

    # Where in the sky were the two celestial objects on those dates?
    e = earth.at(t)

#    for j in range(len(objects)):  # include uranus and neptune
    for j in range(len(objects)-2):  # exclude uranus and neptune
        if j == 0:
            lat, lon, distance = e.observe(objects[j]).ecliptic_latlon()
            lonA = lon.radians
        else:
            ra = e.observe(objects[j]).apparent().radec(epoch='date')[0]
            lonA = ra.radians
        # regarding uranus & neptune, include only 'sun-uranus'
        #   & 'sun-neptune' conjunctions and oppositions
        objmax = len(objects) if j == 0 else len(objects)-2
        for k in range(j+1, objmax):
            opp_ndx = []        # collect indices for planets in opposition
            if j == 0:
                lat, lon, distance = e.observe(objects[k]).ecliptic_latlon()
                lonB = lon.radians
            else:
                ra = e.observe(objects[k]).apparent().radec(epoch='date')[0]
                lonB = ra.radians

    # Where was object A relative to object B?  Compute their difference in
    # longitude, wrapping the value into the range [-pi, pi) to avoid
    # the discontinuity when one or the other object reaches 360 degrees
    # and flips back to 0 degrees.
            relative_lon = (lonB - lonA + pi) % tau - pi

    # Find where object B passed from being ahead of object A to being behind:
            conjunctionsInf = (relative_lon >= 0)[:-1] & (relative_lon < 0)[1:]
    # Find where object A passed from being ahead of object B to being behind:
            conjunctionsSup = (relative_lon < 0)[:-1] & (relative_lon >= 0)[1:]
    # find planets in opposition only within conjunctionsSup ...
            for i in conjunctionsSup.nonzero()[0]:
                if relative_lon[i+1] - relative_lon[i] > 5.0: opp_ndx.append(i)
    # all conjunctions is the sum of both
            conjunctionsALL = conjunctionsInf + conjunctionsSup

    # # ALTERNATIVE: find all conjunctions...
            # cj_lst = []
            # for i in range(len(relative_lon)-1):
                # cj = copysign(1.0, relative_lon[i]) != copysign(1.0, relative_lon[i+1])
                # cj_lst.append(cj)
            # conjunctionsALL = np.array(cj_lst)

            # # if j == 0 and k == 1:
                # # for item in conjunctionsALL.nonzero():
                    # # # return the indices of the elements that are non-zero, i.e. True
                    # # print(item)


    # For each month that included a conjunction,
    # ask SciPy exactly when the conjunction occurred.
            for i in conjunctionsALL.nonzero()[0]:
                t0 = t[i]
                t1 = t[i + 1]
                #print("Starting search at", t0.utc_jpl())
                if j == 0:
                    mode = "EL"
                    jdt = scipy.optimize.brentq(fEL, t[i].tt, t[i+1].tt, args=(j,k))
                else:
                    mode = "RA"
                    jdt = scipy.optimize.brentq(fRA, t[i].tt, t[i+1].tt, args=(j,k))
                # The search boundary is limited to the range
                #     from    t[i].tt    to    t[i+1].tt
                tt = ts.tt(jd=jdt)
                if int(tt.utc_strftime("%Y")) != yy: continue  # filter out incorrect years
                if i in opp_ndx:    # planets in opposition?
                    if j == 0:  # ignore if planet is not in opposition to the sun
                        # note: if j != 0 the planets are also theoretically "in
                        #       opposition" as their longitudes differ by 180°
                        oppositions.append((jdt, j, k))
                else:
                    ra0, dec0, dis0 = earth.at(tt).observe(objects[j]).apparent().radec(epoch='date')
                    ra1, dec1, dis1 = earth.at(tt).observe(objects[k]).apparent().radec(epoch='date')
                    diff = dec0.degrees - dec1.degrees
                    ns = "N" if diff > 0 else "S"
                    delta = "{:3.1f}°{}".format(abs(diff),ns)
                    # append result as tuple to a list
                    conjunctions.append((jdt, j, k, delta, mode))

    conjunctions.sort()    # sort tuples in-place by date
    oppositions.sort()     # sort tuples in-place by date

    if config.debug_scipy:
        print("\nFound {} conjunctions ('EL'=in ecliptic longitude; 'RA'=in right ascension):".format(len(conjunctions)))
        for jdt, j, k, delta, mode in conjunctions:
            tt = ts.tt(jd=jdt)
            print(" {:7}-{:7}: {} {} {} latitude \u0394".format(object_name[j], object_name[k], tt.utc_jpl(), delta, mode))

        # print("\nFound {} oppositions in ecliptic longitude:".format(len(oppositions)))
        # for jdt, j, k in oppositions:
            # tt = ts.tt(jd=jdt)
            # print(" {:7}-{:7}: {}".format(object_name[j], object_name[k], tt.utc_jpl()))

    return conjunctions, oppositions