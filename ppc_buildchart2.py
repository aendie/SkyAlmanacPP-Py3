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

# NOTE: the new format statement requires a literal '{' to be entered as '{{',
#       and a literal '}' to be entered as '}}'. The old '%' format specifier
#       will be removed from Python at some later time. See:
# https://docs.python.org/3/whatsnew/3.0.html#pep-3101-a-new-approach-to-string-formatting

###### Standard library imports ######
import sys
from datetime import date, datetime, timedelta
import math
import signal       # for init_worker
#from collections import deque

###### Third party imports ######
from skyfield.api import pi, tau

###### Local application imports ######
import config
from ppc_buildchart1 import buildchart1
if config.MULTIpr:  # in multi-processing mode ...
    # ! DO NOT PLACE imports IN CONDITIONAL 'if'-STATEMENTS WHEN MULTI-PROCESSING !
    import multiprocessing as mp
    from functools import partial
    # ... following is still required for SINGLE-PROCESSING (in multi-processing mode):
    #from pp_skyfield import MerPass    # more accurate than merpass00 but 3x slower
    from pp_skyfield import merpass00, ariesSHA, get_object_name, conjunctions_oppositions, planet_mag, relative_lon, relative_lon_jdt, sunrise_set, planets_near
    # NOTE: although sunrise_set is NOT required in MULTI-PROCESSING mode
    #       it needs to be imported in case the value of config.MULTIpr is
    #       changed to 'False' dynamically via the '-sp' command-line option.
    # ... following is required for MULTI-PROCESSING:
    from mp_functions import mp_sunrise_set
else:
    # ... following is required for SINGLE-PROCESSING:
    #from pp_skyfield import MerPass    # more accurate than merpass00 but 3x slower
    from pp_skyfield import merpass00, ariesSHA, get_object_name, conjunctions_oppositions, planet_mag, relative_lon, relative_lon_jdt, sunrise_set, planets_near

#   My apologies to those who read this . . .
#   Although use of global variables is frowned upon by the Python community,
#   I have chosen to employ global variables in this module to reduce the
#   number of arguments passed to some functions, so that the function
#   arguments focus on the frequently changing parameters.
#   A comment before a function describes which global variables are used.
#   . . . and Murphy whispered in his sleep "If it works, don't touch it"

# global VARIABLES
d00 = None
daystoprocess = None
label_ndx = 0
tup_crosspoints = None

# global CONSTANTS  (these values are not changed)
degree_sign= u'\N{DEGREE SIGN}'
twopi = 2 * math.pi
todegrees = 180.0/math.pi
toradians = math.pi/180.0
hmin   = 0
hmax   = 24
navstar_fs = "normalsize"   # navigational star fontsize (10pt)
star_fs = "footnotesize"    # star fontsize (8pt)
title_fs ="Large"           # title, SHA, DEC fontsize (14.4pt)
ns_fs = "large"             # North, South fontsize (12pt)
msg0 = "\nKeyboardInterrupt detected - multiprocessing aborted."

# Zodiac house signs from 0° to 360° ecliptic longitude at 30° intervals ...
House_Sign = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricornus', 'Aquarius', 'Pisces']

if config.pgsz == "A4":
    sf = 1.39 * 0.5 # scale factor (0.695cm to 1 hour or 10 calendar days)
else:
    sf = 1.31 * 0.5 # scale factor (0.655cm to 1 hour or 10 calendar days)

#----------------------------------------
#   build 'Visibility Of Planets' page
#----------------------------------------

def planet_visible(obj, obj2, jdt):
    rel_lon = relative_lon_jdt(0, obj, jdt)*todegrees
    deg = 13.0  # not visible if within 52 minutes (time) of sun's position
    #if obj2 == 2: deg = 10.5    # within 42 minutes if with Venus (because it's bright)
    if obj2 == 2: deg = 11.25    # within 45 minutes if with Venus (because it's bright)
    #if obj == 4: print(rel_lon)
    vis = False if -deg < rel_lon < deg else True
    return vis

def approx_week2(idx):
    # 1st week of month defined as days from 1st up to and including Saturday
    dt = d00+timedelta(days=idx)
    dt_mth = dt.strftime("%B")
    days_in_mth = (dt.replace(month = dt.month % 12 +1, day=1) - timedelta(days=1)).day
    dt_first = dt.replace(day=1)
    starting_weekday = int(dt_first.strftime("%w"))  # 0(Sunday) to 6(Saturday)
    d = ((7 - starting_weekday) % 7) + 1    # date of first Sunday
    wk_of_mth = 0
    while d <= days_in_mth:
        if dt.day <= d: break
        wk_of_mth += 1
        d += 7
    ordinals = ['first', 'second', 'third', 'fourth', 'fifth']
    txt = "{} week of {}".format(ordinals[wk_of_mth],dt_mth)
    return txt

def approx_week(idx):
    # 1st week of month defined as first 7 days in month
    dt = d00+timedelta(days=idx)
    dt_mth = dt.strftime("%B")
    wk_of_mth = int((dt.day-1)/7)
    ordinals = ['first', 'second', 'third', 'fourth', 'fifth']
    txt = "the {} week of {}".format(ordinals[wk_of_mth],dt_mth)
    return txt

def approx_mth(idx):        # sub-function for approx_month()
    dt = d00+timedelta(days=idx)
    dt_mth = dt.strftime("%B")
    days_in_mth = (dt.replace(month = dt.month % 12 +1, day=1) - timedelta(days=1)).day
    if dt.day == 1: txt = "start of {}".format(dt_mth)
    if dt.day <= 7: txt = "early {}".format(dt_mth)
    elif dt.day <= 12: txt = "the first half of {}".format(dt_mth)
    elif dt.day == days_in_mth and dt.month == 12: txt = "the end of the year"
    elif dt.day == days_in_mth: txt = "end of {}".format(dt_mth)
    elif dt.day >= 24: txt = "late {}".format(dt_mth)
    elif dt.day >= 18: txt = "the second half of {}".format(dt_mth)
    else: txt = "mid-{}".format(dt_mth)
    return txt
        
def approx_month(idx, idy=-1):
    dt = d00+timedelta(days=idx)
    dt_mth = dt.strftime("%B")

    if idy == -1:    # if one argument supplied
        if dt.day <= 5:
            dt_pmth = (dt-timedelta(days=6)).strftime("%B")
        elif dt.day >= 26:
            dt_nmth = (dt+timedelta(days=6)).strftime("%B")
        if dt.day <= 5: txt = "from late {} to early {}".format(dt_pmth,dt_mth)
        elif dt.day <= 12: txt = "in the first half of {}".format(dt_mth)
        elif dt.day >= 26: txt = "from late {} to early {}".format(dt_mth,dt_nmth)
        elif dt.day >= 18: txt = "in the second half of {}".format(dt_mth)
        else: txt = "around the middle of {}".format(dt_mth)

    else:           # if two arguments supplied
        txt = "from " + approx_mth(idx)
        txt += " to "  + approx_mth(idy)

    return txt

# create VISIBILITY OF PLANETS text for:
#    Venus, Saturn, Uranus, Neptune
def overall_visibility(obj, planetVIS, fmt1=True, fmt2=True, fmt3=False):
    # describe a planet's overall visibility in the night sky over the year
    txt = ""
    objn = get_object_name(obj)
    objn = objn[0].upper() + objn[1:]
    idx_invis = None
    ndx = ndx2 = None

    for index, item in enumerate(planetVIS):
        idx, vis, mpa, sunmpa = item
        txtAMPM = 'morning' if mpa < 12.0 else 'evening'
        if idx == 0:
            if fmt3:
                if vis:
                    txt += "is a brilliant object in the {} sky from the beginning of the year ".format(txtAMPM)
                else:
                    txt += " is not visible at the beginning of the year. "
            else:
                if vis:
                    if mpa < 12:
                        txt += " rises {:.1f} hours before sunrise at the beginning of the year. ".format(sunmpa-mpa)
                    else:
                        txt += " sets {:.1f} hours after sunset at the beginning of the year. ".format(mpa-sunmpa)
                else:
                    txt += " is not visible at the beginning of the year. "
                continue
        #if not vis and idx <= idx_oppo <= idx+1:
        #    txt += txt_oppo
        #    continue
        if not vis and idx < daystoprocess-1:
            idx_invis = idx
            ndx = index + 1
            continue
        if vis and index == ndx and idx == idx_invis+1 and mpa > 23.5:
            dt1 = d00 + timedelta(days=idx_invis)
            txt += " On {dt:%B} {dt.day} {objn} moves into the evening sky. ".format(dt=dt1,objn=objn)
            continue
        if vis and index == ndx and idx < daystoprocess-1:
            txt1 = approx_mth(idx_invis) if fmt1 else approx_week(idx_invis)
            txt2 = approx_mth(idx) if fmt2 else approx_week(idx)
            if fmt3:
                dt1 = d00 + timedelta(days=idx_invis)
                txt += " until {dt:%B} {dt.day} when it becomes too close to the Sun for observation. From the end of {t2} it reappears in the {sky} sky. ".format(dt=dt1,t2=txt2,sky=txtAMPM)
            else:
                txt += " In {} it becomes too close to the Sun for observation and reappears in {} in the {} sky. ".format(txt1,txt2,txtAMPM)
            idx_invis = None
            ndx2 = index + 1
            continue
        if not vis and index == ndx2 and idx == daystoprocess-1:
            txt = txt[:-21] + " and remains in the {} sky for the remainder of the year. ".format(txtAMPM)

        prev_idx = idx

    return txt[:-1]

# def overall_visibility(vis_AM, vis_PM, fmtmth=True, txt="visible"):
    # # describe a planet's overall visibility in the night sky over the year

    # AM_fr = AM_to = PM_fr = PM_to = None
    # if len(vis_AM) > 0:
        # AM_fr, AM_to = vis_AM[0]
        # d1 = d00 + timedelta(days=AM_fr)
        # mAM1 = planet_mag(1, d1)    # magnitude of Venus AM from
        # d2 = d00 + timedelta(days=AM_to)
        # mAM2 = planet_mag(1, d2)    # magnitude of Venus AM to

    # if len(vis_PM) > 0:
        # PM_fr, PM_to = vis_PM[0]
        # d3 = d00 + timedelta(days=PM_fr)
        # mPM1 = planet_mag(1, d3)    # magnitude of Venus PM from
        # d4 = d00 + timedelta(days=PM_to)
        # mPM2 = planet_mag(1, d4)    # magnitude of Venus PM to

    # txtAMPM = txt_fr = txt_to = None
    # txtAMPM2 = txt_fr2 = txt_tp2 = None
    # if AM_fr == 0:
        # txtAMPM = "morning"
        # txt_fr = "the begining of the year"
        # txt_to = approx_mth(AM_to)
        # if PM_fr != None:
            # txt_fr2 = approx_mth(PM_fr) if fmtmth else approx_week(PM_fr)
            # txtAMPM2 = "morning"
            # txt_to2 = approx_mth(PM_to)
    # elif PM_fr == 0:
        # txtAMPM = "evening"
        # txt_fr = "the begining of the year"
        # txt_to = approx_mth(PM_to)
        # if AM_fr != None:
            # txt_fr2 = approx_mth(AM_fr) if fmtmth else approx_week(AM_fr)
            # txtAMPM2 = "morning"
            # txt_to2 = approx_mth(AM_to)
    # else:   # if not visible at the beginning of the year
        # if AM_fr != None and PM_fr != None:
            # if AM_fr < PM_fr:
                # txtAMPM = "morning"
                # txt_fr = approx_mth(AM_fr)
                # if AM_to < daystoprocess-1:
                    # txt_to = approx_mth(AM_to)
                    # txt_fr2 = approx_mth(PM_fr)
                    # txtAMPM2 = "evening"
            # else:
                # txtAMPM = "evening"
                # txt_fr = approx_mth(PM_fr) if fmtmth else approx_week(PM_fr)
                # if PM_to < daystoprocess-1:
                    # txt_to = approx_mth(PM_to)
                    # txt_fr2 = approx_mth(AM_fr)
                    # txtAMPM2 = "morning"
        # else:
            # txt_fr = "????"
            # txt_to = "????"
            # txt_fr2 = "????"
            # txt_to2 = "????"
            # txtAMPM = "????"
            # txtAMPM2 = "????"

    # if AM_fr == 0 or PM_fr == 0:
        # t_vis = "is {} in the {} sky from {} until {} when it becomes too close to the sun for observation. ".format(txt, txtAMPM, txt_fr, txt_to)

        # t_vis2 = "In {} it reappears in the {} sky.".format(txt_fr2, txtAMPM2)
        # if not fmtmth:
            # t_vis2 = t_vis2[:-1] + " where it stays until {}.".format(txt_to2)
    # else:
        # txt2 = ""
        # if txt != "visible": txt2 = "as " + txt + " "   # txt = "a brilliant object"
        # t_vis = "is too close to the Sun for observation until {} when it appears {}in the {} sky. ".format(txt_fr, txt2, txtAMPM)

        # t_vis2 = "In {} it again becomes too close to the Sun for observation until {} when it reappears in the {} sky. ".format(txt_to, txt_fr2, txtAMPM2)

    # return t_vis, t_vis2

def visibility_range(MerPassY):
    vis_range = []
    fr = None
    for idx, vis in MerPassY:
        if vis:
            fr = idx
        else:
            to = idx
            vis_range.append((fr, to))
    return vis_range

def only_when_visible(obj, x_fr, x_to):
    # return a range that is within the limits of visibility
    if x_fr == None: return None, None
    if obj == 1:
        global vis_mercuryAM,vis_mercuryPM
        vis_AM = vis_mercuryAM
        vis_PM = vis_mercuryPM
    if obj == 2:
        global vis_venusAM,vis_venusPM
        vis_AM = vis_venusAM
        vis_PM = vis_venusPM
    if obj == 3:
        global vis_marsAM,vis_marsPM
        vis_AM = vis_marsAM
        vis_PM = vis_marsPM
    if obj == 4:
        global vis_jupiterAM,vis_jupiterPM
        vis_AM = vis_jupiterAM
        vis_PM = vis_jupiterPM
    if obj == 5:
        global vis_saturnAM,vis_saturnPM
        vis_AM = vis_saturnAM
        vis_PM = vis_saturnPM

    # check morning visibility ranges
    vis_fr = False
    vis_to = False
    for fr, to in vis_AM:
        if fr <= x_fr <= to: vis_fr = True
        if fr <= x_to <= to: vis_to = True
        if vis_fr and vis_to:
            return x_fr, x_to
        if vis_fr and not vis_to:
            return x_fr, to
        if not vis_fr and vis_to:
            return fr, x_to
        if fr >= x_fr and to <= x_to:
            return fr, to

    # check eveining visibility ranges
    vis_fr = False
    vis_to = False
    for fr, to in vis_PM:
        if fr <= x_fr <= to: vis_fr = True
        if fr <= x_to <= to: vis_to = True
        if vis_fr and vis_to:
            return x_fr, x_to
        if vis_fr and not vis_to:
            return x_fr, to
        if not vis_fr and vis_to:
            return fr, x_to
        if fr >= x_fr and to <= x_to:
            return fr, to

    return None, None

def vis_fr_to(vis_tuple):
# convert a visibility range to 2 text values as 'month date'
    vis_fr, vis_to = vis_tuple
    dt = d00 + timedelta(days=vis_fr)
    txt_fr = "{dt1:%B} {dt1.day}".format(dt1=dt)
    dt = d00 + timedelta(days=vis_to)
    txt_to = "{dt1:%B} {dt1.day}".format(dt1=dt)
    return txt_fr, '-', txt_to

def visibility_AM_PM(planet_name, vis_AM, vis_PM, rowsep):
# format a row in the 'VISIBILITY OF PLANETS AM/PM table
#    ... with a single or a multirow line

    tex = ''
    AM_fr  = AM_to  = PM_fr  = PM_to  = ''
    AM2_fr = AM2_to = PM2_fr = PM2_to = ''
    AM_sep  = PM_sep  = ''
    AM2_sep = PM2_sep = ''
    vis_planet = 0   # 0= no dates; 1= 1 range; 2= 2 ranges; 3to5= multirow required

    if len(vis_AM) > 0:
        vis_planet += 1
        if len(vis_PM) > 0 and vis_PM[0][0] < vis_AM[0][0]:
            AM2_fr, AM2_sep, AM2_to = vis_fr_to(vis_AM[0])
            vis_planet += 1
        else:
            AM_fr, AM_sep, AM_to = vis_fr_to(vis_AM[0])

    if len(vis_PM) > 0:
        PM_fr, PM_sep, PM_to = vis_fr_to(vis_PM[0])
        vis_planet += 1

    if len(vis_AM) > 1:
        AM2_fr, AM2_sep, AM2_to = vis_fr_to(vis_AM[1])
        if vis_planet == 3:
            print("VISIBILITY OF PLANETS: {} AM {} - {} position unavailable".format(planet_name,AM2_fr,AM2_to))
            sys.exit(0)
        vis_planet += 1

    if len(vis_PM) > 1:
        PM2_fr, PM2_sep, PM2_to = vis_fr_to(vis_PM[1])
        vis_planet += 1

    if 1 <= vis_planet <= 2:
        tex += r'''%s
%s & %s & %s & %s & %s & %s & %s''' %(rowsep,planet_name,AM_fr,AM_sep,AM_to,PM_fr,PM_sep,PM_to)
        rowsep = r'\\'

    if vis_planet >= 3:
        if rowsep != r'\\[2pt]':    # 2Pt vertical space initially for the top row
            rowsep = r'\\\midrule'  # otherwise separate it above with '\midrule'
        tex += r'''%s
\multirow{2}{*}{%s} & %s & %s & %s & %s & %s & %s\\
& %s & %s & %s & %s & %s & %s''' %(rowsep,planet_name,AM_fr,AM_sep,AM_to,PM_fr,PM_sep,PM_to,AM2_fr,AM2_sep,AM2_to,PM2_fr,PM2_sep,PM2_to)
        rowsep = r'\\\midrule'      # separate row below with '\midrule' (unless last row)

    return tex, rowsep


def chart2page2(lats, tm1, bm1, lm1, rm1, yy, ts):
    global meridian_pass, daystoprocess, planet_app_pos#, tup_crosspoints

    # planet_lon = [None]     # for object = 0 (sun)
    # planet_mag = [None]     # for object = 0 (sun)
    # # get planet ecliptic longitude and magnitudes
    # for obj in [1, 2, 3, 4, 5, 6, 7]:
        # pla_lon, pla_mag = ecliptic_lon(obj, d00, daystoprocess)
        # planet_lon.append(pla_lon)
        # planet_mag.append(pla_mag)

    conjunctions, oppositions = conjunctions_oppositions(yy)
    # sort conjunctions (jdt, j, k) by j, k, jdt
    conjunctions_by_obj = sorted(conjunctions, key = lambda x:(x[1],x[2],x[0]))
    if verbose:
        print("\n   Found {} oppositions in ecliptic longitude:".format(len(oppositions)))
        for jdt, j, k in oppositions:
            tt = ts.tt(jd=jdt)
            print("    {:7}-{:7}: {}".format(get_object_name(j), get_object_name(k), tt.utc_jpl()))

        print("\n   Found {} conjunctions ('EL'=in ecliptic longitude; 'RA'=in right ascension):".format(len(conjunctions_by_obj)))
        for jdt, j, k, delta, mode in conjunctions_by_obj:
            tt = ts.tt(jd=jdt)
            print("    {:7}-{:7}: {} {} {} latitude \u0394".format(get_object_name(j), get_object_name(k), tt.utc_jpl(), delta, mode))

    vop = {}    # dictionary 'Visibility Of Planets'
    dnc = []    # list of 'DO NOT CONFUSE' text items

