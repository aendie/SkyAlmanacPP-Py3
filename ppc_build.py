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
#from collections import deque

###### Third party imports ######
#from skyfield.api import Star, load
#from skyfield.data import hipparcos

###### Local application imports ######
import config
from pp_skyfield import pp_init_sf, MerPass
from ppc_buildchart1 import buildchart1
from ppc_buildchart2 import buildchart2, chart2page2
from ppc_buildchart3 import buildchart3, introchart3, gettccdata

#   Note to those who read this . . .
#     Although use of global variables is frowned upon by the Python community,
#     I have chosen to employ global variables in this module to reduce the
#     number of arguments passed to some functions, so that the function
#     arguments focus on the frequently changing parameters.
#     A comment before a function describes which global variables are used.
#     . . . and Murphy whispered in his sleep "If it works, don't touch it"

# global VARIABLES
MPd00 = -1      # Meridian Passage data - year (datetime)
MPobj = -1      # Meridian Passage data - planet
#shamin = shamax = sharng = None
#decmin = decmax = None
#label_ndx = 0

# global CONSTANTS  (these values are not changed)
degree_sign= u'\N{DEGREE SIGN}'

#---------------------------
#   Module initialization
#---------------------------

def init_A4(spad):
    # initialize variables for this module
    global ts                   # buildchart2() and chart2page2() require 'ts'
    ts = pp_init_sf(spad)       # in pp_skyfield

    global sf
    # NOTE!: these scaling values must match those in ppc_buildchart3.buildchart3
    if config.pgsz == "A4":
        sf = 1.39 * 0.5 # scale factor (0.695cm to 1 hour or 10 calendar days)
    else:
        sf = 1.32 * 0.5 # scale factor (0.66 cm to 1 hour or 10 calendar days)

    ## A4/Letter LANDSCAPE ##
    global const_fs
    const_fs = "large"          # constellation name fontsize (12pt)
    global navstar_fs
    navstar_fs = "normalsize"   # navigational star fontsize (10pt)
    #navstar_fs = "fontsize{6pt}" # navigational star fontsize (6pt)
    global navnum_fs
    navnum_fs = "Large"         # navigational starnum fontsize (14.4pt)
    global star_fs
    star_fs = "footnotesize"    # star fontsize (8pt)
    global title_fs
    title_fs ="Large"           # title, SHA, DEC fontsize (14.4pt)
    global ns_fs
    ns_fs = "large"             # North, South fontsize (12pt)

    return


#---------------------------------
#   PDF initialization
#---------------------------------

def beginPDF(ori, tm, bm, lm, rm):

