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
#from collections import deque

###### Third party imports ######
from skyfield.api import pi, tau

###### Local application imports ######
import config
from pp_skyfield import planet_declinations, ariesSHA, get_object_name

#   My apologies to those who read this . . .
#   Although use of global variables is frowned upon by the Python community,
#   I have chosen to employ global variables in this module to reduce the
#   number of arguments passed to some functions, so that the function
#   arguments focus on the frequently changing parameters.
#   A comment before a function describes which global variables are used.
#   . . . and Murphy whispered in his sleep "If it works, don't touch it"

# global VARIABLES
d00 = None
label_ndx = 0
#tup_crosspoints = None

# global CONSTANTS  (these values are not changed)
degree_sign= u'\N{DEGREE SIGN}'
twopi = 2 * math.pi
todegrees = 180.0/math.pi
toradians = math.pi/180.0
decmin = -30
decmax = 30
navstar_fs = "normalsize"   # navigational star fontsize (10pt)
title_fs ="Large"           # title, SHA, DEC fontsize (14.4pt)
ns_fs = "large"             # North, South fontsize (12pt)

if config.pgsz == "A4":
    sf = 1.39 * 1.4     # scale factor (1.946cm to 10 degrees DEC or 30 calendar days)
else:
    sf = 1.31 * 1.4     # scale factor (1.834cm to 10 degrees DEC or 30 calendar days)


# oooooooooooooooooooooooooooooooooooooooooooooooooooo
# ooooooooooooo YEARLY DECLINATION CHART ooooooooooooo
# oooooooooooooooooooooooooooooooooooooooooooooooooooo

# global variables >>> d00
def chart_DecOfSunAndPlanets(daystoprocess):
    #datestr = d00.strftime("%d %b %Y")
    datestr = d00.strftime("%Y")

    # parameters for 'A4/Letter Landscape'
    #bb = "line width=1.85pt"    # bounding box thickness
    bb = "ultra thick"          # bounding box thickness
    ecliptic_indentA = 8.20   # for 'ECLIPTIC'
    ecliptic_indentB = -5.0   # for 'ECLIPTIC'
    ecliptic_raiseB = -2.1

    # A4/Letter landscape (center vertically)
    tex = r"""
  \hspace{0pt}
  \vfill"""

    tex += r"""
\begin{center}                  % center picture horizontally
% ====== DECLINATION of SUN and PLANETS chart ======
\begin{tikzpicture}"""

# --------------------------------------------------------------
# draw chart vertical lines and label the horizontal axis
    tex += r"""
% draw plot inner vertical lines..."""
    d_inc = d00
    x = 0
    xmax = daystoprocess
    ymax = decmax / 10.0
    ymin = decmin / 10.0
    months = ['JAN.','FEB.','MAR.','APR.','MAY','JUNE','JULY','AUG.','SEPT.','OCT.','NOV.','DEC.']

    while x <= daystoprocess:
        dom = int(d_inc.strftime("%d"))     # day of month
        if x == daystoprocess or dom == 1:
            # draw a vertical line
            tex += r"""
  \draw[ultra thin] ({:.3f},{:.3f}) -- ({:.3f},{:.3f});""".format(
x/30*sf,ymin*sf,x/30*sf,ymax*sf)

        moy = int(d_inc.strftime("%m"))     # month of year
        if dom == 1 and x != daystoprocess:
            # month on lower axis
            mth = months[moy-1]
            tex += r"""
  \node[font=\{}] at ({:.3f},{:.3f}) {{\textbf {{{}}}}};""".format(
navstar_fs,((x/30)+0.5)*sf,(ymin-0.18)*sf,mth)

        x += 1
        d_inc += timedelta(days=1)

# -------------------------------------------------------------------
# draw chart horizontal lines and label the vertical axis
    tex += r"""
% draw plot inner horizontal lines..."""
    y = ymin
    dec = decmin
    while y <= ymax:
        # draw a horizontal line
        tex += r"""
  \draw[ultra thin] ({:.3f},{:.3f}) -- ({:.3f},{:.3f});""".format(
0,y*sf,xmax/30*sf,y*sf)

        if dec % 10 == 0:
            # left DEC axis value
            hsph = ""
            if dec > 0: hsph = 'N'
            if dec < 0: hsph = 'S'
            tex += r"""
  \node[font=\{}] at ({:.3f},{:.3f}) {{\scalebox{{.7}}[1.0]{{\textbf {{{}{}°}}}}}};""".format(
ns_fs,-sf/4.09,y*sf,hsph,abs(dec))

        y += 1
        dec += 10

# ------------------- B O R D E R  lines --------------------

  # NOTE: adding -0.6pt is not necessary with "-- cycle" ...
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

    tex += r"""
% text outside border lines
  \node[font=\{}] at ({:.3f},{:.3f}) {{\textbf{{DECLINATION OF SUN AND PLANETS, {}}}}};""".format(
title_fs,(xmax/60)*sf,(ymax+0.35)*sf,datestr)

# -------------------- B O R D E R  end ---------------------


# ---- Declination path of SUN, MERCURY, VENUS, MARS, JUPITER, SATURN ----

    linepattern = ['',
    'dash pattern=on 10pt off 3pt on 1pt off 3pt,',
    'dash pattern=on 10pt off 3pt on 1pt off 3pt on 1pt off 3pt,',
    'dash pattern=on 10pt off 3pt on 1pt off 3pt on 1pt off 3pt on 1pt off 3pt,',
    'dash pattern=on 8pt off 3pt,',
    'dotted,']
    thickness = ['thick','thick','thick','thick','thick','very thick']

    global planet_dec, hdiags, label_pos, chosen_label
    planet_dec = [[] for i in range(6)]
    hdiags = [1.4, 1.4, 1.4, 1.4, 1.4, 1.4]
    # hdiags is the offset the sun/planet name label is to be raised or
    # lowered (perpendicular to the direction of the text itself) in order
    # to be above or below the path drawn.
    # The units are 'degrees' when measured along the vertical axis.
    label_pos = []      # store label position candidates per object
    #label_ok  = []      # store label positions chosen as index to label_pos
    chosen_label = []   # list of tuples (obj, index to label_pos)

    for obj in [0, 1, 2, 3, 4, 5]:
        linetype = linepattern[obj]
        linewdth = thickness[obj]
        planet_name, planet_XY, planet_dec[obj] = planet_declinations(obj,d00,daystoprocess,sf)

        if len(planet_XY) > 0:
            tex += r"""
%% plot %s declinations per day
 \draw[%s,%scolor=Black] plot[smooth,tension=0.5] coordinates{
""" %(planet_name,linewdth,linetype)
            for i in range(len(planet_XY)):
                tex += r"""%s """ %planet_XY[i]
                if (i+1) % 5 == 0: tex += "\n"
            tex += r"""};"""

    # determine where the 6 Declination paths cross each other
    # (to avoid placing name labels there)
    tup_crosspoints = declination_intersections(daystoprocess)

    # define for Sun, Mercury, Venus, Mars (4 objects)
    # lin_segment offset to the two largest segments:
    max_lin_size_seg = [[None, None] for i in range(4)] # max_lin_size_seg[obj][0 to 1]

    global txt_wdth, txt_hgt
    # Helvetica 10pt text width of planet name in Pt:
    txt_wdth = [22.70987, 51.64967, 36.04971, 31.03983, 43.8296, 42.3599]
    # Helvetica 10pt text height of planet name in Pt:
    txt_hgt = 7.40997

    global pt2cm, boxsep
    pt2cm = 1/28.45274  # 1cm = 28.45274 Pt
    boxsep = 0.8        # Pt

    label = ['True' for i in range(6)]
    pab = ['above', 'below']    # label position (above/below the declination path)
    vab = [1.0, -1.0]           # label position hdiag multiplier for above/below