#######################################
#  Inferior Planets: Mercury, Venus
#
#  The inferior planets have four visibility phenomena:
#  1. First visibility in the evening (EF): the first visibility of the planet
#     in the west after sunset following superior conjunction with the sun.
#  2. Last visibility in the evening (EL): the last visibility of the planet
#     in the west after sunset preceding inferior conjunction with the sun.
#  3. First visibility in the morning (MF): the first visibility of the planet
#     in the east before sunrise following inferior conjunction with the sun.
#  4. Last visibility in the morning (ML): the last visibility of the planet
#     in the east before sunrise preceding superior conjunction with the sun.
#
###############  MERCURY  ##############
    obj = 1
    dnctxt = ''
    
    # determine visibility ranges
    global mercuryAM, mercuryPM, vis_mercuryAM, vis_mercuryPM
    vis_mercuryAM = visibility_range(mercuryAM)  # begin,end of morning visibility
    vis_mercuryPM = visibility_range(mercuryPM)  # begin,end of evening visibility

    # mornings ...........................
    txtAM = ''
    tAM = ''
    bcN_AM = []
    bcS_AM = []

    for AM_fr, AM_to in vis_mercuryAM:
        d1 = d00 + timedelta(days=AM_fr)
        mAM1 = planet_mag(1, d1)    # magnitude of Mercury AM from
        d2 = d00 + timedelta(days=AM_to)
        mAM2 = planet_mag(1, d2)    # magnitude of Mercury AM to

        tAMtemp = 'end' if mAM2 < mAM1 else 'beginning'
        if config.debug_magnitude:
            print("Mercury magnitude AM from {dt1:%b} {dt1:%d} to {dt2:%b} {dt2:%d}: {m1:.3f} to {m2:.3f}".format(dt1=d00+timedelta(days=AM_fr), dt2=d00+timedelta(days=AM_to), m1=mAM1, m2=mAM2))
        TO_date = "{dt2:%b} {dt2:%d}".format(dt2=d00+timedelta(days=AM_to))
        if tAM != '' and tAM != tAMtemp and TO_date != 'Dec 31':
            # Note: this test excludes the first magnitude of the year (as tAM = '')
            #       the last magnitude of the year is excluded if ending on Dec 31st
            #       (this is necessary as the period of visibility is prematurely terminated by End of Year)
            print("ERROR: check Mercury brightness in each AM period")
            sys.exit(0)
        tAM = tAMtemp

        if AM_fr == 0:
            txtAM += "beginning of the year to {dt2:%B} {dt2.day}, ".format(dt2=d2)
        elif AM_to == daystoprocess-1:
            txtAM += "{dt1:%B} {dt1.day} to end of the year, ".format(dt1=d1)
        else:
            txtAM += "{dt1:%B} {dt1.day} to {dt2:%B} {dt2.day}, ".format(dt1=d1, dt2=d2)
        
        # best conditions mornings in northern latitudes...
        mpa_min = 12.0
        idx_min = -1
        if AM_fr >= 181 and AM_to > 181:
            vis_days = AM_to - AM_fr + 1
            if vis_days < 30:
                mid_idx = AM_fr + int(vis_days/2)
                bcN_AM.append((vis_days, mid_idx, -1))
                #dt = d00+timedelta(days=mid_idx)
                #print("....",dt)
            else:
                for idx in range(AM_fr,AM_to+1):
                    if meridian_pass[obj][idx] < mpa_min:
                        mpa_min = meridian_pass[obj][idx]
                        idx_min = idx
                idx_end = int((idx_min + AM_to)/2)
                bcN_AM.append((vis_days, idx_min, idx_end))
        
        # best conditions mornings in southern latitudes...
        mpa_min = 12.0
        idx_min = -1
        if AM_fr < 181 and AM_to <= 181:
            vis_days = AM_to - AM_fr + 1
            if vis_days < 30:
                mid_idx = AM_fr + int(vis_days/2)
                bcS_AM.append((vis_days, mid_idx, -1))
            else:
                for idx in range(AM_fr,AM_to+1):
                    if meridian_pass[obj][idx] < mpa_min:
                        mpa_min = meridian_pass[obj][idx]
                        idx_min = idx
                idx_end = int((idx_min + AM_to)/2)
                bcS_AM.append((vis_days, idx_min, idx_end))

    txtAM = txtAM[:-2] + '.'
    ndx = txtAM.rfind(',')
    if ndx != -1: txtAM = txtAM[:ndx] + ' and' + txtAM[ndx+1:]

    bcN_AM.sort(key=lambda x: x[0], reverse = True)    # sort tuples in-place by vis_days DESC
    bcS_AM.sort(key=lambda x: x[0], reverse = True)    # sort tuples in-place by vis_days DESC

    txtbcN_AM = '????'
    if bcN_AM[0] != None:
        vis_mid, idx1, idx2 = bcN_AM[0]
        if idx2 == -1:
            txtbcN_AM = "in " + approx_week(idx1)
        else:
            txtbcN_AM = "from {} to {}".format(approx_mth(idx1), approx_mth(idx2))

    txtbcS_AM = '????'
    if bcS_AM[0] != None:
        vis_mid, idx1, idx2 = bcS_AM[0]
        if idx2 == -1:
            txtbcS_AM = "in " + approx_week(idx1)
        else:
            txtbcS_AM = "from {} to {}".format(approx_mth(idx1), approx_mth(idx2))
        
    # evenings ...........................
    txtPM = ''
    tPM = ''
    bcN_PM = []
    bcS_PM = []

    for PM_fr, PM_to in vis_mercuryPM:
        d3 = d00 + timedelta(days=PM_fr)
        mPM1 = planet_mag(1, d3)    # magnitude of Mercury PM from
        d4 = d00 + timedelta(days=PM_to)
        mPM2 = planet_mag(1, d4)    # magnitude of Mercury PM to

        tPMtemp = 'end' if mPM2 < mPM1 else 'beginning'
        if config.debug_magnitude:
            print("Mercury magnitude PM from {dt1:%b} {dt1:%d} to {dt2:%b} {dt2:%d}: {m1:.3f} to {m2:.3f}".format(dt1=d00+timedelta(days=PM_fr), dt2=d00+timedelta(days=PM_to), m1=mPM1, m2=mPM2))
        TO_date = "{dt2:%b} {dt2:%d}".format(dt2=d00+timedelta(days=PM_to))
        if tPM != '' and tPM != tPMtemp and TO_date != 'Dec 31':
            # Note: this test excludes the first magnitude of the year (as tPM = '')
            #       the last magnitude of the year is excluded if ending on Dec 31st (e.g. year 2034)
            #       (this is necessary as the period of visibility is prematurely terminated by End of Year)
            print("ERROR: check Mercury brightness in each PM period")
            #sys.exit(0)
        tPM = tPMtemp

        if PM_fr == 0:
            txtPM += "beginning of the year to {dt4:%B} {dt4.day}, ".format(dt4=d4)
        elif AM_to == daystoprocess-1:
            txtPM += "{dt3:%B} {dt3.day} to end of the year, ".format(dt3=d3)
        else:
            txtPM += "{dt3:%B} {dt3.day} to {dt4:%B} {dt4.day}, ".format(dt3=d3, dt4=d4)

        # best conditions evenings in northern latitudes...
        mpa_max = 12.0
        idx_max = -1
        idx_from = -1
        if PM_fr < 181 and PM_to <= 181:
            vis_days = PM_to - PM_fr + 1
            if vis_days < 30:
                mid_idx = PM_fr + int(vis_days/2)
                bcN_PM.append((vis_days, mid_idx, -1))
            else:
                for idx in range(PM_fr,PM_to+1):
                    if meridian_pass[obj][idx] > mpa_max:
                        mpa_max = meridian_pass[obj][idx]
                        idx_max = idx
                idx_from = PM_fr + (vis_days/6)
                idx_end = int((idx_max + PM_to)/2)
                bcN_PM.append((vis_days, idx_from, idx_end))
        
        # best conditions evenings in southern latitudes...
        mpa_max = 12.0
        idx_max = -1
        idx_from = -1
        if PM_fr >= 181 and PM_to > 181:
            vis_days = PM_to - PM_fr + 1
            if vis_days < 30:
                mid_idx = PM_fr + int(vis_days/2)
                bcS_PM.append((vis_days, mid_idx, -1))
            else:
                for idx in range(PM_fr,PM_to+1):
                    if meridian_pass[obj][idx] > mpa_max:
                        mpa_max = meridian_pass[obj][idx]
                        idx_max = idx
                        idx_from = idx - (vis_days/6)
                idx_end = int((idx_max + PM_to)/2)
                bcS_PM.append((vis_days, idx_from, idx_end))

    txtPM = txtPM[:-2] + '.'
    ndx = txtPM.rfind(',')
    if ndx != -1: txtPM = txtPM[:ndx] + ' and' + txtPM[ndx+1:]

    bcN_PM.sort(key=lambda x: x[0], reverse = True)    # sort tuples in-place by vis_days DESC
    bcS_PM.sort(key=lambda x: x[0], reverse = True)    # sort tuples in-place by vis_days DESC

    txtbcN_PM = '????'
    if bcN_PM[0] != None:
        vis_mid, idx1, idx2 = bcN_PM[0]
        if idx2 == -1:
            txtbcN_PM = "in the " + approx_week(idx1)
        else:
            txtbcN_PM = "from {} to {}".format(approx_mth(idx1), approx_mth(idx2))
        
    txtbcS_PM = '????'
    if bcS_PM[0] != None:
        vis_mid, idx1, idx2 = bcS_PM[0]
        if idx2 == -1:
            txtbcS_PM = "in the " + approx_week(idx1)
        else:
            txtbcS_PM = "from {} to {}".format(approx_mth(idx1), approx_mth(idx2))

    # assemble the text to print .........................
    vop['mercury'] = "can only be seen low in the east before sunrise, or low in the west after sunset (about the time of civil dawn and civil dusk)."
    vop['mercury'] += r"\newline It is visible in the \textit{{mornings}} between the following approximate dates: {}".format(txtAM)
    vop['mercury'] += " The planet is brighter at the {} of each period. {{\\small (The best conditions in northern latitudes occur {} and in southern latitudes {})}}.".format(tAM, txtbcN_AM, txtbcS_AM)
    #vop['mercury'] += " The planet is brighter at the {} of each period. (The best conditions in northern latitudes occur {} and in southern latitudes {}).".format(tAM, txtbcN_AM, txtbcS_AM)

    vop['mercury'] += r"\newline It is visible in the \textit{{evenings}} between the following approximate dates: {}".format(txtPM)
    vop['mercury'] += " The planet is brighter at the {} of each period. {{\\small (The best conditions in northern latitudes occur {} and in southern latitudes {})}}.".format(tPM, txtbcN_PM, txtbcS_PM)
    #vop['mercury'] += " The planet is brighter at the {} of each period. (The best conditions in northern latitudes occur {} and in southern latitudes {}).".format(tPM, txtbcN_PM, txtbcS_PM)

    # txt = ' Mercury '
    # # scan for superior/inferior conjunction with sun
    # for jdt, j, k in conjunctions:
        # if obj in [j, k]:
            # n = k if j == obj else j
            # objn = get_object_name(n)
            # objn = objn[0].upper() + objn[1:]
            # tt = ts.tt(jd=jdt)
            # if n == 0:      # sun-mercury conjunction
                # idx = (tt.utc_datetime().date()-d00).days
                # inf_sup = 'superior' if rel_lon_delta[idx] else 'inferior'
                # txt += " in {} conjunction on {dt:%B} {dt.day} {dt:%H}h; ".format(inf_sup, dt=tt.utc_datetime()+timedelta(minutes= 30))

    # if txt != '':
        # vop['mercury'] += txt[:-2] + '.'

    #---------------------------------------------------------
    # scan for conjunctions with other *visible* planets
    # collect 'do not confuse' data for 5 planets only
    #dnc_conj = [[None] * 5 for i in range(5)]   # mercury, venus, mars, jupiter, saturn
    conj_fnd = False
    for jdt, j, k, delta, mode in conjunctions:
        if obj in [j, k]:
            obj2 = k if j == obj else j
            if j == 0: continue     # ignore sun-mercury
            if not planet_visible(obj,obj2,jdt): continue   # ignore if not visible
            objn = get_object_name(obj2)
            objn = objn[0].upper() + objn[1:]
            tt = ts.tt(jd=jdt)

            # 'do not confuse' text...
            if not conj_fnd:
                dnctxt += r"\textbf{Mercury} "
            conj_fnd = True
            d = tt.utc_datetime().date()
            idx = (d-d00).days
            m1 = planet_mag(1, d)       # mag of Mercury
            m2 = planet_mag(obj2, d)    # mag of obj2
            objbr = objn if m2 < m1 else 'Mercury'
            if abs(m1-m2) < 1.0:
                dnctxt += "with {n_obj} around {dt:%B} {dt.day} as both objects are similar in brightness; ".format(n_obj=objn,dt=tt.utc_datetime())
            else:
                dnctxt += "with {n_obj} around {dt:%B} {dt.day} when {n_br} is the brighter object; ".format(n_obj=objn,n_br=objbr,dt=tt.utc_datetime())
                #dnctxt += "{m1:.2f} {m2:.2f}  ".format(m1=m1,m2=m2)
            #dnc_conj[0][obj2-1] = (m1,m2,idx)

    # if dnctxt != "":
        # dnctxt = dnctxt[:-2] + ". "
        # dnc.append(dnctxt)

###############  VENUS  ###############
    obj = 2
    t_vis = ''
    t_vis2 = ''
    vop['venus'] = ''

    #t_vis, t_vis2 = overall_visibility(vis_venusAM, vis_venusPM, False, "a brilliant object")

    # # overall visibility through the night sky
    # AM_fr = AM_to = PM_fr = PM_to = None
    # if len(vis_venusAM) > 0:
        # AM_fr, AM_to = vis_venusAM[0]
        # d1 = d00 + timedelta(days=AM_fr)
        # mAM1 = planet_mag(1, d1)    # magnitude of Venus AM from
        # d2 = d00 + timedelta(days=AM_to)
        # mAM2 = planet_mag(1, d2)    # magnitude of Venus AM to

    # if len(vis_venusPM) > 0:
        # PM_fr, PM_to = vis_venusPM[0]
        # d3 = d00 + timedelta(days=PM_fr)
        # mPM1 = planet_mag(1, d3)    # magnitude of Venus PM from
        # d4 = d00 + timedelta(days=PM_to)
        # mPM2 = planet_mag(1, d4)    # magnitude of Venus PM to

    # txtAMPM = txt_fr = None
    # if AM_fr == 0:
        # txtAMPM = "morning"
        # txt_fr = "the begining of the year"
        # txt_to = approx_mth(AM_to)
        # if PM_fr != None:
            # txt_fr2 = approx_week(PM_fr)
            # txtAMPM2 = "morning"
            # txt_to2 = approx_mth(PM_to)
    # elif PM_fr == 0:
        # txtAMPM = "evening"
        # txt_fr = "the begining of the year"
        # txt_to = approx_mth(PM_to)
        # if AM_fr != None:
            # txt_fr2 = approx_week(AM_fr)
            # txtAMPM2 = "morning"
            # txt_to2 = approx_mth(AM_to)
    # else:   # if not visible at the beginning of the year
        # if AM_fr != None and PM_fr != None:
            # if AM_fr < PM_fr:
                # txtAMPM = "morning"
                # txt_fr = approx_mth(AM_fr)
                # if AM_to < daystoprocess-1:
                    # txt_to = approx_mth(AM_to)
                    # txt_fr2 = approx_mth(PM_fr)
                    # txtAMPM2 = "evening"
            # else:
                # txtAMPM = "evening"
                # txt_fr = approx_week(PM_fr)
                # if PM_to < daystoprocess-1:
                    # txt_to = approx_mth(PM_to)
                    # txt_fr2 = approx_mth(AM_fr)
                    # txtAMPM2 = "morning"
        # else:
            # txt_fr = "????"
            # txt_to = "????"
            # txt_fr2 = "????"
            # txt_to2 = "????"
            # txtAMPM = "????"
            # txtAMPM2 = "????"

    # if AM_fr == 0 or PM_fr == 0:
        # t_vis = "is a brilliant object in the {} sky from {} until {} when it becomes too close to the sun for observation. ".format(txtAMPM, txt_fr, txt_to)

        # t_vis2 = "In {} it reappears in the {} sky where it stays until {}.".format(txt_fr2, txtAMPM2, txt_to2)
    # else:
        # t_vis = "is too close to the Sun for observation until the {} when it appears as a brilliant object in the {} sky. ".format(txt_fr, txtAMPM)

        # t_vis2 = "In {} it again becomes too close to the Sun for observation until {} when it reappears in the {} sky. ".format(txt_to, txt_fr2, txtAMPM2)

    # if t_vis != '':
        # vop['venus'] += t_vis
    # if t_vis2 != '':
        # vop['venus'] += t_vis2

    global venusVIS
    t_vis = overall_visibility(obj, venusVIS, False, False, True)

    if t_vis != '':
        vop['venus'] += t_vis
    t_vis = ""

    #---------------------------------------------------------
    # scan for conjunctions with other planets sorting them by planet and then by date
    # also scan and append (inferior/superior) conjunctions with sun
    txt = ''
    txt_conj = [''] * 8
    sun_conj = False
    for jdt, j, k, delta, mode in conjunctions:
        if obj in [j, k]:
            obj2 = k if j == obj else j
            # unless it's a conjunction with the sun, skip if planet not visible
            if j != 0 and not planet_visible(obj,obj2,jdt): continue
            objn = get_object_name(obj2)
            objn = objn[0].upper() + objn[1:]
            tt = ts.tt(jd=jdt)
            if obj2 == 0:   # sun-venus inferior/superior conjunction
                dstart = tt.utc_datetime().date()
                rel_lon = relative_lon(0, obj, dstart, 2)
                curr_rel_lon = rel_lon[0]*todegrees
                next_rel_lon = rel_lon[1]*todegrees
                rel_incr = True if next_rel_lon > curr_rel_lon else False
                inf_sup = 'superior' if rel_incr else 'inferior'
                if not sun_conj: txt_conj[0] += " Venus is "
                sun_conj = True
                txt_conj[0] += "in {} conjunction on {dt:%B} {dt.day} {dt:%H}h; ".format(inf_sup, dt=tt.utc_datetime()+timedelta(minutes= 30))
            else:
                ob1 = "Venus" if obj2 == k else objn
                ob2 = "Venus" if obj2 != k else objn
                txt2 = r"{{\small ({} {}. of {})}}".format(ob1, delta, ob2)
                txt_conj[obj2] += "{dt:%B} {dt.day} {dt:%H}h {t}, ".format(dt=tt.utc_datetime()+timedelta(minutes= 30),t=txt2)

    if sun_conj:
        txt += txt_conj[0][:-2] + '.'

    in_conj = False
    for i in [1, 2, 3, 4, 5]:   # omit Sun, Uranus & Neptune
        if txt_conj[i] != '':
            txt_conj[i] = txt_conj[i][:-2] + '; '
            ndx = txt_conj[i].rfind(',')
            if ndx != -1: txt_conj[i] = txt_conj[i][:ndx] + ' and' + txt_conj[i][ndx+1:]
            if not in_conj: txt += " Venus is in conjunction "
            in_conj = True
            objn = get_object_name(i)
            objn = objn[0].upper() + objn[1:]
            txt += "with {} on ".format(objn)
            txt += txt_conj[i]

    if txt != '': txt = txt[:-2] + '.'
    ndx = txt.rfind(';')
    if ndx != -1: txt = txt[:ndx] + ' and' + txt[ndx+1:]

    if txt != '':
        vop['venus'] += txt


#######################################
#  Superior Planets: Mars, Jupiter, Saturn
#
#  The superior planets have four visibility phenomena:
#  1. First visibility or heliacal rising (F): the first visibility of the
#     planet in the east before sunrise following conjunction with the sun.
#  2. Last visibility or heliacal setting (L): the last visibility of the
#     planet in the west after sunset preceding conjunction with the sun.
#  3. Acronychal or evening rising (acron): the last evening the planet is seen to rise
#     in the east following sunset, which usually occurs before opposition to the sun.
#  4. Cosmical or morning setting (cos): the first morning the planet is seen to set
#     in the west before sunrise, which usually occurs after opposition to the sun.
#
###############  MARS  ################
    obj = 3
    t_vis = ''
    vop['mars'] = ''

    # # overall visibility through the night sky
    # AM_fr = AM_to = PM_fr = PM_to = None
    # if len(vis_marsAM) > 0:
        # AM_fr, AM_to = vis_marsAM[0]
        # d1 = d00 + timedelta(days=AM_fr)
        # mAM1 = planet_mag(1, d1)    # magnitude of Venus AM from
        # d2 = d00 + timedelta(days=AM_to)
        # mAM2 = planet_mag(1, d2)    # magnitude of Venus AM to

    # if len(vis_marsPM) > 0:
        # PM_fr, PM_to = vis_marsPM[0]
        # d3 = d00 + timedelta(days=PM_fr)
        # mPM1 = planet_mag(1, d3)    # magnitude of Venus PM from
        # d4 = d00 + timedelta(days=PM_to)
        # mPM2 = planet_mag(1, d4)    # magnitude of Venus PM to

    # txtAMPM = txt_fr = None
    # if AM_fr == 0:
        # txtAMPM = "morning"
        # txt_fr = "the begining of the year"
        # txt_to = approx_mth(AM_to)
        # if PM_fr != None:
            # txt_fr2 = approx_week(PM_fr)
            # txtAMPM2 = "morning"
            # txt_to2 = approx_mth(PM_to)
    # elif PM_fr == 0:
        # txtAMPM = "evening"
        # txt_fr = "the begining of the year"
        # txt_to = approx_mth(PM_to)
        # if AM_fr != None:
            # txt_fr2 = approx_week(AM_fr)
            # txtAMPM2 = "morning"
            # txt_to2 = approx_mth(AM_to)
    # else:   # if not visible at the beginning of the year
        # if AM_fr != None and PM_fr != None:
            # if AM_fr < PM_fr:
                # txtAMPM = "morning"
                # txt_fr = approx_mth(AM_fr)
                # if AM_to < daystoprocess-1:
                    # txt_to = approx_mth(AM_to)
                    # txt_fr2 = approx_mth(PM_fr)
                    # txtAMPM2 = "evening"
            # else:
                # txtAMPM = "evening"
                # txt_fr = approx_week(PM_fr)
                # if PM_to < daystoprocess-1:
                    # txt_to = approx_mth(PM_to)
                    # txt_fr2 = approx_mth(AM_fr)
                    # txtAMPM2 = "morning"
        # else:
            # txt_fr = "????"
            # txt_to = "????"
            # txt_fr2 = "????"
            # txt_to2 = "????"
            # txtAMPM = "????"
            # txtAMPM2 = "????"

    # if AM_fr == 0 or PM_fr == 0:
        # t_vis = "can be seen in the {} sky from {} until {} when it becomes too close to the sun for observation. ".format(txtAMPM, txt_fr, txt_to)

        # t_vis2 = "In the {} it reappears in the {} sky where it stays until {}. ".format(txt_fr2, txtAMPM2, txt_to2)
    # else:
        # t_vis = "is too close to the Sun for observation until the {} when it appears as a brilliant object in the {} sky. ".format(txt_fr, txtAMPM)

        # t_vis2 = "In {} it again becomes too close to the Sun for observation until {} when it reappears in the {} sky. ".format(txt_to, txt_fr2, txtAMPM2)

    # if t_vis != '':
        # vop['mars'] += t_vis
    # if t_vis2 != '':
        # vop['mars'] += t_vis2

    # scan for at opposition
    txt = ''
    dt = None
    for jdt, j, k in oppositions:
        if obj == k:
            tt = ts.tt(jd=jdt)
            dt = tt.utc_datetime() + timedelta(minutes= 30) # round to hours
            idx = (dt.date() - d00).days
            txt += "Mars is at opposition on {dt1:%B} {dt1.day} {dt1:%H}h, when it can be seen throughout the night. ".format(dt1=dt)
            txt += "Its westward elongation gradually increases until {dt1:%B} {dt1.day} after which its eastward elongation decreases. ".format(dt1=dt)

    global marsVIS
    t_vis = overall_visibility(obj, marsVIS, True, False)

    if t_vis != '':
        vop['mars'] += t_vis
    t_vis = ""

    #---------------------------------------------------------
    # scan for conjunctions with other planets sorting them by planet and then by date
    txt_conj = [''] * 8
    for jdt, j, k, delta, mode in conjunctions:
        if j == 0: continue     # opt to exclude conjuctions with the sun
        if obj in [j, k]:
            obj2 = k if j == obj else j
            # unless it's a conjunction with the sun, skip if planet not visible
            if j != 0 and not planet_visible(obj,obj2,jdt): continue
            objn = get_object_name(obj2)
            objn = objn[0].upper() + objn[1:]
            tt = ts.tt(jd=jdt)
            ob1 = "Mars" if obj2 == k else objn
            ob2 = "Mars" if obj2 != k else objn
            txt2 = r"{{\small ({} {}. of {})}}".format(ob1, delta, ob2)
            txt_conj[obj2] += "{dt:%B} {dt.day} {dt:%H}h {t}, ".format(dt=tt.utc_datetime()+timedelta(minutes= 30),t=txt2)

    in_conj = False
    for i in [1, 2, 3, 4, 5]:   # omit Sun, Uranus & Neptune
        if txt_conj[i] != '':
            txt_conj[i] = txt_conj[i][:-2] + '; '
            ndx = txt_conj[i].rfind(',')
            if ndx != -1: txt_conj[i] = txt_conj[i][:ndx] + ' and' + txt_conj[i][ndx+1:]
            if not in_conj: txt += " Mars is in conjunction "
            in_conj = True
            objn = get_object_name(i)
            objn = objn[0].upper() + objn[1:]
            txt += "with {} on ".format(objn)
            txt += txt_conj[i]

    if txt != '': txt = txt[:-2] + '.'
    ndx = txt.rfind(';')
    if ndx != -1: txt = txt[:ndx] + ' and' + txt[ndx+1:]

    if txt != '':
        vop['mars'] += txt

##############  JUPITER  ##############
    obj = 4
    txt = dnctxt = ''
    vop['jupiter'] = ''

    # scan for at opposition
    dt = None
    in_oppo = False
    for jdt, j, k in oppositions:
        if obj == k:
            tt = ts.tt(jd=jdt)
            dt = tt.utc_datetime() + timedelta(minutes= 30) # round to hours
            idx = (dt.date() - d00).days
            txt += " Jupiter is at opposition on {dt1:%B} {dt1.day} {dt1:%H}h, when it is visible throughout the night. ".format(dt1=dt)
            in_oppo = True

    global jupiterVIS
    t_vis = overall_visibility(obj, jupiterVIS)

    if t_vis != '':
        vop['jupiter'] += t_vis
    t_vis = ""

    #---------------------------------------------------------
    # scan for conjunctions with other planets sorting them by planet and then by date
    txt_conj = [''] * 8
    in_conj = False
    #with_obj = -1
    for jdt, j, k, delta, mode in conjunctions:
        if j == 0: continue     # opt to exclude conjuctions with the sun
        if obj in [j, k]:
            obj2 = k if j == obj else j
            # unless it's a conjunction with the sun, skip if planet not visible
            if j != 0 and not planet_visible(obj,obj2,jdt): continue
            if not in_conj: dnctxt += r"\textbf{Jupiter} "
                #if in_oppo: txt += "Jupiter"
                #txt += " is in conjunction "
            in_conj = True
            objn = get_object_name(obj2)
            objn = objn[0].upper() + objn[1:]
            tt = ts.tt(jd=jdt)
            #if with_obj != -1: txt = txt[:-2] + '; '
            ob1 = "Jupiter" if obj2 == k else objn
            ob2 = "Jupiter" if obj2 != k else objn
            txt2 = r"{{\small ({} {}. of {})}}".format(ob1, delta, ob2)
            # if obj2 != with_obj:
                # txt += "with {} on {dt:%B} {dt.day} {dt:%H}h {t}; ".format(objn,dt=tt.utc_datetime()+timedelta(minutes= 30),t=txt2)
            # else:
                # txt = txt[:-2] + " and on {dt:%B} {dt.day} {dt:%H}h {t}; ".format(dt=tt.utc_datetime()+timedelta(minutes= 30),t=txt2)
            #with_obj = obj2
            txt_conj[obj2] += "{dt:%B} {dt.day} {dt:%H}h {t}, ".format(dt=tt.utc_datetime()+timedelta(minutes= 30),t=txt2)

            # 'do not confuse' text...
            # exclude if conjunction with sun (already skipped if planet not visible)
            if j == 0: continue
            #if j == 0 or obj2 == 5: continue   # and exclude jupiter-saturn (handled below)
            d = tt.utc_datetime().date()
            idx = (d-d00).days
            dnctxt += "with {} {}; ".format(objn,approx_month(idx))

            #m1 = planet_mag(4, d)       # mag of Jupiter
            #m2 = planet_mag(obj2, d)    # mag of obj2
            #dnc_conj[3][obj2-1] = (m1,m2,idx)

    in_conj = False
    for i in [1, 2, 3, 4, 5]:   # omit Sun, Uranus & Neptune
        if txt_conj[i] != '':
            txt_conj[i] = txt_conj[i][:-2] + '; '
            ndx = txt_conj[i].rfind(',')
            if ndx != -1: txt_conj[i] = txt_conj[i][:ndx] + ' and' + txt_conj[i][ndx+1:]
            if not in_conj:
                txt += " Jupiter is in conjunction "
                #dnctxt += "Jupiter "
            in_conj = True
            objn = get_object_name(i)
            objn = objn[0].upper() + objn[1:]
            txt += "with {} on ".format(objn)
            txt += txt_conj[i]

    if txt != '': txt = txt[:-2] + '.'
    ndx = txt.rfind(';')
    if ndx != -1: txt = txt[:ndx] + ' and' + txt[ndx+1:]

    #---------------------------------------------------------
    # 'do not confuse' text...
    # check for close proximity to Saturn for a period of time
    rel_lon = relative_lon(obj, 5, d00, daystoprocess)
    idx = 0
    close_fr = 0
    planets_close = []  # list of tuples: (from_idx, to_idx)
    close_proximity = None      # current proximity state

    while idx < daystoprocess:
        curr_rel_lon = abs(rel_lon[idx]*todegrees)
        curr_proximity = True if curr_rel_lon <= 5.0 else False
        if idx == 0:  # get initial proximity state
            close_proximity = curr_proximity
            if curr_proximity: close_fr = idx
            #print("initial proximity: {:.2f}".format(curr_rel_lon))
        else:
            if curr_proximity and not close_proximity:
                close_fr = idx
            if not curr_proximity and close_proximity:
                planets_close.append((close_fr, idx-1))
                dt1 = d00 + timedelta(days=close_fr)
                dt2 = d00 + timedelta(days=idx-1)
                #print("{}-{} close from {} to {}".format(get_object_name(obj), get_object_name(5),dt1.strftime("%b %d"),dt2.strftime("%b %d")))
        close_proximity = curr_proximity

        idx += 1

    # check end state on Dec 31
    if curr_proximity and close_proximity:
        planets_close.append((close_fr, idx-1))
        dt1 = d00 + timedelta(days=close_fr)
        dt2 = d00 + timedelta(days=idx-1)
        #print("{}-{} close from {} to {}".format(get_object_name(obj), get_object_name(5),dt1.strftime("%b %d"),dt2.strftime("%b %d")))

    # 'do not confuse' text...
    len_pc = len(planets_close)
    if len_pc > 0:
        i = len_pc
        dnctxt += "with Saturn "
        for close_fr, close_to in planets_close:
            sep = ' and' if len_pc > 1 and i == 2 else ','
            dnctxt += "{}{} ".format(approx_month(close_fr,close_to),sep)
            i -= 1

            #d = d00 + timedelta(days=close_fr)
            #m1 = planet_mag(4, d)       # mag of Jupiter
            #m2 = planet_mag(5, d)       # mag of Saturn
            #dnc_conj[3][4] = (m1,m2,close_fr,close_to)

    # if dnctxt != "":
        # dnctxt = dnctxt[:-2] + ". "
        # dnc.append(dnctxt)

    if txt != '':
        vop['jupiter'] += txt