# ---------- DOCUMENT INITIALIZATION ----------
    tex = r"""\pdfminorversion=4
\documentclass[10pt, %s]{report}
\usepackage[utf8]{inputenc}
\usepackage[english]{babel}
%%\usepackage[T1]{fontenc}
\usepackage{fontenc}    %% tikz fonts are clearer than with [T1]
%%\usepackage{textcomp}
%%\usepackage{gensymb}
\usepackage{url}""" %(ori)

    if config.pgsz == "Letter":
        tex += r"""
\usepackage{setspace}
\setstretch{0.96}"""

    # to troubleshoot add "showframe, verbose," in \usepackage[...]{geometry} below:
    tex += r"""
\usepackage[top=%s, bottom=%s, left=%s, right=%s]{geometry}
\usepackage[svgnames]{xcolor}
\usepackage{multicol}
\usepackage{parskip}    %% required for vertical paragraph separation
\definecolor{darkTan}{rgb}{0.65, 0.41, 0.10}
\definecolor{consGrey}{rgb}{0.82, 0.82, 0.82}
\definecolor{ColumbiaBlue}{rgb}{0.61, 0.87, 1.0}
\definecolor{airforceBlue}{rgb}{0.36, 0.54, 0.66}
\definecolor{amaranth}{rgb}{0.9, 0.17, 0.31}
\definecolor{azure}{rgb}{0.0, 0.5, 1.0}
\definecolor{blue2}{rgb}{0.01, 0.28, 1.0}
\definecolor{PastelOrange}{rgb}{1.0, 0.7, 0.28}
\definecolor{Bronze}{rgb}{0.8, 0.5, 0.2}
\definecolor{OliveDrab}{rgb}{0.42, 0.56, 0.14}
%%colours for Lunar Distance lines...
\definecolor{Dark chestnut}{rgb}{0.6, 0.41, 0.38}
\definecolor{Green (pigment)}{rgb}{0.0, 0.65, 0.31}
\definecolor{Gold (metallic)}{rgb}{0.83, 0.69, 0.22}
\definecolor{Celestial blue}{rgb}{0.29, 0.59, 0.82}
\definecolor{Dark turquoise}{rgb}{0.0, 0.79, 0.79}
\definecolor{Rose pink}{rgb}{1.0, 0.4, 0.8}
\definecolor{Orange (color wheel)}{rgb}{1.0, 0.5, 0.0}
\definecolor{Lavender indigo}{rgb}{0.58, 0.34, 0.92}
\definecolor{khaki}{rgb}{0.76, 0.69, 0.57}
\usepackage[inline]{enumitem}
\usepackage{booktabs}
%%\usepackage{tabularx}
\usepackage{multirow}
\usepackage{array}
\newcolumntype{L}[1]{>{\raggedright\let\newline\\\arraybackslash\hspace{0pt}}m{#1}}
\newcolumntype{C}[1]{>{\centering\let\newline\\\arraybackslash\hspace{0pt}}m{#1}}
\newcolumntype{R}[1]{>{\raggedleft\let\newline\\\arraybackslash\hspace{0pt}}m{#1}}
%%\usepackage{scrextend}
%%\makeatletter
%%\newcommand\footnoteref[1]{\protected@xdef\@thefnmark{\ref{#1}}\@footnotemark}
%%\makeatother
\usepackage[pdftex]{graphicx}	%% for \includegraphics
\usepackage{tikz}				%% for \draw  (load after 'graphicx')
%%\showboxbreadth=50  %% use for logging
%%\showboxdepth=50    %% use for logging
\usepackage{tcolorbox}          %% to apply a background color to text (load after 'tikz')
\usetikzlibrary{decorations.text,fpu}   %% to print text on a curve
%%\usetikzlibrary{spath3}         %% for saving and reusing paths
%%\usetikzlibrary{decorations.pathmorphing}
\DeclareUnicodeCharacter{00B0}{\ensuremath{{}^\circ}}""" %(tm,bm,lm,rm)
# ---------- END DOCUMENT INITIALIZATION ----------

    tex += r'''
\begin{{document}}
  \thispagestyle{{empty}}         % no page number
  \newlength{{\myw}}              % for \tcolorbox
  \newlength{{\myh}}              % for \tcolorbox
  \newlength{{\myd}}              % for \tcolorbox
  \newlength{{\myl}}              % for \tcolorbox
  %\renewcommand{{\sfdefault}}{{cmss}}
  \newcommand*{{\PMstyle}}{{\sffamily\{}\color{{MediumBlue}}}}
  \newcommand*{{\AMstyle}}{{\sffamily\{}\color{{DarkRed}}}}'''.format(navstar_fs, navstar_fs)

    return tex

