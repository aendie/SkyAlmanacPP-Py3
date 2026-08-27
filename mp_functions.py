#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   Copyright (C) 2025  Andrew Bauer

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

# NOTE: the new format statement requires a literal '{' to be entered as '{{',
#       and a literal '}' to be entered as '}}'. The old '%' format specifier
#       will be removed from Python at some later time. See:
# https://docs.python.org/3/whatsnew/3.0.html#pep-3101-a-new-approach-to-string-formatting

###### Standard library imports ######
from datetime import datetime, timedelta
import sys

###### Third party imports ######
from skyfield.api import load
from skyfield import almanac
from skyfield.api import wgs84
from skyfield.api import Topos
from skyfield.nutationlib import iau2000b

###### Local application imports ######
import config

#---------------------------------------------------------
#   Required functions
#---------------------------------------------------------

# The following text applies to all 'daylength' functions:

#   The function that this returns will expect a single argument that is a 
#   :class:`~skyfield.timelib.Time` and will return ``True`` if the sun is up
#   or twilight has started, else ``False``.

def daylength(earth, sun, topos, degBelowHorizon):
    # Build a function of time that returns the daylength.
    topos_at = (earth + topos).at

    def is_sun_up_at(t):
        t._nutation_angles = iau2000b(t.tt)
        # Return `True` if the sun has risen by time `t`.
        return topos_at(t).observe(sun).apparent().altaz()[0].degrees > -degBelowHorizon

    is_sun_up_at.rough_period = 0.5  # twice a day
    return is_sun_up_at

# def day5length(earth, planet, topos, degBelowHorizon):
    # # Build a function of time that returns the daylength.
    # topos_at = (earth + topos).at

    # def is_obj_up_at(t):
        # t._nutation_angles = iau2000b(t.tt)
        # # Return `True` if the planet has risen by time `t`.
        # return topos_at(t).observe(planet).apparent().altaz()[0].degrees > -degBelowHorizon

    # is_obj_up_at.rough_period = 0.5  # twice a day
    # return is_obj_up_at

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
    msg = "rise_set {} values for {:4.1f}°{}: {}".format(len(y),lns,abs(lats), y[0])
    # msg = "rise_set {} values for {}: {}".format(len(y),lats, y[0])
    if len(y) > 1:
        msg = msg + " {}".format(y[1])
    if len(y) > 2:
        msg = msg + " {}".format(y[2])
    if len(y) > 3:
        msg = msg + " {}".format(y[3])
    # print to console
    print("{}   {}".format(dt0.isoformat(), msg))
    sys.exit(0)

#---------------------------------------------------------
#   Twilight calculations  (Planetary Phenomena charts)
#---------------------------------------------------------

# > > > > > > > > > > MULTIPROCESSING ENTRY POINT < < < < < < < < < <
def mp_sunrise_set(d, mth, params, sf, sun_Y, ts):
# called from ppc_buildchart2.chart_LocalMeanTimeOfMeridianPassage

    # For the given month offset within the chosen year, return a tuple with these values
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

    eph = load(config.ephemeris[config.ephndx][0])	# load chosen ephemeris
    earth   = eph['earth']
    sun     = eph['sun']