##############  SATURN  ###############
    obj = 5
    txt = dnctxt = ''
    vop['saturn'] = ''

    # scan for at opposition
    dt = None
    in_oppo = False
    #idx_oppo = None
    txt_oppo = ""
    for jdt, j, k in oppositions:
        if obj == k:
            tt = ts.tt(jd=jdt)
            dt = tt.utc_datetime() + timedelta(minutes= 30) # round to hours
            #idx_oppo = (dt.date() - d00).days
            txt += " Saturn is at opposition on {dt1:%B} {dt1.day} {dt1:%H}h, when it is visible throughout the night. ".format(dt1=dt)
            in_oppo = True
    #print("idx_oppo",idx_oppo)

    global saturnVIS
    t_vis = overall_visibility(obj, saturnVIS)

    if t_vis != '':
        vop['saturn'] += t_vis
    t_vis = ""

    #---------------------------------------------------------
    # scan for conjunctions with other planets sorting them by planet and then by date
    txt_conj = [''] * 8
    in_conj = False
    #with_obj = -1
    for jdt, j, k, delta, mode in conjunctions:
        if j == 0: continue     # opt to exclude conjuctions with the sun
        if obj in [j, k]:
            obj2 = k if j == obj else j
            # unless it's a conjunction with the sun, skip if planet not visible
            if j != 0 and not planet_visible(obj,obj2,jdt): continue
            if not in_conj: dnctxt += r"textbf{Saturn} "
                #if in_oppo: txt += "Saturn"
                #txt += " is in conjunction "
            in_conj = True
            objn = get_object_name(obj2)
            objn = objn[0].upper() + objn[1:]
            tt = ts.tt(jd=jdt)
            #if with_obj != -1: txt = txt[:-2] + '; '
            ob1 = "Saturn" if obj2 == k else objn
            ob2 = "Saturn" if obj2 != k else objn
            txt2 = r"{{\small ({} {}. of {})}}".format(ob1, delta, ob2)
            # if obj2 != with_obj:
                # txt += "with {} on {dt:%B} {dt.day} {dt:%H}h {t}; ".format(objn,dt=tt.utc_datetime()+timedelta(minutes= 30),t=txt2)
            # else:
                # txt = txt[:-2] + " and on {dt:%B} {dt.day} {dt:%H}h {t}; ".format(dt=tt.utc_datetime()+timedelta(minutes= 30),t=txt2)
            # in_conj = True
            # with_obj = obj2
            txt_conj[obj2] += "{dt:%B} {dt.day} {dt:%H}h {t}, ".format(dt=tt.utc_datetime()+timedelta(minutes= 30),t=txt2)

            # 'do not confuse' text...
            # exclude if conjunction with sun (already skipped if planet not visible)
            if j == 0: continue
            #if j == 0 or obj2 == 4: continue   # and exclude jupiter-saturn (handled above)
            idx = (tt.utc_datetime().date()-d00).days
            dnctxt += "with {} {}, ".format(objn,approx_month(idx))

    in_conj = False
    for i in [1, 2, 3, 4, 5]:   # omit Sun, Uranus & Neptune
        if txt_conj[i] != '':
            txt_conj[i] = txt_conj[i][:-2] + '; '
            ndx = txt_conj[i].rfind(',')
            if ndx != -1: txt_conj[i] = txt_conj[i][:ndx] + ' and' + txt_conj[i][ndx+1:]
            if not in_conj:
                txt += " Saturn is in conjunction "
                #dnctxt += "Saturn "
            in_conj = True
            objn = get_object_name(i)
            objn = objn[0].upper() + objn[1:]
            txt += "with {} on ".format(objn)
            txt += txt_conj[i]

    if txt != '': txt = txt[:-2] + '.'
    ndx = txt.rfind(';')
    if ndx != -1: txt = txt[:ndx] + ' and' + txt[ndx+1:]

    # if dnctxt != "":
        # dnctxt = dnctxt[:-2] + ". "
        # dnc.append(dnctxt)

    if txt != '':
        vop['saturn'] += txt

##############  URANUS  ###############
    obj = 6
    txt = ''
    vop['uranus'] = ''

    # scan for at opposition
    for jdt, j, k in oppositions:
        if obj == k:
            tt = ts.tt(jd=jdt)
            dt = tt.utc_datetime() + timedelta(minutes= 30) # round to hours
            txt += " Uranus is at opposition on {dt:%B} {dt.day} {dt:%H}h. ".format(dt=dt)

    global uranusVIS
    t_vis = overall_visibility(obj, uranusVIS)

    if t_vis != '':
        vop['uranus'] += t_vis
    t_vis = ""

    if txt != '':
        vop['uranus'] += txt[:-1]

##############  NEPTUNE  ##############
    obj = 7
    txt = ''
    vop['neptune'] = ''

    # scan for at opposition
    idx_oppo = None
    for jdt, j, k in oppositions:
        if obj == k:
            tt = ts.tt(jd=jdt)
            dt = tt.utc_datetime() + timedelta(minutes= 30) # round to hours
            txt += " Neptune is at opposition on {dt:%B} {dt.day} {dt:%H}h. ".format(dt=dt)

    global neptuneVIS
    t_vis = overall_visibility(obj, neptuneVIS)

    if t_vis != '':
        vop['neptune'] += t_vis
    t_vis = ""

    if txt != '':
        vop['neptune'] += txt[:-1]

#---------------------------------------------------------------------------#
####  DO NOT CONFUSE TEXT (quote the planet with lower magnitude first)  ####
#---------------------------------------------------------------------------#

    # determine visibility range (for VISIBILITY OF PLANETS table & DNC-section)
    global venusAM, venusPM, vis_venusAM, vis_venusPM
    vis_venusAM = visibility_range(venusAM)  # begin,end of morning visibility
    vis_venusPM = visibility_range(venusPM)  # begin,end of evening visibility

    global marsAM, marsPM, vis_marsAM, vis_marsPM
    vis_marsAM = visibility_range(marsAM)  # begin,end of morning visibility
    vis_marsPM = visibility_range(marsPM)  # begin,end of evening visibility

    global jupiterAM, jupiterPM, vis_jupiterAM, vis_jupiterPM
    vis_jupiterAM = visibility_range(jupiterAM)  # begin,end of morning visibility
    vis_jupiterPM = visibility_range(jupiterPM)  # begin,end of evening visibility

    global saturnAM, saturnPM, vis_saturnAM, vis_saturnPM
    vis_saturnAM = visibility_range(saturnAM)  # begin,end of morning visibility
    vis_saturnPM = visibility_range(saturnPM)  # begin,end of evening visibility

    global uranusAM, uranusPM, vis_uranusAM, vis_uranusPM
    vis_uranusAM = visibility_range(uranusAM)  # begin,end of morning visibility
    vis_uranusPM = visibility_range(uranusPM)  # begin,end of evening visibility

    global neptuneAM, neptunePM, vis_neptuneAM, vis_neptunePM
    vis_neptuneAM = visibility_range(neptuneAM)  # begin,end of morning visibility
    vis_neptunePM = visibility_range(neptunePM)  # begin,end of evening visibility


    #---------------------------------------------------------
    # check if close to other planets for 'do not confuse' text

    ref_count = [0] * 5     # referenced count per planet
    tup_close = [[None] * 6 for i in range(5)]  # tup_close[0 to 4][0 to 5]
    # 1 Mercury, 2 Venus, 3 Mars, 4 Jupiter, 5 Saturn
    for j in [1, 2, 3, 4]:
        for k in range(j+1,6):
            tup_close[j-1][k-1] = planets_near(j, k, daystoprocess, 5.0, planet_app_pos)
            if len(tup_close[j-1][k-1]) > 0:
                #print(j,k)
                ref_count[j-1] += 1
                ref_count[k-1] += 1
    #print("close references", ref_count)

    # for x_fr, x_to in tup_close[1][2]:
        # d1 = d00 + timedelta(days=x_fr)
        # d2 = d00 + timedelta(days=x_to)
        # print("close: ", d1, d2)

    #----- MERCURY dnc -----

    dnctxt = ""
    obj = 1
    objn = get_object_name(obj)
    objn = objn[0].upper() + objn[1:]
    for j, k in [(1,3), (1,4), (1,5)]:
        dnc0 = ""
        obj2 = k if j == obj else j
        obj2n = get_object_name(obj2)
        obj2n = obj2n[0].upper() + obj2n[1:]
        for x_fr, x_to in tup_close[j-1][k-1]:
            x_fr, x_to = only_when_visible(obj,x_fr,x_to)
            x_fr, x_to = only_when_visible(obj2,x_fr,x_to)
            if x_fr == None: continue
            # if x_to - x_fr <= 2: break  # ignore if range is <= 2 days
            if dnctxt == "": dnctxt = r"\textbf{{{}}} ".format(objn)
            if dnc0 == "": dnc0 = r"\textbf{{with {}}} ".format(obj2n)
            d1 = d00 + timedelta(days=x_fr)
            d2 = d00 + timedelta(days=x_to)
            dnc0 += "between {d1:%b} {d1.day} and {d2:%b} {d2.day}, ".format(d1=d1,d2=d2)
        if dnc0 != '': dnc0 = dnc0[:-2] + '; '
        ndx = dnc0.rfind(',')
        if ndx != -1: dnc0 = dnc0[:ndx] + ' and' + dnc0[ndx+1:]
        if dnc0 != "": dnctxt += dnc0

    if dnctxt != "":
        dnctxt = dnctxt[:-2] + ". "
        dnc.append(dnctxt)

    #----- VENUS dnc -----

    dnctxt = ""
    obj = 2
    objn = get_object_name(obj)
    objn = objn[0].upper() + objn[1:]
    for j, k in [(1,2), (2,3), (2,4), (2,5)]:
        dnc0 = ""
        obj2 = k if j == obj else j
        obj2n = get_object_name(obj2)
        obj2n = obj2n[0].upper() + obj2n[1:]
        for x_fr, x_to in tup_close[j-1][k-1]:
            x_fr, x_to = only_when_visible(obj,x_fr,x_to)
            x_fr, x_to = only_when_visible(obj2,x_fr,x_to)
            if x_fr == None: continue
            # if x_to - x_fr <= 2: break  # ignore if range is <= 2 days
            if dnctxt == "": dnctxt = r"\textbf{{{}}} ".format(objn)
            if dnc0 == "": dnc0 = r"\textbf{{with {}}} ".format(obj2n)
            d1 = d00 + timedelta(days=x_fr)
            d2 = d00 + timedelta(days=x_to)
            dnc0 += "between {d1:%b} {d1.day} and {d2:%b} {d2.day}, ".format(d1=d1,d2=d2)
        if dnc0 != '': dnc0 = dnc0[:-2] + '; '
        ndx = dnc0.rfind(',')
        if ndx != -1: dnc0 = dnc0[:ndx] + ' and' + dnc0[ndx+1:]
        if dnc0 != "": dnctxt += dnc0

    if dnctxt != "":
        dnctxt = dnctxt[:-2] + ". "
        dnc.append(dnctxt)

    #----- MARS dnc -----

    dnctxt = ""
    obj = 3
    objn = get_object_name(obj)
    objn = objn[0].upper() + objn[1:]
    for j, k in [(3,4), (3,5)]:
        dnc0 = ""
        obj2 = k if j == obj else j
        obj2n = get_object_name(obj2)
        obj2n = obj2n[0].upper() + obj2n[1:]
        for x_fr, x_to in tup_close[j-1][k-1]:
            x_fr, x_to = only_when_visible(obj,x_fr,x_to)
            x_fr, x_to = only_when_visible(obj2,x_fr,x_to)
            if x_fr == None: continue
            # if x_to - x_fr <= 2: break  # ignore if range is <= 2 days
            if dnctxt == "": dnctxt = r"\textbf{{{}}} ".format(objn)
            if dnc0 == "": dnc0 = r"\textbf{{with {}}} ".format(obj2n)
            d1 = d00 + timedelta(days=x_fr)
            d2 = d00 + timedelta(days=x_to)
            dnc0 += "between {d1:%b} {d1.day} and {d2:%b} {d2.day}, ".format(d1=d1,d2=d2)
        if dnc0 != '': dnc0 = dnc0[:-2] + '; '
        ndx = dnc0.rfind(',')
        if ndx != -1: dnc0 = dnc0[:ndx] + ' and' + dnc0[ndx+1:]
        if dnc0 != "": dnctxt += dnc0

    if dnctxt != "":
        dnctxt = dnctxt[:-2] + ". "
        dnc.append(dnctxt)

    #----- JUPITER dnc -----

    dnctxt = ""
    obj = 4
    objn = get_object_name(obj)
    objn = objn[0].upper() + objn[1:]
    for j, k in [(4,5)]:
        dnc0 = ""
        obj2 = k if j == obj else j
        obj2n = get_object_name(obj2)
        obj2n = obj2n[0].upper() + obj2n[1:]
        for x_fr, x_to in tup_close[j-1][k-1]:
            x_fr, x_to = only_when_visible(obj,x_fr,x_to)
            x_fr, x_to = only_when_visible(obj2,x_fr,x_to)
            if x_fr == None: continue
            # if x_to - x_fr <= 2: break  # ignore if range is <= 2 days
            if dnctxt == "": dnctxt = r"\textbf{{{}}} ".format(objn)
            if dnc0 == "": dnc0 = r"\textbf{{with {}}} ".format(obj2n)
            d1 = d00 + timedelta(days=x_fr)
            d2 = d00 + timedelta(days=x_to)
            dnc0 += "between {d1:%b} {d1.day} and {d2:%b} {d2.day}, ".format(d1=d1,d2=d2)
        if dnc0 != '': dnc0 = dnc0[:-2] + '; '
        ndx = dnc0.rfind(',')
        if ndx != -1: dnc0 = dnc0[:ndx] + ' and' + dnc0[ndx+1:]
        if dnc0 != "": dnctxt += dnc0

    if dnctxt != "":
        dnctxt = dnctxt[:-2] + ". "
        dnc.append(dnctxt)

    #----- SATURN dnc -----

    # dnctxt = ""
    # obj = 5
    # objn = get_object_name(obj)
    # objn = objn[0].upper() + objn[1:]
    # for j, k in [(1,5)]:
        # dnc0 = ""
        # obj2 = k if j == obj else j
        # obj2n = get_object_name(obj2)
        # obj2n = obj2n[0].upper() + obj2n[1:]
        # for x_fr, x_to in tup_close[j-1][k-1]:
            # x_fr, x_to = only_when_visible(obj,x_fr,x_to)
            # x_fr, x_to = only_when_visible(obj2,x_fr,x_to)
            # if x_fr == None: continue
            # if x_to - x_fr <= 2: break  # ignore if range is <= 2 days
            # if dnctxt == "": dnctxt = r"\textbf{{{}}} ".format(objn)
            # if dnc0 == "": dnc0 = r"\textbf{{with {}}} ".format(obj2n)
            # d1 = d00 + timedelta(days=x_fr)
            # d2 = d00 + timedelta(days=x_to)
            # dnc0 += "between {d1:%b} {d1.day} and {d2:%b} {d2.day}, ".format(d1=d1,d2=d2)
        # ndx = dnc0.rfind(',')
        # if ndx != -1: dnc0 = dnc0[:ndx] + ' and' + dnc0[ndx+1:]
        # if dnc0 != "": dnctxt += dnc0[:-2] + "; "

    # if dnctxt != "":
        # dnctxt = dnctxt[:-2] + ". "
        # dnc.append(dnctxt)


    txt = r'''
  \begin{enumerate*}[label={(\arabic*)}]'''
    for item in dnc:
        txt += r'''
  \item ''' + item

    txt += r'''
  \end{enumerate*}'''
    
    vop['dnc'] = txt

# --------- VISIBILITY OF PLANETS section ---------

    # lat = lats[:-2]  # latitude (degrees)
    lat = "{:03.1f}".format(abs(lats))
    # lns = lats[-1]   # latitude N = North, s = South
    lns = 'N' if lats >= 0 else 'S'

    tex = r'''
% ====== VISIBILITY OF PLANETS section ======
  \newpage
  % for the this page only...
  \newgeometry{{nomarginpar, top={}, bottom={}, left={}, right={}}}'''.format(tm1,bm1,lm1,rm1)

    # NOTE: do not use '\centerline{\Large\textbf{....}}}\\[12pt]' below
    #       as this causes 'Underfull \hbox (badness 10000)'

    tex += r'''
  \setcounter{page}{2}      %% otherwise it's 1
  \thispagestyle{empty}     %% no page number
  \noindent
  \begin{center}
  \Large\textbf{PHENOMENA, %s}\\[8pt]
  \large\textbf{VISIBILITY OF PLANETS AT LATITUDE %s°%s}\\[-6pt]
  \end{center}''' % (str(yy),lat,lns)

    if config.pgsz == "Letter":
        tex += r'''
  \setlength{\columnsep}{18pt}'''
    else:
        tex += r'''
  \setlength{\columnsep}{20pt}'''

    tex += r'''
  \begin{multicols}{2}
  \normalsize\noindent
  MERCURY %s
''' %(vop['mercury'])

    tex += r'''
  VENUS %s
''' %(vop['venus'])

    tex += r'''
  MARS%s
''' %(vop['mars'])

    tex += r'''
  JUPITER%s
''' %(vop['jupiter'])

    if vop['saturn'] != '': tex += r'''
  SATURN%s
''' %(vop['saturn'])

    if config.plotUN and vop['uranus'] != '': tex += r'''
  URANUS%s
''' %(vop['uranus'])

    if config.plotUN and vop['neptune'] != '': tex += r'''
  NEPTUNE%s
''' %(vop['neptune'])

    tex += r'''
  DO NOT CONFUSE %s
  \end{multicols}''' %(vop['dnc'])

# --------- VISIBILITY OF PLANETS IN MORNING AND EVENING TWILIGHT section ---------

# table layout technique: https://tex.stackexchange.com/questions/12703/how-to-create-fixed-width-table-columns-with-text-raggedright-centered-raggedlef

    rowsep = r'\\[2pt]'     # 2Pt vertical space initially for the top row
    tex += r'''
  \vspace{-12Pt}
  \noindent
  \begin{center}
  \large\textbf{VISIBILITY OF PLANETS IN MORNING AND EVENING TWILIGHT}\\[8pt]
  \setlength{\tabcolsep}{2pt}
  \begin{tabular}{L{0.06\textwidth} R{0.1\textwidth} C{0.01\textwidth} L{0.1\textwidth} R{0.1\textwidth} C{0.01\textwidth} L{0.1\textwidth}}
 & \multicolumn{3}{c}{Morning} & \multicolumn{3}{c}{Evening}'''

    #print("visibility_AM_PM - Venus")
    texrow, rowsep = visibility_AM_PM("Venus", vis_venusAM, vis_venusPM, rowsep)
    tex += texrow

    #print("visibility_AM_PM - Mars")
    texrow, rowsep = visibility_AM_PM("Mars", vis_marsAM, vis_marsPM, rowsep)
    tex += texrow

    #print("visibility_AM_PM - Jupiter")
    texrow, rowsep = visibility_AM_PM("Jupiter", vis_jupiterAM, vis_jupiterPM, rowsep)
    tex += texrow

    #print("visibility_AM_PM - Saturn")
    texrow, rowsep = visibility_AM_PM("Saturn", vis_saturnAM, vis_saturnPM, rowsep)
    tex += texrow

    # terminate the last row (but without '\midrule')
    tex += r'''\\
  \end{tabular}
  \end{center}
\restoregeometry    % so it does not affect the rest of the pages'''

    return tex

def endPDF():
    tex = r"""
\end{document}"""
    return tex


# oooooooooooooooooooooooooooooooooooooooooooooooooooo
# oooooooooooooooooo PLANET DIAGRAM oooooooooooooooooo
# oooooooooooooooooooooooooooooooooooooooooooooooooooo


def mp_sunrise_worker(Date, sun_Y, params, ts, mth):
    #print(" mp_sunrise_worker Start {}".format(mth))
    tup = mp_sunrise_set(Date, mth, params, sf, sun_Y, ts)       # ===>>> mp_functions.py
    #print(" mp_sunrise_worker Finish {}".format(mth))
    return tup      # return tuple of list data for a month

# global variables >>> d00, daystoprocess, tup_crosspoints
def chart_LocalMeanTimeOfMeridianPassage(lats, ts):
    global tup_crosspoints
    datestr = d00.strftime("%d %b %Y")
    yearstr = d00.strftime("%Y")

    # required few lines before end of this function...
    lat = "{:03.1f}".format(abs(lats))
    lns = 'N' if lats >= 0 else 'S'

    # A4/Letter landscape (center vertically)
    # https://tex.stackexchange.com/questions/2326/vertically-center-text-on-a-page
    
    tex = r"""
  \hspace{0pt}
  \vfill"""
    
    tex += r"""
\begin{center}                  % center picture horizontally
% ====== Local Mean Time Of Meridian Passage chart ======
\begin{tikzpicture}"""

# --------------------------------------------------------------
# draw chart vertical lines and label the horizontal axis
    tex += r"""
% draw plot inner vertical lines..."""
    d_inc = d00
    extn = 1.25     # line extension (above and below)
    x = 0
    dmax = daystoprocess
    xmax = dmax / 10.0
    ymax = hmax
    ymin = hmin
    months = ['JANUARY','FEBRUARY','MARCH','APRIL','MAY','JUNE','JULY','AUGUST','SEPTEMBER','OCTOBER','NOVEMBER','DECEMBER']

    while x <= dmax:
        dom = int(d_inc.strftime("%d"))     # day of month
        if x == dmax or dom in (1,11,21):
            # draw a vertical line
            e = extn if dom == 1 else 0
            tex += r"""
  \draw[ultra thin] ({:.3f},{:.3f}) -- ({:.3f},{:.3f});""".format(
x/10*sf,(ymin-e)*sf,x/10*sf,(ymax+e)*sf)

        moy = int(d_inc.strftime("%m"))     # month of year
        if dom == 1 and x != dmax:
            # month on lower axis
            mth = months[moy-1]
            tex += r"""
  \node[font=\{}] at ({:.3f},{:.3f}) {{\scalebox{{.9}}[1.0]{{\textbf {{{}}}}}}};""".format(
star_fs,((x/10)+1.5)*sf,(ymin-1.0)*sf,mth)
            # '10th day of month' on lower axis
            tex += r"""
  \node[font=\{}] at ({:.3f},{:.3f}) {{\scalebox{{.9}}[1.0]{{{}}}}};""".format(
star_fs,((x/10)+1.0)*sf,(ymin-0.25)*sf,"10")
            # '20th day of month' on lower axis
            tex += r"""
  \node[font=\{}] at ({:.3f},{:.3f}) {{\scalebox{{.9}}[1.0]{{{}}}}};""".format(
star_fs,((x/10)+2.0)*sf,(ymin-0.25)*sf,"20")

            # month on upper axis
            tex += r"""
  \node[font=\{}] at ({:.3f},{:.3f}) {{\scalebox{{.9}}[1.0]{{\textbf {{{}}}}}}};""".format(
star_fs,((x/10)+1.5)*sf,(ymax+0.95)*sf,mth)
            # '10th day of month' on upper axis
            tex += r"""
  \node[font=\{}] at ({:.3f},{:.3f}) {{\scalebox{{.9}}[1.0]{{{}}}}};""".format(
star_fs,((x/10)+1.0)*sf,(ymax+0.25)*sf,"10")
            # '20th day of month' on upper axis
            tex += r"""
  \node[font=\{}] at ({:.3f},{:.3f}) {{\scalebox{{.9}}[1.0]{{{}}}}};""".format(
star_fs,((x/10)+2.0)*sf,(ymax+0.25)*sf,"20")

        x += 1
        d_inc += timedelta(days=1)

# -------------------------------------------------------------------
# draw chart horizontal lines and label the vertical axis
    tex += r"""
% draw plot inner horizontal lines..."""
    y = 0
    while y <= ymax:
        # draw a horizontal line
        tex += r"""
  \draw[ultra thin] ({:.3f},{:.3f}) -- ({:.3f},{:.3f});""".format(
0,y*sf,xmax*sf,y*sf)

        # left side "h" axis value
        tex += r"""
  \node[font=\{}] at ({:.3f},{:.3f}) {{\scalebox{{.8}}[1.0]{{{:02d}}}}};""".format(
ns_fs,-sf/3.0,y*sf,abs(y))

        # right side "h" axis value
        tex += r"""
  \node[font=\{}] at ({:.3f},{:.3f}) {{\scalebox{{.8}}[1.0]{{{:02d}}}}};""".format(
ns_fs,(xmax+1/3)*sf,y*sf,abs(y))

        y += 1

    # chart top and bottom horitontal line (chart border)
        tex += r"""
  \draw[ultra thin] ({:.3f},{:.3f}) -- ({:.3f},{:.3f});""".format(
0,(ymax+extn)*sf,xmax*sf,(ymax+extn)*sf)
        tex += r"""
  \draw[ultra thin] ({:.3f},{:.3f}) -- ({:.3f},{:.3f});""".format(
0,-extn*sf,xmax*sf,-extn*sf)

# -------------------------------------------------------------------
# calculate the diagonal SHA lines

    # find the 12 dates for the diagonal SHA lines
    d_inc = d00
    seek_SHA = 240
    dSHA = [None] * 13      # last item is a dummy (ignore it)
    d_ndx = 0       # index to dSHA
    prev_sha = None
    for n in range(daystoprocess):
        #dSHA[d_ndx] = d_inc # store the current date
        sha = ariesSHA(d_inc)
        if seek_SHA == 0:
            if sha > 200:
                # fraction of day between the SHA value before and after seek_SHA
                day_frac = prev_sha / (360 + prev_sha - sha)
                #print(d_ndx,dSHA[d_ndx],prev_sha,day_frac)
                #print(d_ndx,d_inc,sha)
                if day_frac > 1.0:
                    print("Error: day_frac = ",day_frac, " on ",dSHA[d_ndx])
                if day_frac > 0.5:
                    dSHA[d_ndx] = d_inc # round up to next day (it's closer to seek_SHA)
                d_ndx += 1
                seek_SHA = 330
        else:
            if sha < seek_SHA:
                # fraction of day between the SHA value before and after seek_SHA
                day_frac = (prev_sha - seek_SHA) / (prev_sha - sha)
                #print(d_ndx,dSHA[d_ndx],prev_sha,day_frac)
                #print(d_ndx,d_inc,sha)
                if day_frac > 1.0:
                    print("Error: day_frac = ",day_frac, " on ",dSHA[d_ndx])
                if day_frac > 0.5:
                    dSHA[d_ndx] = d_inc # round up to next day (it's closer to seek_SHA)
                d_ndx += 1
                seek_SHA -= 30
        dSHA[d_ndx] = d_inc # store the previous date
        prev_sha = sha
        d_inc += timedelta(days=1)

    SHAang = math.atan(ymax/xmax)
    