def Page1(tm1, bm1, lm1, rm1):

    tex = r'''
  % for the first page only...
  \newgeometry{{nomarginpar, top={}, bottom={}, left={}, right={}}}'''.format(tm1,bm1,lm1,rm1)

    # NOTE: to center text vertically on a page:
    #  https://tex.stackexchange.com/questions/2326/vertically-center-text-on-a-page
    # NOTE: \vspace{height} does not add vertical spacing at the beginning
    #       or end of a page unless an asterisk is appended to 'vspace'
    # NOTE: do not use '\centerline{\large\textbf{....}}}\\[-6pt]' below as
    #       this causes 'Underfull \hbox (badness 10000)'; use \begin{center}
    # NOTE: \\ at the end of a paragraph causes spectacularly bad output with an empty,
    #       maximally underfull, box, and so you get a warning about badness 10000.
    #       ( >>> according to David Carlisle <<< )
    # >>>>> start new paragraphs by leaving an empty line in your TeX code.

    tex += r'''
  \setcounter{page}{2}    % otherwise it's 1
  \noindent
  \vspace*{\fill}
  \begin{center}
  \Large\textbf{Phenomena - Visibility of Planets}
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
  The Planet Diagram shows, in graphical form for any date during the year, the local mean times of meridian passage of the Sun, of the five planets, Mercury, Venus, Mars, Jupiter and Saturn, and of every 2\textsuperscript{h} of right ascension.
  Intermediate lines, corresponding to particular stars, may be drawn in by the user if desired.
  The diagram is intended to provide a general picture of the availability of planets and stars for observation during the year.\footnote{``Astronomical Phenomena'' from The Nautical Almanac Office, United States Naval Observatory and Her Majesty's Nautical Almanac Office, United Kingdom Hydrographic Office}
'''

    tex += r'''
  \noindent
  On each side of the line marking the time of meridian passage of the Sun, a band 45\textsuperscript{m} wide is shaded to indicate that planets and most stars crossing the meridian within 45\textsuperscript{m} of the Sun are generally too close to the Sun for observation.\footnotemark[1]
'''

    tex += r'''
  \noindent
  For any date the diagram provides immediately the local mean time of meridian passage of the Sun, planets and stars, and thus the following information:\footnotemark[1]
  \begin{enumerate}[topsep=2pt,noitemsep,label=\emph{\alph*})]
  \item whether a planet or star is too close to the Sun for observation;
  \item visibility of a planet or star in the morning or evening;
  \item location of a planet or star during twilight;
  \item proximity of planets to stars or other planets.
  \end{enumerate}'''

    tex += r'''
  \vspace{6.5pt}\noindent %% 6.5pt if topsep (above) is 2pt and parsep 8pt
  When the meridian passage of a body occurs at midnight, it is close to opposition to the Sun and is visible all night, and may be observed in both morning and evening twilights.
  As the time of meridian passage decreases, the body ceases to be observable in the morning, but its altitude above the eastern horizon during evening twilight gradually increases until it is on the meridian at evening twilight.
  From then onwards the body is observable above the western horizon, its altitude at evening twilight gradually decreasing, until it becomes too close to the Sun for observation.
  When it again becomes visible, it is seen in the morning twilight, low in the east.
  Its altitude at morning twilight gradually increases until meridian passage occurs at the time of morning twilight, then as the time of meridian passage decreases to 0\textsuperscript{h}, the body is observable in the west in the morning twilight with a gradually decreasing altitude, until it once again reaches opposition.\footnotemark[1]
'''

    tex += r'''
  \noindent
  Notes on the visibility of the planets are given following the Planet Diagram. Further information on the visibility of planets may be obtained from the diagram "DECLINATION OF SUN AND PLANETS" below which shows, in graphical form for any date during the year, the declinations of the bodies plotted on the Planet Diagram further below.\footnotemark[1]
'''

    tex += r'''
  \noindent
  The superior planets (Mars, Jupiter, Saturn) have four visibility phenomena:\footnote{Computation of Visibility Phenomena: (\url{https://web.archive.org/web/20200220193243/http://www.alcyone.de/plsv/documentation/compphen.html})}
  \begin{enumerate}[topsep=2pt,noitemsep]
  \item First visibility or heliacal rising: the first visibility of the planet in the east before sunrise following conjunction with the sun.
  \item Last visibility or heliacal setting: the last visibility of the planet in the west after sunset preceding conjunction with the sun.
  \item Acronychal or evening rising: the last evening the planet is seen to rise in the east following sunset, which usually occurs before opposition to the sun.
  \item Cosmical or morning setting: the first morning the planet is seen to set in the west before sunrise, which usually occurs after opposition to the sun.
  \end{enumerate}'''

    tex += r'''
  \vspace{6.5pt}\noindent %% 6.5pt if topsep (above) is 2pt and parsep 8pt
  The inferior planets (Mercury, Venus) have four visibility phenomena:\footnotemark[2]
  \begin{enumerate}[topsep=2pt,noitemsep]
  \item First visibility in the evening: the first visibility of the planet in the west after sunset following superior conjunction with the sun.
  \item Last visibility in the evening: the last visibility of the planet in the west after sunset preceding inferior conjunction with the sun.
  \item First visibility in the morning: the first visibility of the planet in the east before sunrise following inferior conjunction with the sun.
  \item Last visibility in the morning: the last visibility of the planet in the east before sunrise preceding superior conjunction with the sun.
  \end{enumerate}'''

    tex += r'''
  \end{multicols}
  \vspace*{\fill}'''

    # Page 2
    tex += r'''
\newpage
  \thispagestyle{empty}     %% no page number
  \vspace*{\fill}
  \begin{center}
  \Large\textbf{Aspects of planetary phenomena and a closer look at the Planet Diagram}
  \end{center}'''

    tex += r'''
  \begin{multicols}{2}
  \normalsize\noindent
  Navigators and astronomers are probably acquainted with a graphic known as the Planet Diagram which in effect shows the longitude of the sun and planets (expressed as time of meridian passage) over the year, but for others it is relatively mysterious. In contrast the simpler Planet Declinations diagram shows the latitude of the sun and planets over the course of a year.
  Simply stated, eearth's polar axis, around which the earth rotates, is conveniently aligned with the celestial sphere so that a celestial object's declination hardly changes within a day whereas its longitude moves westwards about 15° every hour. Representing the longitude of a celestail object is therefore challenging as one needs to counteract the natural daily rotation of the earth.
'''

    fn1 = r'./diagram.png'
    tex += r'''
    \begin{{center}}
    % TRIM values: left bottom right top     trim=12mm 20cm 12mm 21mm, 
    \includegraphics[width=0.3\textwidth]{{{}}}\\
    \end{{center}}'''.format(fn1)

    tex += r'''
  \noindent
  The simple solution is to take a ‘snapshot’ of the location of celestial objects at a fixed time every day and their positions will only change very slightly day-by-day. The snapshot is taken at 00:00 (midnight) so that all positions align with the beginning of that calendar date on the horizontal axis.
'''

    tex += r'''
  \noindent
  A number of coordinate systems are used in astronomy to define where an object appears in the sky, similar to the latitude and longitude system we use on the Earth. The first, the celestial coordinate system of Right Ascension and Declination, is fixed to certain standard points in the sky and is aligned with the tilt of the Earth.\footnote{Royal Museums Greenwich: \url{ https://www.rmg.co.uk/stories/topics/what-planetary-conjunction}}
  Simply stated, the equatorial plane runs through earth’s equator ... and the celestial equator is projected from the earth’s equator.
  The Right Ascension (RA) of an object indicates its angular distance from the Vernal Equinox in the \textit{equatorial coordinate system}.
'''

    tex += r'''
  \noindent
  Another, known as the \textit{ecliptic coordinate system}, is fixed instead to the orientation of our Solar System within our galaxy and is measured in ecliptic latitude and longitude.\footnotemark[3]
  The ecliptical plane is the plane in which the earth revolves around the sun and is known very precisely.
  Most solar system bodies lie close to the ecliptic plane so it is handy for planetary phenomena, such as conjunctions and oppositions.
  However If two objects have the same right ascension or the same ecliptic longitude, they are considered to be in conjunction with one another\footnotemark[1], i.e. a line through the two objects is perpendicular either to the equatorial plane or the ecliptical plane.
  These two planes have a 23° slant between them.
  To avoid confusion, \textit{we must define which plane is employed when.}
'''

    tex += r'''
  \noindent
  The vertical axis in the Planet Diagram covers 24 hours (solar time) exactly and is labelled `Local Mean Time of Meridian Passage’, meaning at what time (in Greenwich, London) is the celestial object directly above the observer, better known as the `upper meridian’.
  The sun crosses the upper meridian around midday, and the discrepancy is known as the `Equation of Time’.
  The 12h (midday) line correctly separates any day into AM (the lower half) and PM (the upper half).
'''

    # Page 3
    tex += r'''
  \end{multicols}
  \vspace*{\fill}
  \newpage
  \thispagestyle{empty}     % no page number
  \vspace*{\fill}
  \begin{multicols}{2}'''

    tex += r'''
  \noindent
  Conversion from RA to `Local Mean Time of Meridian Passage’ is straightforward, so it follows that the Planet Diagram is fundamentally based on equatorial coordinates. Furthermore, the official USNO/HMNAO publications (``The Nautical Almanac'', ``Astronomical Phenomena'') base all planet-to-planet conjunctions on \textit{equatorial coordinates} - in other words, when two planets are aligned perpendicular to the equatorial plane, also known as `conjunction in right ascension’. (Note that they are probably closer when aligned perpendicular to the ecliptic plane!)
'''

    tex += r'''
  \noindent
  The ecliptic is the path of the sun and the official publications base all conjunctions and oppositions with the sun on \textit{ecliptic coordinates}, also known as `conjunction in ecliptic longitude’. This includes the conjunctions (earth-sun-planet) of the superior planets; the superior conjunctions (earth-sun-planet) of inferior planets; and the inferior conjunctions (earth-planet-sun) of inferior planets. (The orbits of inferior planets lie within earth's orbit, i.e. Mercury and Venus.)
'''

    tex += r'''
  \noindent
  An opposition (sun-earth-planet) is defined by a maximum longitudinal difference \textit{in the ecliptic plane} close to 180°. An opposition can only be with a superior planet (never with Mercury or Venus).
  Before an opposition the planet’s westward elongation is increasing – afterwards its eastward elongation is decreasing. A planet's elongation is the angular separation between the Sun and the planet, with Earth as the reference point.
  A planet’s maximum elongation is close to but below 180°.
  The reason elongation does not reach 180° is because the superior planets do not lie precisely on the ecliptic plane. Elongation only reaches a \textit{maximum apparent elongation from the sun} at opposition.
'''

    tex += r'''
  \noindent
  Using the '-pss' command-line argument one may optionally plot the the sunrise and sunset for a particular latitude on the chart. This helps to distinguish day- and night-time. Using the latitude 51.5°N (corresponding to Greenwich, London, UK) the days during which Mercury is visible during twilight correspond fairly closely to the dates published by USNO/HMNAO in The Nautical Almanac. The best times are beginning of civil twilight mornings (civil dawn) or end of civil twilight evenings (civil dusk).
'''

    tex += r'''
  \normalsize\noindent
  The Planet Diagram has another function: as the relative angular distance (longitude based on the equatorial plane) between them remains almost constant during the same day, one can assert any time one pleases to a point on the vertical axis and infer all positions below (before) or above (after) accordingly.
  (In fact, the Planet Diagram shows how slowly the relative position of the sun and planets changes over the year.)
  \textit{Thus the sun's position can also represent sunrise or sunset} instead of midday.
  If sunrise, then each hour below will represent twilight in the morning. If sunset, then each hour above will represent twilight in the evening. In this way `civil dawn’ can be plotted as a \textit{red line} below the sun's position and `civil dusk’ as a \textit{blue line} above the sun's position. They are roughly 40 minutes (time) from the sun's position at latitides closer to the equator.
'''

    tex += r'''
  \noindent
  The Planet Diagram also has diagonal (top-left to down-right) dashed lines labelled 0° to 330°. These represent the sidereal hour angle (SHA) of a celestial object, which is relatively constant for stars. (The SHA of a star varies by less than a minute of arc per year.)
  It is their longitudinal position, in loose terms, as if the earth didn’t rotate… together with Declination they point to a fixed point in the celestial sphere. To an observer on Earth all stars rotate in a circle within 24 hours.
  This is mirrored in the Planet Diagram in that any vertical line spans the full 360° SHA.
'''

    tex += r'''
  \noindent
  But why are the lines diagonal?
  Let us remember that the vertical axis represents an Earth Day or 24 hours of solar time.
  However, the Earth requires only 23h 56’ 04”, or one Sidereal Day, to point towards the same location in the celestial sphere. Over a year that accounts to 1 day “lost”. And that’s explained because the Earth has completed ONE revolution around the sun in one year.
  The diagonal SHA lines also “lose” one revolution in one year. Now that that’s clarified, stars can be “added” to the Planet Diagram by a straight line with their SHA value.
  The SHA of a solar system planet varies significantly from day to day with the possible exception of the two outermost planets, Uranus and Neptune, that remain fairly close to a fixed SHA value (and are neither plotted on the chart nor considered as navigational planets).'''

    tex += r'''
  \end{multicols}
  \vspace*{\fill}'''

    tex += r'''
\newpage
\restoregeometry    % so it does not affect the rest of the pages'''

    return tex