# calculate Sunrise/Sunset times at latitude 'lats' for a month offset (0 to 11)

    rqrd_mth = d.month + mth    # 1 to 12
    next_yr = d.year + 1
    dt = datetime(d.year, rqrd_mth, d.day, 0, 0, 0)  # convert to datetime
    ndx = []                # list of date offsets in year
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
    idx = int(dt.strftime("%j")) - 1
    process_1day = True

    while process_1day:
        if t0 == None:
        # do NOT use 'ts.ut1' as the date returned can be outside the requested boundary
            t0 = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        t1 = ts.utc(dt.year, dt.month, dt.day+1, dt.hour, dt.minute, dt.second)

        # Sunrise/Sunset time...
        event0, y = almanac.find_discrete(t0, t1, daylength(earth, sun, locn, 0.8333))
        if len(event0) == 2:		# this happens most often
            dt0 = event0[0].utc_datetime()   # sunrise
            dt1 = event0[1].utc_datetime()   # sunset
        else:
            print("find_discrete returned {} rise/set events".format(len(event0)))
            sys.exit(0)

        hoursAM = dt0.hour + dt0.minute/60 + dt0.second/3600
        sunriseY.append(hoursAM)
        xy_txt  = "(%04.3f, %04.3f)" %(idx*sf/10, hoursAM*sf)
        sunAM.append(xy_txt)    # XY scaled coordinates of sunrise

        hoursPM = dt1.hour + dt1.minute/60 + dt1.second/3600
        sunsetY.append(hoursPM)
        xy_txt  = "(%04.3f, %04.3f)" %(idx*sf/10, hoursPM*sf)
        sunPM.append(xy_txt)     # XY scaled coordinates of sunset

        # Civil Twilight duration...
        event1, y = almanac.find_discrete(t0, t1, daylength(earth, sun, locn, dbh))
        if len(event1) == 2:		# this happens most often
            dt0 = event1[0].utc_datetime()   # civil twilight AM
            dt1 = event1[1].utc_datetime()   # civil twilight PM
        else:
            print("find_discrete returned {} civil twilight events".format(len(event1)))
            sys.exit(0)

        # note: sun's Meridian Passage 'sun_Y' is pre-calculated
        hours2 = dt0.hour + dt0.minute/60 + dt0.second/3600
        duration2 = hoursAM - hours2     # sunrise time - civil twilight AM
        y_AM = sun_Y[idx] - duration2
        civilY_AM.append(y_AM)
        xy_txt  = "(%04.3f, %04.3f)" %(idx*sf/10, y_AM*sf)
        civil_twiAM.append(xy_txt)  # XY scaled coordinates of civil twilight AM offset

        hours3 = dt1.hour + dt1.minute/60 + dt1.second/3600
        duration3 = hours3 - hoursPM     # civil twilight PM - sunset time
        y_PM = sun_Y[idx] + duration3
        civilY_PM.append(y_PM)
        xy_txt  = "(%04.3f, %04.3f)" %(idx*sf/10, y_PM*sf)
        civil_twiPM.append(xy_txt)  # XY scaled coordinates of civil twilight PM offset

        # # statistics: collect min/max civil twilight duration AM/PM in year
        # dur2 = duration2 * 60.0
        # if durationAM_min == None:
            # durationAM_min = dur2
        # else:
            # if dur2 < durationAM_min: durationAM_min = dur2
        # if durationAM_max == None:
            # durationAM_max = dur2
        # else:
            # if dur2 > durationAM_max: durationAM_max = dur2

        # dur3 = duration3 * 60.0
        # if durationPM_min == None:
            # durationPM_min = dur3
        # else:
            # if dur3 < durationPM_min: durationPM_min = dur3
        # if durationPM_max == None:
            # durationPM_max = dur3
        # else:
            # if dur3 > durationPM_max: durationPM_max = dur3

        ndx.append(idx)
        t0 = t1
        idx += 1
        dt += timedelta(days=1)
        if rqrd_mth == 12:
            # remember in December we also have to process 1st Jan of next year ...
            process_1day = (dt.month == rqrd_mth) or (dt.year == next_yr and dt.month == 1 and dt.day == 1)
        else:
            process_1day = (dt.month == rqrd_mth)

    # print("civil twilight AM lasts from {:.2f} to {:.2f} minutes in {}".format(durationAM_min, durationAM_max,d.year))
    # print("civil twilight PM lasts from {:.2f} to {:.2f} minutes in {}".format(durationPM_min, durationPM_max,d.year))
    
    tup = (ndx, sunAM, sunPM, sunriseY, sunsetY, civil_twiAM, civil_twiPM, civilY_AM, civilY_PM)

    return tup

#-----------------------------------------------------
#   Twilight calculations  (Planet Rise/Set charts)
#-----------------------------------------------------

# > > > > > > > > > > MULTIPROCESSING ENTRY POINT < < < < < < < < < <
def mp_sunrise_set2(d, mth, params, sf, ts):    # called from ppc_buildchart3.py
# called from ppc_buildchart3.chart_RISE_SET
# calculate Sunrise/Sunset/Dawn/Dusk times at latitude 'lats'

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

    eph = load(config.ephemeris[config.ephndx][0])	# load chosen ephemeris
    earth   = eph['earth']
    sun     = eph['sun']