# ...............................................................
#      based on the two largest gaps between SUN/MERCURY declination crossings
#      try some label positions avoiding a path overlap: SUN
# ...............................................................

    d_inc = d00
    d_mid = None
    x = 0
    prev_hilo = None
    cross_dates = []
    obj = 0         # SUN

    while x <= daystoprocess:
        # traverse path of SUN + MERCURY for largest declination crossing gaps

        DECLdiff = planet_dec[0][x] - planet_dec[1][x]
        hilo = math.copysign(1.0, DECLdiff)
        if x != 0:
            if hilo != prev_hilo:
                #print(d_inc)
                cross_dates.append(d_inc)

        prev_hilo = hilo
        x += 1
        d_inc += timedelta(days=1)
        if d_inc.day == 1 and d_inc.month == 7: d_mid = d_inc


    # find the two largest gaps between SUN/MERCURY declination crossings...
    cross_gap = None
    ###max_gap = 0
    ###max_gap2 = 0
    max_gap = [0, 0]
    d1 = [None, None]   # gap start date
    d2 = [None, None]   # gap end date
    d3 = [None, None]   # gap mid date
    prev_n = 0

    for n in range(1,len(cross_dates)):
        date_gap = (cross_dates[n] - cross_dates[n-1]).days
        if date_gap > max_gap[0]:
            max_gap[0] = date_gap
            d1[0] = cross_dates[n-1]
            d2[0] = cross_dates[n]
            d3[0] = d1[0] + timedelta(days=date_gap/2)
            prev_n = n

    for n in range(1,len(cross_dates)):
        date_gap = (cross_dates[n] - cross_dates[n-1]).days
        if n != prev_n:
            if date_gap > max_gap[1]:
                max_gap[1] = date_gap
                d1[1] = cross_dates[n-1]
                d2[1] = cross_dates[n]
                d3[1] = d1[1] + timedelta(days=date_gap/2)

    # are the two largest SUN/MERCURY gaps adjacent?
    adj_gaps = False        # gaps are not adjacent
    mid_gap = None
    if max_gap[0] != 0 and max_gap[1] != 0:
        if d2[0] == d1[1]: adj_gaps = True # gap 1 is adjacent to gap2
        if d1[0] == d2[1]: adj_gaps = True # gap 2 is adjacent to gap1
        if adj_gaps:
            # which gap center is closer to mid-year?
            if abs(d3[0] - d_mid) < abs(d3[1] - d_mid): mid_gap = 0
            else: mid_gap = 1
        
    #print(max_gap[0], d1[0], d2[0], d3[0])
    #print(max_gap[1], d1[1], d2[1], d3[1], mid_gap)

    # -------------------------------------------------------------
    # |  x-, y-position coordinates are in units of '10 degrees'  |
    # |  or '30 calendar days', i.e. 1 unit corresponds to the    |
    # |  chart horizontal separation lines and very close to the  |
    # |  chart monthly vertical lines.                            |
    # -------------------------------------------------------------

    # try both label positions: above and below the path
    # check if the label overwrites neighboring declination paths
    obj = 0         # SUN
    two_tuples = [None, None]   # store tuple to be appended to label_pos

    for n in [0,1]:         # per SUN/MERCURY gap (two maximum)
        if max_gap[n] != 0:
            idx = (d3[n] - d00).days
            date0 = d00 + timedelta(days=idx)
            hdiag = hdiags[obj]     # height (in degrees) perpendiculat to label text

            abcount = 0             # count successful above/below positions (per segment)
            for ab in [0,1]:        # label above and below path...
                xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang = label_rectangle(obj, idx, hdiag*vab[ab])
                #tex += plot_rectangle(xy)
                #tex += plot_rectangle(rxy)
                #tex += printdot2(rx_min, 0.0)
                #tex += printdot2(rx_max, 0.0)
                date_min = d00 + timedelta(days=idx_min)
                date_max = d00 + timedelta(days=idx_max)
                #print("{} to {}".format(date_min,date_max))
                #print(dec_min, dec_max)
                
                # check if the label overwrites neighboring declination paths
                badobj = path_overlaid_check(obj, xy, idx_min, idx_max, dec_min, dec_max, lab0, ang)
                if len(badobj) > 0:
                    if config.debug_chosen:
                        msg = ""
                        for obj0 in badobj:
                            msg += "{}, ".format(get_object_name(obj0).upper())
                        msg = msg[:-2]
                        print("      {:7} (label {}) on {} overlays path: {}".format(get_object_name(obj).upper(), pab[ab], date0, msg))
                else:
                    abcount += 1
                    abgood = ab
                    two_tuples[ab] = (obj, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang, ab)

            if abcount == 2:    # then save both (above & below) in label_pos
                # look for greatest declination separation from other planets/sun
                abdiff_min = [180.0] * 2            # abdiff_min[0 to 1]
                abdiff = [[180.0] * 6 for i in range(2)]    # abdiff[0 to 1][0 to 5]
                dec1 = planet_dec[obj][idx]
                for k in range(6):
                    if k == obj: continue
                    dec2 = planet_dec[k][idx]
                    j = 0 if dec2 > dec1 else 1     # 0 if above obj; 1 if below
                    abdiff[j][k] = abs(dec2 - dec1)
                abdiff_min[0] = min(abdiff[0])  # minimum dec separation above
                abdiff_min[1] = min(abdiff[1])  # minimum dec separation below
                # the first choice is the preferred position...
                # 1st pick: highest minimum distance to nearest path (above or below obj)
                ab = 0 if abdiff_min[0] > abdiff_min[1] else 1
                write_label_candidate(obj, idx, ang, ab)
                label_pos.append(two_tuples[ab])
                # 2nd pick: the opposite side (above or below obj)
                ab = 1 - ab
                write_label_candidate(obj, idx, ang, ab)
                label_pos.append(two_tuples[ab])
            elif abcount == 1:  # then save the position (above or below) that worked
                write_label_candidate(obj, idx, ang, abgood)
                label_pos.append(two_tuples[abgood])

# ...............................................................
#      based on the two two largest near-linear segments
#      try some label positions avoiding a path overlap: SUN
# ...............................................................

    # ---- analyse path and find two largest near-linear segments ----
    roac = None     # daily rate of angular change in direction
    prev_daily_ang = None
    near_linear = False
    sun_lin_segment = [[], [], [], []] # start date, end date, length (days), valid
    lin_start = None
    max_lin_size = [0, 0]           # size of largest segments
    segnum = 0
    obj = 0         # SUN

    # find the largest and 2nd largest 'near linear' path segments
    for n in range(1,len(planet_dec[obj])):
        daily_ang = math.atan((planet_dec[obj][n] - planet_dec[obj][n-1])*3)*todegrees
        if n > 1:
            roac = daily_ang - prev_daily_ang
            #print(d00 + timedelta(days=n), planet_dec[2][n], daily_ang, roac)
            if abs(roac) < 1.0:
                if not near_linear:
                    lin_start = d00 + timedelta(days=n)
                    #print("VENUS linear section begins: ", lin_start)
                near_linear = True
            else:
                if near_linear:
                    lin_end = d00 + timedelta(days=n)
                    #print("VENUS linear section ends: ", lin_end)
                    lin_size = (lin_end - lin_start).days
                    sun_lin_segment[0].append(lin_start)
                    sun_lin_segment[1].append(lin_end)
                    sun_lin_segment[2].append(lin_size)
                    sun_lin_segment[3].append(True)
                    if lin_size > max_lin_size[0]:
                        max_lin_size[0] = lin_size
                        max_lin_size_seg[obj][0] = segnum
                    segnum += 1
                near_linear = False
        prev_daily_ang = daily_ang
    
    #print(sun_lin_segment)
    #print(sun_lin_segment[0][max_lin_size_seg[obj][0]])
    #print(sun_lin_segment[1][max_lin_size_seg[obj][0]])
    #print(sun_lin_segment[2][max_lin_size_seg[obj][0]])

    # find second largest line segment
    for k in range(len(sun_lin_segment[0])):
        if k != max_lin_size_seg[obj][0]:   # exclude largest segment
            if sun_lin_segment[2][k] > max_lin_size[1]:
                max_lin_size[1] = sun_lin_segment[2][k]
                max_lin_size_seg[obj][1] = k

    #print(max_lin_size[1], max_lin_size_seg[obj][1])
    #print(sun_lin_segment[0][max_lin_size_seg[obj][1]], sun_lin_segment[2][max_lin_size_seg[obj][1]])

    # -------------------------------------------------------------
    # |  x-, y-position coordinates are in units of '10 degrees'  |
    # |  or '30 calendar days', i.e. 1 unit corresponds to the    |
    # |  chart horizontal separation lines and very close to the  |
    # |  chart monthly vertical lines.                            |
    # -------------------------------------------------------------

    # try both label positions: above and below the path
    # check if the label overwrites neighboring declination paths
    obj = 0         # SUN
    two_tuples = [None, None]   # store tuple to be appended to label_pos

    for n in [0,1]:         # per path segment
        if max_lin_size_seg[obj][n] != None:
        
            idx = (sun_lin_segment[0][max_lin_size_seg[obj][n]] - d00).days
            idx += int(sun_lin_segment[2][max_lin_size_seg[obj][n]]/2)
            date0 = d00 + timedelta(days=idx)
            hdiag = hdiags[obj]     # height (in degrees) perpendiculat to label text

            abcount = 0             # count successful above/below positions (per segment)
            for ab in [0,1]:        # label above and below path...
                xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang = label_rectangle(obj, idx, hdiag*vab[ab])
                #tex += plot_rectangle(xy)
                #tex += plot_rectangle(rxy)
                #tex += printdot2(rx_min, 0.0)
                #tex += printdot2(rx_max, 0.0)
                date_min = d00 + timedelta(days=idx_min)
                date_max = d00 + timedelta(days=idx_max)
                #print("{} to {}".format(date_min,date_max))
                #print(dec_min, dec_max)
                
                # check if the label overwrites neighboring declination paths
                badobj = path_overlaid_check(obj, xy, idx_min, idx_max, dec_min, dec_max, lab0, ang)
                if len(badobj) > 0:
                    if config.debug_chosen:
                        msg = ""
                        for obj0 in badobj:
                            msg += "{}, ".format(get_object_name(obj0).upper())
                        print("      {:7} (label {}) on {} overlays path: {}".format(get_object_name(obj).upper(), pab[ab], date0, msg[:-2]))
                else:
                    abcount += 1
                    abgood = ab
                    two_tuples[ab] = (obj, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang, ab)

            if abcount == 2:    # then save both (above & below) in label_pos
                # look for greatest declination separation from other planets/sun
                abdiff_min = [180.0] * 2            # abdiff_min[0 to 1]
                abdiff = [[180.0] * 6 for i in range(2)]    # abdiff[0 to 1][0 to 5]
                dec1 = planet_dec[obj][idx]
                for k in range(6):
                    if k == obj: continue
                    dec2 = planet_dec[k][idx]
                    j = 0 if dec2 > dec1 else 1     # 0 if above obj; 1 if below
                    abdiff[j][k] = abs(dec2 - dec1)
                abdiff_min[0] = min(abdiff[0])  # minimum dec separation above
                abdiff_min[1] = min(abdiff[1])  # minimum dec separation below
                #print("   {:7} {:.2f} {:.2f}".format(get_object_name(obj).upper(), abdiff_min[0], abdiff_min[1]))
                # the first choice is the preferred position...
                # 1st pick: highest minimum distance to nearest path (above or below obj)
                ab = 0 if abdiff_min[0] > abdiff_min[1] else 1
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
#      based on the two two largest near-linear segments
#      try some label positions avoiding a path overlap: MERCURY
# ...................................................................

    # ---- analyse path and find two largest near-linear segments ----
    roac = None     # daily rate of angular change in direction
    prev_daily_ang = None
    near_linear = False
    mercury_lin_segment = [[], [], [], []] # start date, end date, length (days), valid
    lin_start = None
    max_lin_size = [0, 0]           # size of largest segments
    segnum = 0
    obj = 1         # MERCURY

    for n in range(1,len(planet_dec[1])):
        daily_ang = math.atan((planet_dec[1][n] - planet_dec[1][n-1])*3)*todegrees
        if n > 1:
            roac = daily_ang - prev_daily_ang
            #print(d00 + timedelta(days=n), planet_dec[1][n], daily_ang, roac)
            if abs(roac) < 1.0:
                if not near_linear:
                    lin_start = d00 + timedelta(days=n)
                    #print("MERCURY linear section begins: ", lin_start)
                near_linear = True
            else:
                if near_linear:
                    lin_end = d00 + timedelta(days=n)
                    #print("MERCURY linear section ends: ", lin_end)
                    lin_size = (lin_end - lin_start).days
                    mercury_lin_segment[0].append(lin_start)
                    mercury_lin_segment[1].append(lin_end)
                    mercury_lin_segment[2].append(lin_size)
                    mercury_lin_segment[3].append(True)
                    if lin_size > max_lin_size[0]:
                        max_lin_size[0] = lin_size
                        max_lin_size_seg[obj][0] = segnum
                    segnum += 1
                near_linear = False
        prev_daily_ang = daily_ang
    
    #print(mercury_lin_segment)
    #print(mercury_lin_segment[0][max_lin_size_seg[obj][0]])
    #print(mercury_lin_segment[1][max_lin_size_seg[obj][0]])
    #print(mercury_lin_segment[2][max_lin_size_seg[obj][0]])

    # find second largest line segment
    for k in range(len(mercury_lin_segment[0])):
        if k != max_lin_size_seg[obj][0]:   # exclude largest segment
            if mercury_lin_segment[2][k] > max_lin_size[1]:
                max_lin_size[1] = mercury_lin_segment[2][k]
                max_lin_size_seg[obj][1] = k

    #print(max_lin_size[1], max_lin_size_seg[obj][1])
    #print(mercury_lin_segment[0][max_lin_size_seg[obj][1]], mercury_lin_segment[2][max_lin_size_seg[obj][1]])

    # -------------------------------------------------------------
    # |  x-, y-position coordinates are in units of '10 degrees'  |
    # |  or '30 calendar days', i.e. 1 unit corresponds to the    |
    # |  chart horizontal separation lines and very close to the  |
    # |  chart monthly vertical lines.                            |
    # -------------------------------------------------------------

    # try both label positions: above and below the path
    # check if the label overwrites neighboring declination paths
    obj = 1         # MERCURY
    two_tuples = [None, None]   # store tuple to be appended to label_pos

    for n in [0,1]:         # per near-linear segment (two maximum)
        idx_off = 0
        if max_lin_size_seg[obj][n] != None:
            idx = (mercury_lin_segment[0][max_lin_size_seg[obj][n]] - d00).days
            idx += int(mercury_lin_segment[2][max_lin_size_seg[obj][n]]/2)
            date0 = d00 + timedelta(days=idx)
            hdiag = hdiags[obj]     # height (in degrees) perpendiculat to label text

            abcount = 0             # count successful above/below positions (per segment)
            for ab in [0,1]:        # label above and below path...
                xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang = label_rectangle(obj, idx, hdiag*vab[ab])
                #tex += plot_rectangle(xy)
                #tex += plot_rectangle(rxy)
                #tex += printdot2(rx_min, 0.0)
                #tex += printdot2(rx_max, 0.0)
                date_min = d00 + timedelta(days=idx_min)
                date_max = d00 + timedelta(days=idx_max)
                #print("{} to {}".format(date_min,date_max))
                #print(dec_min, dec_max)
                
                # check if the label overwrites neighboring declination paths
                badobj = path_overlaid_check(obj, xy, idx_min, idx_max, dec_min, dec_max, lab0, ang)
                if len(badobj) > 0:
                    if config.debug_chosen:
                        msg = ""
                        for obj0 in badobj:
                            msg += "{}, ".format(get_object_name(obj0).upper())
                        msg = msg[:-2]
                        print("      {:7} (label {}) on {} overlays path: {}".format(get_object_name(obj).upper(), pab[ab], date0, msg))

                    # for obj0 in badobj:
                        # idx_diff_val, idx_diff_min = nearest_path_crossing(idx, obj, obj0, tup_crosspoints)
                        # label_offset = []
                        # # only consider local path crossings within 30 days
                        # if idx_diff_min <= 30:
                            # label_offset.append(math.copysign(5.0, idx - idx_diff_val))
                    # if len(label_offset) > 0:
                        # off_min = min(label_offset)
                        # off_max = max(label_offset)
                        # # ignore if local path crossings are both before and after idx
                        # if not(off_min == -5.0 and off_max == 5.0):
                            # idx_off = int(label_offset[0])
                            
                else:
                    abcount += 1
                    abgood = ab
                    two_tuples[ab] = (obj, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang, ab)

            if abcount == 2:    # then save both (above & below) in label_pos
                # look for greatest declination separation from other planets/sun
                abdiff_min = [180.0] * 2            # abdiff_min[0 to 1]
                abdiff = [[180.0] * 6 for i in range(2)]    # abdiff[0 to 1][0 to 5]
                dec1 = planet_dec[obj][idx]
                for k in range(6):
                    if k == obj: continue
                    dec2 = planet_dec[k][idx]
                    j = 0 if dec2 > dec1 else 1     # 0 if above obj; 1 if below
                    abdiff[j][k] = abs(dec2 - dec1)
                abdiff_min[0] = min(abdiff[0])  # minimum dec separation above
                abdiff_min[1] = min(abdiff[1])  # minimum dec separation below
                # the first choice is the preferred position...
                # 1st pick: highest minimum distance to nearest path (above or below obj)
                ab = 0 if abdiff_min[0] > abdiff_min[1] else 1
                write_label_candidate(obj, idx, ang, ab)
                label_pos.append(two_tuples[ab])
                # 2nd pick: the opposite side (above or below obj)
                ab = 1 - ab
                write_label_candidate(obj, idx, ang, ab)
                label_pos.append(two_tuples[ab])
            elif abcount == 1:  # then save the position (above or below) that worked
                write_label_candidate(obj, idx, ang, abgood)
                label_pos.append(two_tuples[abgood])


