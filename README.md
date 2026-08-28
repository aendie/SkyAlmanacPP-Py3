# SkyalmanacPP-Py3

SkyalmanacPP-Py3 is a Python 3 program to create the Planetary Phenomena data and charts that accompanies a Nautical Almanac. SkyalmanacPP-Py3 is a complimenary program to [Skyalmanac-Py3](https://github.com/aendie/SkyAlmanac-Py3).

**Brief History**

SkyalmanacPP-Py3 began development in January 2023 and has since undergone many updates. I publish only well tested code... the Planetary Visibility Charts, although the charts were correct, required a complete re-write in 2026 that now includes an intermediate language to describe paths that form a perimeter to be shaded, thus providing a level of abstraction from the detailed path descriptions in the "TikZ" language.

**Functionality**

SkyalmanacPP (AKA "Planetary Phenomena") includes:

* the **"DECLINATION OF SUN AND PLANETS"** chart

* the **"Planet Diagram"** (see "Americal Practical Navigator" originally by Nathaniel Bowditch, L.L.D., Volume 1, 2017 Edition, page 256; also any "Astronomical Phenomena" or "Nautical Almanac" from USNO/HMNAO)

* **"VISIBILITY OF PLANETS"** text (see any "Astronomical Phenomena" or "Nautical Almanac" from USNO/HMNAO) with one notable exception: I assume that the data listed in official almanacs is based on latitude 51.5°N, whereas SkyalmanacPP provides planet visibility text based on any latitude you choose (between 60°S and 72°N).

* **"VISIBILITY OF PLANETS IN MORNING AND EVENING TWILIGHT"** table (see any "Astronomical Phenomena" or "Nautical Almanac" from USNO/HMNAO) based on your chosen latitude.

* **Planet Visibility charts**, which I prefer to call "Planet Invisibility" charts, because they show whwn the planet is below the horizon (shaded grey) and when the Sun is higher than 6 degrees below the horizon (shaded gold), i.e. Civil Dawn to Civil Dusk, when it is *generally* too bright to see any planets. (Conversely I maintain that a planet is generally visible during Nautical and Astronomical twilight and night itself, when the Sun is more than 18 degrees below the horizon.) This chart provides the best latitude-specific picture of your chances to observe a given planet. It is based on the pioneering planet visibility work done by the astronomer Rainer Lange, whose web site is now only reachable as an archive: https://web.archive.org/web/20260106175348/https://www.alcyone.de/

&emsp;&emsp;[Sample Planet Visibility chart: Mars in 2026 at 66°N](Mars2026_66N.png)

Note to developers: the Planet Visibility charts have passed 7140 test cases (5 planets x 28 selected latitudes between 60°S and 72°N x years 2000 to 2050 inclusive). Regression testing is built-in in that the newly generated TeX files can be compared to TeX master files without the need to convert them to PDF file format, displaying only the differences. This is a time-saving feature.

**User Documentation**

Please read the following file (in the package): **PPchart usage notes.pdf**

## Requirements

&emsp;Most of the computation is done by the Skyfield astronomical library.  
&emsp;Typesetting is done typically by MiKTeX or TeX Live.  
&emsp;Here are the requirements/recommendations:

* Python v3.4 or higher (v3.12 minimum is recommended)
* Skyfield >= 1.55 (the latest is recommended; see the Skyfield Changelog)
* numpy >= 2.0.0
* scipy >= 1.14.1
* MiKTeX&ensp;or&ensp;TeX Live

**Note that Skyfield version 1.55 is required as a minimum to avert other issues**

## Files required in the execution folder:

* &ast;.py
* diagram.png

**The [DE421 ephemeris](https://pypi.org/project/de421/) is downloaded automatically (as de421.bsp)**

### INSTALLATION GUIDELINES on Windows 10 or 11:

**It is unlikely that the performance improvement with multiprocessing requires specific virtualization settings enabled in the BIOS. (Intel Virtualization Technology or VMM support is not required.) Furthermore Windows 10 Home (without Hyper-V support) is sufficient - Windows 10 Pro/Enterprise/Education is not required. Also Windows 11 Home is sufficient.**

&emsp;Tested on Windows 11 Pro, Version 25H2 with an AMD Ryzen 7 9700X 8-Core Processor  
&emsp;A PDF reader is required, e.g. **Adobe Acrobat Reader**  

&emsp;Install Python 3.13.14 It should be in the system environment variable PATH, e.g.  
&emsp;&ensp;**C:\\Python313\Scripts;C:\\Python313;** .....  
&emsp;Install MiKTeX 25.12 from https://miktex.org/  
&emsp;&emsp;**Run** basic-miktex-25.12-x64.exe **as administrator**  
&emsp;&emsp;I prefer to install MiKTeX **for all users** on a private laptop  
&emsp;&emsp;**Reboot the computer** to avoid the message:  
&emsp;&emsp;"- - - Neither TeX Live nor MiKTeX is installed - - -"  
&emsp;When MiKTeX first runs confirm the installation of additional packages.  
&emsp;Run Command Prompt as Administrator, go to your Python folder and execute, e.g.:

&emsp;**cd C:\\Python313**  
&emsp;**python.exe -m pip install --upgrade pip**  
&emsp;... for a first install (it's preferable to install *wheel* first):  
&emsp;**pip install wheel**  
&emsp;**pip install skyfield**  
&emsp;**pip install scipy**  
&emsp;... if already installed, check for upgrades explicitly:  
&emsp;**pip install --upgrade skyfield scipy**  

&emsp;Put the required files for SkyalmanacPP in a new folder, run Command Prompt in that folder and execute with:  
&emsp;**py PPchart.py**

### INSTALLATION GUIDELINES on Ubuntu Desktop 19.10 or 20.04, 22.04, 24.04 or 26.04:

&emsp;Ubuntu 18.04 and higher comes with Python 3 preinstalled,  
&emsp;however pip may need to be installed:  
&emsp;**sudo apt install python3-pip**

&emsp;Install the following TeX Live package:  
&emsp;**sudo apt install texlive-latex-extra**

&emsp;Install the required astronomical libraries etc.:  
&emsp;**pip3 install wheel**  
&emsp;**pip3 install skyfield**  
&emsp;**pip3 install scipy**  

&emsp;Put the SkyalmanacPP files in a folder and execute with:  
&emsp;**python3 PPchart.py**  

### INSTALLATION GUIDELINES on Ubuntu Desktop 24.04:

&emsp;Ubuntu 24.04 comes with Python 3.12 preinstalled, which requires use of a virtual environment.  
&emsp;Please download the file **How to install Skyalmanac on Linux.pdf** for instructions.  
&emsp;Installation of the PyPI package is described, which is simpler - no other files from GitHub are required.  
&emsp;Please note that although the documentation refers to **Skyalmanac**, it also applies to **SkyalmanacPP**. Just substitute the correct distribution name.

### INSTALLATION GUIDELINES on Mac OS (old; unverified):

&emsp;Every Mac comes with python preinstalled.  
&emsp;(Please choose this version of SFalmanac if Python 3.* is installed.)  
&emsp;You need to install the Ephem and Skyfield libraries to use SFalmanac.  
&emsp;Type the following commands at the commandline (terminal app):

&emsp;**sudo easy_install pip**  
&emsp;**pip install wheel**  
&emsp;**pip install skyfield**  
&emsp;**pip install scipy**  

&emsp;If this command fails, your Mac asks you if you would like to install the header files.  
&emsp;Do so - you do not need to install the full IDE - and try again.

&emsp;Install TeX/LaTeX from https://tug.org/mactex/

&emsp;Now you are almost ready. Put the SkyalmanacPP files in any directory and start with:  
&emsp;**python PPchart**  
&emsp;or  
&emsp;**./PPchart**
