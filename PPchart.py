#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# plot Planetary Phenomena charts on A4 or Letter paper in Landscape orientation

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

###### Standard library imports ######
import os
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path    # works on different operating systems :-)
import difflib

###### Third party imports ######
from skyfield import VERSION

###### Local application imports ######
import config
# !! execute the next 3 lines before importing from other modules !!
config.WINpf = True if sys.platform.startswith('win') else False
config.LINUXpf = True if sys.platform.startswith('linux') else False
config.MACOSpf = True if sys.platform == 'darwin' else False
from multiprocessing import cpu_count
config.CPUcores = cpu_count()
from ppc_build import makePPchart

#----------------------
#   internal methods
#----------------------

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

def toUnix(fn):
    # replacing parentheses with square brackets in Ubuntu works, but is not required.
    if squarebr and (config.LINUXpf or config.MACOSpf):
        fn = fn.replace("(","[").replace(")","]")
    return fn

def toUNIX(fn):
    if not squarebr and (config.LINUXpf or config.MACOSpf):
        # either of the following commands work in Ubuntu:
        if True:
            fn = "'" + fn + "'"
        else:
            # Python 3 requires a raw string to avoid a syntax warning on the following line...
            fn = fn.replace("(",r"\(").replace(")",r"\)")
    return fn

def deletePDF(texname, pdfname=None, tccname=None):
    if texname != None:
        if os.path.exists(texname):
            os.remove(texname)
    if pdfname != None:
        if os.path.exists(pdfname):
            try:
                os.remove(pdfname)
            except PermissionError:
                print("ERROR: please close '{}' so it can be re-created".format(pdfname))
                sys.exit(0)
    if tccname != None:
        if os.path.exists(tccname):
            os.remove(tccname)
    return

def makePDF(pdfcmd, fn, fpath, msg = ""):
    # any shell command in Unix requires either escaped parentheses
    #   or the entire filename within single apostrophes

    returned_value = 0
    outdir = '' if fpath == '' else "-output-directory={} ".format(toUNIX(fpath))
    # note: 'fpath' is essential for rtfnd and nmfnd
    command = r'pdflatex {}{}'.format(outdir, pdfcmd + toUNIX(fpath + fn + '.tex'))
    #print("EXECUTE: {}".format(command))
    if pdfcmd == "":        # verbose mode specified
        os.system(command)
        print("finished" + msg)
    else:
        returned_value = os.system(command)
        if returned_value != 0:
            if msg != "":
                print("ERROR detected while" + msg)
            else:
                print("!!   ERROR detected while creating PDF file   !!")
                print("!! Append '-v' or '-log' for more information !!")
        else:
            if msg != "":
                print("finished" + msg)
            else:
                print("finished creating '{}'".format(fn + ".pdf"))
    return returned_value

def tidy_up(fn, keep_tex=False):
    # use keep_tex during regression testing to keep tex files with differences
    #print("TIDY UP path: {}   keep TEX {} {}".format(fn, keep_tex, keeptex))
    if not keep_tex and not keeptex: os.remove(fn + ".tex")
    if not keeplog:
        if os.path.isfile(fn + ".log"):
            os.remove(fn + ".log")
    if os.path.isfile(fn + ".aux"):
        os.remove(fn + ".aux")
    return

def check_mth(mm):
    if not 1 <= int(mm) <= 12:
        print("ERROR: Enter month between 01 and 12")
        sys.exit()

def check_date(year, month, day):
    yy = int(year)
    mm = int(month)
    day_count_for_month = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if yy%4==0 and (yy%100 != 0 or yy%400==0):
        day_count_for_month[2] = 29
    if not (1 <= mm <= 12 and 1 <= int(day) <= day_count_for_month[mm]):
        print("ERROR: Enter a valid date")
        sys.exit()

def checkCoreCount():       # only called when config.MULTIpr == True
    if not (config.WINpf or config.LINUXpf or config.MACOSpf):
        print("Unsupported OS for multi-processing.")
        sys.exit(0)
    if not sys.version_info.major > 3:
        if not (sys.version_info.major == 3 and sys.version_info.minor >= 4):
            print("Python 3.4 or higher is required for multi-processing.")
            sys.exit(0)
    if config.CPUcores == 1:
        config.MULTIpr = False
        print("\nERROR: 2 logical processors minimum are required for parallel processessing")
        print("       defaulting to single processessing")
    if config.CPUcores < 12 or (config.WINpf and config.CPUcores < 8):
        print("\nNOTE: only {} logical processors are available for parallel processessing".format(config.CPUcores))