# .................................................................
#      based on the largest gap(s) between path crossings
#      try some label positions avoiding a path overlap: MERCURY
# .................................................................

    p_sections = path_sections(obj, daystoprocess, tup_crosspoints)
    for sec_len, from_idx, to_idx, obj8, obj9 in p_sections:
        date0 = d00 + timedelta(days=from_idx)
        date1 = d00 + timedelta(days=to_idx)
        if config.debug_section_length:
            print("{} section length {:5.2f}   {} - {}   {}-{}".format(get_object_name(obj).upper(), sec_len, date0, date1, get_object_name(obj8), get_object_name(obj9)))

    if len(p_sections) >=3:
        for n in [-1,-2,-3]:       # pick the largest three sections
            sec_len, from_idx, to_idx, obj8, obj9 = p_sections[n]
            idx = from_idx
            idx += int((to_idx-from_idx)/2)
            date0 = d00 + timedelta(days=idx)
            hdiag = hdiags[obj]     # height (in degrees) perpendiculat to label text
            
            abcount = 0             # count successful above/below positions (per segment)
            for ab in [0,1]:        # label above and below path...
                xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang = label_rectangle(obj, idx, hdiag*vab[ab])

                # check if the label overwrites neighboring declination paths
                badobj = path_overlaid_check(obj, xy, idx_min, idx_max, dec_min, dec_max, lab0, ang)
                if len(badobj) > 0:
                    if config.debug_chosen:
                        msg = ""
                        for obj0 in badobj:
                            msg += "{}, ".format(get_object_name(obj0).upper())
                        print("      {:7} (label {}) on {} overlays path: {}".format(get_object_name(obj).upper(), pab[ab], date0, msg[:-2]))
                else:
                    abcount += 1
                    abgood = ab
                    two_tuples[ab] = (obj, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang, ab)

            if abcount == 2:    # then save both (above & below) in label_pos
                # look for greatest declination separation from other planets/sun
                abdiff_min = [180.0] * 2            # abdiff_min[0 to 1]
                abdiff = [[180.0] * 6 for i in range(2)]    # abdiff[0 to 1][0 to 5]
                dec1 = planet_dec[obj][idx]
                for k in range(6):
                    if k == obj: continue
                    dec2 = planet_dec[k][idx]
                    j = 0 if dec2 > dec1 else 1     # 0 if above obj; 1 if below
                    abdiff[j][k] = abs(dec2 - dec1)
                abdiff_min[0] = min(abdiff[0])  # minimum dec separation above
                abdiff_min[1] = min(abdiff[1])  # minimum dec separation below
                #print("   {:7} {:.2f} {:.2f}".format(get_object_name(obj).upper(), abdiff_min[0], abdiff_min[1]))
                # the first choice is the preferred position...
                # 1st pick: highest minimum distance to nearest path (above or below obj)
                ab = 0 if abdiff_min[0] > abdiff_min[1] else 1
                write_label_candidate(obj, idx, ang, ab)
                label_pos.append(two_tuples[ab])
                # 2nd pick: the opposite side (above or below obj)
                ab = 1 - ab
                write_label_candidate(obj, idx, ang, ab)
                label_pos.append(two_tuples[ab])
            elif abcount == 1:  # then save the position (above or below) that worked
                write_label_candidate(obj, idx, ang, abgood)
                label_pos.append(two_tuples[abgood])