# ----------------------------------------------------------------------
# draw SHA diagonals with long dashes from top border to right border...

    for i in range(12):

        x = (dSHA[i] - d00).days
        # length units for x and y must be the same ...
        y = ymax * x / daystoprocess    # 1 unit = 1 hour
        x = x / 10                      # 1 unit = 10 days
        tex += r"""
  \draw[ultra thin,color=black!25,dash pattern=on 25pt off 8pt] ({:.3f},{:.3f}) -- ({:.3f},{:.3f});""".format(
x*sf,ymax*sf,xmax*sf,y*sf)

# ------------------- B O R D E R  lines --------------------

  # # NOTE: adding -0.6pt is not necessary with "-- cycle" ...
    # tex += r"""
# % draw thick bounding box
# \begin{{scope}}[{}]
  # \draw plot coordinates {{({:.3f},{:.3f}) ({:.3f},{:.3f}) ({:.3f},{:.3f}) ({:.3f},{:.3f})}} -- cycle;
# \end{{scope}}""".format(
# bb,-sf/1.8,ymin*sf-sf/1.8,
# -sf/1.8,ymax*sf+sf/1.8,
# xmax*sf+sf/2.2,ymax*sf+sf/1.8,
# xmax*sf+sf/2.2,ymin*sf-sf/1.8)

# ------------- Text outside B O R D E R  lines -------------

    # chart title on the left side
    tex += r"""
% text outside border lines
  \node[rotate=90,font=\{}] at ({:.3f},{:.3f}) {{\textbf{{LOCAL MEAN TIME OF MERIDIAN PASSAGE}}}};""".format(
navstar_fs,-1.6*sf,12*sf)

    # chart title on the right side
    tex += r"""
  \node[rotate=270,font=\{}] at ({:.3f},{:.3f}) {{\textbf{{LOCAL MEAN TIME OF MERIDIAN PASSAGE}}}};""".format(
navstar_fs,(xmax+1.6)*sf,12*sf)

    # add the chart year  (ideally this should not shift/jog the chart itself,
    #    i.e. it's not the leftmost/rightmost or topmost item on the chart canvas)
    tex += r"""
  \node[font=\{}] at ({:.3f},{:.3f}) {{\fontfamily{{phv}}\color{{airforceBlue}}\textbf{{{}}}}};""".format(
title_fs,-0.95*sf,24.82*sf,yearstr)
    tex += r"""
  \node[font=\{}] at ({:.3f},{:.3f}) {{\fontfamily{{phv}}\color{{airforceBlue}}\textbf{{{}}}}};""".format(
title_fs,(xmax+0.95)*sf,24.82*sf,yearstr)

    # tex += r"""
# % text outside border lines
  # \node[font=\{}] at ({:.3f},{:.3f}) {{SIDEREAL HOUR ANGLE}};
  # \node[font=\{}, anchor=east] at ({:.3f},{:.3f}) {{\textcopyright\enspace 2022 Andrew Bauer}};
  # \node[font=\{}] at ({:.3f},{:.3f}) {{\textbf{{LUNAR DISTANCE (SHA {}° to {}°)\quad{}}}}};
  # \node[rotate=90,font=\{}] at ({:.3f},0.0) {{DECLINATION}};
  # \node[rotate=90,font=\{}] at ({:.3f},{:.3f}) {{South}};
  # \node[rotate=90,font=\{}] at ({:.3f},{:.3f}) {{North}};""".format(
# title_fs,(xmax/2)*sf,(ymin-0.89)*sf,
# navstar_fs,(xmax)*sf,(ymin-0.89)*sf,
# title_fs,(xmax/2)*sf,(ymax+0.84)*sf,shamin,shamax,datestr,
# title_fs,-0.9*sf,
# ns_fs,-0.9*sf,-2.67*sf,
# ns_fs,-0.9*sf,2.67*sf)

# -------------------- B O R D E R  end ---------------------

# ---- optionally plot sunrise & sunset at 51.5°N on chart ----

    # pack the latitude and twilight value (degrees below horizon) into a tuple
    params = (lats, 6.0)
    # pre-calculate sun's meridian passage
    obj = 0

    # this is more accurate than merpass00 but 3x slower...
    #sun_Y, sun_XY_txt, sun_name, sun_xidx, sunUP_XY, sunDN_XY = MerPass(obj,d00,daystoprocess,sf)
    sun_Y, sun_XY_txt, sun_name, sun_xidx, sunUP_XY, sunDN_XY = merpass00(obj,d00,daystoprocess,sf)

    if config.MULTIpr:
        # multiprocess sunrise/sunset MP times per month simultaneously
        partial_func = partial(mp_sunrise_worker, d00, sun_Y, params, ts)

        try:
            # RECOMMENDED: chunksize = 1
            listoftup = pool.map(partial_func, range(12), 1)
        except KeyboardInterrupt:
            print(msg0)
            sys.exit(0)

        # assemble the multiprocessed results into lists of data for all days in the year...
        ndx = []
        sunrise_XY_txt = []
        sunset_XY_txt = []
        sunrise_Y = []
        sunset_Y = []
        civil_AM_txt = []
        civil_PM_txt = []
        civilY_AM = []
        civilY_PM = []

        prev_ndx = None
        for item in listoftup:
            data0, data1, data2, data3, data4, data5, data6, data7, data8 = item
            curr_ndx = data0[0]
            if len(ndx) > 0:
                if curr_ndx < prev_ndx:
                    print("ERROR: multiprocessing chunks not in sequence")
                    sys.exit(0)
            prev_ndx = curr_ndx
            ndx.extend(data0)
            sunrise_XY_txt.extend(data1)
            sunset_XY_txt.extend(data2)
            sunrise_Y.extend(data3)
            sunset_Y.extend(data4)
            civil_AM_txt.extend(data5)
            civil_PM_txt.extend(data6)
            civilY_AM.extend(data7)
            civilY_PM.extend(data8)
    else:
        # calculate sunrise/sunset MP times at latitude 'lats'
        sunrise_XY_txt, sunset_XY_txt, sunrise_Y, sunset_Y, civil_AM_txt, civil_PM_txt, civilY_AM, civilY_PM = sunrise_set(d00,sun_Y,daystoprocess,params,sf)

    if config.plotSS:
        tex += r"""
%% plot sunrise at chosen latitude per day
 \draw[thick,color=gray] plot[smooth,tension=0.5] coordinates{
"""
        for i in range(len(sunrise_XY_txt)):
            tex += r"""%s """ %sunrise_XY_txt[i]
        tex += r"""};"""

        tex += r"""
%% plot sunset at chosen latitude per day
 \draw[thick,color=gray] plot[smooth,tension=0.5] coordinates{
"""
        for i in range(len(sunset_XY_txt)):
            tex += r"""%s """ %sunset_XY_txt[i]
        tex += r"""};"""

# ---- plot civil twilight AM and PM for chosen latitude on chart ----

        tex += r"""
%% plot civil twilight AM at chosen latitude per day
 \draw[thin,color=red] plot[smooth,tension=0.5] coordinates{
"""
        for i in range(len(civil_AM_txt)):
            tex += r"""%s """ %civil_AM_txt[i]
        tex += r"""};"""

        tex += r"""
%% plot civil twilight PM at chosen latitude per day
 \draw[thin,color=blue] plot[smooth,tension=0.5] coordinates{
"""
        for i in range(len(civil_PM_txt)):
            tex += r"""%s """ %civil_PM_txt[i]
        tex += r"""};"""

#           ---- Meridian Passage path of SUN and ... ----
# ---- MERCURY, VENUS, MARS, JUPITER, SATURN, URANUS, NEPTUNE ----

    # make the following global to avoid passing them often as function arguments:
    global meridian_pass, meridian_xidx, hdiags, label_pos, chosen_label, planet_app_pos

    linepattern = ['',
    'dash pattern=on 10pt off 3pt on 1pt off 3pt,',
    'dash pattern=on 10pt off 3pt on 1pt off 3pt on 1pt off 3pt,',
    'dash pattern=on 10pt off 3pt on 1pt off 3pt on 1pt off 3pt on 1pt off 3pt,',
    'dash pattern=on 8pt off 3pt,',
    'dotted,',
    'loosely dashed,',
    'loosely dotted,']
    thickness = ['thick','thick','thick','thick','thick','very thick','thin','thick']

    # store all sun/planet merpass curves (8) + sunrise/sunset at chosen latitude (2)
    meridian_pass = [[] for i in range(10)]

    # meridian_xidx = [None] * 6  # the planet merpass 00h to 24h crossover days (if any)
    meridian_xidx = [[] for i in range(8)]  # idx when mpa00 goes below 0h (per planet)

    # store all planet (Mercury, Venus, Mars, Jupiter, Saturn) apparent positions at 0h per day
    planet_app_pos = [[] for i in range(5)]

    # 'hdiags' is the offset the sun/planet name label is to be raised or
    # lowered (perpendicular to the direction of the text itself) in order
    # to be above or below the path drawn.
    # The units are '6 minutes' (1/10 hour) when measured along the vertical axis.
    hdiags = [0.95*3, 1.4*3, 1.3*3, 1.1*3, 1.2*3, 1.2*3, 1.2*3, 1.2*3]
    # note: multiply by 3 because the fundamental units in Planet Declination Paths is
    # '10 degrees / 30 days' whereas here it is '1 hour / 10 days' (factor 3 smaller).

    label_pos = []      # store label position candidates per object
    chosen_label = []   # list of tuples (obj, index to label_pos)

    for obj in [0, 1, 2, 3, 4, 5, 6, 7]:
        
        linetype = linepattern[obj]
        linewdth = thickness[obj]
        if obj == 0:
            #object_Y, object_XY_txt, object_name, object_xidx, sunUP_XY, sunDN_XY = merpass00(obj,d00,daystoprocess,sf)
            object_Y = sun_Y
            object_XY_txt = sun_XY_txt
            object_name = sun_name
            object_xidx = sun_xidx
        else:
            # this is more accurate than merpass00 but 3x slower...
            #object_Y, object_XY_txt, object_name, object_xidx, mp_offset, apppos = MerPass(obj,d00,daystoprocess,sf,True)
            object_Y, object_XY_txt, object_name, object_xidx, mp_offset, apppos = merpass00(obj,d00,daystoprocess,sf)
            if obj <= 5:    # Mercury, Venus, Mars, Jupiter, Saturn
                planet_app_pos[obj-1] = apppos  # save for further analysis
        meridian_pass[obj] = object_Y       # save for further analysis
        meridian_xidx[obj] = object_xidx    # save for further analysis

        if not config.plotUN and obj > 5: continue    # calculate but don't plot uranus & neptune
        for n in range(3):      # 3 segments maximum (assumed here)
            if len(object_XY_txt[n]) > 0:
                tex += r"""
%% plot %s Meridian Passage per day
 \draw[%s,%scolor=Black] plot[smooth,tension=0.5] coordinates{
""" %(object_name,linewdth,linetype)
                for i in range(len(object_XY_txt[n])):
                    tex += r"""%s """ %object_XY_txt[n][i]
                    if (i+1) % 5 == 0: tex += "\n"
                tex += r"""};"""

    meridian_pass[8] = sunrise_Y        # save for further analysis
    meridian_pass[9] = sunset_Y         # save for further analysis
    
# ------- Civil Dawn(AM)/Dusk(PM) intersections with Meridian Passage of a planet -------

    obj = 1         # MERCURY
    global mercuryAM, mercuryPM, mercuryVIS
    mercuryAM, mercuryPM, mercuryVIS = twilight_intersections(obj, civilY_AM, civilY_PM)

    obj = 2         # VENUS
    global venusAM, venusPM, venusVIS
    venusAM, venusPM, venusVIS = twilight_intersections(obj, civilY_AM, civilY_PM)

    obj = 3         # MARS with 0.35h less twilight as it is a faint object
    global marsAM, marsPM, marsVIS
    marsAM, marsPM, marsVIS = twilight_intersections(obj, civilY_AM, civilY_PM, 0.35)

    obj = 4         # JUPITER
    global jupiterAM, jupiterPM, jupiterVIS
    jupiterAM, jupiterPM, jupiterVIS = twilight_intersections(obj, civilY_AM, civilY_PM)

    obj = 5         # SATURN with 0.3h less twilight as it is a faint object
    global saturnAM, saturnPM, saturnVIS
    saturnAM, saturnPM, saturnVIS = twilight_intersections(obj, civilY_AM, civilY_PM, 0.3)

    obj = 6         # URANUS with 0.6h less twilight as it is a faint object
    global uranusAM, uranusPM, uranusVIS
    uranusAM, uranusPM, uranusVIS = twilight_intersections(obj, civilY_AM, civilY_PM, 0.6)

    obj = 7         # NEPTUNE with 0.6h less twilight as it is a faint object
    global neptuneAM, neptunePM, neptuneVIS
    neptuneAM, neptunePM, neptuneVIS = twilight_intersections(obj, civilY_AM, civilY_PM, 0.6)

# ---- get sunrise/sunset at chosen latitude path intersections with superior planets ----

    if config.plotSS:
        sunAM, sunPM = sunriseset_intersections(sunrise_Y, sunset_Y)

# ----------------------------------------------------------------------
# label the diagonal SHA lines with the SHA values in degrees
#    (do this after plotting Meridian Passage per planet as it
#     looks neater when lines do not overwrite these labels)

    this_SHA = 240
    digit_placeholder = r"\phantom{0}"
    tex += r"""
% label the diagonal SHA lines"""

    for i in range(12):

    # NOTE: using 'tcolorbox' to create the SHA labels on UPPER/RIGHT/LOWER/LEFT
    #       borders causes "Overfull \hbox (1.20001pt too wide)" warnings.
    # FIX:  incorporate '\addtolength{\myl}{1.2pt}'
    #       The result is graphically identical :-)

        ang = SHAang
        x = (dSHA[i] - d00).days
        # length units for x and y must be the same ...
        y = ymax * x / daystoprocess    # 1 unit = 1 hour
        x = x / 10                      # 1 unit = 10 days

    # ------ add SHA labels to UPPER border ------
        # label position is most accurately specified as ...
        ldiag = 0.7     # length along diagonal (before scaling)
        hdiag = 0.33    # height perpendiculat to diagonal (before scaling)
        xoffset = ldiag*math.cos(ang) + hdiag*math.sin(ang)
        yoffset = hdiag*math.cos(ang) - ldiag*math.tan(ang)

        if i < 11:      # exclude 270° on upper border
            txt = "%d°" %this_SHA
            rot = "%0.3f" %(-ang*todegrees)
            x0 = (xoffset + x)*sf
            y0 = (yoffset + ymax)*sf

            # opacityframe=1.0 shows a thin frame; =0.0 is invisible
            # boxsep > 0.0 adds padding around the text but causes "Overfull \hbox"
            tex += r"""
  \settowidth{\myl}{\pgfinterruptpicture\%s{%s}\endpgfinterruptpicture}
  \addtolength{\myl}{1.2pt}
  \draw[color=Black,anchor=west] (%0.3f,%0.3f) node[rotate=%s,font=\%s]
  {\begin{tcolorbox}[standard jigsaw, size=minimal, colupper=black, colback=white, opacityfill=1.0, opacityframe=0.0, width=\myl, boxsep=0.6pt]{\%s{%s}}\end{tcolorbox}};""" %(star_fs, txt, x0, y0, rot, star_fs, star_fs, txt)

            # tex += r"""
  # \draw[color=Black,anchor=west,fill=white] (%0.3f,%0.3f) node[rotate=%s,font=\%s] {\scalebox{1.0}[1.0]{%s}};""" %(x0, y0, rot, star_fs, txt)

    # ------ add SHA labels on RIGHT border ------
            # label position is most accurately specified as ...
            ldiag = -1.3    # length along diagonal (before scaling)
            hdiag = 0.16    # height perpendiculat to diagonal (before scaling)
            xoffset = ldiag*math.cos(ang) + hdiag*math.sin(ang)
            yoffset = hdiag*math.cos(ang) - ldiag*math.tan(ang)

            txt = ""
            if this_SHA < 100: txt = digit_placeholder
            if this_SHA < 10:  txt += digit_placeholder
            txt += "%d°" %this_SHA
            rot = "%0.3f" %(-ang*todegrees)
            x0 = (xoffset + xmax)*sf
            y0 = (yoffset + y)*sf

            # opacityframe=1.0 shows a thin frame; =0.0 is invisible
            # boxsep > 0.0 adds padding around the text but causes "Overfull \hbox"
            tex += r"""
  \settowidth{\myl}{\pgfinterruptpicture\%s{%s}\endpgfinterruptpicture}
  \addtolength{\myl}{1.2pt}
  \draw[color=Black,anchor=west] (%0.3f,%0.3f) node[rotate=%s,font=\%s]
  {\begin{tcolorbox}[standard jigsaw, size=minimal, colupper=black, colback=white, opacityfill=1.0, opacityframe=0.0, width=\myl, boxsep=0.6pt]{\%s{%s}}\end{tcolorbox}};""" %(star_fs, txt, x0, y0, rot, star_fs, star_fs, txt)

        # ----------------------------------------------------------------------
        # draw diagonals from left border to bottom border...
        x = (dSHA[i] - d00).days / 10
        y = ymax * x * 10 / daystoprocess
        tex += r"""
  \draw[ultra thin,color=black!25,dash pattern=on 25pt off 8pt] ({:.3f},{:.3f}) -- ({:.3f},{:.3f});""".format(
0,y*sf,x*sf,ymin*sf)

    # ------ add SHA labels to LOWER border ------
        # label position is most accurately specified as ...
        ldiag = -0.8    # length along diagonal (before scaling)
        hdiag = 0.19    # height perpendiculat to diagonal (before scaling)
        xoffset = ldiag*math.cos(ang) + hdiag*math.sin(ang)
        yoffset = hdiag*math.cos(ang) - ldiag*math.tan(ang)

        if i > 0:      # exclude 240° on lower border
            txt = ""
            if this_SHA < 100: txt = digit_placeholder
            if this_SHA < 10:  txt += digit_placeholder
            txt += "%d°" %this_SHA
            rot = "%0.3f" %(-ang*todegrees)
            x0 = (xoffset + x)*sf
            y0 = yoffset*sf

            # opacityframe=1.0 shows a thin frame; =0.0 is invisible
            # boxsep > 0.0 adds padding around the text but causes "Overfull \hbox"
            tex += r"""
  \settowidth{\myl}{\pgfinterruptpicture\%s{%s}\endpgfinterruptpicture}
  \addtolength{\myl}{1.2pt}
  \draw[color=Black,anchor=west] (%0.3f,%0.3f) node[rotate=%s,font=\%s]
  {\begin{tcolorbox}[standard jigsaw, size=minimal, colupper=black, colback=white, opacityfill=1.0, opacityframe=0.0, width=\myl, boxsep=0.6pt]{\%s{%s}}\end{tcolorbox}};""" %(star_fs, txt, x0, y0, rot, star_fs, star_fs, txt)

    # ------ add SHA labels to LEFT border ------
        # label position is most accurately specified as ...
        ldiag = -0.2    # length along diagonal (before scaling)
        hdiag = 0.25    # height perpendiculat to diagonal (before scaling)
        xoffset = ldiag*math.cos(ang) + hdiag*math.sin(ang)
        yoffset = hdiag*math.cos(ang) - ldiag*math.tan(ang)

        txt = "%d°" %this_SHA
        rot = "%0.3f" %(-ang*todegrees)
        x0 = xoffset*sf
        y0 = (yoffset + y)*sf

        # opacityframe=1.0 shows a thin frame; =0.0 is invisible
        # boxsep > 0.0 adds padding around the text but causes "Overfull \hbox"
        tex += r"""
  \settowidth{\myl}{\pgfinterruptpicture\%s{%s}\endpgfinterruptpicture}
  \addtolength{\myl}{1.2pt}
  \draw[color=Black,anchor=west] (%0.3f,%0.3f) node[rotate=%s,font=\%s]
  {\begin{tcolorbox}[standard jigsaw, size=minimal, colupper=black, colback=white, opacityfill=1.0, opacityframe=0.0, width=\myl, boxsep=0.6pt]{\%s{%s}}\end{tcolorbox}};""" %(star_fs, txt, x0, y0, rot, star_fs, star_fs, txt)


        this_SHA -= 30
        if this_SHA < 0: this_SHA += 360

# ------------ Meridian Passage of SUN +45m and -45m ------------

    # shade the area sun+45m to sun-45m
    tex += r"""
% shade sun+45m to sun-45m Meridian Passage per day
 \fill[color=red, opacity=0.2]
"""
    for i in range(len(sunUP_XY)):
        tex += r"""%s -- """ %sunUP_XY[i]
        if (i+1) % 5 == 0: tex += "\n"
    #tex += r"""%s } -- plot[smooth,tension=0.5] coordinates{""" %sunDN_XY[-1]
    for i in range(len(sunDN_XY)):
        tex += r"""%s -- """ %sunDN_XY[-i-1]
        if (i+1) % 5 == 0: tex += "\n"
    #tex += r"""%s };""" %sunUP_XY[0]
    tex += r"""cycle;"""

    # NOTE: shading sun+45m to sun-45m *after* labelling the diagonal SHA lines
    #       also shades the SHA label's white background near 12h. Looks better.

# ---------------------------------------------------------------
    # determine where the 6 Meridian Passage paths cross each other
    # (to avoid placing name labels there)
    tup_crosspoints = merpass_intersections()

    global txt_wdth, txt_hgt
    # Helvetica 10pt text width of planet name in Pt:
    txt_wdth = [22.70987, 51.64967, 36.04971, 31.03983, 43.8296, 42.3599, 44.36978, 49.37967, 84.00613, 80.6663]
    # Helvetica 10pt text height of planet name in Pt:
    txt_hgt = 7.40997

    global pt2cm, boxsep
    pt2cm = 1/28.45274  # 1cm = 28.45274 Pt
    boxsep = 0.8        # Pt

    label = ['True' for i in range(6)]
    pab = ['above', 'below']    # label position (above/below the declination path)
    vab = [1.0, -1.0]           # label position hdiag multiplier for above/below

# !=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=
# !=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=

# ...................................................................
#      try some label positions avoiding a path overlap: SUN
# ...................................................................

    # -------------------------------------------------------------------
    # |  x-, y-position coordinates are in units of '1 hour' vertically |
    # |  or '10 calendar days' horizontally, i.e. 1 unit corresponds    |
    # |  to the chart horizontal separation lines and close to the      |
    # |  chart vertical lines (as not every month has 30 days).         |
    # -------------------------------------------------------------------

    obj = 0         # SUN
    few_tuples = []         # store tuple data to be appended to label_pos
    tuple_ndx = -1          # index to few_tuples
    good_positions = []     # store candidates to be appended to label_pos
    idx_mid = []            # idx mid-position values per path segment
    p_segments, p_sections = path_sections(obj, tup_crosspoints, True)
    # p_segments sorted by segment ASC
    # p_sections sorted by segment ASC, length DESC, from date ASC

    # for sec_len, from_idx, to_idx, o_fr, o_to in p_sections[0]:
        # date0 = d00 + timedelta(days=from_idx)
        # date1 = d00 + timedelta(days=to_idx)
        # path_seg = 0
        # print("{} segment {} section length {:5.2f}   {} - {}   {}-{}".format(get_object_name(obj).upper(), path_seg, sec_len, date0, date1, get_object_name(o_fr), get_object_name(o_to)))

    # strategy: try mid-position of 3 longest path sections
    #      with greatest separation to other paths

    for i in range(0,min(3,len(p_sections[0]))):
        sec_len, from_idx, to_idx, o_fr, o_to = p_sections[0][i]
        idx_len = to_idx - from_idx
        # print("Sun",d00 + timedelta(days=from_idx + int(idx_len/2)))
        idx_mid.append(from_idx + int(idx_len/2))

    hdiag = hdiags[obj]     # height (in 1/10 hour) perpendiculat to label text

    for idx in idx_mid:
        abcount = 0             # count successful above/below positions (per segment)

        for ab in [0,1]:        # label above and below path...
            xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang = label_rectangle(obj, idx, hdiag*vab[ab])
            #print(xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang)
            date_min = d00 + timedelta(days=idx_min)
            date_max = d00 + timedelta(days=idx_max)
            date0 = d00 + timedelta(days=idx)
            #tex += plot_rectangle(xy)
            #tex += plot_rectangle(rxy)
            #tex += printdot(100, 5.0)           # test: 100 days, 5 hours
            #tex += printdot2(10*sf, 5.0*sf)     # test: 100 days, 5 hours

            # check if the label overwrites neighboring declination paths
            badobj = path_overlaid_check(obj, xy, idx_min, idx_max, dec_min, dec_max, lab0, ang)
            if len(badobj) > 0:
                if config.debug_chosen:
                    msg = ""
                    for obj0 in badobj:
                        if obj0 == -1:
                            msg += "label off-chart!, "
                        else:
                            msg += "{}, ".format(get_object_name(obj0).upper())
                    print("      {:7} (label {}) on {} overlays path: {}".format(get_object_name(obj).upper(), pab[ab], date0, msg[:-2]))
            else:
                abcount += 1
                abgood = ab
                tuple_ndx += 1
                few_tuples.append((obj, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang, ab))

        # look for greatest vertical separation from other planets/sun
        abdiff_min = [24.0] * 2                 # abdiff_min[0 to 1]
        abdiff = [[24.0] * 6 for i in range(2)] # abdiff[0 to 1][0 to 5]
        mpa1 = meridian_pass[obj][idx]
        for k in range(6):
            if k == obj: continue
            mpa2 = meridian_pass[k][idx]
            j = 0 if mpa2 > mpa1 else 1     # 0 if above obj; 1 if below
            abdiff[j][k] = abs(mpa2 - mpa1)
        abdiff_min[0] = min(abdiff[0])  # minimum dec separation above
        abdiff_min[1] = min(abdiff[1])  # minimum dec separation below

        if abcount == 2:    # then save both (above & below) in label_pos
            # 1st pick: highest minimum distance to nearest path (above or below obj)
            ab = 0 if abdiff_min[0] > abdiff_min[1] else 1
            abdiff_max = max(abdiff_min[0], abdiff_min[1])  # max separation above/below
            good_positions.append((abdiff_max, tuple_ndx+ab-1))
            write_label_candidate(obj, idx, ang, ab)
        elif abcount == 1:  # then save the position (above or below) that worked
            abdiff_max = abdiff_min[abgood]     # max separation (above or below)
            good_positions.append((abdiff_max, tuple_ndx))
            write_label_candidate(obj, idx, ang, abgood)

    # sort 'good_positions' by separation (high to low)
    good_positions.sort(key = lambda x: x[0], reverse = True)
    for abdiff_max, tuple_ndx in good_positions:
        # first candidate has highest preference
        label_pos.append(few_tuples[tuple_ndx])