###### Main Program ######

if __name__ == '__main__':      # execute if this module explicitely run
    if sys.version_info[0] < 3:
        print("This runs only with Python 3")
        sys.exit(0)

    # check if pandas version is compatible with numpy
    n = sys.version.find(" ")
    py_ver = sys.version[:n]        # python version

    if SkyfieldVersion("1.55") < 0:
        # Skyfield >=1.47 is required for almanac.find_transits in MerPass in pp_skyfield.py
        print("Skyfield version 1.55 or higher is required...")
        print("Please upgrade skyfield using:     pip install skyfield==1.55")
        print(" or to get the latest version:     pip install skyfield --upgrade")
        sys.exit(0)

    # if SkyfieldVersion("1.49") != 0:
        # print("Skyfield version 1.49 is required until the problems with 1.50 to 1.53 are fixed.")
        # print("Issue: https://github.com/skyfielders/python-skyfield/issues/1086")
        # sys.exit(0)

    devuser = True      # enable added functionality for developers
    obj = None
    allplanets = False
    latndx = 0; rtndx = 0; nmndx = 0
    yyfr = yyto = -1
    lns = "N"       # default hemisphere
    lats = 51.5     # default latitude (Greenwich, London, UK is 51.48°N 0.0°E)
    twidbh = 6.0    # default twilight - Sun degrees below horizon (6.0 = Civil Dusk/Dawn)
    # command line arguments...
    validargs = ['-v', '-vt', '-log', '-tex', '-a4', '-let', '-dpo', '-pss', '-sbr', '-sp', '-un', '-lat', '-lats', '-orth', '-pv', '-pv1', '-pv2', '-pv3', '-pv4', '-pv5', '-pv6', '-pv7']
    if devuser:     # commands for development users...
        validargs += ['-nsa', '-nsb', '-nsdah', '-nsdbh', '-df', '-db', '-00h', '-24h', '-rt', '-nm']

    exclude_ndx = []

    latfnd = False
    laterr = False
    pvofnd = False
    pverr  = False
    rtfnd  = False
    rterr  = False
    nmfnd  = False
    config.PVonly = False

    for i in list(range(1, len(sys.argv))):
        # print("process: {}".format(sys.argv[i]))
        if sys.argv[i] == '-lat':
            latfnd = True
            latndx = i+1
            exclude_ndx.append(i+1)
            lats = 100.0    # special case of 'all latitudes' in ONE PDF
        if i == latndx and sys.argv[i][0] != '-':
            arg = sys.argv[i]
            if len(arg) != 5:
                laterr = True
            else:
                if arg[2] != '.': laterr = True
                s = arg[:2] + arg[3]
                if not s.isdigit(): laterr = True
                if arg[4] not in ['N', 'S']: laterr = True
            if not laterr:
                lns = arg[4]
                lat = float(arg[0:4])
                if lat == 0.0: lns = 'N'
                if lat > 72: laterr = True
                if lat > 60 and lns == 'S': laterr = True
                else:
                    print("selected latitude: {:4.1f}°{}".format(lat,lns))
                    lats = -lat if lns == 'S' else lat  # signed latitude

        if laterr:
            print("Please input the latitude as '-lat nn.nN' or '-lat nn.nS'.")
            print("The valid range is between 72.0N and 60.0S   For example:")
            print("     -lat 51.5N")
            print("     -lat 40.0S")
            print("     -lat 22.7N")
            print("     -lat 05.5S")
            print("     -lat 00.0N")
            sys.exit(0)

        if sys.argv[i][:3] == '-pv':
            config.PVonly = True
            pvofnd = True
            pverr = False
            if sys.argv[i] == '-pv': obj = 1; allplanets = True
            else:
                arg = sys.argv[i][3]
                if not arg.isdigit(): pverr = True
                elif not 1 <= int(arg) <= 7: pverr = True
                if pverr:
                    print("Please specify the planet of choice, i.e.")
                    print("   '-pv1' for Mercury")
                    print("   '-pv2' for Venus")
                    print("   '-pv3' for Mars")
                    print("   '-pv4' for Jupiter")
                    print("   '-pv5' for Saturn")
                    print("   '-pv6' for Uranus")
                    print("   '-pv7' for Neptune")
                    print("   '-pv'  for the first 5 planets (Mercury to Saturn)")
                    sys.exit(0)
                obj = int(arg)

        if sys.argv[i] == '-rt':
            rtfnd = True
            rtndx = i+1
            exclude_ndx.append(i+1)

        if sys.argv[i] == '-nm':
            nmfnd = True
            nmndx = i+1
            exclude_ndx.append(i+1)

        # 'regression testing' or 'new master' helper...
        if (i == rtndx or i == nmndx) and sys.argv[i][0] != '-':
            arg = sys.argv[i]
            if len(arg) >= 2:
                if not arg[:2].isdigit(): rterr = True
                else:
                    k = int(arg[:2])
                    j = 2000 if k <= 50 else 1900
                    yyfr = yyto = k + j
                    syr = str(yyfr)             # syr = "20" + arg[:2]
            else: rterr = True
            if not rterr and len(arg) > 2:
                if len(arg)!= 5: rterr = True
                if arg[2] != '-': rterr = True
                if not rterr:
                    if not arg[3:].isdigit(): rterr = True
                    else:
                        k = int(arg[3:])
                        j = 2000 if k <= 50 else 1900
                        yyto = k + j
                        syr += '-' + str(yyto)  # syr += "-20" + arg[3:]
                        if yyto <= yyfr: rterr = True

        if sys.argv[i] not in validargs and not i in exclude_ndx:      # i != latndx:
            print("Invalid argument: {}".format(sys.argv[i]))
            print("\nValid command line arguments are:")
            print(" -v   ... 'verbose': to send detailed output to the terminal")
            print(" -vt  ... 'verbose': to send pdfTeX output to the terminal")
            print(" -log ... to keep the log file")
            print(" -tex ... to keep the tex file")
            print(" -a4  ... A4 papersize")
            print(" -let ... Letter papersize")
            print(" -dpo ... data pages only")
            print(" -un  ... also plot Uranus & Neptune*")
            print(" -pss ... plot sunrise/sunset & civil dusk/dawn at chosen latitude*")
            print(" -sbr ... use square brackets in Unix filenames")
            print(" -sp  ... execute in single-processing mode (slower)")
            print("      * applies only to the Planet Diagram")
            print(" --------  Planet Visibility charts  --------")
            print(" -pv1 ..... for Mercury")
            print(" -pv2 ..... for Venus")
            print(" -pv3 ..... for Mars")
            print(" -pv4 ..... for Jupiter")
            print(" -pv5 ..... for Saturn")
            print(" -pv6 ..... for Uranus")
            print(" -pv7 ..... for Neptune")
            print(" -pv  ..... for the first 5 planets (Mercury to Saturn)")
            print(" -lat 51.5N ... select one latitude as nn.nN or nn.nS")
            print(" -lat ... print charts with all the following latitudes:")
            print("          60S 58S 55S 50S 45S 40S 30S 15S 0 15N 30N 40N 45N 50N 55N 58N 60N 62N 63N 64N 65N 66N 67N 68N 69N 70N 71N 72N")
            print(" -lats .. print all above latitudes as separate PDF chart files")
            print(" -orth .. orthogonal plot data: data 00h to 24h is aligned vertically on start of day")
            if devuser:
                print(" -nsa ... no gold Civil Dawn-to-Dusk & 'planet above horizon' shading")
                print(" -nsb ... no grey 'planet below horizon' shading")
                print(" -nsdah . no gold 'planet all day below horizon' shading")
                print(" -nsdbh . no grey 'planet all day below horizon' shading")
                print(" -df  ... debug: 'trace above horizon contour forwards'")
                print(" -db  ... debug: 'trace above horizon contour backwards'")
                print(" -00h ... debug: contours along 00h during noDAWN")
                print(" -24h ... debug: contours along 24h during noDUSK")
                print(" -nm xx    ... create new master for year 19xx/20xx")
                print(" -nm xx-yy ... create new master from year 19xx/20xx to 19yy/20yy")
                print(" -rt xx    ... regression test against year 19xx/20xx")
                print(" -rt xx-yy ... regression test from year 19xx/20xx to 19yy/20yy")
                print("          where xx and yy are the last 2 digits of a year between 1951 and 2050")
            sys.exit(0)
    # ----------------------------------------- end of 'for'

    if rterr or (rtndx != 0 and not (1951 <= yyfr <= 2050) and not (1951 <= yyto <= 2050)):
        print("Enter a year or years between 1951 and 2050, i.e.")
        print("   '-rt 99' for 1999")
        print("   '-rt 23' for 2023")
        print("   '-rt 21-23' for 2021 to 2023")
        print("Regression testing compares each newly created .tex file with")
        print("saved .tex files in another folder, without PDF file creation.")
        print("           Results appear in 'differences.txt'.")
        sys.exit(0)

    verbose = True if "-v" in set(sys.argv[1:]) else False
    listarg = "" if "-vt" in set(sys.argv[1:]) else "-interaction=batchmode -halt-on-error "
    keeplog = True if "-log" in set(sys.argv[1:]) else False
    keeptex = True if "-tex" in set(sys.argv[1:]) else False
    quietmode = True if "-q" in set(sys.argv[1:]) else False
    squarebr = True if "-sbr" in set(sys.argv[1:]) else False
    alllats = True if "-lats" in set(sys.argv[1:]) else False
    config.orthogonal = True if "-orth" in set(sys.argv[1:]) else False
    config.DPonly = True if "-dpo" in set(sys.argv[1:]) else False
    config.plotSS = True if "-pss" in set(sys.argv[1:]) else False
    config.plotUN = True if "-un" in set(sys.argv[1:]) else False
    config.PV_nsa = True if "-nsa" in set(sys.argv[1:]) else False
    config.PV_nsb = True if "-nsb" in set(sys.argv[1:]) else False
    config.PV_nsdah = True if "-nsdah" in set(sys.argv[1:]) else False
    config.PV_nsdbh = True if "-nsdbh" in set(sys.argv[1:]) else False
    config.PV_df = True if "-df" in set(sys.argv[1:]) else False
    config.PV_db = True if "-db" in set(sys.argv[1:]) else False
    config.debug_00h_contour = True if "-00h" in set(sys.argv[1:]) else False
    config.debug_24h_contour = True if "-24h" in set(sys.argv[1:]) else False

    if rtfnd and nmfnd:
        print("Use either '-rt' or '-nm', not both together")
        sys.exit(0)

    if rtfnd or nmfnd:
        config.orthogonal = True    # master for regression testing must have orthogonal data
        if nmfnd: keeptex = True    # default '-tex' only if nmfnd
        config.DPonly = True        # default '-dpo'
        src_path = Path('.').resolve().as_posix()
        if src_path.count('/') <3:
            print("ERROR: Inadequate folder levels - this needs to run from a deeper folder level")
            sys.exit(0)

    if rtfnd and latfnd and lats == 100.0:
        #alllats = True   # only with '-rt', '-lat' means '-lats'
        print("ERROR: Regression test requires '-lat' with an argument, or '-lats'")
        sys.exit(0)

    if lats == 100.0:
        print("process list of latitudes")

    if alllats and not pvofnd:
        print("'-lats' is only relevant if '-pv' or '-pv[digit]' is specified")
        sys.exit(0)

    if (rtfnd or nmfnd) and not pvofnd:
        print("'-pv' or '-pv[digit]' is also required")
        sys.exit(0)

    if pvofnd and not (latfnd or alllats):
        #print(latfnd,lats)
        print("If '-pv' or '-pv[digit]' is specified, '-lat' or '-lats' is also required")
        sys.exit(0)

    if "-sp" in set(sys.argv[1:]):
        # NOTE: this only works if ppc_buildchart2.py imports
        #       sunrise_set when config.MULTIpr = True
        config.MULTIpr = False

    if "-a4" in set(sys.argv[1:]) and "-let" in set(sys.argv[1:]):
        print("Please choose either '-a4' or '-let' (not A4 AND Letter papersize!)")
        sys.exit(0)
    else:
        if "-a4" in set(sys.argv[1:]):  config.pgsz = "A4"
        if "-let" in set(sys.argv[1:]): config.pgsz = "Letter"

    if compareVersion(py_ver,"3.11") >= 0:
        # Python >= 3.13 now requires timezone-aware datetimes
        d = datetime.now(timezone.utc).date()   # 'datetime.UTC' only added in version 3.11
    else:
        d = datetime.utcnow().date()   # deprecated since Python 3.12
    first_day = date(d.year, d.month, d.day)
    yy = d.year         # NOT ... yy = "%s" % d.year

    if config.pgsz not in set(['A4', 'Letter']):
        print("Please choose a valid paper size in config.py")
        sys.exit(0)

    if config.ephndx not in set([0, 1, 2, 3, 4]):
        print("Error - Please choose a valid ephemeris in config.py")
        sys.exit(0)

    spad = "./"

    # ------------ process user input ------------
    entireMth = False
    entireYr  = False
    entireYrs = False

    yrmin = config.ephemeris[config.ephndx][1]
    yrmax = config.ephemeris[config.ephndx][2]
    yrmin = max(1951,yrmin)     # minimum for Planet Visibility charts
    yrmax = min(2050,yrmax)     # maximum for Planet Visibility charts

    if not rtfnd and not nmfnd:

        syr = input("""
  Enter as numeric digits:
    - 'YYYY'        (1951 <= year <= 2050)
    - 'YYYY-YYYY'   for a range of years
    - nothing for the current year
""")

        sErr = False    # syntax error
        if len(syr) == 0:
            syr  = "{}".format(d.year)
            if d.year > yrmax:
                print("!! Only years up to {} are valid!!".format(yrmax))
                sys.exit(0)

        if len(syr) not in [4,9]: sErr = True
        if not syr[:4].isnumeric(): sErr = True
        if len(syr) == 9:
            if syr[4] != '-': sErr = True
            if not syr[5:].isnumeric(): sErr = True
        if sErr:
            print("ERROR: Enter numeric digits in the correct format")
            sys.exit(0)