# .................................................................
#      based on the two two largest near-linear segments
#      try some label positions avoiding a path overlap: VENUS
# .................................................................

    # ---- analyse path and find two largest near-linear segments ----
    roac = None     # daily rate of angular change in direction
    prev_daily_ang = None
    near_linear = False
    venus_lin_segment = [[], [], [], []] # start date, end date, length (days), valid
    lin_start = None
    max_lin_size = [0, 0]           # size of largest segments
    segnum = 0
    obj = 2         # VENUS

    # find the largest and 2nd largest 'near linear' path segments
    for n in range(1,len(planet_dec[obj])):
        daily_ang = math.atan((planet_dec[obj][n] - planet_dec[obj][n-1])*3)*todegrees
        if n > 1:
            roac = daily_ang - prev_daily_ang
            #print(d00 + timedelta(days=n), planet_dec[2][n], daily_ang, roac)
            if abs(roac) < 1.0:
                if not near_linear:
                    lin_start = d00 + timedelta(days=n)
                    #print("VENUS linear section begins: ", lin_start)
                near_linear = True
            else:
                if near_linear:
                    lin_end = d00 + timedelta(days=n)
                    #print("VENUS linear section ends: ", lin_end)
                    lin_size = (lin_end - lin_start).days
                    venus_lin_segment[0].append(lin_start)
                    venus_lin_segment[1].append(lin_end)
                    venus_lin_segment[2].append(lin_size)
                    venus_lin_segment[3].append(True)
                    if lin_size > max_lin_size[0]:
                        max_lin_size[0] = lin_size
                        max_lin_size_seg[obj][0] = segnum
                    segnum += 1
                near_linear = False
        prev_daily_ang = daily_ang
    
    #print(venus_lin_segment)
    #print(venus_lin_segment[0][max_lin_size_seg[obj][0]])
    #print(venus_lin_segment[1][max_lin_size_seg[obj][0]])
    #print(venus_lin_segment[2][max_lin_size_seg[obj][0]])

    # find second largest line segment
    for k in range(len(venus_lin_segment[0])):
        if k != max_lin_size_seg[obj][0]:   # exclude largest segment
            if venus_lin_segment[2][k] > max_lin_size[1]:
                max_lin_size[1] = venus_lin_segment[2][k]
                max_lin_size_seg[obj][1] = k

    #print(max_lin_size[1], max_lin_size_seg[obj][1])
    #print(venus_lin_segment[0][max_lin_size_seg[obj][1]], venus_lin_segment[2][max_lin_size_seg[obj][1]])

    # -------------------------------------------------------------
    # |  x-, y-position coordinates are in units of '10 degrees'  |
    # |  or '30 calendar days', i.e. 1 unit corresponds to the    |
    # |  chart horizontal separation lines and very close to the  |
    # |  chart monthly vertical lines.                            |
    # -------------------------------------------------------------

    # try both label positions: above and below the path
    # check if the label overwrites neighboring declination paths
    obj = 2         # VENUS
    two_tuples = [None, None]   # store tuple to be appended to label_pos

    for n in [0,1]:         # per path segment
        if max_lin_size_seg[obj][n] != None:
        
            idx = (venus_lin_segment[0][max_lin_size_seg[obj][n]] - d00).days
            idx += int(venus_lin_segment[2][max_lin_size_seg[obj][n]]/2)
            date0 = d00 + timedelta(days=idx)
            hdiag = hdiags[obj]     # height (in degrees) perpendiculat to label text

            abcount = 0             # count successful above/below positions (per segment)
            for ab in [0,1]:        # label above and below path...
                xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang = label_rectangle(obj, idx, hdiag*vab[ab])
                #tex += plot_rectangle(xy)
                #tex += plot_rectangle(rxy)
                #tex += printdot2(rx_min, 0.0)
                #tex += printdot2(rx_max, 0.0)
                date_min = d00 + timedelta(days=idx_min)
                date_max = d00 + timedelta(days=idx_max)
                #print("{} to {}".format(date_min,date_max))
                #print(dec_min, dec_max)
                
                # check if the label overwrites neighboring declination paths
                badobj = path_overlaid_check(obj, xy, idx_min, idx_max, dec_min, dec_max, lab0, ang)
                if len(badobj) > 0:
                    if config.debug_chosen:
                        msg = ""
                        for obj0 in badobj:
                            msg += "{}, ".format(get_object_name(obj0).upper())
                        print("      {:7} (label {}) on {} overlays path: {}".format(get_object_name(obj).upper(), pab[ab], date0, msg[:-2]))
                else:
                    abcount += 1
                    abgood = ab
                    two_tuples[ab] = (obj, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang, ab)

            if abcount == 2:    # then save both (above & below) in label_pos
                # look for greatest declination separation from other planets/sun
                abdiff_min = [180.0] * 2            # abdiff_min[0 to 1]
                abdiff = [[180.0] * 6 for i in range(2)]    # abdiff[0 to 1][0 to 5]
                dec1 = planet_dec[obj][idx]
                for k in range(6):
                    if k == obj: continue
                    dec2 = planet_dec[k][idx]
                    j = 0 if dec2 > dec1 else 1     # 0 if above obj; 1 if below
                    abdiff[j][k] = abs(dec2 - dec1)
                abdiff_min[0] = min(abdiff[0])  # minimum dec separation above
                abdiff_min[1] = min(abdiff[1])  # minimum dec separation below
                #print("   {:7} {:.2f} {:.2f}".format(get_object_name(obj).upper(), abdiff_min[0], abdiff_min[1]))
                # the first choice is the preferred position...
                # 1st pick: highest minimum distance to nearest path (above or below obj)
                ab = 0 if abdiff_min[0] > abdiff_min[1] else 1
                write_label_candidate(obj, idx, ang, ab)
                label_pos.append(two_tuples[ab])
                # 2nd pick: the opposite side (above or below obj)
                ab = 1 - ab
                write_label_candidate(obj, idx, ang, ab)
                label_pos.append(two_tuples[ab])
            elif abcount == 1:  # then save the position (above or below) that worked
                write_label_candidate(obj, idx, ang, abgood)
                label_pos.append(two_tuples[abgood])
                
# .................................................................
#      based on the largest gap(s) between path crossings
#      try some label positions avoiding a path overlap: VENUS
# .................................................................

    p_sections = path_sections(obj, daystoprocess, tup_crosspoints)
    for sec_len, from_idx, to_idx, obj8, obj9 in p_sections:
        date0 = d00 + timedelta(days=from_idx)
        date1 = d00 + timedelta(days=to_idx)
        if config.debug_section_length:
            print("{} section length {:5.2f}   {} - {}   {}-{}".format(get_object_name(obj).upper(), sec_len, date0, date1, get_object_name(obj8), get_object_name(obj9)))

    if len(p_sections) >=2:
        for n in [-1,-2]:       # pick the largest two sections
            sec_len, from_idx, to_idx, obj8, obj9 = p_sections[n]
            idx = from_idx
            idx += int((to_idx-from_idx)/2)
            date0 = d00 + timedelta(days=idx)
            hdiag = hdiags[obj]     # height (in degrees) perpendiculat to label text
            
            abcount = 0             # count successful above/below positions (per segment)
            for ab in [0,1]:        # label above and below path...
                xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang = label_rectangle(obj, idx, hdiag*vab[ab])

                # check if the label overwrites neighboring declination paths
                badobj = path_overlaid_check(obj, xy, idx_min, idx_max, dec_min, dec_max, lab0, ang)
                if len(badobj) > 0:
                    if config.debug_chosen:
                        msg = ""
                        for obj0 in badobj:
                            msg += "{}, ".format(get_object_name(obj0).upper())
                        print("      {:7} (label {}) on {} overlays path: {}".format(get_object_name(obj).upper(), pab[ab], date0, msg[:-2]))
                else:
                    abcount += 1
                    abgood = ab
                    two_tuples[ab] = (obj, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang, ab)

            if abcount == 2:    # then save both (above & below) in label_pos
                # look for greatest declination separation from other planets/sun
                abdiff_min = [180.0] * 2            # abdiff_min[0 to 1]
                abdiff = [[180.0] * 6 for i in range(2)]    # abdiff[0 to 1][0 to 5]
                dec1 = planet_dec[obj][idx]
                for k in range(6):
                    if k == obj: continue
                    dec2 = planet_dec[k][idx]
                    j = 0 if dec2 > dec1 else 1     # 0 if above obj; 1 if below
                    abdiff[j][k] = abs(dec2 - dec1)
                abdiff_min[0] = min(abdiff[0])  # minimum dec separation above
                abdiff_min[1] = min(abdiff[1])  # minimum dec separation below
                #print("   {:7} {:.2f} {:.2f}".format(get_object_name(obj).upper(), abdiff_min[0], abdiff_min[1]))
                # the first choice is the preferred position...
                # 1st pick: highest minimum distance to nearest path (above or below obj)
                ab = 0 if abdiff_min[0] > abdiff_min[1] else 1
                write_label_candidate(obj, idx, ang, ab)
                label_pos.append(two_tuples[ab])
                # 2nd pick: the opposite side (above or below obj)
                ab = 1 - ab
                write_label_candidate(obj, idx, ang, ab)
                label_pos.append(two_tuples[ab])
            elif abcount == 1:  # then save the position (above or below) that worked
                write_label_candidate(obj, idx, ang, abgood)
                label_pos.append(two_tuples[abgood])