# calculate Sunrise/Sunset times at latitude 'lats' for a month offset (0 to 11)

    rqrd_mth = d.month + mth    # 1 to 12
    next_yr = d.year + 1
    dt = datetime(d.year, rqrd_mth, d.day, 0, 0, 0)  # convert to datetime
    ndx = []                # list of date offsets in year

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
    idx = int(dt.strftime("%j")) - 1
    process_1day = True

    while process_1day:
        hoursAM = hoursPM = None
        if t0 == None:
        # do NOT use 'ts.ut1' as the date returned can be outside the requested boundary
            t0 = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        t1 = ts.utc(dt.year, dt.month, dt.day+1, dt.hour, dt.minute, dt.second)

        # Sunrise/Sunset time...
        event0, y = almanac.find_discrete(t0, t1, daylength(earth, sun, locn, 0.8333))
        dt_rise, dt_set, finalstate = rise_set(event0, y, lats)

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
        event1, y = almanac.find_discrete(t0, t1, daylength(earth, sun, locn, dbh))
        dt_rise, dt_set, finalstate = rise_set(event1, y, lats)

        if len(dt_rise) > 0:
            for dt0 in dt_rise:
                y_AM = dt0.hour + dt0.minute/60 + dt0.second/3600
                # duration2 = hoursAM - y_AM  # sunrise time - civil twilight AM
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

        if len(dt_set) > 0:
            for dt1 in dt_set:
                y_PM = dt1.hour + dt1.minute/60 + dt1.second/3600
                # duration3 = y_PM - hoursPM  # civil twilight PM - sunset time
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

        # # statistics: collect min/max civil twilight duration AM/PM in year
        # dur2 = duration2 * 60.0
        # if durationAM_min == None:
            # durationAM_min = dur2
        # else:
            # if dur2 < durationAM_min: durationAM_min = dur2
        # if durationAM_max == None:
            # durationAM_max = dur2
        # else:
            # if dur2 > durationAM_max: durationAM_max = dur2

        # dur3 = duration3 * 60.0
        # if durationPM_min == None:
            # durationPM_min = dur3
        # else:
            # if dur3 < durationPM_min: durationPM_min = dur3
        # if durationPM_max == None:
            # durationPM_max = dur3
        # else:
            # if dur3 > durationPM_max: durationPM_max = dur3

        ndx.append(idx)
        t0 = t1
        idx += 1
        dt += timedelta(days=1)

        if rqrd_mth == 12 and orthogonal:
            # remember in December we also have to process 1st Jan of next year ...
            process_1day = (dt.month == rqrd_mth) or (dt.year == next_yr and dt.month == 1 and dt.day == 1)
        else:
            process_1day = (dt.month == rqrd_mth)

    # print("civil twilight AM lasts from {:.2f} to {:.2f} minutes in {}".format(durationAM_min, durationAM_max,d.year))
    # print("civil twilight PM lasts from {:.2f} to {:.2f} minutes in {}".format(durationPM_min, durationPM_max,d.year))

    tup = (ndx, sunAM, sunPM, sunriseY, sunsetY, civil_twiAM, civil_twiPM, civilY_AM, civilY_PM)

    return tup


# > > > > > > > > > > MULTIPROCESSING ENTRY POINT < < < < < < < < < <

# NOTE:   A planet can have multiple rise & set times per day

def mp_objrise_set3(d, mth, params, sf, ts):

    # For the given month, return a list of tuples per day with these values
    #   idx             = day offset within year (= dayofyear - 1)
    #   riseset_time    = list of (True and False) event times per day
    #   isrise          = list of the Rise or Set value per event
    #   isTrue          = list of the True/False value per event

    obj, lats, orthogonal = params      # tuple: planet, the latitude and orthogonal data (True/False)
    eph = load(config.ephemeris[config.ephndx][0])	# load chosen ephemeris
    sun     = eph['sun']
    mercury = eph['mercury']
    venus   = eph['venus']
    earth   = eph['earth']
    if config.ephndx >= 3:
        mars    = eph['mars barycenter']
    else:
        mars    = eph['mars']
    jupiter = eph['jupiter barycenter']
    saturn  = eph['saturn barycenter']
    uranus  = eph['uranus barycenter']
    neptune = eph['neptune barycenter']

    # objects = [sun, mercury, venus, mars, jupiter, saturn]
    objects = [sun, mercury, venus, mars, jupiter, saturn, uranus, neptune]
    planet  = objects[obj]

# calculate planet rise/set times at latitude 'lats' for a month offset (0 to 11)

    data_per_month = []         # data to return
    rqrd_mth = d.month + mth    # 1 to 12
    next_yr = d.year + 1
    dt = datetime(d.year, rqrd_mth, d.day, 0, 0, 0)  # convert to datetime
    # lats = "51.5 N"
    # locn = Topos(lats, "0.0 E")
    topos = wgs84.latlon(lats, 0.0, elevation_m=0.0)
    observer = earth + topos

    t0 = None
    idx = int(dt.strftime("%j")) - 1
    process_1day = True

    while process_1day:
        if t0 == None:
        # do NOT use 'ts.ut1' as the date returned can be outside the requested boundary
        #   e.g. Saturn 2042 Feb 13 60°N returns RISE at 14 Feb 00:00:00
            t0 = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        t1 = ts.utc(dt.year, dt.month, dt.day+1, dt.hour, dt.minute, dt.second)

        # OLDEST....
        # Planet rise/set time...
        #   (the standard refraction angle is 0.56667 = 34 arcminutes,
        #    by which the image of the object is raised at the horizon)
#        event0, y = almanac.find_discrete(t0, t1, day5length(earth, planet, locn, 0.56667))

        # NOW A LEGACY FUNCTION....
        # f = almanac.risings_and_settings(eph, planet, topos)
        # f.step_days = 0.005      # 0.005 required for planets
        # riseset_time, isrise = almanac.find_discrete(t0, t1, f)
        # dt_rise, dt_set, finalstate = rise_set(riseset_time, isrise, lats)

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
        data_per_month.append((idx, riseset_time, isrise, isTrue))

        t0 = t1
        idx += 1
        dt += timedelta(days=1)

        if rqrd_mth == 12 and orthogonal:
            # remember in December we also have to process 1st Jan of next year ...
            process_1day = (dt.month == rqrd_mth) or (dt.year == next_yr and dt.month == 1 and dt.day == 1)
        else:
            process_1day = (dt.month == rqrd_mth)

    # ----------------------------------------- end of 'while'

    return data_per_month