#   ------------------  PROCESS YEAR RANGE  ------------------

    dd = "01"
    mm = "01"
    yy1 = int(syr[:4])        # 'YYYY' or 'YYYY-YYYY' format
    yy = yy2 = yy1
    #check_date(yy1,mm,dd)
    if not (yrmin <= yy1 <= yrmax):
        print("!! Please pick a year between {} and {} !!".format(yrmin,yrmax))
        sys.exit(0)

    if len(syr) == 9:
        yy2 = int(syr[5:])    # 'YYYY-YYYY' format
        #check_date(yy2,mm,dd)
        if not (yrmin <= yy2 <= yrmax):
            print("!! Please pick an end year between {} and {} !!".format(yrmin,yrmax))
            sys.exit(0)
        if yy2 <= yy1:
            print("!! The FROM year {} must be lower than the TO year {} !!".format(yy1,yy2))
            sys.exit(0)
        if rtfnd or nmfnd: entireYr = True
        else:    entireYrs = True
    else:
        entireYr = True

#   ------------------

    if allplanets: obj = 1
    workpath = ''       # not '.'
    cwd = os.getcwd()
    if rtfnd or nmfnd:
        workpath = './_rt/'
        if not os.path.isdir(workpath): os.makedirs(workpath)   # create any missing folders