# ................................................................
#      based on fixed calendar dates ...
#      try some label positions avoiding a path overlap: MARS
# ................................................................

    # -------------------------------------------------------------
    # |  x-, y-position coordinates are in units of '10 degrees'  |
    # |  or '30 calendar days', i.e. 1 unit corresponds to the    |
    # |  chart horizontal separation lines and very close to the  |
    # |  chart monthly vertical lines.                            |
    # -------------------------------------------------------------

    # try between FEB/MAR, APR/MAY, JUN/JUL; AUG/SEP; OCT/NOV
    obj = 3         # MARS
    two_tuples = [None, None]   # store tuple to be appended to label_pos

    for mm in range(3,13,2):
        yy = d00.year
        date0 = date(int(yy), int(mm), 1)
        idx = (date0 - d00).days
        # height (in degrees) perpendiculat to label text
        hdiag = hdiags[obj]     # height (in degrees) perpendiculat to label text

        abcount = 0             # count successful above/below positions (per segment)
        for ab in [0,1]:        # label above and below path...
            xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang = label_rectangle(obj, idx, hdiag*vab[ab])
            date_min = d00 + timedelta(days=idx_min)
            date_max = d00 + timedelta(days=idx_max)
            
            # check if the label overwrites neighboring declination paths
            #tex += plot_rectangle(xy)
            #tex += plot_rectangle(rxy)
            #tex += printdot2(rx_min, 0.0)
            #tex += printdot2(rx_max, 0.0)
            #print("{} to {}".format(date_min,date_max))
            #print(dec_min, dec_max)
            badobj = path_overlaid_check(obj, xy, idx_min, idx_max, dec_min, dec_max, lab0, ang)
            if len(badobj) > 0:
                if config.debug_chosen:
                    msg = ""
                    for obj0 in badobj:
                        msg += "{}, ".format(get_object_name(obj0).upper())
                    print("      {:7} (label {}) on {} overlays path: {}".format(get_object_name(obj).upper(), pab[ab], date0, msg[:-2]))
            else:
                abcount += 1
                abgood = ab
                two_tuples[ab] = (obj, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang, ab)

        if abcount == 2:    # then save both (above & below) in label_pos
            # look for greatest declination separation from other planets/sun
            abdiff_min = [180.0] * 2            # abdiff_min[0 to 1]
            abdiff = [[180.0] * 6 for i in range(2)]    # abdiff[0 to 1][0 to 5]
            dec1 = planet_dec[obj][idx]
            for k in range(6):
                if k == obj: continue
                dec2 = planet_dec[k][idx]
                j = 0 if dec2 > dec1 else 1     # 0 if above obj; 1 if below
                abdiff[j][k] = abs(dec2 - dec1)
            abdiff_min[0] = min(abdiff[0])  # minimum dec separation above
            abdiff_min[1] = min(abdiff[1])  # minimum dec separation below
            # the first choice is the preferred position...
            # 1st pick: highest minimum distance to nearest path (above or below obj)
            ab = 0 if abdiff_min[0] > abdiff_min[1] else 1
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
#      based on fixed calendar dates ...
#      try some label positions avoiding a path overlap: JUPITER
# ...................................................................

    # -------------------------------------------------------------
    # |  x-, y-position coordinates are in units of '10 degrees'  |
    # |  or '30 calendar days', i.e. 1 unit corresponds to the    |
    # |  chart horizontal separation lines and very close to the  |
    # |  chart monthly vertical lines.                            |
    # -------------------------------------------------------------

    # try between FEB/MAR, APR/MAY, JUN/JUL; AUG/SEP; OCT/NOV
    obj = 4         # JUPITER
    two_tuples = [None, None]   # store tuple to be appended to label_pos

    for mm in range(3,13,2):
        yy = d00.year
        date0 = date(int(yy), int(mm), 1)
        idx = (date0 - d00).days
        # height (in degrees) perpendiculat to label text
        hdiag = hdiags[obj]     # height (in degrees) perpendiculat to label text
        #hdiag = -hdiags[obj] if planet_dec[4][idx] < planet_dec[5][idx] and (planet_dec[5][idx] - planet_dec[4][idx]) < 5.0 else hdiags[obj]

        abcount = 0             # count successful above/below positions (per segment)
        for ab in [0,1]:        # label above and below path...
            xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang = label_rectangle(obj, idx, hdiag*vab[ab])
            date_min = d00 + timedelta(days=idx_min)
            date_max = d00 + timedelta(days=idx_max)

            # check if the label overwrites neighboring declination paths
            badobj = path_overlaid_check(obj, xy, idx_min, idx_max, dec_min, dec_max, lab0, ang)
            if len(badobj) > 0:
                if config.debug_chosen:
                    msg = ""
                    for obj0 in badobj:
                        msg += "{}, ".format(get_object_name(obj0).upper())
                    print("      {:7} (label {}) on {} overlays path: {}".format(get_object_name(obj).upper(), pab[ab], date0, msg[:-2]))
            else:
                abcount += 1
                abgood = ab
                two_tuples[ab] = (obj, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang, ab)

        if abcount == 2:    # then save both (above & below) in label_pos
            # look for greatest declination separation from other planets/sun
            abdiff_min = [180.0] * 2            # abdiff_min[0 to 1]
            abdiff = [[180.0] * 6 for i in range(2)]    # abdiff[0 to 1][0 to 5]
            dec1 = planet_dec[obj][idx]
            for k in range(6):
                if k == obj: continue
                dec2 = planet_dec[k][idx]
                j = 0 if dec2 > dec1 else 1     # 0 if above obj; 1 if below
                abdiff[j][k] = abs(dec2 - dec1)
            abdiff_min[0] = min(abdiff[0])  # minimum dec separation above
            abdiff_min[1] = min(abdiff[1])  # minimum dec separation below
            # the first choice is the preferred position...
            # 1st pick: highest minimum distance to nearest path (above or below obj)
            ab = 0 if abdiff_min[0] > abdiff_min[1] else 1
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
#      based on fixed calendar dates ...
#      try some label positions avoiding a path overlap: SATURN
# ..................................................................

    # -------------------------------------------------------------
    # |  x-, y-position coordinates are in units of '10 degrees'  |
    # |  or '30 calendar days', i.e. 1 unit corresponds to the    |
    # |  chart horizontal separation lines and very close to the  |
    # |  chart monthly vertical lines.                            |
    # -------------------------------------------------------------

    # try between FEB/MAR, APR/MAY, JUN/JUL; AUG/SEP; OCT/NOV
    obj = 5         # SATURN
    two_tuples = [None, None]   # store tuple to be appended to label_pos

    for mm in range(3,13,2):
        yy = d00.year
        date0 = date(int(yy), int(mm), 1)
        idx = (date0 - d00).days
        # height (in degrees) perpendiculat to label text
        hdiag = hdiags[obj]     # height (in degrees) perpendiculat to label text
        #hdiag = -hdiags[obj] if planet_dec[5][idx] < planet_dec[4][idx] and (planet_dec[4][idx] - planet_dec[5][idx]) < 5.0 else hdiags[obj]

        abcount = 0             # count successful above/below positions (per segment)
        for ab in [0,1]:        # label above and below path...
            xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang = label_rectangle(obj, idx, hdiag*vab[ab])
            date_min = d00 + timedelta(days=idx_min)
            date_max = d00 + timedelta(days=idx_max)

            # check if the label overwrites neighboring declination paths
            badobj = path_overlaid_check(obj, xy, idx_min, idx_max, dec_min, dec_max, lab0, ang)
            if len(badobj) > 0:
                if config.debug_chosen:
                    msg = ""
                    for obj0 in badobj:
                        msg += "{}, ".format(get_object_name(obj0).upper())
                    print("      {:7} (label {}) on {} overlays path: {}".format(get_object_name(obj).upper(), pab[ab], date0, msg[:-2]))
            else:
                abcount += 1
                abgood = ab
                two_tuples[ab] = (obj, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang, ab)

        if abcount == 2:    # then save both (above & below) in label_pos
            # look for greatest declination separation from other planets/sun
            abdiff_min = [180.0] * 2            # abdiff_min[0 to 1]
            abdiff = [[180.0] * 6 for i in range(2)]    # abdiff[0 to 1][0 to 5]
            dec1 = planet_dec[obj][idx]
            for k in range(6):
                if k == obj: continue
                dec2 = planet_dec[k][idx]
                j = 0 if dec2 > dec1 else 1     # 0 if above obj; 1 if below
                abdiff[j][k] = abs(dec2 - dec1)
            abdiff_min[0] = min(abdiff[0])  # minimum dec separation above
            abdiff_min[1] = min(abdiff[1])  # minimum dec separation below
            # the first choice is the preferred position...
            # 1st pick: highest minimum distance to nearest path (above or below obj)
            ab = 0 if abdiff_min[0] > abdiff_min[1] else 1
            write_label_candidate(obj, idx, ang, ab)
            label_pos.append(two_tuples[ab])
            # 2nd pick: the opposite side (above or below obj)
            ab = 1 - ab
            write_label_candidate(obj, idx, ang, ab)
            label_pos.append(two_tuples[ab])
        elif abcount == 1:  # then save the position (above or below) that worked
            write_label_candidate(obj, idx, ang, abgood)
            label_pos.append(two_tuples[abgood])

# .................................................
    # print()
    # for i in range(len(label_pos)):
        # print(label_pos[i])
    # print()
# .................................................

# .................................................
#       check for label overlap conflict: SUN
# .................................................

    # -------------------------------------------------------------
    # |  x-, y-position coordinates are in units of '10 degrees'  |
    # |  or '30 calendar days', i.e. 1 unit corresponds to the    |
    # |  chart horizontal separation lines and very close to the  |
    # |  chart monthly vertical lines.                            |
    # -------------------------------------------------------------

    # check if the sun's label overwrites a neighboring label
    obj = 0         # SUN
    pos_chosen = False
    n = 0
    prev_idx = -1   # invalid value
    good_positions = []     # list contains no duplicate idx values

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
                #label[obj] = False          # for DEBUGGING
                #label[obj0] = False         # for DEBUGGING
                if config.debug_labels:
                    tex += plot_rectangle(rxy0) # for DEBUGGING
                    tex += tex0                 # for DEBUGGING
                msg += "{:2d} {}, ".format(ndx+1, get_object_name(obj0).upper())
            print("   {:7} (label {}) on {} overlays label: {}".format(get_object_name(obj).upper(), pab[ab], date0, msg[:-2]))
        else:
            min_diff = min_idx_diff(good_positions, idx)
            if min_diff <= 90: continue  # ensure sufficient idx gap
            n += 1      # count good positions
            good_positions.append((idx, index))
            chosen_label.append((obj, index))
            if config.debug_chosen: print("   {:2d} {:7} chosen".format(index+1,get_object_name(obj).upper()))
            pos_chosen = True
            prev_idx = idx      # skip second label at same idx position
            good_idx = idx      # ensure sufficient gap from last chosen position
            # note: the first of two labels at same idx is the preferred one

    if not pos_chosen:      
        print("FAILED to position label for {}".format(get_object_name(obj).upper()))