def endPDF():
    tex = r"""
\end{document}"""
    return tex


#===========================================================

#--------------------------
#   external entry point
#--------------------------

# global variables >>> d00
def makePPchart(obj, first_year, last_year, lats, outfile, tccfile, spad, verbose):

    global d00
    # data for these global variables is stored at module level at retained for the next function call...
    global MPd00, MPobj, MPdata

    ok = True               # return code
    DEBUG_m2 = False        # 'True' to print each LD object

    yy = first_year
    init_A4(spad)          # initialize variables
    # lat_list = [-60.0, -55.0, -50.0, -40.0, -20.0, 0.0, 20.0, 40.0, 50.0, 55.0, 60.0, 62.0, 63.0, 64.0, 65.0, 66.0, 67.0, 68.0, 69.0, 70.0, 71.0, 72.0]

    lat_list = config.lat_list

    n = len(lat_list) - 1       # so only one latitude is processed below
    alllats = False
    if lats == 100.0:
        n = 0
        lats = lat_list[n]
        alllats = True

    # A4     = 210mm x 297mm (8.27 x 11.69 in)
    # Letter = 8.5 x 11 in   (216mm x 279mm)
    if config.pgsz == "A4": # parameters for A4 Landscape
        ori = "a4paper,landscape"
        tm = "5mm"
        bm = "5mm"
        lm = "2mm"
        rm = "2mm"
        tm1 = "13mm"    # first page...  was 15mm
        bm1 = "13mm"    # was 15mm
        lm1 = "23mm"    # was 10mm
        rm1 = "23mm"    # was 10mm
        lm2 = "12mm"
        rm2 = "12mm"
        #parsepPage1 = "[8pt]"
        #parsep = "[12pt]"
    else:                   # parameters for Letter Landscape
        ori = "letterpaper,landscape"
        tm = "5mm"
        bm = "5mm"
        lm = "2mm"
        rm = "2mm"
        tm1 = "13mm"    # first page...
        bm1 = "13mm"
        lm1 = "20mm"    # was 10mm
        rm1 = "20mm"    # was 10mm
        lm2 = "10mm"
        rm2 = "10mm"
        #parsepPage1 = "[8pt]"
        #parsep = "[8pt]"

    outfile.write(beginPDF(ori,tm,bm,lm,rm))
    firstpage = False

    if not config.DPonly and not config.PVonly:
        outfile.write(Page1(tm1,bm1,lm1,rm1))
        firstpage = True

    while yy <= last_year:
        if verbose: print()
        lns = 'N' if lats >= 0.0 else 'S'
        if obj != None:
            objn = config.objnames[obj-1]
            txt = '------ Process {}: {} at latitude {}°{} ------'.format(objn, yy, abs(lats), lns)
            print(txt)
        else:
            txt = '------ Process: {} at latitude {}°{} ------'.format(yy, abs(lats), lns)
            print(txt)

        d00 = date(yy, 1, 1)
        daysinyear = (date(yy+1, 1, 1) - date(yy, 1, 1)).days
        daystoprocess = daysinyear + 1 if config.orthogonal else daysinyear    # for MerPass() below

        # DECLINATION OF SUN AND PLANETS  chart

        if not config.PVonly:
            outfile.write(buildchart1(d00,daysinyear,verbose,firstpage))
            firstpage = False

        # LOCAL MEAN TIME OF MERIDIAN PASSAGE  [= Planet Diagram] chart

        if not config.PVonly:
            outfile.write(buildchart2(d00,daysinyear,lats,verbose,firstpage,ts))
            outfile.write(chart2page2(lats,tm1,bm1,lm2,rm2,yy,ts))
            firstpage = False

        # PLANET VISIBILITY  chart

        if config.PVonly:
            latmax = 75.0       # arbitrary maximum permissable North latitude
            if 1 <= obj <= 5:
                latmax = 72.0   # all latitudes up to 72°N in one file

            if yy == first_year:
                #print("   ",MPd00,MPobj)
                if MPd00 == d00 and MPobj == obj:
                    print("    using stored Meridian Passage data for {} in {}".format(objn,d00.year))
                else:
                    # calculate the planet's Meridian Passage  (this data is independent of latitude)
                    MPstart = time.time()
                    meridian_pass, object_XY_txt, object_name, object_xidx, mp_offset = MerPass(obj,d00,daystoprocess,sf)
                    MPdata = (meridian_pass, object_XY_txt, object_name, object_xidx, mp_offset)
                    MPstop = time.time()
                    msg = "    Meridian Passage execution time = {:0.2f} seconds".format(MPstop-MPstart)
                    print(msg)
                    MPd00 = d00; MPobj = obj
            if yy == first_year and not config.DPonly:
                outfile.write(introchart3(firstpage))
                firstpage = False
            while n < len(lat_list):    # loop through latitude list
                if alllats:
                    lats = lat_list[n]
                    if 1 <= obj <= 5 and lats > latmax: break
                    if n > 0:   # print subsequent title lines
                        lns = 'N' if lats >= 0.0 else 'S'
                        txt = '\n------ Process {}: {} at latitude {}°{} ------'.format(objn, yy, abs(lats), lns)
                        print(txt)
                tex = buildchart3(obj,d00,daysinyear,lats,verbose,firstpage,yy,MPdata,ts)
                outfile.write(tex)
                if alllats:
                    tccfile.write(txt)
                    tccfile.write(gettccdata())
                if len(tex) <= 64:  # \newpage\end{tikzpicture}\end{center}  \vfill  \hspace{0pt}
                    # if "LIMITATION: this software only works with 1 'days above horizon' zone
                    ok = False; break
                firstpage = False
                n += 1

        yy += 1
    # ----------------------------------------- end of 'while'

    outfile.write(endPDF())
    return ok