#   ------------------  IF REGRESSION TEST  ------------------

    if rtfnd:
        yy = yyfr
        objn = config.objnames[obj-1] if obj is not None else "????"
        if allplanets: diffpath = workpath + "differences {:d}.txt".format(yy)
        else:          diffpath = workpath + "differences {} {:d}.txt".format(objn,yy)
        if os.path.exists(diffpath):
            os.remove(diffpath)
        difffile = open(diffpath, mode="w", encoding="utf8")

#   ------------------  IF NEW/UPDATE MASTER  ------------------
    if nmfnd:
        yy = yyfr

#   --------------------- FOR ALL PLANETS --------------------

    while True:

#   ----------------------- PER PLANET -----------------------

        filestocreate = 1
        latmax = 200.0      # ensure latmax > lats (= 100.0)
        objn = None
        if config.PVonly:
            lat_list = config.lat_list
            filestocreate = 1

            if alllats:     # 'alllats' means create separate files (one per latitude)
                latmax = 72.0

                filestocreate = len(lat_list) if alllats else 0
                for index, item in enumerate(config.lat_list):
                    if item > latmax:
                        n1 = index
                        n2 = len(lat_list) - index
                        filestocreate = n1 if alllats else n2
                        break

            # first check if all necessary files are deletable...
            if filestocreate > 1:
                objn = config.objnames[obj-1]
                ndx  = - 1
                for n in range(filestocreate):
                    ndx += 1
                    papersize = config.pgsz
                    lats = lat_list[ndx]
                    lns = 'N' if lats >= 0.0 else 'S'
                    latlns = "{:04.1f}{}".format(abs(lats),lns)
                    if entireYr:
                        filename = toUnix("{}({})_{}_{}".format(objn,papersize,latlns,yy1))
                    elif entireYrs:
                        filename = toUnix("{}({})_{}_{}-{}".format(objn,papersize,latlns,yy1,yy2))

                    texname = filename + ".tex"
                    pdfname = filename + ".pdf"
                    texpath = workpath + texname
                    pdfpath = workpath + pdfname
                    filepath = workpath + filename
                    if rtfnd: deletePDF(texpath)
                    else: deletePDF(texpath, pdfpath)
                    if nmfnd:       # new
                        dst_path = "../../_" + str(yy) + "/" + objn + "/"   # works on Windows too
                        deletePDF(texpath, dst_path+pdfname)

                # for index, item in enumerate(config.lat_max):
                    # if item == yy: latmax = config.lat_max[index+obj]
    