# ...................................................
#      check for label overlap conflict: MERCURY
# ...................................................

    # -------------------------------------------------------------
    # |  x-, y-position coordinates are in units of '10 degrees'  |
    # |  or '30 calendar days', i.e. 1 unit corresponds to the    |
    # |  chart horizontal separation lines and very close to the  |
    # |  chart monthly vertical lines.                            |
    # -------------------------------------------------------------

    # check if the planet's label overwrites a neighboring label
    obj = 1         # MERCURY
    pos_chosen = False
    n = 0
    good_positions = []     # list contains no duplicate idx values
    prev_idx = -1   # invalid value
    two_tuples = [None, None]   # store tuple to be appended to label_pos
    limit = len(label_pos)

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
                #label[obj] = False          # for DEBUGGING
                #label[obj0] = False         # for DEBUGGING
                if config.debug_labels:
                    tex += plot_rectangle(rxy0) # for DEBUGGING
                    tex += tex0                 # for DEBUGGING
                msg += "{:2d} {}, ".format(ndx+1, get_object_name(obj0).upper())
            if verbose:
                print("      {:7} (label {}) on {} overlays label: {}".format(get_object_name(obj).upper(), pab[ab], date0, msg[:-2]))

            # ||  AS A LAST RESORT, attampt to shift the label slightly away   ||
            # ||  from the nearest local path crossing (MERCURY<>some object)  ||
            idx_diff_val, idx_diff_min = nearest_path_crossing(idx, obj, tup_crosspoints)
            # DO NOT process items appended to label_pos within this FOR loop!!
            # AND only consider local path crossings within 30 days
            if index < limit and idx_diff_min <= 30:
                # try applying a label shift of 5 days
                label_offset = math.copysign(5.0, idx - idx_diff_val)
                idx += int(label_offset)     # try this idx offset
                date1 = d00 + timedelta(days=idx)
                hdiag = hdiags[obj]     # height (in degrees) perpendiculat to label text
                if verbose:
                    print("      {:7} label date shift {} => {}".format(get_object_name(obj).upper(),date0,date1))

                abcount = 0             # count successful above/below positions (per segment)
                for ab in [0,1]:        # label above and below path...
                    xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang = label_rectangle(obj, idx, hdiag*vab[ab])

                    # check if the label overwrites neighboring declination paths
                    badobj = path_overlaid_check(obj, xy, idx_min, idx_max, dec_min, dec_max, lab0, ang)
                    if len(badobj) > 0:
                        msg = ""
                        for obj0 in badobj:
                            msg += "{}, ".format(get_object_name(obj0).upper())
                        msg = msg[:-2]
                        if verbose:
                            print("      {:7} (label {}) on {} overlays path: {}".format(get_object_name(obj).upper(), pab[ab], date1, msg))
                
                    else:
                        abcount += 1
                        abgood = ab
                        two_tuples[ab] = (obj, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, lab0, ang, ab)

                if abcount == 2:    # then save both (above & below) in label_pos
                    # look for greatest declination separation from other planets/sun
                    abdiff_min = [180.0] * 2            # abdiff_min[0 to 1]
                    abdiff = [[180.0] * 6 for i in range(2)]    # abdiff[0 to 1][0 to 5]
                    dec1 = planet_dec[obj][idx]
                    for k in range(6):
                        if k == obj: continue
                        dec2 = planet_dec[k][idx]
                        j = 0 if dec2 > dec1 else 1     # 0 if above obj; 1 if below
                        abdiff[j][k] = abs(dec2 - dec1)
                    abdiff_min[0] = min(abdiff[0])  # minimum dec separation above
                    abdiff_min[1] = min(abdiff[1])  # minimum dec separation below
                    # the first choice is the preferred position...
                    # 1st pick: highest minimum distance to nearest path (above or below obj)
                    ab = 0 if abdiff_min[0] > abdiff_min[1] else 1
                    write_label_candidate(obj, idx, ang, ab)
                    label_pos.append(two_tuples[ab])
                    # 2nd pick: the opposite side (above or below obj)
                    ab = 1 - ab
                    write_label_candidate(obj, idx, ang, ab)
                    label_pos.append(two_tuples[ab])
                elif abcount == 1:  # then save the position (above or below) that worked
                    write_label_candidate(obj, idx, ang, abgood)
                    label_pos.append(two_tuples[abgood])
                # NOTE: it's appended to chosen_label at end of FOR loop!
        else:
            min_diff = min_idx_diff(good_positions, idx)
            if min_diff <= 90: continue  # ensure sufficient idx gap
            n += 1      # count good positions
            good_positions.append((idx, index))
            chosen_label.append((obj, index))
            if config.debug_chosen: print("   {:2d} {:7} chosen".format(index+1,get_object_name(obj).upper()))
            pos_chosen = True
            prev_idx = idx      # skip second label at same idx position
            # note: the first of two labels at same idx is the preferred one

    if not pos_chosen:
        print("FAILED to position label for {}".format(get_object_name(obj).upper()))

# ..................................................................
#  pick optimal position(s) without a label overlap conflict: VENUS
# ..................................................................

    # -------------------------------------------------------------
    # |  x-, y-position coordinates are in units of '10 degrees'  |
    # |  or '30 calendar days', i.e. 1 unit corresponds to the    |
    # |  chart horizontal separation lines and very close to the  |
    # |  chart monthly vertical lines.                            |
    # -------------------------------------------------------------

    # check if the planet's label overwrites a neighboring label
    obj = 2         # VENUS
    pos_chosen = False
    n = 0
    good_positions = []     # list contains no duplicate idx values
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
                #label[obj] = False          # for DEBUGGING
                #label[obj0] = False         # for DEBUGGING
                if config.debug_labels:
                    tex += plot_rectangle(rxy0) # for DEBUGGING
                    tex += tex0                 # for DEBUGGING
                msg += "{:2d} {}, ".format(ndx+1, get_object_name(obj0).upper())
            print("   {:7} (label {}) on {} overlays label: {}".format(get_object_name(obj).upper(), pab[ab], date0, msg[:-2]))
        else:
            min_diff = min_idx_diff(good_positions, idx)
            if min_diff <= 90: continue  # ensure sufficient idx gap
            n += 1      # count good positions
            good_positions.append((idx, index))
            #print("{} label_pos({}) {}".format(get_object_name(obj).upper(), index, pab[ab]))
            chosen_label.append((obj, index))
            if config.debug_chosen: print("   {:2d} {:7} chosen".format(index+1,get_object_name(obj).upper()))
            pos_chosen = True
            prev_idx = idx      # skip second label at same idx position
            # note: the first of two labels at same idx is the preferred one

    if not pos_chosen:      
        print("FAILED to position label for {}".format(get_object_name(obj).upper()))

# .................................................................
#  pick optimal position(s) without a label overlap conflict: MARS
# .................................................................

    # -------------------------------------------------------------
    # |  x-, y-position coordinates are in units of '10 degrees'  |
    # |  or '30 calendar days', i.e. 1 unit corresponds to the    |
    # |  chart horizontal separation lines and very close to the  |
    # |  chart monthly vertical lines.                            |
    # -------------------------------------------------------------

    # check if the planet's label overwrites a neighboring label
    obj = 3         # MARS
    pos_chosen = False
    n = 0                   # length of good_positions list
    good_positions = []     # list contains no duplicate idx values
    prev_idx = -1           # invalid value
    ydiff = [180.0] * 6

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
                #label[obj] = False          # for DEBUGGING
                #label[obj0] = False         # for DEBUGGING
                if config.debug_labels:
                    tex += plot_rectangle(rxy0) # for DEBUGGING
                    tex += tex0                 # for DEBUGGING
                msg += "{:2d} {}, ".format(ndx+1, get_object_name(obj0).upper())
            print("   {:7} (label {}) on {} overlays label: {}".format(get_object_name(obj).upper(), pab[ab], date0, msg[:-2]))
        else:
            n += 1      # count good positions
            good_positions.append((idx, index))
            prev_idx = idx      # skip second label at same idx position
            # note: the first of two labels at same idx is the preferred one
            if 181 <= idx <= 182:   # preference for JUN/JUL
                chosen_label.append((obj, index))
                if config.debug_chosen: print("   {:2d} {:7} chosen".format(index+1,get_object_name(obj).upper()))
                pos_chosen = True

    if config.debug_chosen:
        msg = '   good_positions: '
        for idx, ndx in good_positions:
            o = label_pos[ndx][0]
            msg += "{:2d} {}, ".format(ndx+1,get_object_name(o).upper())
        print(msg[:-2])

    if pos_chosen:
        for j in range(0,n):
            idx, index = good_positions[j]
            # avoid printing the label twice in positions adjacent to JUN/JUL
            if 120 <= idx <= 244: continue   # if APR/MAY, JUN/JUL or AUG/SEP
            chosen_label.append((obj, index))
            if config.debug_chosen: print("   {:2d} {:7} chosen".format(index+1,get_object_name(obj).upper()))
            pos_chosen = True
    elif n > 0:
        # look for greatest declination separation from other planets/sun
        ydiff_min = [180.0] * n
        prev_idx = -1           # invalid value
        for j in range(0,n):
            idx, index = good_positions[j]
            if idx == prev_idx: continue    # exclude duplicate idx values
            dec1 = planet_dec[obj][idx]
            for k in range(6):
                if k == obj: continue
                dec2 = planet_dec[k][idx]
                ydiff[k] = abs(dec2 - dec1)
            ydiff_min[j] = min(ydiff)
            prev_idx = idx      # skip second label at same idx position
        # get the highest minimum distance to nearest path
        j = ydiff_min.index(max(ydiff_min))
        idx, index = good_positions[j]
        chosen_label.append((obj, index))
        if config.debug_chosen: print("   {:2d} {:7} chosen".format(index+1,get_object_name(obj).upper()))
        pos_chosen = True

        # for j in range(0,n):
            # idx, index = good_positions[j]
            # if 120 <= idx <= 121 or 243 <= idx <= 244:      # if APR/MAY or AUG/SEP
                # chosen_label.append((obj, index))
                # pos_chosen = True
                # idx_chosen = idx
                # break

    # if not pos_chosen:
        # for j in range(0,n):
            # idx, index = good_positions[j]
            # # avoid printing the label twice in consecutive positions,
            # #      e.g. on 1st March and 1st May
            # if idx - prev_idx > 90:
                # chosen_label.append((obj, index))
                # pos_chosen = True
            # prev_idx = idx

    if not pos_chosen:      
        print("FAILED to position label for {}".format(get_object_name(obj).upper()))

