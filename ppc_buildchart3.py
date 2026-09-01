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
import sys, time
from datetime import date, datetime, timedelta
import math
import signal       # for init_worker
#from inspect import currentframe, getframeinfo
#from collections import deque
from inspect import getframeinfo, stack

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
    from pp_skyfield import get_object_name, planet_mag, sunrise_set2, objrise_set3, planet_altitude, planet_elevation, rise_set
    # NOTE: although sunrise_set2 is NOT required in MULTI-PROCESSING mode
    #       it needs to be imported in case the value of config.MULTIpr is
    #       changed to 'False' dynamically via the '-sp' command-line option.
    # ... following is required for MULTI-PROCESSING:
    from mp_functions import mp_sunrise_set2, mp_objrise_set3
else:
    # ... following is required for SINGLE-PROCESSING:
    from pp_skyfield import get_object_name, planet_mag, sunrise_set2, objrise_set3, planet_altitude, planet_elevation, rise_set

#   My confession to those who read this . . .
#   Although use of global variables is frowned upon by the Python community,
#   I have chosen to employ global variables in this module to reduce the
#   number of arguments passed to some functions, so that the function
#   arguments focus on the frequently changing parameters.
#   A comment before a function describes which global variables are used.
#   . . . and Murphy whispered in his sleep "If it works, don't touch it"

# global VARIABLES
d00 = None
daysinyear = None
daystoprocess = None
# globals required in: getc, showLD, buildchart, printcname, addstar, addtext ...
shamin = shamax = sharng = None
decmin = decmax = None

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
msgKInt = "\nKeyboardInterrupt detected - multiprocessing aborted."

# Zodiac house signs from 0° to 360° ecliptic longitude at 30° intervals ...
House_Sign = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricornus', 'Aquarius', 'Pisces']

pt2cm = 1/28.45274  # 1cm = 28.45274 Pt
boxsep = 0.8        # Pt

pab = ['above', 'below']    # label position (above/below the declination path)
vab = [1.0, -1.0]           # label position hdiag multiplier for above/below

txt_text = [r"\textbf{Meridian Passage}",
 r"\textbf{MERCURY}",   r"\textbf{MERCURY rise}",   r"\textbf{MERCURY set}",
 r"\textbf{VENUS}",   r"\textbf{VENUS rise}",   r"\textbf{VENUS set}",
 r"\textbf{MARS}",    r"\textbf{MARS rise}",    r"\textbf{MARS set}",
 r"\textbf{JUPITER}", r"\textbf{JUPITER rise}", r"\textbf{JUPITER set}",
 r"\textbf{SATURN}",  r"\textbf{SATURN rise}",  r"\textbf{SATURN set}",
 r"\textbf{URANUS}",  r"\textbf{URANUS rise}",  r"\textbf{URANUS set}",
 r"\textbf{NEPTUNE}",  r"\textbf{NEPTUNE rise}",  r"\textbf{NEPTUNE set}"]
# txt_width  = [85.779, 42.3599, 62.92944, 59.58961]  # Jupiter rise,Mars rise(?),Saturn rise,Saturn set
# txt_height = [7.29498, 7.40997, 7.40997, 7.40997]
# txt_depth  = [2.16992, 0.18494, 0.18494, 0.18494]

sf = 1.0    # scale factor: dummy value - initialized in buildchart3()

# NOTE: the above code is executed when each worker process is created if multiprocessing is enabled.

def intro_PLANET_VISIBILITY(tm1,bm1,lm1,rm1):

    tex = r"""
\newpage
  % for the this page only...
  \newgeometry{{nomarginpar, top={}, bottom={}, left={}, right={}}}""".format(tm1,bm1,lm1,rm1)

    tex += r'''
  \setcounter{page}{2}      %% otherwise it's 1
  \thispagestyle{empty}     %% no page number
  \noindent
  \begin{center}
  \large\textbf{INTRODUCTION TO THE PLANET VISIBILITY CHARTS}\\[-6pt]
  \end{center}'''

    if config.pgsz == "Letter":
        tex += r'''
  \setlength{\columnsep}{18pt}'''
    else:
        tex += r'''
  \setlength{\columnsep}{20pt}'''

    tex += r'''
  \begin{multicols}{2}
  \normalsize\noindent
  The classic Planet Diagram\footnote{American Practical Navigator, Vol. 1 by Nathaniel Bowditch, 2017 Edition, page 256} shows the Local Mean Time of Meridian Passage of the Sun and five planets (two inferior and three superior). It does not provide useful information as to the actual visibility of the planets. Unlike stars, which have an inherent brightness, our planets only reflect the Sun's light and thus their magnitude (or brightness) is constantly changing, particularly with their distance from the Sun as they orbit the Sun in a near eliptical path (while we're doing the same on Earth). Planet visibility varies not only with a planet's current magnitude but also with the observer's location, specifically with the observer's latitude. Clearly a planet is not visible whenever it is below the horizon and neither when it is overpowered by the Sun's brightness, i.e. during daytime. Other miscellaneous factors also affect planet visibility.

  All these factors (and a few others) complicate the assessment of a planet's visibility. Generally one can assume that a planet will become visible soon after Civil Dusk and up to Civil Dawn when the Sun is again six degrees below the horizon. But a brighter planet is visible longer and dimmer planets possibly require the Sun to be around 12 degrees below the horizon, i.e. between Nautical Dusk and Dawn. The following diagrams illustrate when a planet is both above the horizon and when the Sun is at least six degrees below the horizon ... based on a chosen latitude.
  
  The classic Planet Diagram is printed in portrait orientation, however landscape orientation has been chosen for these charts. A day proceeds vertically upwards from midnight (at 00h) to midnight (at 24h). The days span a year horizontally from left to right. So any typical ``planet rise to Meridian Passage to planet set'' is a vertical line going upwards and often crosses midnight into the next day.
  
  The term ``Local Mean Time'' (LMT) to describe the vertical chart axis needs a little explanation. Local Mean Time originated before Time Zones were introduced when each town kept its own meridian such that locations one degree of longitude apart had times four minutes apart. LMT, as in the charts, applies to any location on Earth - it is independent of latitude and longitude. However no clock (apart from a sundial) shows LMT time. LMT maintains the same time along any meridian - it only changes with longitude.
  
  Time Zones, normally one hour apart, were introduced so that a whole region could share the same time. Thus Time Zones ideally jump by one hour every 15° of longitude and Greenwich in south-east London defines 0° longitude, also known as the prime meridian. So an appropriate correction must be applied when converting Civil Time to Local Mean Time, which depends on the observer's longitude. In practice this means that Civil Time is equivalent to LMT only at the central Time Zone reference longitudes that are 15° offset from the prime meridian, i.e. at 24 specific longitudes.
  
  Consider an observer in Cork, Ireland at longitude 8.5° West. A planet's Meridian Passing over Greenwich occurs earlier ... it will reach the upper meridian about 34 minutes later in Cork. This correction can be applied simply in the charts by reading 34 minutes higher than the Local Mean Time. No correction is required if you are on the central meridian of a Time Zone (that has 15° longitude width), i.e. at the \textit{standard meridian}.
  In practice no one will be at that ``ideal'' longitude, so a correction of up to ±30 minutes is to be applied depending on your actual location West (positive) or East (negative) of the Time Zone's central reference longitude.
  
  As an example, although Time Zone +1 in Europe stretches from Western Spain (9° 18' West) to Eastern Sweden (30° 55' East), the Local Mean Time on the chart will only match Civil Time at locations with longitude 15° East. A location in Time Zone +1 with longitude 7.5° East will have to add 30 minutes to the Local Mean Times on the chart.
  
  Time Zones which don't adhere to the 15° standard Time Zone boundary are special cases. Consider Reykjavik in Iceland (21° 57' West) ... officially in Time Zone Zero: here they need to add around 90 minutes to the Local Mean Times on the chart. Time Zones not on the hour (Marquesas Islands, Newfoundland, Cocos Islands, Myanmar, Lord Howe Island, Chatham Islands, ...) need further appropriate correction.
  
  In the following charts the planet's RISE and SET times are drawn as lines. A solitary RISE or SET is depicted as a small red (RISE) or blue (SET) cross. Grey shading shows when the planet is below the horizon, i.e. between planet SET and planet RISE. Of the remaining time, gold shading indicates that the Sun is too high (= too bright) for any planet to be seen. Unshaded areas show when the planet is likely to be visible. Civil Dawn and Civil Dusk (when the Sun is 6° below the horizon) is chosen to represent the zone during which any planet cannot be seen. The unshaded areas representing ``planet is visibile'' are always between planet RISE and SET as well as between Civil Dusk and Civil Dawn. A representative planet magnitude value is printed given sufficient space. Planet data is not printed orthogonally per day - the timeline on which the data is plotted is a helix, so that 24h on any day is vertically above 00h of the next day.
  
  The Visibility Charts are practical when using navigational planets — they clearly indicate the days or weeks when a planet is not visible at all (at that latitude) or for such a short time as to be impractical for taking sextant readings. More detailed information regarding Visibiliy Phenomena can be found on Rainer Lange's web pages\footnote{Visibility Phenomena - Rainer Lange: \url{http://www.alcyone.de/planetary_lunar_and_stellar_visibility.html}}. Acknowledgements\footnote{The charts are produced using Skyfield, an astronomical library from Brandon Rhodes: \url{https://rhodesmill.org/skyfield/}}
  \end{multicols}
'''

    tex += r'''
\restoregeometry    % so it does not affect the rest of the pages'''

    return tex

# oooooooooooooooooooooooooooooooooooooooooooooo
# oooooooooo PLANET VISIBILITY CHART ooooooooooo
# oooooooooooooooooooooooooooooooooooooooooooooo

def mp_sunrise_worker(Date, params, sf, ts, mth):
    #print(" mp_sunrise_worker Start {}".format(mth))
    # NOTE: 'sf' must be supplied as an argument - otherwise the next line executes with the default value of 1.0
    tup = mp_sunrise_set2(Date, mth, params, sf, ts)        # ===>>> mp_functions.py
    #print(" mp_sunrise_worker Finish {}".format(mth))
    return tup      # return tuple of list data for a month

def mp_obj5rise_worker(Date, params, ts, mth):
    #print(" mp_obj5rise_worker Start {}".format(mth))
    listoftup = mp_objrise_set3(Date, mth, params, sf, ts)  # ===>>> mp_functions.py
    #print(" mp_obj5rise_worker Finish {}".format(mth))
    return listoftup    # return list of tuples with data per day for a month

def chart_PLANET_VISIBILITY(obj, yy, lats, MPdata, ts):
    global tccdata

    datestr = d00.strftime("%d %b %Y")
    yearstr = d00.strftime("%Y")

    global xmax, ymax   # e.g. for function 'TA_bhor'
    global sha_ang      # rqrd for 'TA_set' & 'TA_rise'
    # parameters for 'A4/Letter Landscape'

    # A4/Letter landscape (center vertically)
    # https://tex.stackexchange.com/questions/2326/vertically-center-text-on-a-page

    tex = r"""
  \hspace{0pt}
  \vfill"""

    tex += r"""
\begin{center}                  % center picture horizontally
% ====== PLANET_VISIBILITY chart ======
\begin{tikzpicture}"""

    lat = "{:03.1f}".format(abs(lats))
    lns = 'N' if lats >= 0 else 'S'

    # make the following global to avoid passing it often as a function argument:
    global meridian_pass
    # unpack Meridian Passage data for the requested year ...
    meridian_pass, object_XY_txt, object_name, object_xidx, mp_offset = MPdata

# -------------------------------------------------------------------
# ----  draw chart vertical lines and label the horizontal axis  ----
# -------------------------------------------------------------------

    global dmax
    tex += r"""
% draw plot inner vertical lines..."""
    d_inc = d00
    extn = 1.25     # line extension (above and below)
    x = 0           # Jan 1
    dmax = daysinyear
    xmax = dmax / 10.0
    ymax = hmax
    ymin = hmin
    months = ['JANUARY','FEBRUARY','MARCH','APRIL','MAY','JUNE','JULY','AUGUST','SEPTEMBER','OCTOBER','NOVEMBER','DECEMBER']
    verticals = []  # collect date offsets for vertical lines
                    # (used for text annotations, vis_per_day(), Planet_Sun_Zone(), Planet_Vis_Zone())
    sha_ang = math.atan2(-ymax, xmax)     # radians (between -pi and pi)
    # print("   SHA angle = {:.3f}".format(sha_ang*todegrees))
    tex0 = ''

    while x <= dmax:
        DoM = int(d_inc.strftime("%d"))     # day of month
        if x == dmax or DoM in (1,11,21):
            # draw a vertical line
            e = extn if DoM == 1 else 0
            verticals.append(x)             # date offsets of vertical lines

            if config.orthogonal:
                tex += r"""
  \draw[ultra thin] ({:.3f},{:.3f}) -- ({:.3f},{:.3f});""".format(
x/10*sf,(ymin-e)*sf,x/10*sf,(ymax+e)*sf)

            else:
                if x == 0 or x == dmax:     # left or right chart border
                    tex += r"""
  \draw[ultra thin] ({:.3f},{:.3f}) -- ({:.3f},{:.3f});""".format(
x/10*sf,(ymin-e)*sf,x/10*sf,ymin*sf)
                    tex += r"""
  \draw[ultra thin] ({:.3f},{:.3f}) -- ({:.3f},{:.3f});""".format(
x/10*sf,ymax*sf,x/10*sf,(ymax+e)*sf)
                else:                       # vertical lines within chart
                    tex += r"""
  \draw[ultra thin] ({:.3f},{:.3f}) -- ({:.3f},{:.3f});""".format(
x/10*sf,(ymin-e)*sf,x/10*sf,(ymax+e)*sf)
                if x == 0:                  # left slanting chart border
                    tex += r"""
  \draw[ultra thin] ({:.3f},{:.3f}) -- ({:.3f},{:.3f});""".format(
x/10*sf,ymin*sf,(x+1)/10*sf,ymax*sf)
                if x == dmax:               # right slanting chart border
                    tex += r"""
  \draw[ultra thin] ({:.3f},{:.3f}) -- ({:.3f},{:.3f});""".format(
(x-1)/10*sf,ymin*sf,x/10*sf,ymax*sf)

        elif not config.orthogonal:
            # daily tickmarks (except 11th, 21st) on upper border
            tex0 += r""" ({:.3f},{:.3f}) -- ({:.3f},{:.3f})""".format(
x/10*sf,ymax*sf,x/10*sf,(ymax+(extn/20))*sf)

            # daily tickmarks (except 11th, 21st) on lower border
            tex0 += r""" ({:.3f},{:.3f}) -- ({:.3f},{:.3f})""".format(
x/10*sf,ymin*sf,x/10*sf,(ymin-(extn/20))*sf)


        MoY = int(d_inc.strftime("%m"))     # month of year
        if DoM == 1 and x != dmax:
            # month on lower axis
            mth = months[MoY-1]
            tex += r"""
  \node[font=\{}] at ({:.3f},{:.3f}) {{\scalebox{{.9}}[1.0]{{\textbf {{{}}}}}}};""".format(
star_fs,((x/10)+1.5)*sf,(ymin-1.0)*sf,mth)
            # '11th day of month' on lower axis
            tex += r"""
  \node[font=\{}] at ({:.3f},{:.3f}) {{\scalebox{{.9}}[1.0]{{{}}}}};""".format(
star_fs,((x/10)+1.0)*sf,(ymin-0.25)*sf,"11")
            # '21st day of month' on lower axis
            tex += r"""
  \node[font=\{}] at ({:.3f},{:.3f}) {{\scalebox{{.9}}[1.0]{{{}}}}};""".format(
star_fs,((x/10)+2.0)*sf,(ymin-0.25)*sf,"21")

            # month on upper axis
            tex += r"""
  \node[font=\{}] at ({:.3f},{:.3f}) {{\scalebox{{.9}}[1.0]{{\textbf {{{}}}}}}};""".format(
star_fs,((x/10)+1.5)*sf,(ymax+0.95)*sf,mth)
            # '11th day of month' on upper axis
            tex += r"""
  \node[font=\{}] at ({:.3f},{:.3f}) {{\scalebox{{.9}}[1.0]{{{}}}}};""".format(
star_fs,((x/10)+1.0)*sf,(ymax+0.25)*sf,"11")
            # '21st day of month' on upper axis
            tex += r"""
  \node[font=\{}] at ({:.3f},{:.3f}) {{\scalebox{{.9}}[1.0]{{{}}}}};""".format(
star_fs,((x/10)+2.0)*sf,(ymax+0.25)*sf,"21")

        x += 1
        d_inc += timedelta(days=1)

        if x == dmax or DoM in (1,11,21):   # dump the buffer containing tickmarks
            if tex0 != '':
                tex += r"""
  \draw[ultra thin] {};""".format(tex0)
                tex0 = ''
    # ----------------------------------------- end of 'while'

# -------------------------------------------------------------------
# ----  draw chart horizontal lines and label the vertical axis  ----
# -------------------------------------------------------------------

    tex += r"""
% draw plot inner horizontal lines..."""
    y = 0       # start at 00h
    xx = 0.0 if config.orthogonal else 1.0/24
    yy = 0 if config.orthogonal else 0.1

    while y <= ymax:
        # draw a horizontal line
        tex += r"""
  \draw[ultra thin] ({:.3f},{:.3f}) -- ({:.3f},{:.3f});""".format(
y*xx/10*sf,y*sf,(xmax-yy+(y*xx/10))*sf,y*sf)

        # left side "h" axis value
        tex += r"""
  \node[font=\{}] at ({:.3f},{:.3f}) {{\scalebox{{.8}}[1.0]{{{:02d}}}}};""".format(
ns_fs,-sf/3.0,y*sf,abs(y))

        # right side "h" axis value
        tex += r"""
  \node[font=\{}] at ({:.3f},{:.3f}) {{\scalebox{{.8}}[1.0]{{{:02d}}}}};""".format(
ns_fs,(xmax+1/3)*sf,y*sf,abs(y))

        # for regression testing only...
        if config.orthogonal:   # this was incorrectly placed inseide the while loop!
            # chart top and bottom horitontal line (chart border)
            tex += r"""
  \draw[ultra thin] ({:.3f},{:.3f}) -- ({:.3f},{:.3f});""".format(
0,(ymax+extn)*sf,xmax*sf,(ymax+extn)*sf)
            tex += r"""
  \draw[ultra thin] ({:.3f},{:.3f}) -- ({:.3f},{:.3f});""".format(
0,-extn*sf,xmax*sf,-extn*sf)

        y += 1      # 1 hour step
    # ----------------------------------------- end of 'while'

    if not config.orthogonal:
        # chart top and bottom horitontal line (chart border)
        tex += r"""
  \draw[ultra thin] ({:.3f},{:.3f}) -- ({:.3f},{:.3f});""".format(
0,(ymax+extn)*sf,xmax*sf,(ymax+extn)*sf)
        tex += r"""
  \draw[ultra thin] ({:.3f},{:.3f}) -- ({:.3f},{:.3f});""".format(
0,-extn*sf,xmax*sf,-extn*sf)

# -------------------------------------------------------------
# -------------  Text outside B O R D E R  lines  -------------
# -------------------------------------------------------------

    # chart title on the left side
    tex += r"""
% text outside border lines
  \node[rotate=90,font=\{}] at ({:.3f},{:.3f}) {{\textbf{{LOCAL MEAN TIME}}}};""".format(
navstar_fs,-1.6*sf,12*sf)

    # chart title on the right side
    tex += r"""
  \node[rotate=270,font=\{}] at ({:.3f},{:.3f}) {{\textbf{{LOCAL MEAN TIME}}}};""".format(
navstar_fs,(xmax+1.6)*sf,12*sf)

    # add the chart year  (ideally this should not shift/jog the chart itself,
    #    i.e. it's not the leftmost/rightmost or topmost item on the chart canvas)
    tex += r"""
  \node[font=\{}] at ({:.3f},{:.3f}) {{\fontfamily{{phv}}\color{{airforceBlue}}\textbf{{{}}}}};""".format(
title_fs,-0.95*sf,24.82*sf,yearstr)
    tex += r"""
  \node[font=\{}] at ({:.3f},{:.3f}) {{\fontfamily{{phv}}\color{{airforceBlue}}\textbf{{{}}}}};""".format(
title_fs,(xmax+0.95)*sf,-0.82*sf,yearstr)
    
    # add the chart latitude  (ideally this should not shift/jog the chart itself,
    #    i.e. it's not the leftmost/rightmost or topmost item on the chart canvas)
    tex += r"""
  \node[font=\{}] at ({:.3f},{:.3f}) {{\fontfamily{{phv}}\color{{airforceBlue}}\textbf{{{}°{}}}}};""".format(
"large",(xmax+0.95)*sf,24.82*sf,lat,lns)
    tex += r"""
  \node[font=\{}] at ({:.3f},{:.3f}) {{\fontfamily{{phv}}\color{{airforceBlue}}\textbf{{{}°{}}}}};""".format(
"large",(-0.95)*sf,-0.82*sf,lat,lns)

# -------------------------------------------------------------------------
# --------------  calculate sunrise/sunset & civil dawn/dusk  -------------
# -------------------------------------------------------------------------

    # pack the latitude and twilight value (degrees below horizon) into a tuple
    params = (lats, 6.0, config.orthogonal)

    global civilY_AM, civilY_PM, civil_AM_txt, civil_PM_txt         # for BHwidth etc.
    if config.MULTIpr:
        # multiprocess sunrise/sunset MP times per month simultaneously
        partial_func = partial(mp_sunrise_worker, d00, params, sf, ts)

        try:
            # RECOMMENDED: chunksize = 1
            listoftup = pool.map(partial_func, range(12), 1)
        except KeyboardInterrupt:
            print(msgKInt)
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
        sunrise_XY_txt, sunset_XY_txt, sunrise_Y, sunset_Y, civil_AM_txt, civil_PM_txt, civilY_AM, civilY_PM = sunrise_set2(d00,daystoprocess,params,sf)
        # print("civil_AM days",len(civil_AM_txt))
        # print(civil_AM_txt)
        # print("civil_PM days",len(civil_PM_txt))
        # print(civil_PM_txt)

# |----------------------------------------------------------|
# |----------------------------------------------------------|
# |-----  Get planet data and calculate chart metadata  -----|
# |----------------------------------------------------------|
# |----------------------------------------------------------|

# ---------------------------------------------------------------
# --------------  calculate planet rise/set times  --------------
# ---------------------------------------------------------------

    # note: 'planet all day above/below horizon' is only handled in INFERIOR planet logic.
    # obj = 5     # Saturn
    # obj = 4     # Jupiter
    # obj = 3     # Mars
    # obj = 2     # Venus
    # obj = 1     # Mercury
    # sup_obj = 6 # superior planets begin with 'sup_obj'

    def patchdata(nn, val):
        rs_time, is_rise, is_true = corrected_events[nn[0]]
        is_true[nn[1]] = val
        corrected_events[nn[0]] = (rs_time, is_rise, is_true)

    global objn     # for 'flush_AMbuf()', 'flush_PMbuf()'
    objs = get_object_name(obj)         # lowercase
    objn = objs[0].upper() + objs[1:]   # first letter capitalized
    obju = objs.upper()                 # uppercase

    global rise_offset, set_offset, objrise_XY_txt, objset_XY_txt, plotrise_XY_txt, plotset_XY_txt
    objrise_XY_txt = []
    objset_XY_txt = []
    plotrise_XY_txt = []
    plotset_XY_txt = []
    rise_offset = []
    set_offset = []

##    # global variables for LOWER_forw, UPPER_back
##    global g_idx, g_c, g_Y, g_rise_seg, g_ab_MP, g_set_seg

    # pack the planet, the latitude and orthogonal data (True/False) into a tuple
    # (note that if data is changed in config.py, it is not picked up when multiprocessing)
    params = (obj, lats, config.orthogonal)

    global objrise_Y, objset_Y
    if config.MULTIpr:
        # multiprocess sunrise/sunset MP times per month simultaneously
        partial_func = partial(mp_obj5rise_worker, d00, params, ts)

        try:
            # RECOMMENDED: chunksize = 1
            listoflists = pool.map(partial_func, range(12), 1)
        except KeyboardInterrupt:
            print(msgKInt)
            sys.exit(0)

        # assemble the multiprocessed results into lists of data for all days in the year...
        data_per_year = []
        prev_ndx = None
        for data_per_month in listoflists:
            curr_ndx, _, _, _ = data_per_month[0]
            #i, daily_riseset_time, daily_isrise, daily_isTrue = data_per_month
            if prev_ndx is not None:
                if curr_ndx < prev_ndx:
                    print("ERROR: multiprocessing chunks not in sequence")
                    sys.exit(0)
            prev_ndx = curr_ndx
            data_per_year.extend(data_per_month)
        # ----------------------------------------- end of 'for'

    else:
        data_per_year = objrise_set3(d00,daystoprocess,params)

# --------------------------------------------------------------------------------
# --------------  data consistency check (see Skyfield ISSUE #998)  --------------
# --------------------------------------------------------------------------------

    dt = datetime(d00.year, d00.month, d00.day, 0, 0, 0)  # convert to datetime
    idx = 0
    pl_name = ['Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune']
    patch_msg = "ISSUE 998:  " + pl_name[obj]
    fail_msg = "ERROR: missing previous planet-event"
    aboveHorizon_tracked = None     # track 'above horizon' state
    last_true_dt0 = None; last_false_dt0 = None
    last_true_rs = ""; last_false_rs = ""
    last_true_event = [None, None]; last_false_event = [None, None]
    corrected_events = [([], [], [])] * daystoprocess   # ([riseset_time], [isrise], [isTrue])

    while idx < daystoprocess:

        _, riseset_time, isrise, isTrue = data_per_year[idx]
        no_events = False

        if len(riseset_time) == 2 and not isTrue[0] and not isTrue[1]:
            # if RISE == SET and both are False..... which is the case
            #     if the planet is entirely above or below the horizon
            if riseset_time[0] == riseset_time[1] and isrise[0] != isrise[1]:

                # Note: there are two cases for no events within one day:
                # usually - one false RISE and one false SET with the identical datetime
                # rare    - no RISE or SET, e.g. Mercury at 71°N on 1972-06-05
                no_events = True
                dtX = riseset_time[0]

                planet_elev, above_horizon = planet_elevation(obj, dtX, lats)
                #prnt("{} elevation at {} = {:.5f}; above horizon: {}".format(pl_name[obj],dtX.utc_iso(' '),planet_elev,above_horizon))
                
                if aboveHorizon_tracked is None:
                    aboveHorizon_tracked = above_horizon
                elif aboveHorizon_tracked != above_horizon:
                    if last_true_dt0 is not None:
                        prnt("{} {} {}     True -> False".format(patch_msg, last_true_rs, last_true_dt0.utc_iso(' ')))
                        patchdata(last_true_event, False)   # patch corrected data...
                        aboveHorizon_tracked = above_horizon
                    else:
                        print(fail_msg, dt.strftime("%Y-%b-%d"),"    True -> False FAILED!")
                        sys.exit(0)

                # clear all previous event references once we enter "all day above/below horizon" correctly
                last_true_dt0  = None; last_true_event  = [None, None]; last_true_rs  = ""
                last_false_dt0 = None; last_false_event = [None, None]; last_false_rs = ""
                
        if not no_events:

            # scan day's events in chronological order checking for logical consistency
            # and patch the data if necessary

            for ndx, dt0 in enumerate(riseset_time):
                rs = "  rise" if isrise[ndx] else "  set "
                #prnt(rs,dt0.utc_iso(' '),"   ",isTrue[ndx])

                if isTrue[ndx]:     # if it is a TRUE event
                    last_true_dt0 = dt0; last_true_rs = rs; last_true_event = [idx, ndx]

                    if aboveHorizon_tracked is None:
                        # initialize aboveHorizon state on first event
                        if isrise[ndx]: # true RISE event
                            aboveHorizon_tracked = True
                        else:           # true SET event
                            aboveHorizon_tracked = False

                    elif isrise[ndx]: # true RISE event
                        if not aboveHorizon_tracked:
                            aboveHorizon_tracked = True     # now above horizon

                        elif last_false_dt0 is not None:
                            prnt("{} {} {}     False -> True".format(patch_msg, last_false_rs, last_false_dt0.utc_iso(' ')))
                            if last_false_event[0] == idx:
                                isTrue[last_false_event[1]] = True  # patch one of today's events
                            else:
                                patchdata(last_false_event, True)   # patch into corrected data...
                            last_false_dt0 = None; last_false_event = [None, None]; last_false_rs = ""

                        elif last_true_dt0 is not None:
                            prnt("{} {} {}     True -> False".format(patch_msg, last_true_rs, last_true_dt0.utc_iso(' ')))
                            if last_true_event[0] == idx:
                                isTrue[last_true_event[1]] = False  # patch one of today's events
                            else:
                                patchdata(last_true_event, False)   # patch into corrected data...
                            last_true_dt0 = None; last_true_event = [None, None]; last_true_rs = ""

                        else:
                            print(fail_msg, dt.strftime("%Y-%b-%d"),"    True -> False FAILED!")
                            sys.exit(0)

                    else:           # true SET event
                        if aboveHorizon_tracked:
                            aboveHorizon_tracked = False    # now below horizon

                        elif last_false_dt0 is not None:
                            prnt("{} {} {}     False -> True".format(patch_msg, last_false_rs, last_false_dt0.utc_iso(' ')))
                            if last_false_event[0] == idx:
                                isTrue[last_false_event[1]] = True  # patch today's event
                            else:
                                patchdata(last_false_event, True)   # patch corrected data...
                            last_false_dt0 = None; last_false_event = [None, None]; last_false_rs = ""

                        else:
                            print(fail_msg, dt.strftime("%Y-%b-%d"),"    False -> True FAILED!")
                            sys.exit(0)

                else:               # if it is a FALSE event
                    last_false_dt0 = dt0; last_false_rs = rs; last_false_event = [idx, ndx]
            # ----------------------------------------- end of 'for'
                
        # store daily corrected rise/set data as tuple of three lists
        corrected_events[idx] = (riseset_time, isrise, isTrue)

        idx += 1
        dt += timedelta(days=1)
    # ----------------------------------------- end of 'while'

# -----------------------------------------------------
# --------------  obtain XY coordinates  --------------
# -----------------------------------------------------

    # For the given year, calculate these values:
    #   pertaining to sunrise/sunset times at 51.5°N 0.0°E:
    # objrise_XY_txt[seg][i]  = planet rise scaled XY coordinates as text (orthogonal data)
    # objset_XY_txt[seg][i]   = planet set  scaled XY coordinates as text (orthogonal data)
    # plotrise_XY_txt[seg][i] = planet rise scaled XY coordinates as text (orthogonal/helix data)
    # plotset_XY_txt[seg][i]  = planet set  scaled XY coordinates as text (orthogonal/helix data)
    # objrise_Y[idx]    = planet rise Y coordinate (unscaled) or list
    # objset_Y[idx]     = planet set  Y coordinate (unscaled) or list
    # rise_offset[seg]  = first idx value per RISE segment: objriseY[seg][0]
    # set_offset[seg]   = first idx value per SET  segment: objsetY[seg][0]

    # create objrise_Y, riseDays from dt_rise
    # create objset_Y, setDays from dt_set
    idx = 0
    objrise_Y = []      # planet rise Y coordinate (unscaled) or list
    objset_Y  = []      # planet set  Y coordinate (unscaled) or list
    riseDays  = []      # segment span in days (= array length - 1)
    setDays   = []      # segment span in days (= array length - 1)
    segAM = -1          # uninitialized
    segPM = -1          # uninitialized
    prev_hourAM = prev_hourPM = None
    segAM_active = False
    segPM_active = False

    global RS_events    # for isRISEhighestSEG()
    RS_events = [([], [], [])] * daystoprocess  # ([isRise], [segnum], [segoffset])
    # RS_events:  collect a list of tuples per day - filtered by True events only -
    #             containing all RISE & SET events per day in chronological order
    #             with the (RISE or SET) segment number and offset within.
    #
    #       (This data is useful later when deciding if the gold boundary to be
    #        shaded may extend to DAWN or DUSK, otherwise to the chart upper 'T'
    #        or lower 'B' border during noDAWN/noDUSK,
    #        i.e. is there any other segment in the way?)

    while idx < daystoprocess:  # includes 1st Jan of next year (for an orthogonal data plot only)

        rs_time, is_rise, isTrue = corrected_events[idx]    # daily events (True and False)
        riseset_time = []; isrise = []                      # prepare new daily lists
        seg_num = []; seg_off = []              # prepare new daily lists
        rise_ndx = []; set_ndx = []             # offsets to each RISE or SET within daily lists

        # filter out False events... (rise_set() requires True events only)
        n = 0       # offset within daily lists, e.g. isrise[]
        for index, dt0 in enumerate(rs_time):
            if isTrue[index]:
                riseset_time.append(dt0)
                isrise.append(is_rise[index])
                # for RS_events ......
                if is_rise[index]: rise_ndx.append(n)
                else: set_ndx.append(n)
                seg_num.append(-1)
                seg_off.append(-1)
                n += 1

        dt_rise, dt_set, fs = rise_set(riseset_time, isrise, lats)

        hoursAM = []
        index = None
        new_segAM = False
        nAM = 0     # for RS_events

        for index, dt0 in enumerate(dt_rise):
            doy = dt0.timetuple().tm_yday - 1       # day of year (counting from 0, like idx)
            if dt0.year > d00.year: doy = dmax+doy  # if 1st Jan of next year (orthogonal chart only)
            if doy != idx:
                print("RISE buffer overflow {}-{:02d}-{:02d}".format(dt0.year,dt0.month,dt0.day)); sys.exit(0)
                #rise_buffer.append(dt0)
                #continue
            #print("{:3d} RISE: {}".format(idx,dt0.strftime("%Y-%b-%d %H:%M:%S")))
            hourAM = dt0.hour + dt0.minute/60 + dt0.second/3600
            if not segAM_active:    # initialize a RISE segment
                new_segAM = True
                segAM_active = True
            elif prev_hourAM is not None and abs(hourAM - prev_hourAM) > 23:
                new_segAM = True
                nAM += 1        # for RS_events
            if new_segAM:
                new_segAM = False
                segAM += 1
                #objrise_XY_txt.append([])    # create a new line segment
                #plotrise_XY_txt.append([])   # create a new line segment
                #rise_offset.append(idx)
                riseDays.append(-1)
                #riseseg_Ymax.append(hourAM)
                #riseseg_Ymin.append(hourAM)
            xy_txt  = "(%04.3f, %04.3f)" %(idx*sf/10, hourAM*sf)
            #objrise_XY_txt[segAM].append(xy_txt)     # XY scaled coordinates of planet RISE
            if not config.orthogonal:
                x = idx + (hourAM/24.0)
                xy_txt  = "(%04.3f, %04.3f)" %(x*sf/10, hourAM*sf)
            #plotrise_XY_txt[segAM].append(xy_txt)    # XY scaled coordinates of planet RISE

            riseDays[segAM] += 1            # count span (not length)
            hoursAM.append(hourAM)
            #if hourAM > riseseg_Ymax[segAM]: riseseg_Ymax[segAM] = hourAM
            #if hourAM < riseseg_Ymin[segAM]: riseseg_Ymin[segAM] = hourAM
            prev_hourAM = hourAM
            # for RS_events .....
            seg_num[rise_ndx[nAM]] = segAM
            seg_off[rise_ndx[nAM]] = riseDays[segAM]
        # ----------------------------------------- end of 'for'

        # append one list item ('None', value or list) per day (= 'idx' value)
        if index is None:
            objrise_Y.append(None)           # if no values
            segAM_active = False
        elif index == 0:
            objrise_Y.append(hoursAM[0])     # append value
        else:
            objrise_Y.append(hoursAM)        # append list if > 1 value

        # . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 
        hoursPM = []
        index = None
        new_segPM = False
        nPM = 0     # for RS_events

        for index, dt1 in enumerate(dt_set):
            doy = dt1.timetuple().tm_yday - 1       # day of year (counting from 0, like idx)
            if dt1.year > d00.year: doy = dmax+doy  # if 1st Jan of next year (orthogonal chart only)
            if doy != idx:
                print("SET buffer overflow {}-{:02d}-{:02d}".format(dt0.year,dt0.month,dt0.day)); sys.exit(0)
                #set_buffer.append(dt0)
                #continue
            #print("{:3d}  SET: {}".format(idx,dt1.strftime("%Y-%b-%d %H:%M:%S")))
            hourPM = dt1.hour + dt1.minute/60 + dt1.second/3600
            if not segPM_active:    # initialize a SET segment
                new_segPM = True
                segPM_active = True
            elif prev_hourPM is not None and abs(hourPM - prev_hourPM) > 23:
                new_segPM = True
                nPM += 1        # for RS_events
            if new_segPM:
                new_segPM = False
                segPM += 1
                #objset_XY_txt.append([])    # create a new line segment
                #plotset_XY_txt.append([])   # create a new line segment
                #set_offset.append(idx)
                setDays.append(-1)
                #setseg_Ymax.append(hourPM)
                #setseg_Ymin.append(hourPM)
            xy_txt  = "(%04.3f, %04.3f)" %(idx*sf/10, hourPM*sf)
            #objset_XY_txt[segPM].append(xy_txt)     # XY scaled coordinates of planet SET
            if not config.orthogonal:
                x = idx + (hourPM/24.0)
                xy_txt  = "(%04.3f, %04.3f)" %(x*sf/10, hourPM*sf)
            #plotset_XY_txt[segPM].append(xy_txt)    # XY scaled coordinates of planet SET

            setDays[segPM] += 1             # count span (not length)
            hoursPM.append(hourPM)
            #if hourPM > setseg_Ymax[segPM]: setseg_Ymax[segPM] = hourPM
            #if hourPM < setseg_Ymin[segPM]: setseg_Ymin[segPM] = hourPM
            prev_hourPM = hourPM
            # for RS_events .....
            seg_num[set_ndx[nPM]] = segPM
            seg_off[set_ndx[nPM]] = setDays[segPM]
        # ----------------------------------------- end of 'for'

        # append one list item ('None', value or list) per day (= 'idx' value)
        if index is None:
            objset_Y.append(None)            # if no values
            segPM_active = False
        elif index == 0:
            objset_Y.append(hoursPM[0])      # append value
        else:
            objset_Y.append(hoursPM)         # append list if > 1 value

        RS_events[idx] = (isrise, seg_num, seg_off)
        idx += 1
    # ----------------------------------------- end of 'while'

##    for m in range(190,204):
##        print("   ",m,"  ",RS_events[m])

# -------------------------------------------------------
#                convert objrise_Y into...
#     objrise_XY_txt, plotrise_XY_txt, rise_offset,
#     riseseg_Ymax, riseseg_Ymin
# -------------------------------------------------------

    global riseseg_Y, setseg_Y      # for get_Y()
    objrise_XY_txt = []     # RISE orthogonal coordinates
    objset_XY_txt = []      #  SET orthogonal coordinates
    plotrise_XY_txt = []    # RISE coordinates to plot (orthogonal or helix)
    plotset_XY_txt = []     #  SET coordinates to plot (orthogonal or helix)
    rise_offset = []        # RISE starting date offset per 'objrise_XY_txt' segment
    set_offset = []         #  SET starting date offset per 'objset_XY_txt' segment
    hourRISE = []           # RISE time per segment per day
    hourSET = []            #  SET time per segment per day
    riseseg_Y = []          # RISE time per segment per day truncated to 3 decimal places
    setseg_Y = []           #  SET time per segment per day truncated to 3 decimal places
    riseseg_Ymax = []
    riseseg_Ymin = []
    setseg_Ymax = []
    setseg_Ymin = []
    segAM = -1          # uninitialized
    segPM = -1          # uninitialized
    segAM_active = False
    segPM_active = False
    prev_hourAM = prev_hourPM = None

    for idx, item in enumerate(objrise_Y):
        hoursAM = item if type(item) is list else [item]
        #if len(hoursAM) != 1 or hoursAM[0] == None:
        #    print("RISE len = {} on idx {}".format(len(hoursAM),idx))
        if hoursAM[0] is None:
            segAM_active = False
            #print("segAM_active FALSE")
            continue

        for hourAM in hoursAM:
            if not segAM_active:            # initialize an AM segment
                segAM += 1
                objrise_XY_txt.append([])   # create a new line segment
                plotrise_XY_txt.append([])  # create a new line segment
                hourRISE.append([])         # create a new line segment
                riseseg_Y.append([])        # create a new line segment
                rise_offset.append(idx)
                riseseg_Ymax.append(hourAM)
                riseseg_Ymin.append(hourAM)
                segAM_active = True
            elif prev_hourAM is not None and abs(hourAM - prev_hourAM) > 23:
                segAM += 1
                objrise_XY_txt.append([])   # create a new line segment
                plotrise_XY_txt.append([])  # create a new line segment
                hourRISE.append([])         # create a new line segment
                riseseg_Y.append([])        # create a new line segment
                rise_offset.append(idx)
                riseseg_Ymax.append(hourAM)
                riseseg_Ymin.append(hourAM)
            xy_txt  = "(%04.3f, %04.3f)" %(idx*sf/10, hourAM*sf)
            objrise_XY_txt[segAM].append(xy_txt)    # XY scaled coordinates of planet RISE
            hourRISE[segAM].append(hourAM)  # rise time
            riseseg_Y[segAM].append(round(hourAM,3))    # rise time rounded to 3 decimal places
            if not config.orthogonal:
                x = idx + (hourAM/24.0)
                xy_txt  = "(%04.3f, %04.3f)" %(x*sf/10, hourAM*sf)
            plotrise_XY_txt[segAM].append(xy_txt)   # XY scaled coordinates of planet RISE
            if hourAM > riseseg_Ymax[segAM]: riseseg_Ymax[segAM] = hourAM
            if hourAM < riseseg_Ymin[segAM]: riseseg_Ymin[segAM] = hourAM
            prev_hourAM = hourAM
        # ----------------------------------------- end of 'for'
    # ----------------------------------------- end of 'for'

# -------------------------------------------------------
#                convert objset_Y into...
#     objset_XY_txt, plotset_XY_txt, set_offset,
#     setseg_Ymax, setseg_Ymin
# -------------------------------------------------------

    for idx, item in enumerate(objset_Y):
        hoursPM = item if type(item) is list else [item]
        #if len(hoursPM) != 1 or hoursPM[0] is None:
        #    print("SET  len = {} on idx {}".format(len(hoursPM),idx))
        if hoursPM[0] is None:
            segPM_active = False
            #print("segPM_active FALSE")
            continue

        for hourPM in hoursPM:
            if not segPM_active:            # initialize a PM segment
                segPM += 1
                objset_XY_txt.append([])    # create a new line segment
                plotset_XY_txt.append([])   # create a new line segment
                hourSET.append([])          # create a new line segment
                setseg_Y.append([])         # create a new line segment
                set_offset.append(idx)
                setseg_Ymax.append(hourPM)
                setseg_Ymin.append(hourPM)
                segPM_active = True
            elif prev_hourPM is not None and abs(hourPM - prev_hourPM) > 23:
                segPM += 1
                objset_XY_txt.append([])    # create a new line segment
                plotset_XY_txt.append([])   # create a new line segment
                hourSET.append([])          # create a new line segment
                setseg_Y.append([])         # create a new line segment
                set_offset.append(idx)
                setseg_Ymax.append(hourPM)
                setseg_Ymin.append(hourPM)
            xy_txt  = "(%04.3f, %04.3f)" %(idx*sf/10, hourPM*sf)
            objset_XY_txt[segPM].append(xy_txt)    # XY scaled coordinates of planet SET
            hourSET[segPM].append(hourPM)  # set time
            setseg_Y[segPM].append(round(hourPM,3))    # set time rounded to 3 decimal places
            if not config.orthogonal:
                x = idx + (hourPM/24.0)
                xy_txt  = "(%04.3f, %04.3f)" %(x*sf/10, hourPM*sf)
            plotset_XY_txt[segPM].append(xy_txt)   # XY scaled coordinates of planet SET
            if hourPM > setseg_Ymax[segPM]: setseg_Ymax[segPM] = hourPM
            if hourPM < setseg_Ymin[segPM]: setseg_Ymin[segPM] = hourPM
            prev_hourPM = hourPM
        # ----------------------------------------- end of 'for'
    # ----------------------------------------- end of 'for'
    # -------------------------------------------------------------------------------

    prnt("   .   .   .   .   .   .   .   .   .   .  collect Metadata  .   .   .   .   .   .   .   .   .   .")
    prnt("days in year: {}   days to process: {}".format(daysinyear,daystoprocess))

    if config.debug_Rsegments:
        for segnum, rise_seg in enumerate(objrise_XY_txt):
            print("RISE segment {}".format(segnum))
            n = 0
            for xy in rise_seg:
                x1,y1 = tikzXY(xy)
                idx = int((x1+0.01)*10/sf)  # convert to day offset
#                print("   {:6} {:6.3f}".format(DOY(idx),y1),end = '')
                print("   {:6.3f} {:6.3f}".format(x1,y1),end = '')
                n += 1
                if n % 5 == 0: print()
            # ----------------------------------------- end of 'for'
            if n % 5 != 0: print()
        # ----------------------------------------- end of 'for'

    if config.debug_Ssegments:
        for segnum, set_seg in enumerate(objset_XY_txt):
            print("SET segment {}".format(segnum))
            n = 0
            for xy in set_seg:
                x1,y1 = tikzXY(xy)
                idx = int((x1+0.01)*10/sf)  # convert to day offset
                print("   {:6} {:6.3f}".format(DOY(idx),y1),end = '')
                n += 1
                if n % 5 == 0: print()
            # ----------------------------------------- end of 'for'
            if n % 5 != 0: print()
        # ----------------------------------------- end of 'for'

    # print("'objrise_XY_txt' RISE segment offsets: ",rise_offset, end=" ")
    # print(" days per segment:", end=" ")
    # for i in range(len(objrise_XY_txt)):
        # print(len(objrise_XY_txt[i]),end=" ")

# ---------------------------------------------------------------------------------
# --------------  build simple lists based on RISE and SET segments  --------------
# ---------------------------------------------------------------------------------

    global rise_days, rise_starts, rise_ends    # for fill_below_horizon()
    rise_days = []      # build list of RISE segment span in days
    rise_range = []     # build list of RISE 'range(from, to)' date offsets
    solitary_RISE_seg = []    # collect solitary RISE segments
    solitary_RISE_at_00h = []   # collect solitary RISE events at 00h
    solitary_RISE_at_24h = []   # collect solitary RISE events at 24h
    rise_starts = []    # days on which a RISE segment starts
    rise_ends = []      # days on which a RISE segment ends

    for ndx, idx in enumerate(rise_offset):
        lnth = len(objrise_XY_txt[ndx])
        ldx = idx + lnth - 1
        rise_days.append(ldx-idx)
        rise_range.append(range(idx,idx+lnth))  # last value is excluded from the range!
        prnt("RISE segment {} offset: {:3d} = {:6} to {:3d} = {:6}, length {:3d} (spans {} days)".format(ndx,idx,DOY(idx),ldx,DOY(ldx),lnth,lnth-1))
        if lnth == 1:
            solitary_RISE_seg.append(ndx)
            xR,yR = getXY(objrise_XY_txt[ndx][0])   # start of RISE
            if yR < 0.6:  solitary_RISE_at_00h.append(xR)
            if yR > 23.4: solitary_RISE_at_24h.append(xR)
        rise_starts.append(idx)
        rise_ends.append(ldx)

    if verbose:
        print("   max hour per RISE segment:", end=" ")
        for item in riseseg_Ymax: print("  {:6.3f}".format(item), end="")
        print("\n   min hour per RISE segment:", end=" ")
        for item in riseseg_Ymin: print("  {:6.3f}".format(item), end="")
        print()

    #print("RISE range: ",rise_range)
    # idx = rise_offset[0]
    # for index, item in enumerate(objrise_XY_txt[0]):
        # print(idx+index, item)

    # print("'objset_XY_txt'  SET  segment offsets: ",set_offset, end=" ")
    # print(" days per segment:", end=" ")
    # for i in range(len(objset_XY_txt)):
        # print(len(objset_XY_txt[i]), end=" ")

    global set_days, set_starts, set_ends   # for fill_below_horizon()
    global set_days     # for 'get_isSoY'
    set_days = []       # build list of SET segment span in days
    set_range = []      # build list of SET 'range(from, to)' date offsets
    solitary_SET_seg = []    # collect solitary SET segments
    solitary_SET_at_00h = []   # collect solitary SET events at 00h
    solitary_SET_at_24h = []   # collect solitary SET events at 24h
    set_starts = []    # days on which a SET segment starts
    set_ends = []      # days on which a SET segment ends

    for ndx, idx in enumerate(set_offset):
        lnth = len(objset_XY_txt[ndx])
        ldx = idx + lnth - 1
        set_days.append(ldx-idx)
        set_range.append(range(idx,idx+lnth))
        prnt("SET  segment {} offset: {:3d} = {:6} to {:3d} = {:6}, length {:3d} (spans {} days)".format(ndx,idx,DOY(idx),ldx,DOY(ldx),lnth,lnth-1))
        if lnth == 1:
            solitary_SET_seg.append(ndx)
            xS,yS = getXY(objset_XY_txt[ndx][0])    # start of SET
            if yS < 0.6:  solitary_SET_at_00h.append(xS)
            if yS > 23.4: solitary_SET_at_24h.append(xS)
        set_starts.append(idx)
        set_ends.append(ldx)

    if verbose: 
        print("   max hour per SET  segment:", end=" ")
        for item in setseg_Ymax: print("  {:6.3f}".format(item), end="")
        print("\n   min hour per SET  segment:", end=" ")
        for item in setseg_Ymin: print("  {:6.3f}".format(item), end="")
        print()
        #print(rise_days)
        #print(set_days)

# ---------------------------------------------------------------------------------------
# -------------  determine if SET or RISE crosses Civil Dawn or Civil Dusk  -------------
# ---------------------------------------------------------------------------------------

    global SETcrossesDAWN, SETcrossesDUSK, RISEcrossesDAWN, RISEcrossesDUSK     # originally for LOWER_forw() - now OBSOLETE
    SETcrossesDAWN = []         # per segment: True if SET seg crosses DAWN
    SETcrossesDUSK = []         # per segment: True if SET seg crosses DUSK
    RISEcrossesDAWN = []        # per segment: True if RISE seg crosses DAWN
    RISEcrossesDUSK = []        # per segment: True if RISE seg crosses DUSK

    for Rseg, idx in enumerate(rise_offset):
        lnth = len(objrise_XY_txt[Rseg])
        ldx = idx + lnth - 1
        RISEaboveDAWN = None
        RISEbelowDUSK = None
        idx_fr = rise_starts[Rseg]
        idx_to = rise_ends[Rseg]
        RISEcrossesDAWN.append(False)
        RISEcrossesDUSK.append(False)
        # Check if RISE segment crosses DAWN or DUSK
        ndx = 0
        for idx0 in range(idx_fr, idx_to+1):
            xR,yR = getXY(objrise_XY_txt[Rseg][ndx]) # y of RISE
            dawn  = f_AM(civilY_AM[idx0])           #  0.0 if dawn is None
            dusk  = f_PM(civilY_PM[idx0])           # 24.0 if dusk is None
            if RISEaboveDAWN is None:               # initialize RISEaboveDAWN
                RISEaboveDAWN = True if yR > dawn else False
            if (yR > dawn) != RISEaboveDAWN:         # does SET cross DAWN ?
                RISEcrossesDAWN[Rseg] = True
            if RISEbelowDUSK is None:               # initialize RISEbelowDUSK
                RISEbelowDUSK = True if yR < dusk else False
            if (yR < dusk) != RISEbelowDUSK:        # does RISE cross DUSK ?
                RISEcrossesDUSK[Rseg] = True
            ndx += 1
        # ----------------------------------------- end of 'for'
        prnt("RISE segment {} crosses Civil...  Dawn: {}   Dusk: {}".format(Rseg,bval(RISEcrossesDAWN[Rseg]),bval(RISEcrossesDUSK[Rseg])))
    # ----------------------------------------- end of 'for'

    for Sseg, idx in enumerate(set_offset):
        lnth = len(objset_XY_txt[Sseg])
        ldx = idx + lnth - 1
        SETaboveDAWN = None
        SETbelowDUSK = None
        idx_fr = set_starts[Sseg]
        idx_to = set_ends[Sseg]
        SETcrossesDAWN.append(False)
        SETcrossesDUSK.append(False)
        # Check if SET segment crosses DAWN or DUSK
        ndx = 0
        for idx0 in range(idx_fr, idx_to+1):
            xS,yS = getXY(objset_XY_txt[Sseg][ndx]) # y of SET
            dawn  = f_AM(civilY_AM[idx0])           #  0.0 if dawn is None
            dusk  = f_PM(civilY_PM[idx0])           # 24.0 if dusk is None
            if SETaboveDAWN is None:                # initialize SETaboveDAWN
                SETaboveDAWN = True if yS > dawn else False
            if (yS > dawn) != SETaboveDAWN:         # does SET cross DAWN ?
                SETcrossesDAWN[Sseg] = True
            if SETbelowDUSK is None:                # initialize SETbelowDUSK
                SETbelowDUSK = True if yS < dusk else False
            if (yS < dusk) != SETbelowDUSK:         # does SET cross DUSK ?
                SETcrossesDUSK[Sseg] = True
            ndx += 1
        # ----------------------------------------- end of 'for'
        prnt("SET  segment {} crosses Civil...  Dawn: {}   Dusk: {}".format(Sseg,bval(SETcrossesDAWN[Sseg]),bval(SETcrossesDUSK[Sseg])))
    # ----------------------------------------- end of 'for'

# ----------------------------------------------------------------------------------
# --------------  Meridian Passage dates when btwn Civil Dawn & Dusk  --------------
# ----------------------------------------------------------------------------------

    mp_btwn_dawn_dusk = []  # collect from-to dates when MerPass is between Civil Dawn & Dusk
    for ndx, idx_begin in enumerate(mp_offset):
        lnth = len(object_XY_txt[ndx])
        idx_end = idx_begin + lnth - 1
        prnt("MerPass segment {} offset: {:3d} = {:6} to {:3d} = {:6}, length {:3d} (spans {} days)".format(ndx,idx_begin,DOY(idx_begin),idx_end,DOY(idx_end),lnth,lnth-1))
        # get the 'from-to' date offsets during which MerPass is between Dawn & Dusk
        btwn = False
        for idx in range(idx_begin, idx_end+1):
            bt =  f_AM(civilY_AM[idx]) < meridian_pass[idx] < f_PM(civilY_PM[idx])
            if bt:
                if not btwn: idx_fr = idx
                btwn = True
            if not bt or idx == daystoprocess-1:
                if btwn:
                    mp_btwn_dawn_dusk.append((idx_fr, idx-1))
                    # print("mp btwn: {} to {}".format(DOY(idx_fr),DOY(idx-1)))
                btwn = False

# -----------------------------------------------------------------------------
# --------------  get Civil Dawn and Civil Dusk segment lengths  --------------
# -----------------------------------------------------------------------------

    # get civil DAWN segment lengths
    idx = 0
    seg_active = False
    segs_DAWN = 0     # count of AM segments including 'None' segments
    global seglen_DAWN, seglen_DUSK     # for LOWER_forw()
    seglen_DAWN = []  # list of segment lengths including 'None' segments
    seglen = 0

    while idx < daystoprocess:
        if civil_AM_txt[idx] is not None:
            if not seg_active:     # begin of DAWN segment
                if seglen != 0:
                    seglen_DAWN.append(seglen)
                    seglen = 0
                segs_DAWN += 1
            seglen += 1
            seg_active = True
        else:
            if seg_active:
                seglen_DAWN.append(seglen)
                seglen = -1
                segs_DAWN += 1
                seg_active = False
            else:
                seglen -= 1     # count length of 'None' segments as a negative value
        idx += 1

    if seglen != 0: seglen_DAWN.append(seglen)

    # get civil DUSK segment lengths
    idx = 0
    seg_active = False
    segs_DUSK = 0     # count of PM segments including 'None' segments
    seglen_DUSK = []  # list of segment lengths including 'None' segments
    seglen = 0

    while idx < daystoprocess:
        if civil_PM_txt[idx] is not None:
            if not seg_active:     # begin of DUSK segment
                if seglen != 0:
                    seglen_DUSK.append(seglen)
                    seglen = 0
                segs_DUSK += 1
            seglen += 1
            seg_active = True
        else:
            if seg_active:
                seglen_DUSK.append(seglen)
                seglen = -1
                segs_DUSK += 1
                seg_active = False
            else:
                seglen -= 1     # count length of 'None' segments as a negative value
        idx += 1

    if seglen != 0: seglen_DUSK.append(seglen)

    idx = 0; msg = " starting at ["
    for i in seglen_DAWN:
        msg += "{}, ".format(DOY(idx))
        idx += abs(i)
    prnt("civil dawn   seglen_DAWN",seglen_DAWN,msg[:-2]+"]")
    
    idx = 0; msg = " starting at ["
    for i in seglen_DUSK:
        msg += "{}, ".format(DOY(idx))
        idx += abs(i)
    prnt("civil dusk   seglen_DUSK",seglen_DUSK,msg[:-2]+"]")

# --------------------------------------------------------------------------------------
# -----  detect whole days with 'planet below horizon' and 'planet above horizon'  -----
# -----      if 'planet above horizon': identify segments that adjoin it           -----
# --------------------------------------------------------------------------------------

    segR = segS = None
    if len(rise_offset) > 0: segR = 0
    if len(set_offset)  > 0: segS = 0
    ahor = None     # True if above horizon at end of day
    RISEnxt = SETnxt = daystoprocess        # assume no RISE or SET within the year

    if segR is not None and segS is not None:
        # detect the initial condition on 1st Jan
        if rise_offset[segR] > 0 and set_offset[segS] == 0:
            ahor = False
        if rise_offset[segR] == 0 and set_offset[segS] > 0:
            ahor = True
        if rise_offset[segR] > 0 and set_offset[segS] > 0:
            if rise_offset[segR] == set_offset[segS]:
                # does the year begin with a planet RISE or a SET?
                if getY(objrise_Y[rise_offset[segR]]) < getY(objset_Y[set_offset[segS]]): ahor = False
                else: ahor = True
        RISEnxt = rise_offset[segR]
        SETnxt  =  set_offset[segS]
    else:
        # determine above/below horizon by inspecting the planet's altitude on 1st Jan
        ahor = planet_altitude(obj, d00, lats)
        # ahor = False      # DON'T assume planet all year below horizon if no RISE or SET within year

    na = 0          # offset counter into 'dah'
    idx = 0
    global dah      # for LOWER_forw()
    dah = []        # days totally above horizon
    # NOTE that this software only works with maximum 1 DAH zone
    dahoffset = []  # starting offset in 'dah' to each DAH zone
    prev_adahor = adahor = False    # all day above horizon

    nb = 0          # offset counter into 'dbh'
    dbh = []        # days totally below horizon
    # NOTE: there can be 3 DBH zones, e.g. Mercury 2024 69°N 70°N
    dbhoffset = []  # starting offset in 'dbh' to each DBH zone
    prev_adbhor = adbhor = False    # all day below horizon

    while idx < daystoprocess:
        # obtain the current RISE & SET segments:
        ndxR, segR = get_seg(idx, rise_offset)
        ndxS, segS = get_seg(idx, set_offset)

        objrise_Y_idx = getY(objrise_Y[idx], -1)    # last RISE of day
        objset_Y_idx = getY(objset_Y[idx], -1)      # last SET of day
        if idx > RISEnxt:
            # obtain the beginning of the next RISE segment, if any
            if segR is not None and segR+1 < len(rise_offset):
                RISEnxt = rise_offset[segR+1]
            else: RISEnxt = daystoprocess           # beyond the right border (Jan 2) Venus 2028 68°N
        if idx > SETnxt:
            # obtain the beginning of the next SET segment, if any
            if segS is not None and segS+1 < len(set_offset):
                SETnxt  = set_offset[segS+1]
            else: SETnxt = daystoprocess            # beyond the right border (Jan 2) Venus 2028 68°N

        if objrise_Y_idx is None and objset_Y_idx is None:
            if ahor: adahor = True
            else:    adbhor = True
        elif f_AM(objrise_Y_idx) > f_AM(objset_Y_idx):
            ahor = True
            adahor = adbhor = False
        else:
            ahor = False
            adahor = adbhor = False
        # if idx >= 356: print(DOY(idx), objrise_Y_idx, objset_Y_idx, RISEnxt, adahor, adbhor)

        if adahor:      # if planet currently all day above horizon...
            if idx < SETnxt:
                dah.append(idx)
                if adahor != prev_adahor:
                    dahoffset.append(na)
                na += 1     # next offset into dah
            else: adahor = False

        elif adbhor:    # if planet currently all day below horizon...
            if idx < RISEnxt:
                dbh.append(idx)
                if adbhor != prev_adbhor:
                    dbhoffset.append(nb)
                nb += 1     # next offset into dbh
            else: adbhor = False

        prev_adahor = adahor
        prev_adbhor = adbhor
        idx += 1
    # ----------------------------------------- end of 'while'

    global dah_range            # for LOWER_forw()
    global dbh_range            # for btwn_RISE_to_SET()
    dah_range = []  # build list of DAH 'range(from, to)' date offsets
    dbh_range = []  # build list of DBH 'range(from, to)' date offsets

    txt = "planet all day above horizon (DAH) on: "
    n = len(txt)
    # print(txt, dah)
    if dah != []:
        for ndx, i in enumerate(dahoffset):
            if ndx > 0:
                idx_to = dah[i-1]
                dah_range.append(range(idx_fr,idx_to+1))
            idx_fr = dah[i]
        dah_range.append(range(idx_fr,dah[-1]+1))

        for rng in dah_range:
            dah_fr = rng.start; dah_to = rng.stop
            lnth = dah_to - dah_fr
            prnt("{}  {:3d} = {:6} to {:3d} = {}, {:d} days".format(txt,dah_fr,DOY(dah_fr),dah_to-1,DOY(dah_to-1),lnth))
            txt = ' ' * n
    else: prnt("{}  <no days>".format(txt))

    txt = "planet all day below horizon (DBH) on: "
    n = len(txt)
    # print(txt, dbh)
    if dbh != []:
        for ndx, i in enumerate(dbhoffset):
            if ndx > 0:
                idx_to = dbh[i-1]
                dbh_range.append(range(idx_fr,idx_to+1))
            idx_fr = dbh[i]
        dbh_range.append(range(idx_fr,dbh[-1]+1))

        for rng in dbh_range:
            dbh_fr = rng.start; dbh_to = rng.stop
            lnth = dbh_to - dbh_fr
            prnt("{}  {:3d} = {:6} to {:3d} = {}, {:d} days".format(txt,dbh_fr,DOY(dbh_fr),dbh_to-1,DOY(dbh_to-1),lnth))
            txt = ' ' * n
    else: prnt("{}  <no days>".format(txt))


    dahseg = []         # list of segments adjoining each 'planet all day above horizon' zone
    dah_starts = []     # days of which dah starts
    dah_ends = []       # days of which dah ends

    if dah == []: dahseg.append([])   # create an empty dahseg[0]
    else:
        # gather list of days on which DAH starts & ends
        for rng in dah_range:
            dah_fr = rng.start; dah_to = rng.stop - 1
            dah_starts.append(dah_fr)
            dah_ends.append(dah_to)

        for zone, ndx in enumerate(dahoffset):
            dahseg.append([])   # new list for a DAH zone
            dah_fr = dah[ndx]
            dah_to = dah[-1]
            if len(dahoffset)-1 > zone: dah_to = dah[dahoffset[zone+1] - 1]

            # 'above/below MerPass' ('ab' variable) refers to the relative position of the
            #    Meridian Passage ON THE SAME DAY as the RISE/SET segment starts/ends.

            # note: DAH is first followed by a SET then by a RISE which may come a day after the SET
            last_ndx = len(rise_offset) - 1
            for rise_seg, offR in enumerate(rise_offset):
                ##if rise_days[rise_seg] == 0: continue    # ignore zero length segments
                idx = None
                endR = offR + len(objrise_XY_txt[rise_seg])  # end of RISE segment + 1
                # if year begins with dah -OR- RISE follows dah
                if ((rise_seg == 0 and dah_fr == 0) or \
                    (dah_fr != 0 and (offR == dah_to+1 or offR == dah_to+2))):
                    # determine if following segment is above or below the Meridian Passage
                    idx = offR
                    xR,yR = getXY(objrise_XY_txt[rise_seg][0])  # start of RISE following DAH
                    ab = +1 if yR > meridian_pass[idx] else -1  # +1 if above merpass else -1
                    dahseg[zone].append(("RISE_after_dah", rise_seg, ab))
                # if dah begins after a RISE segment -OR- year ends with dah
                elif (endR == dah_fr or \
                     (rise_seg == last_ndx and dah_to == daystoprocess - 1)):
                    # determine if preceeding segment is above or below the Meridian Passage
                    idx = endR - 1
                    xRe,yRe = getXY(objrise_XY_txt[rise_seg][-1])  # end of RISE preceeding DAH
                    ab = +1 if yRe > meridian_pass[idx] else -1 # +1 if above merpass else -1
                    dahseg[zone].append(("RISE_before_dah", rise_seg, ab))

            # note: DAH is preceeded by a RISE which is preceeded by a SET that may come a day earlier
            last_ndx = len(set_offset) - 1
            for set_seg, offS in enumerate(set_offset):
                # include SET segments length 1 spanning 0 days (Mercury 2026 66°N)
                ##if set_days[set_seg] == 0: continue     # ignore zero length segments
                idx = None
                endS = offS + len(objset_XY_txt[set_seg])  # end of SET segment + 1
                # if year begins with dah -OR- SET follows dah
                if ((set_seg == 0 and dah_fr == 0) or \
                    (dah_fr != 0 and offS == dah_to+1)):
                    # determine if following segment is above or below the Meridian Passage
                    idx = offS
                    xS,yS = getXY(objset_XY_txt[set_seg][0])    # start of SET following DAH
                    ab = +1 if yS > meridian_pass[idx] else -1  # +1 if above merpass else -1
                    dahseg[zone].append(("SET_after_dah", set_seg, ab))
                # if dah begins after a SET segment or 1 day later(!)
                # -OR- year ends with dah
                elif (endS == dah_fr or endS+1 == dah_fr or \
                     (set_seg == last_ndx and dah_to == daystoprocess - 1)):
                    # determine if preceeding segment is above or below the Meridian Passage
                    idx = endS - 1
                    xSe,ySe = getXY(objset_XY_txt[set_seg][-1]) # end of SET preceeding DAH
                    ab = +1 if ySe > meridian_pass[idx] else -1 # +1 if above merpass else -1
                    dahseg[zone].append(("SET_before_dah", set_seg, ab))
            
            # NOTE: (!) refers to the case when the last SET occurs 2 days before DAH, e.g.
            #       Mercury 2024 65°N. (The day in-between has the last RISE before DAH.)

            if verbose and  dahseg[zone] != []:
                msg = ""
                if len(dahoffset) > 1: msg = "{} ".format(zone)
                print("   segments adjoining DAH zone {}from {} to {}:\n    ".format(msg,DOY(dah_fr),DOY(dah_to)),end='')
                print("     <adjoining type>, <seg no>, <+1 above MerPass, -1 below MerPass>\n    ",end='')
                for txt, seg, ab in dahseg[zone]:
                    print(" ('{}', {:d}, {:+d})".format(txt,seg,ab), end = '')
                print()
        # ----------------------------------------- end of 'for'


    # if len(dbhoffset) > 1:
        # print("multiple dbh zones ... starting at offset: ", dbhoffset)
    dbhseg = [] # list of segments adjoining each 'planet all day below horizon' zone

    if dbh == []: dbhseg.append([])   # create an empty dbhseg[0]
    else:
        # gather list of days on which DBH starts & ends
        for zone, ndx in enumerate(dbhoffset):
            dbhseg.append([])   # new list for a DBH zone
            dbh_fr = dbh[ndx]
            dbh_to = dbh[-1]
            if len(dbhoffset)-1 > zone: dbh_to = dbh[dbhoffset[zone+1] - 1]

            last_ndx = len(rise_offset) - 1
            for rise_seg, offR in enumerate(rise_offset):
                # DON'T IGNORE zero length segments (Mars 1954 63°N)
                ##if rise_days[rise_seg] == 0: continue    # ignore zero length segments
                idx = None
                endR = offR + len(objrise_XY_txt[rise_seg])  # end of RISE segment + 1
                #print(DOY(endR), DOY(dbh_fr))
                # if year begins with dbh -OR- RISE follows dbh
                if ((rise_seg == 0 and dbh_fr == 0) or \
                    (dbh_fr != 0 and offR == dbh_to +1)):
                    idx = offR
                    dbhseg[zone].append(("RISE_after_dbh", rise_seg))
                # if dbh begins after a RISE segment -OR- year ends with dbh
                #     'endR+1 == dbh_fr' for Mars 2018 65°N
                elif (endR == dbh_fr or endR+1 == dbh_fr or \
                     (rise_seg == last_ndx and dbh_to == daystoprocess - 1)):
                    idx = endR - 1
                    dbhseg[zone].append(("RISE_before_dbh", rise_seg))

            last_ndx = len(set_offset) - 1
            for set_seg, offS in enumerate(set_offset):
                ##if set_days[set_seg] == 0: continue     # ignore zero length segments
                idx = None
                endS = offS + len(objset_XY_txt[set_seg])  # end of SET segment + 1
                # if year begins with dbh -OR- SET follows dbh
                if ((set_seg == 0 and dbh_fr == 0) or \
                    (dbh_fr != 0 and offS == dbh_to +1)):
                    idx = offS
                    dbhseg[zone].append(("SET_after_dbh", set_seg))
                # if dbh begins after a SET segment -OR- year ends with dbh
                elif (endS == dbh_fr or \
                     (set_seg == last_ndx and dbh_to == daystoprocess - 1)):
                    idx = endS - 1
                    dbhseg[zone].append(("SET_before_dbh", set_seg))

            if verbose and dbhseg[zone] != []:
                msg = ""
                if len(dbhoffset) > 1: msg = "{} ".format(zone)
                print("   segments adjoining DBH zone {}from {} to {}:\n    ".format(msg,DOY(dbh_fr),DOY(dbh_to)),end='')
                for seg in dbhseg[zone]: print(" {}".format(seg), end = '')
                print()
        # ----------------------------------------- end of 'for'

    sdah = sorted(set(dah))     # python sets are by definition unsorted
    sdbh = sorted(set(dbh))     # python sets are by definition unsorted


# ------------------------------------------------------------------------------------
# ----  get the initial/final visibility states at the corners of the plot chart  ----
# ------------------------------------------------------------------------------------

    global isSoY, fsSoY, isEoY, fsEoY
    isSoY = get_isSoY(getY(objrise_Y[0]),getY(objset_Y[0]),sdah,sdbh)       # initial state at Start of Year
    fsSoY = get_fsSoY(getY(objrise_Y[0],-1),getY(objset_Y[0],-1),sdah,sdbh) #   final state at Start of Year
    d = daystoprocess-1
    isEoY = get_isEoY(getY(objrise_Y[d]),getY(objset_Y[d]),sdah,sdbh)       # initial state at End of Year
    fsEoY = get_fsEoY(getY(objrise_Y[d],-1),getY(objset_Y[d],-1),sdah,sdbh) #   final state at End of Year

    prnt("{} Visibility - SoY 00h: {},  SoY 24h: {},  EoY 00h: {},  EoY 24h: {}".format(objn,isSoY,fsSoY,isEoY,fsEoY))
    #print("   isSoY=", isSoY, sep = "", end = "  ")
    #print("fsSoY=", fsSoY, sep = "", end = "  ")
    #print("isEoY=", isEoY, sep = "", end = "  ")
    #print("fsEoY=", fsEoY, sep = "")


# ---------------------------------------------------------------
# --------------  IDENTIFY ALL SEGMENT END POINTS  --------------
# ---------------------------------------------------------------

# ... which chart border (SoY EoY 00h 24h) they end on or which DAH/DBH zone they touch
    global rise_ep, set_ep      # for LOWER_forw() & UPPER_back()
    rise_ep, RISEflips = seg_endpoints(rise_offset,dah,dbh,dahseg,dbhseg,dahoffset,dbhoffset, \
                                       rise_starts,rise_ends,set_starts,set_ends)
    set_ep,  SETflips  = seg_endpoints(set_offset, dah,dbh,dahseg,dbhseg,dahoffset,dbhoffset, \
                                       rise_starts,rise_ends,set_starts,set_ends)

    if verbose:
        print("SoY/EoY = Start/End of Year, 00h = lower border, 24h = upper border, DAH/DBH = adjoins DAH/DBH")

        txt = ''
        print("RISE endpoints per segment:",end='')
        for index, item in enumerate(rise_ep):
            ep0, ep1 = item
            if ep0 == ep1 and rise_days[index] == 0:
                txt += " {},".format(ep0)     # indicates a solitary endpoint (seg length 1; spans 0 days)
            else: txt += " {} to {},".format(ep0,ep1)
        # ----------------------------------------- end of 'for'
        print(txt[:-1])

        txt = ''
        print("SET  endpoints per segment:",end='')
        for index, item in enumerate(set_ep):
            ep0, ep1 = item
            if ep0 == ep1 and set_days[index] == 0:
                txt += " {},".format(ep0)    # indicates a solitary endpoint (seg length 1; spans 0 days)
            else: txt += " {} to {},".format(ep0,ep1)
        # ----------------------------------------- end of 'for'
        print(txt[:-1])


# ------------------------------------------------------------------------
# --------------  detect SET-to-RISE 'below horizon' bands  --------------
# ------------------------------------------------------------------------

# (any two bands that overlap in dates where SET occurs before RISE on the same day)

    set_to_rise_pair = []           # overlapping SET-to-RISE segment pair

    # ignore RISE seg length of 1 day:
    # ignore SET  seg length of 1 day: Mercury 2020 65°N; Venus 2024 70°N
    for Sseg, Srng in enumerate(set_range):
        if Srng.stop - Srng.start == 1: continue    # ignore SET seg length of 1 day
        for Rseg, Rrng in enumerate(rise_range):
            if Rrng.stop - Rrng.start == 1: continue    # ignore RISE seg length of 1 day
            overlap = range(max(Rrng.start,Srng.start), min(Rrng.stop,Srng.stop))
            if len(overlap) > 0:
                # test if RISE time is higher than SET time
                idx = overlap.start     # any overalp date will do
                Sfr = set_offset[Sseg]
                xS,yS = getXY(objset_XY_txt[Sseg][idx-Sfr])
                Rfr = rise_offset[Rseg]
                xR,yR = getXY(objrise_XY_txt[Rseg][idx-Rfr])
                if yR > yS:
                    set_to_rise_pair.append((Sseg, Rseg))

    global SET_to_RISE_band     # for fill_below_horizon()
    global SET_to_RISE_band_range
    SETseg_to_multiRISE_segs = []   # SET  segs that form a band with multiple RISE segs
    multiSET_to_RISEseg_segs = []   # RISE segs that form a band with multiple SET  segs
    SET_to_RISE_band      = []      # list of SET-to-RISE bands as tuples: ([SET segs],[RISE segs])
    SET_to_RISE_band_txt  = []      # save for #0 GENERIC: SET-to-RISE band
    SET_to_RISE_band_range = []     # minimum and maximum date offsets as tuple per band

    if len(set_to_rise_pair) > 0:
        # the complexity here arises from collecting ...
        #     all RISE segs that match a SET  seg
        #  OR all SET  segs that match a RISE seg
        # ... as this comprises just one band.
        prnt("SET_to_RISE 'below horizon' bands:")
        ndx_pair = []       # collect index of each handled SET-to-RISE pair
        i = -1
        for Sseg, Rseg in set_to_rise_pair:
            i += 1
            if i in ndx_pair: continue
            Ssegtxt = str(Sseg); Sband = [Sseg]
            Rsegtxt = str(Rseg); Rband = [Rseg]
            if i not in ndx_pair: ndx_pair.append(i)
            ii = -1
            for Sseg2, Rseg2 in set_to_rise_pair:
                ii += 1
                if ii in ndx_pair: continue
                new = False
                if Sseg2 == Sseg:
                    Rband.append(Rseg2)
                    Rsegtxt += ", " + str(Rseg2); new = True
                if Rseg2 == Rseg:
                    Sband.append(Sseg2)
                    Ssegtxt += ", " + str(Sseg2); new = True
                if new:
                    if ii not in ndx_pair: ndx_pair.append(ii)
            msg = "SET seg {} to RISE seg {}".format(Ssegtxt,Rsegtxt)
            prnt("   " + msg)
            SET_to_RISE_band_txt.append(msg)
            SET_to_RISE_band.append((Sband,Rband))
            if ',' in Rsegtxt: SETseg_to_multiRISE_segs.append(Sseg)
            if ',' in Ssegtxt: multiSET_to_RISEseg_segs.append(Rseg)
        # ----------------------------------------- end of 'for'

        # determine SET_to_RISE band overall range
        for Ssegs, Rsegs in SET_to_RISE_band:   # for each s2r band
            all_ep = []
            for Rseg in Rsegs:
                all_ep.append(rise_starts[Rseg])
                all_ep.append(rise_ends[Rseg])
            for Sseg in Ssegs:
                all_ep.append(set_starts[Sseg])
                all_ep.append(set_ends[Sseg])
            band_min = min(all_ep)
            band_max = max(all_ep)
            SET_to_RISE_band_range.append((band_min, band_max))
        # ----------------------------------------- end of 'for'

        # print("   SETseg_to_multiRISE_segs", SETseg_to_multiRISE_segs, "multiSET_to_RISEseg_segs", multiSET_to_RISEseg_segs)


# ------------------------------------------------------------------------
# --------------  detect RISE-to-SET 'above horizon' bands  --------------
# ------------------------------------------------------------------------

# (any two bands that overlap in dates where RISE occurs before SET on the same day)

    rise_to_set_pair = []           # overlapping RISE-to-SET segment pair

    # ignore RISE seg length of 1 day:
    # ignore SET  seg length of 1 day:
    for Rseg, Rrng in enumerate(rise_range):
        if Rrng.stop - Rrng.start == 1: continue    # ignore RISE seg length of 1 day
        for Sseg, Srng in enumerate(set_range):
            if Srng.stop - Srng.start == 1: continue    # ignore SET seg length of 1 day
            overlap = range(max(Rrng.start,Srng.start), min(Rrng.stop,Srng.stop))
            if len(overlap) > 0:
                # test if RISE time is higher than SET time
                idx = overlap.start     # any overalp date will do
                Sfr = set_offset[Sseg]
                xS,yS = getXY(objset_XY_txt[Sseg][idx-Sfr])
                Rfr = rise_offset[Rseg]
                xR,yR = getXY(objrise_XY_txt[Rseg][idx-Rfr])
                if yS > yR:
                    rise_to_set_pair.append((Rseg, Sseg))

    global RISE_to_SET_band     # for fill_below_horizon()
    global RISE_to_SET_band_range
    RISEseg_to_multiSET_segs = []   # RISE segs that form a band with multiple SET  segs
    multiRISE_to_SETseg_segs = []   # SET  segs that form a band with multiple RISE segs
    RISE_to_SET_band      = []      # list of RISE-to-SET bands as tuples: ([RISE segs],[SET segs])
    RISE_to_SET_band_txt  = []      # save for Civil DAWN to DUSK zone: RISE-to-SET band
    RISE_to_SET_band_txt2 = []      # save for Civil DAWN to DUSK zone: RISE-to-SET band
    RISE_to_SET_band_size = []      # sum of all segment lengths
    RISE_to_SET_band_size_d2d = []  # sum of all segment lengths between Civil Dawn & Dusk
    RISE_to_SET_band_Rdays = []     # number of days RISE is between Civil Dawn and Dusk
    RISE_to_SET_band_Sdays = []     # number of days SET  is between Civil Dawn and Dusk
    RISE_to_SET_band_range = []     # minimum and maximum date offsets as tuple per band

    if len(rise_to_set_pair) > 0:
        # the complexity here arises from collecting ...
        #     all SET  segs that match a RISE seg
        #  OR all RISE segs that match a SET  seg
        # ... as this comprises just one band.
        prnt("RISE_to_SET 'above horizon' bands:")
        ndx_pair = []       # collect index of each handled RISE-to-SET pair
        ndx_band = -1       # index to last RISE-to-SET band
        i = -1
        msgs = []
        for Rseg, Sseg in rise_to_set_pair:
            i += 1
            if i in ndx_pair: continue
            Rsegtxt = str(Rseg); Rband = [Rseg]
            Rsegtxt2 = str(Rseg) + ' ' + str(rise_ep[Rseg])
            Ssegtxt = str(Sseg); Sband = [Sseg]
            Ssegtxt2 = str(Sseg) + ' ' + str(set_ep[Sseg])
            RISE_to_SET_band_size.append(rise_days[Rseg]+set_days[Sseg]+2)  # +2 for length
            ndx_band += 1
            if i not in ndx_pair: ndx_pair.append(i)
            ii = -1
            for Rseg2, Sseg2 in rise_to_set_pair:
                ii += 1
                if ii in ndx_pair: continue
                new = False
                if Sseg2 == Sseg:
                    Rband.append(Rseg2)
                    Rsegtxt += ", " + str(Rseg2); new = True
                    Rsegtxt2 += ", " + str(Rseg2) + ' ' + str(rise_ep[Rseg2])
                    RISE_to_SET_band_size[ndx_band] += rise_days[Rseg2]+1
                if Rseg2 == Rseg:
                    Sband.append(Sseg2)
                    Ssegtxt += ", " + str(Sseg2); new = True
                    Ssegtxt2 += ", " + str(Sseg2) + ' ' + str(set_ep[Sseg2])
                    RISE_to_SET_band_size[ndx_band] += set_days[Sseg2]+1
                if new:
                    if ii not in ndx_pair: ndx_pair.append(ii)
            msg = "RISE seg {} to SET seg {}".format(Rsegtxt, Ssegtxt)
            msg2 = "RISE seg {} to SET seg {}".format(Rsegtxt2, Ssegtxt2)
            msgs.append("   " + msg)
            RISE_to_SET_band_txt.append(msg)
            RISE_to_SET_band_txt2.append(msg2)
            RISE_to_SET_band.append((Rband,Sband))
            if ',' in Rsegtxt: RISEseg_to_multiSET_segs.append(Rseg)
            if ',' in Ssegtxt: multiRISE_to_SETseg_segs.append(Sseg)
        # ----------------------------------------- end of 'for'

        # determine RISE_to_SET band overall range
        for Rsegs, Ssegs in RISE_to_SET_band:   # for each r2s band
            all_ep = []
            for Rseg in Rsegs:
                all_ep.append(rise_starts[Rseg])
                all_ep.append(rise_ends[Rseg])
            for Sseg in Ssegs:
                all_ep.append(set_starts[Sseg])
                all_ep.append(set_ends[Sseg])
            band_min = min(all_ep)
            band_max = max(all_ep)
            RISE_to_SET_band_range.append((band_min, band_max))
        # ----------------------------------------- end of 'for'

        # calculate 'RISE_to_SET_band_size' as number of days RISE and SET in the
        #    band are between DAWN and DUSK. Overwrite 'RISE_to_SET_band_size'.
        #    (e.g. This is necessary for Mars 2050 69°N)
        ndx_band = -1
        for Rsegs, Ssegs in RISE_to_SET_band:   # for each r2s band
            Rdays = 0
            Sdays = 0
            ndx_band += 1
            for Rseg in Rsegs:
                ndx = 0
                for idx in rise_range[Rseg]:
                    dawn = f_AM(civilY_AM[idx])             #  0.0 if None
                    dusk = f_PM(civilY_PM[idx])             # 24.0 if None
                    xR,yR = getXY(objrise_XY_txt[Rseg][ndx])   # y of RISE
                    if dawn < yR < dusk: Rdays += 1
                    ndx += 1
            for Sseg in Ssegs:
                ndx = 0
                for idx in set_range[Sseg]:
                    dawn = f_AM(civilY_AM[idx])             #  0.0 if None
                    dusk = f_PM(civilY_PM[idx])             # 24.0 if None
                    xS,yS = getXY(objset_XY_txt[Sseg][ndx])    # y of SET
                    if dawn < yS < dusk: Sdays += 1
                    ndx += 1
            #print("   band {} size:  Rdays {:3d},  Sdays {:3d}".format(ndx_band,Rdays,Sdays))
            RISE_to_SET_band_Rdays.append(Rdays)            # rqrd for trace#80 section
            RISE_to_SET_band_Sdays.append(Sdays)            # rqrd for trace#80 section
            RISE_to_SET_band_size_d2d.append(Rdays + Sdays)
            msg = ''
            if RISE_to_SET_band_size_d2d[ndx_band] == RISE_to_SET_band_size[ndx_band]:
                msg = ' (band within Civil Dawn to Dusk)'
            else:
                msg += " ({} RISE & {} SET days between Civil Dawn and Dusk)".format(Rdays,Sdays)
            prnt(msgs[ndx_band]+msg)
            #print("   band {}: d2d {}, overall {}".format(ndx_band,RISE_to_SET_band_size_d2d[ndx_band],RISE_to_SET_band_size[ndx_band]))
        # ----------------------------------------- end of 'for'

    # print("   RISEseg_to_multiSET_segs", RISEseg_to_multiSET_segs, "multiRISE_to_SETseg_segs", multiRISE_to_SETseg_segs)


# ----------------------------------------------------------------------------------------------------------------
# ----  Identify sections during noDAWN when 'sun above horizon' (shaded gold) is adjacent to the 00h border  ----
# ----               (noDAWN is from seglen_DAWN[0] to 'seglen_DAWN[0] - seglen_DAWN[1] - 1'                  ----
# ----------------------------------------------------------------------------------------------------------------

# Test cases:       bh = planet below horizon (grey); nv = not visible (gold)
#   Jupiter 2026 72°N   |nv|      (RISE/SET only after noDAWN)
#   Saturn  2030 72°N   |nv|
#   Mars    2028 62°N   |bh|
#   Mercury 2028 64°N   |bh|
#   Jupiter 2046 63°N   |bh - RISE end - nv|
#   Mars    2046 64°N   |nv - SET end  - bh|
#   Mercury 2027 63°N   |nv - SET end  - bh|
#   Venus   2028 65°N   |nv - SET both - bh - RISE end - nv|        (SET segment length 0)
#   Venus   2020 65°N   |nv - SET both - bh - RISE end - nv|        (SET segment length 0)
#   Venus   2028 68°N   |nv - Rise start - bh - RISE end - nv|
#   Venus   2046 65°N   |bh - RISE end - nv - RISE start - bh|
#   Venus   2029 66°N   |bh - SET start - nv - SET end - bh|
#   Mercury 2024 66°N   |bh - RISE end - nv - SET end - bh|
#   Mercury 2025 72°N   |bh - RISE end - nv - SET end - bh - RISE end - nv|
#   Mercury 2026 69°N   |bh - RISE end - nv - SET end - bh - RISE end - nv - RISE start - bh|
#   Mercury 2020 67°N   |bh - SET both - nv - SET end - bh - RISE end - nv - RISE start - bh|

    # noDAWN_00h_contour = []
    # noDAWN_fr = None
    # noDAWN_to = None
    # if len(seglen_DAWN) == 3:
        # noDAWN_fr = seglen_DAWN[0] - 1              # include the day that DAWN ends
        # noDAWN_to = seglen_DAWN[0] - seglen_DAWN[1] # include the day that DAWN restarts
        # rise_fr = rise_to = set_fr = set_to = None
        # if config.debug_00h_contour: print("   noDAWN: contours along 00h...")

        # # get chronological list of RISE/SET segments that "contact" 00h (all and during noDAWN)
        # all_00h_segs = []       # tuple (date offset, RISE seg, SET seg, v)
        # noDAWN_00h_segs = []    # tuple (date offset, RISE seg, SET seg, v)
                                # # v = True if start; False if end; None if singleton (length 1 day)

        # for nR in range(len(rise_offset)):
            # rise_fr = rise_starts[nR]
            # rise_to = rise_ends[nR]
            # v = True    # default: start of segment
            # # if segment length 1 (spans 0 days) ...
            # if rise_ep[nR][0] == rise_ep[nR][1] == '00h' and rise_days[nR] == 0: v = None

            # if rise_ep[nR][0] == '00h':
                # all_00h_segs.append((rise_fr, nR, None, v))
                # if noDAWN_fr < rise_fr < noDAWN_to:
                    # noDAWN_00h_segs.append((rise_fr, nR, None, v))

            # if rise_ep[nR][1] == '00h' and v is not None:
                # all_00h_segs.append((rise_to, nR, None, False))
                # if noDAWN_fr < rise_to < noDAWN_to:
                    # noDAWN_00h_segs.append((rise_to, nR, None, False))

        # for nS in range(len(set_offset)):
            # set_fr = set_starts[nS]
            # set_to = set_ends[nS]
            # v = True    # default: start of segment
            # # if segment length 1 (spans 0 days) ...
            # if set_ep[nS][0] == set_ep[nS][1] == '00h' and set_days[nS] == 0: v = None

            # if set_ep[nS][0] == '00h':
                # all_00h_segs.append((set_fr, None, nS, v))
                # if noDAWN_fr < set_fr < noDAWN_to:
                    # noDAWN_00h_segs.append((set_fr, None, nS, v))

            # elif set_ep[nS][1] == '00h' and v is not None:
                # all_00h_segs.append((set_to, None, nS, False))
                # if noDAWN_fr < set_to < noDAWN_to:
                    # noDAWN_00h_segs.append((set_to, None, nS, False))

        # # Note: a boolean cannot be compared to 'None' during a sort.
        # #       If the date offsets are the same, one cannot ensure 'None'
        # #       doesn't exist in the second element, e.g. Jupiter 2042 72°N.
        # #       So to be safe, sort only on the first element.

        # all_00h_segs.sort(key=lambda x: x[0])
        # noDAWN_00h_segs.sort(key=lambda x: x[0])
        # #print(all_00h_segs)

        # # above/below horizon state when noDAWN begins
        # above_horizon = isSoY      # visible state on Jan 1 00:00 (False = below horizon)
        # #print(above_horizon)
        # for item in all_00h_segs:
            # idx, nR, nS, start = item
            # if idx > noDAWN_fr: break
            # #print(DOY(idx),DOY(noDAWN_fr))
            # if nR is not None and rise_ep[nR][0] == '00h': above_horizon = False
            # if nR is not None and rise_ep[nR][1] == '00h': above_horizon = True
            # if nS is not None and set_ep[nS][0]  == '00h': above_horizon = True
            # if nS is not None and set_ep[nS][1]  == '00h': above_horizon = False
        # #print(above_horizon)

        # txt = '   '
        # for idx, nR, nS, start in noDAWN_00h_segs:
            # if len(txt) > 8: txt += ", "
            # txt += DOY(idx)
            # if nR is not None: txt += " Rise {} ".format(nR)
            # if nS is not None: txt += " Set {} ".format(nS)
            # if start is None: sten = "both"
            # else: sten = "start" if start else "end"
            # txt += sten
        # if len(txt) > 3: print("segments adjoining the 00h border:\n" + txt)

        # # inspect segment endpoints during noDAWN chronologically...
        # n = len(noDAWN_00h_segs)
        # idx0 = idx1 = None

        # for index, item in enumerate(noDAWN_00h_segs):
            # idx, nR, nS, start = item
            # if nS is not None and start is None:
                # above_horizon = not above_horizon
                # if above_horizon: idx0 = idx
                # else:             idx1 = idx
            # else:
                # if nS is not None and start:     idx0 = idx; above_horizon = True   # Mars 2032 66°N
                # if nS is not None and not start: idx1 = idx; above_horizon = False  # Mercury 2033 65°N
            # if nR is not None and not start: idx0 = idx; above_horizon = True       # Mercury 2033 68°N
            # if nR is not None and start:     idx1 = idx; above_horizon = False      # Mercury 2033 68°N

            # if index == 0   and idx0 is None and idx1 is not None: idx0 = noDAWN_fr
            # if index == n-1 and idx0 is not None and idx1 is None: idx1 = noDAWN_to
            # if idx0 is not None and idx1 is not None and idx1 > idx0:
                # if config.debug_00h_contour: print("        {:6} to {:6}".format(DOY(idx0),DOY(idx1)))
                # noDAWN_00h_contour.append((idx0, idx1))
                # idx0 = idx1 = None

        # if n == 0 and above_horizon:  # if no RISE/SET segments that "contact" 00h during noDAWN
            # idx0 = noDAWN_fr; idx1 = noDAWN_to
            # if config.debug_00h_contour: print("        {:6} to {:6}".format(DOY(idx0),DOY(idx1)))
            # noDAWN_00h_contour.append((idx0, idx1))


# ----------------------------------------------------------------------------------------------------------------
# ----  Identify sections during noDUSK when 'sun above horizon' (shaded gold) is adjacent to the 24h border  ----
# ----               (noDUSK is from seglen_DUSK[0] to 'seglen_DUSK[0] - seglen_DUSK[1] - 1'                  ----
# ----------------------------------------------------------------------------------------------------------------

# Test cases:       bh = planet below horizon (grey); nv = not visible (gold)
#   Jupiter 2026 72°N   |nv|      (RISE/SET only after noDUSK)
#   Mars    2028 62°N   |bh|
#   Mars    2028 67°N   |bh - RISE start - nv|
#   Jupiter 2026 65°N   |nv - SET start - bh|
#   Saturn  2032 66°N   |nv - SET start - bh - RISE start - nv|
#   Mercury 2026 65°N   |bh - SET end - nv - SET start - bh|
#   Mercury 2026 69°N   |bh - SET end - nv - SET start - bh - RISE start - nv - RISE end - bh|
#   Venus   2020 68°N   |nv - RISE both - bh - RISE start - nv|

    # noDUSK_24h_contour = []
    # noDUSK_fr = None
    # noDUSK_to = None
    # if len(seglen_DUSK) == 3:
        # noDUSK_fr = seglen_DUSK[0] - 1              # include the day that DUSK ends
        # noDUSK_to = seglen_DUSK[0] - seglen_DUSK[1] # include the day that DUSK restarts
        # rise_fr = rise_to = set_fr = set_to = None
        # if config.debug_24h_contour: print("   noDUSK: contours along 24h...")

        # # get chronological list of RISE/SET segments that "contact" 24h (all and during noDUSK)
        # all_24h_segs = []       # tuple (date offset, RISE seg, SET seg, v)
        # noDUSK_24h_segs = []    # tuple (date offset, RISE seg, SET seg, v)
                                # # v = True if start; False if end; None if singleton (length 1 day)

        # for nR in range(len(rise_offset)):
            # rise_fr = rise_starts[nR]
            # rise_to = rise_ends[nR]
            # v = True    # default: start of segment
            # # if segment length 1 (spans 0 days) ...
            # if rise_ep[nR][0] == rise_ep[nR][1] == '24h' and rise_days[nR] == 0: v = None

            # if rise_ep[nR][0] == '24h':
                # all_24h_segs.append((rise_fr, nR, None, v))
                # if noDUSK_fr < rise_fr < noDUSK_to:
                    # noDUSK_24h_segs.append((rise_fr, nR, None, v))

            # if rise_ep[nR][1] == '24h' and v is not None:
                # all_24h_segs.append((rise_to, nR, None, False))
                # if noDUSK_fr < rise_to < noDUSK_to:
                    # noDUSK_24h_segs.append((rise_to, nR, None, False))

        # for nS in range(len(set_offset)):
            # set_fr = set_starts[nS]
            # set_to = set_ends[nS]
            # v = True    # default: start of segment
            # # if segment length 1 (spans 0 days) ...
            # if set_ep[nS][0] == set_ep[nS][1] == '24h' and set_days[nS] == 0: v = None

            # if set_ep[nS][0] == '24h':
                # all_24h_segs.append((set_fr, None, nS, v))
                # if noDUSK_fr < set_fr < noDUSK_to:
                    # noDUSK_24h_segs.append((set_fr, None, nS, v))

            # elif set_ep[nS][1] == '24h' and v is not None:
                # all_24h_segs.append((set_to, None, nS, False))
                # if noDUSK_fr < set_to < noDUSK_to:
                    # noDUSK_24h_segs.append((set_to, None, nS, False))

        # # Note: a boolean cannot be compared to 'None' during a sort.
        # #       If the date offsets are the same, one cannot ensure 'None'
        # #       doesn't exist in the second element, e.g. Jupiter 2008 68°N.
        # #       So to be safe, sort only on the first element.
        
        # all_24h_segs.sort(key=lambda x: x[0])
        # noDUSK_24h_segs.sort(key=lambda x: x[0])
        # #print(all_24h_segs)

        # # above/below horizon state when noDUSK begins
        # above_horizon = fsSoY      # visible state on Jan 1 24:00 (False = below horizon)
        # #print(above_horizon)
        # for item in all_24h_segs:
            # idx, nR, nS, start = item
            # if idx > noDUSK_fr: break
            # #print(DOY(idx),DOY(noDUSK_fr))
            # if nR is not None and rise_ep[nR][0] == '24h': above_horizon = True
            # if nR is not None and rise_ep[nR][1] == '24h': above_horizon = False
            # if nS is not None and set_ep[nS][0]  == '24h': above_horizon = False
            # if nS is not None and set_ep[nS][1]  == '24h': above_horizon = True
        # #print(above_horizon)

        # txt = '   '
        # for idx, nR, nS, start in noDUSK_24h_segs:
            # if len(txt) > 8: txt += ", "
            # txt += DOY(idx)
            # if nR is not None: txt += " Rise {} ".format(nR)
            # if nS is not None: txt += " Set {} ".format(nS)
            # if start is None: sten = "both"
            # else: sten = "start" if start else "end"
            # txt += sten
        # if len(txt) > 3: print("segments adjoining the 24h border:\n" + txt)

        # # inspect segment endpoints during noDUSK chronologically...
        # n = len(noDUSK_24h_segs)
        # idx0 = idx1 = None
        # for index, item in enumerate(noDUSK_24h_segs):
            # idx, nR, nS, start = item
            # if nR is not None and start is None:
                # above_horizon = not above_horizon
                # if above_horizon: idx0 = idx
                # else:             idx1 = idx
            # else:
                # if nR is not None and start:     idx0 = idx; above_horizon = True
                # if nR is not None and not start: idx1 = idx; above_horizon = False
            # if nS is not None and not start: idx0 = idx; above_horizon = True
            # if nS is not None and start:     idx1 = idx; above_horizon = False

            # if index == 0   and idx0 is None and idx1 is not None: idx0 = noDUSK_fr
            # if index == n-1 and idx0 is not None and idx1 is None: idx1 = noDUSK_to
            # if idx0 is not None and idx1 is not None and idx1 > idx0:
                # if config.debug_24h_contour: print("        {:6} to {:6}".format(DOY(idx0),DOY(idx1)))
                # noDUSK_24h_contour.append((idx0, idx1))
                # idx0 = idx1 = None

        # if n == 0 and above_horizon:  # if no RISE/SET segments that "contact" 24h during noDUSK
            # idx0 = noDUSK_fr; idx1 = noDUSK_to
            # if config.debug_24h_contour: print("        {:6} to {:6}".format(DOY(idx0),DOY(idx1)))
            # noDUSK_24h_contour.append((idx0, idx1))


# ---------------------------------------------------------------------------
# ---------------   determine relation of segments adjoining  ---------------
# -----------  'planet all day below horizon' to Meridian Passage  ----------
# -----------   WHY? IS THIS STILL MEANINGFUL? ??????????????????
# ---------------------------------------------------------------------------

    global rise_seg_done, set_seg_done
    rise_seg_done = []      # list of segments processed
    set_seg_done = []       # list of segments processed

    #     the variables ab_RbDAH ab_SbDAH ab_RaDAH ab_SaDAH are no longer
    #       used in the 'planet all day below horizon' shading section

    # if dah != []:
        # # variables relating to segments that contact the DAH zone
        # ab_RbDAH = ab_SbDAH = ab_RaDAH = ab_SaDAH = None
        # for txt, rise_seg, rise_ab in dahseg[0]:
            # if txt == "RISE_before_dah":
                # if rise_days[rise_seg] == 0: continue   # ignore zero length segments
                # ab_RbDAH = rise_ab; rise_segB = rise_seg; break
        # for txt, set_seg, set_ab in dahseg[0]:
            # if txt == "SET_before_dah":
                # if set_days[set_seg] == 0: continue     # ignore zero length segments
                # ab_SbDAH = set_ab; set_segB = set_seg; break
        # for txt, rise_seg, rise_ab in dahseg[0]:
            # if txt == "RISE_after_dah":
                # if rise_days[rise_seg] == 0: continue   # ignore zero length segments
                # ab_RaDAH = rise_ab; rise_segA = rise_seg; break
        # for txt, set_seg, set_ab in dahseg[0]:
            # if txt == "SET_after_dah":
                # if set_days[set_seg] == 0: continue     # ignore zero length segments
                # ab_SaDAH = set_ab; set_segA = set_seg; break
    # else:
        # ab_RbDAH = ab_SbDAH = ab_RaDAH = ab_SaDAH = 3     # fake 4x same value

    # print("ab_RbDAH = {}, ab_SbDAH = {}, ab_RaDAH = {}, ab_SaDAH = {}".format(ab_RbDAH,ab_SbDAH,ab_RaDAH,ab_SaDAH))

    # beware of segments that border more than one shading area!
    rise_seg = set_seg = None

    # DO NOT ATTEMPT to process zero length segments (with just 1 value in the segment)
    #   if they occur on Jan 1 or EOY (Jan 1 next year) .... otherwise
    #   WE NEED TO PROCESS zero length segments mid-year, e.g. Mercury 2020 65°N
    for ndx, lnth in enumerate(rise_days):
        idx = rise_offset[ndx]
        if lnth == 0 and (idx == 0 or idx == daystoprocess-1):
            rise_seg_done.append(ndx)
    for ndx, lnth in enumerate(set_days):
        idx = set_offset[ndx]
        if lnth == 0 and (idx == 0 or idx == daystoprocess-1):
            set_seg_done.append(ndx)

    #       DON'T MARK AS PROCESSED ... (Mercury 2023 67°N)
    # mark SET-to-RISE bands as 'already processed ..... they will
    # be picked up later in the 'GENERIC: SET-to-RISE band' section
    # for Sseg, Rseg in set_to_rise_pair:
        # rise_seg_done.append(Rseg)
        # set_seg_done.append(Sseg)

    #pBh_before = pBh_after = None       # ------------------ both O B S O L E T E ------------------
    pBh_before = []
    pBh_after = []
    #if dbh != []:
    for zone, ndx in enumerate(dbhoffset):
        pBh_before.append(None)
        pBh_after.append(None)
        # get the segments to process before DBH
        # note: the first match is found (zero length segments are ignored)
        rise_seg = set_seg = None
        fnd = 0     # check both are found below...
        for txt, r_seg in dbhseg[zone]:
            if txt == "RISE_before_dbh":
                if r_seg in rise_seg_done: continue
                fnd += 1; rise_seg = r_seg; break
        for txt, s_seg in dbhseg[zone]:
            if txt == "SET_before_dbh":
                if s_seg in set_seg_done: continue
                fnd += 1; set_seg = s_seg; break

        if fnd == 2:
            xS,yS = getXY(objset_XY_txt[set_seg][0])    # start of SET  before DBH
            xR,yR = getXY(objrise_XY_txt[rise_seg][0])  # start of RISE before DBH
            xSe,ySe = getXY(objset_XY_txt[set_seg][-1])   # end of SET  before DBH
            xRe,yRe = getXY(objrise_XY_txt[rise_seg][-1]) # end of RISE before DBH

            # are both ySe and yRe on the same side of the Meridian Passage?
            idx_frR = rise_offset[rise_seg]
            idx_toR = idx_frR + len(objrise_XY_txt[rise_seg]) -1
            idx_frS = set_offset[set_seg]
            idx_toS = idx_frS + len(objset_XY_txt[set_seg]) -1
            mpass = meridian_pass[idx_toS]

            #print(pBh_before)
            # if len(dbhoffset) <= 3:
            pBh_before[zone] = 0       # 'planet all day below horizon zone' RISE < mpass & SET > mpass
            if ySe < mpass and yRe < mpass:
                pBh_before[zone] = -1  # 'planet all day below horizon zone' RISE & SET below mpass
            if ySe > mpass and yRe > mpass:
                pBh_before[zone] = 1   # 'planet all day below horizon zone' RISE & SET above mpass
            prnt("   pBh_before(DBH zone {}) = {:2}  RISE seg {}, SET seg {}".format(zone,pBh_before[zone], rise_seg, set_seg))

        # get the segments to process after DBH
        # note: zero length segments have to be skipped (as they are the first match)
        rise_seg = set_seg = None
        fnd = 0     # check both are found below...
        for txt, r_seg in dbhseg[zone]:
            if txt == "RISE_after_dbh":
                if r_seg in rise_seg_done: continue
                if rise_days[r_seg] == 0: continue      # ignore zero length segments
                fnd += 1; rise_seg = r_seg; break
        for txt, s_seg in dbhseg[zone]:
            if txt == "SET_after_dbh":
                if s_seg in set_seg_done: continue
                if set_days[s_seg] == 0: continue       # ignore zero length segments
                fnd += 1; set_seg = s_seg; break

        if fnd == 2:
            xS,yS = getXY(objset_XY_txt[set_seg][0])    # start of SET  after DBH
            xR,yR = getXY(objrise_XY_txt[rise_seg][0])  # start of RISE after DBH
            xSe,ySe = getXY(objset_XY_txt[set_seg][-1])   # end of SET  after DBH
            xRe,yRe = getXY(objrise_XY_txt[rise_seg][-1]) # end of RISE after DBH

            # are both ySe and yRe on the same side of the Meridian Passage?
            idx_frR = rise_offset[rise_seg]
            idx_toR = idx_frR + len(objrise_XY_txt[rise_seg]) -1
            idx_frS = set_offset[set_seg]
            idx_toS = idx_frS + len(objset_XY_txt[set_seg]) -1
            mpass = meridian_pass[idx_frS]

            # skip 'pBh_after' setup if >= 2 DBH zones (Mercury 2024 69°N)
            # if len(dbhoffset) <= 3:
            pBh_after[zone] = 0         # 'planet all day below horizon zone' RISE < mpass & SET > mpass
            if yS < mpass and yR < mpass:
                pBh_after[zone] = -1    # 'planet all day below horizon zone' RISE & SET below mpass
            if yS > mpass and yR > mpass:
                pBh_after[zone] = 1     # 'planet all day below horizon zone' RISE & SET above mpass
            prnt("   pBh_after (DBH zone {}) = {:2}  RISE seg {}, SET seg {}".format(zone,pBh_after[zone], rise_seg, set_seg))

    #print(pBh_before)
# ---------------------------------------------------------------------------
# ---------------   determine relation of segments adjoining  ---------------
# -----------  'planet all day above horizon' to Meridian Passage  ----------
# ---------------------------------------------------------------------------

    #pAh_before = pAh_after = None       # ----------------- pAh_after O B S O L E T E ? -----------------
    pAh_before = []
    pAh_after = []
    #if dah != []:
    for zone, ndx in enumerate(dahoffset):
        pAh_before.append(None)
        pAh_after.append(None)
        # ========== get the segments to process before a DAH zone ==========
        # note: the first match is found (zero length segments are ignored)
        rise_seg = set_seg = None
        fnd = 0       # check both are found below...
        for txt, r_seg, rise_ab in dahseg[zone]:
            if txt == "RISE_before_dah":
                if r_seg in rise_seg_done: continue
                #if rise_days[r_seg] == 0: continue      # ignore zero length segments
                fnd += 1; rise_seg = r_seg; break
        for txt, s_seg, set_ab in dahseg[zone]:
            if txt == "SET_before_dah":
                if s_seg in set_seg_done: continue
                #if set_days[s_seg] == 0: continue       # ignore zero length segments
                fnd += 1; set_seg = s_seg; break

        if fnd == 2:
            xS,yS = getXY(objset_XY_txt[set_seg][0])    # start of SET  before DAH
            xR,yR = getXY(objrise_XY_txt[rise_seg][0])  # start of RISE before DAH
            xSe,ySe = getXY(objset_XY_txt[set_seg][-1])   # end of SET  before DAH
            xRe,yRe = getXY(objrise_XY_txt[rise_seg][-1]) # end of RISE before DAH
            # print("  ySe = {}  yRe = {}  fnd = {} set_seg = {}".format(ySe,yRe,fnd,set_seg))

            # are both ySe and yRe on the same side of the Meridian Passage?
            idx_frR = rise_offset[rise_seg]
            idx_toR = idx_frR + len(objrise_XY_txt[rise_seg]) -1
            idx_frS = set_offset[set_seg]
            idx_toS = idx_frS + len(objset_XY_txt[set_seg]) -1
            mpass = meridian_pass[idx_toS]

            # if len(dahoffset) <= 3:
            pAh_before[zone] = 0       # 'planet all day above horizon zone' RISE < mpass < SET
            if ySe < mpass and yRe < mpass:
                pAh_before[zone] = -1  # 'planet all day above horizon zone' RISE & SET below mpass
            if ySe > mpass and yRe > mpass:
                pAh_before[zone] = 1   # 'planet all day above horizon zone' RISE & SET above mpass
            prnt("   pAh_before(DAH zone {}) = {:2}  RISE seg {}, SET seg {}".format(zone,pAh_before[zone], rise_seg, set_seg))

        # ========== get the segments to process after a DAH zone ==========
        # note: zero length segments have to be skipped (as they are the first match)
        rise_seg = set_seg = None
        fnd = 0       # check both are found below...
        for txt, r_seg, rise_ab in dahseg[zone]:
            if txt == "RISE_after_dah":
                if r_seg in rise_seg_done: continue
                if rise_days[r_seg] == 0: continue
                fnd += 1; rise_seg = r_seg; break
        for txt, s_seg, set_ab in dahseg[zone]:
            if txt == "SET_after_dah":
                if s_seg in set_seg_done: continue
                if set_days[s_seg] == 0: continue
                fnd += 1; set_seg = s_seg; break

        if fnd == 2:
            xS,yS = getXY(objset_XY_txt[set_seg][0])    # start of SET  after DAH
            xR,yR = getXY(objrise_XY_txt[rise_seg][0])  # start of RISE after DAH
            xSe,ySe = getXY(objset_XY_txt[set_seg][-1])   # end of SET  after DAH
            xRe,yRe = getXY(objrise_XY_txt[rise_seg][-1]) # end of RISE after DAH
            # print("  ySe = {}  yRe = {}  fnd = {} set_seg = {}".format(ySe,yRe,fnd,set_seg))

            # are both ySe and yRe on the same side of the Meridian Passage?
            idx_frR = rise_offset[rise_seg]
            idx_toR = idx_frR + len(objrise_XY_txt[rise_seg]) -1
            idx_frS = set_offset[set_seg]
            idx_toS = idx_frS + len(objset_XY_txt[set_seg]) -1
            mpass = meridian_pass[idx_frS]

            # if len(dahoffset) <= 3:
            pAh_after[zone] = 0       # 'planet all day above horizon zone' RISE < mpass < SET
            if yS < mpass and yR < mpass:
                pAh_after[zone] = -1  # 'planet all day above horizon zone' RISE & SET below mpass
            if yS > mpass and yR > mpass:
                pAh_after[zone] = 1   # 'planet all day above horizon zone' RISE & SET above mpass
            prnt("   pAh_after (DAH zone {}) = {:2}  RISE seg {}, SET seg {}".format(zone,pAh_after[zone], rise_seg, set_seg))

# ----------------------------------------------------------------------------
# ------------ establish 'dayinitial' and 'dayfinal' based on DBH ------------
# ----------------------------------------------------------------------------

    # dayinitial = 0
    # dayfinal = daystoprocess-1
    # fdaDBH_X = 0.0              # in tikz units
    # ldbDBH_X = float("%04.3f"%((daystoprocess-1)/10*sf))  # in tikz units
    # fdaDBH = 0                  # first day (offset) after DBH at beginning of year
    # ldbDBH = daystoprocess-1    # last  day (offset) before DBH at end of year
    # if dbh != []:
        # if dbh[-1] == daystoprocess-1:
            # n = daystoprocess - 1
            # i = -1
            # while -i <= len(dbh):
                # if dbh[i] != n: break
                # dayfinal = dbh[i]
                # n -= 1
                # i -= 1
            # dayfinal -= 1
            # idx0 = dayfinal/10*sf
            # idxs = "%04.3f" % idx0  # rounded value
            # ldbDBH_X = float(idxs)  # tikz units
            # ldbDBH = dayfinal       # day offset
            # print("last day before DBH at end of year: {} offset {} x={}".format(DOY(dayfinal),dayfinal,idxs))
        # if dbh[0] == 0:
            # n = 0
            # for idx in sdbh:
                # if idx == n: dayinitial = idx
                # else: break
                # n += 1
            # dayinitial += 1
            # idx0 = dayinitial/10*sf
            # idxs = "%04.3f" % idx0  # rounded value
            # fdaDBH_X = float(idxs)  # tikz units
            # fdaDBH = dayinitial
            # print("first day after DBH at beginning of year: {} offset {} x={}".format(DOY(dayinitial),dayinitial,idxs))

# ----------------------------------------------------------------------
# --------------  handle solitary evets before/after DAH  --------------
#       O N L Y   R E Q U I R E D   f o r   G R E Y   S H A D I N G
#          e.g.  Mercury 71°N 2000
# ----------------------------------------------------------------------

# Solitary RISE/SET events (with length 1 day) are removed from the list of segments that require
#  to be in a path that describes an area to be filled with colour (because they have no width).

# For charting purposes a solitary event before/after a DAH zone can be
# handled by substituting a start or end point of the adjoining segment
# with '00h' for the lower border or '24h' for the upper border as follows:

# Solitary SET '00h' before RISE segment 'n' end before DAH zone:   RISE n end   'DAH' --> '00h'
# Solitary SET '00h' before RISE segment 'n' start after DAH zone:  RISE n start 'DAH' --> '00h'
# Solitary RISE '24h' after SET segment 'n' end before DAH zone:    SET n  end   'DAH' --> '24h'
# Solitary RISE '24h' after SET segment 'n' start after DAH zone:   SET n  start 'DAH' --> '24h'

    global RISEep, SETep
    # on lists & dicts, DO NOT USE: RISEep = rise_ep    !!!!!!!!!!!!
    RISEep = rise_ep.copy()     # keep original for gold shading
    SETep  = set_ep.copy()      # keep original for gold shading

    for zone, ndx in enumerate(dahoffset):      # for each DAH zone...
        # first gather the non-zero length segments adjoining each DAH zone...
        Rbefore = Rafter = Sbefore = Safter = None
        Rstart = Rend = Sstart = Send = None

        for txt, seg, merpass_ab in dahseg[zone]:
            if txt == "RISE_before_dah" and rise_days[seg] != 0:
                Rbefore = seg; Rend = rise_ends[seg]

            if txt == "SET_before_dah" and set_days[seg] != 0:
                Sbefore = seg; Send = set_ends[seg]

            if txt == "RISE_after_dah" and rise_days[seg] != 0:
                Rafter = seg; Rstart = rise_starts[seg]

            if txt == "SET_after_dah" and set_days[seg] != 0:
                Safter = seg; Sstart = set_starts[seg]
        # ----------------------------------------- end of 'for'

        # now search for zero-length solitary RISE/SET events adjoining each DAH zone...
        # ... and PATCH the segment adjoining the DAH zone accordingly (replace the tuple)
        for txt, seg, merpass_ab in dahseg[zone]:

            if txt == "RISE_before_dah" and rise_days[seg] == 0:
                if Send == rise_ends[seg]:
                    prnt("patch SET seg {} end: {} --> {}".format(Sbefore,set_ep[Sbefore][1],rise_ep[seg][1]))
                    set_ep[Sbefore] = (set_ep[Sbefore][0], rise_ep[seg][1])

            if txt == "SET_before_dah" and set_days[seg] == 0:
                if Rend == set_ends[seg]:
                    prnt("patch RISE seg {} end: {} --> {}".format(Rbefore,rise_ep[Rbefore][1],set_ep[seg][1]))
                    rise_ep[Rbefore] = (rise_ep[Rbefore][0], set_ep[seg][1])

            if txt == "RISE_after_dah" and rise_days[seg] == 0:
                if Sstart == rise_starts[seg]:
                    prnt("patch SET seg {} start: {} --> {}".format(Safter,set_ep[Safter][0],rise_ep[seg][0]))
                    set_ep[Safter] = (rise_ep[seg][0], set_ep[Safter][1])

            if txt == "SET_after_dah" and set_days[seg] == 0:
                if Rstart == set_starts[seg]:
                    prnt("patch RISE seg {} start: {} --> {}".format(Rafter,rise_ep[Rafter][0],set_ep[seg][0]))
                    rise_ep[Rafter] = (set_ep[seg][0], rise_ep[Rafter][1])
        # ----------------------------------------- end of 'for'
    # ----------------------------------------- end of 'for'
    # print(RISEep)
    # print(RISEep is rise_ep)


# ------------------------------------------------------------------------
# --------------  collect useful data for TEXTt annotations  --------------
# ------------------------------------------------------------------------

    # we need to define 'meridian passage' now but use tex999 later
    tex999 = LocalMeanTimeOfMeridianPassage(obj, object_name, object_XY_txt)
    # get text positioning metadata for 'below horizon'...
    #   as lower meridian transit date offset per hour of day
    listLT, altLT = LocalMeanTimeOfLowerTransit()

    # calculate visibility per day ...
    #vis_stat, vis_frto = vis_per_day(dbh, verticals, objrise_Y, objset_Y, civilY_AM, civilY_PM)
    vis_stat, vis_frto = vis_per_day(dbh, verticals)
    hrAMfr, hrAMto, hrPMfr, hrPMto = vis_frto
    if config.debug_visibility:
        for i in range(len(verticals)):
            idx = verticals[i]
            hrAMf = "{:4.1f}".format(hrAMfr[i]) if hrAMfr[i] is not None else "None"
            hrAMt = "{:4.1f}".format(hrAMto[i]) if hrAMto[i] is not None else "None"
            hrPMf = "{:4.1f}".format(hrPMfr[i]) if hrPMfr[i] is not None else "None"
            hrPMt = "{:4.1f}".format(hrPMto[i]) if hrPMto[i] is not None else "None"
            prnt("{:6}:   AM {}-{}   PM {}-{}".format(DOY(idx),hrAMf,hrAMt,hrPMf,hrPMt))

    # # get text positioning metadata for 'planet visible'...
    idx_hrAM, hrAM, idx_hrPM, hrPM = Planet_Vis_Zone(verticals, vis_frto)
    # vis_preMP, vis_postMP, idx_vispreMP_max, idx_vispostMP_max = Planet_Vis_Zone(verticals, vis_frto)
    # print("vis_preMP ",vis_preMP)
    # print("vis_postMP",vis_postMP)

    # get text positioning metadata for 'above horizon with sun'...
    # hr_preMP, hr_postMP, idx_preMP_max, idx_postMP_max, ang_preMP, ang_postMP = Planet_Sun_Zone(dbh, verticals, objrise_Y, objset_Y, civilY_AM, civilY_PM)
    hr_preMP, hr_postMP, idx_preMP_max, idx_postMP_max, ang_preMP, ang_postMP = Planet_Sun_Zone(dbh, verticals)


# .....................................................................
# ..............  add   T E X T  /  A N N O T A T I O N  ..............
# ..............      "<planet name>", "visible"         ..............
# .....................................................................
#   Note: text is printed with a white background for better readability.
#   Note: this text may in a few cases be overwriten by a neighbouring grey or gold shaded area.
#         (See Mars 2003 72°N.)

    idx = idx_hrAM
    if idx is not None:
        d = d00 + timedelta(days=idx)
        m = planet_mag(obj, d, hrAM)
        tn = 1 + ((obj-1)*3)
        xy0 = [idx/10*sf, (hrAM + 0.35)*sf]
        xy1 = [idx/10*sf, (hrAM - 0.35)*sf]
        tex += printlabelXY(txt_text[tn], xy0, 0.0, 'gray')     # with white background
        tex += printlabelXY("visible m{:3.1f}".format(m), xy1, 0.0, 'gray') # with white background

    idx = idx_hrPM
    if idx is not None:
        d = d00 + timedelta(days=idx)
        m = planet_mag(obj, d, hrPM)
        tn = 1 + ((obj-1)*3)
        xy0 = [idx/10*sf, (hrPM + 0.35)*sf]
        xy1 = [idx/10*sf, (hrPM - 0.35)*sf]
        tex += printlabelXY(txt_text[tn], xy0, 0.0, 'gray')     # with white background
        tex += printlabelXY("visible m{:3.1f}".format(m), xy1, 0.0, 'gray') # with white background


# ||---------------------------------------------------------------------------||
# ||---------------------------------------------------------------------------||
# ||------ fill 'planet below horizon' (invisible due to altitude) areas ------||
# ||------ fill 'planet above horizon' invisible (between dawn and dusk) ------||
# ||---------------------------------------------------------------------------||
# ||---------------------------------------------------------------------------||

    shape = "rectangular area" if config.orthogonal else "rhomboid"
    prnt("   .   .   .   .   .   .  fill grey 'planet all day below horizon' {}  .   .   .   .   .   .".format(shape))

    # global code_cov   # for 'flush_AMbuf()' & 'flush_PMbuf()'
    code_cov = []       # code coverage ... list of trace# used
    # global PM_cov     # code coverage is written to file
    # global AM_cov     # code coverage is written to file
    PM_cov = []         # code coverage within 'UPPER_back()'
    AM_cov = []         # code coverage within 'LOWER_forw()'
    below_horizon = []  # list of tuples (hr, idx) where 'below horizon' labels are placed
    global helix        # for 'fillpath()'
    helix = 0 if config.orthogonal else 1   # day offset for chart top border
    maxXY = "(%04.3f, %04.3f)" %(xmax*sf,ymax*sf)
    maxX, maxY = tikzXY(maxXY)   # scaled (tikz) values!

# ...........................................................
# ...... FILL 'all day below horizon' grey rectangles .......
# ...... do this now not to overwrite text annotations ......
# ...........................................................

    if not config.PV_nsb and not config.PV_nsdbh and dbh != []:

        shape = "rectangular area" if config.orthogonal else "rhomboid"

        for rng in dbh_range:
            dbh_fr = rng.start; dbh_to = rng.stop - 1
            path = ''
            tex += r"""
%%
%% fill ----- %s 'all day below horizon' from %s to %s -----""" %(shape,DOY(dbh_fr),DOY(dbh_to))

            idx_fr = dbh_fr - 1 if dbh_fr > 0 else 0
            idx_to = dbh_to + 1 # (also includes Jan 1 of next year)
            if idx_to >= daystoprocess: idx_to = daystoprocess-1    # Venus 2028 68°N

            path += 'B' + str(idx_fr) + ','     # bottom left
            path += 'T' + str(idx_fr) + ','     # top left
            path += 'T' + str(idx_to) + ','     # top right
            path += 'B' + str(idx_to) + ','     # bottom right (of rectangle)

            if idx_to - idx_fr > 25:    # add "below horizon" if DBH wide enough

                # .....................................................................
                # ..............  add   T E X T  /  A N N O T A T I O N  ..............
                # ..............         reserve "below horizon"         ..............
                # .....................................................................
                # reserve "below horizon" locations (DO NOT PRINT YET ... grey shading will overwrie it)
                mid_idx = int((idx_fr + idx_to) / 2.0)      # mid-idx
                for hr in [2, 22]:
                    # xy0 = [mid_idx/10*sf, (hr + 0.35)*sf]   # print near 'hr'
                    # xy1 = [mid_idx/10*sf, (hr - 0.35)*sf]
                    # tex += printlabelXY("below", xy0, 0.0, 'white', False)
                    # tex += printlabelXY("horizon", xy1, 0.0, 'white', False)
                    below_horizon.append((hr, mid_idx))

            path = path[:-1]
            p = path
            tp = []
            txt = 'path:'
            n = p.find(',', 70)
            while n != -1:
                prnt("      {}       {}".format(txt,p[:n+1]))
                tp.append("{} {}".format(txt,p[:n+1]))
                txt = '     '
                p = p[n+1:]
                n = p.find(',', 70)
            prnt("      {}       {}".format(txt,p))
            tp.append("{} {}".format(txt,p))

            tex += fillpath(path, 'LightSlateGrey', '0.9', tp)
        # ----------------------------------------- end of 'for'

# .............................................................
# ......     FILL 'all day above horizon' gold areas     ......
# ...... (rectangles or rhomboids between dawn and dusk) ......
# ......  do this now not to overwrite text annotations  ......
# .............................................................

    prnt("   .   .   .   .   .   .  fill gold 'planet all day above horizon' {}  .   .   .   .   .   .".format(shape))

    if not config.PV_nsa and not config.PV_nsdah and dah != []:

        DAWN_fr, DAWN_to, DUSK_fr, DUSK_to, noDAWN_fr, noDAWN_to, noDUSK_fr, noDUSK_to = getDAWN_DUSK()

        shape = "rectangular area" if config.orthogonal else "rhomboid"

        for rng in dah_range:
            dwn_fr = dsk_fr = dwn_fr2 = dsk_fr2 = -1
            dwn_to = dsk_to = dwn_to2 = dsk_to2 = -1
            dah_fr = rng.start; dah_to = rng.stop - 1
            path = ''
            tex += r"""
%%
%% fill ----- %s 'all day above horizon' from %s to %s -----""" %(shape,DOY(dah_fr),DOY(dah_to))

            idx_fr = dah_fr - 1 if dah_fr > 0 else 0    # shading starts one day before DAH
            idx_to = dah_to + 1 # (also includes Jan 1 of next year)
            if idx_to >= daystoprocess: idx_to = daystoprocess-1
            #....................................................................................

            if DAWN_to < idx_fr < DAWN_fr:      # if idx_fr during noDAWN
                path += 'B' + str(idx_fr) + ','

            if DAWN_to >= idx_fr or DAWN_fr <= idx_to:  # if DAWN within range idx_fr - idx_to
                # not for Mars 69°-72°N 2015

                for idx in range(idx_fr, idx_to+1):           # scan forwards
                    if idx <= DAWN_to:
                        if dwn_fr == -1: dwn_fr = idx
                        dwn_to = idx

                    if idx >= DAWN_fr:
                        if dwn_fr2 == -1: dwn_fr2 = idx
                        dsk_to2 = idx
                # ----------------------------------------- end of 'for'

                if idx_fr <= DAWN_to:
                    path += 'dawn:' + str(dwn_fr) + '-' + str(dwn_to) + ','
                    if 0 <= dwn_to < idx_to:
                        path += 'B' + str(dwn_to) + ','

                if idx_to >= DAWN_fr:
                    path += 'B' + str(dwn_fr2) + ','
                    path += 'dawn:' + str(dwn_fr2) + '-' + str(idx_to) + ','
                # elif dwn_to < idx_to:
                    # path += 'B' + str(idx_to) + ','     # Mercury 72°N 2010

            if DAWN_to < idx_to < DAWN_fr:      # if idx_to during noDAWN
                # not for Mars 69°-72°N 2015
                path += 'B' + str(idx_to) + ','
            #....................................................................................

            if DUSK_to < idx_to < DUSK_fr:      # if idx_to during noDUSK
                path += 'T' + str(idx_to) + ','

            if DUSK_to >= idx_fr or DUSK_fr <= idx_to:  # if DUSK within range idx_fr - idx_to

                for idx in range(idx_to, idx_fr-1, -1):       # scan backwards
                    if idx >= DUSK_fr:
                        if dsk_fr == -1: dsk_fr = idx
                        dsk_to = idx

                    if idx <= DUSK_to:
                        if dsk_fr2 == -1: dsk_fr2 = idx
                        dsk_to2 = idx
                # ----------------------------------------- end of 'for'

                if idx_to >= DUSK_fr:
                    path += 'dusk:' + str(dsk_fr) + '-' + str(dsk_to) + ','
                    if dsk_to > idx_fr:
                        path += 'T' + str(dsk_to) + ','

                if idx_fr <= DUSK_to:
                    if dsk_fr2 < idx_to:
                        # path += 'T' + str(idx_to) + ','     # Mercury 72°N 2010
                        path += 'T' + str(dsk_fr2) + ','    # not for Mercury 71°N 2010
                    path += 'dusk:' + str(dsk_fr2) + '-' + str(idx_fr) + ','

            if DUSK_to < idx_fr < DUSK_fr:      # if idx_fr during noDUSK
                path += 'T' + str(idx_fr) + ','
            #....................................................................................

            path = path[:-1]
            p = path
            tp = []
            txt = 'path:'
            n = p.find(',', 70)
            while n != -1:
                prnt("      {}       {}".format(txt,p[:n+1]))
                tp.append("{} {}".format(txt,p[:n+1]))
                txt = '     '
                p = p[n+1:]
                n = p.find(',', 70)
            prnt("      {}       {}".format(txt,p))
            tp.append("{} {}".format(txt,p))

            tex += fillpath(path, 'Gold', '0.85', tp)
        # ----------------------------------------- end of 'for'

# .............................................................
# ......  gather events (rise, set, dawn, dusk) per day  ......
# .............................................................
 
    idx = 0
    Rseg = 0; Sseg = 0
    nRseg = len(rise_offset); nSseg = len(set_offset)
    hourR = None; hourS = None
    # dailyevents is a list of tuples (hour, type)
    #   RISE:   = segment number + 1
    #   SET:    = -segment number -1
    #   Dawn:   = +100
    #   Dusk    = -100
    dailyevents = []

    while idx < daystoprocess:
        eventsperday = []
        Rseg = 0; Sseg = 0

        while Rseg < nRseg:

            hourR = None
            risestarts = rise_starts[Rseg]
            if risestarts <= idx <= rise_ends[Rseg]:
                hourR = hourRISE[Rseg][idx-risestarts]

            if hourR is not None:
                eventsperday.append((hourR, Rseg+1))
            Rseg += 1
        # ----------------------------------------- end of 'while'

        while Sseg < nSseg:

            hourS = None
            setstarts = set_starts[Sseg]
            if setstarts <= idx <= set_ends[Sseg]:
                hourS = hourSET[Sseg][idx-setstarts]

            if hourS is not None:
                eventsperday.append((hourS, -Sseg-1))
            Sseg += 1
        # ----------------------------------------- end of 'while'


        eventsperday.append((f_AM(civilY_AM[idx]), 100))
        eventsperday.append((f_PM(civilY_PM[idx]), -100))
        sortedevents = sorted(eventsperday, key=lambda x: x[0])
        dailyevents.append(sortedevents)

        idx += 1
    # ----------------------------------------- end of 'while'

    #for idx in range(10):
        #print(dailyevents[idx])

# ............................................................
# .............  get sequence of events per day  .............
# ............................................................
 
    idx = 0
    all_et  = []    # sequence of events per day
    all_et0 = []    # sequence of events per day excluding 'Dawn', 'Dusk'
    while idx < daystoprocess:
        eventsperday = dailyevents[idx]
        et = ''     # all events
        et0 = ''    # events excluding 'Dawn', 'Dusk'
        for item in eventsperday:
            eventtype = item[1]
            if eventtype == 100: et += 'Dawn,'
            elif eventtype == -100: et += 'Dusk,'
            elif eventtype > 0:
                et  += 'r' + str(eventtype-1) + ','
                et0 += 'r' + str(eventtype-1) + ','
            else:
                et  += 's' + str(-eventtype-1) + ','
                et0 += 's' + str(-eventtype-1) + ','
        if len(et) > 0: et = et[:-1]
        if len(et0) > 0: et0 = et0[:-1]
        #if idx < 3: print("{:3d}  {}".format(idx,et))
        #if idx < 3: print("{:3d}  {}".format(idx,et0))
        all_et.append(et)
        all_et0.append(et0)

        idx += 1
    # ----------------------------------------- end of 'while'


# ||---------------------------------------------------------------------------||
# ||---------------------------------------------------------------------------||
# ||-----  fill 'planet below horizon' (invisible due to altitude) areas  -----||
# ||-----------------------------  (shaded GREY)  -----------------------------||
# ||---------------------------------------------------------------------------||

    prnt("   .   .   .   .   .   .   .  fill grey 'planet below horizon' areas  .   .   .   .   .   .   .")

    if not config.PV_nsb:   # and not config.PV_nsdbh:
        rise_seg_done.sort()
        set_seg_done.sort()
        msgR = "   rise_seg_done {}".format(rise_seg_done)
        msg  = msgR + " "*(40-len(msgR)) + " set_seg_done {}".format(set_seg_done)
        prnt(msg)

#   >>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<
#   >>>>>>     CODE TO FILL AREAS BELOW HORIZON     <<<<<<
#   >>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<

        # CONDITION: the SET and RISE bands must overlap (share common dates)
        # Note: SET-to-RISE bands are stored as tuples in 'set_to_rise_pair'
        SRbands = 0     # count SET-to-RISE bands processed

        # !! process multiple SET-to-RISE bands !!
        for index,item in enumerate(SET_to_RISE_band):
            SRbands += 1
            set_segs, rise_segs = item
            msg0 = SET_to_RISE_band_txt[index]
            msg5 = ">process {} band".format(msg0)

            # print(">process SET-to-RISE band: SET seg {} & RISE seg {}".format(set_seg, rise_seg))
            prnt(msg5)
            tccdata += "\n" + msg5

            tex += fill_below_horizon(obj, set_segs, rise_segs)
        # ----------------------------------------- end of 'for'

        rise_seg_done.sort()
        set_seg_done.sort()
        msgR = "   rise_seg_done {}".format(rise_seg_done)
        msg  = msgR + " "*(40-len(msgR)) + " set_seg_done {}".format(set_seg_done)
        prnt(msg)

        # !! process multiple RISE-to-SET bands !!
        for index,item in enumerate(RISE_to_SET_band):
            rise_segs, set_segs = item
            msg1 = RISE_to_SET_band_txt[index]
            msg6 = ">process {} band".format(msg1)
            
            prnt(msg6)
            tccdata += "\n" + msg6

            # for segR in rise_segs:
                # if not segR in rise_seg_done:
                    # tex += fill_below_horizon(obj, [], [segR], False)

            # for segS in set_segs:
                # if not segS in set_seg_done:
                    # tex += fill_below_horizon(obj, [segS], [], False)

            tex += fill_below_horizon(obj, set_segs, rise_segs)
        # ----------------------------------------- end of 'for'


# .....................................................................
# ..............  add   T E X T  /  A N N O T A T I O N  ..............
# ..............         reserve "below horizon"         ..............
# .....................................................................

        if SRbands > 0:
    #       reserve "below horizon" locations (DO NOT PRINT YET ... grey shading will overwrie it)
            hr_done = 26    # permit first value (hr = 22)
            for hr in range(22,1,-1):
                if hr_done - hr < 4: continue   # separate labels by 4hr minimum
                for idx in listLT[hr]:
                    if dah != []:   # exclude dates close to DAH
                        if dah[0] - 15 < idx < dah[-1] + 15: continue

                    tryit = True
                    # for multiple DBH
                    for n, i in enumerate(dbhoffset):
                        dbh_fr = dbh[i]
                        dbh_to = dbh[-1]
                        if n+1 < len(dbhoffset): dbh_to = dbh[dbhoffset[n+1]-1]
                        if dbh_fr - 15 < idx < dbh_to + 15: tryit = False

                    if tryit:
                        daymax = daystoprocess-78 if hr == 1 else daystoprocess-21  # leave room for Copyright text
                        if 20 <= idx <= daymax: # keep distance from left&right border
                            # xy0 = [idx/10*sf, (hr + 0.35)*sf]   # print near 'hr'
                            # xy1 = [idx/10*sf, (hr - 0.35)*sf]
                            # tex += printlabelXY("below", xy0, 0.0, 'white', False)
                            # tex += printlabelXY("horizon", xy1, 0.0, 'white', False)
                            hr_done = hr
                            below_horizon.append((hr, idx))
                            break
            # ----------------------------------------- end of 'for'

        if SRbands == 0: # and BHtext_section6:     # not for Saturn 2025 15°S to 60°N
            prev_idx = None
            hr = 1 if len(listLT[2]) == 0 else 2    # try near 02h; 01h as last resort
            for idx in listLT[hr]:
                if dah != []:   # exclude dates close to DAH
                    if dah[0] - 15 < idx < dah[-1] + 15: continue

                tryit = True
                # for multiple DBH
                for n, i in enumerate(dbhoffset):
                    dbh_fr = dbh[i]
                    dbh_to = dbh[-1]
                    if n+1 < len(dbhoffset): dbh_to = dbh[dbhoffset[n+1]-1]
                    if dbh_fr - 15 < idx < dbh_to + 15: tryit = False

                if tryit:
                    # don't print two that are closer than 60 days...
                    if prev_idx is not None and abs(prev_idx - idx) < 60: continue
                    daymax = daystoprocess-78 if hr == 1 else daystoprocess-21  # leave room for Copyright text
                    if 20 <= idx <= daymax: # keep distance from left&right border
                        # xy0 = [idx/10*sf, (hr + 0.35)*sf]   # print near 'hr'
                        # xy1 = [idx/10*sf, (hr - 0.35)*sf]
                        # tex += printlabelXY("below", xy0, 0.0, 'white', False)
                        # tex += printlabelXY("horizon", xy1, 0.0, 'white', False)
                        prev_idx = idx
                        below_horizon.append((hr, idx))
            # ----------------------------------------- end of 'for'


# .....................................................................
# ..............  add   T E X T  /  A N N O T A T I O N  ..............
# ..............  "below horizon" anywhere on the chart  ..............
# .....................................................................

        # first print at the already selected label positions (stored already in 'below_horizon')
        for hr, idx in below_horizon:
            xy0 = [idx/10*sf, (hr + 0.35)*sf]   # print near 'hr'
            xy1 = [idx/10*sf, (hr - 0.35)*sf]
            tex += printlabelXY("below", xy0, 0.0, 'white', False)
            tex += printlabelXY("horizon", xy1, 0.0, 'white', False)
        # ----------------------------------------- end of 'for'

        for hr in [22,21,20,19,18,17,16,15,14,13,23,2,3,4,5,6,7,8,9,10,11,12,1]:
            for idx in listLT[hr]:
                # exclude dates close to DAH
                if dah != []:
                    if dah[0] - 15 < idx < dah[-1] + 15: continue

                tryit = True
                # exclude dates close to DBH
                for n, i in enumerate(dbhoffset):
                    dbh_fr = dbh[i]
                    dbh_to = dbh[-1]
                    if n+1 < len(dbhoffset): dbh_to = dbh[dbhoffset[n+1]-1]
                    if dbh_fr - 15 < idx < dbh_to + 15: tryit = False

                if tryit and below_horizon != []:
                    for hr_done, idx_done in below_horizon:
                        # permit labels that separated by more than 4hr -OR- 60 days...
                        if abs(hr - hr_done) < 4 and (abs(idx - idx_done) < 60): tryit = False
                        # print("{:2d} {:6}  {:5}  {:2d} {:6}".format(hr,DOY(idx),str(tryit),hr_done,DOY(idx_done)))
                if tryit:
                    daymax = daystoprocess-78 if hr == 1 else daystoprocess-21  # leave room for Copyright text
                    if 20 <= idx <= daymax: # keep distance from left&right border
                        xy0 = [idx/10*sf, (hr + 0.35)*sf]   # print near 'hr'
                        xy1 = [idx/10*sf, (hr - 0.35)*sf]
                        tex += printlabelXY("below", xy0, 0.0, 'white', False)
                        tex += printlabelXY("horizon", xy1, 0.0, 'white', False)
                        below_horizon.append((hr,idx))
        # ----------------------------------------- end of 'for'

# ........... final list of segments processed ...........

        rise_seg_done.sort()
        set_seg_done.sort()
        msgR = "   rise_seg_done {}".format(rise_seg_done)
        msg  = msgR + " "*(40-len(msgR)) + " set_seg_done {}".format(set_seg_done)
        prnt(msg)

# ||----------------------------------------------------------------------||
# ||----------------------------------------------------------------------||
# ||----  fill zones 'above horizon and between Civil Dawn and Dusk'  ----||
# ||---------------------------  (shaded GOLD)  --------------------------||
# ||----------------------------------------------------------------------||

    rise_seg_done = []      # list of segments processed (emptied)
    set_seg_done = []       # list of segments processed (emptied)
    # required for trace#80 onwards ...
    civil_dawn_done = []    # list of (from,to) dates processed along Civil DAWN
    civil_dusk_done = []    # list of (from,to) dates processed along Civil DUSK

    # ................... IMPORTANT ...................
    # Add dates with a solitary RISE and SET into civil_dawn_done and/or civil_dusk_done
    # to prevent the 'trace#80' and 'trace#90' sections trying to handle them! (Mercury 2024 72°N)
    for seg in solitary_RISE_seg:
        xR, yR = getXY(objrise_XY_txt[seg][0])
        for seg in solitary_SET_seg:
            xS, yS = getXY(objset_XY_txt[seg][0])
            if xR == xS:    # if solitary RISE and SET events are on the same day
                if yR < f_AM(civilY_AM[xR]) < yS: civil_dawn_done.append((xR, xR)); check_dawn(civil_dawn_done)
                if yR < f_PM(civilY_PM[xS]) < yS: civil_dusk_done.append((xS, xS)); check_dusk(civil_dusk_done)
        # ----------------------------------------- end of 'for'
    # ----------------------------------------- end of 'for'

    prnt("   .   .   .   .   .   .   .   . fill gold 'dawn-to-dusk' areas .   .   .   .   .   .   .   .")

#   >>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<
#   >>>>>>     CODE TO FILL AREAS ABOVE HORIZON     <<<<<<
#   >>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<

    if not config.PV_nsa:
        rise_seg_done.sort()
        set_seg_done.sort()
        msgR = "   rise_seg_done {}".format(rise_seg_done)
        msg  = msgR + " "*(40-len(msgR)) + " set_seg_done {}".format(set_seg_done)
        prnt(msg)

        msg6 = ''
        for index,item in enumerate(RISE_to_SET_band):      # process multiple RISE-to-SET bands
            rise_segs, set_segs = item
            msg1 = RISE_to_SET_band_txt2[index]
            msg6 += ">process {} band".format(msg1)

            prnt(msg6)
            tccdata += "\n" + msg6
            tex += fill_above_horizon(obj, rise_segs, set_segs)
            msg6 = "----------------------------------------\n"
        # ----------------------------------------- end of 'for'

        # for index,item in enumerate(SET_to_RISE_band):      # process multiple SET-to-RISE bands
            # # e.g. Jupiter 69°N 2000, Saturn 72°N 2000
            # set_segs, rise_segs = item
            # msg0 = SET_to_RISE_band_txt[index]
            # msg5 = ">process {} band".format(msg0)

            # # print(">process SET-to-RISE band: SET seg {} & RISE seg {}".format(set_seg, rise_seg))
            # print(msg5)
            # tccdata += "\n" + msg5

            # tex += fill_above_horizon(obj, rise_segs, set_segs)
        # # ----------------------------------------- end of 'for'

        if msg6 != '':
            rise_seg_done.sort()
            set_seg_done.sort()
            msgR = "   rise_seg_done {}".format(rise_seg_done)
            msg  = msgR + " "*(40-len(msgR)) + " set_seg_done {}".format(set_seg_done)
            prnt(msg)

        # check for unprocessed SET segments
        Sseg = 0
        nn = 0
        while len(set_days) > Sseg:

            #print("SET seg {}".format(str(Sseg)))
            if Sseg not in set_seg_done:
                Stxt = 's' + str(Sseg)
                Slen = set_days[Sseg]
                nn += 1

                msg6 += ">process SET segment {} {}".format(str(Sseg), str(SETep[Sseg]))
                prnt(msg6)
                tccdata += "\n" + msg6
                tex += fill_SET_above_horizon(obj, Sseg)

            Sseg += 1
            msg6 = "----------------------------------------\n"
        # ----------------------------------------- end of 'while'

        if nn > 0:
            rise_seg_done.sort()
            set_seg_done.sort()
            msgR = "   rise_seg_done {}".format(rise_seg_done)
            msg  = msgR + " "*(40-len(msgR)) + " set_seg_done {}".format(set_seg_done)
            prnt(msg)

        # check for unprocessed RISE segments
        Rseg = 0
        nn = 0
        while len(rise_days) > Rseg:

            #print("RISE seg {}".format(str(Rseg)))
            if Rseg not in rise_seg_done:
                Rtxt = 's' + str(Rseg)
                Rlen = rise_days[Rseg]
                nn += 1

                msg6 += ">process RISE segment {} {}".format(str(Rseg), str(RISEep[Rseg]))
                prnt(msg6)
                tccdata += "\n" + msg6
                tex += fill_RISE_above_horizon(obj, Rseg)

            Rseg += 1
            msg6 = "----------------------------------------\n"
        # ----------------------------------------- end of 'while'

        if msg6 != '':
            prnt(msg6[:-1])    # '\n' counts as one character

# ........... final list of segments processed ...........

        if nn > 0:
            rise_seg_done.sort()
            set_seg_done.sort()
            msgR = "   rise_seg_done {}".format(rise_seg_done)
            msg  = msgR + " "*(40-len(msgR)) + " set_seg_done {}".format(set_seg_done)
            prnt(msg)


# .....................................................................
# ..............  add   T E X T  /  A N N O T A T I O N  ..............
# ..............        "above horizon with sun"         ..............
# .....................................................................

    if idx_preMP_max is not None:
        # xy0 = [idx_preMP_max/10*sf, (hr_preMP)*sf]      # print near hr_preMP
        # tex += printlabelXY("above horizon with sun", xy0, ang_preMP, 'gray', False)
        tex += AHwS2(idx_preMP_max, hr_preMP, ang_preMP)

    if idx_postMP_max is not None:
        # xy0 = [idx_postMP_max/10*sf, (hr_postMP)*sf]    # print near hr_postMP
        # tex += printlabelXY("above horizon with sun", xy0, ang_postMP, 'gray', False)
        tex += AHwS2(idx_postMP_max, hr_postMP, ang_postMP)

# .....................................................................
# ..............  add   T E X T  /  A N N O T A T I O N  ..............
# ..............          "© 2026 Andrew Bauer"          ..............
# .....................................................................

    txt = ''
    tex0 = ""
    sliceBW = False             # no slanting line that slices Copyright text into black & white
    slice_00h_to_00h = False    # no 00h to 00h curve that slices Copyright text horizontally
    slice_horizontally = False  # no curve that slices Copyright text horizontally
    upwards = False             # direction of slanting slice curve to determine black & white portions

    tryslice = True
# ....... check if the last DBH zone overlaps the Copytight text (Mercury 2023 65°N to 70°N)
    if dbh != []:
        lastdbhzone_fr = dbh[dbhoffset[-1]]
        lastdbhzone_to = dbh[-1]
        # if the last dbh zone overlaps the Copyright text, print it all white
        overlap = range(max(lastdbhzone_fr,daystoprocess-62),min(lastdbhzone_to,daystoprocess-1))
        if len(overlap) > 0: tryslice = False
        # if the last dbh zone starts after the Copyright text, print it all white (Venus 2023 72°N)
        if lastdbhzone_fr >= 360: tryslice = False

# ....... decide if black & white text slicing is required based on a SET segment .........
    if tryslice:
        for set_seg, idx in enumerate(set_offset):
            
            slice_00h_to_00h = False    # no 00h to 00h curve that slices Copyright text horizontally
            if set_ep[set_seg] == ('00h', '00h'): slice_00h_to_00h = True
            xS,yS = getXY(objset_XY_txt[set_seg][0])        # start of SET
            xSe,ySe = getXY(objset_XY_txt[set_seg][-1])     # end of SET
            lnth = xSe - xS
            if yS > 6.0 and ySe > 6.0: continue             # ignore any SET higher than 06h (Venus 2024 58.0S) 

            if daystoprocess-62 <= xSe <= daystoprocess-1:    # SET ends btwn Nov1 and Jan1?
                # don't start tracing SET before Nov 1 ....
                k0 = max(xS,daystoprocess-62) - xS      # k0 = seg offset to min(Nov1 OR seg_start)
                                                        # k0 = 0 if xS >= daystoprocess-62
                k1 = max(xS,daystoprocess-32) - xS      # k1 = seg offset to min(Dec1 OR seg_start)
                k1 = min(k1, lnth-1)                    # keep k1 within the segment length

                if xS <= daystoprocess-62:      # if seg_start <= Nov1
                    #print(set_seg,k0,k1)
                    xSn,ySn = getXY(objset_XY_txt[set_seg][k0])      # SET on Nov1
                    xSd,ySd = getXY(objset_XY_txt[set_seg][k1])      # SET on Dec1 or xSe if earlier
                    #print("    ySn = {:.3f} ySe = {:.3f}".format(ySn,ySe))
                    # compare y on Nov1 with y at end of SET ... does it overlap 0.1 to 0.8 (text height range)?
                    overlap = foverlap(min(ySn,ySe), max(ySn,ySe), 0.1, 0.8)
                    if overlap > 0:     # it overlaps ... slanting upwards or downwards?
                        upwards = True if ySe > ySn else False
                    elif ySd > 0.8:     # if not a 00h-to-00h SET
                        continue        # skip this SET segment
                elif not slice_00h_to_00h:      # if seg_start > Nov1
                    # compare y on SET start with y at SET end ... does it overlap 0.1 to 0.8 (text height range)?
                    overlap = foverlap(min(yS,ySe), max(yS,ySe), 0.1, 0.8)
                    if overlap > 0:     # it overlaps ... slanting upwards or downwards?
                        upwards = True if ySe > yS else False
                    else: continue      # skip this SET segment (Mars 2050 64-69°N)

                sliceBW = True      # print text using black & white
                i = j = 0           # end of segment   (0 <= j < lnth)
                lnth = len(objset_XY_txt[set_seg])
                # check if SET curve begins and ends on 00h
                if slice_00h_to_00h:
                    while i < lnth - k0:        # scan backwards
                        j = i                   # quit loop with 'j' valid  (Venus 2048 58°S)
                        xS,yS = getXY(objset_XY_txt[set_seg][-j-1])
                        #print("    xS {}, yS = {:.3f}".format(DOY(xS),yS))
                        i += 1

                    # define the slice curve (start-to-end)
                    s6 = r"""%s""" %plotset_XY_txt[set_seg][-j-1]
                    tex0 += s6[:s6.index(', ')] + ", 0.000) "   # first coordinate with 0.000 as y
                    for i in range(j,-1,-1):
                        tex0 += r"""%s""" %plotset_XY_txt[set_seg][-i-1]
                    s7 = r"""%s""" %plotset_XY_txt[set_seg][-1]
                    tex0 += s7[:s7.index(', ')] + ", 0.000) "   # last coordinate with 0.000 as y
                else:
                    while i < lnth - k0:        # scan backwards
                        j = i                   # quit loop with 'j' valid
                        xS,yS = getXY(objset_XY_txt[set_seg][-j-1])
                        if not upwards and yS > 0.9: break      # exclude values above 0.9h
                        i += 1

                    #print("    xS {}, yS = {:.3f}, xSe {}, ySe = {:.3f}".format(DOY(xS),yS,DOY(xSe),ySe))
                    # is this a horizontal slice from Nov1 to EoY?
                    if xSe == daystoprocess-1 and j == 61:
                        # slice horizontally if both ends are between 00h and 0.9h
                        slice_horizontally = True   # LOWER portion black; UPPER portion white

                    # define the slice curve (start-to-end)
                    s6 = r"""%s""" %plotset_XY_txt[set_seg][-j-1]
                    Yfirst = 0.1*sf if upwards else 0.8*sf      # begin with 0.1h or 0.8h as y
                    if (upwards and yS > 0.1) or (not upwards and yS < 0.8):
                        tex0 += s6[:s6.index(', ')] + ", {:.3f}) ".format(Yfirst)
                    for i in range(j,-1,-1):
                        s6 = r"""%s""" %plotset_XY_txt[set_seg][-i-1]
                        tex0 += s6
                    Ylast = 0.8*sf if upwards else 0.1*sf      # terminate with 0.8h or 0.1h as y
                    if (upwards and ySe < 0.8) or (not upwards and ySe > 0.1):
                        tex0 += s6[:s6.index(', ')] + ", {:.3f}) ".format(Ylast)
                txt = 'SET'
                c1 = 'black'; c2 = 'white'             # LEFT portion black; RIGHT portion white
                # if NOT slice_horizontally and upwards: LEFT portion white; RIGHT portion black
                break

# ....... decide if black & white text slicing is required based on a RISE segment .........
    if tryslice and txt == '':
        for rise_seg, idx in enumerate(rise_offset):

            slice_00h_to_00h = False    # no 00h to 00h curve that slices Copyright text horizontally
            if rise_ep[rise_seg] == ('00h', '00h'): slice_00h_to_00h = True
            xR,yR = getXY(objrise_XY_txt[rise_seg][0])      # start of RISE
            xRe,yRe = getXY(objrise_XY_txt[rise_seg][-1])   # end of RISE
            lnth = xRe - xR
            if yR > 6.0 and yRe > 6.0: continue             # ignore any RISE higher than 06h

            if daystoprocess-62 <= xRe <= daystoprocess-1:  # RISE ends btwn Nov1 and Jan1?
                # don't start tracing RISE before Nov 1 ....
                k0 = max(xR,daystoprocess-62) - xR      # k0 = seg offset to min(Nov1 OR seg_start)
                                                        # k0 = 0 if xR >= daystoprocess-62
                k1 = max(xR,daystoprocess-32) - xR      # k1 = seg offset to min(Dec1 OR seg_start)
                k1 = min(k1, lnth-1)                    # keep k1 within the segment length

                if xR <= daystoprocess-62:      # if seg_start <= Nov1
                    xRn,yRn = getXY(objrise_XY_txt[rise_seg][k0])    # RISE on Nov1
                    xRd,yRd = getXY(objrise_XY_txt[rise_seg][k1])    # RISE on Dec1 or xRe if earlier
                    #print("    yRn = {:.3f} yRe = {:.3f}".format(yRn,yRe))
                    # compare y on Nov1 with y at end of RISE ... does it overlap 0.1 to 0.8 (text height range)?
                    overlap = foverlap(min(yRn,yRe), max(yRn,yRe), 0.1, 0.8)
                    if overlap > 0:     # it overlaps ... slanting upwards or downwards?
                        upwards = True if yRe > yRn else False
                    elif yRd > 0.8:     # if not a 00h-to-00h RISE 
                        continue        # skip this RISE segment
                elif not slice_00h_to_00h:      # if seg_start > Nov1
                    # compare y on RISE start with y at RISE end ... does it overlap 0.1 to 0.8 (text height range)?
                    overlap = foverlap(min(yR,yRe), max(yR,yRe), 0.1, 0.8)
                    if overlap > 0:     # it overlaps ... slanting upwards or downwards?
                        upwards = True if yRe > yR else False
                    else: continue      # skip this RISE segment

                sliceBW = True      # print text using black & white
                i = j = 0           # end of segment   (0 <= j < lnth)
                lnth = len(objrise_XY_txt[rise_seg])
                # check if RISE curve begins and ends on 00h
                if slice_00h_to_00h:
                    while i < lnth - k0:        # scan backwards
                        j = i                   # quit loop with 'j' valid
                        xR,yR = getXY(objrise_XY_txt[rise_seg][-j-1])
                        #print("    xR {}, yR = {:.3f}".format(DOY(xR),yR))
                        i += 1

                    # define the slice curve (start-to-end)
                    s6 = r"""%s""" %plotrise_XY_txt[rise_seg][-j-1]
                    tex0 += s6[:s6.index(', ')] + ", 0.000) "   # first coordinate with 0.000 as y
                    for i in range(j,-1,-1):
                        tex0 += r"""%s""" %plotrise_XY_txt[rise_seg][-i-1]
                    s7 = r"""%s""" %objrise_XY_txt[rise_seg][-1]
                    tex0 += s7[:s7.index(', ')] + ", 0.000) "   # last coordinate with 0.000 as y
                else:
                    while i < lnth - k0:        # scan backwards
                        j = i                   # quit loop with 'j' valid
                        xR,yR = getXY(objrise_XY_txt[rise_seg][-j-1])
                        if not upwards and yR > 0.9: break      # exclude values above 0.9
                        i += 1

                    #print("    xR {}, yR = {:.3f}, xRe {}, yRe = {:.3f}".format(DOY(xR),yR,DOY(xRe),yRe))
                    # is this a horizontal slice from Nov1 to EoY?
                    if xRe == daystoprocess-1 and j == 61:
                        # slice horizontally if both ends are between 00h and 0.9h
                        slice_horizontally = True   # LOWER portion white; UPPER portion black

                    # define the slice curve (start-to-end)
                    s6 = r"""%s""" %plotrise_XY_txt[rise_seg][-j-1]
                    Yfirst = 0.1*sf if upwards else 0.8*sf      # begin with 0.1h or 0.8h as y
                    if (upwards and yR > 0.1) or (not upwards and yR < 0.8):
                        tex0 += s6[:s6.index(', ')] + ", {:.3f}) ".format(Yfirst)
                    for i in range(j,-1,-1):
                        s6 = r"""%s""" %plotrise_XY_txt[rise_seg][-i-1]
                        tex0 += s6
                    Ylast = 0.8*sf if upwards else 0.1*sf      # terminate with 0.8h or 0.1h as y
                    if (upwards and yRe < 0.8) or (not upwards and yRe > 0.1):
                        tex0 += s6[:s6.index(', ')] + ", {:.3f}) ".format(Ylast)
                txt = 'RISE'
                c1 = 'white'; c2 = 'black'             # LEFT portion white; RIGHT portion black
                # if NOT slice_horizontally and upwards: LEFT portion black; RIGHT portion white
                break

    # if slice_00h_to_00h: print("    slice UPPER/LOWER 00h to 00h with {} curve".format(txt))
    # elif slice_horizontally: print("    slice UPPER/LOWER horizontally with {} curve".format(txt))
    # elif sliceBW:
        # txt0 = 'upwards' if upwards else 'downwards'
        # print("    slice LEFT/RIGHT with {} slanting {} curve".format(txt0,txt))


# ........... print the copyright text ...........
    #print("    sliceBW", sliceBW)
    if not sliceBW:
        # print Copyright black OR white
        c1 = 'white'
        if isEoY:
            c1 = 'black'        # usual case
            # check for a short SET just above the right lower corner (Mars 2050 64 to 72°N)
            if len(set_days) > 0:       # if a SET exists...
                if (set_ep[-1] == ('00h', 'EoY') or set_ep[-1] == ('EoY', 'EoY')) \
                and set_days[-1] <= 6:
                    xS,yS = getXY(objset_XY_txt[set_seg][0])        # start of SET
                    xSe,ySe = getXY(objset_XY_txt[set_seg][-1])     # end of SET
                    if ySe < 0.25: c1 = 'white'
                
        tex += r"""
\node[font=\{}, color={}, anchor=east] at ({:.3f},{:.3f}) {{\textcopyright\enspace 2026 Andrew Bauer}};""".format(navstar_fs, c1, (xmax-0.53)*sf, 0.37*sf)


    else:       # elif sliceBW:
        # slice text into BLACK and WHITE portions (either LEFT/RIGHT or UPPER/LOWER)

        if slice_horizontally:
# .......... slice text into LOWER and UPPER portions horizontally ..........

            # LOWER portion of text (within 00h to curve) is bounded by 0.1h on the LEFT side,
            #       to RISE/SET curve start-end, to 0.1h on the RIGHT side
            x0 = daystoprocess-62
            tex += r"""
\begin{{scope}}
  \clip ({:.3f}, {:.3f}) -- plot[smooth,tension=0.5] coordinates{{
""".format(x0/10*sf, 0.1*sf)
            tex += tex0 + r""" }} -- ({:.3f}, {:.3f}) -- cycle;
  \node[font=\{}, color={}, anchor=east] at ({:.3f},{:.3f}) {{\textcopyright\enspace 2026 Andrew Bauer}};
\end{{scope}}""".format((xmax-0.1)*sf, 0.1*sf, navstar_fs, c1, (xmax-0.53)*sf, 0.37*sf)

            # UPPER portion of text (within 01h to curve) is bounded by 0.8h on the LEFT side,
            #       to RISE/SET curve start-end, to 0.8h on the RIGHT side
            tex += r"""
\begin{{scope}}
  \clip ({:.3f}, {:.3f}) -- plot[smooth,tension=0.5] coordinates{{
""".format(x0/10*sf, 0.8*sf)
            tex += tex0 + r""" }} -- ({:.3f}, {:.3f}) -- cycle;
  \node[font=\{}, color={}, anchor=east] at ({:.3f},{:.3f}) {{\textcopyright\enspace 2026 Andrew Bauer}};
\end{{scope}}""".format((xmax-0.1)*sf, 0.8*sf, navstar_fs, c2, (xmax-0.53)*sf, 0.37*sf)


        elif slice_00h_to_00h:
# .......... slice text into LOWER and UPPER portions along 00h ..........

            # LOWER portion of text (within 00h to curve) is bounded only by the RISE/SET curve start-end,
            #       i.e. the RISE/SET curve MUST begin and end near 00h
            # RISE/SET curve begins and ends on 00h (Venus 2024 60°S, Mars 2028 62°N)
            tex += r"""
\begin{scope}
  \clip plot[smooth,tension=0.5] coordinates{
"""

            tex += tex0 + r""" }} -- cycle;
  \node[font=\{}, color={}, anchor=east] at ({:.3f},{:.3f}) {{\textcopyright\enspace 2026 Andrew Bauer}};
\end{{scope}}""".format(navstar_fs, c1, (xmax-0.53)*sf, 0.37*sf)

            # UPPER portion of text (bounded by 0.1h to 0.8h on the RIGHT, to 0.8h to 0.1h on the LEFT, and the RISE/SET curve start-end)
            x0 = min(xS, daystoprocess-62)
            tex += r"""
\begin{{scope}}
  \clip ({:.3f}, {:.3f}) -- ({:.3f}, {:.3f}) -- ({:.3f}, {:.3f}) -- ({:.3f}, {:.3f})""".format(
(xmax-0.1)*sf, 0.1*sf,
(xmax-0.1)*sf, 0.8*sf,
x0/10*sf, 0.8*sf,
x0/10*sf, 0.1*sf)

            tex += r""" -- plot[smooth,tension=0.5] coordinates{
"""

            tex += tex0 + r""" }} -- cycle;
  \node[font=\{}, color={}, anchor=east] at ({:.3f},{:.3f}) {{\textcopyright\enspace 2026 Andrew Bauer}};
\end{{scope}}""".format(navstar_fs, c2, (xmax-0.53)*sf, 0.37*sf)


        elif upwards:
# .......... UPWARD slanting "line" slices text into LEFT and RIGHT portions ..........

            # LEFT portion of text (bounded by RISE/SET curve 0.1h-start-end-0.8h; 0.8h, 0.1h LEFT)
            tex += r"""
\begin{scope}
  \clip plot[smooth,tension=0.5] coordinates{
"""
            tex += tex0 + r""" }}  -- ({:.3f}, {:.3f}) -- ({:.3f}, {:.3f}) -- cycle;""".format(
(xmax-5.9)*sf, 0.8*sf,
(xmax-5.9)*sf, 0.1*sf)

            tex += r"""
  \node[font=\{}, color={}, anchor=east] at ({:.3f},{:.3f}) {{\textcopyright\enspace 2026 Andrew Bauer}};
\end{{scope}}""".format(navstar_fs, c2, (xmax-0.53)*sf, 0.37*sf)

            # RIGHT portion of text (bounded by RISE/SET curve 0.1h-start-end-0.8h; 0.8h, 0.1h RIGHT)
            tex += r"""
\begin{scope}
  \clip plot[smooth,tension=0.5] coordinates{
"""
            tex += tex0 + r""" }}  -- ({:.3f}, {:.3f}) -- ({:.3f}, {:.3f}) -- cycle;""".format(
(xmax-0.5)*sf, 0.8*sf,
(xmax-0.5)*sf, 0.1*sf)

            tex += r"""
  \node[font=\{}, color={}, anchor=east] at ({:.3f},{:.3f}) {{\textcopyright\enspace 2026 Andrew Bauer}};
\end{{scope}}""".format(navstar_fs, c1, (xmax-0.53)*sf, 0.37*sf)

        else:
# .......... DOWNWARD slanting "line" slices text into LEFT and RIGHT portions ..........

            # LEFT portion of text (bounded by 0.1h, 0.8h LEFT; RISE/SET curve 0.8h-start-end-0.1h)
            tex += r"""
\begin{{scope}}
  \clip ({:.3f}, {:.3f}) -- ({:.3f}, {:.3f})""".format(
(xmax-5.9)*sf, 0.1*sf,
(xmax-5.9)*sf, 0.8*sf)

            tex += r""" -- plot[smooth,tension=0.5] coordinates{
"""
            tex += tex0 + r""" }} -- ({:.3f}, {:.3f}) -- cycle;
  \node[font=\{}, color={}, anchor=east] at ({:.3f},{:.3f}) {{\textcopyright\enspace 2026 Andrew Bauer}};
\end{{scope}}""".format((xmax-0.5)*sf, 0.1*sf, navstar_fs, c1, (xmax-0.53)*sf, 0.37*sf)


            # RIGHT portion of text (bounded by 0.1h, 0.8h RIGHT; RISE/SET curve 0.8h-start-end-0.1h)
            tex += r"""
\begin{{scope}}
  \clip ({:.3f}, {:.3f}) -- ({:.3f}, {:.3f})""".format(
(xmax-0.5)*sf, 0.1*sf,
(xmax-0.5)*sf, 0.8*sf)

            tex += r""" -- plot[smooth,tension=0.5] coordinates{
"""

            tex += tex0 + r""" }} -- cycle;
  \node[font=\{}, color={}, anchor=east] at ({:.3f},{:.3f}) {{\textcopyright\enspace 2026 Andrew Bauer}};
\end{{scope}}""".format(navstar_fs, c2, (xmax-0.53)*sf, 0.37*sf)


# -------------- print & prepare code coverage to write to file ---------------

    # s = list(set(code_cov))
    # if not None in s: s.sort()    # sort s in-place
    # print("'trace' code coverage: {}".format(s))
    # tccdata += "\n{}\n".format(s)

    # s = list(set(AM_cov))
    # if not None in s: s.sort()    # sort s in-place
    # print("   'AM' coverage going forwards:  {}".format(s))
    # tccdata += "AM: {}\n".format(s)

    # s = list(set(PM_cov))
    # if not None in s: s.sort()    # sort s in-place
    # print("   'PM' coverage going backwards: {}".format(s))
    # tccdata += "PM: {}\n".format(s)

# -------------- draw solitary RISE/SET events as a simple red/blue cross --------------

    for seg in solitary_RISE_seg:
        xR, yR = getXY(objrise_XY_txt[seg][0])
        tex += solitary_event(xR, yR, True)

    for seg in solitary_SET_seg:
        xS, yS = getXY(objset_XY_txt[seg][0])
        tex += solitary_event(xS, yS, False)

# -------------- draw planet rise/set times -------------

    tex += r"""
%%
%% plot ------ %s rise times at %s°%s per day ------""" % (objs,lat,lns)
    for index, item in enumerate(objrise_XY_txt):
        if len(objrise_XY_txt[index]) > 1:
            tex += r"""
 \draw[thin,color=black] plot[smooth,tension=0.5] coordinates{
"""
            for i in range(len(objrise_XY_txt[index])):
                tex += r"""%s """ %plotrise_XY_txt[index][i]
                if (i+1) % 5 == 0: tex += "\n"
            tex += r"""};"""


    tex += r"""
%%
%% plot ------ %s set times at %s°%s per day ------""" % (objs,lat,lns)
    for index, item in enumerate(objset_XY_txt):
        if len(objset_XY_txt[index]) > 1:
            tex += r"""
 \draw[thin,color=black] plot[smooth,tension=0.5] coordinates{
"""
            for i in range(len(objset_XY_txt[index])):
                tex += r"""%s """ %plotset_XY_txt[index][i]
                if (i+1) % 5 == 0: tex += "\n"
            tex += r"""};"""

    tex += r"""
%%
%% plot ------ civil dawn at %s°%s per day ------""" %(lat,lns)

    idx = 0
    seg_active = False

    while idx < daystoprocess:
        if civil_AM_txt[idx] is not None:
            if not seg_active:     # begin of DAWN segment
                ndx = idx
                tex += r"""
 \draw[thin,color=DarkRed] plot[smooth,tension=0.5] coordinates{
"""
            tex += r"""%s """ %civil_AM_txt[idx]
            if (idx+1-ndx) % 5 == 0: tex += "\n"
            seg_active = True
        else:
            if seg_active:
                tex += r"""};"""
                seg_active = False
        idx += 1

    if seg_active:
        tex += r"""};"""


    tex += r"""
%%
%% plot ------ civil dusk at %s°%s per day ------""" %(lat,lns)

    idx = 0
    seg_active = False

    while idx < daystoprocess:
        if civil_PM_txt[idx] is not None:
            if not seg_active:     # begin of DUSK segment
                ndx = idx
                tex += r"""
 \draw[thin,color=MediumBlue] plot[smooth,tension=0.5] coordinates{
"""
            tex += r"""%s """ %civil_PM_txt[idx]
            if (idx+1-ndx) % 5 == 0: tex += "\n"
            seg_active = True
        else:
            if seg_active:
                tex += r"""};"""
                seg_active = False
        idx += 1

    if seg_active:
        tex += r"""};"""


# .....................................................................
# ..............  add   T E X T  /  A N N O T A T I O N  ..............
# ..........  "C I V I L   D U S K" / "C I V I L   D A W N"  ..........
# .....................................................................

    sbh = 6     # Sun Below Horizon (degrees)
    # !!! DO NOT put text in curly braces - it prints as if it was a single character !!!
    # txt = r"D U S K~~~at latitude %s{°}%s~~~(Sun %d{°} below horizon)" %(lat,lns,sbh)   # original

    # WORKAROUND for "! Dimension too large." crash during PDF creation... (2020 62.0°N)
    txt = r"D U S K~~~at latitude %s{\textdegree}%s~~~(Sun %d{\textdegree} below horizon)" %(lat,lns,sbh)
    # SOLUTION for "! Dimension too large." crash is to use:
    #     \usetikzlibrary{decorations.text,fpu}
    #     \path [/pgf/fpu/install only=veclen,decorate, etc.

    if segs_DUSK == 1:

        tex += r"""
%% decorate PM dusk with text aligned left
\path [/pgf/fpu/install only=veclen,decorate,decoration={text along path,raise=-2.4ex,text align={left indent=%1.2fcm},text={|\PMstyle|%s}}]
plot[smooth,tension=0.5] coordinates{
""" % (1.6*sf, txt)

        n = 0
        l = len(civil_PM_txt); lend = int(l/2)
        for idx in range(0,lend):               # we only need the left half
            if idx % 7 == 0 or idx == lend-1:   # about 75 coordinates is the limit in MiKTeX
                tex += r"""%s """ %civil_PM_txt[idx]
                if (n+1) % 5 == 0: tex += "\n"
                n += 1
        tex += r"""};"""

        tex += r"""
%% decorate PM dusk with text aligned right
\path [/pgf/fpu/install only=veclen,decorate,decoration={text along path,raise=-2.4ex,text align={right, right indent=%1.2fcm},text={|\PMstyle|%s}}]
plot[smooth,tension=0.5] coordinates{
""" % (1.6*sf, txt)

        n = 0
        l = len(civil_PM_txt)
        for idx in range(int(l/2),l):           # we only need the right half
            if idx % 7 == 0 or idx == l-1:      # about 75 coordinates is the limit in MiKTeX
                tex += r"""%s """ %civil_PM_txt[idx]
                if (n+1) % 5 == 0: tex += "\n"
                n += 1
        tex += r"""};"""

    if segs_DUSK == 3:
        # OLD Note: "! Dimension too large." for Saturn 2004 66°N using "align={left indent=%1.3fcm}"
        tex += r"""
%% decorate PM dusk with text aligned left
\path [/pgf/fpu/install only=veclen,decorate,decoration={text along path,raise=-2.4ex,text align={left indent=%1.2fcm},text={|\PMstyle|%s}}]
plot[smooth,tension=0.5] coordinates{
""" % (1.6*sf, txt)

        n = 0
        idx = 0
        l = seglen_DUSK[0]
        while idx < l:
            if idx % 5 == 0 or idx == l-1:  # about 75 coordinates is the limit in MiKTeX
                tex += r"""%s """ %civil_PM_txt[idx]
                if (n+1) % 5 == 0: tex += "\n"
                n += 1
            idx += 1
        tex += r"""};"""

        tex += r"""
%% decorate PM dusk with text aligned right
\path [/pgf/fpu/install only=veclen,decorate,decoration={text along path,raise=-2.4ex,text align={right, right indent=%1.2fcm},text={|\PMstyle|%s}}]
plot[smooth,tension=0.5] coordinates{
""" % (1.6*sf, txt)

        n = 0
        idx = seglen_DUSK[0] - seglen_DUSK[1]
        l = idx + seglen_DUSK[2]
        while idx < l:
            if idx % 5 == 0 or idx == l-1:  # about 75 coordinates is the limit in MiKTeX
                tex += r"""%s """ %civil_PM_txt[idx]
                if (n+1) % 5 == 0: tex += "\n"
                n += 1
            idx += 1
        tex += r"""};"""

# .....     .....     .....     .....     .....     .....     .....     .....     .....

    # !!! DO NOT put text in curly braces - it prints as if it was a single character !!!
    # txt = r"D A W N~~~at latitude %s{°}%s~~~(Sun %d{°} below horizon)" %(lat,lns,sbh)   # original

    # WORKAROUND for "! Dimension too large." crash during PDF creation... (2020 62.0°N)
    txt = r"D A W N~~~at latitude %s{\textdegree}%s~~~(Sun %d{\textdegree} below horizon)" %(lat,lns,sbh)
    # SOLUTION for "! Dimension too large." crash is to use:
    #     \usetikzlibrary{decorations.text,fpu}
    #     \path [/pgf/fpu/install only=veclen,decorate, etc.

    if segs_DAWN == 1:

        tex += r"""
%% decorate AM dawn with text aligned left
\path [/pgf/fpu/install only=veclen,decorate,decoration={text along path,raise=0.75ex,text align={left indent=%1.2fcm},text={|\AMstyle|%s}}]
plot[smooth,tension=0.5] coordinates{
""" % (1.6*sf, txt)

        n = 0
        l = len(civil_AM_txt); lend = int(l/2)
        for idx in range(0,lend):               # we only need the left half
            if idx % 7 == 0 or idx == lend-1:   # about 75 coordinates is the limit in MiKTeX
                tex += r"""%s """ %civil_AM_txt[idx]
                if (n+1) % 5 == 0: tex += "\n"
                n += 1
                #if idx > l/2: break             # we only need the left half
        tex += r"""};"""

        tex += r"""
%% decorate AM dawn with text aligned right
\path [/pgf/fpu/install only=veclen,decorate,decoration={text along path,raise=0.75ex,text align={right, right indent=%1.2fcm},text={|\AMstyle|%s}}]
plot[smooth,tension=0.5] coordinates{
""" % (1.6*sf, txt)

        n = 0
        l = len(civil_AM_txt)
        for idx in range(int(l/2),l):           # we only need the right half
            if idx % 7 == 0 or idx == l-1:      # about 75 coordinates is the limit in MiKTeX
                tex += r"""%s """ %civil_AM_txt[idx]
                if (n+1) % 5 == 0: tex += "\n"
                n += 1
        tex += r"""};"""

    if segs_DAWN == 3:
        tex += r"""
%% decorate AM dawn with text aligned left
\path [/pgf/fpu/install only=veclen,decorate,decoration={text along path,raise=0.75ex,text align={left indent=%1.2fcm},text={|\AMstyle|%s}}]
plot[smooth,tension=0.5] coordinates{
""" % (1.6*sf, txt)

        n = 0
        idx = 0
        l = seglen_DAWN[0]
        while idx < l:
            if idx % 5 == 0 or idx == l-1:  # about 75 coordinates is the limit in MiKTeX
                tex += r"""%s """ %civil_AM_txt[idx]
                if (n+1) % 5 == 0: tex += "\n"
                n += 1
            idx += 1
        tex += r"""};"""

        tex += r"""
%% decorate AM dawn with text aligned right
\path [/pgf/fpu/install only=veclen,decorate,decoration={text along path,raise=0.75ex,text align={right, right indent=%1.2fcm},text={|\AMstyle|%s}}]
plot[smooth,tension=0.5] coordinates{
""" % (1.6*sf, txt)

        idx = seglen_DAWN[0] - seglen_DAWN[1]
        n = 0
        l = idx + seglen_DAWN[2]
        while idx < l:
            if idx % 5 == 0 or idx == l-1:  # about 75 coordinates is the limit in MiKTeX
                tex += r"""%s """ %civil_AM_txt[idx]
                if (n+1) % 5 == 0: tex += "\n"
                n += 1
            idx += 1
        tex += r"""};"""

# -------------- draw planet upper Meridian Passage --------------

    # plot Meridian Passage of planet
    tex += tex999

# .....................................................................
# ..............  add   T E X T  /  A N N O T A T I O N  ..............
# ................  "<planet name>, Meridian Passage"  ................
# .....................................................................

    # 'hdiags' is the offset the sun/planet name label is to be raised or
    # lowered (perpendicular to the direction of the text itself) in order
    # to be above or below the path drawn.
    # The units are '6 minutes' (1/10 hour) when measured along the vertical axis.
    hdiags = [0.95*3, 1.4*3, 1.3*3, 1.1*3, 1.2*3, 1.2*3, 1.2*3, 1.2*3]
    # note: multiply by 3 because the fundamental units in Planet Declination Paths is
    # '10 degrees / 30 days' whereas here it is '1 hour / 10 days' (factor 3 smaller).
    hdiag = hdiags[obj]     # height (in 1/10 hour) perpendiculat to label text

    if idx_preMP_max is not None and idx_postMP_max is not None:
        # mid-X-position between 'not visible' texts...
        idx = int((idx_preMP_max + idx_postMP_max) / 2)
        mpas = meridian_pass[idx]
        dawn = f_AM(civilY_AM[idx])
        dusk = f_PM(civilY_PM[idx])
        # ... unless they're in different gold bands
        if len(mp_btwn_dawn_dusk) == 1 and len(mp_offset) == 1:
            if dawn < mpas < dusk:
                tn = 1 + ((obj-1)*3)
                ab = 0      # print above
                # txt_size = (txt_width[tn], txt_height[tn], txt_depth[tn])
                # xy, rxy, idx_min, idx_max, dec_min, dec_max, txtXY, ang = label_rectangle(meridian_pass, idx, txt_size, hdiag*vab[ab])
                txtXY, ang = text_position(meridian_pass, idx, hdiag*vab[ab])
                tex += printlabelXY(txt_text[tn], txtXY, ang, 'gray', False)

                tn = 0
                ab = 1      # print below
                # txt_size = (txt_width[tn], txt_height[tn], txt_depth[tn])
                # xy, rxy, idx_min, idx_max, dec_min, dec_max, txtXY, ang = label_rectangle(meridian_pass, idx, txt_size, hdiag*vab[ab])
                txtXY, ang = text_position(meridian_pass, idx, hdiag*vab[ab])
                tex += printlabelXY(txt_text[tn], txtXY, ang, 'gray', False)
        else:
            # print in mid-X-position of "MerPass between Civil Dawn and Dusk"
            for idx_fr, idx_to in mp_btwn_dawn_dusk:
                if idx_to - idx_fr > 44:
                    idx = int((idx_fr + idx_to) / 2)
                    tn = 1 + ((obj-1)*3)
                    ab = 0      # print above
                    txtXY, ang = text_position(meridian_pass, idx, hdiag*vab[ab])
                    tex += printlabelXY(txt_text[tn], txtXY, ang, 'gray', False)
                    tn = 0
                    ab = 1      # print below
                    txtXY, ang = text_position(meridian_pass, idx, hdiag*vab[ab])
                    tex += printlabelXY(txt_text[tn], txtXY, ang, 'gray', False)


# --------------------------------------------------------------
# re-draw plot borders as shading areas often removes it

# re-draw plot vertical border lines
    tex += r"""
% re-draw chart border lines..."""

    if config.orthogonal:
        tex += r"""
  \draw[ultra thin] ({:.3f},{:.3f}) -- ({:.3f},{:.3f});""".format(
0.0,0.0,0.0,ymax*sf)
        tex += r"""
  \draw[ultra thin] ({:.3f},{:.3f}) -- ({:.3f},{:.3f});""".format(
xmax*sf,0.0,xmax*sf,ymax*sf)

    else:
        # left slanting chart border
        tex += r"""
\draw[ultra thin] ({:.3f},{:.3f}) -- ({:.3f},{:.3f});""".format(
0.0,0.0,1/10*sf,ymax*sf)
        # right slanting chart border
        tex += r"""
\draw[ultra thin] ({:.3f},{:.3f}) -- ({:.3f},{:.3f});""".format(
(xmax-1/10)*sf,0.0,xmax*sf,ymax*sf)


# re-draw plot horizontal border lines
    tex += r"""
  \draw[ultra thin] ({:.3f},{:.3f}) -- ({:.3f},{:.3f});""".format(
0.0,0.0,xmax*sf,0.0)
    tex += r"""
  \draw[ultra thin] ({:.3f},{:.3f}) -- ({:.3f},{:.3f});""".format(
0.0,ymax*sf,xmax*sf,ymax*sf)

    return tex

# --------------------------------------------------
# --------------  REQUIRED  FUNCTIONS --------------
# --------------------------------------------------

#   fillpath element codes:
#   r    = RISE segment  <seg #>:<day offset>
#   r    = RISE segment  <seg #>:<day offset from>-<to>
#   s    = SET  segment  <seg #>:<day offset>
#   s    = SET  segment  <seg #>:<day offset from>-<to>
#   dawn = DAWN path     :<day offset>
#   dawn = DAWN path     :<day offset from>-<to>
#   dusk = DUSK path     :<day offset>
#   dusk = DUSK path     :<day offset from>-<to>
#   T    = TOP     to upper chart border :<at day offset>
#   B    = BOTTOM  to lower chart border :<at day offset>

def fillpath(path, colour, opacity, textpath=['']):
    tex = ''
    if path == '': return tex
    path_elements = path.split(',')
    trace00 = False; trace24 = False
    begin = True        # begin a segment of coordinates (False = 'continue')

    tex += r"""
%"""
    for txt in textpath:
        tex += r"""
% {}""".format(txt)

    tex += r"""
%
\fill[color={},opacity={}]""".format(colour,opacity)
    for p in path_elements:
        #print("PATH ELEMENT:",p)
        if p.find(':') == 2:

        # . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
            if p[0] == 'r':
                trace00 = False; trace24 = False
                rise_seg = int(p[1])
                sss = p[3:].split('-')
                idx_fr = int(sss[0])
                idx_to = int(sss[1]) if len(sss) > 1 else None
                txt2 = "" if begin else "-- "

                if idx_to is not None:
                    tex += r"""
% trace {} RISE seg {} from {} to {}
{}plot[smooth,tension=0.5] coordinates{{
""".format(objn, rise_seg, DOY(idx_fr), DOY(idx_to), txt2)

                    step = 1 if idx_fr <= idx_to else -1     # backwards
                    ndx_fr = idx_fr - rise_offset[rise_seg]
                    ndx_to = idx_to - rise_offset[rise_seg] + step
                    i = 0
                    for n in range(ndx_fr, ndx_to, step):
                        tex += r"""%s """ %plotrise_XY_txt[rise_seg][n]
                        if (i+1) % 5 == 0: tex += "\n"
                        i += 1
                    tex += r"""}"""

                else:
                    tex += r"""
% {} RISE seg {} on {}
{}""".format(objn, rise_seg, DOY(idx_fr), txt2)
                    ndx = idx_fr - rise_offset[rise_seg]
                    tex += r"""%s """ %plotrise_XY_txt[rise_seg][ndx]

        # . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
            elif p[0] == 's':
                trace00 = False; trace24 = False
                set_seg = int(p[1])
                sss = p[3:].split('-')
                idx_fr = int(sss[0])
                idx_to = int(sss[1]) if len(sss) > 1 else None
                txt2 = "" if begin else "-- "

                if idx_to is not None:
                    tex += r"""
% trace {} SET seg {} from {} to {}
{}plot[smooth,tension=0.5] coordinates{{
""".format(objn, set_seg, DOY(idx_fr), DOY(idx_to), txt2)

                    step = 1 if idx_fr <= idx_to else -1     # backwards
                    ndx_fr = idx_fr - set_offset[set_seg]
                    ndx_to = idx_to - set_offset[set_seg] + step
                    i = 0
                    for n in range(ndx_fr, ndx_to, step):
                        tex += r"""%s """ %plotset_XY_txt[set_seg][n]
                        if (i+1) % 5 == 0: tex += "\n"
                        i += 1
                    tex += r"""}"""

                else:
                    tex += r"""
% {} SET seg {} on {}
{}""".format(objn, set_seg, DOY(idx_fr), txt2)
                    ndx = idx_fr - set_offset[set_seg]
                    tex += r"""%s """ %plotset_XY_txt[set_seg][ndx]

        # . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
        elif p.find(':') == 4:
            if p[:4] == 'dawn':
                sss = p[5:].split('-')
                idx_fr = int(sss[0])
                idx_to = int(sss[1]) if len(sss) > 1 else None
                txt2 = "" if begin else "-- "

                if idx_to is not None:
                    tex += r"""
% trace CIVIL DAWN from {} to {}
{}plot[smooth,tension=0.5] coordinates{{
""".format(DOY(idx_fr), DOY(idx_to), txt2)

                    step = 1 if idx_fr <= idx_to else -1    # backwards
                    i = 0
                    for n in range(idx_fr, idx_to+step, step):
                        tex += r"""%s """ %civil_AM_txt[n]
                        if (i+1) % 5 == 0: tex += "\n"
                        i += 1
                    tex += r"""}"""

                else:
                    tex += r"""
% {} CIVIL DAWN on {}
{}""".format(objn, DOY(idx_fr), txt2)
                    tex += r"""%s """ %civil_AM_txt[idx_fr]

        # . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
            elif p[:4] == 'dusk':
                sss = p[5:].split('-')
                idx_fr = int(sss[0])
                idx_to = int(sss[1]) if len(sss) > 1 else None
                txt2 = "" if begin else "-- "

                if idx_to is not None:
                    tex += r"""
% trace CIVIL DUSK from {} to {}
{}plot[smooth,tension=0.5] coordinates{{
""".format(DOY(idx_fr), DOY(idx_to), txt2)

                    step = 1 if idx_fr <= idx_to else -1    # backwards
                    i = 0
                    for n in range(idx_fr, idx_to+step, step):
                        tex += r"""%s """ %civil_PM_txt[n]
                        if (i+1) % 5 == 0: tex += "\n"
                        i += 1
                    tex += r"""}"""

                else:
                    tex += r"""
% {} CIVIL DUSK on {}
{}""".format(objn, DOY(idx_fr), txt2)
                    tex += r"""%s """ %civil_PM_txt[idx_fr]

        # . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
        elif p[0] == 'B':
            if not trace00:
                idx_to = int(p[1:])
                txt1 = "begin at" if begin else "move down to"
                txt2 = "" if begin else "-- "
                tex += r"""
% {} 00h on {}
{}({:.3f}, 0.000)""".format(txt1, DOY(idx_to), txt2, idx_to/10*sf)
                trace00 = True
            
            else:
                idx_to = int(p[1:])
                tex += r"""
% jump to {} along 00h
-- ({:.3f}, 0.000)""".format(DOY(idx_to), idx_to/10*sf)

        # . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
        elif p[0] == 'T':
            if not trace24:
                idx_to = int(p[1:])
                txt1 = "begin at" if begin else "move up to"
                txt2 = "" if begin else "-- "
                tex += r"""
% {} 24h on {}
{}({:.3f}, {:.3f})""".format(txt1, DOY(idx_to), txt2, (idx_to+helix)/10*sf, ymax*sf)
                trace24 = True
            
            else:
                idx_to = int(p[1:])
                tex += r"""
% jump to {} along 24h
-- ({:.3f}, {:.3f})""".format(DOY(idx_to), (idx_to+helix)/10*sf, ymax*sf)

        begin = False

    # -------------------------------- end of 'for'

    tex += r""" -- cycle;"""

    return tex

def fix0path(s):
    # filter out paths that have no "width"
    if s == '': return ''
    idxmin = idxmax = -1
    path_elements = s.split(',')
    for p in path_elements:
        n = p.find(':')
        if n > 0:
            sss = p[n+1:].split('-')
            idx_fr = int(sss[0])
            if idxmin == -1: idxmin = idxmax = idx_fr
            if idx_fr < idxmin: idxmin = idx_fr
            if idx_fr > idxmax: idxmax = idx_fr
            if len(sss) > 1:
                idx_to = int(sss[1])
                if idx_to < idxmin: idxmin = idx_to
                if idx_to > idxmax: idxmax = idx_to
        else:   # path element does not contain ':'
            idx_to = int(p[1:])
            if idxmin == -1: idxmin = idxmax = idx_to
            if idx_to < idxmin: idxmin = idx_to
            if idx_to > idxmax: idxmax = idx_to
        if idxmin != idxmax: return s
    # -------------------------------- end of 'for'
    if idxmin == idxmax: return ''
    return s

def trimpath(s):
    # check if the first and last elements are identical fixed positions
    # .... if so, remove the last element
    # note: this is a cosmetic fix, as it unnecessary that a path returns to its srarting position
    i = s.find(',')
    if i == -1: return s
    first_element = s[:i]
    # exclude a rise or set path...
    if first_element.find(':') != -1: return s
    k = s.rfind(',')
    last_element = s[k+1:]
    if first_element == last_element:
        # if first and last elements are identical, eliminate the last element
        return s[:k]
    return s

def btwn_RISE_to_SET(idx, Rseg, Sseg):
    # is DAWN between RISE (Rseg) and SET (Sseg) at date offset idx?
    # is DUSK between RISE (Rseg) and SET (Sseg) at date offset idx?

    # return DAWN(True/False) and DUSK(True/False)
    dwn = False; dsk = False

    for rng in dah_range:
        dah_fr = rng.start; dah_to = rng.stop - 1
        if dah_fr <= idx <= dah_to: return dwn, dsk

    for rng in dbh_range:
        dbh_fr = rng.start; dbh_to = rng.stop - 1
        if dbh_fr <= idx <= dbh_to: return dwn, dsk

    # if len(seglen_DAWN) == 3:
        # if seglen_DAWN[0] <= idx <= seglen_DAWN[0] - seglen_DAWN[1] - 1: dwn = False
    dawn = f_AM(civilY_AM[idx])

    # if len(seglen_DUSK) == 3:
        # if seglen_DUSK[0] <= idx <= seglen_DUSK[0] - seglen_DUSK[1] - 1: dsk = False
    dusk = f_PM(civilY_PM[idx])


    isR = rise_starts[Rseg] <= idx <= rise_ends[Rseg]
    isS =  set_starts[Sseg] <= idx <= set_ends[Sseg]
    yR, yS = get_Y(idx,Rseg,Sseg)

    if isR:
        ndx = idx - rise_starts[Rseg]
        # xR,yR = getXY(objrise_XY_txt[Rseg][ndx])
    else:
        yR = None
        if idx < rise_starts[Rseg]:
            if RISEep[Rseg][0] in ['00h']: yR = 0.0
            if RISEep[Rseg][0] in ['24h']: yR = 24.0

        else:
            if RISEep[Rseg][1] in ['00h']: yR = 0.0
            if RISEep[Rseg][1] in ['24h']: yR = 24.0

    if isS:
        ndx = idx - set_starts[Sseg]
        # xS,yS = getXY(objset_XY_txt[Sseg][ndx])   # NOT for Venus 30°N 2000 idx=185 in fill_above_horizon()
    else:
        yS = None
        if idx < set_starts[Sseg]:
            if SETep[Sseg][0] in ['00h']: yS = 0.0
            if SETep[Sseg][0] in ['24h']: yS = 24.0
        else:
            if SETep[Sseg][1] in ['00h']: yS = 0.0
            if SETep[Sseg][1] in ['24h']: yS = 24.0

    if yR is None or yS is None: return dwn, dsk

    dwn = yR < dawn < yS
    dsk = yR < dusk < yS
    return dwn, dsk

def Sline(Sfr, Sto, Stx):
    if Sfr == Sto:          # Stx = SET seg#
        path = Stx + ':' + str(Sfr) + ','
    else:
        path = Stx + ':' + str(Sfr) + '-' + str(Sto) + ','
    return path

def Rline(Rfr, Rto, Rtx):   # Rtx = RISE seg#
    if Rfr == Rto:
        path = Rtx + ':' + str(Rfr) + ','
    else:
        path = Rtx + ':' + str(Rfr) + '-' + str(Rto) + ','
    return path

def Dline(fr, to, tx):      # tx = 'dawn' or 'dusk'
    if fr == to:
        path = tx + ':' + str(fr) + ','
    else:
        path = tx + ':' + str(fr) + '-' + str(to) + ','
    return path

# .........................................................................................
# ............  fill grey SET-to-RISE bands (and handle RISE-to-SET bands)  ...............
# .........................................................................................

def fill_below_horizon(obj, set_segs, rise_segs):

    TEX = ''
    Sindex = 0; Rindex = 0

    while len(set_segs) > Sindex or len(rise_segs) > Rindex:

        seg6 = seg7 = None; Sseg = None; Stxt = 's'; Sstart = 1000; Slen = Send = None
        while len(set_segs) > Sindex:
            Sseg = set_segs[Sindex]      # first SET segment in the band
            if Sseg not in set_seg_done:
                Stxt = 's' + str(Sseg)
                Slen = set_days[Sseg]
                Sstart = set_starts[Sseg]
                Send = set_ends[Sseg]
                break
            else: Sseg = None
            Sindex += 1
        # ----------------------------------------- end of 'while'

        Rseg = None; Rtxt = 'r'; Rstart = 1000; Rlen = Rend = None
        while len(rise_segs) > Rindex:
            Rseg = rise_segs[Rindex]     # first RISE segment in the band
            if Rseg not in rise_seg_done:
                Rtxt = 'r' + str(Rseg)
                Rlen = rise_days[Rseg]
                Rstart = rise_starts[Rseg]
                Rend = rise_ends[Rseg]
                break
            else: Rseg = None
            Rindex += 1
        # ----------------------------------------- end of 'while'

        # are we in a RISE-to-SET band?
        r2s_band = False
        for Rband, Sband in RISE_to_SET_band:
            if Rseg in Rband and Sseg in Sband:
                r2s_band = True

        # are we in a SET-to-RISE band?
        s2r_band = False
        for Sband, Rband in SET_to_RISE_band:
            if Sseg in Sband and Rseg in Rband:
                s2r_band = True

        if s2r_band:
            m = '      S'
            m += ' none' if Sseg is None else str(Sseg) + ' start ' + str(Sstart) + ' end ' + str(Send)
            m += ' ' * (30 - len(m)) + 'R'
            m += ' none' if Rseg is None else str(Rseg) + ' start ' + str(Rstart) + ' end ' + str(Rend)
        else:
            m = '      R'
            m += ' none' if Rseg is None else str(Rseg) + ' start ' + str(Rstart) + ' end ' + str(Rend)
            m += ' ' * (30 - len(m)) + 'S'
            m += ' none' if Sseg is None else str(Sseg) + ' start ' + str(Sstart) + ' end ' + str(Send)

        overlap = 0
        if Rseg is not None and Sseg is not None:
            # we have a RISE and a SET segment to process - do their dates overlap?
            overlap = len(range(max(Rstart,Sstart), min(Rend,Send)))
            m += ' ' * (53 - len(m))
            if overlap == 0:
                m += "no overlap"
            else:
                m += str(overlap) + " days overlap"

        if r2s_band: m += ' ' * (70 - len(m)) + 'R2S_band'
        if s2r_band: m += ' ' * (70 - len(m)) + 'S2R_band'

        prnt(m)

        doSET = False
        if s2r_band and len(set_segs) == 1 and len(rise_segs) > 1:
            doSET = True        # True if SET to multi-RISE
        if s2r_band and set_ep[Sseg] == ('DAH', 'DBH'):
            doSET = True        # Venus 70° - 72°N 2020

        # if both RISE and SET segmments start on same day, process the shorter segment first
        # ... otherwise process the segment that starts first
#        if not doSET and Rseg is not None and Sseg is not None:
        if not doSET and s2r_band:      # Mercury 65°N 2020
            if Rstart == Sstart and Slen < Rlen: doSET = True   # e.g.  Venus 67°N 2026
            elif Sstart < Rstart and Sseg is not None: doSET = True

        path = ''       # new path to fill
        # ........................................................................................
        # ................................  trace a RISE segment  ................................
        # ........................................................................................

        if Rseg is not None and not doSET:
            # trace a RISE segment
            if Rseg not in rise_seg_done:
                rise_seg_done.append(Rseg)      # rise segment processed

            forwR = True    # RISE trace direction
            if (rise_ep[Rseg] == ('DAH', 'EoY') and Sseg is not None and overlap > 0) \
            or (rise_ep[Rseg] == ('DAH', '24h') and s2r_band):

                # trace RISE segment backwards
                forwR = False
                if rise_ep[Rseg][1] == '00h': path += 'B'+ str(Rend) + ','
                if rise_ep[Rseg][1] == '24h': path += 'T'+ str(Rend) + ','
                path += Rline(Rend, Rstart, Rtxt)                                   #<<<rise<<<
                if rise_ep[Rseg][0] == '00h': path += 'B'+ str(Rstart) + ','
                if rise_ep[Rseg][0] == '24h': path += 'T'+ str(Rstart) + ','
                if rise_ep[Rseg] == ('DBH', '00h'):
                    path += 'B' + str(Rstart) + ','
                elif rise_ep[Rseg] == ('SoY', 'DBH'):   # Venus 70°N 2000
                    path += 'B' + str(Rstart) + ','

            else:   # trace RISE segment forwards
                if rise_ep[Rseg][0] == 'SoY' and r2s_band: path += 'B'+ str(Rstart) + ','
                if rise_ep[Rseg][0] in ['00h', 'DBH']: path += 'B'+ str(Rstart) + ','
                if rise_ep[Rseg][0] == '24h': path += 'T'+ str(Rstart) + ','
                if rise_ep[Rseg] in [('DAH', 'DBH'), ('DAH', '00h')] and r2s_band:
                    # Venus 70°N 2000; Mercury 71°N 2000
                    path += 'B'+ str(Rstart) + ','
                path += Rline(Rstart, Rend, Rtxt)                                   #>>>rise>>>
                if rise_ep[Rseg][1] in ['00h', 'DBH', 'EoY']: path += 'B'+ str(Rend) + ','
                if rise_ep[Rseg][1] == '24h': path += 'T'+ str(Rend) + ','
                if rise_ep[Rseg] == ('00h', 'DBH'):
                    path += 'B' + str(Rend) + ','

#               elif rise_ep[Rseg] in [('SoY', 'DAH'), ('SoY', '00h')] and overlap == 0:
                elif rise_ep[Rseg] == ('SoY', '00h') and overlap == 0:
                    # Mercury 65°N 2000, Venus 67°N 2000
                    path += 'B'+ str(Rend) + ','
                    path += 'B' + str(Rstart) + ','

            # only consider the SET if it overlaps with the RISE
#            if Sseg is not None and overlap > 0 and rise_ep[Rseg] != ('DBH', 'DBH'):
            if Sseg is not None and s2r_band and rise_ep[Rseg] != ('DBH', 'DBH'):
                if Sseg not in set_seg_done:
                    set_seg_done.append(Sseg)       # set  segment processed
                if rise_ep[Rseg] == ('DAH', 'DAH') and set_ep[Sseg] == ('DAH', 'DAH'):
                    # trace SET segment backwards (Uranus 70°N 2026)
                    path += Sline(Send, Sstart, Stxt)                               #<<<set<<<

                if rise_ep[Rseg] in [('DBH', 'DAH'), ('SoY', 'DAH')]:
                    # trace SET segment backwards (Venus 67°N 2026)
                    #if set_ep[Sseg][1] == '00h': path += 'B'+ str(Send) + ','
                    #if set_ep[Sseg][1] == '24h': path += 'T'+ str(Send) + ','
                    path += Sline(Send, Sstart, Stxt)                               #<<<set<<<
                    if set_ep[Sseg][0] == '00h': path += 'B'+ str(Sstart) + ','
                    #if set_ep[Sseg][0] == '24h': path += 'T'+ str(Sstart) + ','

                    path += 'B' + str(Rstart) + ','

                elif rise_ep[Rseg] == ('SoY', 'DAH'):
                    # trace SET segment backwards (Jupiter 67°N 2026)
                    path += Sline(Send, Sstart, Stxt)                               #<<<set<<<

                elif rise_ep[Rseg] == ('SoY', '00h'):
                    if set_ep[Sseg] == ('SoY', '00h') and Slen < Rlen:
                        # trace SET segment backwards
                        path += 'B' + str(Rend) + ','
                        path += 'B' + str(Send) + ','
                        path += Sline(Send, Sstart, Stxt)                           #<<<set<<<
                    else:
                        path += 'B' + str(Rstart) + ','

                elif rise_ep[Rseg] in [('SoY', 'EoY'), ('SoY', 'DBH')]:
                    # Mercury 63°N 2026; Mercury 65°N 2035
                    if set_ep[Sseg] == ('SoY', '00h') \
                    or (set_ep[Sseg] == ('00h', '00h') and s2r_band):

                        # trace SET segment backwards
                        if set_ep[Sseg][1] == '00h': path += 'B'+ str(Send) + ','
                        if set_ep[Sseg][1] == '24h': path += 'T'+ str(Send) + ','
                        path += Sline(Send, Sstart, Stxt)                           #<<<set<<<
                        if set_ep[Sseg][0] == '00h': path += 'B'+ str(Sstart) + ','
                        if set_ep[Sseg][0] == '24h': path += 'T'+ str(Sstart) + ','
                        if set_ep[Sseg] == ('00h', '00h'):
                            path += 'B'+ str(Rstart) + ','   # Mercury 63°N 2026

                    else:   # Mercury  60°S 30°S 2026
                        ###path += 'B' + str(Rend) + ','
                        path += 'B' + str(Rstart) + ','

                elif rise_ep[Rseg] == ('DAH', 'EoY') and not r2s_band:
                    # trace SET segment forwards
                    path += Sline(Sstart, Send, Stxt)                               #>>>set>>>
                    if set_ep[Sseg][1] == '00h': path += 'B'+ str(Send) + ','
                    if set_ep[Sseg][1] in ['24h']: path += 'T'+ str(Send) + ','

                elif rise_ep[Rseg] == ('DAH', '24h') and s2r_band: # Mars 72.0°N 2000
                    # trace SET segment forwards
                    path += Sline(Sstart, Send, Stxt)                               #>>>set>>>
                    if set_ep[Sseg] == ('DAH', 'EoY'): path += 'T'+ str(Send) + ','

            path = path[:-1]
            path = trimpath(path)   # avoid identical first and last fixed position elements
            p = path
            tp = []
            txt = 'path:'
            n = p.find(',', 70)
            while n != -1:
                prnt("      {}       {}".format(txt,p[:n+1]))
                tp.append("{} {}".format(txt,p[:n+1]))
                txt = '     '
                p = p[n+1:]
                n = p.find(',', 70)
            prnt("      {}       {}".format(txt,p))
            tp.append("{} {}".format(txt,p))

            TEX += fillpath(path, 'LightSlateGrey', '0.9', tp)
            path = ''

            # .....................................................................
            # ..............  add   T E X T  /  A N N O T A T I O N  ..............
            # ..............         "<planet name> rise/set"        ..............
            # .....................................................................

            #   "<planet name> rise"
            prnt("      annotate rise seg {} ..... #01".format(Rseg))
            tex8, txtXY = TA_rise(obj,Rseg)  # add text annotation
            TEX += tex8

            if Sseg is not None and Sseg in set_seg_done:
                #   "<planet name> set"
                prnt("      annotate set  seg {} ..... #02".format(Sseg))
                tex9, txtXY = TA_set(obj,Sseg)     # add text annotation
                TEX += tex9
                Sseg = None                     # set  segment processed & annotated

        # .........................................................................................
        # .............................  trace SET segment(s) in band  ............................
        # .........................................................................................
        if Sseg is not None:
            # trace a SET segment
            if Sseg not in set_seg_done:
                set_seg_done.append(Sseg)       # set  segment processed

            forwS = True    # SET trace direction
            if (set_ep[Sseg] == ('DAH', '00h') and Rseg is not None and overlap > 0) \
            or (set_ep[Sseg] == ('DAH', 'DBH') and s2r_band) \
            or len(rise_segs) > 1: forwS = False
            # note: multiple RISE segs must be procesed forwards - hence trace SET backwards ;-)

            if not forwS:
                # trace SET segment backwards
                if set_ep[Sseg][1] == '00h': path += 'B'+ str(Send) + ','
                if set_ep[Sseg][1] in  ['24h', 'DBH']: path += 'T'+ str(Send) + ','

                path += Sline(Send, Sstart, Stxt)                                   #<<<set<<<

                if set_ep[Sseg][0] == '00h': path += 'B'+ str(Sstart) + ','
                if set_ep[Sseg][0] == '24h': path += 'T'+ str(Sstart) + ','
                if set_ep[Sseg] in [('DBH', '24h'), ('SoY', 'DBH')]:
                    path += 'T' + str(Sstart) + ','

                elif set_ep[Sseg] == ('SoY', '24h'):
                    path += 'T' + str(Sstart) + ','

                elif set_ep[Sseg] == ('SoY', 'EoY') and Rseg is None:   # Mercury 51.5N 2026
                    path += 'T' + str(Sstart) + ','

                elif len(rise_segs) > 1 and rise_ep[Rseg][0] == '24h':  # Mars 62°-64°N 2028
                    path += 'T' + str(Sstart) + ','

            else:   # trace SET segment forwards
                if set_ep[Sseg] in [('SoY', 'EoY'), ('SoY', 'DAH'), ('SoY', 'DBH'), ('SoY', '24h')] \
                and not s2r_band: # Mercury 60°S 2010, ..., Mercury 69°N 2010, Mercury 66°N 2010
                    path += 'T'+ str(Sstart) + ','
                elif set_ep[Sseg][0] == 'SoY' and s2r_band and rise_ep[Rseg][0] != 'SoY':
                    path += 'T'+ str(Sstart) + ','  # not Mars 0°N 2010, but Neptune 60°S 2000
                elif set_ep[Sseg][0] == 'DAH' and Rstart > Sstart:
                    path += 'T'+ str(Sstart) + ','
                if set_ep[Sseg][0] == '00h': path += 'B'+ str(Sstart) + ','
                if set_ep[Sseg][0] in ['24h', 'DBH']: path += 'T'+ str(Sstart) + ','

                path += Sline(Sstart, Send, Stxt)                                   #>>>set>>>

                if set_ep[Sseg][1] == '00h': path += 'B'+ str(Send) + ','
                if Rseg is None and not fsEoY:
                    path += 'T'+ str(Send) + ',' # Venus 65° 67°N 2026
                if set_ep[Sseg] == ('DAH', 'EoY'): path += 'T'+ str(Send) + ',' # Mars 67°N 2000
                # exclude 'EoY' below: Uranus 65°N 2026
                if set_ep[Sseg][1] == '24h': path += 'T'+ str(Send) + ','
                if set_ep[Sseg][1] in ['DBH', 'EoY']:
                    if not s2r_band \
                    or (s2r_band and rise_ends[Rseg] < set_ends[Sseg]): # Mercry 67°N 2020
                        path += 'T'+ str(Send) + ',' # ----; Mars 66°N 2000

                # ----; Mercury 71°N 2026 (R singularity)
                if set_ep[Sseg] in [('DAH', 'DBH'), ('DBH', 'DAH')]:  # remove ('24h', 'DBH')
                    path += 'T' + str(Send) + ','

                # Mars 69°N 2050
                if set_ep[Sseg][1] == '00h' and len(set_segs) > Sindex:

                    # add next SET segment in the r2s band
                    Sindex += 1
                    while Sindex < len(set_segs):
                        Stmp = set_segs[Sindex]     # SET segment in the band
                        if Stmp not in set_seg_done:
                            seg6 = Sseg     # save for text annotation
                            Sseg = Stmp
                            Stxt = 's' + str(Sseg)
                            Slen = set_days[Sseg]
                            Sstart = set_starts[Sseg]
                            Send = set_ends[Sseg]
                            if set_ep[Sseg] in [('00h', 'EoY'), ('00h', '00h')]:
                                set_seg_done.append(Sseg)      # set segment processed
                                path += 'B'+ str(Sstart) + ','
                                path += Sline(Sstart, Send, Stxt)                   #>>>set>>>
                                if set_ep[Sseg][1] == '00h':
                                    path += 'B'+ str(Send) + ','
                                    path += 'B' + str(dmax-helix) + ',' # include bottom right corner
                            break
                        else: Sseg = None
                        Sindex += 1
                    # ----------------------------------------- end of 'while'

        # .........................................................................................
        # ............................  trace RISE segment(s) in band  ............................
        # .........................................................................................

        # ..................... RISE segment to be traced BACKWARDS .....................

            # only consider the RISE if it overlaps with the SET
            if forwS and Rseg is not None and s2r_band:

                if Rseg not in rise_seg_done:
                    rise_seg_done.append(Rseg)      # rise segment processed

                # Mars 67°N 2026; Mars 66°N 2026
                if set_ep[Sseg] in [('DBH', 'DAH'), ('SoY', 'DAH')] and s2r_band:
                    # trace RISE segment backwards
                    path += Rline(Rend, Rstart, Rtxt)                               #<<<rise<<<
                    if rise_ep[Rseg][0] == '24h': path += 'T'+ str(Rstart) + ','
                    path += 'T' + str(Sstart) + ','

                elif set_ep[Sseg] == ('24h', 'DAH') and rise_ep[Rseg] == ('24h', 'DAH'):
                    # trace RISE segment backwards (Mercury 70°N 2026)
                    path += Rline(Rend, Rstart, Rtxt)                               #<<<rise<<<
                    path += 'T'+ str(Rstart) + ','

                elif set_ep[Sseg] in [('24h', 'EoY'), ('SoY', '00h'), ('24h', 'DBH'), ('DBH', 'EoY'), ('00h', '00h')] \
                and ((rise_ep[Rseg] == ('24h', 'EoY') and s2r_band) \
                or (rise_ep[Rseg] == ('24h', '24h') and s2r_band) \
                or (rise_ep[Rseg] == ('SoY', 'EoY') and s2r_band)):
#                if (rise_ep[Rseg] == ('24h', 'EoY') and Rlen < Slen) \ # removed for Jupiter 60°S 2030

                    if set_ep[Sseg][1] == '00h' and rise_ep[Rseg][1] == 'EoY':
                        # NOT for Mars 60°S 2037 ?
                        path += 'B' + str(dmax-helix) + ',' # include bottom right corner
                    elif set_ep[Sseg][1] == '00h' and rise_ep[Rseg][1] == '24h':
                        # Mars 65°N 2018 (neither Sseg nor Rseg end with 'DBH'.....)
                        for rng in dbh_range:
                            dbh_fr = rng.start; dbh_to = rng.stop - 1
                            if Send + 1 == dbh_fr:
                                path += 'T'+ str(Send) + ','

                    # trace RISE segment backwards
                    if rise_ep[Rseg][1] == '00h': path += 'B'+ str(Rend) + ','
                    if rise_ep[Rseg][1] == '24h': path += 'T'+ str(Rend) + ','
                    path += Rline(Rend, Rstart, Rtxt)                               #<<<rise<<<
                    if rise_ep[Rseg][0] == '00h': path += 'B'+ str(Rstart) + ','
                    if rise_ep[Rseg][0] == '24h': path += 'T'+ str(Rstart) + ','

                    if set_ep[Sseg][0] == 'SoY' and s2r_band and rise_ep[Rseg][0] != 'SoY':
                        path += 'T0,'  # include top left corner

                elif set_ep[Sseg] == ('SoY', '00h') and rise_ep[Rseg] in [('SoY', '00h')] \
                and Rlen > Slen:
                    # trace RISE segment backwards (Jupiter 51.5N 2026)
                    if rise_ep[Rseg][1] == '00h': path += 'B'+ str(Rend) + ','
                    if rise_ep[Rseg][1] == '24h': path += 'T'+ str(Rend) + ','
                    path += Rline(Rend, Rstart, Rtxt)                               #<<<rise<<<

                elif set_ep[Sseg] in [('SoY','00h')] and rise_ep[Rseg] == ('SoY','DBH') \
                and s2r_band:
                    # Mars 67°-71°N 2027
                    path += 'B'+ str(Rend) + ','
                    path += Rline(Rend, Rstart, Rtxt)                               #<<<rise<<<

                elif set_ep[Sseg] in [('DBH','00h'),('SoY','00h'),('00h','00h')] and rise_ep[Rseg] == ('24h','DBH') \
                and s2r_band:
                    # Jupiter 68°N 2020; Jupiter 69°N 2030, Jupiter 72°N 2042
                    path += 'B'+ str(Rend) + ','
                    path += Rline(Rend, Rstart, Rtxt)                               #<<<rise<<<
                    path += 'T'+ str(Rstart) + ','

                elif set_ep[Sseg] == ('DBH','00h') and rise_ep[Rseg] == ('24h','EoY') \
                and s2r_band:
                    # Saturn 69°N 2020, not Mars 69°N 2050
                    path += 'B'+ str(dmax-helix) + ','   # to bottom right corner
                    path += Rline(Rend, Rstart, Rtxt)                               #<<<rise<<<
                    path += 'T'+ str(Rstart) + ','

                elif set_ep[Sseg] == ('00h', 'EoY') and rise_ep[Rseg] == ('24h','EoY') \
                and s2r_band:
                    # Mars 69°N 2050
                    path += Rline(Rend, Rstart, Rtxt)                               #<<<rise<<<
                    path += 'T'+ str(Rstart) + ','

                elif set_ep[Sseg] in [('SoY', 'EoY'), ('SoY', 'DBH'), ('DBH', 'DBH')] and forwS:
                    # ...; Venus 67°N 2025; Mars 70°N 2050
                    if rise_ep[Rseg] == ('24h', 'EoY') \
                    or (rise_ep[Rseg] in [('24h', '24h'), ('24h', 'DBH')] and s2r_band and forwS):

                        # trace RISE segment backwards
                        if rise_ep[Rseg][1] == '00h': path += 'B'+ str(Rend) + ','
                        if rise_ep[Rseg][1] == '24h': path += 'T'+ str(Rend) + ','
                        path += Rline(Rend, Rstart, Rtxt)                           #<<<rise<<<
                        if rise_ep[Rseg][0] == '00h': path += 'B'+ str(Rstart) + ','
                        if rise_ep[Rseg][0] == '24h': path += 'T'+ str(Rstart) + ','
###                        path += 'T0,'    # remove for Venus 66°N 2030

                elif set_ep[Sseg] == ('SoY', '00h'):
                    if rise_ep[Rseg] == ('SoY', '00h') and Slen < Rlen: # Jupiter 51.5N 2026
                        path += 'B' + str(Rend) + ','
                        path += Rline(Rend, Rstart, Rtxt)                           #<<<rise<<<

        # ..................... RISE segment to be traced FORWARDS .....................

            if not forwS and Rseg is not None and s2r_band:

                if Rseg not in rise_seg_done:
                    rise_seg_done.append(Rseg)      # rise segment processed

                if set_ep[Sseg] in [('DAH', '00h'), ('DAH', '24h'), ('DAH', 'EoY'), ('DAH', 'DAH'), ('DAH', 'DBH')] \
                or (set_ep[Sseg] in [('SoY', 'EoY'), ('SoY', '00h')] and not forwS): # Mars 62°-64°N 2028, Mars 60°-58°S 2037, Mercury 71°N 2041, Jupiter 72°N 2038
                    # trace RISE segment forwards
                    if rise_ep[Rseg][0] == '24h': path += 'T'+ str(Rstart) + ','
                    path += Rline(Rstart, Rend, Rtxt)                               #>>>rise>>>
                    if rise_ep[Rseg][1] in ['00h', 'DBH', 'EoY']: path += 'B'+ str(Rend) + ','
                    if rise_ep[Rseg][1] in ['24h']: path += 'T'+ str(Rend) + ','

                    # add next RISE segment in the r2s band
                    Rindex += 1
                    while Rindex < len(rise_segs):
                        Rtmp = rise_segs[Rindex]     # RISE segment in the band
                        if Rtmp not in rise_seg_done:
                            seg7 = Rseg     # save for text annotation
                            Rseg = Rtmp
                            Rtxt = 'r' + str(Rseg)
                            Rlen = rise_days[Rseg]
                            Rstart = rise_starts[Rseg]
                            Rend = rise_ends[Rseg]
                            if rise_ep[Rseg] in [('24h', '24h'), ('24h', 'DAH'), ('24h', 'EoY')]:
                                # , Mercury 71°N 2041, Mars 62°-64°N 2028
                                rise_seg_done.append(Rseg)      # rise segment processed
                                path += 'T'+ str(Rstart) + ','
                                path += Rline(Rstart, Rend, Rtxt)                   #>>>rise>>>
                                if rise_ep[Rseg][1] == '24h': path += 'T'+ str(Rend) + ','
                                if rise_ep[Rseg][1] == 'EoY' and set_ep[Sseg][1] == '00h': # Mars 60°S 2037
                                    path += 'B' + str(dmax-helix) + ',' # include bottom right corner
                            break
                        else: Rseg = None
                        Rindex += 1
                    # ----------------------------------------- end of 'while'

            path = path[:-1]
            path = trimpath(path)   # avoid identical first and last fixed position elements
            p = path
            tp = []
            txt = 'path:'
            n = p.find(',', 70)
            while n != -1:
                prnt("      {}       {}".format(txt,p[:n+1]))
                tp.append("{} {}".format(txt,p[:n+1]))
                txt = '     '
                p = p[n+1:]
                n = p.find(',', 70)
            prnt("      {}       {}".format(txt,p))
            tp.append("{} {}".format(txt,p))

            TEX += fillpath(path, 'LightSlateGrey', '0.9', tp)
            path = ''

            # .....................................................................
            # ..............  add   T E X T  /  A N N O T A T I O N  ..............
            # ..............         "<planet name> rise/set"        ..............
            # .....................................................................

            #   "<planet name> set"
            prnt("      annotate set  seg {} ..... #03".format(Sseg))
            tex9, txtXY = TA_set(obj,Sseg)     # add text annotation
            TEX += tex9

            if seg6 is not None:
                #   "<planet name> set"
                prnt("      annotate set  seg {} ..... #05".format(seg6))
                tex9, txtXY = TA_set(obj,seg6)  # add text annotation
                TEX += tex9

            if seg7 is not None:
                #   "<planet name> rise"
                prnt("      annotate rise seg {} ..... #05".format(seg7))
                tex8, txtXY = TA_rise(obj,seg7)  # add text annotation
                TEX += tex8

            if Rseg is not None and Rseg in rise_seg_done:
                #   "<planet name> rise"
                prnt("      annotate rise seg {} ..... #04".format(Rseg))
                tex8, txtXY = TA_rise(obj,Rseg)  # add text annotation
                TEX += tex8
                Rseg = None                     # rise segment processed & annotated

        # This loops when there are SEPARATE shading areas within the same band, e.g. Mercury 62°-63°N 2000
    # ----------------------------------------- end of 'while'

    if verbose and (len(set_segs) > Sindex+1 or len(rise_segs) > Rindex+1):
        print("ERROR: fill_below_horizon - not all segments processed in band\nset_segs: {}\nrise_segs: {}".format(set_segs,rise_segs));sys.exit(0)

    return TEX

def getDAWN_DUSK():
# here we only identify the the region when noDAWN and noDUSK exists!

    DAWN_fr = -1; DAWN_to = -1
    noDAWN_fr = -1; noDAWN_to = -1
    if len(seglen_DAWN) == 3:
        DAWN_fr = seglen_DAWN[0] - seglen_DAWN[1]
        DAWN_to = seglen_DAWN[0] - 1
        noDAWN_fr = seglen_DAWN[0]
        noDAWN_to = seglen_DAWN[0] - seglen_DAWN[1] -1

    DUSK_fr = -1; DUSK_to = -1
    noDUSK_fr = -1; noDUSK_to = -1
    if len(seglen_DUSK) == 3:
        DUSK_fr = seglen_DUSK[0] - seglen_DUSK[1]
        DUSK_to = seglen_DUSK[0] - 1
        noDUSK_fr = seglen_DUSK[0]
        noDUSK_to = seglen_DUSK[0] - seglen_DUSK[1] -1

    return DAWN_fr, DAWN_to, DUSK_fr, DUSK_to, noDAWN_fr, noDAWN_to, noDUSK_fr, noDUSK_to

# .......................................................................................
# ............................  fill gold RISE-to-SET bands  ............................
# .......................................................................................

# ---------- trace codes ----------
#     -1  trace nothing / stop tracing in current direction
#      0  follow 00h
#      1  trace RISE segment
#      2  trace  SET segment
#      3  trace DAWN
#      4  trace DUSK
#      9  follow 24h
# ---------------------------------

def fill_above_horizon(obj, rise_segs, set_segs):

    # this function accepts RISE_to_SET bands and SET_to_RISE bands
    # however the RISE_to_SET bands have to be processed first ??????????????????????????????????

    TEX = ''
    Rindex = 0
    Sindex = len(set_segs) - 1
    msg7 = "........................................"

    Rseg = None; Rtxt = 'r'; Rstart = 1000; Rlen = Rend = None
    while len(rise_segs) > Rindex:
        Rseg = rise_segs[Rindex]     # first RISE segment in the band
        first_Rseg = Rseg
        if Rseg not in rise_seg_done:
            Rtxt = 'r' + str(Rseg)
            Rlen = rise_days[Rseg]
            Rstart = rise_starts[Rseg]
            first_Rstart = Rstart
            Rend = rise_ends[Rseg]
            first_Rend = Rend
            break
        else: Rseg = None
        Rindex += 1
    # ----------------------------------------- end of 'while'

    Sseg = None; Stxt = 's'; Sstart = 1000; Slen = Send = None
    while Sindex >= 0:
        Sseg = set_segs[Sindex]      # last SET segment in the band
        if Sseg not in set_seg_done:
            Stxt = 's' + str(Sseg)
            Slen = set_days[Sseg]
            Sstart = set_starts[Sseg]
            Send = set_ends[Sseg]
            break
        else: Sseg = None
        Sindex -= 1
    # ----------------------------------------- end of 'while'

    # one2one is True if only 1 RISE seg and 1 SET seg in a band
    one2one = True if len(rise_segs) == 1 and len(set_segs) == 1 else False
    one2two = True if len(rise_segs) == 1 and len(set_segs) == 2 else False
    two2one = True if len(rise_segs) == 2 and len(set_segs) == 1 else False

    # are we in a RISE-to-SET band?
    r2s_band = False
    i = 0
    for Rband, Sband in RISE_to_SET_band:
        if Rseg in Rband and Sseg in Sband:
            r2s_band = True
            band_min = RISE_to_SET_band_range[i][0]
            band_max = RISE_to_SET_band_range[i][1]
            break
        i += 1

    # are we in a SET-to-RISE band?
    s2r_band = False
    for Sband, Rband in SET_to_RISE_band:
        if Sseg in Sband and Rseg in Rband:
            s2r_band = True

    if s2r_band:
        m = '      S'
        m += ' none' if Sseg is None else str(Sseg) + ' start ' + str(Sstart) + ' end ' + str(Send)
        m += ' ' * (30 - len(m)) + 'R'
        m += ' none' if Rseg is None else str(Rseg) + ' start ' + str(Rstart) + ' end ' + str(Rend)
    else:
        m = '      R'
        m += ' none' if Rseg is None else str(Rseg) + ' start ' + str(Rstart) + ' end ' + str(Rend)
        m += ' ' * (30 - len(m)) + 'S'
        m += ' none' if Sseg is None else str(Sseg) + ' start ' + str(Sstart) + ' end ' + str(Send)

    overlap = 0
    if Rseg is not None and Sseg is not None:
        # we have a RISE and a SET segment to process - do their dates overlap?
        overlap = len(range(max(Rstart,Sstart), min(Rend,Send)))
        m += ' ' * (53 - len(m))
        if overlap == 0:
            m += "no overlap"
        else:
            m += str(overlap) + " days overlap"

    if r2s_band: m += ' ' * (70 - len(m)) + 'R2S_band'
    if s2r_band: m += ' ' * (70 - len(m)) + 'S2R_band'
    prnt(m)
    prnt('      scan from {} {} to {} {}'.format(band_min,DOY(band_min),band_max,DOY(band_max)))

    if not r2s_band: return TEX     # here we only process r2s bands

    # .......................................................................................
    # >>>>>>>>>>>>>>>>  trace nothing, 00h, DAWN or RISE segment(s) forwards  >>>>>>>>>>>>>>>
    # .......................................................................................

    DAWN_fr, DAWN_to, DUSK_fr, DUSK_to, noDAWN_fr, noDAWN_to, noDUSK_fr, noDUSK_to = getDAWN_DUSK()

    if r2s_band and config.PV_df:
        print("      DAWN up to {} and from {} ".format(DOY(DAWN_to), DOY(DAWN_fr)))

    # scan the RISE_to_SET band range forwards
    idx_fr = band_min
    idx_to = band_max
    maxloops = 3

    # NEW: there can be more than one area to fill on the RISE segment...
    while idx_fr < band_max:
        maxloops -=1
        if maxloops < 0: break
        if maxloops < 2 and verbose: print(msg7)

        # process RISE segment(s) in a RISE-to-SET band
        path = ''       # new path to fill
        tracing = -1    # not tracing anything
        trace = -1
        fr00 = -1       # starting 00h value
        to00 = -1       #   ending 00h value
        dsk_fr = -1     # begin tracing DUSK from
        dwn_fr = -1     # begin tracing DAWN from
        tfr = -1        # trace area begins here
        PV_df = '>>> '
        max_loops = 5
        halt_fwd = False

        while r2s_band and len(rise_segs) > Rindex:
            max_loops -= 1
            if max_loops < 0: break

            if Rseg not in rise_seg_done:
                rise_seg_done.append(Rseg)      # rise segment processed

            # I guess every possible type should be in this list...
            if RISEep[Rseg] not in [('SoY', '00h'), ('SoY', 'DAH'), ('SoY', 'DBH'), ('SoY', 'EoY'), \
            ('00h', '00h'), ('00h', 'DBH'), ('00h', 'EoY'), \
            ('DAH', 'DBH'), ('DAH', '00h'), ('DAH', 'EoY'), \
            ('DBH', '00h'), ('DBH', 'DAH'), ('DBH', 'DBH'), ('DBH', 'EoY'), \
            ('24h', 'DBH'), ('24h', 'EoY')]:
                print("ERROR: Add {} to RISE list types in R2S band".format(RISEep[Rseg])); sys.exit(0)

            prnt("      >>> RISE {} for idx from {} to {}".format(Rseg,idx_fr,idx_to))
            # forward direction
            for idx in range(idx_fr, idx_to+1):
                dawn = f_AM(civilY_AM[idx])
                dusk = f_PM(civilY_PM[idx])
                # get RISE and SET time only for the specified segments
                objrise_Y_idx, objset_Y_idx = get_Y(idx,Rseg,Sseg)
                # print(idx,objrise_Y_idx, objset_Y_idx)

                dwn, dsk = btwn_RISE_to_SET(idx,Rseg,Sseg)
                # print(idx,objset_Y_idx,dusk,objrise_Y_idx)  # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                # if tracing == 3 and objset_Y_idx < dawn < objrise_Y_idx:
                if (objset_Y_idx is not None and tracing in [0, 3] and objset_Y_idx < dawn):
                    # tracing = 0 for Saturn 68°N 2020, Saturn 62°N 2045
                    prnt("      !! HALT_FWD",idx,dwn,dsk,trace,objrise_Y_idx,"!!")
                    halt_fwd = True         # Saturn 68°N 2020 (don't modify 'trace')
                    trace = -1              # Venus 71°N 2000
                    # idx_fr = idx - 1       # Jupiter 60°S 2010

                else:
                    if Rstart <= idx <= Rend:
                        # trace RISE or trace Dawn/Dusk?
                        # note - Saturn 72°N 2000: objrise_Y_idx == dawn on May 4
                        if dusk >= objrise_Y_idx >= dawn: trace = 1     # trace RISE
                        elif objset_Y_idx is not None and objset_Y_idx >= dawn >= objrise_Y_idx:
                            trace = 3           # trace DAWN (Saturn 71°N 2015)
                        elif objset_Y_idx is None and dawn >= objrise_Y_idx:
                            trace = 3           # trace DAWN
                  #OLD: elif dawn < objset_Y_idx < objrise_Y_idx: trace = 3
                        elif dwn: trace = 3         # trace DAWN (Jupiter 60°S 2000, not Saturn 72°N 2010))
                        elif dsk: trace = 4         # trace DUSK (Saturn 61°N-72°N 2015)
##                        elif dusk <= objrise_Y_idx: # NOT for Saturn 72°N 2015 !!
##                            trace = 4   # trace DUSK Saturn 62°N-70°N 2015 -- NOT for Mars 60°S-65°N 2010 !!!
                        elif idx == DUSK_to and RISEep[Rseg][0] == '24h':
                            trace = 1       # trace RISE (Jupiter 71°N 2030)
                        else:
                            prnt("      !! HALT_FWD",idx,dwn,dsk,trace,objrise_Y_idx,"!!!")
                            trace = -1    # trace neither RISE, DAWN nor DUSK
                            halt_fwd = True     # ESSENTIAL: Saturn 69°N 2020

                    else: # if *not* within RISE segment Rseg range...
                        # do NOT reference dwn or dsk here... (they're always False)
                        if tracing == 0:
                            if idx == Send:
                                trace = -1 # Saturn 62°N 2015
                            # trace DAWN (Jupiter 62°N 2010)
                            # elif idx == DAWN_fr and objset_Y_idx < dawn: trace = -1  # Saturn 68°N 2020
                            else: trace = 3 if dawn > 0.0 else 0
                        elif RISEep[Rseg][0] == '00h' and SETep[Sseg][0] in ['24h','DAH']:
                            # Mars 66-71°N 2000, Mercury 69°N 2015
##                            trace = 0           # follow 00h NOT for Mars 68°N 2015
                            trace = 3 if dawn > 0.0 else 0
                            if tracing == 3 and idx == noDAWN_fr:
                                fr00 = idx-1                        # Saturn 62°N 2015
                            if fr00 == -1: fr00 = idx       #  (not Saturn 72°N 2000)

                        # elif dawn > 0.0:
                            # trace = 3                  # trace DAWN (Mars 72°N 2000)
                        # else: trace = -1    # trace neither RISE, DAWN nor DUSK

                        else:   # Saturn 62°N-70°N 2015 ???????????????????????????
                            trace = 3 if dawn > 0.0 else 0
                            if tracing == 3 and idx == noDAWN_fr:
                                fr00 = idx-1                        # Saturn 62°N 2015
                            if fr00 == -1: fr00 = idx       #  (not Saturn 72°N 2000)

                    if trace != -1 and tfr == -1: tfr = idx     # tracing begins here (Jupiter 60°S 2010)
                    if trace != tracing and trace == 3: dwn_fr = idx
                    if trace != tracing and trace == 4: dsk_fr = idx

                if config.PV_df:
                    PV_df += "{} {}, ".format(idx,trace)
                    if verboase and len(PV_df) > 80: print(PV_df); PV_df = '>>> '

                if tracing == -1:
                    tracing = trace     # initialisation
                    x_start = idx       # not = Rstart

                # tc = trace != tracing   # True if trace changed
                xx = (trace == tracing) and (idx != idx_to) and not halt_fwd

                # -.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.
                if trace != tracing or idx in [Rend,idx_to] or halt_fwd:
                    if len(PV_df) > 4:
                        prnt(PV_df[:-2])
                        PV_df = '>>> '
                    p = ''      # path element
                    ndx = idx if (idx in [idx_to,Rend] and trace == tracing) else idx-1

                    if tracing == 0:            # end tracing 00h
                        to00 = idx              # Mercury 68°-70°N 2020
#!#                        to00 = idx if idx == DAWN_fr else idx-1     # ???????
                        if verbose and fr00 >= 0:
                            print("      follow 00h from {} to {}".format(fr00,to00))
                        if fr00 >= 0: p += 'B'+ str(fr00) + ','; fr00 = -1      # Mars 66-71°N 2000
                        if to00 != fr00:
                            p += 'B'+ str(to00) + ','
                            halt_fwd = False    # don't decrement idx (Saturn 68°N 2020)

                    if tracing == 1:            # end tracing RISE
                        if RISEep[Rseg][0] == '00h' and x_start == Rstart:
                            # handled with 'end tracing 00h'?
                            if to00 != Rstart: p += 'B'+ str(Rstart) + ','
                            to00 = -1

                        # Jupiter 63°N 2001
                        if (RISEep[Rseg][0] == '00h' or RISEep[Rseg][1] == '00h') \
                        and idx == DAWN_fr: ndx += 1  # at DAWN_fr
                        p += Rline(x_start, ndx, Rtxt)                          #>>>rise>>>

                        if RISEep[Rseg][1] == '00h' and Rend == ndx and DAWN_to <= ndx < DAWN_fr:
                            # NOT Saturn 69° Aug 13 2005
                            # p += 'B'+ str(Rend) + ','; trace = 0; fr00 = ndx    # follow 00h
                            trace = 0; fr00 = ndx    # follow 00h (Mercury 71°N 2010, saturn 68°N 2020)

                        if trace == 3 and idx == idx_to:    # Venus 65° - 66°N 2015
                            p += 'dawn:' + str(dwn_fr) + ','                    #!!!DAWN!!!
                            dwn_fr = -1

                    if not xx and tracing == 3: # end tracing DAWN
                        # note: you CAN have a single DAWN coordinate (Mercury 50°S 2000, Jupiter 60°S 2000)
                        if dwn_fr == ndx:
                            p += 'dawn:' + str(dwn_fr) + ','                    #!!!DAWN!!!
                        else:
                            p += 'dawn:' + str(dwn_fr) + '-' + str(ndx) + ','   #>>>DAWN>>>
                        dwn_fr = -1

                    if not xx and tracing == 4: # end tracing DUSK
                        if dsk_fr == ndx:
                            p += 'dusk:' + str(dsk_fr) + ','                    #!!!DUSK!!!
                        else:
                            p += 'dusk:' + str(dsk_fr) + '-' + str(ndx) + ','   #>>>DUSK>>>
                        dsk_fr = -1

                    if config.PV_df: print("  {} --> {}: ndx {}, x_start {}: {}".format(tracing,trace,ndx,x_start,p))
                    path += p
                    x_start = idx

                tracing = trace
                if halt_fwd:            # 'halt_fwd' means discard the latest idx ...
                    idx_fr = idx-1      # Venus 71°N 2000
                elif trace == -1:       # ... otherwise continue from the latest idx
                    idx_fr = idx        # Saturn 72°N 2000, Saturn 69°N 2020
                    halt_fwd = True     # NEW2020

                if halt_fwd: break      # quit the for loop - switch to last SET segment

                if idx == Rend:         # Jupiter 68°N 2000
                    #idx_fr = idx
                    if trace == 1: tracing = -1
                    # pick next RISE segment in the r2s band, if any
                    n = Rindex + 1
                    while n < len(rise_segs):
                        Rseg = rise_segs[n]
                        if Rseg not in rise_seg_done:
                            Rindex = n
                            Rtxt = 'r' + str(Rseg)
                            Rlen = rise_days[Rseg]
                            Rstart = rise_starts[Rseg]
                            Rend = rise_ends[Rseg]
                            rise_seg_done.append(Rseg)      # rise segment processed
                            prnt("      next Rseg:  {}  index {}".format(Rseg,Rindex))
                            break
                        n += 1
                    # ----------------------------------------- end of 'while'
            # ----------------------------------------- end of 'for'

##            if tfr != -1: band_min = tfr        # Jupiter 60°S 2010, NOT for Mercury 67°N 2015

            if trace != -1 and idx >= idx_to: idx_fr = idx_to   # Venus 71°N 2000
            prnt("      idx_fr {} tfr {} band_min {}".format(idx_fr,tfr,band_min))
            if halt_fwd: break  # quit the while loop

            # Mercury 69°N 2000, Mercury 71°N 2010
            if one2one and RISEep[Rseg] == ('DAH', '00h') and SETep[Sseg] == ('24h', 'DAH'):
                idx_fr = Send           # IMPORTANT - begin tracing SET from Send

            if idx >= idx_to: break
            idx_fr = idx
        # ----------------------------------------- end of 'while'


        # ........................................................................................
        # <<<<<<<<<<<<<<<<<  trace nothing, 24h, DUSK or a SET segment backwards <<<<<<<<<<<<<<<<<
        # ........................................................................................

        # process SET segment(s) in a RISE-to-SET band
        tracing = -1    # not tracing anything
        fr24 = -1       # starting 24h value
        to24 = -1       #   ending 24h value
        dsk_fr = -1     # begin tracing DUSK from
        dwn_fr = -1     # begin tracing DAWN from
        PV_db = '<<< '
        max_loops = 5

        if r2s_band and config.PV_db:
            print("      DUSK up to {} and from {} ".format(DOY(DUSK_to), DOY(DUSK_fr)))

        # do not process a backward path if there is no forward path (Venus 72°N 2015 idx 364 to 359)
        while path != '' and r2s_band and Sindex >= 0:      # only consider the SET(s) if they overlap with the RISE
            max_loops -= 1
            if max_loops < 0: break

            if Sseg not in set_seg_done:
                set_seg_done.append(Sseg)       # set  segment processed

            # I guess every possible type should be in this list...
            if SETep[Sseg] not in [('SoY', '00h'), ('SoY', '24h'), ('SoY', 'DAH'), ('SoY', 'DBH'), \
            ('SoY', 'EoY'), ('DAH', 'DAH'), ('DAH', 'DBH'), ('DAH', 'EoY'), \
            ('DBH', '00h'), ('DBH', '24h'), ('DBH', 'DAH'), ('DBH', 'DBH'), ('DBH', 'EoY'), \
            ('24h', '24h'), ('24h', 'DAH'), ('24h', 'DBH'), ('24h', 'EoY')]:
                print("ERROR: Add {} to SET list types in R2S band".format(SETep[Sseg])); sys.exit(0)

            prnt("      <<< SET {} for idx from {} to {}".format(Sseg,idx_fr,band_min))
            # reverse direction
            for idx in range(idx_fr, band_min-1, -1):
                dawn = f_AM(civilY_AM[idx])
                dusk = f_PM(civilY_PM[idx])
                # get RISE and SET time only for the specified segments (Jupiter 62°N 2000)
                objrise_Y_idx, objset_Y_idx = get_Y(idx,Rseg,Sseg)
                dwn, dsk = btwn_RISE_to_SET(idx,Rseg,Sseg)
                #print(idx,"    ",dwn,dsk)

                if Sstart <= idx <= Send:
                    # trace SET or trace Dawn/Dusk?
                    #trace_set = False
                    if dusk >= objset_Y_idx >= dawn: trace = 2      # trace SET
                    # elif dawn > objset_Y_idx: trace = 3     # trace DAWN ... NOT Saturn 62°N 2015
##                    elif dusk <= objset_Y_idx: trace = 4     # trace DUSK (NOT for Venus 72°N 2000
                    elif dsk: trace = 4         # trace DUSK (Venus 72°N 2000)
                    elif tracing == -1:
                        if DAWN_fr != -1:
                            if idx == Send == DAWN_fr: trace = 2
                            trace = 2                       # Saturn 62°N 2045 !!!
                        else: trace = 2                     # trace SET (Saturn 62°N 2015)
                    else: trace = -1    # trace neither SET, DAWN nor DUSK
                    #print(idx,trace,tracing)

                else: # if *not* within SET segment Sseg range...
                    if dusk < 24.0: trace = 4               # trace DUSK (Mars 69°N 2000)
                    else:
                        trace = 9                           # follow 24h (Mars 68°N 2000 Mercury 66°N 2000)
                        if fr24 == -1:
                            # align fr24 vertically above DUSK_fr
                            fr24 = idx + 1 if idx + 1 == DUSK_fr else idx
                    if trace == 4 and not dsk: trace = -1   # stop tracing reverse direction (Jupiter 60°S) 2015 ??????????????????????????????

                if trace != tracing and trace == 3: dwn_fr = idx
                if trace != tracing and trace == 4: dsk_fr = idx

                if config.PV_db:
                    PV_db += "{} {}, ".format(idx,trace)
                    if len(PV_db) > 80: print(PV_db); PV_db = '<<< '

                if tracing == -1:
                    tracing = trace     # initialisation
                    x_end = idx         # not = Send

                # tc = trace != tracing   # True if trace changed
                xx = (trace == tracing) and (idx != band_min)

                # -.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.
                if trace != tracing or idx in [Sstart,band_min]:
                    if len(PV_db) > 4:
                        prnt(PV_db[:-2])
                        PV_db = '<<< '

                    p = ''      # path element
                    ndx = idx if (idx in [band_min,Sstart] and trace == tracing) else idx+1

                    if tracing == 2:                # end tracing SET
                        if SETep[Sseg][1] == '24h' and x_end == Send:
                            if to24 != Send: p += 'T'+ str(Send) + ','
                            to24 = -1

                        # Jupiter 65°N 2001, Saturn 69°N 2001, Mercury 67°N 2000
                        if (SETep[Sseg][0] == '24h' or SETep[Sseg][1] == '24h') \
                        and idx == DUSK_to: ndx -= 1 # at DUSK_to
                        p += Sline(x_end, ndx, Stxt)                            #<<<set<<<

                        if SETep[Sseg][0] == '24h' and ndx == Sstart: fr24 = Sstart # Mercury 66°N 2000
                        if trace == 4 and idx == band_min:   #Mars 70°N 2015
                            p += 'dusk:' + str(dsk_fr) + ','                    #!!!DUSK!!!
                            dsk_fr = -1

                    if not xx and tracing == 3:     # end tracing DAWN
                        p += Dline(dwn_fr, ndx, 'dawn')                         #<<<DAWN<<<
                        dwn_fr = -1

                    if not xx and tracing == 4:     # end tracing DUSK
                        #if x_end >= Send and currently_noDUSK(x_end):   # Mars 68°N 69°N 2000
                            #p += 'T'+ str(x_end) + ','
                        p += Dline(dsk_fr, ndx, 'dusk')                         #<<<DUSK<<<
                        dsk_fr = -1

                    if not xx and tracing == 9:     # end tracing 24h
                        if verbose and fr24 >= 0:
                            print("      follow 24h from {} to {}".format(fr24,idx))
                        if fr24 >= 0: p += 'T'+ str(fr24) + ','; fr24 = -1
                        if idx != fr24: p += 'T'+ str(idx) + ','; to24 = idx

                    if config.PV_db: print("  {} --> {}: idx_fr {}, ndx {}, x_end {}: {}".format(tracing,trace,idx_fr,ndx,x_end,p))
                    path += p
                    x_end = idx         # Mars 66°N 2000

                tracing = trace
                # Venus 60°S 2000,      Jupiter 68°N 2000 ?
                # print(".... idx = ", idx)
                if trace == -1: idx = band_min; break   # stop tracing altogether (Jupiter 60°S 2015)

                if idx == Sstart:
                    #idx_fr = idx
                    # NOT FOR Venus 60°S 2000 ... this continues tracing DUSK
                    if trace == 2: tracing = -1 # Mercury 62°N 2000
                    ### tracing = -1    # Mercury 62°N 2000
                    # pick previous SET segment in the r2s band, if any
                    n = Sindex - 1
                    while n >= 0:
                        Sseg = set_segs[n]
                        if Sseg not in set_seg_done:
                            Sindex = n
                            Stxt = 's' + str(Sseg)
                            Slen = set_days[Sseg]
                            Sstart = set_starts[Sseg]
                            Send = set_ends[Sseg]
                            set_seg_done.append(Sseg)       # set segment processed
                            prnt("      next Sseg:  {}  index {}".format(Sseg,Sindex))
                            break
                        n -= 1
                    # ----------------------------------------- end of 'while'
            # ----------------------------------------- end of 'for'

            # objset_Y_idx  = getY(objset_Y[Sstart],1)
            dusk = f_PM(civilY_PM[Sstart])
            ###idx_fr = idx
            ###print("      idx_fr",idx_fr)

            if idx <= band_min: break
            ###idx_fr = idx
        # ----------------------------------------- end of 'while'


        path = path[:-1]
        path = trimpath(path)   # avoid identical first and last fixed position elements
        p = path
        tp = []
        txt = 'path:'
        n = p.find(',', 70)
        while n != -1:
            prnt("      {}       {}".format(txt,p[:n+1]))
            tp.append("{} {}".format(txt,p[:n+1]))
            txt = '     '
            p = p[n+1:]
            n = p.find(',', 70)
        prnt("      {}       {}".format(txt,p))
        tp.append("{} {}".format(txt,p))

        TEX += fillpath(path, 'Gold', '0.85', tp)
        path = ''
        idx_fr += 1

        # !!! SKIP INVALID next forward scan STARTING DATES !!! (Saturn 60°S - 60°N 2015, Jupiter 70°N 2030)
        idx_fr0 = idx_fr
        for idx in range(idx_fr0, idx_to+1):
            dawn = f_AM(civilY_AM[idx])
            dusk = f_PM(civilY_PM[idx])
            # get RISE and SET time only for the specified segments
            objrise_Y_idx, objset_Y_idx = get_Y(idx,Rseg,Sseg)
            dwn, dsk = btwn_RISE_to_SET(idx,Rseg,Sseg)      # NEW2020
            if dwn or dsk:                                  # NEW2020
##            if dawn < objset_Y_idx:
                idx_fr = idx                                # NEW2020
                prnt("   continue with idx_fr {}".format(idx_fr))
                break
            if idx == noDUSK_fr and RISEep[Rseg][0] == '24h':  # Jupiter 71°N 2030
                idx_fr = idx-1
                prnt("   continue with idx_fr {}".format(idx_fr))
                break
            idx_fr = idx
        # ----------------------------------------- end of 'for'

    # ----------------------------------------- end of 'while'

    return TEX

# ........................................................................................
# ........................  fill SET segments gold above horizon  ........................
# ........................................................................................

# ---------- trace codes ----------
#     -1  trace nothing / stop tracing in current direction
#      0  follow 00h
#      1  trace RISE segment
#      2  trace  SET segment
#      3  trace DAWN
#      4  trace DUSK
#      9  follow 24h
# ---------------------------------

def fill_SET_above_horizon(obj, Sseg):

    # process SET segment

    TEX = ''
    path = ''       # new path to fill
    Stxt   = 's' + str(Sseg)
    Sspan  = set_days[Sseg]     # segment span in days (not length)
    Sstart = set_starts[Sseg]
    Send   = set_ends[Sseg]
    done = True                 # True for a single pass (not forward & backward trace)

    if Sspan == 0: return TEX   # if segment spans 0 days

    DAWN_fr, DAWN_to, DUSK_fr, DUSK_to, noDAWN_fr, noDAWN_to, noDUSK_fr, noDUSK_to = getDAWN_DUSK()

    # single path (one area to fill during noDAWN)
    if SETep[Sseg] in [('00h', 'DAH'), ('DAH', 'DAH')] \
    and noDAWN_fr <= Sstart <= Send <= noDAWN_to:
        # Mercury 72°N 2015, Mars 69°N 2000

        # scan SET segment range forwards
        if Sseg not in set_seg_done:
            set_seg_done.append(Sseg)       # set segment processed

        tracing = None  # not tracing anything
        ##tfr = -1        # tracing begins here
        n = 0           # count days during SET trace when above Dawn
        for idx in range(Sstart, Send+1):
            # objset_Y_idx  = getY(objset_Y[idx])
            # objrise_Y_idx = getY(objrise_Y[idx])
            objrise_Y_idx, objset_Y_idx = get_Y(idx,None,Sseg)
            dawn = f_AM(civilY_AM[idx])
            dusk = f_PM(civilY_PM[idx])
            if objset_Y_idx > dawn > 0.0: n += 1    # count days when SET is above DAWN contour
            # trace SET or trace Dawn/Dusk?
            # trace_set = True if dusk > objset_Y_idx > dawn else False
            if dusk >= objset_Y_idx >= dawn: trace = 2                  # trace SET
            elif dawn <= objset_Y_idx: trace = 3     # trace DAWN
            #elif dusk > objset_Y_idx: trace = 4     # trace DUSK
            else: trace = -1        # trace neither SET, DAWN or DUSK

            if tracing is None:
                tracing = trace     # initialisation
                xfr = idx
            if trace == -1:
                xfr = idx+1         # as long as tracing nothing
            ##if trace != -1 and tfr == -1:
                ##tfr = idx           # tracing begins here
                ##if idx == seglen_DAWN[0]: tfr -= 1    # Mars 69°N 2000 NOT for 68°N 2000 !!!

            if config.PV_df: print("      idx {}, n {}, xfr {}, trace {}, tracing {}, {}".format(idx,n,xfr,trace,tracing,trace!=tracing or idx == Send))

            trace_dawn = True
            if trace != tracing or idx == Send:
                ndx = idx-1
                if idx == Send: ndx = idx; tracing = trace

                if tracing == 2 and ndx > xfr:      # end tracing SET (ignore a single coordinate)
                    if xfr + n - 1 != ndx:      # Venus 65°N 2010
                        path += 'B'+ str(xfr) + ','; trace_dawn = False # Mercury 64°N 2040
                    path += Stxt + ':' + str(xfr) + '-' + str(ndx) + ','    #>>>set>>>
                    if dawn == 0.0: path += 'B'+ str(ndx) + ','

                if tracing == 3 and ndx > xfr:      # end tracing DAWN (ignore a single coordinate)
                    # Jupiter 68°N 2025 SET seg 0
#                    print("add USE CASE #01"); sys.exit(0)
                    ##if tfr == xfr: path += 'B'+ str(xfr) + ','
                    path += 'dawn:' + str(xfr) + '-' + str(ndx) + ','       #>>>DAWN>>>
                    if trace == -1: path += 'B'+ str(ndx) + ','

                # if tracing == 4:    # end tracing DUSK
                    # path += 'dusk:' + str(xfr) + '-' + str(ndx) + ','      #>>>DUSK>>>

                # if tracing == -1:    # end tracing nothing
                    # xfr = idx-1 # reset when trace changes from -1 to 2 (Mars 70°N 2000)
                    # print("xfr {}".format(xfr))

            tracing = trace
        # ----------------------------------------- end of 'for'

        if trace_dawn and n > 0:   # trace DAWN backwards (Venus 65°N 2010 but NOT Mercury 64°N 2040)
            trace = tracing = -1
            xfr = -1

            for idx in range(Send, Sstart-1, -1):
                objrise_Y_idx, objset_Y_idx = get_Y(idx,None,Sseg)
                dawn = f_AM(civilY_AM[idx])
                # dusk = f_PM(civilY_PM[idx])

                if objset_Y_idx >= dawn >= 0.0:
                    trace = 3                   # trace DAWN
                    if xfr == -1: xfr = idx
                else: trace = -1
                    
                if config.PV_df: print("      idx {}, xfr {}, trace {}, tracing {}".format(idx,xfr,trace,tracing))

                if trace != tracing or idx == Sstart:
                    ndx = idx+1
                    if idx == Sstart: ndx = idx; tracing = trace

                    if tracing == 3 and ndx < xfr:  # end tracing DAWN
                        path += Dline(xfr, ndx, 'dawn')                     #<<<DAWN<<<
                        break

                tracing = trace
            # ----------------------------------------- end of 'for'

# .......................................................................................................

    elif SETep[Sseg] == ('00h', '00h'):     # single path (one area to fill)

        # If DAWN crosses the SET segment:
        #   starting point is where DAWN crosses SET
        #   scan DAWN forwards-or-backwards towards noDAWN Iif any)
        #   (if DAWN_to stops before crossing SET, follow 00h from there instead)
        #   ... then scan the SET segment range back to starting point

        # If DAWN does NOT intercept the SET segment:
        #   scan the SET segment forwards and 00h backwards

        if Sseg not in set_seg_done:
            set_seg_done.append(Sseg)       # set  segment processed

        fwd = None
        if SETcrossesDAWN[Sseg]:    # Mercury 63°N 2020
            if Sstart <= DAWN_to <= Send: fwd = True
            if Sstart <= DAWN_fr <= Send: fwd = False
            if fwd is None: Print("UNEXPECTED  CASE +1"); sys.exit(0)

            xfr = xto = fr00 = to00 = trace = -1
            if fwd:
                for idx in range(Sstart, Send+1):   # forwards
                    objrise_Y_idx, objset_Y_idx = get_Y(idx,None,Sseg)
                    dawn = f_AM(civilY_AM[idx])

                    # is SET between dawn-to-dusk?
                    dwn2dsk = True if 0.0 < dawn < objset_Y_idx else False

                    if dwn2dsk:
                        if trace == -1: trace = 3; xfr = idx        # trace DAWN from
                        if trace == 3:  xto = idx                   # trace DAWN to
                    elif idx == DAWN_to: trace = 0; to00 = idx      # follow 00h to

                    #print(idx,dwn2dsk,trace,xfr,xto,to00,DAWN_to)
                # ----------------------------------------- end of 'for'

                if xfr != -1:       # end tracing DAWN
                    # if xfr == DAWN_fr:
                        # path += 'B'+ str(xfr) + ','

                    if xfr != -1 and xto != -1:
                        path += Dline(xfr, xto, 'dawn')                         #>>>DAWN>>>

                    if xto == DAWN_to:
                        path += 'B'+ str(xto) + ','
                    elif to00 != -1:
                        path += 'B'+ str(to00) + ','

                if xfr == -1:       # no DAWN to trace
                    xfr = to00 if to00 != -1 else Sstart
                    path += 'B'+ str(xfr) + ','

                path += 'B'+ str(Send) + ','
                path += Sline(Send, xfr, Stxt)                                  #<<<set<<<

            else:
                for idx in range(Send, Sstart-1, -1):   # backwards
                    objrise_Y_idx, objset_Y_idx = get_Y(idx,None,Sseg)
                    dawn = f_AM(civilY_AM[idx])

                    # is SET between dawn-to-dusk?
                    dwn2dsk = True if 0.0 < dawn < objset_Y_idx else False

                    if dwn2dsk:
                        if trace == -1: trace = 3; xfr = idx        # trace DAWN from
                        if trace == 3:  xto = idx                   # trace DAWN to
                    elif idx == DAWN_fr: trace = 0; fr00 = idx      # follow 00h from

                    #print(idx,dwn2dsk,trace,xfr,xto,fr00,DAWN_fr)
                # ----------------------------------------- end of 'for'

                if xfr != -1:       # end tracing DAWN
                    #if xfr == DAWN_to:
                        # path += 'B'+ str(xfr) + ','

                    if xfr != -1 and xto != -1:
                        path += Dline(xfr, xto, 'dawn')                         #<<<DAWN<<<

                    if xto == DAWN_fr:
                        path += 'B'+ str(xto) + ','
                    elif fr00 != -1:
                        path += 'B'+ str(fr00) + ','

                if xfr == -1:       # no DAWN to trace
                    xfr = fr00 if fr00 != -1 else Send
                    path += 'B'+ str(xfr) + ','

                path += 'B'+ str(Sstart) + ','
                path += Sline(Sstart, xfr, Stxt)                                #>>>set>>>


        else:   # SET does not intercept the DAWN path, but is it before or after DAWN?

            fillSET = False
            if DAWN_fr != -1:
                if DAWN_to <= Sstart and DAWN_fr >= Send: fillSET = True

            if fillSET:
                path += 'B'+ str(Sstart) + ','
                path += Sline(Sstart, Send, Stxt)                               #>>>set>>>
                path += 'B'+ str(Send) + ','

# .......................................................................................................

    # This section is designed to handle multiple separate areas
    #       to be filled adjacent to the same SET segment

    elif SETep[Sseg] in [('DAH', '00h'), ('00h', 'DAH')]:     # single path (one area to fill)
        # Mercury 64°-72°N 2026, Venus 65°-72°N 2026, Jupiter 67°-70°NN 2026
#        print("add USE CASE #03"); sys.exit(0)

        # -------- scan SET segment range from DAH towards 24h --------
        #  (the path "cycles" back between the furthermost endpoints)
        if Sseg not in set_seg_done:
            set_seg_done.append(Sseg)       # set  segment processed

        if SETep[Sseg] == ('00h', 'DAH'):
            step = -1       # trace backwards away from DAH
            tr_fr = Send
            tr_to = Sstart
        else:               # trace forwards away from DAH
            step = 1
            tr_fr = Sstart
            tr_to = Send

        max_loops = 3
        idx_fr = tr_fr; idx_to = tr_to
        
        while idx_fr * step < idx_to * step:
            tr_fr = idx_fr; tr_to = idx_to
            max_loops -= 1
            if max_loops < 0: break

            prnt("      from {} = {} to {} = {}".format(tr_fr, DOY(tr_fr), tr_to, DOY(tr_to)))
            trace = tracing = -1    # not tracing anything
            tfr = -1        # tracing begins here
            n = 0           # count days during SET trace when above Dawn
            # note:  use path[:1] instead of path[0] to include ''

            for idx in range(tr_fr, tr_to+step, step):
                objrise_Y_idx, objset_Y_idx = get_Y(idx,None,Sseg)
                dawn = f_AM(civilY_AM[idx])
                dusk = f_PM(civilY_PM[idx])
                if objset_Y_idx > dawn > 0.0: n += 1    # count days when SET is above DAWN contour

                # trace SET or trace Dawn/Dusk?          Mars 69°N 2000
                if dusk > objset_Y_idx > dawn or idx in [DAWN_to, DAWN_fr]: trace = 2   # trace SET
                elif 0.0 < dawn < objset_Y_idx: trace = 3   # trace DAWN
                elif trace != 0: trace = -1             # trace neither SET, DAWN or DUSK

                if tracing == -1 and trace != -1:
                    tracing = trace     # initialisation
                    x0 = idx; xdawn = dawn
                if trace != -1 and tfr == -1: tfr = idx # tracing begins here

                z = bool(trace != tracing or idx == tr_to)
                traceTXT = "{}->{}".format(tracing,trace) if z else str(trace)
                if config.PV_df: print("  > idx {}: trace {}  {}".format(idx,traceTXT,z))

                if z:
                    ndx = idx if idx == tr_to else idx-step

                    if tracing == 2 and ndx != x0:      # end tracing SET (ignore a single coordinate)
                        if tfr == tr_fr and xdawn == 0.0:
                            path += 'B'+ str(x0) + ','
                        path += Stxt + ':' + str(x0) + '-' + str(ndx) + ','    #---set---
                        if dawn == 0.0 or ndx in [DAWN_fr, DAWN_to]:
                            path += 'B'+ str(ndx) + ','     # Mars 66°N 2010
                            if path[:1] != 'B': trace = 0   # continue if path didn't begin at 00h

                    if tracing == 3 and ndx != x0:      # end tracing DAWN  (ignore a single coordinate)
                        if tfr == x0: path += 'B'+ str(x0) + ','
                        path += 'dawn:' + str(x0) + '-' + str(ndx) + ','       #---DAWN---
                        if trace == -1: path += 'B'+ str(ndx) + ','; trace = 0

                    if tracing == -1:   # end tracing nothing
                        x0 = idx

                tracing = trace
    #            print("..>.idx {}: trace {}".format(idx,trace))
                if tfr != -1 and trace == -1:
                    tr_to = idx - step
                    break
            # ----------------------------------------- end of 'for'

            if path == '': return TEX   # scan reverse direction only if a forward path exists
            idx_fr = idx if idx != tr_to+step else tr_to+step   # where to restart another area fill search

            # following are just SET and DAWN back:
            #   Mercury 64°N 2001, Venus 65°N 2002, Venus 62°N 2004
            if n > 0:   # trace DAWN in the other direction (Mars 66°N 2010)
                        # n = 1 required for Mercury 64°N 2007
                trace = tracing
                xfr = -1
                plen = len(path)

                for idx in range(tr_to, tr_fr-step, -step):
                    objrise_Y_idx, objset_Y_idx = get_Y(idx,None,Sseg)
                    dawn = f_AM(civilY_AM[idx])
                    # dusk = f_PM(civilY_PM[idx])

                    if objset_Y_idx > dawn > 0.0:
                        trace = 3                   # trace DAWN
                        if xfr == -1: xfr = idx
                    elif trace != 0: trace = -1
                        
                    z = bool(trace != tracing or idx == tr_fr)
                    traceTXT = "{}->{}".format(tracing,trace) if z else str(trace)
                    if config.PV_df: print(" <  idx {}: trace {}  {}".format(idx,traceTXT,z))

                    if z:
                        ndx = idx if idx == tr_fr else idx+step

                        if tracing == 3:    # end tracing DAWN
                            if DAWN_to < ndx < DAWN_fr: ndx += step     # Venus 63°N 2012
                            path += Dline(xfr, ndx, 'dawn')                     #---DAWN---
                            if ndx == DAWN_to and path[:1] == 'B':
                                path += 'B'+ str(ndx) + ','
                            break

                        if tracing == 0:    # end tracing 00h
                            if trace == 3 and idx in [DAWN_fr, DAWN_to]:
                                path += 'B'+ str(xfr) + ','     # Jupiter 66°N 2002

                    tracing = trace
                # ----------------------------------------- end of 'for'

                # clear 'path' if no reverse DAWN trace and initial trace is only a SET trace
                # mercury 65°N 2027 set seg 1 clears 's1:134-133,'
                if len(path) == plen and path.find('dawn:') == -1 and path.find('B') == -1:
                    path = ''

# .......................................................................................................

            path = path[:-1]
            path = trimpath(path)   # avoid identical first and last fixed position elements
            path = fix0path(path)   # filter out paths that have no "width"
            p = path
            tp = []
            txt = 'path:'
            n = p.find(',', 70)
            while n != -1:
                prnt("      {}       {}".format(txt,p[:n+1]))
                tp.append("{} {}".format(txt,p[:n+1]))
                txt = '     '
                p = p[n+1:]
                n = p.find(',', 70)
            prnt("      {}       {}".format(txt,p))
            tp.append("{} {}".format(txt,p))

            TEX += fillpath(path, 'Gold', '0.85', tp)
            path = ''       # new path to fill
        # ----------------------------------------- end of 'while'

        return TEX

# .......................................................................................................

    else: done = False

    
    if done:
        path = path[:-1]
        path = trimpath(path)   # avoid identical first and last fixed position elements
        path = fix0path(path)   # filter out paths that have no "width"
        p = path
        tp = []
        txt = 'path:'
        n = p.find(',', 70)
        while n != -1:
            prnt("      {}       {}".format(txt,p[:n+1]))
            tp.append("{} {}".format(txt,p[:n+1]))
            txt = '     '
            p = p[n+1:]
            n = p.find(',', 70)
        prnt("      {}       {}".format(txt,p))
        tp.append("{} {}".format(txt,p))

        TEX += fillpath(path, 'Gold', '0.85', tp)

        return TEX

# .......................................................................................................

    # This section is principally designed to handle multiple separate
    #     areas to be filled adjacent to the same SET segment

    if SETep[Sseg] in [('SoY', '00h'), ('SoY', 'DAH'), ('00h', '00h'), ('DAH', 'DAH'), ('DAH', 'EoY')]:
        # Mercury 65°N 2015, Jupiter 69°N 2000, Saturn 72°N 2010

        # scan SET segment range forwards
        if Sseg not in set_seg_done:
            set_seg_done.append(Sseg)       # set  segment processed

        # there can be more than one area to fill on the SET segment...
        idx_fr = Sstart
        max_loops = 3
        xFR = [-1] * 10     # list of FROM dates per trace type
        PV_df = '>>> '

        while idx_fr < Send:
            max_loops -=1
            if max_loops < 0: break

            trace = tracing = -1        # not tracing anything yet
            noRetPath = False           # cancel return Path scan

            # forward direction  (idx_fr -> Send)
            for idx in range(idx_fr, Send+1):
                objrise_Y_idx, objset_Y_idx = get_Y(idx,None,Sseg)
                dawn = f_AM(civilY_AM[idx])
                dusk = f_PM(civilY_PM[idx])
                # trace SET or trace Dawn/Dusk?
                trace_set = True if dusk >= objset_Y_idx >= dawn else False
                if trace_set: trace = 2                     # trace SET
                # elif dawn >= objset_Y_idx: trace = 3      # trace DAWN
                elif dusk <= objset_Y_idx: trace = 4        # trace DUSK  Jupiter 68°N 2025
                elif not (SETep[Sseg][0] == '00h' and trace == 1 and idx == DAWN_fr and not trace_set):
                    # cosmetic - extend rise by 1 day (Venus 63°N 2025)
                    trace = -1        # trace neither SET, DAWN or DUSK

                if tracing == -1:
                    tracing = trace     # initialisation for area to trace
                    fill_fr = idx       # current area to fill begins here
                    if trace != -1: xFR[trace] = idx    # area to trace begins here

                if config.PV_df:
                    PV_df += "{} {}, ".format(idx,trace)
                    if len(PV_df) > 80: print(PV_df); PV_df = '>>> '

                if trace != tracing or idx == Send:
                    if trace != -1 and not (trace == tracing and idx == Send):
                        xFR[trace] = idx
                    ndx = idx if idx == Send else idx-1
                    if len(PV_df) > 4:
                        prnt(PV_df[:-2])
                        PV_df = '>>> '
                    p = ''      # path element

                    if tracing == 2:    # end tracing SET
                        if SETep[Sseg][0] == '00h' and xFR[2] == Sstart:
                            p += 'B'+ str(xFR[2]) + ','
                        p += Sline(xFR[2], ndx, Stxt)                           #>>>set>>>
                        if SETep[Sseg][1] == '00h' and ndx == Send:
                            p += 'B'+ str(ndx) + ','; trace = 0
                            # trace = -1; fill_fr = ndx+1 # cancel reverse scan !! NOT for Jupiter 62°N 2026
                        xFR[2] = -1

                    if tracing == 3:    # end tracing DAWN
                        p += Dline(xFR[3], ndx, 'dawn')                         #>>>DAWN>>>
                        xFR[3] = -1

                    if tracing == 4:    # end tracing DUSK
                        p += Dline(xFR[4], ndx, 'dusk')                         #>>>DUSK>>>
                        xFR[4] = -1

                    if config.PV_df: print("  {} --> {}: ndx {}, fill_fr {}:  {}".format(tracing,trace,ndx,fill_fr,p))
                    path += p
                    
                    if tracing == 2 and trace == -1:
                        idx_to = jdx = ndx; tracing = trace
                        break     # Jupiter 62°N 2026, Saturn 70°N 2030

                tracing = trace
                jdx = idx
            # ----------------------------------------- end of 'for'

            tracing = trace     # in case 'break' out of 'for' above
            objrise_Y_idx, objset_Y_idx = get_Y(ndx,None,Sseg)
            dawn = f_PM(civilY_AM[ndx])
            case1 = False
            if 0.0 < dawn <= objset_Y_idx:    # DAWN cannot be noDAWN (0.0)
                tracing = trace = 3     # trace DAWN
                xFR[trace] = ndx
            elif SETep[Sseg][0] == '00h' and ndx == DAWN_fr and dawn > objset_Y_idx:
                tracing = trace = 0     # trace 00h
                xFR[trace] = ndx
                case1 = True
            elif trace == 0: pass       # Jupiter 62°-66°N 2026 Sseg 0 (leave xFR[trace] alone)
            else:
                tracing = trace = 0     # trace 00h
                xFR[trace] = ndx
            if idx == Send: idx_to = Send
            idx_fr = idx_to + 1     # where to restart another area fill search
            if path == '': noRetPath = True  # scan reverse direction only if an initial path exists

            if noRetPath or (SETep[Sseg] == ('00h', '00h') and idx_to ==Send):
                fill_fr = idx_to+1  # no return path

            # reverse direction  (idx_to -> fill_fr)
            PV_db = '<<< '
            for idx in range(idx_to, fill_fr-1, -1):
                objrise_Y_idx, objset_Y_idx = get_Y(idx,None,Sseg)
                dawn = f_AM(civilY_AM[idx])
                dusk = f_PM(civilY_PM[idx])

                # trace SET or trace Dawn/Dusk?
                if case1: trace = 0
                elif  dawn >= objset_Y_idx: trace = -1
                else: trace = 3 if dawn > 0.0 else 0

                if config.PV_db:
                    PV_db += "{} {}, ".format(idx,trace)
                    if len(PV_db) > 80: print(PV_db); PV_db = '<<< '

                if trace != tracing or idx == fill_fr:
                    if trace != -1 and not (trace == tracing and idx == fill_fr):
                        xFR[trace] = idx
                    ndx = idx if idx == fill_fr else idx+1
                    if len(PV_db) > 4:
                        prnt(PV_db[:-2])
                        PV_db = '<<< '
                    p = ''      # path element

                    if tracing == 0:    # end tracing 00h
                        if xFR[0] != -1: p += 'B'+ str(xFR[0]) + ','
                        if not case1 and idx != xFR[0]: p += 'B'+ str(idx) + ','    # Jupiter 62°-66°N 2026
                        xFR[0] = -1
                        jdx = idx

                    if tracing == 3:    # end tracing DAWN
                        p += Dline(xFR[3], ndx, 'dawn')                         #<<<DAWN<<<
                        if ndx == DAWN_fr:
                            p += 'B'+ str(ndx) + ','
                            trace = 0; xFR[0] = -1   # DO NOT DUPLICATE the 'B' path element
                        xFR[3] = -1

                    if config.PV_db: print("  {} --> {}: idx_to {}, ndx {}, fill_fr {}:  {}".format(tracing,trace,idx_to,ndx,fill_fr,p))
                    path += p

                tracing = trace
            # ----------------------------------------- end of 'for'

# .......................................................................................................

            path = path[:-1]
            path = trimpath(path)   # avoid identical first and last fixed position elements
            path = fix0path(path)   # filter out paths that have no "width"
            p = path
            tp = []
            txt = 'path:'
            n = p.find(',', 70)
            while n != -1:
                prnt("      {}       {}".format(txt,p[:n+1]))
                tp.append("{} {}".format(txt,p[:n+1]))
                txt = '     '
                p = p[n+1:]
                n = p.find(',', 70)
            prnt("      {}       {}".format(txt,p))
            tp.append("{} {}".format(txt,p))

            TEX += fillpath(path, 'Gold', '0.85', tp)
            path = ''       # new path to fill
        # ----------------------------------------- end of 'while'

        return TEX

# .......................................................................................................

    return ''

# .........................................................................................
# ........................  fill RISE segments gold above horizon  ........................
# .........................................................................................

# ---------- trace codes ----------
#     -1  trace nothing / stop tracing in current direction
#      0  follow 00h
#      1  trace RISE segment
#      2  trace  SET segment
#      3  trace DAWN
#      4  trace DUSK
#      9  follow 24h
# ---------------------------------

def fill_RISE_above_horizon(obj, Rseg):

    # process RISE segment

    TEX = ''
    path = ''       # new path to fill
    Rtxt   = 'r' + str(Rseg)
    Rspan  = rise_days[Rseg]    # segment span in days  (not length)
    Rstart = rise_starts[Rseg]
    Rend   = rise_ends[Rseg]
    done = True                 # True for a single pass (not forward & backward trace)

    if Rspan == 0: return TEX   # if segment spans 0 days

    DAWN_fr, DAWN_to, DUSK_fr, DUSK_to, noDAWN_fr, noDAWN_to, noDUSK_fr, noDUSK_to = getDAWN_DUSK()

    # single path (one area to fill during noDUSK)
    # !!! this cannot handle multiple paths (Saturn 67°N 2032) !!!
#    if RISEep[Rseg] in [('24h', 'DAH')] or \
    if (RISEep[Rseg] in [('DAH', 'DAH'), ('24h', 'DBH')] \
    and noDUSK_fr <= Rstart <= Rend <= noDUSK_to):    
        # Mercury 72°N 2015, Jupiter 68°N 2008

        # scan RISE segment range forwards
        if Rseg not in rise_seg_done:
            rise_seg_done.append(Rseg)       # rise segment processed

        tracing = -1    # not tracing anything
        tfr = -1        # tracing begins here

        for idx in range(Rstart, Rend+1):
            # objset_Y_idx  = getY(objset_Y[idx],1)
            # objrise_Y_idx = getY(objrise_Y[idx],1)
            objrise_Y_idx, objset_Y_idx = get_Y(idx,Rseg,None)
            dawn = f_AM(civilY_AM[idx])
            dusk = f_PM(civilY_PM[idx])
            # trace RISE or trace Dawn/Dusk?
            if dusk >= objrise_Y_idx >= dawn: trace = 1     # trace RISE
            #elif dawn > objrise_Y_idx: trace = 3            # trace DAWN
            #elif dusk < objrise_Y_idx: trace = 4            # trace DUSK
            else: trace = -1        # trace neither RISE, DAWN or DUSK
            if tracing == -1:
                tracing = trace     # initialisation
                xto = idx
            if trace != -1 and tfr == -1: tfr = idx # tracing begins here

            if config.PV_db: print("      idx {}, trace {}, {}".format(idx,trace,trace!=tracing or idx == Rend))

            if trace != tracing or idx == Rend:
                ndx = idx if idx == Rend else idx-1

                if tracing == 1 and ndx > xto:    # end tracing RISE (ignore a single coordinate)
                    if tfr == xto: path += 'T'+ str(xto) + ','
                    # if RISEep[Rseg][0] == '24h': path += 'T'+ str(Rstart) + ','
                    path += Rtxt + ':' + str(xto) + '-' + str(ndx) + ','    #>>>rise>>>
                    if ndx == Rend: path += 'T'+ str(ndx) + ','

                # if tracing == 3:    # end tracing DAWN
                    # path += 'dawn:' + str(xto) + '-' + str(ndx) + ','      #>>>DAWN>>>

                if tracing == 4 and ndx > xto:    # end tracing DUSK (ignore a single coordinate)
                    if tfr == xto: path += 'T'+ str(xto) + ','
                    path += 'dusk:' + str(xto) + '-' + str(ndx) + ','       #>>>DUSK>>>
                    if trace == -1: path += 'T'+ str(ndx) + ','

                if tracing == -1:    # end tracing nothing
                    xto = idx-1 # reset when trace changes from -1 to 1

            tracing = trace
        # ----------------------------------------- end of 'for'

        # if RISEep[Rseg][1] == 'DAH':
            # path += 'T'+ str(Rend) + ','

# .......................................................................................................

    elif RISEep[Rseg] == ('24h', '24h'):     # single path (one area to fill)

        # If DUSK crosses the RISE segment:
        #   starting point is where DUSK crosses RISE
        #   scan DUSK forwards-or-backwards towards noDUSK (if any)
        #   (if DUSK stops before crossing RISE, follow 24h from there instead)
        #   ... then scan the RISE segment range back

        # If DUSK does NOT intercept the RISE segment:
        #   scan the RISE segment forwards and 24h backwards

        if Rseg not in rise_seg_done:
            rise_seg_done.append(Rseg)       # rise  segment processed

        fwd = None
        if RISEcrossesDUSK[Rseg]:
            if Rstart <= DUSK_to <= Rend: fwd = True
            if Rstart <= DUSK_fr <= Rend: fwd = False
            if fwd is None: Print("UNEXPECTED  CASE +2"); sys.exit(0)

            #print("!!!!!!!", Rstart, Rend, fwd)
            xfr = xto = fr24 = to24 = trace = -1
            if fwd:
                for idx in range(Rstart, Rend+1):   # forwards
                    objrise_Y_idx, objset_Y_idx = get_Y(idx,Rseg,None)
                    dusk = f_PM(civilY_PM[idx])

                    # is RISE between dawn-to-dusk?
                    dwn2dsk = True if 24.0 > dusk > objrise_Y_idx else False

                    if dwn2dsk:
                        if trace == -1: trace = 4; xfr = idx        # trace DUSK from
                        if trace == 4:  xto = idx                   # trace DUSK to
                    elif idx == DUSK_to: trace = 9; to24 = idx      # follow 24h to

                    #print(idx,dwn2dsk,trace,xfr,xto,to24,DUSK_to)
                # ----------------------------------------- end of 'for'

                if xfr != -1:       # end tracing DUSK
                    # if xfr == DUSK_fr:
                        # path += 'T'+ str(xfr) + ','

                    if xfr != -1 and xto != -1:
                        path += Dline(xfr, xto, 'dusk')                         #>>>DUSK>>>

                    if xto == DUSK_to:
                        path += 'T'+ str(xto) + ','
                    elif to24 != -1:
                        path += 'T'+ str(to24) + ','

                if xfr == -1:       # no DUSK to trace
                    xfr = to24 if to24 != -1 else Rstart
                    path += 'T'+ str(xfr) + ','

                path += 'T'+ str(Rend) + ','
                path += Rline(Rend, xfr, Rtxt)                                  #<<<rise<<<

            else:
                for idx in range(Rend, Rstart-1, -1):   # backwards
                    objrise_Y_idx, objset_Y_idx = get_Y(idx,Rseg,None)
                    dusk = f_PM(civilY_PM[idx])

                    # is RISE between dawn-to-dusk?
                    dwn2dsk = True if 24.0 > dusk > objrise_Y_idx else False

                    if dwn2dsk:
                        if trace == -1: trace = 4; xfr = idx        # trace DUSK from
                        if trace == 4:  xto = idx                   # trace DUSK to
                    elif idx == DUSK_fr: trace = 9; fr24 = idx      # follow 24h from

                    #print(idx,dwn2dsk,trace,xfr,xto,fr24,DUSK_fr)
                # ----------------------------------------- end of 'for'

                if xfr != -1:     # end tracing DUSK
                    if xfr != -1 and xto != -1:
                        path += Dline(xfr, xto, 'dusk')                         #<<<DUSK<<<

                    if xto == DUSK_fr:
                        path += 'T'+ str(xto) + ','
                    elif fr24 != -1:
                        path += 'T'+ str(fr24) + ','

                if xfr == -1:     # no DUSK to trace
                    xfr = fr24 if fr24 != -1 else Rend
                    path += 'T'+ str(xfr) + ','

                path += 'T'+ str(Rstart) + ','
                path += Rline(Rstart, xfr, Rtxt)                                #>>>rise>>>


        else:   # RISE does not intercept the DUSK path, but is it before or after DUSK?

            fillRISE = False
            if DUSK_fr != -1:
                if DUSK_to <= Rstart and DUSK_fr >= Rend: fillRISE = True

            if fillRISE:
                path += 'T'+ str(Rstart) + ','
                path += Rline(Rstart, Rend, Rtxt)                               #>>>rise>>>
                path += 'T'+ str(Rend) + ','

# .......................................................................................................

    # This section is designed to handle multiple separate areas
    #       to be filled adjacent to the same RISE segment

    elif RISEep[Rseg] in [('DAH', '24h'), ('24h', 'DAH')]:
        # Venus 67°-72°N 2030, Mars 67°-72°N 2030, Mars 66°N 2013
#        print("add USE CASE #02"); sys.exit(0)

        # -------- scan RISE segment range from DAH towards 24h --------
        #   (the path "cycles" back between the furthermost endpoints)
        if Rseg not in rise_seg_done:
            rise_seg_done.append(Rseg)      # rise segment processed

        if RISEep[Rseg] == ('24h', 'DAH'):
            step = -1       # trace backwards away from DAH
            tr_fr = Rend
            tr_to = Rstart
        else:               # trace forwards away from DAH
            step = 1
            tr_fr = Rstart
            tr_to = Rend

        max_loops = 3
        idx_fr = tr_fr; idx_to = tr_to
        
        while idx_fr * step < idx_to * step:
            tr_fr = idx_fr; tr_to = idx_to
            max_loops -= 1
            if max_loops < 0: break

            prnt("      from {} = {} to {} = {}".format(tr_fr, DOY(tr_fr), tr_to, DOY(tr_to)))
            trace = tracing = -1    # not tracing anything
            tfr = -1        # tracing begins here
            n = 0           # count days during RISE trace when below Dusk
            # note:  use path[:1] instead of path[0] to include ''

            for idx in range(tr_fr, tr_to+step, step):
                objrise_Y_idx, objset_Y_idx = get_Y(idx,Rseg,None)
                dawn = f_AM(civilY_AM[idx])
                dusk = f_PM(civilY_PM[idx])
                if objrise_Y_idx < dusk < 24.0: n += 1      # count days when RISE is below DUSK contour

                # trace RISE or trace Dusk?
                if dusk > objrise_Y_idx > dawn or idx in [DUSK_to, DUSK_fr]: trace = 1  # trace RISE
                elif 24.0 > dusk > objrise_Y_idx: trace = 4     # trace DUSK
                elif trace != 9: trace = -1             # trace neither RISE, DAWN or DUSK

                if tracing == -1 and trace != -1:
                    tracing = trace     # initialisation
                    x0 = idx; xdusk = dusk
                if trace != -1 and tfr == -1: tfr = idx # tracing begins here

                z = bool(trace != tracing or idx == tr_to)
                traceTXT = "{}->{}".format(tracing,trace) if z else str(trace)
                if config.PV_db: print("  > idx {}: trace {}  {}".format(idx,traceTXT,z))

                if z:
                    # check for noDUSK (Venus 67°N 2030)
                    ndx = idx if idx == tr_to and idx-step != DUSK_fr else idx-step

                    if tracing == 1 and ndx != x0:      # end tracing RISE (ignore a single coordinate)
                        if tfr == x0 and xdusk == 24.0:
                            path += 'T'+ str(x0) + ','
                        path += Rtxt + ':' + str(x0) + '-' + str(ndx) + ','    #---rise---
                        if dusk == 24.0 or ndx in [DUSK_fr, DUSK_to]:
                            path += 'T'+ str(ndx) + ','
                            if path[:1] != 'T': trace = 9    # continue if path didn't begin at 24h

                    if tracing == 4  and ndx != x0:     # end tracing DUSK (ignore a single coordinate)
                        if tfr == x0: path += 'T'+ str(x0) + ','
                        path += 'dusk:' + str(x0) + '-' + str(ndx) + ','       #---DUSK---
                        if trace == -1: path += 'T'+ str(ndx) + ','; trace = 9

                    if tracing == -1:   # end tracing nothing
                        x0 = idx       # Venus 67°N 2006

                tracing = trace
    #            print("..>.idx {}: trace {}".format(idx,trace))
                if tfr != -1 and trace == -1:
                    tr_to = idx - step
                    break
            # ----------------------------------------- end of 'for'

            idx_fr = idx if idx != tr_to+step else tr_to+step   # where to restart another area fill search

            # following cases are just RISE and DUSK back:
            #   Venus 68°N 2001, Venus 68°N 2006

            # scan reverse direction only if an initial path exists
            if path != '' and (n > 0 and not (n == 1 and path[:1] == 'T')):  # trace DUSK in the other direction
                # NOT Venus 67°N 2006 (n = 1)
                trace = tracing
                xfr = -1

                for idx in range(tr_to, tr_fr-step, -step):
                    objrise_Y_idx, objset_Y_idx = get_Y(idx,Rseg,None)
                    # dawn = f_AM(civilY_AM[idx])
                    dusk = f_PM(civilY_PM[idx])

                    if objrise_Y_idx < dusk < 24.0:
                        trace = 4                   # trace DUSK
                        if xfr == -1: xfr = idx
                    elif trace != 9: trace = -1
                        
                    z = bool(trace != tracing or idx == tr_fr)
                    traceTXT = "{}->{}".format(tracing,trace) if z else str(trace)
                    if config.PV_db: print(" <  idx {}: trace {}  {}".format(idx,traceTXT,z))

                    if z:
                        ndx = idx if idx == tr_fr else idx+step

                        if tracing == 4:    # end tracing DUSK
                            if DUSK_to < ndx < DUSK_fr: ndx += step
                            path += Dline(xfr, ndx, 'dusk')                     #---DUSK---
                            if ndx == DUSK_fr and path[:1] == 'T':  # NOT Venus 68°N 2006
                                path += 'T'+ str(ndx) + ','
                            break

                        if tracing == 9:    # end tracing 24h
                            if trace == 4 and idx in [DUSK_fr, DUSK_to]:
                                path += 'T'+ str(xfr) + ','

                    tracing = trace
                # ----------------------------------------- end of 'for'

# .......................................................................................................

            path = path[:-1]
            path = trimpath(path)   # avoid identical first and last fixed position elements
            path = fix0path(path)   # filter out paths that have no "width"
            p = path
            tp = []
            txt = 'path:'
            n = p.find(',', 70)
            while n != -1:
                prnt("      {}       {}".format(txt,p[:n+1]))
                tp.append("{} {}".format(txt,p[:n+1]))
                txt = '     '
                p = p[n+1:]
                n = p.find(',', 70)
            prnt("      {}       {}".format(txt,p))
            tp.append("{} {}".format(txt,p))

            TEX += fillpath(path, 'Gold', '0.85', tp)
            path = ''       # new path to fill
        # ----------------------------------------- end of 'while'

        return TEX

# .......................................................................................................

    else: done = False


    if done:
        path = path[:-1]
        path = trimpath(path)   # avoid identical first and last fixed position elements
        path = fix0path(path)   # filter out paths that have no "width"
        p = path
        tp = []
        txt = 'path:'
        n = p.find(',', 70)
        while n != -1:
            prnt("      {}       {}".format(txt,p[:n+1]))
            tp.append("{} {}".format(txt,p[:n+1]))
            txt = '     '
            p = p[n+1:]
            n = p.find(',', 70)
        prnt("      {}       {}".format(txt,p))
        tp.append("{} {}".format(txt,p))

        TEX += fillpath(path, 'Gold', '0.85', tp)

        return TEX

# .......................................................................................................

    # This section is principally designed to handle multiple separate
    #     areas to be filled adjacent to the same RISE segment

    if RISEep[Rseg] in [('SoY', 'DAH'), ('24h', '24h'), ('24h', 'EoY'), ('DAH', 'DAH'), \
    ('DAH', 'EoY'), ('24h', 'DAH'), ('DAH', '24h')]:
        # Mercury 69°N 2026, Mercury 68°N 2000, Jupiter 69°N 2000, , , Saturn 67°N 2032

        # scan RISE segment range forwards
        if Rseg not in rise_seg_done:
            rise_seg_done.append(Rseg)          # rise segment processed

        # there can be more than one area to fill on the RISE segment...
        idx_fr = Rstart
        max_loops = 3
        xFR = [-1] * 10     # list of FROM dates per trace type
        PV_df = '>>> '

        while idx_fr < Rend:
            max_loops -= 1
            if max_loops < 0: break

            trace = tracing = -1        # not tracing anything yet
            noRetPath = False           # cancel return Path scan

            # forward direction  (idx_fr -> Rend)
            for idx in range(idx_fr, Rend+1):
                objrise_Y_idx, objset_Y_idx = get_Y(idx,Rseg,None)
                dawn = f_AM(civilY_AM[idx])
                dusk = f_PM(civilY_PM[idx])
                # trace RISE or trace Dawn/Dusk?
                trace_rise = True if dusk >= objrise_Y_idx >= dawn else False
                if trace_rise: trace = 1                    # trace RISE
                elif dawn >= objrise_Y_idx: trace = 3       # trace DAWN  Saturn 72°N 2000
                # elif dusk <= objrise_Y_idx: trace = 4       # trace DUSK
                else:
                # elif not (RISEep[Rseg][0] == '24h' and trace == 1 and idx == DUSK_fr and not trace_rise):
                    # cosmetic - extend rise by 1 day (not Venus 63°N 2025)
                    #print("            ",idx,DUSK_fr,trace,trace_rise,bool(idx != DUSK_fr))
                    trace = -1        # trace neither RISE, DAWN or DUSK

                if tracing == -1:
                    tracing = trace     # initialisation for area to trace
                    fill_fr = idx       # current area to fill begins here
                    if trace != -1: xFR[trace] = idx    # area to trace begins here

                if config.PV_df:
                    PV_df += "{} {}, ".format(idx,trace)
                    if len(PV_df) > 80: print(PV_df); PV_df = '>>> '

                if trace != tracing or idx == Rend:
                    if trace != -1 and not (trace == tracing and idx == Rend):
                        xFR[trace] = idx
                    ndx = idx if idx == Rend else idx-1
                    if len(PV_df) > 4:
                        prnt(PV_df[:-2])
                        PV_df = '>>> '
                    p = ''      # path element

                    if tracing == 1:    # end tracing RISE
                        # cosmetic - extend rise by 1 day (Venus 67°N 2030)
                        if ndx == noDUSK_to and ndx < Rend:
                            ndx += 1; noRetPath = True       # cancel reverse scan
                        # handle ('24h', 'DAH') & ('DAH', '24h') Mercury 69°N 2000
##                        if (RISEep[Rseg][0] == '24h' or RISEep[Rseg][1] == '24h') and xFR[1] == Rstart:
##                            p += 'T'+ str(xFR[1]) + ','
                        if noRetPath:
                            if isRISEhighestSEG(Rseg,range(xFR[1],ndx+1)):  # connect to top border?
                                p += 'T'+ str(xFR[1]) + ','
                                p += Rline(xFR[1], ndx, Rtxt)                   #>>>rise>>>
                                p += 'T'+ str(ndx) + ','
                        else:   # Jupiter 60°S-60°N 2000
                            if DUSK_to <= xFR[1] <= DUSK_fr \
                            and beginRISEat24h(Rseg, xFR[1]):    # Jupiter 62°-68°N 2000
                                p += 'T'+ str(xFR[1]) + ','
                            p += Rline(xFR[1], ndx, Rtxt)                       #>>>rise>>>
##                            if noRetPath or (RISEep[Rseg][1] == '24h' and ndx == Rend):
##                                p += 'T'+ str(ndx) + ','
##                                noRetPath = True            # cancel reverse scan
##                                trace = -1; fill_fr = ndx+1 # cancel reverse scan
                        xFR[1] = -1

                    if tracing == 3:    # end tracing DAWN
                        p += Dline(xFR[3], ndx, 'dawn')                         #>>>DAWN>>>
                        xFR[3] = -1

                    if tracing == 4:    # end tracing DUSK
                        p += Dline(xFR[4], ndx, 'dusk')                         #>>>DUSK>>>
                        xFR[4] = -1

                    if config.PV_df: print("  {} --> {}: ndx {}:  {}".format(tracing,trace,ndx,p))
                    path += p

                    if tracing == 1 and trace == -1:
                        idx_to = jdx = ndx; tracing = trace
                        break   # Saturn 72°N 2000, Saturn 64°N 2030

                tracing = trace
                jdx = idx
            # ----------------------------------------- end of 'for'

            tracing = trace     # in case 'break' out of 'for' above
            objrise_Y_idx, objset_Y_idx = get_Y(ndx,Rseg,None)
            dusk = f_PM(civilY_PM[ndx])
            case1 = False
            # print(idx,ndx)
            if 24.0 > dusk >= objrise_Y_idx:    # DUSK cannot be noDUSK (24.0)
                tracing = trace = 4     # trace DUSK (Saturn 64°N 2030)
                xFR[trace] = ndx
            elif RISEep[Rseg][0] == '24h' and ndx == DUSK_fr and dusk < objrise_Y_idx:
                tracing = trace = 9     # trace 24h (Venus 63°N 2025)
                xFR[trace] = ndx
                case1 = True
            else:
                tracing = trace = 9     # trace 24h
                xFR[trace] = ndx
            if idx == Rend: idx_to = Rend
            idx_fr = idx_to + 1     # where to restart another area fill search
            if path == '': noRetPath = True  # scan reverse direction only if an initial path exists

            if noRetPath or (RISEep[Rseg] == ('24h', '24h') and idx_to == Rend):
                fill_fr = idx_to+1  # no return path

            # reverse direction  (idx_to -> fill_fr)
            PV_db = '<<< '
            for idx in range(idx_to, fill_fr-1, -1):
                objrise_Y_idx, objset_Y_idx = get_Y(idx,Rseg,None)
                dawn = f_AM(civilY_AM[idx])
                dusk = f_PM(civilY_PM[idx])

                # trace RISE or trace Dawn/Dusk?
                if case1: trace = 9
                elif  dusk <= objrise_Y_idx: trace = -1
                else: trace = 4 if dusk < 24.0 else 9

                if config.PV_db:
                    PV_db += "{} {}, ".format(idx,trace)
                    if len(PV_db) > 80: print(PV_db); PV_db = '<<< '

                if trace != tracing or idx == fill_fr:
                    if trace != -1 and not (trace == tracing and idx == fill_fr):
                        xFR[trace] = idx
                    ndx = idx if idx == fill_fr else idx+1
                    if len(PV_db) > 4:
                        prnt(PV_db[:-2])
                        PV_db = '<<< '
                    p = ''      # path element

                    if tracing == 9:    # end tracing 24h
                        if xFR[9] != -1: p += 'T'+ str(xFR[9]) + ','
                        if not case1 and ndx != xFR[9]: p += 'T'+ str(ndx) + ','
                        xFR[9] = -1
                        jdx = idx

                    if tracing == 4:    # end tracing DUSK
                        p += Dline(xFR[4], ndx, 'dusk')                         #<<<DUSK<<<
                        if ndx == DUSK_fr:
                            p += 'T'+ str(ndx) + ','
                            if trace == 9: xFR[9] = -1   # DO NOT DUPLICATE the 'T' path element
                        xFR[4] = -1

                    if config.PV_db: print("  {} --> {}: idx_to {}, ndx {}, fill_fr {}:  {}".format(tracing,trace,idx_to,ndx,fill_fr,p))
                    path += p

                tracing = trace
            # ----------------------------------------- end of 'for'

            if xFR[9] != -1 and fill_fr == Rstart:    # Jupiter 71°N 2026   ????????????????????????????
                path += 'T'+ str(fill_fr) + ','

# .......................................................................................................

            path = path[:-1]
            path = trimpath(path)   # avoid identical first and last fixed position elements
            path = fix0path(path)   # filter out paths that have no "width"
            p = path
            tp = []
            txt = 'path:'
            n = p.find(',', 70)
            while n != -1:
                prnt("      {}       {}".format(txt,p[:n+1]))
                tp.append("{} {}".format(txt,p[:n+1]))
                txt = '     '
                p = p[n+1:]
                n = p.find(',', 70)
            prnt("      {}       {}".format(txt,p))
            tp.append("{} {}".format(txt,p))

            TEX += fillpath(path, 'Gold', '0.85', tp)
            path = ''       # new path to fill
        # ----------------------------------------- end of 'while'

        return TEX

# .......................................................................................................

    return ''


# def prnt_v0(txt):
    # # print text only if '-v' (verbose) is specified in the command line
    # # note that it only accepts ONE ARGUMENT
    # if verbose: print(txt)
    # return

def prnt(*args, **kwargs):
    # print text only if '-v' (verbose) is specified in the command line
    if not verbose: return
    print(*args, **kwargs)
    return

def beginRISEat24h(Rseg, i):
    # check if trace RISE start begins at 24h (check beforehand for noDUSK !!)
    # print("   ",i,"  ",RS_events[i])
    isrise, seg_num, seg_off = RS_events[i]
    if len(isrise) == 0: return False
    if isrise[-1] and seg_num[-1] == Rseg and seg_off[-1] == 0:
        return True         # RISE is last segment and starts at 'i'
    if len(isrise) > 1:     # is there a segment above the RISE?
        if isrise[-2] and seg_num[-2] == Rseg and seg_off[-2] == 0:
            # yes - is it a SET singularity?
            if not isrise[-1] and set_days[seg_num[-1]] == 0 and set_off[-1] == 0:
                return True # yes
    return False

def beginSETat00h(Sseg, i):
    # check if trace SET start begins at 00h (check beforehand for noDAWN !!)
    # print("   ",i,"  ",RS_events[i])
    isrise, seg_num, seg_off = RS_events[i]
    if len(isrise) == 0: return False
    if not isrise[0] and seg_num[0] == Sseg and seg_off[0] == 0:
        return True         # SET is first segment and starts at 'i'
    if len(isrise) > 1:     # is there a segment below the SET?
        if not isrise[1] and seg_num[1] == Sseg and seg_off[1] == 0:
            # yes - is it a RISE singularity?
            if isrise[0] and rise_days[seg_num[0]] == 0 and set_off[0] == 0:
                return True # yes
    return False

def isRISEhighestSEG(Rseg, rng):
    # check that there is no segment above Rseg during date offset range
    for i in rng:
        isrise, seg_num, seg_off = RS_events[i]
        if len(isrise) == 0: continue
        if not (isrise[-1] and seg_num[-1] == Rseg): return False
    return True

def isSETlowestSEG(Sseg, rng):
    # check that there is no segment below Sseg during date offset range
    for i in rng:
        isrise, seg_num, seg_off = RS_events[i]
        if len(isrise) == 0: continue
        if not (not isrise[0] and seg_num[0] == Sseg): return False
    return True

def bval(bvalue):
    if bool(bvalue): return '\u2713'    # tick mark
    return 'x'

def currently_noDAWN(idx):
    # return True if there is 'noDAWN' on this date
    noDAWN_fr = noDAWN_to = -1   # make it fail if len(seglen_DAWN) == 1
    if len(seglen_DAWN) == 3:
        noDAWN_fr = seglen_DAWN[0]
        noDAWN_to = seglen_DAWN[0] - seglen_DAWN[1] - 1
    if not noDAWN_fr <= idx <= noDAWN_to: return False
    return True

def currently_noDUSK(idx):
    # return True if there is 'noDUSK' on this date
    noDUSK_fr = noDUSK_to = -1   # make it fail if len(seglen_DUSK) == 1
    if len(seglen_DUSK) == 3:
        noDUSK_fr = seglen_DUSK[0]
        noDUSK_to = seglen_DUSK[0] - seglen_DUSK[1] - 1
    if not noDUSK_fr <= idx <= noDUSK_to: return False
    return True

def check_dawn(cdd):
# this is used to check immediately after "civil_dawn_done.append()" for sequence errors
# https://stackoverflow.com/questions/24438976/debugging-get-filename-and-line-number-from-which-a-function-is-called

    caller = getframeinfo(stack()[1][0])
    # note: with "getframeinfo(stack()[2][0])" you get the line number of:
    #       tex += chart_PLANET_VISIBILITY(obj, yy, lats, MPdata, ts)
    if len(cdd) > 0:
        cdd.sort()
        msg = ""
        for fr, to in cdd:
            msg += "  {:6} to {:6},".format(DOY(fr),DOY(to))
            if fr > to:
                print("civil_dawn_done sequence ERROR at {}: ({})".format(caller.lineno,msg[-17:-1]))
                sys.exit(0)

def check_dusk(cdd):
# this is used to check immediately after "civil_dusk_done.append()" for sequence errors
# https://stackoverflow.com/questions/24438976/debugging-get-filename-and-line-number-from-which-a-function-is-called

    caller = getframeinfo(stack()[1][0])
    # note: with "getframeinfo(stack()[2][0])" you get the line number of:
    #       tex += chart_PLANET_VISIBILITY(obj, yy, lats, MPdata, ts)
    if len(cdd) > 0:
        cdd.sort()
        msg = ""
        for fr, to in cdd:
            msg += "  {:6} to {:6},".format(DOY(fr),DOY(to))
            if fr > to:
                print("civil_dusk_done sequence ERROR at {}: ({})".format(caller.lineno,msg[-17:-1]))
                sys.exit(0)

# def get_DAH_ab(DAH_zone):
    # return all_ab_RbDAH[DAH_zone], all_ab_SbDAH[DAH_zone], all_ab_RaDAH[DAH_zone], all_ab_SaDAH[DAH_zone]

# def get_DAH_rs(DAH_zone):
    # return all_rise_segB[DAH_zone], all_set_segB[DAH_zone], all_rise_segA[DAH_zone], all_set_segA[DAH_zone]

def foverlap(start1, end1, start2, end2):
    # Does the float range (start1, end1) overlap with (start2, end2)?
    return end1 >= start2 and end2 >= start1

# def NEQ(a, b):
    # # return True if a == None or b == None
    # # return True if a != b
    # if a is None or b is None: return True
    # return a != b

def mark_rise_seg_done(rise_seg):
    if rise_seg is None: return
    if rise_seg not in rise_seg_done: rise_seg_done.append(rise_seg)
    return

def mark_set_seg_done(set_seg):
    if set_seg is None: return
    if set_seg not in set_seg_done: set_seg_done.append(set_seg)
    return

# def civil_done(idx, civil_done):
    # done = False
    # for fr, to in civil_done:
        # if fr <= idx <= to: done = True
    # return done

# def flush_AMbuf(cc, trace, tex0, seg, from_idx, to_idx):
    # if trace == 1:
        # code_cov.append('#{}-1'.format(cc))
        # tex = r"""
# % trace#{}-1 CIVIL DAWN from {} to {}""".format(cc,DOY(from_idx),DOY(to_idx))
        # tex += tex0 + r"""}"""
    # elif trace == 2:
        # code_cov.append('#{}-2'.format(cc))
        # tex = r"""
# % trace#{}-2 {} RISE seg {} from {} to {}""".format(cc,objn,seg,DOY(from_idx),DOY(to_idx))
        # tex += tex0 + r"""}"""
    # elif trace == 3:
        # code_cov.append('#{}-3'.format(cc))
        # tex = r"""
# % trace#{}-3 {} SET seg {} from {} to {}""".format(cc,objn,seg,DOY(from_idx),DOY(to_idx))
        # tex += tex0 + r"""}"""
    # else:
        # tex = r"""}"""
    # return tex

# def flush_PMbuf(cc,trace, tex0, set_seg, from_idx, to_idx):
    # if trace == 1:
        # code_cov.append('#{}-1'.format(cc))
        # tex = r"""
# % trace#{}-1 CIVIL DUSK from {} to {}""".format(cc,DOY(from_idx),DOY(to_idx))
        # tex += tex0 + r"""}"""
    # elif trace == 2:
        # code_cov.append('#{}-2'.format(cc))
        # tex = r"""
# % trace#{}-2 {} SET seg {} from {} to {}""".format(cc,objn,set_seg,DOY(from_idx),DOY(to_idx))
        # tex += tex0 + r"""}"""
    # else:
        # tex = r"""}"""
    # return tex

def get_DAH(dah):
    # store each DAH zone as a from-to range in a list
    idx_fr = None; idx_to = None
    DAH_zone = []
    if dah == []: return DAH_zone

    for ndx, idx in enumerate(dah):
        if ndx == 0:
            idx_fr = idx_to = idx
        else:
            if idx == prev_idx + 1:
                idx_to = idx
            else:
                DAH_zone.append(range(idx_fr,idx_to+1))
                idx_fr = idx_to = idx
        prev_idx = idx

    DAH_zone.append(range(idx_fr,idx_to+1))
    return DAH_zone

def get_midDAH(dah):
    # get DAH that is not at start or end of year (even if >1 DAH)
    idx_fr = None; idx_to = None
    active = False
    for ndx, idx in enumerate(dah):
        if idx > 0:
            if not active:
                if (ndx == 0) or (idx != prev_idx + 1):
                    active = True
                    idx_fr = idx_to = idx
            else:
                if idx == prev_idx + 1:
                    idx_to = idx
                else:
                    active = False
        prev_idx = idx

    if idx_to is None or idx_to == daystoprocess-1:
        return None, None
    return idx_fr, idx_to

def get_seg(idx, seg_offset, condition=None, preferred_seg = None):
    # based on the date offset 'idx', get the relevant segment and offset
    # 2nd parameter is 'rise_offset' or 'set_offset'
    # 3rd parameter: 'aboveMP' or 'belowMP' or '00htoMP' or 'MPto24h'
    #     'aboveMP' = between MP and next lowerMP (may cross day boundary)
    #     'belowMP' = between MP and previous lowerMP (may cross day boundary)
    #     '00htoMP' = between 00h and MP on same day
    #     'MPto24h' = between MP and 24h on same day
    
    # 'objrise_XY_txt' and 'objset_XY_txt' are RISE/SET line segments.
    # There can be none, one, two or three values on a particular day.
    #   The optional 3rd parameter allows specification of a segment
    #   that is above or below the Meridian Passage.
    okay = False
    ndx = seg = None

    # WARNING: the following test FAILS because it compares the variables VALUES instead:
    #     riseset = objrise_XY_txt if seg_offset == rise_offset else objset_XY_txt

    riseset = objrise_XY_txt if seg_offset is rise_offset else objset_XY_txt
    txt = "RISE" if seg_offset is rise_offset else "SET"
    if len(seg_offset) > 10:
        raise ValueError('ERROR: get_seg 2nd argument incorrect')

    for index, item in enumerate(seg_offset):
        offset = idx - item
        # print("    ",txt,offset,len(riseset[index]))
        if 0 <= offset < len(riseset[index]):  # if a valid possibility
            if condition is not None:
                x0, y0 = getXY(riseset[index][offset])  # y0 in hours!
                upper_mp = meridian_pass[idx]           # upper Meridian Passage
                lower_mp = (upper_mp + 12.0) % 24.0     # lower Meridian Passage
                # print(x0, y0, lower_mp, upper_mp)
                if condition == "aboveMP":
                    okay = True
                    if (lower_mp > y0 > upper_mp) or \
                    (lower_mp < upper_mp and not (lower_mp < y0 < upper_mp)): pass
                    else: continue
                if condition == "belowMP":
                    okay = True
                    if (lower_mp < y0 < upper_mp) or \
                    (lower_mp > upper_mp and not (lower_mp > y0 > upper_mp)): pass
                    else: continue
                if condition == "00htoMP":
                    okay = True
                    if 0.0 <= y0 < upper_mp: pass
                    else: continue
                if condition == "MPto24h":
                    okay = True
                    if upper_mp < y0 <= 24.0 : pass
                    else: continue
                if not okay:
                    print("get_seg ERROR: invalid 3rd parameter:",condition); sys.exit(0)
                # print("{} on {}: y0 = {:.3f} upper_mp = {:.3f} lower_mp = {:.3f}".format(condition,DOY(idx),y0,upper_mp,lower_mp))
            if seg is not None:     # and condition == None:
                if seg == preferred_seg: break
                if preferred_seg is not None and index != preferred_seg:
                    print("WARNING: get_seg {} possibilities for {}:".format(txt, DOY(idx)))
                    print("        ndx = {:3}  seg = {}".format(ndx, seg))
                    print("        ndx = {:3}  seg = {}  <== default".format(offset, index))
            seg = index
            ndx = offset

    # print("get_seg: ndx = {} {} seg = {}".format(ndx,txt,seg))
    return ndx, seg

# def SETseg24h(seg_PM_min, setseg_Ymax):
# # pick next SET segment that borders on 24h
    # seg_PM_max = len(setseg_Ymax)
    # for i in range(seg_PM_min, seg_PM_max):
        # if setseg_Ymax[i] > 23.9: return i
    # return seg_PM_max   # invalid segment number

# def RISEseg00h(seg_AM_min, riseseg_Ymin):
# # pick next RISE segment that borders on 00h
    # seg_AM_max = len(riseseg_Ymin)
    # for i in range(seg_AM_min, seg_AM_max):
        # if riseseg_Ymin[i] < 0.1: return i
    # return seg_AM_max   # invalid segment number

# def duskLTset(dusk,obj_SET):
    # objset = obj_SET
    # # objset = obj_SET if obj_SET > 12.0 else 24.0
    # return dusk < objset

# def dawnGTrise(dawn,obj_RISE):
    # objrise = obj_RISE
    # # objrise = obj_RISE if obj_RISE < 12.0 else 0.0
    # return dawn > objrise

def f_PM(y):
    # replace None with 24.0
    return 24.0 if y is None else y

def f_AM(y):
    # replace None with 0.0
    return 0.0 if y is None else y

def seg_endpoints(seg_offset, dah, dbh, dahseg, dbhseg, dahoffset, dbhoffset, rise_starts, rise_ends, set_starts, set_ends):
# determine metadata relating to the RISE/SET segment end points as follows:
#    if segment length > 1 day, return:
#       - '24h' if adjoining top (24h) border
#       - '00h' if adjoining bottom (00h) border
#       - 'SoY' if adjoining left (Start of Year) border
#       - 'EoY' if adjoining right (End of Year) border
#       - 'DAH' if adjoining a 'days above horizon' zone (new!) and not '00h' or '24h'
#       - 'DBH' if adjoining a 'days below horizon' zone (new!) and not '00h' or '24h'
#    else if segment length = 1 day, for a singular RISE or SET event return...
#       ep0 = ep1 = '24h' if adjoining top (24h) border
#       ep0 = ep1 = '00h' if adjoining bottom (00h) border
# OBSOLETE:
#       - '<DAH' if it is before a 'days above horizon' zone
#       - '>DAH' if it is after  a 'days above horizon' zone
#       - '<DBH' if it is before a 'days below horizon' zone
#       - '>DBH' if it is after  a 'days below horizon' zone

# The 'starting_endpoint' is always earlier than the 'ending_endpoint'
# OBSOLETE: ... however solitary endpoints (seg length 1, spans 0 days) have ep1 = '='

# return a list of tuples ('starting_endpoint','ending_endpoint') per [RISE or SET] segment

    # WARNING: the following test FAILS because it compares the variable VALUES instead:
    #     riseset = objrise_XY_txt if seg_offset == rise_offset else objset_XY_txt

    riseset = objrise_XY_txt if seg_offset is rise_offset else objset_XY_txt
    rs = "RISE" if seg_offset is rise_offset else "SET"
    if len(seg_offset) > 10:
        raise ValueError('ERROR: seg_endpoints 1st argument incorrect')

    endpoints = [(None,None)] * len(seg_offset)
    flip = [False, False]
    # flip[0] = True    when first or last segment coordinate reaches 00h, i.e. it flips to 24h
    # flip[1] = True    when first or last segment coordinate reaches 24h, i.e. it flips to 00h
    RS_flips = False    # True when start or end of segment flips 00h-> 24h or 24h-> 00h

    RbDAH = []; SbDAH = []; RaDAH = []; SaDAH = []
    if dahseg != [[]]:
        for zone in range(len(dahseg)):             # for all DAH zones...
            for DAHtype, seg, ab in dahseg[zone]:   # collect all segments adjoining that zone
                if DAHtype == "RISE_before_dah": RbDAH.append(seg)
                if DAHtype == "SET_before_dah":  SbDAH.append(seg)
                if DAHtype == "RISE_after_dah":  RaDAH.append(seg)
                if DAHtype == "SET_after_dah":   SaDAH.append(seg)

    for index, item in enumerate(seg_offset):

        ep0 = ep1 = ''      # ep0 = 'starting_point';  ep1 = 'ending_point'
        X,Y   = getXY(riseset[index][0])        # start of segment
        Xe,Ye = getXY(riseset[index][-1])       # end of segment

        if X == 0: ep0 = 'SoY'                  # start of year
        elif X == daystoprocess-1: ep0 = 'EoY'
        if Xe == 0: ep1 = 'SoY'                 # end of year
        elif Xe == daystoprocess-1: ep1 = 'EoY'
        ###print("seg_          - {} seg {}: ep0 = '{}' ep1 = '{}'".format(rs, index, ep0, ep1))

        if (ep0 == '' and ep1 == '') and len(riseset[index]) == 1:
            # if solitary event not at SoY or EoY...
            # ... then it could be adjacent to either a DAH or DBH zone
            ep0 = ep1 = '???'

            for index0, offset in enumerate(dahoffset):
                if dah[offset] == X+1:              # at start of DAH zone
                    if rs == 'RISE': ep0 = ep1 = '24h'
                    elif rs == 'SET': ep0 = ep1 = '00h'
                    break
                if offset != 0:
                    if dah[offset-1] == X-1:        # at end of DAH zone
                        if rs == 'SET': ep0 = ep1 = '00h'
                        elif rs == 'RISE': ep0 = ep1 = '24h'
                        break
                if index0 == len(dahoffset) - 1:
                    if dah[-1] == X-1:              # at end of last DAH zone
                        if rs == 'SET': ep0 = ep1 = '00h'
                        elif rs == 'RISE': ep0 = ep1 = '24h'    # Venus 2020 68°N
                        break
            # ----------------------------------------- end of 'for'

            if ep0 == '???':
                for index1, offset in enumerate(dbhoffset):
                    if dbh[offset] == X+1:          # at start of DBH zone
                        if rs == 'SET': ep0 = ep1 = '24h'
                        elif rs == 'RISE': ep0 = ep1 = '00h'    # Mars 1954 63°N
                        break
                    if offset != 0:
                        if dbh[offset-1] == X-1:    # at end of DBH zone
                            if rs == 'RISE': ep0 = ep1 = '00h'
                            break
                    if index1 == len(dbhoffset) - 1:
                        if dbh[-1] == X-1:          # at end of last DBH zone
                            if rs == 'RISE': ep0 = ep1 = '00h'
                            break
                # ----------------------------------------- end of 'for'

            if ep0 == '???' and dah == [] and dbh == []:    # Mercury 1968 62°N
                if Y < 0.6: ep0 = ep1 = '00h'
                elif Y > 23.4: ep0 = ep1 = '24h'

            if ep0 == '???':
                print("ERROR in seg_endpoints: singular {} not identified".format(rs)); sys.exit(0)

        elif (ep0 == '' or ep1 == '') and len(riseset[index]) > 1:  # excluding solitary (length 1) events

            # it is necessary to check the adjoining coordinate for short segments near the upper/lower border
            # e.g. Jupiter 1983 70°N Rise seg 1
            X2,Y2   = getXY(riseset[index][1])      # start+1 of segment    (second coordinate)
            X2e,Y2e = getXY(riseset[index][-2])     # end-1 of segment (penultimate coordinate)

            if dahseg != [[]]:
                if rs == 'SET':
                # if adjoining a DAH zone...
                # ...does the start of a SET segment after DAH also adjoin the 24h border?
                    if index in SaDAH:      # first SET after a DAH zone?
                        for segR, idxR in enumerate(rise_starts):
                            if X == idxR:
                                xR,yR = getXY(objrise_XY_txt[segR][0]) # start of RISE segment
                                if yR > Y: ep0 = 'DAH'
                        if ep0 == '':      ep0 = '24h'; flip[1] = True
                    elif Y  > 23.4 and Y > Y2:
                        ep0 = '24h'; flip[1] = True

                # ...does the end of a SET segment before DAH also adjoin the 24h border?
                    if index in SbDAH:      # last SET before a DAH zone?
                        for segR, idxR in enumerate(rise_ends):
                            if Xe == idxR:
                                xR,yR = getXY(objrise_XY_txt[segR][-1]) # end of RISE segment
                                if yR > Ye: ep1 = 'DAH'
                        if ep1 == '':       ep1 = '24h'; flip[1] = True
                    elif Ye > 23.4 and Ye > Y2e:
                        ep1 = '24h'; flip[1] = True

                # ...does the end of a RISE segment before DAH also adjoin the 00h border?
                if rs == 'RISE':
                    if index in RbDAH:      # last RISE before a DAH zone?
                        for segS, idxS in enumerate(set_ends):
                            if Xe == idxS:
                                xS,yS = getXY(objset_XY_txt[segS][-1]) # end of SET segment
                                if yS < Ye: ep1 = 'DAH'
                        if ep1 == '':       ep1 = '00h'; flip[0] = True
                    elif Ye  < 0.6 and Ye < Y2e:
                        ep1 = '00h'; flip[0] = True

                # ...does the start of a RISE segment after DAH also adjoin the 00h border?
                    if index in RaDAH:      # first RISE after a DAH zone?
                        for segS, idxS in enumerate(set_starts):
                            if X == idxS:
                                xS,yS = getXY(objset_XY_txt[segS][0])  # start of SET segment
                                if yS < Y: ep0 = 'DAH'
                        if ep0 == '':      ep0 = '00h'; flip[0] = True
                    elif Y  < 0.6 and Y < Y2:
                        ep0 = '00h'; flip[0] = True


            if dahseg != [[]]:
                for zone in range(len(dahseg)):
                    for DAHtype, seg, ab in dahseg[zone]:
                        if rs == "RISE" and DAHtype == "RISE_before_dah":
                            if seg == index and ep1 == '': ep1 = 'DAH'; break
                        if rs == "SET"  and DAHtype == "SET_before_dah":
                            if seg == index and ep1 == '': ep1 = 'DAH'; break
                        if rs == "RISE" and DAHtype == "RISE_after_dah":
                            if seg == index and ep0 == '': ep0 = 'DAH'; break
                        if rs == "SET"  and DAHtype == "SET_after_dah":
                            if seg == index and ep0 == '': ep0 = 'DAH'; break

            if dbhseg != [[]]:
                for zone in range(len(dbhseg)):
                    xS = xSe = xR = xRe = yS = ySe = yR = yRe = None    # NEW NEW NEW (Mars 2018 65°N)
                    # first collect the segment end points adjoining the DBH zone
                    for DBHtype, seg in dbhseg[zone]:
                        if DBHtype == "RISE_before_dbh":
                            xRe,yRe = getXY(objrise_XY_txt[seg][-1])    # end of RISE segment
                        if DBHtype == "SET_before_dbh":
                            xSe,ySe = getXY(objset_XY_txt[seg][-1])     # end of SET segment
                        if DBHtype == "RISE_after_dbh":
                            xR,yR = getXY(objrise_XY_txt[seg][0])       # start of RISE segment
                        if DBHtype == "SET_after_dbh":
                            xS,yS = getXY(objset_XY_txt[seg][0])        # start of SET segment

                    # return 'DBH' unless the endpoint also adjoins the upper/lower border
                    for DBHtype, seg in dbhseg[zone]:
                        if rs == "RISE" and DBHtype == "RISE_before_dbh":
                            if seg == index and ep1 == '':
                                ep1 = 'DBH' if yRe < ySe else '24h'; break      # NEW NEW NEW
                        if rs == "SET"  and DBHtype == "SET_before_dbh":
                            if seg == index and ep1 == '':
                                ep1 = 'DBH' if yRe < ySe else '00h'; break      # NEW NEW NEW
                        if rs == "RISE" and DBHtype == "RISE_after_dbh":
                            if seg == index and ep0 == '':
                                ep0 = 'DBH' if yR < yS else '24h'; break        # NEW NEW NEW
                        if rs == "SET"  and DBHtype == "SET_after_dbh":
                            if seg == index and ep0 == '':
                                ep0 = 'DBH' if yR < yS else '00h'; break        # NEW NEW NEW

            # 3 or more coordinates are required to determine the Y rise/fall direction
            # else:
                # X1,Y1 = getXY(riseset[index][1])       # 2nd coord of segment
                # if Y1 < Y and Y > 23.4: ep0 = '24h'; flip[1] = True
                # if Y1 > Y and Y < 0.5:  ep0 = '00h'; flip[0] = True

                # X9,Y9 = getXY(riseset[index][-2])      # penultimate coord of segment
                # if Y9 < Ye and Ye > 23.3: ep1 = '24h'; flip[1] = True    # 23.3 for Mercury 2033 68°N
                # if Y9 > Ye and Ye < 0.5:  ep1 = '00h'; flip[0] = True
            ###print("seg_endpoints - {} seg {}: ep0 = '{}' ep1 = '{}'".format(rs, index, ep0, ep1))

            if ep1 == '':
                next_index = index+1
                if next_index < len(seg_offset):
                    Xn,Yn   = getXY(riseset[next_index][0])         # start of next segment
                    if Ye < 1.0  and Xe == Xn:   ep1 = '00h'; flip[0] = True
                    if Ye > 23.0 and Xe == Xn-2: ep1 = '24h'; flip[1] = True

            if ep0 == '':
                prev_index = index-1
                if 0 <= prev_index:
                    Xn,Yn   = getXY(riseset[prev_index][-1])        # end of previous segment
                    if Y < 1.0  and X == Xn+2: ep0 = '00h'; flip[0] = True  # Mercury 2043 71°N
                    if Y > 23.0 and X == Xn:   ep0 = '24h'; flip[1] = True

        ###print("SEG ENDPOINTS - {} seg {}: ep0 = '{}' ep1 = '{}'".format(rs, index, ep0, ep1))
        if ep0 == '' or ep1 == '':
            print("ERROR in seg_endpoints - {} seg {}: ep0 = '{}' ep1 = '{}'".format(rs, index, ep0, ep1));sys.exit(0)

        endpoints[index] = (ep0, ep1)

    if flip[0] or flip[1]: RS_flips = True    # if RISE or SET flips from 00h to 24h or vice-versa
    # if RS_flips: print("**** RISE or SET flips from 00h to 24h or vice-versa ****")

    return endpoints, RS_flips

# def rise_aboveMP(idx):
# # return TRUE if object RISE is above MerPass, i.e. within 12 hours later (can cross date boundary)
    # orise = getY(objrise_Y[idx])
    # mpass = meridian_pass[idx]
    # if 0.0 < orise - mpass < 12.0: return True
    # #if mpass > orise:      # unnecessary :-)
    # if 24.0 > mpass - orise > 12.0: return True
    # return False

# def rise_belowMP(idx):
# # return TRUE if object RISE is below MerPass, i.e. within 12 hours earlier (can cross date boundary)
    # orise = getY(objrise_Y[idx])
    # mpass = meridian_pass[idx]
    # if 0.0 < mpass - orise < 12.0: return True
    # if 24.0 > orise - mpass > 12.0: return True
    # return False

# def set_aboveMP(idx):
# # return TRUE if object SET is below MerPass, i.e. within 12 hours earlier (can cross date boundary)
    # oset = getY(objset_Y[idx],-1)
    # mpas = meridian_pass[idx]
    # if 0.0 < oset - mpas < 12.0: return True
    # if 24.0 > mpas - oset > 12.0: return True
    # return False

# def set_belowMP(idx):
# # return TRUE if object SET is below MerPass, i.e. within 12 hours earlier (can cross date boundary)
    # oset = getY(objset_Y[idx],-1)
    # mpas = meridian_pass[idx]
    # if 0.0 < mpas - oset < 12.0: return True
    # if 24.0 > oset - mpas > 12.0: return True
    # return False

# def RISE_above_SET(idx, set_seg):
    # RISEabvSET = False
    # ndx = idx - set_offset[set_seg]
    # if 0 <= ndx < len(objset_XY_txt[set_seg]):
        # xS,yS = getXY(objset_XY_txt[set_seg][ndx])
        # # return False if 'objrise_Y[idx]' is None
        # RISEabvSET = f_AM(getY(objrise_Y[idx], -1)) > yS
        # # check if last RISE spans 0 days (Mars 2032 60°S)
        # if rise_offset[-1] == daystoprocess-1: RISEabvSET = False
    # return RISEabvSET
    
# def SET_below_RISE(idx, rise_seg):
    # SETblwRISE = False
    # ndx = idx - rise_offset[rise_seg]
    # if 0 <= ndx < len(objrise_XY_txt[rise_seg]):
        # xR,yR = getXY(objrise_XY_txt[rise_seg][ndx])
        # SETblwRISE = f_PM(getY(objset_Y[idx])) < yR
        # # return False if 'objset_Y[idx]' is None
    # return SETblwRISE

# OBSOLETE...
# def get_returnSET(idx,rise_seg):
# # get the matching SET segment to the specified RISE segment.
# # Note that MerPass separates them almost equally.
# # This is only called shortly after calling 'LOWER_forw'

# #      This is the most reliable calculation to find the SET
# #      segment return path for 'above horizon' shading area.

    # orise = getY(objrise_Y[idx])
    # ndx, set_seg = get_seg(idx, set_offset)
    # if ndx is None: return None
    # xS,yS   = getXY(objset_XY_txt[set_seg][ndx])
    # mpas = meridian_pass[idx]
    # if orise is not None:
        # # print("   returnSET on {}: {:.3f}".format(DOY(idx),(yS - mpas) - (mpas - orise)))
        # if abs((yS - mpas) - (mpas - orise)) < 0.25:
            # if config.PV_df: print("   RISE seg {} matches SET seg {}".format(rise_seg,set_seg))
            # return set_seg
    # return None

# def TA_bhor_OLD(txtXY):
    # # .....................................................................
    # # ..............  add   T E X T  /  A N N O T A T I O N  ..............
    # # ..............             'below horizon'             ..............
    # # .....................................................................

    # tex = ''
    # # if (xmax - txtXY[0])/sf > 4 and (ymax - txtXY[1])/sf > 3:
        # # x0 = txtXY[0] + (xmax*sf - txtXY[0])/2
        # # y0 = txtXY[1] + (ymax*sf - txtXY[1])/2

    # if txtXY is not None:
        # x0 = y0 = None
        # if 6 < xmax - txtXY[0]/sf < daysinyear/20 and 4 < txtXY[1]/sf < 12 and not isEoY:
            # # position in bottom right corner
            # x0 = (daysinyear-20)*sf/10
            # y0 = 2.0 * sf
        # elif 6 < xmax - txtXY[0]/sf < daysinyear/20 and 4 < ymax - txtXY[1]/sf < 12 and not fsEoY:
            # # position in top right corner
            # x0 = (daysinyear-20)*sf/10
            # y0 = 22.0 * sf
        # elif 6 < txtXY[0]/sf < daysinyear/20 and 4 < txtXY[1]/sf < 12 and not isSoY:
            # # position in bottom left corner
            # x0 = 20*sf/10
            # y0 = 2.0 * sf
        # elif 6 < txtXY[0]/sf < daysinyear/20 and 4 < ymax - txtXY[1]/sf < 12 and not fsSoY:
            # # position in top left corner
            # x0 = 20*sf/10
            # y0 = 22.0 * sf
        # if x0 is not None:
            # xy0 = [x0, y0 + 0.35*sf]
            # xy1 = [x0, y0 - 0.35*sf]
            # tex += printlabelXY("below", xy0, 0.0, 'white', False)
            # tex += printlabelXY("horizon", xy1, 0.0, 'white', False)
            
    # return tex

#def TA_rise(obj, rise_seg, objrise_Y, debug=False):
def TA_rise(obj, rise_seg, debug=False):
    # .....................................................................
    # ..............  add   T E X T  /  A N N O T A T I O N  ..............
    # ..............           '<planet name> rise'          ..............
    # .....................................................................

    tex = ''; txtXY = None
    if rise_seg is None: return tex, txtXY
    # xRs = rise_offset[rise_seg]         # start RISE segment
    xRe = rise_offset[rise_seg] + len(objrise_XY_txt[rise_seg]) -1  # end of RISE segment
    # the minimum segment length for annotation depends if the text is inwarda-facing or outwards
    minlen = 36
    if xRe == daystoprocess-1: minlen = 28
    if len(objrise_XY_txt[rise_seg]) <= minlen: return tex, txtXY

    # first check if the segment roughly approximates a short straight line along a constant SHA
    #   (similar to a shaded triangle bottom-left of the chart, typically Jupiter or Saturn)
    step = len(objrise_XY_txt[rise_seg])/4        # measure four line quarter segments (float!)
    xR = [None] * 5
    yR = [None] * 5
    xR[0],yR[0] = getXY(objrise_XY_txt[rise_seg][0])    # start of RISE segment

    linear = True
    seg_min = math.pi       # atan2 return result is between -pi and pi
    seg_max = -math.pi
    for i in range(1,5):
        if i == 4:
            xR[4],yR[4] = getXY(objrise_XY_txt[rise_seg][-1])   # end of RISE segment
        else:
            ndx = round(i * step)
            xR[i],yR[i] = getXY(objrise_XY_txt[rise_seg][ndx])
        seg_ang = math.atan2(10*(yR[i]-yR[i-1]), xR[i]-xR[i-1])     # radians (-pi to pi)
        if seg_ang < seg_min: seg_min = seg_ang
        if seg_ang > seg_max: seg_max = seg_ang
        seg_sha = abs(seg_ang - sha_ang)
        if debug: print("   seg angle = {:.3f}, deviation from SHA = {:.2f}".format(seg_ang*todegrees, seg_sha*todegrees))
        if seg_sha*todegrees > 10.0: linear = False     # keep within 10 degrees of SHA (arbitrary)

    # also check that the maximum deviation of the 4 quarter segments is within 12 degrees (arbitrary)
    if (seg_max - seg_min) * todegrees > 12.0: linear = False

    if linear:      # if the segment approximates a sloping SHA line
        # Why print near the line mid-point? Because the other algorithm below
        #   causes irregulartext shifts with short lines (span < 45 days)
        idx = rise_offset[rise_seg] + int((len(objrise_XY_txt[rise_seg]) + 1)/2)
        if debug: print("   segment approximates a SHA line, idx = {}".format(DOY(idx)))

    else:
        # check for RISE curve linearity... do not print where the curve bends
        Xstart = rise_offset[rise_seg]
        Xlen = len(objrise_XY_txt[rise_seg])
        Xhalflen = int((Xlen + 1)/2)
        Xend = Xstart + Xlen - 1
        if debug: print("   TA_rise: start at {}".format(DOY(Xstart)))

        prev_yR = None
        Yarray = [None] * (int((Xlen/2)-0.01))
        for ndx in range(0, Xlen, 2):
            if not (0 <= ndx < Xlen): continue
            xR,yR = getXY(objrise_XY_txt[rise_seg][ndx])
            if prev_yR is not None:
                Ydev = yR - prev_yR
                Ymid = (yR + prev_yR) / 2.0
                Yang = math.atan2(10*(yR - prev_yR), 2.0)*todegrees     # degrees (-180 to +180)
                if debug: print("   {:3} RISE {:6}  Ydev = {:5.2f}  Yang = {:5.1f}  Ymid = {:5.2f}".format(int(ndx/2)-1,DOY(Xstart+ndx-1),Ydev,Yang,Ymid))
                Yarray[int(ndx/2)-1] = (ndx-1, Yang, Ymid, Ydev)
            prev_yR = yR

        bestXshift = Xshift = 0
        Ydev_goal = 0.2
        Yang_delta_goal = -3.0      # -5.0 is worse
        Xshift_limit = 25
        Xmid = int(len(Yarray)/2)
        okay = False
        curveANG_goal = 10.0        # 10 degrees curvature
        curveROCmin = 180.0

        loop = True
        while loop:
            if Xmid + Xshift -7 < 0: break
            if Xmid + Xshift +7 >= len(Yarray): break
            curveROC = 0.0      # overall change in curvature
            prev_Yang = None
            prev_Yang_delta = None
            Yang_delta_MIN = +180.0
            Yang_delta_MAX = -180.0
            delta_roc_MIN = +1000.0
            delta_roc_MAX = -1000.0

            for n in range(-7,8):
                ndx, Yang, Ymid, Ydev = Yarray[Xmid + Xshift + n]
                if n == -7: ndx_min = ndx
                if n == 7:  ndx_max = ndx
                if n == 0: midndx = ndx; midY = Ymid
                if prev_Yang is not None:
                    # RISE curve as seen from the text annotation (below) ...
                    Yang_delta = Yang - prev_Yang   # +ve convex (good),-ve concave (bad)
                    if Yang_delta > Yang_delta_MAX: Yang_delta_MAX = Yang_delta
                    if Yang_delta < Yang_delta_MIN: Yang_delta_MIN = Yang_delta
                    if prev_Yang_delta is not None:
                        delta_roc = Yang_delta - prev_Yang_delta
                        if delta_roc > delta_roc_MAX: delta_roc_MAX = delta_roc
                        if delta_roc < delta_roc_MIN: delta_roc_MIN = delta_roc
                        curveROC += abs(delta_roc)      # cumulative rate of change
                    prev_Yang_delta = Yang_delta
                prev_Yang = Yang

            if curveROC < curveROCmin and midY > 1.7 and Yang_delta_MIN > Yang_delta_goal:
                # store best results so far...
                curveROCmin = curveROC
                bestXshift = Xshift
                if debug: print("best: curveROCmin = {:.2f}  Xshift = {}".format(curveROCmin, bestXshift))

            if debug: print("   {:2} RISE {:6} to {:6}  angΔMIN/MAX: {:5.1f} {:5.1f}  curveROC = {:5.1f}  midY = {:4.1f}h on {}".format(Xshift,DOY(Xstart+ndx_min),DOY(Xstart+ndx_max),Yang_delta_MIN,Yang_delta_MAX,curveROC,midY,DOY(Xstart+midndx)))

            if curveROC < curveANG_goal and Yang_delta_MIN > Yang_delta_goal and midY > 1.7:
                okay = True; break    # break before the next Xshift is assigned
            if Xshift > 0: Xshift = -Xshift         # alternate left & right
            elif Xshift <= 0: Xshift = -Xshift + 1

            cnd1 = curveROC > curveANG_goal or Yang_delta_MIN < Yang_delta_goal or midY < 1.7
            loop = cnd1 and abs(Xshift) < Xshift_limit

        if debug: print("okay =",okay)
        if not okay: #return tex, txtXY
            Xshift = bestXshift

        ndx, Yang, Ymid, delta = Yarray[Xmid + Xshift]
        idx = Xstart + ndx
        if debug: print("   TA_rise: choose {} at {:4.1f}h".format(DOY(Xstart+ndx), Ymid))

    tn = 2 + ((obj-1)*3)
    ab = 1      # print below
    hdiag = 1.5 * 3
    # ndx = rise_offset[rise_seg] + int((len(objrise_XY_txt[rise_seg]) + 1)/2)
    # txt_size = (txt_width[tn], txt_height[tn], txt_depth[tn])
    # xy, rxy, idx_min, idx_max, dec_min, dec_max, txtXY, ang = label_rectangle(objrise_Y, ndx, txt_size, hdiag*vab[ab])
    labXY, ang = text_position(objrise_Y, idx, hdiag*vab[ab])
    if labXY is not None:
        y0 = labXY[1]/sf
        if y0 >= 0.5:   # don't print below 0.5h 
            txtXY = labXY
            tex += printlabelXY(txt_text[tn], txtXY, ang, 'white', False)

    return tex, txtXY

#def TA_set(obj, set_seg, objset_Y, debug=False):
def TA_set(obj, set_seg, debug=False):
    # .....................................................................
    # ..............  add   T E X T  /  A N N O T A T I O N  ..............
    # ..............           '<planet name> set'           ..............
    # .....................................................................
    tex = txtXY = ''; txtXY = None
    if set_seg is None: return tex, txtXY
    xSs = set_offset[set_seg]           # start SET segment
    # xSe = set_offset[set_seg] + len(objset_XY_txt[set_seg]) -1  # end of SET segment
    # the minimum segment length for annotation depends if the text is inwarda-facing or outwards
    minlen = 36
    if xSs == 0: minlen = 28
    if len(objset_XY_txt[set_seg]) <= minlen: return tex, txtXY

    # first check if the segment roughly approximates a short straight line along a constant SHA
    #   (similar to a shaded triangle top-right of the chart, typically Jupiter or Saturn)
    step = len(objset_XY_txt[set_seg])/4        # measure four line quarter segments (float!)
    xS = [None] * 5
    yS = [None] * 5
    xS[0],yS[0] = getXY(objset_XY_txt[set_seg][0])    # start of SET segment

    linear = True
    seg_min = math.pi       # atan2 return result is between -pi and pi
    seg_max = -math.pi
    for i in range(1,5):
        if i == 4:
            xS[4],yS[4] = getXY(objset_XY_txt[set_seg][-1])   # end of SET segment
        else:
            ndx = round(i * step)
            xS[i],yS[i] = getXY(objset_XY_txt[set_seg][ndx])
        seg_ang = math.atan2(10*(yS[i]-yS[i-1]), xS[i]-xS[i-1])     # radians (-pi to pi)
        if seg_ang < seg_min: seg_min = seg_ang
        if seg_ang > seg_max: seg_max = seg_ang
        seg_sha = abs(seg_ang - sha_ang)
        if debug: print("   seg angle = {:.3f}, deviation from SHA = {:.2f}".format(seg_ang*todegrees, seg_sha*todegrees))
        if seg_sha*todegrees > 10.0: linear = False     # keep within 10 degrees of SHA (arbitrary)

    # also check that the maximum deviation of the 4 quarter segments is within 12 degrees (arbitrary)
    if (seg_max - seg_min) * todegrees > 12.0: linear = False

    if linear:      # if the segment approximates a sloping SHA line
        # Why print near the line mid-point? Because the other algorithm below
        #   causes irregulartext shifts with short lines (span < 45 days)
        idx = set_offset[set_seg] + int((len(objset_XY_txt[set_seg]) + 1)/2)
        if debug: print("   segment approximates a SHA line, idx = {}".format(DOY(idx)))

    else:
        # check for SET curve linearity... do not print where the curve bends
        Xstart = set_offset[set_seg]
        Xlen = len(objset_XY_txt[set_seg])
        Xhalflen = int((Xlen + 1)/2)
        Xend = Xstart + Xlen - 1
        if debug: print("   TA_set: start at {}".format(DOY(Xstart)))

        prev_yR = None
        Yarray = [None] * (int((Xlen/2)-0.01))
        for ndx in range(0, Xlen, 2):
            if not (0 <= ndx < Xlen): continue
            xR,yR = getXY(objset_XY_txt[set_seg][ndx])
            if prev_yR is not None:
                Ydev = yR - prev_yR
                Ymid = (yR + prev_yR) / 2.0
                Yang = math.atan2(10*(yR - prev_yR), 2.0)*todegrees     # degrees (-180 to +180)
                if debug: print("   {:3} SET {:6}  Ydev = {:5.2f}  Yang = {:5.1f}  Ymid = {:5.2f}".format(int(ndx/2)-1,DOY(Xstart+ndx-1),Ydev,Yang,Ymid))
                Yarray[int(ndx/2)-1] = (ndx-1, Yang, Ymid, Ydev)
            prev_yR = yR

        bestXshift = Xshift = 0
        Ydev_goal = 0.2
        Yang_delta_goal = +3.0      # +5.0 is worse
        Xshift_limit = 25
        Xmid = int(len(Yarray)/2)
        okay = False
        curveANG_goal = 10.0        # 10 degrees curvature
        curveROCmin = 180.0

        loop = True
        while loop:
            if Xmid + Xshift -6 < 0: break
            if Xmid + Xshift +6 >= len(Yarray): break
            curveROC = 0.0      # overall change in curvature
            prev_Yang = None
            prev_Yang_delta = None
            Yang_delta_MIN = +180.0
            Yang_delta_MAX = -180.0
            delta_roc_MIN = +1000.0
            delta_roc_MAX = -1000.0

            for n in range(-6,7):
                ndx, Yang, Ymid, Ydev = Yarray[Xmid + Xshift + n]
                if n == -6: ndx_min = ndx
                if n == 6:  ndx_max = ndx
                if n == 0: midndx = ndx; midY = Ymid
                if prev_Yang is not None:
                    # SET curve as seen from the text annotation (above) ...
                    Yang_delta = Yang - prev_Yang   # +ve concave (bad),-ve convex (good)
                    if Yang_delta > Yang_delta_MAX: Yang_delta_MAX = Yang_delta
                    if Yang_delta < Yang_delta_MIN: Yang_delta_MIN = Yang_delta
                    if prev_Yang_delta is not None:
                        delta_roc = Yang_delta - prev_Yang_delta
                        if delta_roc > delta_roc_MAX: delta_roc_MAX = delta_roc
                        if delta_roc < delta_roc_MIN: delta_roc_MIN = delta_roc
                        curveROC += abs(delta_roc)      # cumulative rate of change
                    prev_Yang_delta = Yang_delta
                prev_Yang = Yang

            if curveROC < curveROCmin and midY < 22.3:    # and Yang_delta_MAX < Yang_delta_goal:
                # store best results so far...
                curveROCmin = curveROC
                bestXshift = Xshift
                if debug: print("best: curveROCmin = {:.2f}  Xshift = {}".format(curveROCmin, bestXshift))

            if debug: print("   {:2} SET {:6} to {:6}  angΔMIN/MAX: {:5.1f} {:5.1f}  curveROC = {:5.1f}  midY = {:4.1f}h on {}".format(Xshift,DOY(Xstart+ndx_min),DOY(Xstart+ndx_max),Yang_delta_MIN,Yang_delta_MAX,curveROC,midY,DOY(Xstart+midndx)))

            if curveROC < curveANG_goal and Yang_delta_MAX < Yang_delta_goal and midY < 22.3:
                okay = True; break    # break before the next Xshift is assigned
            # if Xshift > 0: Xshift = -Xshift         # alternate left & right of segment mid-point
            # elif Xshift <= 0: Xshift = -Xshift + 1
            if Xshift < 0: Xshift = -Xshift         # alternate left & right of segment mid-point
            elif Xshift >= 0: Xshift = -Xshift - 1

            cnd1 = curveROC > curveANG_goal or Yang_delta_MAX > Yang_delta_goal or midY > 22.3
            loop = cnd1 and abs(Xshift) < Xshift_limit

        if debug: print("okay =",okay)
        if not okay:
            if Yang_delta_MAX < 10.0:  # tolerate YangΔ (Mercury 2023 70°N)
                Xshift = bestXshift
            else: return tex, txtXY

        ndx, Yang, Ymid, delta = Yarray[Xmid + Xshift]
        idx = Xstart + ndx
        if debug: print("   TA_set: choose {} at {:4.1f}h".format(DOY(Xstart+ndx), Ymid))

    tn = 3 + ((obj-1)*3)
    ab = 0      # print above
    hdiag = 1.5 * 3
    # ndx = set_offset[set_seg] + int((len(objset_XY_txt[set_seg]) + 1)/2)
    # txt_size = (txt_width[tn], txt_height[tn], txt_depth[tn])
    # xy, rxy, idx_min, idx_max, dec_min, dec_max, txtXY, ang = label_rectangle(objset_Y, ndx, txt_size, hdiag*vab[ab])
    labXY, ang = text_position(objset_Y, idx, hdiag*vab[ab])
    if labXY is not None:
        y0 = labXY[1]/sf
        if y0 <= 23.5:   # don't print above 23.5h
            txtXY = labXY
            tex += printlabelXY(txt_text[tn], txtXY, ang, 'white', False)

    return tex, txtXY

# def AHwS(idx_mid, n):       # 'Above Horizon with Sun'
    # # .....................................................................
    # # ..............  add   T E X T  /  A N N O T A T I O N  ..............
    # # ..............              'not visible'              ..............
    # # ..............        '(between dawn and dusk)'        ..............
    # # .....................................................................

    # # global meridian_pass
    # hdiag = 0.27    # text shift perpendicular to text direction
    # lab0, ang = text_position(meridian_pass, idx_mid, hdiag)
    # xoffset = hdiag*math.sin(-ang)
    # yoffset = hdiag*math.cos(-ang)
    # x0 = idx_mid/10 + xoffset
    # y0 = meridian_pass[idx_mid] + n + yoffset
    # xy0 = [x0*sf, y0*sf]
    # x1 = idx_mid/10 - xoffset
    # y1 = meridian_pass[idx_mid] + n - yoffset
    # xy1 = [x1*sf, y1*sf]
    # tex  = printlabelXY("not visible", xy0, ang, 'gray', False)
    # tex += printlabelXY("(between dawn and dusk)", xy1, ang, 'gray', False)

    # return tex

def AHwS2(idx_mid, hr_mid, ang):    # 'Above Horizon with Sun'
    # .....................................................................
    # ..............  add   T E X T  /  A N N O T A T I O N  ..............
    # ..............              'not visible'              ..............
    # ..............        '(between dawn and dusk)'        ..............
    # .....................................................................

    # global meridian_pass
    hdiag = 0.27    # text shift perpendicular to text direction
    #lab0, ang = text_position(meridian_pass, idx_mid, hdiag)
    xoffset = hdiag*math.sin(-ang)
    yoffset = hdiag*math.cos(-ang)
    x0 = idx_mid/10 + xoffset
    y0 = hr_mid + yoffset
    xy0 = [x0*sf, y0*sf]
    x1 = idx_mid/10 - xoffset
    y1 = hr_mid - yoffset
    xy1 = [x1*sf, y1*sf]
    tex  = printlabelXY("not visible", xy0, ang, 'gray', False)
    tex += printlabelXY("(between dawn and dusk)", xy1, ang, 'gray', False)

    return tex

#def vis_per_day(dbh, verticals, objrise_Y, objset_Y, civilY_AM, civilY_PM):
def vis_per_day(dbh, verticals):
# build and return a list with hours of visibility per day
#   & return total hours visibility mornings and evenings
#   & return hours of visibility AM & PM roughly every 10th day

# note: the AM/PM split (independent of MP) is intended to provide
#       visibility data for separate visible morning/evening zones.

    daystotal = daystoprocess
    maxAM  = [0.0] * daystotal  # hours per day before dawn
    maxPM  = [0.0] * daystotal  # hours per day after dusk
    visAM  = [0.0] * daystotal  # hours of visibility AM per day
    visPM  = [0.0] * daystotal  # hours of visibility PM per day
    visday = [0.0] * daystotal  # hours of visibility per day
    # the following are saved only for the date offsets in 'verticals'
    hrAMfr = [None] * len(verticals) # AM time visibility starts
    hrAMto = [None] * len(verticals) # AM time visibility ends
    hrPMfr = [None] * len(verticals) # PM time visibility starts
    hrPMto = [None] * len(verticals) # PM time visibility ends
    
    allhrAM = allhrPM = maxhrAM = maxhrPM = 0.0

    for idx in range(daystotal):

        if idx in dbh: continue     # skip if 'all day below horizon'

        ndx = None          # check if idx is within 'verticals'
        if idx in verticals:
            ndx = verticals.index(idx)

        rise = getY(objrise_Y[idx])
        sett = getY(objset_Y[idx])
        ris2 = getY(objrise_Y[idx],1)
        set2 = getY(objset_Y[idx],1)
        dawn = civilY_AM[idx]
        dusk = civilY_PM[idx]
        hrAM = hrPM = 0.0

        # AM visibility
        if dawn is not None:
            maxAM[idx] = dawn
            hrAM = dawn
            maxhrAM += hrAM
            if f_PM(sett) < f_PM(rise) < dawn:
                # special case - two 'from-to' AM areas, e.g. 2023 Venus 70°N
                hrAMf = 0.0; hrAMt = sett       # 1st region: "0.0 to sett"
                hrAMf2 = rise; hrAMt2 = dawn    # 2nd region: "rise to dawn"
                hrAM = hrAMt + hrAMt2 - hrAMf2
            else:
                hrAMf = 0.0; hrAMt = hrAM   # begin with "0.0 to dawn"
                if f_PM(sett) < dawn:
                    hrAM -= dawn - sett     # trim it "to sett"
                    hrAMt = sett
                if f_PM(rise) < dawn:
                    hrAM -= rise            # trim it "from rise"
                    hrAMf = rise
                elif f_PM(sett) > dawn and f_PM(rise) < f_PM(sett):
                    hrAM = 0.0; hrAMf = None; hrAMt = None
            if hrAM < 0.0:
                print("FAULT: hrAM = {} on {}".format(hrAM,DOY(idx)))
            allhrAM += hrAM
            if ndx is not None:
                hrAMfr[ndx] = hrAMf
                hrAMto[ndx] = hrAMt

        # PM visibility
        if dusk != None:
            maxPM[idx] = 24.0 - dusk
            hrPM = 24.0 - dusk
            maxhrPM += hrPM
            if dusk < f_AM(set2) < f_AM(ris2):
                # special case - two 'from-to' PM areas
                hrPMf = ris2; hrPMt = 24.0      # 1st region: "ris2 to 24.0"
                hrPMf2 = dusk; hrPMt2 = set2    # 2nd region: "dusk to set2"
                hrPM = 24.0 - hrPMf + hrPMt2 - hrPMf2
            else:
                hrPMf = dusk; hrPMt = 24.0  # begin with "dusk to 24.0"
                if f_AM(ris2) > dusk:
                    hrPM -= ris2 - dusk     # trim it "from  ris2"
                    hrPMf = ris2
                if f_AM(set2) > dusk:
                    hrPM -= 24.0 - set2     # trim it "to set2"
                    hrPMt = set2
                elif f_AM(set2) < dusk and f_AM(set2) > f_AM(ris2):
                    hrPM = 0.0; hrPMf = None; hrPMt = None
            if hrPM < 0.0:
                print("FAULT: hrPM = {} on {}".format(hrPM,DOY(idx)))
            allhrPM += hrPM
            if ndx is not None:
                hrPMfr[ndx] = hrPMf
                hrPMto[ndx] = hrPMt

        visAM[idx] = hrAM
        visPM[idx] = hrPM
        visday[idx] = hrAM + hrPM

    if config.debug_visibility:
        print("\nplanet visible {:5.1f} hours or {:5.1f}% of year PM:".format(allhrPM,allhrPM*100/maxhrPM))
        for index, vis in enumerate(visPM):
            print("{:4.1f} ".format(vis), end='')
            if (index+1) % 10 == 0: print()

        print("\nplanet visible {:5.1f} hours or {:5.1f}% of year AM:".format(allhrAM,allhrAM*100/maxhrAM))
        for index, vis in enumerate(visAM):
            print("{:4.1f} ".format(vis), end='')
            if (index+1) % 10 == 0: print()

        # print("\nplanet visibility hours per day")
        # for index, vis in enumerate(visday):
            # print("{:4.1f} ".format(vis), end='')
            # if (index+1) % 10 == 0: print()
        print("\nplanet visible for {:5.1f}% of year".format((allhrAM+allhrPM)/(daysinyear*24)*100))

    vis_stat = maxhrAM, maxhrPM, allhrAM, allhrPM, visday
    vis_frto = hrAMfr, hrAMto, hrPMfr, hrPMto
    return vis_stat, vis_frto

# def trim_SET(objset_XY_txt, objset_Y, set_offset):
# # these special cases need to be trimmed - otherwise they are handled incorrectly...

# # trim former of double SET event at SOY (Jan 1) near 00h if none on Jan 2
# #    e.g. SOY 2027 00:00
    # if len(set_offset) > 1:
        # if set_offset[:2] == [0, 0] and len(objset_XY_txt[0]) == 1:
            # set_offset = set_offset[1:]
            # objset_Y = [objset_Y[0][1]] + objset_Y[1:]
            # newobjset_XY_txt = objset_XY_txt[1:]
            # return (newobjset_XY_txt, objset_Y, set_offset)

# # trim latter of double SET events at EOY near 24h (Jan 1)
# #    e.g. EOY 2026 24:00
    # if len(set_offset) == 2:
        # if set_offset[1] == 365 and len(objset_XY_txt[1]) == 1:
            # set_offset = set_offset[:1]
            # objset_Y = objset_Y[:-1] + [objset_Y[-1][0]]
            # newobjset_XY_txt = objset_XY_txt[:-1]
            # return (newobjset_XY_txt, objset_Y, set_offset)

    # return None

def DOY(idx):
# format day of year like 'Jan 1'
    if idx is None: return "-NONE-"
    if not 0 <= idx <= daysinyear:
        # print("invalid date offset passed to DOY: ",idx)
        # raise Exception     # detect the caller
        # sys.exit(0)
        return "idx={}".format(idx)
    if idx == daysinyear:
        return "Dec 31 24:00"
    dt = d00 + timedelta(days=idx)
    return "{dt:%b} {dt.day}".format(dt=dt)

# def aboveHor(lmt, tuphor):
# # return True if the object's LocalMeanTime (lmt) is above the horizon
    # for fr, to in tuphor:
        # if fr < lmt < to: return True
    # return False

# def get_Jan1_alt(dbh, objrise_Y, objset_Y):
# # build a list of 'from-to' tuples in ascending order with 
# #    Local Mean Time on Jan 1 when object is above horizon.

    # if 0 in dbh: return []

    # Jan1rise_Y = objrise_Y[0]
    # Jan1set_Y  = objset_Y[0]
    # rise_Y = Jan1rise_Y if type(Jan1rise_Y) is list else [Jan1rise_Y]
    # set_Y  = Jan1set_Y  if type(Jan1set_Y)  is list else [Jan1set_Y]
    # # now they're both lists
    # i = r = s = 0
    # hor = []
    # # print("rise_Y",rise_Y)
    # # print("set_Y ",set_Y)
    # while s < len(set_Y) or r < len(rise_Y):
        # if s < len(set_Y) and r < len(rise_Y):
            # if set_Y[s] < rise_Y[r]:
                # hor.append((0.0, set_Y[s]))
                # s += 1
            # else:
                # hor.append((rise_Y[r], set_Y[s]))
                # s += 1
                # r += 1
        # elif r < len(rise_Y):
            # hor.append((rise_Y[r], 24.0))
            # r += 1
        # elif s < len(set_Y):
            # hor.append((0.0, set_Y[s]))
            # s += 1
    # return hor

# def Y00h(XY_txt, pick=-1):  # default is END of segment
# # return precise X coordinate when START/END of curve crosses 00h
# #   START:  pick = 0    END:    pick = -1
    # x1, y1 = tikzXY(XY_txt[pick])
    # if len(XY_txt) >= 2:
        # n = 1 if pick == 0 else -2
        # x2, y2 = tikzXY(XY_txt[n])
        # return x2 + (y2 * (x1- x2) / (y2 - y1))
    # else:
        # return x1

# def Y24h(XY_txt, ymax, pick=0):     # default is START of segment
# # return precise X coordinate when START/END of curve crosses 24h
# #   START:  pick = 0    END:  pick = -1
    # x1, y1 = tikzXY(XY_txt[pick])
    # if len(XY_txt) >= 2:
        # n = 1 if pick == 0 else -2
        # x2, y2 = tikzXY(XY_txt[n])
        # return x2 - ((ymax - y2) * (x2- x1) / (y1 - y2))
    # else:
        # return x1

def getXY(coord):               # return unscaled (comparable) chart values
    x, y = tikzXY(coord)
    idx = int((x+0.01)*10/sf)   # convert to day offset (integer)
    return idx, y/sf

def tikzXY(coord):              # return scaled values, in tikz units!
    i = coord.find(",")
    x = float(coord[1:i])       # omit leading bracket
    y = float(coord[i+1:-1])    # omit trailing bracket
    return x,y

def getY(valY, ndx=0):
    # ndx = the desired offset (positive or negative e.g. 0,1,-1)
    if type(valY) is list:
        # # txt = ""
        # # print("getY returns a list: [",end="")      # warn if valY is a list
        # # for item in valY:
            # # txt0 = "{:.3f}".format(item)
            # # if txt != "": print(txt,end= ", ")
            # # txt = txt0
        # # print("{}]".format(txt0))

        # if multiple values exist,
        #    return the first if ndx omitted, else valY[ndx] if it exists, otherwise the last value
        if ndx > len(valY)-1 or ndx < -len(valY): ndx = len(valY)-1 # get last value in list
        return valY[ndx]
    return valY

def get_Y(idx, Rseg, Sseg):
    # idx     day offset from January 1
    # Rseg    RISE segment number (or None)
    # Rseg    SET segment number  (or None)

    # return yR, yS as hour rounded to 3 decimal places or 'None' if not within the segment
    # CAUTION: as yR and yS are rounded, they might be equal to 0.0 or 24.0

    # this is similar to getY() except that only one value is returned (for the relevant segment)

    yR = None; yS = None
    if Rseg is not None:
        isR = rise_starts[Rseg] <= idx <= rise_ends[Rseg]
        if isR:
            ndx = idx - rise_starts[Rseg]
            yR = riseseg_Y[Rseg][ndx]

    if Sseg is not None:
        isS =  set_starts[Sseg] <= idx <= set_ends[Sseg]
        if isS:
            ndx = idx - set_starts[Sseg]
            yS = setseg_Y[Sseg][ndx]

    return yR, yS

def get_isSoY(rise, sett, sdah, sdbh):
    # return True if object visible at Jan 1 00:00
    if 0 in sdah: return True
    if 0 in sdbh: return False
    if set_starts[0] == 0 and set_days[0] == 0 and sett < 0.5: return False    # solitary SET near 00h  (Mars 2006 58°S)
    if rise is not None and sett is not None: return rise > sett
    if rise is     None and sett is not None: return True
    if rise is not None and sett is     None: return False
    return None     # invalid

def get_fsSoY(rise, sett, sdah, sdbh):
    # return True if object visible at Jan 1 24:00
    if 0 in sdah: return True
    if 0 in sdbh: return False
    if rise is not None and sett is not None: return rise > sett
    if rise is     None and sett is not None: return False
    if rise is not None and sett is     None: return True
    return None     # invalid

def get_isEoY(rise, sett, sdah, sdbh):
    # orthogonal data: return True if object visible at Jan 1  00:00 next year
    #    helical data: return True if object visible at Dec 31 00:00
    if daystoprocess-1 in sdah: return True
    if daystoprocess-1 in sdbh: return False
    if rise is not None and sett is not None: return rise > sett
    if rise is     None and sett is not None: return True
    if rise is not None and sett is     None: return False
    return None     # invalid

def get_fsEoY(rise, sett, sdah, sdbh):
    # orthogonal data: return True if object visible at Jan 1  24:00 next year
    #    helical data: return True if object visible at Dec 31 24:00
    if daystoprocess-1 in sdah: return True
    if daystoprocess-1 in sdbh: return False
    if rise is not None and sett is not None: return rise > sett
    if rise is     None and sett is not None: return False
    if rise is not None and sett is     None: return True
    return None     # invalid

def text_position(text_Y, idx, hdiag):
# simplified version of 'label_rectangle'
# determine the text coordinates and rotation angle

    # check idx limits
    if idx < 1: idx = 1
    if idx > daystoprocess-2: idx = daystoprocess-2

    # TEXT position
    obj_x = idx/10
    obj_y = text_Y[idx]

    # check if Y data is available
    if obj_y is None or text_Y[idx+1] is None or text_Y[idx-1] is None: return None, None

    # label rotation angle
    ydiff = text_Y[idx+1] - text_Y[idx-1]
    ang = math.atan((ydiff)/(2.0/10))    # radians
    rot = "%0.3f" %(ang*todegrees)

    # label shift (label center position - planet position)
    xoffset = hdiag*math.sin(-ang)
    yoffset = hdiag*math.cos(-ang)

    # TEXT center position ('sf' scaling factor required!)
    x0 = (xoffset/10 + obj_x)*sf
    y0 = (yoffset/10 + obj_y)*sf
    lab0 = [x0, y0]

    return lab0, ang

def label_rectangle(object_Y, idx, txt_size, hdiag):
# determine the rectangle encosing the label + its white background
    txt_wdth, txt_hgt, txt_dpt = txt_size

    # check idx limits
    if idx < 1: idx = 1
    if idx > daystoprocess-2: idx = daystoprocess-2

    # PLANET position
    obj_x = idx/10
    obj_y = object_Y[idx]

    # label rotation angle
    ydiff = object_Y[idx+1] - object_Y[idx-1]
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
    v_shift = (txt_hgt+txt_dpt)/2
    xy[0][0] = x0 - (txt_wdth/2)*pt2cm
    xy[0][1] = y0 - (v_shift+boxsep)*pt2cm
    xy[1][0] = xy[0][0]
    xy[1][1] = y0 + (v_shift+boxsep)*pt2cm
    xy[2][0] = x0 + (txt_wdth/2)*pt2cm
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

def solitary_event(x, y, ev):
# print a cross for solitary RISE (red) or SET (blue) events
# ev = True if 'rise' or False if 'set'

    if not config.orthogonal: x += y/24.0
    x0 = x - 1; y0 = y + 0.1
    x1 = x + 1; y1 = y - 0.1
    x8 = x0; y8 = y1
    x9 = x1; y9 = y0
    c = 'red' if ev else 'blue'

    tex = r"""
\draw[thin,color=%s] (%0.3f,%0.3f) -- (%0.3f,%0.3f);""" % (c, x0/10*sf, y0*sf, x1/10*sf, y1*sf)
    tex += r"""
\draw[thin,color=%s] (%0.3f,%0.3f) -- (%0.3f,%0.3f);""" % (c, x8/10*sf, y8*sf, x9/10*sf, y9*sf)
    return tex

# oooooooooooooooooooooooooooooooooooooooooooooooooooooo

def LocalMeanTimeOfMeridianPassage(obj, object_name, object_XY_txt):

    linepattern = ['',
    'dash pattern=on 10pt off 3pt on 1pt off 3pt,',
    'dash pattern=on 10pt off 3pt on 1pt off 3pt on 1pt off 3pt,',
    'dash pattern=on 10pt off 3pt on 1pt off 3pt on 1pt off 3pt on 1pt off 3pt,',
    'dash pattern=on 8pt off 3pt,',
    'dotted,',
    'loosely dashed,',
    'loosely dotted,']
    thickness = ['thick','thick','thick','thick','thick','very thick','thin','thick']

    # meridian_xidx = []  # idx when mpa00 goes below 0h

    # store all planet (Mercury, Venus, Mars, Jupiter, Saturn) apparent positions at 0h per day
    # planet_app_pos = []

    # 'hdiags' is the offset the sun/planet name label is to be raised or
    # lowered (perpendicular to the direction of the text itself) in order
    # to be above or below the path drawn.
    # The units are '6 minutes' (1/10 hour) when measured along the vertical axis.
    hdiags = [0.95*3, 1.4*3, 1.3*3, 1.1*3, 1.2*3, 1.2*3, 1.2*3, 1.2*3]
    # note: multiply by 3 because the fundamental units in Planet Declination Paths is
    # '10 degrees / 30 days' whereas here it is '1 hour / 10 days' (factor 3 smaller).

    # global txt_wdth, txt_hgt
    # Helvetica 10pt text width of planet name in Pt:
    # txt_wdth = [22.70987, 51.64967, 36.04971, 31.03983, 43.8296, 42.3599, 44.36978, 49.37967, 84.00613, 80.6663]
    # Helvetica 10pt text height of planet name in Pt:
    # txt_hgt = 7.40997

    # label_pos = []      # store label position candidates per object
    # chosen_label = []   # list of tuples (obj, index to label_pos)

    linetype = linepattern[obj]
    linewdth = thickness[obj]

    tex = ""
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

    # # .....................................................................
    # # ..............  add   T E X T  /  A N N O T A T I O N  ..............
    # # ..............              'not visible'              ..............
    # # ..............     "<planet name> Meridian Passage"    ..............
    # # .....................................................................
    # prev_len = 0
    # for index, item in enumerate(object_XY_txt):
        # if len(item) > 45:      # if segment lenth > 45 days
            # y = None
            # idx1 = idx2 = None
            # for j in range(len(item)):
                # idx = j + prev_len
                # y0 = meridian_pass[idx]
                # # can't think why I tried this - not suitable for Mars 2024 ...
                # # # try a location near 22.7h or 1.8h in visible zone
                # # if 22.7 > y0 > 22.3: y = y0; break
                # # if 1.8 > y0 > 1.4: y = y0; break
                # if f_PM(civilY_PM[idx]) > y0 > f_AM(civilY_AM[idx]):
                    # if idx1 == None: idx1 = idx
                    # idx2 = idx
            # if y == None:   # no suitable location in visible zone found
                # idx = int((idx1+idx2)/2)    # use mid-idx in 'between dawn and dusk' zone
            # # ensure minimum distance from border
            # idx = max(idx, 25)  # minimum distance from left border
            # idx = min(idx, daystoprocess-25)
            # hdiag = hdiags[obj]     # height (in 1/10 hour) perpendiculat to label text

            # tn = 1 + ((obj-1)*3)
            # ab = 0      # print above
            # # txt_size = (txt_width[tn], txt_height[tn], txt_depth[tn])
            # # xy, rxy, idx_min, idx_max, dec_min, dec_max, txtXY, ang = label_rectangle(meridian_pass, idx, txt_size, hdiag*vab[ab])
            # txtXY, ang = text_position(meridian_pass, idx, hdiag*vab[ab])
            # tex += printlabelXY(txt_text[tn], txtXY, ang, 'gray', False)

            # tn = 0
            # ab = 1      # print below
            # # txt_size = (txt_width[tn], txt_height[tn], txt_depth[tn])
            # # xy, rxy, idx_min, idx_max, dec_min, dec_max, txtXY, ang = label_rectangle(meridian_pass, idx, txt_size, hdiag*vab[ab])
            # txtXY, ang = text_position(meridian_pass, idx, hdiag*vab[ab])
            # tex += printlabelXY(txt_text[tn], txtXY, ang, 'gray', False)

        # prev_len = len(item)
    return tex

# oooooooooooooooooooooooooooooooooooooooooooooooooooooo

def BHwidth(idx, hr):
# return the 'below horizon' vertical bandwidth in hours
# ( < 2.4 is too narrow for text annotation, e.g. Mars 2025 63°N)
    suitability = 2     # good candidate
    if abs(hr - f_AM(civilY_AM[idx])) < 2.0: suitability = 1    # maintain distance from DAWN
    if abs(hr - f_PM(civilY_PM[idx])) < 2.0: suitability = 1    # maintain distance from DUSK

    for s, r in [(0,0),(0,1),(1,0),(1,1)]:
        objset_Y_idx = getY(objset_Y[idx],s)
        objrise_Y_idx = getY(objrise_Y[idx],r)
        if objset_Y_idx is None or objrise_Y_idx is None: continue
        if objset_Y_idx < hr < objrise_Y_idx:   # if a SET-to-RISE band exists...
            if objrise_Y_idx - objset_Y_idx > 2.4: return suitability   # or 'return 2'
            # ignore minimum distance from DAWN/DUSK if SET-to-RISE band
        # ... otherwise if the SET-to-RISE band crosses midnight (24h):
        if objrise_Y_idx < meridian_pass[idx] < objset_Y_idx: return suitability

    return 0    # unsuitable

def LocalMeanTimeOfLowerTransit():
# Simplified calculation of lower transit ...
#   (which is good enough for text annotation purposes)
#   (useful for assessing best text annotation location)

    tup_lowertransit = []
    lst_lowertransit = [[] for i in range(24)]  # includes suitability = 2
    alt_lowertransit = [[] for i in range(24)]  # includes suitability = 1
    prev_y = hr = None
    prev_y_incr = None

    for index, item in enumerate(meridian_pass):
        y = (item + 12.0) % 24
        if index > 0:   # skip index == 0 in order to initialize prev_y
            if y - prev_y >  23.0: prev_y += 24.0   #; hr = 23; hr1 = 24
            if y - prev_y < -23.0: prev_y -= 24.0   #; hr = 0; hr1 = 1
            y_incr = False if y < prev_y else True
            if prev_y_incr is None: prev_y_incr = y_incr
            if index == 1:  # initialize boundary that y is within (hr < y < hr1)
                #hr = int(y)+1 if y_incr else int(y)
                hr = int(y)
                hr1 = hr+1          # includes 24

            # print("LMToLT: y_incr {} on {}({}) y {:.2f} hr {} hr1 {}".format(y_incr,index,DOY(index),y,hr,hr1),end='')
            if not hr < y < hr1:    # if outside boundary
                hr = int(y)
                hr1 = hr+1          # includes 24
                hr_crossed = hr if y_incr else hr1 % 24
                # check suitability regarding vertical space for printing...
                suit = BHwidth(index, hr_crossed)
                if suit == 2 or (suit == 1 and (hr_crossed == 2 or hr_crossed == 22)):
                    # print("  suit {} append {} at {}({})".format(suit,hr_crossed,index,DOY(index)))
                    tup_lowertransit.append((hr_crossed,index, suit))
            # else: print()

            prev_y_incr = y_incr
        prev_y = y

    # store each 'idx' date offset per lower meridian transit hour
    # print(tup_lowertransit)
    for hr, idx, suit in tup_lowertransit:
        if suit == 2: lst_lowertransit[hr].append(idx)
        if suit == 1: alt_lowertransit[hr].append(idx)
    # print(lst_lowertransit)

    if False:       # for debugging only...
        for hr in range(24):
            txt0 = "   lst_lowertransit at {:02d}h: ".format(hr)
            for idx in lst_lowertransit[hr]:
                print("{}{} ".format(txt0,DOY(idx)))
        for hr in range(24):
            txt0 = "   alt_lowertransit at {:02d}h: ".format(hr)
            for idx in alt_lowertransit[hr]:
                print("{}{} ".format(txt0,DOY(idx)))

    return lst_lowertransit, alt_lowertransit

def hr_beforeMP(idx, hr_mp, hr_dawn, objrise_Y):
# determine which line borders the gold zone below the MerPass
    hr_rise = f_AM(getY(objrise_Y[idx]))
    hr_lo = None; limit = 0
    if hr_rise < hr_dawn < hr_mp: hr_lo = hr_dawn; limit = 2
    if hr_dawn < hr_rise < hr_mp: hr_lo = hr_rise; limit = 1
    # return limit = 1 if hr_rise; 2 if hr_dawn; 0 if none
    return hr_lo, limit

def hr_afterMP(idx, hr_mp, hr_dusk, objset_Y):
# determine which line borders the gold zone above the MerPass
    hr_set = f_PM(getY(objset_Y[idx], -1))
    hr_hi = None; limit = 0
    if hr_set > hr_dusk > hr_mp: hr_hi = hr_dusk; limit = 2
    if hr_dusk > hr_set > hr_mp: hr_hi = hr_set;  limit = 1
    # return limit = 1 if hr_set; 2 if hr_dusk; 0 if none
    return hr_hi, limit

#def Planet_Sun_Zone(dbh, verticals, objrise_Y, objset_Y, civilY_AM, civilY_PM):
def Planet_Sun_Zone(dbh, verticals):
# find date with highest vertical gap midway between ...
#       "Meridian Passage and planet Rise or DAWN/DUSK (whichever is closer)"
#     & "Meridian Passage and planet Set  or DAWN/DUSK (whichever is closer)"
#   on the vertical chart lines (approx every 10 days) in year.
#   (useful for assessing best text annotation location)

# Leave a boundary of ... (less than this is unusable for text positioning):
#         approx 30 days from left/right border
#         2 hours from upper/lower chart border

    hr_pre_wdth_max = 0.0
    hr_post_wdth_max = 0.0
    idx_preMP_max = None
    idx_postMP_max = None
    hr_preMP = None
    hr_postMP = None
    n = 3       # start on Feb 1

    while n <= len(verticals) - 4:      # end on Dec 1
        idx = verticals[n]
        hr_mp = meridian_pass[idx]
        hr_rise = getY(objrise_Y[idx])
        hr_set  = getY(objset_Y[idx],-1)
        hr_dusk = f_PM(civilY_PM[idx])
        hr_dawn = f_AM(civilY_AM[idx])
        # skip if planet meridian not between dawn & dusk
        if not (hr_dawn < hr_mp < hr_dusk): n += 1; continue
        # skip if planet never above horizon...
        if (hr_rise is None or hr_set is None) and idx in dbh: n += 1; continue
        hr_lo, lim_beforeMP = hr_beforeMP(idx, hr_mp, hr_dawn, objrise_Y)
        hr_hi, lim_afterMP  = hr_afterMP(idx, hr_mp, hr_dusk, objset_Y)

        if hr_lo is not None:
            hr_pre_wdth = hr_mp - hr_lo
            hr_pre_mp   = hr_mp - (hr_pre_wdth/2)
            if 2.0 < hr_pre_mp < 22.0:
                if hr_pre_wdth > hr_pre_wdth_max:
                    idx_preMP_max = idx
                    hr_preMP = hr_pre_mp
                    hr_pre_wdth_max = hr_pre_wdth
                    # obtain the angle of the border limiting line...
                    if lim_beforeMP == 1:   # if RISE closer to MerPass
                        ydiff = f_AM(getY(objrise_Y[idx+1])) - hr_rise
                    else:                   # if dawn closer
                        ydiff = f_AM(civilY_AM[idx+1]) - hr_dawn
                    ang2_preMP = math.atan(ydiff/0.1)        # radians

        if hr_hi is not None:
            hr_post_wdth = hr_hi - hr_mp
            hr_post_mp   = hr_mp + (hr_post_wdth/2)
            if 2.0 < hr_post_mp < 22.0:
                if hr_post_wdth > hr_post_wdth_max:
                    idx_postMP_max = idx
                    hr_postMP = hr_post_mp
                    hr_post_wdth_max = hr_post_wdth
                    # obtain the angle of the border limiting line...
                    if lim_afterMP == 1:    # if SET closer to MerPass
                        ydiff = f_PM(getY(objset_Y[idx+1])) - hr_set
                    else:                   # if dusk closer
                        ydiff = f_PM(civilY_PM[idx+1]) - hr_dusk
                    ang2_postMP = math.atan(ydiff/0.1)        # radians

        n += 1

    ang_preMP = ang_postMP = None
    # standard value for 'hdiag' here...
    hdiag = 1.2*3   # height (in 1/10 hour) perpendiculat to label text
    ab = 0          # print above
    if idx_preMP_max is not None:     # obtain 'ang' angle at Meridian Passage
        txtXY, ang_preMP = text_position(meridian_pass, idx_preMP_max, hdiag*vab[ab])
        # ang_preMP  = (ang_preMP + ang2_preMP) / 2.0     # bisect the two angles
        ang_preMP  = ang_preMP / 2.0                # bisect the MP slope angle
    if idx_postMP_max is not None:    # obtain 'ang' angle at Meridian Passage
        txtXY, ang_postMP = text_position(meridian_pass, idx_postMP_max, hdiag*vab[ab])
        # ang_postMP = (ang_postMP + ang2_postMP) / 2.0   # bisect the two angles
        ang_postMP = ang_postMP / 2.0               # bisect the MP slope angle

    return hr_preMP, hr_postMP, idx_preMP_max, idx_postMP_max, ang_preMP, ang_postMP

def Planet_Vis_Zone(verticals, vis_frto):
# per AM/PM: find date with highest vertical gap midway between ...
#       "planet visibility begin"
#     & "planet visibility end"
#   on the vertical chart lines (approx every 10 days in year).
#   (useful for assessing best text annotation location)

# NOTE:  AM = before MP          ??????????????????????????????????????????????
#        PM = after MP

# Leave a boundary of ... (less than this is unusable for text positioning):
#         approx 20 days from left/right border
#         1 hour from upper/lower chart border

    hrAMfr, hrAMto, hrPMfr, hrPMto = vis_frto

    hrAM = None
    idx_hrAM = None
    hrAMwdthmax = 0.0

    hrPM = None
    idx_hrPM = None
    hrPMwdthmax = 0.0

    n = 2       # start on Jan 20
    while n <= len(verticals) - 3:      # end on Dec 10
        idx = verticals[n]

        if hrAMfr[n] is not None and hrAMto[n] is not None:
            hrAMwdth = hrAMto[n] - hrAMfr[n]
            hrAMmid = hrAMfr[n] + (hrAMwdth/2.0)
            # if suitable...
            if hrAMwdth > 2.0 and hrAMmid > 1.0:
                if hrAMwdth > hrAMwdthmax:
                    hrAMwdthmax = hrAMwdth
                    idx_hrAM = idx
                    hrAM = hrAMmid

        if hrPMfr[n] is not None and hrPMto[n] is not None:
            hrPMwdth = hrPMto[n] - hrPMfr[n]
            hrPMmid = hrPMfr[n] + (hrPMwdth/2.0)
            # if suitable...
            if hrPMwdth > 2.0 and hrPMmid < 23.0:
                if hrPMwdth > hrPMwdthmax:
                    hrPMwdthmax = hrPMwdth
                    idx_hrPM = idx
                    hrPM = hrPMmid

        n += 1

    return idx_hrAM, hrAM, idx_hrPM, hrPM



# <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> 
# <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> 
# <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> <-> 

#--------------------------
#   external entry point
#--------------------------

def gettccdata():
    return tccdata

def introchart3(page1):

    # A4     = 210mm x 297mm (8.27 x 11.69 in)
    # Letter = 8.5 x 11 in   (216mm x 279mm)
    if config.pgsz == "A4": # parameters for A4 Landscape
        tm1 = "15mm"    # first page...
        bm1 = "15mm"
        lm1 = "10mm"
        rm1 = "10mm"
    else:                   # parameters for Letter Landscape
        tm1 = "13mm"    # first page...
        bm1 = "13mm"
        lm1 = "10mm"
        rm1 = "10mm"

    tex = ""
    if not page1:
        tex += r"""
\newpage"""
    tex += intro_PLANET_VISIBILITY(tm1,bm1,lm1,rm1)

    return tex


#   This simple but effective function eliminates endless keyboard interrupts
#   each time Ctrl-C is issued, while none actually kill the parent process
#   ... and this causes the Command Prompt window (in Windows, MPmode=0) to hang.
def init_worker():
    # Prevent child process from ever receiving a KeyboardInterrupt.
    signal.signal(signal.SIGINT, signal.SIG_IGN)

def buildchart3(obj, d0, diy, lats, v, page1, yy, MPdata, ts):
# Planet Rise and Set times charts

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
    global daystoprocess, daysinyear
    daysinyear = diy
    # we need to include Jan 1 of next year only if processing orthogonal data...
    daystoprocess = diy + 1 if config.orthogonal else diy
    global tccdata
    tccdata = ''
    global sf

    # NOTE!: these scaling values must match those in ppc_build.init_A4
    if config.pgsz == "A4":
        sf = 1.39 * 0.5 # scale factor (0.695cm to 1 hour or 10 calendar days)
    else:
        sf = 1.32 * 0.5 # scale factor (0.66 cm to 1 hour or 10 calendar days)

    # A4     = 210mm x 297mm (8.27 x 11.69 in)
    # Letter = 8.5 x 11 in   (216mm x 279mm)
    if config.pgsz == "A4": # parameters for A4 Landscape
        ori = "a4paper,landscape"
        tm = "5mm"
        bm = "5mm"
        lm = "2mm"
        rm = "2mm"
        tm1 = "15mm"    # first page...
        bm1 = "15mm"
        lm1 = "10mm"
        rm1 = "10mm"
        #parsep = "[12pt]"
    else:                   # parameters for Letter Landscape
        ori = "letterpaper,landscape"
        tm = "5mm"
        bm = "5mm"
        lm = "2mm"
        rm = "2mm"
        tm1 = "13mm"    # first page...
        bm1 = "13mm"
        lm1 = "10mm"
        rm1 = "10mm"
        #parsep = "[8pt]"

    # tikz line thickness...
    # ultra thin    = 0.1pt
    # very thin     = 0.2pt
    # thin          = 0.4pt (default)
    # semithick     = 0.6pt
    # thick         = 0.8pt
    # very thick    = 1.2pt
    # ultra thick   = 1.6pt

    tex = ""

    print("\n       Creating Planet Visibility Charts for {}".format(d0.year))
    if not page1:
        tex += r"""
\newpage"""

    # tex += intro_PLANET_VISIBILITY(tm1,bm1,lm1,rm1)
    tex += chart_PLANET_VISIBILITY(obj, yy, lats, MPdata, ts)

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