#   ----------------------- PER LATITUDE ---------------------

        ndx = - 1
        for n in range(filestocreate):
            ndx += 1
            papersize = config.pgsz
            objn = "PPchart"
            if config.PVonly:
                objn = config.objnames[obj-1]
                if filestocreate > 1:
                    lats = lat_list[ndx]
                    lns = 'N' if lats >= 0.0 else 'S'
                if lats == 100.0:
                    latlns = "all"
                else:
                    latlns = "{:04.1f}{}".format(abs(lats),lns)
            else:
                latlns = "{:04.1f}{}".format(abs(lats),lns)
            if entireYr:
                filename = toUnix("{}({})_{}_{}".format(objn,papersize,latlns,yy1))
            elif entireYrs:
                filename = toUnix("{}({})_{}_{}-{}".format(objn,papersize,latlns,yy1,yy2))

            texname = filename + ".tex"
            pdfname = filename + ".pdf"
            oldpdfname = filename + " OLD.pdf"
            tccname = filename + ".txt"         # 'trace Code Coverage' data file
            texpath = workpath + texname
            pdfpath = workpath + pdfname
            tccpath = workpath + tccname
            filepath = workpath + filename

            if rtfnd: deletePDF(texpath)
            else:     deletePDF(texpath, pdfpath, tccpath)

            if nmfnd:
                dst_path = "../../_" + str(yy) + "/" + objn + "/"        # works on Windows too
                old_file = dst_path + pdfname
                if latfnd and lats == 100.0:    # if '-lat' without a specific latitude
                    # rename the old 'all' PDF file (if it exists) - it's useful to compare with the new PDF
                    new_file = dst_path + oldpdfname
                    deletePDF(texpath, new_file)
                    if os.path.exists(old_file):
                        try:
                            os.rename(old_file, new_file)
                        except Exception as ex:
                            print("ERROR: {}\n'{}' cannot be renamed to '{}'\ncwd = {}".format(type(ex),old_file,new_file,cwd))
                            sys.exit(0)
                else:
                    deletePDF(texpath, old_file)

            if lats > latmax: break     # stop processing when an invalid latitude is reached

            if config.MULTIpr: checkCoreCount()
            start = time.time()

            if obj == None:
                msg = "\nCreating the planetary phenomena charts at {} ".format(latlns)
            else:
                msg = "\nCreating {} visibility charts ".format(objn)

            if entireYr: msg += "for the year {}".format(yy1)
            elif entireYrs: msg += "for the years {}-{}".format(yy1,yy2)
            print(msg)

            if rtfnd:
                difffile.flush()
                txt = '------ Process {}: {} at latitude {}°{} ------'.format(objn, yy, abs(lats), lns)
                ###difffile.write("\n" + txt + "\n\n")
                difffile.write(txt + "\n")

            yy3 = yy2 if entireYrs else yy1

            if lats == 100.0:
                tccfile = open(tccpath, mode="w", encoding="utf8")
                outfile = open(texpath, mode="w", encoding="utf8")
                ok = makePPchart(obj,yy1,yy3,lats,outfile,tccfile,spad,verbose)
                outfile.close()
                tccfile.close()
            else:
                outfile = open(texpath, mode="w", encoding="utf8")
                ok = makePPchart(obj,yy1,yy3,lats,outfile,None,spad,verbose)
                outfile.close()

            stop = time.time()
            msg2 = "\nexecution time excluding conversion to PDF = {:0.2f} seconds\n".format(stop-start)
            print(msg2)

            if not ok: break

            if rtfnd:
                rtyy = str(yy)
                rtpath = "../../_" + rtyy + "/" + objn + "/"     # works on Windows too
                xxfn   = workpath + texname
                rtfn   = rtpath + texname

                with open(xxfn, mode="r", encoding="utf8") as file_1:
                    file1 = file_1.readlines(); file_1.close()

                with open(rtfn, mode="r", encoding="utf8") as file_2:
                    file2 = file_2.readlines(); file_2.close()

                nn = 0; keep_tex = False
                # gather differences, if any