# ....................................................................
#  pick optimal position(s) without a label overlap conflict: JUPITER
# ....................................................................

    # -----------------------------------------------------------------------
    # |  x-, y-position coordinates are in units of '10 degrees' vertically |
    # |  or '30 calendar days' horizontally, i.e. 1 unit corresponds to the |
    # |  chart horizontal separation lines and very close to the chart      |
    # |  monthly vertical lines (as not every month has 30 days).           |
    # -----------------------------------------------------------------------

    # check if the planet's label overwrites a neighboring label
    obj = 4         # JUPITER
    pos_chosen = False
    n = 0                   # length of good_positions list
    good_positions = []     # list contains no duplicate idx values
    prev_idx = -1           # invalid value

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
                #label[obj] = False          # for DEBUGGING
                #label[obj0] = False         # for DEBUGGING
                if config.debug_labels:
                    tex += plot_rectangle(rxy0) # for DEBUGGING
                    tex += tex0                 # for DEBUGGING
                msg += "{:2d} {}, ".format(ndx+1, get_object_name(obj0).upper())
            print("   {:7} (label {}) on {} overlays label: {}".format(get_object_name(obj).upper(), pab[ab], date0, msg[:-2]))
        else:
            # ||  as the path is relatively straight, one label is  ||
            # ||  sufficient if placed APR/MAY, JUN/JUL or AUG/SEP  ||
            n += 1      # count good positions
            good_positions.append((idx, index))
            if 181 <= idx <= 182:   # preference for JUN/JUL
                chosen_label.append((obj, index))
                if config.debug_chosen: print("   {:2d} {:7} chosen".format(index+1,get_object_name(obj).upper()))
                pos_chosen = True
                prev_idx = idx      # skip second label at same idx position
                # note: the first of two labels at same idx is the preferred one

    if not pos_chosen:
        prev_idx = -1           # invalid value
        for j in range(0,n):
            idx, index = good_positions[j]
            if idx == prev_idx: continue    # don't print above & below for the same idx
            if 120 <= idx <= 121 or 243 <= idx <= 244:   # if APR/MAY or AUG/SEP
                chosen_label.append((obj, index))
                if config.debug_chosen: print("   {:2d} {:7} chosen".format(index+1,get_object_name(obj).upper()))
                pos_chosen = True
                prev_idx = idx      # skip second label at same idx position
                # note: the first of two labels at same idx is the preferred one

    if not pos_chosen:      
        # then pick two non-adjacent positions if possible, otherwise one position
        if n >= 1:
            idx1, index = good_positions[0]
            chosen_label.append((obj, index))
            if config.debug_chosen: print("   {:2d} {:7} chosen".format(index+1,get_object_name(obj).upper()))
            pos_chosen = True
        if n >= 2:
            idx2, index = good_positions[-1]
            if idx2 - idx1 > 31:
                chosen_label.append((obj, index))
                if config.debug_chosen: print("   {:2d} {:7} chosen".format(index+1,get_object_name(obj).upper()))

    if not pos_chosen:      
        print("FAILED to position label for {}".format(get_object_name(obj).upper()))

# ...................................................................
#  pick optimal position(s) without a label overlap conflict: SATURN
# ...................................................................

    # -------------------------------------------------------------
    # |  x-, y-position coordinates are in units of '10 degrees'  |
    # |  or '30 calendar days', i.e. 1 unit corresponds to the    |
    # |  chart horizontal separation lines and very close to the  |
    # |  chart monthly vertical lines.                            |
    # -------------------------------------------------------------

    # check if the planet's label overwrites a neighboring label
    obj = 5         # SATURN
    pos_chosen = False
    n = 0                   # length of good_positions list
    good_positions = []     # list contains no duplicate idx values
    prev_idx = -1           # invalid value

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
                #label[obj] = False          # for DEBUGGING
                #label[obj0] = False         # for DEBUGGING
                if config.debug_labels:
                    tex += plot_rectangle(rxy0) # for DEBUGGING
                    tex += tex0                 # for DEBUGGING
                msg += "{:2d} {}, ".format(ndx+1, get_object_name(obj0).upper())
            print("   {:7} (label {}) on {} overlays label: {}".format(get_object_name(obj).upper(), pab[ab], date0, msg[:-2]))
        else:
            # ||  as the path is relatively straight, one label is  ||
            # ||  sufficient if placed APR/MAY, JUN/JUL or AUG/SEP  ||
            n += 1      # count good positions
            good_positions.append((idx, index))
            if 181 <= idx <= 182:   # preference for JUN/JUL
                chosen_label.append((obj, index))
                if config.debug_chosen: print("   {:2d} {:7} chosen".format(index+1,get_object_name(obj).upper()))
                pos_chosen = True
                prev_idx = idx      # skip second label at same idx position
                # note: the first of two labels at same idx is the preferred one

    if not pos_chosen:
        prev_idx = -1           # invalid value
        for j in range(0,n):
            idx, index = good_positions[j]
            if idx == prev_idx: continue    # don't print above & below for the same idx
            if 120 <= idx <= 121 or 243 <= idx <= 244:   # if APR/MAY or AUG/SEP
                chosen_label.append((obj, index))
                if config.debug_chosen: print("   {:2d} {:7} chosen".format(index+1,get_object_name(obj).upper()))
                pos_chosen = True
                prev_idx = idx      # skip second label at same idx position
                # note: the first of two labels at same idx is the preferred one

    if not pos_chosen:      
        # then pick two non-adjacent positions if possible, otherwise one position
        if n >= 1:
            idx1, index = good_positions[0]
            chosen_label.append((obj, index))
            if config.debug_chosen: print("   {:2d} {:7} chosen".format(index+1,get_object_name(obj).upper()))
            pos_chosen = True
        if n >= 2:
            idx2, index = good_positions[-1]
            if idx2 - idx1 > 31:
                chosen_label.append((obj, index))
                if config.debug_chosen: print("   {:2d} {:7} chosen".format(index+1,get_object_name(obj).upper()))

    if not pos_chosen:      
        print("FAILED to position label for {}".format(get_object_name(obj).upper()))

# ........................................................

    if verbose:
        print("   ========== {} chosen labels ==========".format(len(chosen_label)))
        msg = '   '
        for o, ndx in chosen_label:
            msg += "{:2d} {}, ".format(ndx+1,get_object_name(o).upper())
        print(msg[:-2])

# ==========================================================================
# ========== finally ... PRINT CHOSEN LABELS ON DECLINATION PATHS ==========
# ==========================================================================

    # print the label(s) for SUN
    obj = 0
    txt = r"\textbf{SUN}"
    for o, ndx in chosen_label:
        if o != obj: continue
        obj9, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, labXY, ang, ab = label_pos[ndx]
        #tex += printlabel(txt, idx, hdiag, planet_dec[obj])
        tex += printlabelXY(txt, labXY, ang)

    # ---- print label(s) for MERCURY ----
    obj = 1
    txt = r"\textbf{MERCURY}"
    for o, ndx in chosen_label:
        if o != obj: continue
        obj9, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, labXY, ang, ab = label_pos[ndx]
        #tex += printlabel(txt, idx, hdiag, planet_dec[obj])
        tex += printlabelXY(txt, labXY, ang)

    # ---- print label(s) for VENUS ----
    obj = 2
    txt = r"\textbf{VENUS}"
    for o, ndx in chosen_label:
        if o != obj: continue
        obj9, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, labXY, ang, ab = label_pos[ndx]
        #tex += printlabel(txt, idx, hdiag, planet_dec[obj])
        tex += printlabelXY(txt, labXY, ang)

    # ---- print label mid-position: MARS ----
    obj = 3
    txt = r"\textbf{MARS}"
    for o, ndx in chosen_label:
        if o != obj: continue
        obj9, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, labXY, ang, ab = label_pos[ndx]
        tex += printlabelXY(txt, labXY, ang)

    # ---- print label mid-position: JUPITER ----
    obj = 4
    txt = r"\textbf{JUPITER}"
    for o, ndx in chosen_label:
        if o != obj: continue
        obj9, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, labXY, ang, ab = label_pos[ndx]
        #tex += printlabel(txt, idx, hdiag, planet_dec[obj])
        tex += printlabelXY(txt, labXY, ang)

    # ---- print label mid-position: SATURN ----
    obj = 5
    txt = r"\textbf{SATURN}"
    for o, ndx in chosen_label:
        if o != obj: continue
        obj9, idx, xy, rxy, idx_min, idx_max, dec_min, dec_max, labXY, ang, ab = label_pos[ndx]
        #tex += printlabel(txt, idx, hdiag, planet_dec[obj])
        tex += printlabelXY(txt, labXY, ang)

    return tex

# --------------------------------------------------
# --------------  REQUIRED  FUNCTIONS --------------
# --------------------------------------------------

def label_rectangle(obj, idx, hdiag):
# determine the rectangle encosing the label + its white background
    global planet_dec, txt_wdth, txt_hgt, boxsep, pt2cm

    # PLANET position
    planet_decl = planet_dec[obj][idx]
    obj_x = idx/30
    obj_y = planet_decl/10

    # label rotation angle
    ydiff = planet_dec[obj][idx+3] - planet_dec[obj][idx-3]
    ang = math.atan((ydiff/10)/(6.0/30))    # radians
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
    idx_min = math.floor(rx_min*30/sf)
    idx_max = math.ceil(rx_max*30/sf)
    
    # get limits of y range (in degrees)
    ry_min = min([y[1] for y in rxy])*10/sf
    ry_max = max([y[1] for y in rxy])*10/sf

    return xy, rxy, idx_min, idx_max, ry_min, ry_max, lab0, ang

def path_overlaid_check(obj, xy, idx_min, idx_max, dec_min, dec_max, lab0, ang):
    # test if any planet coordinates are overlaid by label rectangle
    global planet_dec

    x0 = lab0[0]
    y0 = lab0[1]
    badobj = []     # list of offending objects

    # NOTE: A MERCURY label can overlay its own path!
    for o in range(6):  # for each object (sun/planet)
        ####if o == obj: continue   # skip the current object
        for n in range(idx_min, idx_max+1):     # scan relevant dates
            if dec_min < planet_dec[o][n] < dec_max:
                # test if point is within label rectangle...
                # ||  rotate the point about the label center  ||
                # ||   back to where the label is horizontal   ||
                dx = n/30*sf - x0
                dy = planet_dec[o][n]/10*sf - y0
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

    # UNROTATED box limits for obj0:
    x0_min = xy0[0][0]
    x0_max = xy0[2][0]
    y0_min = xy0[0][1]
    y0_max = xy0[1][1]
    date_obj0 = d00 + timedelta(days=labXY0[0]/sf*30)
    #print("checking if any label overlaid by {} on {}, dec = {:7.3f}".format(get_object_name(obj0).upper(),date_obj0,labXY0[1]/sf*10))
    #print("x0_min = {:.2f} x0_max = {:.2f} y0_min = {:.2f} y0_max = {:.2f}".format(x0_min,x0_max,y0_min,y0_max))
    
    tex = ''
    badobj = []     # list of offending objects

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
        if abs(labXY[0] - labXY0[0])/sf*30 > 45.0: continue
        if abs(labXY[1] - labXY0[1])/sf*10 > 15.0: continue
        # overlap possible: the label centers are within 15 degrees or 45 calendar days

        # ||  to compare against UNROTATED obj0 box limits we need  ||
        # ||  to rotate obj's coordinates by -ang0 about labXY0     ||
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

def plot_rectangle(xy):
# draw a rectangle (for debugging purposes)

    tex = r"""
  \draw[ultra thin] ({:.4f},{:.4f}) -- ({:.4f},{:.4f}) -- ({:.4f},{:.4f}) -- ({:.4f},{:.4f}) -- cycle;
""".format(xy[0][0], xy[0][1], xy[1][0], xy[1][1], xy[2][0], xy[2][1], xy[3][0], xy[3][1])
    return tex