# ...................................................................
#      try some label positions avoiding a path overlap: MERCURY
# ...................................................................

    # -------------------------------------------------------------------
    # |  x-, y-position coordinates are in units of '1 hour' vertically |
    # |  or '10 calendar days' horizontally, i.e. 1 unit corresponds    |
    # |  to the chart horizontal separation lines and close to the      |
    # |  chart vertical lines (as not every month has 30 days).         |
    # -------------------------------------------------------------------

    obj = 1         # MERCURY
    few_tuples = []         # store tuple data to be appended to label_pos
    tuple_ndx = -1          # index to few_tuples
    good_positions = []     # store candidates to be appended to label_pos
    idx_mid = []            # idx mid-position values per path segment
    p_segments, p_sections = path_sections(obj, tup_crosspoints, True)
    # p_segments sorted by segment ASC
    # p_sections sorted by segment ASC, length DESC, from date ASC

    # for sec_len, from_idx, to_idx, o_fr, o_to in p_sections[0]:
        # date0 = d00 + timedelta(days=from_idx)
        # date1 = d00 + timedelta(days=to_idx)
        # path_seg = 0
        # print("{} segment {} section length {:5.2f}   {} - {}   {}-{}".format(get_object_name(obj).upper(), path_seg, sec_len, date0, date1, get_object_name(o_fr), get_object_name(o_to)))

    # strategy: try mid-position of 3 longest path sections
    #      with greatest separation to other paths

    for i in range(0,min(3,len(p_sections[0]))):
        sec_len, from_idx, to_idx, o_fr, o_to = p_sections[0][i]
        idx_len = to_idx - from_idx
        # print("Sun",d00 + timedelta(days=from_idx + int(idx_len/2)))
        idx_mid.append(from_idx + int(idx_len/2))

    hdiag = hdiags[obj]     # height (in 1/10 hour) perpendiculat to label text

    for idx in idx_mid:
        abcount = 0             # count successful above/below positions (per segment)

        for ab in [0,1]:        # label above and below path...
            xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang = label_rectangle(obj, idx, hdiag*vab[ab])
            #print(xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang)
            date_min = d00 + timedelta(days=idx_min)
            date_max = d00 + timedelta(days=idx_max)
            date0 = d00 + timedelta(days=idx)
            #tex += plot_rectangle(xy)
            #tex += plot_rectangle(rxy)
            #tex += printdot(100, 5.0)           # test: 100 days, 5 hours
            #tex += printdot2(10*sf, 5.0*sf)     # test: 100 days, 5 hours

            # check if the label overwrites neighboring declination paths
            badobj = path_overlaid_check(obj, xy, idx_min, idx_max, dec_min, dec_max, lab0, ang)
            if len(badobj) > 0:
                if config.debug_chosen:
                    msg = ""
                    for obj0 in badobj:
                        if obj0 == -1:
                            msg += "label off-chart!, "
                        else:
                            msg += "{}, ".format(get_object_name(obj0).upper())
                    print("      {:7} (label {}) on {} overlays path: {}".format(get_object_name(obj).upper(), pab[ab], date0, msg[:-2]))
            else:
                abcount += 1
                abgood = ab
                tuple_ndx += 1
                few_tuples.append((obj, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang, ab))

        # look for greatest vertical separation from other planets/sun
        abdiff_min = [24.0] * 2                 # abdiff_min[0 to 1]
        abdiff = [[24.0] * 6 for i in range(2)] # abdiff[0 to 1][0 to 5]
        mpa1 = meridian_pass[obj][idx]
        for k in range(6):
            if k == obj: continue
            mpa2 = meridian_pass[k][idx]
            j = 0 if mpa2 > mpa1 else 1     # 0 if above obj; 1 if below
            abdiff[j][k] = abs(mpa2 - mpa1)
        abdiff_min[0] = min(abdiff[0])  # minimum dec separation above
        abdiff_min[1] = min(abdiff[1])  # minimum dec separation below

        if abcount == 2:    # then save both (above & below) in label_pos
            # 1st pick: highest minimum distance to nearest path (above or below obj)
            ab = 0 if abdiff_min[0] > abdiff_min[1] else 1
            abdiff_max = max(abdiff_min[0], abdiff_min[1])  # max separation above/below
            good_positions.append((abdiff_max, tuple_ndx+ab-1))
            write_label_candidate(obj, idx, ang, ab)
        elif abcount == 1:  # then save the position (above or below) that worked
            abdiff_max = abdiff_min[abgood]     # max separation (above or below)
            good_positions.append((abdiff_max, tuple_ndx))
            write_label_candidate(obj, idx, ang, abgood)

    # sort 'good_positions' by separation (high to low)
    good_positions.sort(key = lambda x: x[0], reverse = True)
    for abdiff_max, tuple_ndx in good_positions:
        # first candidate has highest preference
        label_pos.append(few_tuples[tuple_ndx])

# ...................................................................
#      try some label positions avoiding a path overlap: VENUS
# ...................................................................

    # -------------------------------------------------------------------
    # |  x-, y-position coordinates are in units of '1 hour' vertically |
    # |  or '10 calendar days' horizontally, i.e. 1 unit corresponds    |
    # |  to the chart horizontal separation lines and close to the      |
    # |  chart vertical lines (as not every month has 30 days).         |
    # -------------------------------------------------------------------

    obj = 2         # VENUS
    two_tuples = [None, None]   # store tuple to be appended to label_pos
    idx_mid = []                # idx mid-position values per path segment
    p_segments, p_sections = path_sections(obj, tup_crosspoints, True)
    # p_segments sorted by segment ASC
    # p_sections sorted by segment ASC, length DESC, from date ASC

    for seg_len, seg_mid_idx, seg_mid_mpa, sect_count in p_segments:
        date0 = d00 + timedelta(days=seg_mid_idx)
        if config.debug_chosen:
            print("      {} segment with {} sections, length {:5.2f}   mid {} {:5.2f}".format(get_object_name(obj).upper(), sect_count, seg_len, date0, seg_mid_mpa))

    for path_seg in range(len(p_sections)):
        for sec_len, from_idx, to_idx, obj8, obj9 in p_sections[path_seg]:
            date0 = d00 + timedelta(days=from_idx)
            date1 = d00 + timedelta(days=to_idx)
            if config.debug_chosen:
                print("      {} segment {} section length {:5.2f}   {} - {}   {}-{}".format(get_object_name(obj).upper(), path_seg, sec_len, date0, date1, get_object_name(obj8), get_object_name(obj9)))

    planet_Y = meridian_pass[obj]
    planet_xidx = meridian_xidx[obj]

    for index, item in enumerate(p_segments):   # per path segment
        seg_len, seg_mid_idx, seg_mid_mpa, sect_count = item
        # 1) try mid-position of each segment
        if seg_len > 6:
            idx_mid.append((index, seg_mid_idx))  # tuple: segment# + mid-date offset
    
        # 2) try mid-position of longest section of each segment
        #             (this may cause duplicates)
        for i in range(sect_count):
            sec_len, from_idx, to_idx, obj8, obj9 = p_sections[index][i]  # pick longest
            mid_idx = from_idx + int((to_idx - from_idx)/2)
            if sec_len > 5.0:   # skip if section is too short
                idx_mid.append((index, mid_idx))    # append tuple
            break

    idx_mid = list(set(idx_mid))    # remove duplicate tuples in list

    # # strategy: try mid-position of first path section that's longer than 30 days
    # n = 0
    # idx_fr = -1     # invalid value
    # while n < len(p_sections):
        # path_seg, sec_len, from_idx, to_idx, o_fr, o_to = p_sections[n]
        # if sec_len > 3:     # if > 30 days
            # idx_len = to_idx - from_idx
            # idx = from_idx + int(idx_len/2)
            # idx_mid.append(idx)
            # idx_fr = idx
            # #print("found first: ",d00 + timedelta(days=idx))
            # break
        # n += 1

    # # strategy: try mid-position of last path section that's longer than 30 days
    # n = -1
    # while -n <= len(p_sections):
        # path_seg, sec_len, from_idx, to_idx, o_fr, o_to = p_sections[n]
        # if sec_len > 3:     # if > 30 days
            # idx_len = to_idx - from_idx
            # idx = from_idx + int(idx_len/2)
            # if idx != idx_fr:   # ignore if duplicate
                # idx_mid.append(idx)
                # #print("found  last: ",d00 + timedelta(days=idx))
            # break
        # n -= 1

    hdiag = hdiags[obj]     # height (in 1/10 hour) perpendiculat to label text
    seg_chosen = []         # segments with a label position

    for segnum, idx in idx_mid:
        if segnum in seg_chosen: continue   # one label per segment is sufficient
        abcount = 0             # count successful above/below positions (per segment)

        for ab in [0,1]:        # label above and below path...
            xy, rxy, idx_min, idx_max, ry_min, ry_max, lab0, ang = label_rectangle(obj, idx, hdiag*vab[ab])
            date_min = d00 + timedelta(days=idx_min)
            date_max = d00 + timedelta(days=idx_max)
            date0 = d00 + timedelta(days=idx)

            # check if the label overwrites neighboring declination paths
            badobj = path_overlaid_check(obj, xy, idx_min, idx_max, ry_min, ry_max, lab0, ang)
            if len(badobj) > 0:
                if config.debug_chosen:
                    msg = ""
                    for obj0 in badobj:
                        if obj0 == -1:
                            msg += "label off-chart!, "
                        else:
                            msg += "{}, ".format(get_object_name(obj0).upper())
                    print("      {:7} (label {}) on {} overlays path: {}".format(get_object_name(obj).upper(), pab[ab], date0, msg[:-2]))
            else:
                seg_chosen.append(segnum)
                abcount += 1
                abgood = ab
                two_tuples[ab] = (obj, idx, xy, rxy, idx_min, idx_max, ry_min, ry_max, lab0, ang, ab)

        if abcount == 2:    # then save both (above & below) in label_pos
            # look for greatest vertical separation from other planets/sun
            abdiff_min = [24.0] * 2            # abdiff_min[0 to 1]
            abdiff = [[24.0] * 6 for i in range(2)]    # abdiff[0 to 1][0 to 5]
            mpa1 = meridian_pass[obj][idx]
            for k in range(6):
                if k == obj: continue
                mpa2 = meridian_pass[k][idx]
                j = 0 if mpa2 > mpa1 else 1     # 0 if above obj; 1 if below
                abdiff[j][k] = abs(mpa2 - mpa1)
            abdiff_min[0] = min(abdiff[0])  # minimum dec separation above
            abdiff_min[1] = min(abdiff[1])  # minimum dec separation below
            # the first choice is the preferred position...
            # 1st pick: highest minimum distance to nearest path (above or below obj)
            ab = 0 if abdiff_min[0] > abdiff_min[1] else 1
            # check if label too near the sun
            okay = True
            if ab == 0 and 10.2 < mpa1 < 12.8: okay = False
            if ab == 1 and 11.2 < mpa1 < 13.8: okay = False
            if okay:
                write_label_candidate(obj, idx, ang, ab)
                label_pos.append(two_tuples[ab])
            # 2nd pick: the opposite side (above or below obj)
            ab = 1 - ab
            # check if label too near the sun
            if ab == 0 and 10.2 < mpa1 < 12.8: continue
            if ab == 1 and 11.2 < mpa1 < 13.8: continue
            write_label_candidate(obj, idx, ang, ab)
            label_pos.append(two_tuples[ab])
        elif abcount == 1:  # then save the position (above or below) that worked
            # check if label too near the sun
            mpa1 = meridian_pass[obj][idx]
            if abgood == 0 and 10.2 < mpa1 < 12.8: continue
            if abgood == 1 and 11.2 < mpa1 < 13.8: continue
            write_label_candidate(obj, idx, ang, abgood)
            label_pos.append(two_tuples[abgood])

# ...................................................................
#      try some label positions avoiding a path overlap: MARS
# ...................................................................

    # -------------------------------------------------------------------
    # |  x-, y-position coordinates are in units of '1 hour' vertically |
    # |  or '10 calendar days' horizontally, i.e. 1 unit corresponds    |
    # |  to the chart horizontal separation lines and close to the      |
    # |  chart vertical lines (as not every month has 30 days).         |
    # -------------------------------------------------------------------

    obj = 3         # MARS
    two_tuples = [None, None]   # store tuple to be appended to label_pos
    idx_mid = []                # idx mid-position values per path segment
    # lcount = 0                  # count label position candidates
    p_segments, p_sections = path_sections(obj, tup_crosspoints, True)
    # p_segments sorted by segment ASC
    # p_sections sorted by segment ASC, length DESC, from date ASC

    for seg_len, seg_mid_idx, seg_mid_mpa, sect_count in p_segments:
        date0 = d00 + timedelta(days=seg_mid_idx)
        if config.debug_chosen:
            print("      {} segment with {} sections, length {:5.2f}   mid {} {:5.2f}".format(get_object_name(obj).upper(), sect_count, seg_len, date0, seg_mid_mpa))

    for path_seg in range(len(p_sections)):
        for sec_len, from_idx, to_idx, obj8, obj9 in p_sections[path_seg]:
            date0 = d00 + timedelta(days=from_idx)
            date1 = d00 + timedelta(days=to_idx)
            if config.debug_chosen:
                print("      {} segment {} section length {:5.2f}   {} - {}   {}-{}".format(get_object_name(obj).upper(), path_seg, sec_len, date0, date1, get_object_name(obj8), get_object_name(obj9)))

    planet_Y = meridian_pass[obj]
    planet_xidx = meridian_xidx[obj]

    for index, item in enumerate(p_segments):   # per path segment
        seg_len, seg_mid_idx, seg_mid_mpa, sect_count = item
        # 1) try mid-position of each segment
        if seg_len > 6:
            idx_mid.append((index, seg_mid_idx))  # tuple: segment# + mid-date offset
    
        # 2) try mid-position of 2 longest sections of each segment
        #             (this may cause duplicates)
        n = 0
        for i in range(sect_count):
            sec_len, from_idx, to_idx, obj8, obj9 = p_sections[index][i]  # pick 2 longest
            mid_idx = from_idx + int((to_idx - from_idx)/2)
            if sec_len > 4.5: # skip if section is too short
                idx_mid.append((index, mid_idx))    # append tuple
                n += 1
            if n >= 2: break

    idx_mid = list(set(idx_mid))    # remove duplicate tuples in list

    # for segnum, idx in idx_mid:
        # date0 = d00 + timedelta(days=idx)
        # print("{} seg {}: pick {}".format(get_object_name(obj).upper(),segnum,date0))

    # for sec_len, from_idx, to_idx, obj8, obj9 in p_sections[0]:
        # date0 = d00 + timedelta(days=from_idx)
        # date1 = d00 + timedelta(days=to_idx)
        # path_seg = 0
        # print("{} segment {} section length {:5.2f}   {} - {}   {}-{}".format(get_object_name(obj).upper(), path_seg, sec_len, date0, date1, get_object_name(obj8), get_object_name(obj9)))

    # # strategy: try mid-position of longest path sections (2 max)
    # #       if either begin on Jan 1 or end on Dec 31
    # #       or begin/end on upper/lower chart border
    # for i in range(len(p_sections[0])):
        # from_list = [0] + meridian_xidx[obj]
        # to_list = meridian_xidx[obj] + [daystoprocess-1]
        # sec_len, from_idx, to_idx, obj8, obj9 = p_sections[0][-i]  # pick longest
        # if from_idx in from_list or to_idx in to_list:
            # idx_len = to_idx - from_idx
            # if sec_len > 6: # skip if section is too short
                # idx_mid.append(from_idx + int(idx_len/2))
                # lcount += 1     # count label position candidates
                # if lcount >= 2: break

    hdiag = hdiags[obj]     # height (in 1/10 hour) perpendiculat to label text
    seg_chosen = []         # segments with a label position

    for segnum, idx in idx_mid:
        # if segnum in seg_chosen: continue   # one label per segment is sufficient
        abcount = 0             # count successful above/below positions (per segment)

        for ab in [0,1]:        # label above and below path...
            xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang = label_rectangle(obj, idx, hdiag*vab[ab])
            #print(xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang)
            date_min = d00 + timedelta(days=idx_min)
            date_max = d00 + timedelta(days=idx_max)
            date0 = d00 + timedelta(days=idx)
            #tex += plot_rectangle(xy)
            #tex += plot_rectangle(rxy)
            #tex += printdot(100, 5.0)           # test: 100 days, 5 hours
            #tex += printdot2(10*sf, 5.0*sf)     # test: 100 days, 5 hours

            # check if the label overwrites neighboring declination paths
            badobj = path_overlaid_check(obj, xy, idx_min, idx_max, dec_min, dec_max, lab0, ang)
            if len(badobj) > 0:
                if config.debug_chosen:
                    msg = ""
                    for obj0 in badobj:
                        if obj0 == -1:
                            msg += "label off-chart!, "
                        else:
                            msg += "{}, ".format(get_object_name(obj0).upper())
                    print("      {:7} (label {}) on {} overlays path: {}".format(get_object_name(obj).upper(), pab[ab], date0, msg[:-2]))
            else:
                seg_chosen.append(segnum)
                abcount += 1
                abgood = ab
                two_tuples[ab] = (obj, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang, ab)

        if abcount == 2:    # then save both (above & below) in label_pos
            # look for greatest vertical separation from other planets/sun
            abdiff_min = [24.0] * 2                 # abdiff_min[0 to 1]
            abdiff = [[24.0] * 6 for i in range(2)] # abdiff[0 to 1][0 to 5]
            mpa1 = meridian_pass[obj][idx]
            for k in range(6):
                if k == obj: continue
                mpa2 = meridian_pass[k][idx]
                j = 0 if mpa2 > mpa1 else 1     # 0 if above obj; 1 if below
                abdiff[j][k] = abs(mpa2 - mpa1)
            abdiff_min[0] = min(abdiff[0])  # minimum dec separation above
            abdiff_min[1] = min(abdiff[1])  # minimum dec separation below
            # the first choice is the preferred position...
            # 1st pick: highest minimum distance to nearest path (above or below obj)
            ab = 0 if abdiff_min[0] > abdiff_min[1] else 1
            # check if label too near the sun
            okay = True
            if ab == 0 and 10.2 < mpa1 < 12.8: okay = False
            if ab == 1 and 11.2 < mpa1 < 13.8: okay = False
            if okay:
                write_label_candidate(obj, idx, ang, ab)
                label_pos.append(two_tuples[ab])
            # 2nd pick: the opposite side (above or below obj)
            ab = 1 - ab
            # check if label too near the sun
            if ab == 0 and 10.2 < mpa1 < 12.8: continue
            if ab == 1 and 11.2 < mpa1 < 13.8: continue
            write_label_candidate(obj, idx, ang, ab)
            label_pos.append(two_tuples[ab])
        elif abcount == 1:  # then save the position (above or below) that worked
            # check if label too near the sun
            mpa1 = meridian_pass[obj][idx]
            if abgood == 0 and 10.2 < mpa1 < 12.8: continue
            if abgood == 1 and 11.2 < mpa1 < 13.8: continue
            write_label_candidate(obj, idx, ang, abgood)
            label_pos.append(two_tuples[abgood])

# ...................................................................
#      try some label positions avoiding a path overlap: JUPITER
# ...................................................................

    # -------------------------------------------------------------------
    # |  x-, y-position coordinates are in units of '1 hour' vertically |
    # |  or '10 calendar days' horizontally, i.e. 1 unit corresponds    |
    # |  to the chart horizontal separation lines and close to the      |
    # |  chart vertical lines (as not every month has 30 days).         |
    # -------------------------------------------------------------------

    obj = 4         # JUPITER
    two_tuples = [None, None]   # store tuple to be appended to label_pos
    idx_mid = []                # idx mid-position values per path segment
    p_segments, p_sections = path_sections(obj, tup_crosspoints, True)
    # p_segments sorted by segment ASC
    # p_sections sorted by segment ASC, length DESC, from date ASC

    for seg_len, seg_mid_idx, seg_mid_mpa, sect_count in p_segments:
        date0 = d00 + timedelta(days=seg_mid_idx)
        if config.debug_chosen:
            print("      {} segment with {} sections, length {:5.2f}   mid {} {:5.2f}".format(get_object_name(obj).upper(), sect_count, seg_len, date0, seg_mid_mpa))

    for path_seg in range(len(p_sections)):
        for sec_len, from_idx, to_idx, obj8, obj9 in p_sections[path_seg]:
            date0 = d00 + timedelta(days=from_idx)
            date1 = d00 + timedelta(days=to_idx)
            if config.debug_chosen:
                print("      {} segment {} section length {:5.2f}   {} - {}   {}-{}".format(get_object_name(obj).upper(), path_seg, sec_len, date0, date1, get_object_name(obj8), get_object_name(obj9)))

    planet_Y = meridian_pass[obj]
    planet_xidx = meridian_xidx[obj]

    for index, item in enumerate(p_segments):   # per path segment
        seg_len, seg_mid_idx, seg_mid_mpa, sect_count = item
        # 1) try mid-position of each segment
        if seg_len > 4.75:
            idx_mid.append((index, seg_mid_idx))  # tuple: segment# + mid-date offset
    
        # 2) try mid-position of longest section of each segment
        #             (this may cause duplicates)
        for i in range(sect_count):
            sec_len, from_idx, to_idx, obj8, obj9 = p_sections[index][i]  # pick longest
            mid_idx = from_idx + int((to_idx - from_idx)/2)
            # date0 = d00 + timedelta(days=mid_idx)
            # print(sec_len, date0)
            if sec_len > 5.5: # skip if section is too short
                idx_mid.append((index, mid_idx))    # append tuple
            break

    # for segnum, idx in idx_mid:
        # date0 = d00 + timedelta(days=idx)
        # print("{} seg {}: pick {}".format(get_object_name(obj).upper(),segnum,date0))

    idx_mid = list(set(idx_mid))    # remove duplicate tuples in list

    # # strategy to position the name label if path has >= 2 segments
    # idx_min = 0                 # process first segment from Jan 1st
    # for xidx in planet_xidx:
        # idx_max = xidx - 1
        # idx_len = idx_max - idx_min
        # if idx_len >= 60:
            # idx_mid.append(idx_min + int(idx_len/2))
            # #print(idx_mid[ncount],d00 + timedelta(days=idx_mid[ncount]))
        # idx_min = xidx

    # if len(planet_xidx) > 0:    # process final segment up to Dec 31st
        # idx_max = daystoprocess - 1
        # idx_len = idx_max - idx_min
        # if idx_len >= 60:
            # idx_mid.append(idx_min + int(idx_len/2))
            # #print(idx_mid[ncount],d00 + timedelta(days=idx_mid[ncount]))

    # if len(planet_xidx) == 0:
        # # strategy to position the name label if path has only 1 segment
        # pass

    hdiag = hdiags[obj]     # height (in 1/10 hour) perpendiculat to label text
    seg_chosen = []         # segments with a label position

    for segnum, idx in idx_mid:
        if segnum in seg_chosen: continue   # one label per segment is sufficient
        abcount = 0             # count successful above/below positions (per segment)

        for ab in [0,1]:        # label above and below path...
            xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang = label_rectangle(obj, idx, hdiag*vab[ab])
            #print(xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang)
            date_min = d00 + timedelta(days=idx_min)
            date_max = d00 + timedelta(days=idx_max)
            date0 = d00 + timedelta(days=idx)
            #tex += plot_rectangle(xy)
            #tex += plot_rectangle(rxy)
            #tex += printdot(100, 5.0)           # test: 100 days, 5 hours
            #tex += printdot2(10*sf, 5.0*sf)     # test: 100 days, 5 hours

            # check if the label overwrites neighboring declination paths
            badobj = path_overlaid_check(obj, xy, idx_min, idx_max, dec_min, dec_max, lab0, ang)
            if len(badobj) > 0:
                if config.debug_chosen:
                    msg = ""
                    for obj0 in badobj:
                        if obj0 == -1:
                            msg += "label off-chart!, "
                        else:
                            msg += "{}, ".format(get_object_name(obj0).upper())
                    print("      {:7} (label {}) on {} overlays path: {}".format(get_object_name(obj).upper(), pab[ab], date0, msg[:-2]))
            else:
                seg_chosen.append(segnum)
                abcount += 1
                abgood = ab
                two_tuples[ab] = (obj, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang, ab)

        if abcount == 2:    # then save both (above & below) in label_pos
            # look for greatest vertical separation from other planets/sun
            abdiff_min = [24.0] * 2            # abdiff_min[0 to 1]
            abdiff = [[24.0] * 6 for i in range(2)]    # abdiff[0 to 1][0 to 5]
            mpa1 = meridian_pass[obj][idx]
            for k in range(6):
                if k == obj: continue
                mpa2 = meridian_pass[k][idx]
                j = 0 if mpa2 > mpa1 else 1     # 0 if above obj; 1 if below
                abdiff[j][k] = abs(mpa2 - mpa1)
            abdiff_min[0] = min(abdiff[0])  # minimum dec separation above
            abdiff_min[1] = min(abdiff[1])  # minimum dec separation below
            # the first choice is the preferred position...
            # 1st pick: highest minimum distance to nearest path (above or below obj)
            ab = 0 if abdiff_min[0] > abdiff_min[1] else 1
            # 1st pick: away from corner if idx < 25 or daytoprocess - idx < 25
            if idx < 25: ab = 0
            if daystoprocess - idx < 25: sb = 1
            write_label_candidate(obj, idx, ang, ab)
            label_pos.append(two_tuples[ab])
            # 2nd pick: the opposite side (above or below obj)
            ab = 1 - ab
            write_label_candidate(obj, idx, ang, ab)
            label_pos.append(two_tuples[ab])
        elif abcount == 1:  # then save the position (above or below) that worked
            write_label_candidate(obj, idx, ang, abgood)
            label_pos.append(two_tuples[abgood])

