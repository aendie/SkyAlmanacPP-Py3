#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

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

# ================ EDIT LINES IN THIS SECTION for PPchart.py  ================

# latitudes to print when all are required (-60 <= latitude <= 72):
lat_list = [-60.0, -58.0, -55.0, -50.0, -45.0, -40.0, -30.0, -15.0, 0.0, 15.0, 30.0, 40.0, 45.0, 50.0, 55.0, 58.0, 60.0, 62.0, 63.0, 64.0, 65.0, 66.0, 67.0, 68.0, 69.0, 70.0, 71.0, 72.0]

# choose an ephemeris (ephndx = 0, 1, 2, 3 or 4):
#   0   de421.bsp   1900 to 2050
#   1   de405.bsp   1600 to 2200
#   2   de406.bsp   1000 to 2750 (Equation of Time may show ??:?? after 2750)
#   3   de430t.bsp  1550 to 2650
#   4   de440.bsp   1550 to 2650
ephndx = 0

pgsz = 'A4'     # page size 'A4' or 'Letter' (global variable)
useIERS = False  # 'True' to download finals2000A.all; 'False' to use built-in UT1 tables
ageIERS = 30    # download a new finals2000A.all version after 'ageIERS' days
MULTIpr = True  # 'True' enables multiprocessing; otherwise only 1 logical processor is used

# ================ DO NOT EDIT LINES BELOW HERE ================

# global variables initialized during main program startup (and on every spawned process)
CPUcores = 1        # CPU core count
WINpf = False       # system platform
LINUXpf = False     # system platform
MACOSpf = False     # system platform
DPonly = False      # process data pages only
PVonly = False      # create planet visibility charts only
plotSS = False      # plot sunrise/sunset at 51.5° N
plotUN = False      # also plot Uranus and Neptune
PV_nsa = False      # PV chart: 'True' to disable gold 'planet above horizon with Sun' shading
PV_nsb = False      # PV chart: 'True' to disable gray 'planet below horizon' shading
PV_nsdah = False    # PV chart: 'True' to disable gold 'all day above horizon' shading
PV_nsdbh = False    # PV chart: 'True' to disable gray 'all day below horizon' shading
PV_df  = False      # 'True' to log 'above horizon' shading for 'scan the RISE segment forwards'
PV_db  = False      # 'True' to log 'above horizon' shading for 'scan matching SET segment backwards'
orthogonal = False  # 'True' to print all data for a day vertically at start of day...
    #   (technically incorrect above 00h but practical for debugging/regression testing)
    # ... thus Civil Dawn&Dusk + planet RISE&SET + Meridian Passage data is slanting right by 0.238731033 degrees.
    #   ( 1 hour vertically and 10 calendar days horizontally have the same length )

ephemeris = [['de421.bsp',1900,2050],['de405.bsp',1600,2200],['de406.bsp',1000,2750],['de430t.bsp',1550,2650],['de440.bsp',1550,2650]]
objnames = ['Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune']

# 'True' on 'debug_....' variables expands the terminal/console output
debug_labels = False        # 'True' to print 'label_overlaid_check' data
debug_section_length = False    # 'True' to print path section lengths in Declination Chart
debug_chosen = False        # 'True' to print chosen labels in Declination Chart
debug_crossing = False      # 'True' to print all MerPass path crossing points
debug_scipy = False         # 'True' to print planet Conjunctions and Oppositions (for Planet Diagram page 2)
debug_magnitude = False     # 'True' to print planet magnitudes
debug_visibility = False    # 'True' to print planet visibility over the year
debug_Rsegments = False     # 'True' to print rise segment coordinates
debug_Ssegments = False     # 'True' to print set segment coordinates
debug_00h_contour = False   # 'True' to print contours along 00h during noDAWN
debug_24h_contour = False   # 'True' to print contours along 24h during noDUSK