def label_clearance_check(obj, idx, test_obj, test_idx):
# check if the label overwrites a neighboring declination path crossing .....
    global planet_dec, hdiags, txt_wdth, txt_hgt, boxsep, pt2cm

    clash = False
    # PLANET position
    planet_decl = planet_dec[obj][idx]
    obj_x = idx/30
    obj_y = planet_decl/10

    # coordinates of test position
    test_dec = planet_dec[test_obj][test_idx]
    test_x = test_idx/30
    test_y = test_dec/10

    # label rotation angle
    ydiff = planet_dec[obj][idx+3] - planet_dec[obj][idx-3]
    ang = math.atan((ydiff/10)/(6.0/30))    # radians
    rot = "%0.3f" %(ang*todegrees)

    # label shift (label center position - planet position)
    xoffset = hdiags[obj]*math.sin(-ang)
    yoffset = hdiags[obj]*math.cos(-ang)

    # PLANET label center position
    x0 = (xoffset/10 + obj_x)*sf
    y0 = (yoffset/10 + obj_y)*sf
    dx0 = test_x*sf - x0

    # simulate rotating the test coordinate by '-ang' about the
    # label center position so that the label is horizontal
    # and still on the identical label center position.
    # (we know the dimensions of the unrotated label)
    dy1 = test_y*sf - y0
    #dy1 = tup[i][3]/10 - y0
    #dy2 = tup[i][4]/10 - y0
    new_x = x0 + math.cos(-ang) * (dx0) - math.sin(-ang) * (dy1)
    new_y = y0 + math.sin(-ang) * (dx0) + math.cos(-ang) * (dy1)

    # check if the label would overlap the test position
    wdth = txt_wdth[obj]/2*pt2cm
    hgt  = ((txt_hgt/2)+boxsep)*pt2cm
    within_x = x0 - wdth < new_x < x0 + wdth
    within_y = y0 - hgt < new_y < y0 + hgt

    tex = ""
    errmsg = ""
    if within_x and within_y:
        tex += printlabel(get_object_name(obj).upper(), idx, hdiags[obj], planet_dec[obj], True, True)
        tex += printdot2(new_x, new_y)
        clash = True
        errmsg = "  label mid-point x0  = {:6.2f}".format(x0*30/sf)
        errmsg += "  y0  = {:6.2f}".format(y0*10/sf)
        errmsg += "\n  new_x  = {:6.2f}".format(new_x*30/sf)
        errmsg += "  new_y  = {:6.2f}".format(new_y*10/sf)
        errmsg += "\n  test_idx  = {:d}".format(test_idx)
        errmsg += "  dx0  = {:6.2f}".format(dx0)
        errmsg += "  dy1 = {:6.2f}".format(dy1)
        #errmsg += "  dy2 = {:6.2f}".format(dy2)

    return clash, tex, errmsg

def declination_intersections(dmax):
# collect all declination path crossing intersections
    global planet_dec

    # return a list of tuples with these values per intersection:
    # [0] - n, the date offset from Jan 1
    # [1] - j, object 1 that intersects with ...
    # [2] - k, object 2 (k > j always)
    # [3] - jdec, the declination (-30.0 < dec < 30.0) object 1
    # [4] - kdec, the declination (-30.0 < dec < 30.0) object 2

    all_n = []
    all_j = []
    all_k = []
    all_jdec = []
    all_kdec = []

    for j in range(6):
        for k in range(j+1, 6):
            n = 0
            d_inc = d00
            prev_hilo = None
            
            while n <= dmax:
                DECLdiff = planet_dec[j][n] - planet_dec[k][n]
                hilo = math.copysign(1.0, DECLdiff)
                if n != 0:
                    if hilo != prev_hilo:
                        # store only the previous day (before the paths cross)
                        all_j.append(j)
                        all_k.append(k)
                        all_n.append(n-1)   # previous day...
                        all_jdec.append(planet_dec[j][n-1])
                        all_kdec.append(planet_dec[k][n-1])

                prev_hilo = hilo
                n += 1
                d_inc += timedelta(days=1)

    #tup = list(zip(all_n, all_dec, all_j, all_k))
    tup = list(zip(all_n, all_j, all_k, all_jdec, all_kdec))
    tup.sort(key = lambda x: x[0])  # sort by n, the date offset from Jan 1

    if config.debug_crossing:
        print("\n       Sun & Planet crossing points...")
        for i in range(len(tup)):
            idx, j, k, jdec, kdec = tup[i]
            date0 = d00 + timedelta(days=idx)
            print("       {}   {:7}-{:7}".format(date0,get_object_name(j),get_object_name(k)))

    return tup

def path_sections(obj, daystoprocess, tup):
# find longest sections between paths crossing the 'obj' path.
# The section length is the straight line length between the two
# crossing points, taking the date and declination into account.
# in units '30 calendar days' horizontally or 10 degrees vertically.
# in units '3 calendar days' horizontally or degrees vertically.
    global planet_dec
    sections = []
    from_idx = 0
    dec0 = planet_dec[obj][0]
    obj8 = -1       # path section is from obj8 to obj9
    
    # note: tup is sorted by increasing date offset from Jan 1
    for i in range(len(tup)):
        if tup[i][1] == obj or tup[i][2] == obj:
            k = 3 if tup[i][1] == obj else 4
            obj9 = tup[i][2] if tup[i][1] == obj else tup[i][1]
            to_idx = tup[i][0]
            dec1 = tup[i][k]
            sec_len = math.sqrt(((to_idx-from_idx)/3)**2 + (dec1-dec0)**2)
            sections.append((sec_len, from_idx, to_idx, obj8, obj9))    # append tuple
            from_idx = to_idx   # prepare for next section
            dec0 = dec1         # prepare for next section
            obj8 = obj9

    # append final section
    to_idx = daystoprocess - 1
    dec1 = planet_dec[obj][to_idx]
    sec_len = math.sqrt(((to_idx-from_idx)/3)**2 + (dec1-dec0)**2)
    sections.append((sec_len, from_idx, to_idx, obj8, -1))    # append tuple
    sections.sort(key = lambda x: x[0])  # sort by sec_len ascending
    # return list of tuples (sec_len, from_idx, to_idx)
    # sorted by sec_len, the section length, low to high.
    return sections

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

def printdot(xpos, ypos, tf= True):
    # x units in days; y units in degrees
    c = 'red' if tf else 'blue'
    tex = r"""
  \fill[color={}] ({:.4f}, {:.4f}) circle (1pt);""".format(c, xpos*sf/30, ypos*sf/10)
    return tex

def printdot2(xpos, ypos, tf= True):
    # x units in cm; y units in cm (scaled)
    c = 'red' if tf else 'blue'
    tex = r"""
  \fill[color={}] ({:.4f}, {:.4f}) circle (1pt);""".format(c, xpos, ypos)
    return tex

def printlabel(txt, idx, hdiag, obj_dec, val=True, debug=False):
# print a label using date, label offset & a list of planet declinations

    c = 'Black' if val else 'Red'   # print invalid labels RED
    #d_mid = d00 + timedelta(days=idx)
    ydiff = obj_dec[idx+3] - obj_dec[idx-3]
    ang = math.atan((ydiff/10)/(6.0/30))    # radians
    rot = "%0.3f" %(ang*todegrees)
    if debug: rot = "0.0"   # print label text unrotated

    # label position is most accurately specified as ...
    ldiag = 0.0     # length along diagonal (before scaling)
    # hdiag         = height perpendiculat to label text (before scaling)
    xoffset = hdiag*math.sin(-ang) + ldiag*math.cos(-ang)
    yoffset = hdiag*math.cos(-ang) - ldiag*math.sin(-ang)
    x0 = (xoffset/10 + (idx/30)) * sf
    y0 = (yoffset/10 + (obj_dec[idx]/10)) * sf
    #print(txt, ydiff, rot, xoffset, yoffset)

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
    return tex

def printlabelXY(txt, labXY, ang, val=True, debug=False):
# print a label using XY coordinates and rotation angle

    c = 'Black' if val else 'Red'   # print invalid labels RED
    rot = "%0.3f" %(ang*todegrees)
    if debug: rot = "0.0"   # print label text unrotated
    x0 = labXY[0]
    y0 = labXY[1]

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
    return tex

def write_label_candidate(obj, idx, ang, label_ab=0):
# output a console message that a candidate label position has been found
# label_ab = 0 if label above path;   = 1 if below path

    if not verbose: return
    global planet_dec, label_ndx
    p = ['above', 'below']
    label_ndx += 1
    test_date = d00 + timedelta(days=idx)
    test_dec = planet_dec[obj][idx]
    print("   {:2d} {:7} (label {}) on {} decl {:6.2f} ang {:6.2f}°".format(label_ndx, get_object_name(obj).upper(), p[label_ab], test_date, test_dec, ang*todegrees))
    return

def min_idx_diff(good_pos, new_idx):
#find the minimum difference between new_idx and all values in good_pos
    min_diff = 365  # theoretical maximum
    for idx, index in good_pos:
        idx_diff = abs(new_idx - idx)
        if idx_diff < min_diff: min_diff = idx_diff
    return min_diff


#--------------------------
#   external entry point
#--------------------------

def buildchart1(d0, daystoprocess, v, page1=False):
# DECLINATION OF SUN AND PLANETS  chart

    # define global VARIABLES
    global verbose
    verbose = v
    global d00
    d00 = d0        # initialize the starting date
    global label_ndx
    label_ndx = 0   # this must be reset

    # tikz line thickness...
    # ultra thin    = 0.1pt
    # very thin     = 0.2pt
    # thin          = 0.4pt (default)
    # semithick     = 0.6pt
    # thick         = 0.8pt
    # very thick    = 1.2pt
    # ultra thick   = 1.6pt

    print("\n       Creating Declination Chart for {}".format(d0.year))
    if page1:
        tex = ""
    else:
        tex = r"""
\newpage"""

    tex += chart_DecOfSunAndPlanets(daystoprocess)

# -------------- terminate TikZ picture --------------

    tex += r"""
\end{tikzpicture}
\end{center}"""

    # A4/Letter landscape (center vertically)
    tex += r"""
  \vfill
  \hspace{0pt}"""
    return tex