# ...................................................................
#      try some label positions avoiding a path overlap: SATURN
# ...................................................................

    # -------------------------------------------------------------------
    # |  x-, y-position coordinates are in units of '1 hour' vertically |
    # |  or '10 calendar days' horizontally, i.e. 1 unit corresponds    |
    # |  to the chart horizontal separation lines and close to the      |
    # |  chart vertical lines (as not every month has 30 days).         |
    # -------------------------------------------------------------------

    obj = 5         # SATURN
    two_tuples = [None, None]   # store tuple to be appended to label_pos
    idx_mid = []                # idx mid-position values per path segment
    p_segments, p_sections = path_sections(obj, tup_crosspoints, True)
    # p_segments sorted by segment ASC
    # p_sections sorted by segment ASC, length DESC, from date ASC

    for seg_len, seg_mid_idx, seg_mid_mpa, sect_count in p_segments:
        date0 = d00 + timedelta(days=seg_mid_idx)
        if config.debug_chosen:
            print("      {} segment with {} sections, length {:5.2f}   mid {} {:5.2f}".format(get_object_name(obj).upper(), sect_count, seg_len, date0, seg_mid_mpa))

    for path_seg in range(len(p_sections)):
        for sec_len, from_idx, to_idx, obj8, obj9 in p_sections[path_seg]:
            date0 = d00 + timedelta(days=from_idx)
            date1 = d00 + timedelta(days=to_idx)
            if config.debug_chosen:
                print("      {} segment {} section length {:5.2f}   {} - {}   {}-{}".format(get_object_name(obj).upper(), path_seg, sec_len, date0, date1, get_object_name(obj8), get_object_name(obj9)))

    planet_Y = meridian_pass[obj]
    planet_xidx = meridian_xidx[obj]

    for index, item in enumerate(p_segments):   # per path segment
        seg_len, seg_mid_idx, seg_mid_mpa, sect_count = item
        # 1) try mid-position of each segment
        if seg_len > 6:
            idx_mid.append((index, seg_mid_idx))  # tuple: segment# + mid-date offset
    
        # 2) try mid-position of longest section of each segment
        #             (this may cause duplicates)
        for i in range(sect_count):
            sec_len, from_idx, to_idx, obj8, obj9 = p_sections[index][i]  # pick longest
            mid_idx = from_idx + int((to_idx - from_idx)/2)
            if sec_len > 5.5:   # skip if section is too short
                idx_mid.append((index, mid_idx))    # append tuple
            break

    # idx_mid = list(set(idx_mid))    # remove duplicate tuples in list

    # for segnum, idx in idx_mid:
        # date0 = d00 + timedelta(days=idx)
        # print("      {} seg {}: pick {}".format(get_object_name(obj).upper(),segnum,date0))

    # # strategy to position the name label if path has >= 2 segments
    # # 1) try mid-position of segment (left border to lower border)
    # idx_min = 0                 # process first segment from Jan 1st
    # for xidx in planet_xidx:
        # idx_max = xidx
        # idx_len = idx_max - idx_min
        # if idx_len >= 60:
            # idx_mid.append(idx_min + int(idx_len/2))
        # idx_min = xidx + 1

    # # 2) try mid-position of segment (upper border to right border)
    # if len(planet_xidx) > 0:    # process final segment up to Dec 31st
        # idx_max = daystoprocess - 1
        # idx_len = idx_max - idx_min
        # if idx_len >= 60:
            # idx_mid.append(idx_min + int(idx_len/2))

    # if len(planet_xidx) > 0:
        # # 3) try mid-position of longest section of first segment
        # # 4) try mid-position of longest section of last segment
        # lseg = rseg = False
        # for i in range(len(p_sections[0])):
            # sec_len, from_idx, to_idx, obj8, obj9 = p_sections[0][-i]  # pick longest
            # mid_idx = from_idx + int((to_idx - from_idx)/2)
            # if sec_len > 6: # skip if section is too short
                # if not lseg and mid_idx < planet_xidx[0]:
                    # idx_mid.append(mid_idx)
                    # lseg = True     # left segment label position candidate found
                # if not rseg and mid_idx > planet_xidx[0]:
                    # idx_mid.append(mid_idx)
                    # rseg = True     # right segment label position candidate found
            # if lseg and rseg: break

    # # strategy to position the name label if path has only 1 segment
    # if len(planet_xidx) == 0:
        # pass

    hdiag = hdiags[obj]     # height (in 1/10 hour) perpendiculat to label text
    seg_chosen = []         # segments with a label position

    for segnum, idx in idx_mid:
        if segnum in seg_chosen: continue   # one label per segment is sufficient
        abcount = 0             # count successful above/below positions (per segment)

        for ab in [0,1]:        # label above and below path...
            xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang = label_rectangle(obj, idx, hdiag*vab[ab])
            #print(xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang)
            date_min = d00 + timedelta(days=idx_min)
            date_max = d00 + timedelta(days=idx_max)
            date0 = d00 + timedelta(days=idx)
            #tex += plot_rectangle(xy)
            #tex += plot_rectangle(rxy)
            #tex += printdot(100, 5.0)           # test: 100 days, 5 hours
            #tex += printdot2(10*sf, 5.0*sf)     # test: 100 days, 5 hours

            # check if the label overwrites neighboring declination paths
            badobj = path_overlaid_check(obj, xy, idx_min, idx_max, dec_min, dec_max, lab0, ang)
            if len(badobj) > 0:
                msg = ""
                for obj0 in badobj:
                    if obj0 == -1:
                        msg += "label off-chart!, "
                    else:
                        msg += "{}, ".format(get_object_name(obj0).upper())
                if verbose:
                    print("      {:7} (label {}) on {} overlays path: {}".format(get_object_name(obj).upper(), pab[ab], date0, msg[:-2]))
            else:
                seg_chosen.append(segnum)
                abcount += 1
                abgood = ab
                two_tuples[ab] = (obj, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang, ab)

        if abcount == 2:    # then save both (above & below) in label_pos
            # look for greatest vertical separation from other planets/sun
            abdiff_min = [24.0] * 2            # abdiff_min[0 to 1]
            abdiff = [[24.0] * 6 for i in range(2)]    # abdiff[0 to 1][0 to 5]
            mpa1 = meridian_pass[obj][idx]
            for k in range(6):
                if k == obj: continue
                mpa2 = meridian_pass[k][idx]
                j = 0 if mpa2 > mpa1 else 1     # 0 if above obj; 1 if below
                abdiff[j][k] = abs(mpa2 - mpa1)
            abdiff_min[0] = min(abdiff[0])  # minimum dec separation above
            abdiff_min[1] = min(abdiff[1])  # minimum dec separation below
            # the first choice is the preferred position...
            # 1st pick: highest minimum distance to nearest path (above or below obj)
            ab = 0 if abdiff_min[0] > abdiff_min[1] else 1
            # 1st pick: away from corner if idx < 25 or daytoprocess - idx < 25
            if idx < 25: ab = 0
            if daystoprocess - idx < 25: sb = 1
            write_label_candidate(obj, idx, ang, ab)
            label_pos.append(two_tuples[ab])
            # 2nd pick: the opposite side (above or below obj)
            ab = 1 - ab
            write_label_candidate(obj, idx, ang, ab)
            label_pos.append(two_tuples[ab])
        elif abcount == 1:  # then save the position (above or below) that worked
            write_label_candidate(obj, idx, ang, abgood)
            label_pos.append(two_tuples[abgood])

# ..................................................................
#      try some label positions avoiding a path overlap: URANUS
# ..................................................................

    if config.plotUN:
        obj = 6         # URANUS
        two_tuples = [None, None]   # store tuple to be appended to label_pos
        idx_ok = []                 # idx mid-position values per path segment

        if len(meridian_xidx[obj]) > 0:
            xidx = meridian_xidx[obj][0]
            if xidx >= 40:
                idx_ok.append((0, xidx - 20))
            if xidx <= daystoprocess - 41:
                idx_ok.append((1, xidx + 21))

        hdiag = hdiags[obj]     # height (in 1/10 hour) perpendiculat to label text
        seg_chosen = []         # segments with a label position

        for segnum, idx in idx_ok:
            if segnum in seg_chosen: continue   # one label per segment is sufficient
            abcount = 0             # count successful above/below positions (per segment)

            for ab in [0,1]:        # label above and below path...
                xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang = label_rectangle(obj, idx, hdiag*vab[ab])
                # check if the label overwrites neighboring declination paths
                badobj = path_overlaid_check(obj, xy, idx_min, idx_max, dec_min, dec_max, lab0, ang)
                if len(badobj) > 0:
                    msg = ""
                    for obj0 in badobj:
                        if obj0 == -1:
                            msg += "label off-chart!, "
                        else:
                            msg += "{}, ".format(get_object_name(obj0).upper())
                    if verbose:
                        print("      {:7} (label {}) on {} overlays path: {}".format(get_object_name(obj).upper(), pab[ab], date0, msg[:-2]))
                else:
                    seg_chosen.append(segnum)
                    abcount += 1
                    abgood = ab
                    two_tuples[ab] = (obj, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang, ab)

            if abcount == 2:    # then save both (above & below) in label_pos
                ab = 0 if segnum == 0 else 1    # above/below label preference
                write_label_candidate(obj, idx, ang, ab)
                label_pos.append(two_tuples[ab])
                # 2nd pick: the opposite side (above or below obj)
                ab = 1 - ab
                write_label_candidate(obj, idx, ang, ab)
                label_pos.append(two_tuples[ab])
            elif abcount == 1:  # then save the position (above or below) that worked
                write_label_candidate(obj, idx, ang, abgood)
                label_pos.append(two_tuples[abgood])

# ...................................................................
#      try some label positions avoiding a path overlap: NEPTUNE
# ...................................................................

    if config.plotUN:
        obj = 7         # NEPTUNE
        two_tuples = [None, None]   # store tuple to be appended to label_pos
        idx_ok = []                 # idx mid-position values per path segment

        if len(meridian_xidx[obj]) > 0:
            xidx = meridian_xidx[obj][0]
            if xidx >= 40:
                idx_ok.append((0, xidx - 20))
            if xidx <= daystoprocess - 41:
                idx_ok.append((1, xidx + 21))

        hdiag = hdiags[obj]     # height (in 1/10 hour) perpendiculat to label text
        seg_chosen = []         # segments with a label position

        for segnum, idx in idx_ok:
            if segnum in seg_chosen: continue   # one label per segment is sufficient
            abcount = 0             # count successful above/below positions (per segment)

            for ab in [0,1]:        # label above and below path...
                xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang = label_rectangle(obj, idx, hdiag*vab[ab])
                # check if the label overwrites neighboring declination paths
                badobj = path_overlaid_check(obj, xy, idx_min, idx_max, dec_min, dec_max, lab0, ang)
                if len(badobj) > 0:
                    if config.debug_chosen:
                        msg = ""
                        for obj0 in badobj:
                            if obj0 == -1:
                                msg += "label off-chart!, "
                            else:
                                msg += "{}, ".format(get_object_name(obj0).upper())
                        print("      {:7} (label {}) on {} overlays path: {}".format(get_object_name(obj).upper(), pab[ab], date0, msg[:-2]))
                else:
                    seg_chosen.append(segnum)
                    abcount += 1
                    abgood = ab
                    two_tuples[ab] = (obj, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang, ab)

            if abcount == 2:    # then save both (above & below) in label_pos
                ab = 0 if segnum == 0 else 1    # above/below label preference
                write_label_candidate(obj, idx, ang, ab)
                label_pos.append(two_tuples[ab])
                # 2nd pick: the opposite side (above or below obj)
                ab = 1 - ab
                write_label_candidate(obj, idx, ang, ab)
                label_pos.append(two_tuples[ab])
            elif abcount == 1:  # then save the position (above or below) that worked
                write_label_candidate(obj, idx, ang, abgood)
                label_pos.append(two_tuples[abgood])

# ......................................................................................
#  try some label positions avoiding a path overlap: Sunrise/Sunset at chosen latitude
# ......................................................................................

    objn = [8, 9]    # Sunrise/Sunset at 51.5°N path
    name = ['Sunrise', 'Sunset']

    if config.plotSS:
        two_tuples = [None, None]   # store tuple to be appended to label_pos
        idx_mid = []                # idx mid-position values

        #      candidates for sunrise ..........
        # p_sections sorted by length DESC, from date ASC
        p_sections = sunrise_set_sections(sunAM, True)
        sec_len, from_idx, to_idx = p_sections[0]   # pick longest
        # 1) try around October 1st if section up to Jan 1 next year is over 6 months long
        if to_idx == daystoprocess and sec_len > 18.4: 
            idx_mid.append((0, 273))    # append tuple (with pathnum = 0)
        # 2) try mid-position of longest section
        mid_idx = from_idx + int((to_idx - from_idx)/2)
        # date0 = d00 + timedelta(days=mid_idx)
        # print(sec_len, date0)
        if sec_len > 6: # skip if section is too short (<2 months)
            idx_mid.append((0, mid_idx))    # append tuple (with pathnum = 0)

        #      candidates for sunset ..........
        # p_sections sorted by length DESC, from date ASC
        p_sections = sunrise_set_sections(sunPM, True)
        sec_len, from_idx, to_idx = p_sections[0]   # pick longest
        # 1) try around March 22nd if section from Jan 1 is over 6 months long
        if from_idx == 0 and sec_len > 18.1: 
            idx_mid.append((1, 81))     # append tuple (with pathnum = 1)
        # 2) try mid-position of longest section
        mid_idx = from_idx + int((to_idx - from_idx)/2)
        # date0 = d00 + timedelta(days=mid_idx)
        # print(sec_len, date0)
        if sec_len > 6: # skip if section is too short
            idx_mid.append((1, mid_idx))    # append tuple (with pathnum = 1)

        hdiag = 1.4*3   # offset the text is to be raised or lowered
        for pathnum, idx in idx_mid:
            abcount = 0             # count successful above/below positions (per segment)

            for ab in [0,1]:        # label above and below path...
                xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang = label_rectangle(objn[pathnum], idx, hdiag*vab[ab])
                #print(xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang)
                date_min = d00 + timedelta(days=idx_min)
                date_max = d00 + timedelta(days=idx_max)
                date0 = d00 + timedelta(days=idx)

                # check if the label overwrites neighboring declination paths
                badobj = path_overlaid_check(objn[pathnum], xy, idx_min, idx_max, dec_min, dec_max, lab0, ang)
                if len(badobj) > 0:
                    if config.debug_chosen:
                        msg = ""
                        for obj0 in badobj:
                            if obj0 == -1:
                                msg += "label off-chart!, "
                            else:
                                msg += "{}, ".format(get_object_name(obj0).upper())
                        print("      {:7} (label {}) on {} overlays path: {}".format(name[objn[pathnum]], pab[ab], date0, msg[:-2]))
                else:
                    seg_chosen.append(segnum)
                    abcount += 1
                    abgood = ab
                    two_tuples[ab] = (objn[pathnum], idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang, ab)

            if abcount == 2:    # then save both (above & below) in label_pos
                ab = 0 if pathnum == 1 else 1   # above/below label preference
                write_label_candidate(objn[pathnum], idx, ang, ab)
                label_pos.append(two_tuples[ab])
                # 2nd pick: the opposite side (above or below obj)
                ab = 1 - ab
                write_label_candidate(objn[pathnum], idx, ang, ab)
                label_pos.append(two_tuples[ab])
            elif abcount == 1:  # then save the position (above or below) that worked
                write_label_candidate(objn[pathnum], idx, ang, abgood)
                label_pos.append(two_tuples[abgood])

# !=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=
# !=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#  pick optimal position(s) without a label overlap conflict: SUN
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    # check if the planet's label overwrites a neighboring label
    obj = 0         # SUN
    pos_chosen = 0
    prev_idx = -1   # invalid value

    for index, item in enumerate(label_pos):
        obj9, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, labXY, ang, ab = item
        if obj9 != obj: continue
        if idx == prev_idx: continue    # don't print above & below for the same idx
        date0 = d00 + timedelta(days=idx)
        badobj = label_overlaid_check(index, idx, xy, idx_min, idx_max, dec_min, dec_max, labXY, ang)

        if len(badobj) > 0:
            # SUN overwrites a neighboring label
            msg = ""
            if config.debug_labels:
                tex += plot_rectangle(xy)   # for DEBUGGING
            for ndx, obj0, rxy0, tex0 in badobj: # tuple 'badobj' is unpacked here
                if config.debug_labels:
                    tex += plot_rectangle(rxy0) # for DEBUGGING
                    tex += tex0                 # for DEBUGGING
                msg += "{:2d} {}, ".format(ndx+1, get_object_name(obj0).upper())
            if config.debug_chosen:
                print("      {:7} (label {}) on {} overlays label: {}".format(get_object_name(obj).upper(), pab[ab], date0, msg[:-2]))
        else:
            # ||  two labels are sufficient  ||
            chosen_label.append((obj, index))
            if config.debug_chosen:
                print("   {:2d} {:7} chosen".format(index+1,get_object_name(obj).upper()))
            pos_chosen += 1
            prev_idx = idx      # skip second label at same idx position
            # note: the first of two labels at same idx is the preferred one
            if pos_chosen >= 2: break   # two labels are sufficient

    if pos_chosen == 0:
        print("FAILED to position label for {}".format(get_object_name(obj).upper()))

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#  pick optimal position(s) without a label overlap conflict: MERCURY
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    # check if the planet's label overwrites a neighboring label
    obj = 1         # MERCURY
    pos_chosen = 0
    prev_idx = -1   # invalid value

    for index, item in enumerate(label_pos):
        obj9, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, labXY, ang, ab = item
        if obj9 != obj: continue
        if idx == prev_idx: continue    # don't print above & below for the same idx
        date0 = d00 + timedelta(days=idx)
        badobj = label_overlaid_check(index, idx, xy, idx_min, idx_max, dec_min, dec_max, labXY, ang)

        if len(badobj) > 0:
            # MERCURY overwrites a neighboring label
            msg = ""
            if config.debug_labels:
                tex += plot_rectangle(xy)   # for DEBUGGING
            for ndx, obj0, rxy0, tex0 in badobj: # tuple 'badobj' is unpacked here
                if config.debug_labels:
                    tex += plot_rectangle(rxy0) # for DEBUGGING
                    tex += tex0                 # for DEBUGGING
                msg += "{:2d} {}, ".format(ndx+1, get_object_name(obj0).upper())
            if config.debug_chosen:
                print("      {:7} (label {}) on {} overlays label: {}".format(get_object_name(obj).upper(), pab[ab], date0, msg[:-2]))
        else:
            # ||  two labels are sufficient  ||
            chosen_label.append((obj, index))
            if config.debug_chosen:
                print("   {:2d} {:7} chosen".format(index+1,get_object_name(obj).upper()))
            pos_chosen += 1
            prev_idx = idx      # skip second label at same idx position
            # note: the first of two labels at same idx is the preferred one
            if pos_chosen >= 2: break   # two labels are sufficient

    if pos_chosen == 0:
        print("FAILED to position label for {}".format(get_object_name(obj).upper()))

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#  pick optimal position(s) without a label overlap conflict: VENUS
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    # check if the planet's label overwrites a neighboring label
    obj = 2         # VENUS
    pos_chosen = 0
    prev_idx = -1   # invalid value

    for index, item in enumerate(label_pos):
        obj9, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, labXY, ang, ab = item
        if obj9 != obj: continue
        if idx == prev_idx: continue    # don't print above & below for the same idx
        date0 = d00 + timedelta(days=idx)
        badobj = label_overlaid_check(index, idx, xy, idx_min, idx_max, dec_min, dec_max, labXY, ang)

        if len(badobj) > 0:
            # VENUS overwrites a neighboring label
            msg = ""
            if config.debug_labels:
                tex += plot_rectangle(xy)   # for DEBUGGING
            for ndx, obj0, rxy0, tex0 in badobj: # tuple 'badobj' is unpacked here
                if config.debug_labels:
                    tex += plot_rectangle(rxy0) # for DEBUGGING
                    tex += tex0                 # for DEBUGGING
                msg += "{:2d} {}, ".format(ndx+1, get_object_name(obj0).upper())
            if config.debug_chosen:
                print("      {:7} (label {}) on {} overlays label: {}".format(get_object_name(obj).upper(), pab[ab], date0, msg[:-2]))
        else:
            # ||  two labels are sufficient  ||
            chosen_label.append((obj, index))
            if config.debug_chosen:
                print("   {:2d} {:7} chosen".format(index+1,get_object_name(obj).upper()))
            pos_chosen += 1
            prev_idx = idx      # skip second label at same idx position
            # note: the first of two labels at same idx is the preferred one
            if pos_chosen >= 2: break   # two labels are sufficient

    if pos_chosen == 0:
        print("FAILED to position label for {}".format(get_object_name(obj).upper()))

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#  pick optimal position(s) without a label overlap conflict: MARS
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    # check if the planet's label overwrites a neighboring label
    obj = 3         # MARS
    pos_chosen = 0
    prev_idx = -1   # invalid value

    for index, item in enumerate(label_pos):
        obj9, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, labXY, ang, ab = item
        if obj9 != obj: continue
        if idx == prev_idx: continue    # don't print above & below for the same idx
        date0 = d00 + timedelta(days=idx)
        badobj = label_overlaid_check(index, idx, xy, idx_min, idx_max, dec_min, dec_max, labXY, ang)

        if len(badobj) > 0:
            # MARS overwrites a neighboring label
            msg = ""
            if config.debug_labels:
                tex += plot_rectangle(xy)   # for DEBUGGING
            for ndx, obj0, rxy0, tex0 in badobj: # tuple 'badobj' is unpacked here
                if config.debug_labels:
                    tex += plot_rectangle(rxy0) # for DEBUGGING
                    tex += tex0                 # for DEBUGGING
                msg += "{:2d} {}, ".format(ndx+1, get_object_name(obj0).upper())
            if config.debug_chosen:
                print("      {:7} (label {}) on {} overlays label: {}".format(get_object_name(obj).upper(), pab[ab], date0, msg[:-2]))
        else:
            # ||  two labels are sufficient  ||
            chosen_label.append((obj, index))
            if config.debug_chosen:
                print("   {:2d} {:7} chosen".format(index+1,get_object_name(obj).upper()))
            pos_chosen += 1
            prev_idx = idx      # skip second label at same idx position
            # note: the first of two labels at same idx is the preferred one
            if pos_chosen >= 2: break   # two labels are sufficient

    if pos_chosen == 0:
        print("FAILED to position label for {}".format(get_object_name(obj).upper()))

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#  pick optimal position(s) without a label overlap conflict: JUPITER
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    # check if the planet's label overwrites a neighboring label
    obj = 4         # JUPITER
    pos_chosen = 0
    prev_idx = -1   # invalid value

    for index, item in enumerate(label_pos):
        obj9, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, labXY, ang, ab = item
        if obj9 != obj: continue
        if idx == prev_idx: continue    # don't print above & below for the same idx
        date0 = d00 + timedelta(days=idx)
        badobj = label_overlaid_check(index, idx, xy, idx_min, idx_max, dec_min, dec_max, labXY, ang)

        if len(badobj) > 0:
            # JUPITER overwrites a neighboring label
            msg = ""
            if config.debug_labels:
                tex += plot_rectangle(xy)   # for DEBUGGING
            for ndx, obj0, rxy0, tex0 in badobj: # tuple 'badobj' is unpacked here
                if config.debug_labels:
                    tex += plot_rectangle(rxy0) # for DEBUGGING
                    tex += tex0                 # for DEBUGGING
                msg += "{:2d} {}, ".format(ndx+1, get_object_name(obj0).upper())
            if config.debug_chosen:
                print("      {:7} (label {}) on {} overlays label: {}".format(get_object_name(obj).upper(), pab[ab], date0, msg[:-2]))
        else:
            # ||  two labels are sufficient  ||
            chosen_label.append((obj, index))
            if config.debug_chosen:
                print("   {:2d} {:7} chosen".format(index+1,get_object_name(obj).upper()))
            pos_chosen += 1
            prev_idx = idx      # skip second label at same idx position
            # note: the first of two labels at same idx is the preferred one
            if pos_chosen >= 2: break   # two labels are sufficient

    if pos_chosen == 0:
        print("FAILED to position label for {}".format(get_object_name(obj).upper()))

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#  pick optimal position(s) without a label overlap conflict: SATURN
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    # check if the planet's label overwrites a neighboring label
    obj = 5         # SATURN
    pos_chosen = 0
    prev_idx = -1   # invalid value

    for index, item in enumerate(label_pos):
        obj9, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, labXY, ang, ab = item
        if obj9 != obj: continue
        if idx == prev_idx: continue    # don't print above & below for the same idx
        date0 = d00 + timedelta(days=idx)
        badobj = label_overlaid_check(index, idx, xy, idx_min, idx_max, dec_min, dec_max, labXY, ang)

        if len(badobj) > 0:
            # SATURN overwrites a neighboring label
            msg = ""
            if config.debug_labels:
                tex += plot_rectangle(xy)   # for DEBUGGING
            for ndx, obj0, rxy0, tex0 in badobj: # tuple 'badobj' is unpacked here
                if config.debug_labels:
                    tex += plot_rectangle(rxy0) # for DEBUGGING
                    tex += tex0                 # for DEBUGGING
                msg += "{:2d} {}, ".format(ndx+1, get_object_name(obj0).upper())
            if config.debug_chosen:
                print("      {:7} (label {}) on {} overlays label: {}".format(get_object_name(obj).upper(), pab[ab], date0, msg[:-2]))
        else:
            # ||  two labels are sufficient  ||
            chosen_label.append((obj, index))
            if config.debug_chosen:
                print("   {:2d} {:7} chosen".format(index+1,get_object_name(obj).upper()))
            pos_chosen += 1
            prev_idx = idx      # skip second label at same idx position
            # note: the first of two labels at same idx is the preferred one
            if pos_chosen >= 2: break   # two labels are sufficient

    if pos_chosen == 0:
        print("FAILED to position label for {}".format(get_object_name(obj).upper()))

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#  pick optimal position(s) without a label overlap conflict: URANUS
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    if config.plotUN:
        obj = 6         # URANUS
        pos_chosen = 0
        prev_idx = -1   # invalid value

        for index, item in enumerate(label_pos):
            obj9, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, labXY, ang, ab = item
            if obj9 != obj: continue
            if idx == prev_idx: continue    # don't print above & below for the same idx
            date0 = d00 + timedelta(days=idx)
            badobj = label_overlaid_check(index, idx, xy, idx_min, idx_max, dec_min, dec_max, labXY, ang)

            if len(badobj) > 0:
                # URANUS overwrites a neighboring label
                msg = ""
                if config.debug_labels:
                    tex += plot_rectangle(xy)   # for DEBUGGING
                for ndx, obj0, rxy0, tex0 in badobj: # tuple 'badobj' is unpacked here
                    if config.debug_labels:
                        tex += plot_rectangle(rxy0) # for DEBUGGING
                        tex += tex0                 # for DEBUGGING
                    msg += "{:2d} {}, ".format(ndx+1, get_object_name(obj0).upper())
                if config.debug_chosen:
                    print("      {:7} (label {}) on {} overlays label: {}".format(get_object_name(obj).upper(), pab[ab], date0, msg[:-2]))
            else:
                # ||  two labels are sufficient  ||
                chosen_label.append((obj, index))
                if config.debug_chosen:
                    print("   {:2d} {:7} chosen".format(index+1,get_object_name(obj).upper()))
                pos_chosen += 1
                prev_idx = idx      # skip second label at same idx position
                # note: the first of two labels at same idx is the preferred one
                if pos_chosen >= 2: break   # two labels are sufficient

        if pos_chosen == 0:
            print("FAILED to position label for {}".format(get_object_name(obj).upper()))

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#  pick optimal position(s) without a label overlap conflict: NEPTUNE
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    if config.plotUN:
        obj = 7         # NEPTUNE
        pos_chosen = 0
        prev_idx = -1   # invalid value

        for index, item in enumerate(label_pos):
            obj9, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, labXY, ang, ab = item
            if obj9 != obj: continue
            if idx == prev_idx: continue    # don't print above & below for the same idx
            date0 = d00 + timedelta(days=idx)
            badobj = label_overlaid_check(index, idx, xy, idx_min, idx_max, dec_min, dec_max, labXY, ang)

            if len(badobj) > 0:
                # NEPTUNE overwrites a neighboring label
                msg = ""
                if config.debug_labels:
                    tex += plot_rectangle(xy)   # for DEBUGGING
                for ndx, obj0, rxy0, tex0 in badobj: # tuple 'badobj' is unpacked here
                    if config.debug_labels:
                        tex += plot_rectangle(rxy0) # for DEBUGGING
                        tex += tex0                 # for DEBUGGING
                    msg += "{:2d} {}, ".format(ndx+1, get_object_name(obj0).upper())
                if config.debug_chosen:
                    print("      {:7} (label {}) on {} overlays label: {}".format(get_object_name(obj).upper(), pab[ab], date0, msg[:-2]))
            else:
                # ||  two labels are sufficient  ||
                chosen_label.append((obj, index))
                if config.debug_chosen:
                    print("   {:2d} {:7} chosen".format(index+1,get_object_name(obj).upper()))
                pos_chosen += 1
                prev_idx = idx      # skip second label at same idx position
                # note: the first of two labels at same idx is the preferred one
                if pos_chosen >= 2: break   # two labels are sufficient

        if pos_chosen == 0:
            print("FAILED to position label for {}".format(get_object_name(obj).upper()))


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#  pick optimal position(s) without a label overlap conflict: Sunrise at 51.5°N
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    if config.plotSS:
        # check if the planet's label overwrites a neighboring label
        obj = 8         # Sunrise at 51.5°N
        pos_chosen = 0
        prev_idx = -1   # invalid value

        for index, item in enumerate(label_pos):
            obj9, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, labXY, ang, ab = item
            if obj9 != obj: continue
            if idx == prev_idx: continue    # don't print above & below for the same idx
            date0 = d00 + timedelta(days=idx)
            badobj = label_overlaid_check(index, idx, xy, idx_min, idx_max, dec_min, dec_max, labXY, ang)

            if len(badobj) > 0:
                # Sunrise at 51.5°N overwrites a neighboring label
                msg = ""
                if config.debug_labels:
                    tex += plot_rectangle(xy)   # for DEBUGGING
                for ndx, obj0, rxy0, tex0 in badobj: # tuple 'badobj' is unpacked here
                    if config.debug_labels:
                        tex += plot_rectangle(rxy0) # for DEBUGGING
                        tex += tex0                 # for DEBUGGING
                    msg += "{:2d} {}, ".format(ndx+1, get_object_name(obj0).upper())
                if config.debug_chosen:
                    print("      {:7} (label {}) on {} overlays label: {}".format(get_object_name(obj), pab[ab], date0, msg[:-2]))
            else:
                # ||  one label is sufficient  ||
                chosen_label.append((obj, index))
                if config.debug_chosen:
                    print("   {:2d} {:7} chosen".format(index+1,get_object_name(obj)))
                pos_chosen += 1
                prev_idx = idx      # skip second label at same idx position
                # note: the first of two labels at same idx is the preferred one
                if pos_chosen >= 1: break   # one label is sufficient

        if pos_chosen == 0:
            print("FAILED to position label for {}".format(get_object_name(obj)))

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#  pick optimal position(s) without a label overlap conflict: Sunset at 51.5°N
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    if config.plotSS:
        # check if the planet's label overwrites a neighboring label
        obj = 9         # Sunset at 51.5°N
        pos_chosen = 0
        prev_idx = -1   # invalid value

        for index, item in enumerate(label_pos):
            obj9, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, labXY, ang, ab = item
            if obj9 != obj: continue
            if idx == prev_idx: continue    # don't print above & below for the same idx
            date0 = d00 + timedelta(days=idx)
            badobj = label_overlaid_check(index, idx, xy, idx_min, idx_max, dec_min, dec_max, labXY, ang)

            if len(badobj) > 0:
                # Sunset at 51.5°N overwrites a neighboring label
                msg = ""
                if config.debug_labels:
                    tex += plot_rectangle(xy)   # for DEBUGGING
                for ndx, obj0, rxy0, tex0 in badobj: # tuple 'badobj' is unpacked here
                    if config.debug_labels:
                        tex += plot_rectangle(rxy0) # for DEBUGGING
                        tex += tex0                 # for DEBUGGING
                    msg += "{:2d} {}, ".format(ndx+1, get_object_name(obj0).upper())
                if config.debug_chosen:
                    print("      {:7} (label {}) on {} overlays label: {}".format(get_object_name(obj), pab[ab], date0, msg[:-2]))
            else:
                # ||  one label is sufficient  ||
                chosen_label.append((obj, index))
                if config.debug_chosen:
                    print("   {:2d} {:7} chosen".format(index+1,get_object_name(obj)))
                pos_chosen += 1
                prev_idx = idx      # skip second label at same idx position
                # note: the first of two labels at same idx is the preferred one
                if pos_chosen >= 1: break   # one label is sufficient

        if pos_chosen == 0:
            print("FAILED to position label for {}".format(get_object_name(obj)))