#               for line in difflib.unified_diff(file1, file2, fromfile=str(xxfn), tofile=str(rtfn), n=0, lineterm = '\n'):
                for line in difflib.context_diff(file1, file2, fromfile=str(xxfn), tofile=str(rtfn), n=0, lineterm = '\n'):
                    print(line, end='')
                    if nn == 0: difffile.write("\n")
                    difffile.write(line)
                    nn += 1
                if nn > 0:
                    difffile.write("\n")
                    # keep_tex = True   # keep only if needed for debugging

                tidy_up(filepath, keep_tex)

            elif nmfnd:
                err = makePDF(listarg, filename, workpath)
                if err != 0: sys.exit(0)    # quit on error to suppress further error messages
                tidy_up(filepath, True)

                # move PDF and TEX (and TXT) files to master folder
                # NOTE: relative paths are unreliable in Windows 11 (e.g. with Python 3.13.9)
                dst_path = "../../_" + str(yy) + "/" + objn + "/"       # works on Windows too
                #dst_path = "../../../_" + str(yy) + "/" + objn + "/"        # works on Windows too
                if not os.path.isdir(dst_path): os.makedirs(dst_path)   # create any missing folders

                src_file = Path(workpath, texname)
                dst_file = Path(dst_path, texname)
                try:
                    src_file.replace(dst_file)      # move/overwrite file to destination folder
                except Exception as ex:
                    print("ERROR: {}\n'{}' cannot be overwritten\ncwd = {}".format(type(ex),dst_file,cwd))
                    sys.exit(0)

                src_file = Path(workpath, pdfname)
                dst_file = Path(dst_path, pdfname)
                try:
                    src_file.replace(dst_file)      # move/overwrite file to destination folder
                except PermissionError:
                    print("ERROR: please close '{}  {}' so it can be overwritten".format(dst_file,pdfname))
                    sys.exit(0)
                except Exception as ex:
                    print("ERROR: {}\n'{}' cannot be overwritten\ncwd = {}".format(type(ex),dst_file,cwd))
                    sys.exit(0)

                if latfnd and lats == 100.0:    # if '-lat' without a specific latitude
                    src_file = Path(workpath, tccname)
                    dst_file = Path(dst_path, tccname)
                    try:
                        src_file.replace(dst_file)  # move/overwrite file to destination folder
                    except Exception as ex:
                        print("ERROR: {}\n'{}' cannot be overwritten\ncwd = {}".format(type(ex),dst_file,cwd))
                        sys.exit(0)

            else:
                makePDF(listarg, filename, workpath)
                tidy_up(filepath)

        # ------------------------------------- end of 'for'
 
        if rtfnd:
            os.fsync(difffile)              # https://docs.python.org/2/library/stdtypes.html#file.flush
        if allplanets:
            obj = (obj % 5) + 1             # next planet (1 to 5 repetitively)
            objn = config.objnames[obj-1]
            if rtfnd: difffile.write("\n")  # blank line between planets
            if obj == 1:
                yy += 1; yy1 = yy           # next year
                if yy > yy2: break
                if rtfnd:
                    difffile.close()
                    # new differences-filename
                    diffpath = workpath + "differences {:d}.txt".format(yy)
                    if os.path.exists(diffpath):
                        os.remove(diffpath)
                    difffile = open(diffpath, mode="w", encoding="utf8")
        elif rtfnd or nmfnd:
            yy += 1; yy1 = yy               # next year
            if yy > yy2: break
            if rtfnd:
                difffile.close()
                # new differences-filename
                if allplanets: diffpath = workpath + "differences {:d}.txt".format(yy)
                else:          diffpath = workpath + "differences {} {:d}.txt".format(objn,yy)
                if os.path.exists(diffpath):
                    os.remove(diffpath)
                difffile = open(diffpath, mode="w", encoding="utf8")
        else: break

    # ----------------------------------------- end of 'while'

    if rtfnd:
        difffile.close()