# !=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=
# !=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=!=

    if verbose:
        print("   ========== {} chosen labels ==========".format(len(chosen_label)))
        msg = '   '
        for o, ndx in chosen_label:
            msg += "{:2d} {}, ".format(ndx+1,get_object_name(o).upper())
        print(msg[:-2])

# =========================================================================
# ======= finally ... PRINT CHOSEN LABELS ON MERIDIAN PASSAGE PATHS =======
# =========================================================================

    tex += """
% print chosen labels on Meridian Passage chart"""

    # ---- print label at mid-position: SUN ----
    obj = 0
    txt = r"\textbf{SUN}"
    for o, ndx in chosen_label:
        if o != obj: continue
        obj9, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, labXY, ang, ab = label_pos[ndx]
        #tex += printlabel(txt, idx, hdiag, planet_dec[obj])
        tex += printlabelXY(txt, labXY, ang, 'darkgray', False)

    # ---- print label at mid-position: MERCURY ----
    obj = 1
    txt = r"\textbf{MERCURY}"
    for o, ndx in chosen_label:
        if o != obj: continue
        obj9, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, labXY, ang, ab = label_pos[ndx]
        #tex += printlabel(txt, idx, hdiag, planet_dec[obj])
        tex += printlabelXY(txt, labXY, ang)

    # ---- print label at mid-position: VENUS ----
    obj = 2
    txt = r"\textbf{VENUS}"
    for o, ndx in chosen_label:
        if o != obj: continue
        obj9, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, labXY, ang, ab = label_pos[ndx]
        #tex += printlabel(txt, idx, hdiag, planet_dec[obj])
        tex += printlabelXY(txt, labXY, ang)

    # ---- print label at mid-position: MARS ----
    obj = 3
    txt = r"\textbf{MARS}"
    for o, ndx in chosen_label:
        if o != obj: continue
        obj9, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, labXY, ang, ab = label_pos[ndx]
        #tex += printlabel(txt, idx, hdiag, planet_dec[obj])
        tex += printlabelXY(txt, labXY, ang)

    # ---- print label at mid-position: JUPITER ----
    obj = 4
    txt = r"\textbf{JUPITER}"
    for o, ndx in chosen_label:
        if o != obj: continue
        obj9, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, labXY, ang, ab = label_pos[ndx]
        #tex += printlabel(txt, idx, hdiag, planet_dec[obj])
        tex += printlabelXY(txt, labXY, ang)

    # ---- print label at mid-position: SATURN ----
    obj = 5
    txt = r"\textbf{SATURN}"
    for o, ndx in chosen_label:
        if o != obj: continue
        obj9, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, labXY, ang, ab = label_pos[ndx]
        #tex += printlabel(txt, idx, hdiag, planet_dec[obj])
        tex += printlabelXY(txt, labXY, ang)

    # ---- print label at mid-position: URANUS ----
    if config.plotUN:
        obj = 6
        txt = r"\textbf{URANUS}"
        for o, ndx in chosen_label:
            if o != obj: continue
            obj9, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, labXY, ang, ab = label_pos[ndx]
            #tex += printlabel(txt, idx, hdiag, planet_dec[obj])
            tex += printlabelXY(txt, labXY, ang)

    # ---- print label at mid-position: NEPTUNE ----
    if config.plotUN:
        obj = 7
        txt = r"\textbf{NEPTUNE}"
        for o, ndx in chosen_label:
            if o != obj: continue
            obj9, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, labXY, ang, ab = label_pos[ndx]
            #tex += printlabel(txt, idx, hdiag, planet_dec[obj])
            tex += printlabelXY(txt, labXY, ang)

    # ---- print label at mid-position: Sunrise at 51.5°N ----
    if config.plotSS:
        obj = 8
        txt = r"\textbf{{Sunrise at {}°{}}}".format(lat,lns)
        for o, ndx in chosen_label:
            if o != obj: continue
            obj9, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, labXY, ang, ab = label_pos[ndx]
            #tex += printlabel(txt, idx, hdiag, planet_dec[obj])
            tex += printlabelXY(txt, labXY, ang, 'gray')

    # ---- print label at mid-position: Sunset at 51.5°N ----
    if config.plotSS:
        obj = 9
        txt = r"\textbf{{Sunset at {}°{}}}".format(lat,lns)
        for o, ndx in chosen_label:
            if o != obj: continue
            obj9, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, labXY, ang, ab = label_pos[ndx]
            #tex += printlabel(txt, idx, hdiag, planet_dec[obj])
            tex += printlabelXY(txt, labXY, ang, 'gray')

    return tex

# --------------------------------------------------
# --------------  REQUIRED  FUNCTIONS --------------
# --------------------------------------------------

def label_rectangle(obj, idx, hdiag):
# determine the rectangle encosing the label + its white background
    global meridian_pass, txt_wdth, txt_hgt, boxsep, pt2cm, daystoprocess

    # check idx limits
    if idx < 1: idx = 1
    if idx > daystoprocess-2: idx = daystoprocess-2

    # PLANET position
    planet_Y = meridian_pass[obj][idx]
    obj_x = idx/10
    obj_y = planet_Y

    # label rotation angle
    ydiff = meridian_pass[obj][idx+1] - meridian_pass[obj][idx-1]
    ang = math.atan((ydiff)/(2.0/10))    # radians
    rot = "%0.3f" %(ang*todegrees)

    # label shift (label center position - planet position)
    xoffset = hdiag*math.sin(-ang)
    yoffset = hdiag*math.cos(-ang)

    # PLANET label center position ('sf' scaling factor required!)
    x0 = (xoffset/10 + obj_x)*sf
    y0 = (yoffset/10 + obj_y)*sf
    lab0 = [x0, y0]

    # label bounding box coordinates UNROTATED
    xy = [[0.0, 0.0] for i in range(4)]     # xy[0 to 3][0 to 1]
    xy[0][0] = x0 - (txt_wdth[obj]/2)*pt2cm
    xy[0][1] = y0 - ((txt_hgt/2)+boxsep)*pt2cm
    xy[1][0] = xy[0][0]
    xy[1][1] = y0 + ((txt_hgt/2)+boxsep)*pt2cm
    xy[2][0] = x0 + (txt_wdth[obj]/2)*pt2cm
    xy[2][1] = xy[1][1]
    xy[3][0] = xy[2][0]
    xy[3][1] = xy[0][1]

    # label bounding box coordinates ROTATED about label center position
    rxy = [[0.0, 0.0] for i in range(4)]    # rxy[0 to 3][0 to 1]
    dx0 = xy[0][0] - x0
    dy0 = xy[0][1] - y0
    rxy[0][0] = x0 + (math.cos(ang) * dx0) - (math.sin(ang) * dy0)
    rxy[0][1] = y0 + (math.sin(ang) * dx0) + (math.cos(ang) * dy0)
    dx1 = xy[1][0] - x0
    dy1 = xy[1][1] - y0
    rxy[1][0] = x0 + (math.cos(ang) * dx1) - (math.sin(ang) * dy1)
    rxy[1][1] = y0 + (math.sin(ang) * dx1) + (math.cos(ang) * dy1)
    dx2 = xy[2][0] - x0
    dy2 = xy[2][1] - y0
    rxy[2][0] = x0 + (math.cos(ang) * dx2) - (math.sin(ang) * dy2)
    rxy[2][1] = y0 + (math.sin(ang) * dx2) + (math.cos(ang) * dy2)
    dx3 = xy[3][0] - x0
    dy3 = xy[3][1] - y0
    rxy[3][0] = x0 + (math.cos(ang) * dx3) - (math.sin(ang) * dy3)
    rxy[3][1] = y0 + (math.sin(ang) * dx3) + (math.cos(ang) * dy3)

    # get limits of x range (in days)
    rx_min = min([x[0] for x in rxy])
    rx_max = max([x[0] for x in rxy])
    idx_min = math.floor(rx_min*10/sf)
    idx_max = math.ceil(rx_max*10/sf)
    
    # get limits of y range (in hours)
    ry_min = min([y[1] for y in rxy])/sf
    ry_max = max([y[1] for y in rxy])/sf

    return xy, rxy, idx_min, idx_max, ry_min, ry_max, lab0, ang

def path_overlaid_check(obj, xy, idx_min, idx_max, dec_min, dec_max, lab0, ang):
    # test if any planet coordinates are overlaid by label rectangle
    global meridian_pass

    x0 = lab0[0]
    y0 = lab0[1]
    badobj = []     # list of offending objects

    # range check...
    if idx_min < 0 or idx_max > daystoprocess-2:
        badobj.append(-1)   # indicate out-of-range
        return badobj

    # NOTE: A MERCURY label can overlay its own path!
    for o in range(6):  # for each object (sun/planet)
        ####if o == obj: continue   # skip the current object
        for n in range(idx_min, idx_max+1):     # scan relevant dates
            if dec_min < meridian_pass[o][n] < dec_max:
                # test if point is within label rectangle...
                # ||  rotate the point about the label center  ||
                # ||   back to where the label is horizontal   ||
                dx = n/10*sf - x0
                dy = meridian_pass[o][n]*sf - y0
                px = x0 + (math.cos(-ang) * dx) - (math.sin(-ang) * dy)
                py = y0 + (math.sin(-ang) * dx) + (math.cos(-ang) * dy)
                # is px,py within the horizontal label rectangle?
                if xy[0][0] < px < xy[2][0] and xy[0][1] < py < xy[1][1]:
                    badobj.append(o)
                    break
    return badobj

def rotate_xy(old_x, old_y, about_x, about_y, ang):
# rotate point 'old_x, old_y' by 'ang' radians about 'about_x, about_y'
    dx = old_x - about_x
    dy = old_y - about_y
    new_x = about_x + (math.cos(ang) * dx) - (math.sin(ang) * dy)
    new_y = about_y + (math.sin(ang) * dx) + (math.cos(ang) * dy)
    return new_x, new_y

def label_overlaid_check(index0, idx0, xy0, idx_min0, idx_max0, dec_min0, dec_max0, labXY0, ang0):
# test if the object's label is overlaid by another label rectangle
    global label_pos, chosen_label

    # UNROTATED box limits for object's label:
    x0_min = xy0[0][0]
    x0_max = xy0[2][0]
    y0_min = xy0[0][1]
    y0_max = xy0[1][1]
    date_obj0 = d00 + timedelta(days=labXY0[0]/sf*10)
    #print("checking if any label overlaid by {} on {}, dec = {:7.3f}".format(get_object_name(obj0).upper(),date_obj0,labXY0[1]/sf*10))
    #print("x0_min = {:.2f} x0_max = {:.2f} y0_min = {:.2f} y0_max = {:.2f}".format(x0_min,x0_max,y0_min,y0_max))
    
    tex = ''
    badobj = []     # list of offending objects

    # check against the other already chosen labels...
    for index, item in enumerate(label_pos):
        obj, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, labXY, ang, ab = item
        # EXCLUDE THE LABEL WE WANT TO VALIDATE (index == index0)
        if index == index0: break   # EXCLUDE UN-PROCESSED LABELS (index > index0)

        # first check if there are any chosen labels in 'chosen_label'
        # ... as we don't need to check all label candidates
        cfnd = False
        for cobj, cndx  in chosen_label:
            if cobj == obj:
                cfnd = True     # labels are alredy chosen for object 'obj'
                if index == cndx: break
        # skip further processing if some labels for other object are chosen ...
        #     .... but this isn't one of them
        if cfnd and index != cndx: continue

        date_min = d00 + timedelta(days=idx_min)
        date_max = d00 + timedelta(days=idx_max)
        if abs(labXY[0] - labXY0[0])/sf*10 > 45.0: continue
        if abs(labXY[1] - labXY0[1])/sf    > 1.5:  continue
        # overlap possible: the label centers are within 15 degrees or 45 calendar days

        # ||  to compare against UNROTATED object's label box limits:  ||
        # ||      rotate obj's coordinates by -ang0 about labXY0       ||
        x0, y0 = rxy[0]
        x1, y1 = rxy[1]
        x2, y2 = rxy[2]
        x3, y3 = rxy[3]
        rx0, ry0 = rotate_xy(x0, y0, labXY0[0], labXY0[1], -ang0)
        rx1, ry1 = rotate_xy(x1, y1, labXY0[0], labXY0[1], -ang0)
        rx2, ry2 = rotate_xy(x2, y2, labXY0[0], labXY0[1], -ang0)
        rx3, ry3 = rotate_xy(x3, y3, labXY0[0], labXY0[1], -ang0)
        # store rectangle in rxy0
        rxy0 = [[0.0, 0.0] for i in range(4)]    # rxy0[0 to 3][0 to 1]
        rxy0[0] = [rx0, ry0]
        rxy0[1] = [rx1, ry1]
        rxy0[2] = [rx2, ry2]
        rxy0[3] = [rx3, ry3]
        # DEBUGGING ONLY ... test orthogonal rectangle
        # rxy0[0] = [4.5, 0.5]
        # rxy0[1] = [5.0, 0.5]
        # rxy0[2] = [5.0, -0.2]
        # rxy0[3] = [4.5, -0.2]

        # not overlaid if all coordinates are above box top; below box bottom;
        #     left of box left edge; right of box right edge
        if min(ry0, ry1, ry2, ry3) > y0_max: continue
        if max(ry0, ry1, ry2, ry3) < y0_min: continue
        if min(rx0, rx1, rx2, rx3) > x0_max: continue
        if max(rx0, rx1, rx2, rx3) < x0_min: continue
        
        # easy to check:   the rectangles definitely overlap...
        # ...if one corner of rectangle rxy0 is within rectangle xy0
        overlap = False
        for xx, yy in rxy0:
            if x0_min < xx < x0_max and y0_min < yy < y0_max:
                overlap = True
                break

        if overlap:
            if config.debug_labels: print("rectangles overlap")
            badobj.append((index, obj, rxy0, tex))
            continue

        # define the 4 line segments of rectangle rxy0
        segments = [[[0.0, 0.0],[0.0, 0.0]] for i in range(4)]
        segments[0] = [rxy0[0], rxy0[1]]
        segments[1] = [rxy0[1], rxy0[2]]
        segments[2] = [rxy0[2], rxy0[3]]
        segments[3] = [rxy0[3], rxy0[0]]
        #print(segments)

        # ||  check if any line segment in rectangle rxy0 intersects  ||
        # ||  with a line segment in the orthogonal rectangle xy0     ||
        overlap = False

        # when debugging... a red dot indicates both rectangles intersect,
        # i.e. rectangles overlap ... and a blue dot is a projection of
        # only one rectangle (invalid for overlap testing)
        for seg in segments:
            intersect1 = intersect2 = intersect3 = intersect4 = False
            intersectH = intersectV = False
            seg_x0, seg_y0 = seg[0]
            seg_x1, seg_y1 = seg[1]
            if config.debug_labels:
                print("\nsegment: {:.2f},{:.2f} to {:.2f},{:.2f}".format(seg_x0, seg_y0, seg_x1, seg_y1))
            seg_xmin = min(seg_x0, seg_x1)
            seg_xmax = max(seg_x0, seg_x1)
            seg_ymin = min(seg_y0, seg_y1)
            seg_ymax = max(seg_y0, seg_y1)

            if seg_y1 == seg_y0:    # if segment is a horizontal line
                if y0_min < seg_y0 < y0_max:
                    if seg_xmin < x0_min < seg_xmax or seg_xmin < x0_max < seg_xmax:
                        intersectH = True
                    if config.debug_labels:
                        print("intersectH:",intersectH, y0_min, seg_y0, y0_max)
            else:
                # does it intersect with the y0_min segment of xy0?
                dx = (y0_min - seg_y0) * (seg_x1 - seg_x0) / (seg_y1 - seg_y0)
                if x0_min < seg_x0+dx < x0_max:
                    if seg_ymin < y0_min < seg_ymax: intersect1 = True
                    if config.debug_labels:
                        print("intersect1:",intersect1, x0_min, seg_x0+dx, x0_max)
                    tex += printdot2((seg_x0 + dx), y0_min, intersect1)
                # does it intersect with the y0_max segment of xy0?
                dx = (y0_max - seg_y0) * (seg_x1 - seg_x0) / (seg_y1 - seg_y0)
                if x0_min < seg_x0+dx < x0_max:
                    if seg_ymin < y0_max < seg_ymax: intersect2 = True
                    if config.debug_labels:
                        print("intersect2:",intersect2, x0_min, seg_x0+dx, x0_max)
                    tex += printdot2((seg_x0 + dx), y0_max, intersect2)

            if seg_x1 == seg_x0:    # if segment is a vertical line
                if x0_min < seg_x0 < x0_max:
                    if seg_ymin < y0_min < seg_ymax or seg_ymin < y0_max < seg_ymax:
                        intersectV = True
                    if config.debug_labels:
                        print("intersectV:",intersectV, x0_min, seg_x0, x0_max)
            else:
                # does it intersect with the x0_min segment of xy0?
                dy = (x0_min - seg_x0) * (seg_y1 - seg_y0) / (seg_x1 - seg_x0)
                if y0_min < seg_y0+dy < y0_max:
                    if seg_xmin < x0_min < seg_xmax: intersect3 = True
                    if config.debug_labels:
                        print("intersect3:",intersect3, y0_min, seg_y0+dy, y0_max)
                    tex += printdot2(x0_min, (seg_y0 + dy), intersect3)
                # does it intersect with the x0_max segment of xy0?
                dy = (x0_max - seg_x0) * (seg_y1 - seg_y0) / (seg_x1 - seg_x0)
                if y0_min < seg_y0+dy < y0_max:
                    if seg_xmin < x0_max < seg_xmax: intersect4 = True
                    if config.debug_labels:
                        print("intersect4:",intersect4, y0_min, seg_y0+dy, y0_max)
                    tex += printdot2(x0_max, (seg_y0 + dy), intersect4)

            if intersect1 or intersect2 or intersect3 or intersect4 or intersectH or intersectV:
                overlap = True
                break

        if overlap:
            if config.debug_labels: print("rectangles overlap")
            badobj.append((index, obj, rxy0, tex))

    return badobj

# ||====================================================================||
# ||                            DEFINITIONS                             ||
# ||  path           - all LMTMP data for a whole year for one object   ||
# ||                       (Sun/Mercury/Venus/Mars/Jupiter/Sarurn)      ||
# ||  path-segment   - LMTMP data between chart borders, i.e.           ||
# ||                      left / bottom / top / right - chart borders   ||
# ||  path-section   - LMTMP data between path crossing points of a     ||
# ||                   path-segment, i.e. where other object paths      ||
# ||                   cross over the object path-segment in question   ||
# ||====================================================================||

def merpass_intersections():
# collect all LMTMP path crossing intersections
#    (this is close to planet conjunctions)
# include MerPass 00h to 24h (or vice-versa) end points
#      (the path section also ends/begins here)
# LMTMP = Local Mean Time of Meridian Passage

    global meridian_pass, meridian_xidx, daystoprocess

    # return a list of tuples with these values per intersection:
    # [0] - n, the date offset from Jan 1
    # [1] - j, object 1 that intersects with ...
    # [2] - k, object 2 (k > j always)
    # [3] - jhour, the LMTMP (0.0 <= hour < 24.0) object 1
    # [4] - khour, the LMTMP (0.0 <= hour < 24.0) object 2

    all_n = []
    all_j = []
    all_k = []
    all_jhour = []
    all_khour = []
    prev_mpa = [None] * 6

    n = 0
    d_inc = d00
    # only half of the following 2D list is actually used ...
    prev_hilo = [[None for i in range(6)] for j in range(6)]

    # loop through all days of the year...
    while n <= daystoprocess:
        for j in range(6):
            MPAobj1 = meridian_pass[j][n]
            if n != 0:      # skip jan 1st
                if abs(MPAobj1 - prev_mpa[j]) > 20:
                    all_j.append(j)
                    all_k.append(None)  # 00h -> 24h switch
                    all_n.append(n-1)   # previous day...
                    all_jhour.append(meridian_pass[j][n-1])
                    all_khour.append(None)
            prev_mpa[j] = MPAobj1

            for k in range(j+1, 6):
                MPAobj2 = meridian_pass[k][n]
                MPAdiff = MPAobj1 - MPAobj2
                hilo = math.copysign(1.0, MPAdiff)  # +ve if path j is above k, else -ve
                if n != 0:      # skip jan 1st
                    # note: 'n-1' because hilo jumps on day 'n'
                    if n-1 in meridian_xidx[j] or n-1 in meridian_xidx[k]:
                        prev_hilo[j][k] = hilo  # ignore when planet LMTMP goes below 0h
                    if hilo != prev_hilo[j][k]:
                        # store only the previous day (before the paths cross)
                        all_j.append(j)
                        all_k.append(k)
                        all_n.append(n-1)   # previous day...
                        all_jhour.append(meridian_pass[j][n-1])
                        all_khour.append(meridian_pass[k][n-1])
                prev_hilo[j][k] = hilo

        n += 1
        d_inc += timedelta(days=1)

    tup = list(zip(all_n, all_j, all_k, all_jhour, all_khour))
    # a sort by date offset is no longer required ...
    #tup.sort(key = lambda x: x[0])  # sort by n, the date offset from Jan 1

    if config.debug_crossing:
        print()
        for i in range(len(tup)):
            idx, j, k, jhour, khour = tup[i]
            date0 = d00 + timedelta(days=idx)
            if k == None:
                print("{}   {:7} 0h->24h".format(date0,get_object_name(j)))
            else:
                print("{}   {:7}-{:7}".format(date0,get_object_name(j),get_object_name(k)))

    return tup

def twilight_intersections(obj, twiAM_Y, twiPM_Y, delta=0):
# collect all path crossings between the MPA of a celestial object
# and Civil Dawn(AM)/Dusk(PM) projected on the sun's MerPass near 12h.
# 'delta' (in hours) adds an offset from Civil Dawn/Dusk away from sunrise/sunset

    global meridian_pass, daystoprocess

    # for VISIBILITY OF PLANETS IN MORNING AND EVENING table ...
    # return two lists (morning & evening) of tuples with these values per intersection:
    # [0] - n, the date offset from Jan 1
    # [1] - vis, TRUE at beginning of visible range, else FALSE
    #    Jan 1  is added if vis = FALSE encountered first
    #    Dec 31 is added if vis = TRUE  encountered last

    # for VISIBILITY OF PLANETS text ...
    # return a third list of tuples with these values ordered chronologically:
    # [0] - n, the date offset from Jan 1
    # [1] - vis, TRUE at beginning of visible range, else FALSE
    # [2] - hour, the LMTMP (0.0 <= hour < 24.0) for the object
    # [3] - hour, the LMTMP (0.0 <= hour < 24.0) for the sun

    allAM_n = []
    allAM_vis = []
    allPM_n = []
    allPM_vis = []
    all_n = []
    all_vis = []
    all_hour = []
    all_sunh = []

    n = 0
    d_inc = d00
    prev_hiloAM = None
    prev_hiloPM = None
    prev_MPAobj = None

    # loop through all days of the year...
    while n < daystoprocess:

        MPAobj = meridian_pass[obj][n]
        # also detect if MPA flips 0h -> 24h
        AM2PM = True if n > 0 and MPAobj - prev_MPAobj > 23 else False
        AMdiff = MPAobj - twiAM_Y[n] + delta
        hiloAM = math.copysign(1.0, AMdiff)  # -ve if visible
        if n == 0:                  # if Jan 1st
            if hiloAM < 0:          # if initially visible
                allAM_n.append(n)
                allAM_vis.append(True)
                all_n.append(n)
                all_vis.append(True)
                all_hour.append(MPAobj)
                all_sunh.append(meridian_pass[0][n])
        elif n == daystoprocess-1:  # if Dec 31st
            if hiloAM < 0:          # if still visible
                allAM_n.append(n)
                allAM_vis.append(False)
                all_n.append(n)
                all_vis.append(False)
                all_hour.append(MPAobj)
                all_sunh.append(meridian_pass[0][n])
        else:
            if hiloAM != prev_hiloAM:
                vis = True if hiloAM < 0 else False
                idx = n if vis else n-1 # previous day if 'end of visibility'
                allAM_n.append(idx)
                allAM_vis.append(vis)
                all_n.append(idx)
                all_vis.append(vis)
                all_hour.append(prev_MPAobj if AM2PM else MPAobj)
                all_sunh.append(meridian_pass[0][n-1] if AM2PM else meridian_pass[0][n])

        prev_hiloAM = hiloAM

        PMdiff = MPAobj - twiPM_Y[n] - delta
        hiloPM = math.copysign(1.0, PMdiff)  # +ve if visible
        if n == 0:                  # if Jan 1st
            if hiloPM > 0:          # if initially visible
                allPM_n.append(n)
                allPM_vis.append(True)
                all_n.append(n)
                all_vis.append(True)
                all_hour.append(MPAobj)
                all_sunh.append(meridian_pass[0][n])
        elif n == daystoprocess-1:  # if Dec 31st
            if hiloPM > 0:          # if still visible
                allPM_n.append(n)
                allPM_vis.append(False)
                all_n.append(n)
                all_vis.append(False)
                all_hour.append(MPAobj)
                all_sunh.append(meridian_pass[0][n])
        else:
            if hiloPM != prev_hiloPM:
                vis = True if hiloPM > 0 else False
                idx = n if vis else n-1 # previous day if 'end of visibility'
                all_n.append(idx)       # --- correct here (ignore next line) ---
                if AM2PM: idx = n-1     # previous day if MPA flips 0h -> 24h
                allPM_n.append(idx)
                allPM_vis.append(vis)
                all_vis.append(vis)
                all_hour.append(MPAobj)
                all_sunh.append(meridian_pass[0][n])

        prev_hiloPM = hiloPM
        prev_MPAobj = MPAobj

        n += 1
        d_inc += timedelta(days=1)

    tupAM = list(zip(allAM_n, allAM_vis))
    tupPM = list(zip(allPM_n, allPM_vis))
    tup3  = list(zip(all_n, all_vis, all_hour, all_sunh))

    if config.debug_visibility:
        print("{}VIS:".format(get_object_name(obj)))
        for idx, vis, mpa, sunmpa in tup3:
            d1 = d00 + timedelta(days=idx)
            print("{:3d} {} {:5} {:5.2f}  {:5.2f}".format(idx,d1,str(vis),mpa,sunmpa))

    if config.debug_crossing:
        for i in range(len(tupAM)):
            idx, vis = tupAM[i]
            date0 = d00 + timedelta(days=idx)
            txt = "starts" if vis else "ends"
            print("{}   {:7}: morning visibility {}".format(date0,get_object_name(obj),txt))

        for i in range(len(tupPM)):
            idx, vis = tupPM[i]
            date0 = d00 + timedelta(days=idx)
            txt = "starts" if vis else "ends"
            print("{}   {:7}: evening visibility {}".format(date0,get_object_name(obj),txt))

    return tupAM, tupPM, tup3


def sunriseset_intersections(sunrise_Y, sunset_Y):
# collect all path crossings between sunrise/sunset paths at 51.5° N and the superior planets

    global meridian_pass, daystoprocess
    
    # return two lists of tuples with these values per intersection:
    # [0] - n, the date offset from Jan 1
    # [1] - j, the object that intersects with the sunrise/sunset path

    allAM_n = []
    allAM_j = []
    allPM_n = []
    allPM_j = []

    n = 0
    d_inc = d00
    prev_hiloAM = [None, None, None]    # for Mars, Jupiter, Saturn
    prev_hiloPM = [None, None, None]    # for Mars, Jupiter, Saturn
    prev_MPAobj = [None, None, None]    # for Mars, Jupiter, Saturn

    # loop through all days of the year...
    while n < daystoprocess:
        MPA_AM = sunrise_Y[n]
        MPA_PM = sunset_Y[n]

        for j in [0, 1, 2]:
            MPAobj = meridian_pass[j+3][n]  # only check Mars, Jupiter, Saturn
            # also detect if MPA flips 0h -> 24h
            AM2PM = True if n > 0 and MPAobj - prev_MPAobj[j] > 23 else False

            MPAdiff = MPAobj - MPA_AM
            hiloAM = math.copysign(1.0, MPAdiff)  # +ve if path j is above k, else -ve
            MPAdiff = MPAobj - MPA_PM
            hiloPM = math.copysign(1.0, MPAdiff)  # +ve if path j is above k, else -ve

            if n != 0 and not AM2PM:        # skip jan 1st; ignore 0h->24h flip
                if hiloAM != prev_hiloAM[j]:
                    allAM_n.append(n-1)     # previous day
                    allAM_j.append(j+3)
                if hiloPM != prev_hiloPM[j]:
                    allPM_n.append(n-1)     # previous day
                    allPM_j.append(j+3)

            prev_hiloAM[j] = hiloAM
            prev_hiloPM[j] = hiloPM
            prev_MPAobj[j] = MPAobj

        n += 1
        d_inc += timedelta(days=1)

    tupAM = list(zip(allAM_n, allAM_j))
    tupPM = list(zip(allPM_n, allPM_j))

    if config.debug_crossing:
        print()
        for i in range(len(tupAM)):
            idx, j = tupAM[i]
            date0 = d00 + timedelta(days=idx)
            print("{}   sunrise-{:7}".format(date0,get_object_name(j)))
        for i in range(len(tupPM)):
            idx, j = tupPM[i]
            date0 = d00 + timedelta(days=idx)
            print("{}   sunset -{:7}".format(date0,get_object_name(j)))

    return tupAM, tupPM
    
def sunrise_set_sections(tup, bylength=False):
# find longest sections between sunrise/sunset path crossing points.
#          Here is only ONE path SEGMENT.
# The section length is the x-axis separation between the two
#    crossing points ... in units '10 calendar days'.
    global daystoprocess
    sections_by_date = []
    from_idx = 0        # starting date offset for section
    o_fr = -1           # path section is from o_fr to o_to (-1 is chart border)
    
    # note: tup is sorted by increasing date offset from Jan 1
    for i in range(len(tup)):
        to_idx = tup[i][0]
        sec_len = (to_idx - from_idx)/10
        # append section data tuple...
        sections_by_date.append((sec_len, from_idx, to_idx))
        from_idx = to_idx   # prepare for next section

    to_idx = daystoprocess - 1
    # append final section up to Dec 31
    sec_len = (to_idx - from_idx)/10
    # if obj == 3: print(sec_len,"...",from_idx,to_idx,"...",mpa0,mpa)
    sections_by_date.append((sec_len, from_idx, to_idx))    # append tuple

    if bylength:
        # sect_by_len_list = sorted(sections_by_date)   # sort all ASC
        # sort by sec_len DESC, then by from_idx ASC
        sect_by_len_list = sorted(sections_by_date, key = lambda x:(-x[0],x[1]))
        # note: the 'sorted' function returns a list

        # return a list containing...
        #    a list of tuples (sec_len, from_idx, to_idx)
        # 1) sorted by sec_len ASC, the section length
        return sect_by_len_list

    # return a list of tuples (sec_len, from_idx, to_idx)
    # 2) sorted by from_idx, the section start date offset
    return sections_by_date


# the following function worked, however it is now abandoned...
def get_path_section(p_sections, min_len, idx_find):
# RECURSIVE funstion to return first/last path over specified length in days
# call it initially with either:
#        get_path_section(p_sections, 15, 0)
#        get_path_section(p_sections, -15, daystoprocess-1)
# to begin searching for first or last path section over 15 days in length.
# When found it returns the mid-idx date of the path.
# The sign of min_len determines the direction: +ve forwards; -ve backwards
# This works only if all path sections in p_sections are linked (end-to-start).

    if len(p_sections) == 0: return None
    #print(min_len, idx_find)

    for index, items in enumerate(p_sections):
        sec_len, from_idx, to_idx, obj8, obj9 = items
        idx_seek = from_idx if min_len > 0 else to_idx
        idx_next = from_idx if min_len < 0 else to_idx

        if idx_seek == idx_find:
            idx_len = to_idx - from_idx
            if idx_len >= abs(min_len):
                return from_idx + int(idx_len/2)
            idx_find = idx_next
            p_sections.pop(index)   # to avoid infinite recursion
            break
    else:   # loop ended without break
        return None     # all idx_find values must exist in p_sections

    # following break out of for loop ... here is the recursive call
    idx = get_path_section(p_sections, min_len, idx_find)
    # now return its value to the original caller...
    return idx

def path_sections(obj, tup, bylength=False):
# find longest sections between paths crossing the 'obj' path.
# The section length is the straight line length between the two
#    crossing points ...
# in units '10 calendar days' horizontally or 1 hour vertically.
    global meridian_pass, meridian_xidx, daystoprocess
    sections_by_date = []
    segments_by_date = []
    from_idx = 0        # starting date offset for section
    seg_from_idx = 0    # starting date offset for segment
    path_seg = 0        # path segment: 0, 1, ...
    mpa0 = meridian_pass[obj][0]
    seg_mpa0 = mpa0     # starting LMTMP for segment
    o_fr = -1           # path section is from o_fr to o_to (-1 is chart border)
    sections_prev_segs = 0  # count of sections in PREVIOUS segments
    
    # note: tup is sorted by increasing date offset from Jan 1
    for i in range(len(tup)):
        if tup[i][1] == obj or tup[i][2] == obj:
            k = 3 if tup[i][1] == obj else 4
            to_idx = tup[i][0]
            mpa = tup[i][k]
            sec_len = math.sqrt(((to_idx - from_idx)/10)**2 + (mpa - mpa0)**2)
            # if obj == 3: print(sec_len,"...",from_idx,to_idx,"...",mpa0,mpa)
            o_to = tup[i][1] if k == 4 else tup[i][2]    # other object
            # append section data tuple...
            sections_by_date.append((path_seg, sec_len, from_idx, to_idx, o_fr, o_to))
            from_idx = to_idx   # prepare for next section
            mpa0 = mpa          # prepare for next section
            if to_idx in meridian_xidx[obj]:
                # if planet crosses the 0h/24h border ...
                seg_len = math.sqrt(((to_idx - seg_from_idx)/10)**2 + (mpa - seg_mpa0)**2)  # calculate segment length
                seg_mid_idx = seg_from_idx + int((to_idx - seg_from_idx)/2)
                seg_mid_mpa = meridian_pass[obj][seg_mid_idx]
                sect_per_seg = len(sections_by_date) - sections_prev_segs
                sections_prev_segs = len(sections_by_date)
                # append segment data tuple...
                segments_by_date.append((seg_len, seg_mid_idx, seg_mid_mpa, sect_per_seg))
                # next segment...
                seg_from_idx = to_idx + 1
                # also switch to other side (lower->upper) of chart!
                mpa0 = meridian_pass[obj][to_idx + 1]
                seg_mpa0 = mpa0
                path_seg += 1   # next segment
            o_fr = o_to

    to_idx = daystoprocess - 1
    mpa = meridian_pass[obj][to_idx]

    # append final section up to Dec 31
    sec_len = math.sqrt(((to_idx-from_idx)/10)**2 + (mpa-mpa0)**2)
    # if obj == 3: print(sec_len,"...",from_idx,to_idx,"...",mpa0,mpa)
    sections_by_date.append((path_seg, sec_len, from_idx, to_idx, o_fr, -1))    # append tuple

    # append final segment up to Dec 31
    seg_len = math.sqrt(((to_idx - seg_from_idx)/10)**2 + (mpa - seg_mpa0)**2)
    seg_mid_idx = seg_from_idx + int((to_idx - seg_from_idx)/2)
    seg_mid_mpa = meridian_pass[obj][seg_mid_idx]
    sect_per_seg = len(sections_by_date) - sections_prev_segs
    sections_prev_segs = len(sections_by_date)
    # append segment data tuple...
    segments_by_date.append((seg_len, seg_mid_idx, seg_mid_mpa, sect_per_seg))
    
    if bylength:
        # sect_by_len_list = sorted(sections_by_date)   # sort all ASC
        # sort by path_seg ASC, sec_len DESC, then by from_idx ASC
        sect_by_len_list = sorted(sections_by_date, key = lambda x:(x[0],-x[1],x[2]))
        # note: the 'sorted' function returns a list
        pseg = 0
        sect_by_len = []
        sect_by_len_per_seg = []

        for item in sect_by_len_list:
            path_seg, sec_len, from_idx, to_idx, o_fr, o_to = item
            if pseg == path_seg:
                sect_by_len.append((sec_len, from_idx, to_idx, o_fr, o_to))
            else:
                sect_by_len_per_seg.append(tuple(sect_by_len))
                sect_by_len.clear()
                sect_by_len.append((sec_len, from_idx, to_idx, o_fr, o_to))
                pseg += 1

        sect_by_len_per_seg.append(sect_by_len)
        ##sections_by_length = tuple(sect_by_len_list)

        # return a list per segment containing...
        #    a list of tuples (sec_len, from_idx, to_idx, o_fr, o_to)
        # 1) sorted by sec_len DESC, the section length
        return segments_by_date, sect_by_len_per_seg
    
    # return a list of tuples (path_seg, sec_len, from_idx, to_idx, o_fr, o_to)
    # 2) sorted by from_idx, the section start date offset
    return segments_by_date, sections_by_date

def nearest_path_crossing(ref_idx, obj, tup):
# find the nearest path crossing to ref_idx for objects obj
    crossing_idx = []

    for i in range(len(tup)):
        if tup[i][1] == obj or tup[i][2] == obj:
            idx = tup[i][0]
            crossing_idx.append(idx)
    idx_diff_min = 1000
    idx_diff_val = -1

    for idx in crossing_idx:
        idx_diff = abs(ref_idx - idx)
        if idx_diff < idx_diff_min:
            idx_diff_min = idx_diff
            idx_diff_val = idx

    # return the nearest path crossing to ref_idx and the difference (in days)
    return idx_diff_val, idx_diff_min

def printlabelXY(txt, labXY, ang, c='Black', bgbox=True):
# print a label using XY coordinates and rotation angle

    debug = False
    #c = 'Black' if val else 'Red'   # print invalid labels RED
    rot = "%0.3f" %(ang*todegrees)
    if debug: rot = "0.0"   # print label text unrotated
    x0 = labXY[0]
    y0 = labXY[1]

    if bgbox:   # if a background box is required
        tex = r"""
  \settowidth{\myw}{\pgfinterruptpicture\fontfamily{phv}\%s{%s}\endpgfinterruptpicture}
  \settoheight{\myh}{\pgfinterruptpicture\fontfamily{phv}\%s{%s}\endpgfinterruptpicture}
  \settodepth{\myd}{\pgfinterruptpicture\fontfamily{phv}\%s{%s}\endpgfinterruptpicture}
  \setlength{\myl}{\myw}
  \addtolength{\myl}{1.6Pt} %% back color needs width extended by 2*boxsep""" %(navstar_fs, txt, navstar_fs, txt, navstar_fs, txt)

        # no anchor is equivalent to an anchor at center of text
        # opacityframe=1.0 shows a thin frame; =0.0 is invisible
        # boxsep > 0.0 adds padding around the text but causes "Overfull \hbox"
        tex += r"""
  \draw[color=Black] (%0.4f,%0.4f) node[rotate=%s,font=\%s]
  {\begin{tcolorbox}[standard jigsaw, size=minimal, colupper=%s, colback=white, opacityfill=1.0, opacityframe=0.0, width=\myl, boxsep=0.8pt]{\fontfamily{phv}\%s{%s}}\end{tcolorbox}};""" %(x0, y0, rot, navstar_fs, c, navstar_fs, txt)

    else:
        tex = r"""
  \draw[color=%s] (%0.4f,%0.4f) node[rotate=%s] {\fontfamily{phv}\%s{%s}};""" %(c, x0, y0, rot, navstar_fs, txt)

    return tex

def plot_rectangle(xy):
# draw a rectangle (for debugging purposes)

    tex = r"""
  \draw[ultra thin] ({:.4f},{:.4f}) -- ({:.4f},{:.4f}) -- ({:.4f},{:.4f}) -- ({:.4f},{:.4f}) -- cycle;
""".format(xy[0][0], xy[0][1], xy[1][0], xy[1][1], xy[2][0], xy[2][1], xy[3][0], xy[3][1])
    return tex

def printdot(xpos, ypos, tf= True):
    # x units in days; y units in hours
    c = 'red' if tf else 'blue'
    tex = r"""
  \fill[color={}] ({:.4f}, {:.4f}) circle (1pt);""".format(c, xpos*sf/10, ypos*sf)
    return tex

def printdot2(xpos, ypos, tf= True):
    # x in units '10 days'; y in units 'hours' (scaled)
    c = 'red' if tf else 'blue'
    tex = r"""
  \fill[color={}] ({:.4f}, {:.4f}) circle (1pt);""".format(c, xpos, ypos)
    return tex

def write_label_candidate(obj, idx, ang, label_ab=0):
# output a console message that a candidate label position has been found
# label_ab = 0 if label above path;   = 1 if below path

    if not verbose: return
    global planet_dec, label_ndx
    p = ['above', 'below']
    label_ndx += 1
    test_date = d00 + timedelta(days=idx)
    test_hour = meridian_pass[obj][idx]
    obj_name = get_object_name(obj)
    if obj <= 7: obj_name = obj_name.upper()    # cosmetic only
    print("   {:2d} {:7} (label {}) on {} MerPass {:6.2f} ang {:6.2f}°".format(label_ndx, obj_name, p[label_ab], test_date, test_hour, ang*todegrees))
    return

# <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> 
# <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> 
# <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> 

#--------------------------
#   external entry point
#--------------------------

#   This simple but effective function eliminates endless keyboard interrupts
#   each time Ctrl-C is issued, while none actually kill the parent process
#   ... and this causes the Command Prompt window (in Windows, MPmode=0) to hang.
def init_worker():
    # Prevent child process from ever receiving a KeyboardInterrupt.
    signal.signal(signal.SIGINT, signal.SIG_IGN)

def buildchart2(d0, dtp, lats, v, page1, ts):
# LOCAL MEAN TIME OF MERIDIAN PASSAGE  chart

    if config.MULTIpr:
        # Windows & macOS defaults to "spawn"; Unix to "fork"
        #mp.set_start_method("spawn")
        n = config.CPUcores
        if n > 12: n = 12   # use 12 cores maximum
        if (config.WINpf or config.MACOSpf) and n > 8: n = 8   # 8 maximum if Windows or Mac OS
        global pool
        pool = mp.Pool(n, init_worker)   # start 12 max. worker processes

    # define global VARIABLES
    global verbose
    verbose = v
    global d00
    d00 = d0        # initialize the starting date
    global label_ndx
    label_ndx = 0   # this must be reset
    global daystoprocess
    daystoprocess = dtp

    # tikz line thickness...
    # ultra thin    = 0.1pt
    # very thin     = 0.2pt
    # thin          = 0.4pt (default)
    # semithick     = 0.6pt
    # thick         = 0.8pt
    # very thick    = 1.2pt
    # ultra thick   = 1.6pt

    tex = ""

    print("\n       Creating Planet Diagram for {}".format(d0.year))
    if not page1:
        tex += r"""
\newpage"""

    tex += chart_LocalMeanTimeOfMeridianPassage(lats, ts)

# ------------- Text outside B O R D E R  lines -------------

    # txt = ""
    # n = 0       # output 4 maximum
    # # first output the navigational stars used as an LD target
    # for item in stars_LD:
        # if n > 3: break
        # if item[2]:         # if used as a LD object (connected to the Moon)
            # n += 1
            # txt += r"""\fontfamily{phv}\%s\color{airforceBlue}\textbf{%s}\fontfamily{cmr}\color{black}\%s = {%s}\quad""" %(navnum_fs,item[1],navstar_fs,item[0])

    # for item in stars_LD:
        # if n > 3: break
        # if not item[2]:     # if not used as a LD object (connected to the Moon)
            # n += 1
            # txt += r"""\fontfamily{phv}\%s\color{airforceBlue}\textbf{%s}\fontfamily{cmr}\color{black}\%s = {%s}\quad""" %(navnum_fs,item[1],navstar_fs,item[0])

    # if txt != "":
        # tex += r"""
  # \node[anchor=west] at (%0.3f,%0.3f) {%s};""" %(-sf/1.8,((decmin/10)-0.89)*sf,txt)    # ymin = decmin / 10

# -------------- terminate TikZ picture --------------

    tex += r"""
\end{tikzpicture}
\end{center}"""

    # A4/Letter landscape (center vertically)
    tex += r"""
  \vfill
  \hspace{0pt}"""

    if config.MULTIpr:
        pool.close()    # close all worker processes
        pool.join()

    return tex