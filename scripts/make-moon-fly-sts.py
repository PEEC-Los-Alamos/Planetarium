#!/usr/bin/env python3

# Given a list of coordinates on the moon, generate an STS script
# to fly between them.
#
# Thanks to Galen Gisler for figuring out how to do this in STS
# and adapting the heading equations from the Wikipedia article
# on great circle navigation,
# https://en.wikipedia.org/wiki/Great-circle_navigation#Course
#
# Output is an STS script.
#

import collections
from math import radians, degrees, sin, cos, atan2, sqrt
import sys

coordinates = collections.OrderedDict ([
    ( 'Apollo 15',          (.5, 23.5) ),
    ( 'Moltke',             (-0.5, 24.2) ),
    ( 'Tycho',              (-43.25, -11.2) ),
    ( 'Orientale',          (-20, -90) ),
    ( 'Hortensius',         (7.75, -27.8) ),
    ( 'Rumker',             (41, -58.1) ),

    ( 'Schroter\'s Valley', (24.2, -49.75) ),
    ( 'Schroter fly',       (25.7, -49.8) ),
    ( 'Schroter fly',       (26, -51) ),
    ( 'Schroter fly',       (26.15, -51.7) ),
    ( 'Schroter fly',       (25.8, -52) ),

    ( 'Hadley Rille',       (26, 3) ),
    ( 'Ariadaeus',          (7.75, 10) ),
    ( 'Ariadaus fly',       (5, 17.6) ),

    ( 'Catena Davy',        (-11.15, -6.5) ),

    ( 'Straight Wall',      (-20, -8.25) ),
    ( 'Straight Wall fly',  (-23.7, -7.3) ),

    ( 'Reiner Gamma',       (7.75, -59) )
])


def flyfromto(lat1, lon1, lat2, lon2):
    '''Return initial heading, final heading when flying from (lat1, lon1)
       to (lat2, lon2) on a great circle course.
    '''
    # Convert everything to radians
    d3_lat1 = radians(lat1)
    e3_lon1 = radians(lon1)
    d4_lat2 = radians(lat2)
    e4_lon2 = radians(lon2)

    e5_dlon = e4_lon2 - e3_lon1

    f3_num1 = cos(d4_lat2) * sin(e5_dlon)
    g3_denom1 = cos(d3_lat1) * sin(d4_lat2) \
        - sin(d3_lat1) * cos(d4_lat2) * cos(e5_dlon)

    f4_num2 = cos(d3_lat1) * sin(e5_dlon)
    g4_denom2 = sin(d4_lat2) * cos(d3_lat1) * cos(e5_dlon) \
        - cos(d4_lat2) * sin(d3_lat1)

    f6_cd_num = sqrt(g3_denom1**2 + f3_num1**2)
    g6_cd_denom = sin(d3_lat1) * sin(d4_lat2) \
        + cos(d3_lat1) * cos(d4_lat2) * cos(e5_dlon)

    # Python atan2 takes args in the opposite order to spreadsheets
    e6_cd_rad = atan2(f6_cd_num, g6_cd_denom)
    # c6_cd_deg = degrees(e6_cd_rad)

    d7_init_heading_rad = atan2(f3_num1, g3_denom1)
    d8_final_heading_rad = atan2(f4_num2, g4_denom2)

    return degrees(d7_init_heading_rad), degrees(d8_final_heading_rad)

def nightshadefromto(lat1, lon1, lat2, lon2, name):
    '''Generate nightshade commands to fly from one point to the other.'''

    init_heading, final_heading = flyfromto(lat1, lon1, lat2, lon2)
    if name.endswith(" fly"):
        alt = '10km'
        cmt = 'Cruise around'
        # Eventually, adjust speed too
    else:
        alt = '10km'
        cmt = 'Fly to'

    # Make duration dependent on distance
    print('''text action drop name caption

# %s %s: (%f %f)
moveto alt %s lat %f lon %f heading %f pitch -10 duration 5
wait duration 5
moveto alt %s lat %f lon %f heading %f pitch -10 duration 20
wait duration 20
text action load alpha 1 coordinate_system dome altitude 9 azimuth 180 font_size 2 r 1 g 1 b 0 name caption string "%s"

script action pause''' % (cmt, name, lat2, lon2,
       alt, lat1, lon1, init_heading,
       alt, lat2, lon2, init_heading,
       name),
          file=outfp)

if __name__ == '__main__':
    outfp = sys.stdout

    # Initial point to fly to before starting the trip
    from_lat = 0
    from_lon = 0

    #
    # Begin script
    #
    print('''# Nightshade script to fly between a set of points on the moon.
# Uses great circle headings:
# https://en.wikipedia.org/wiki/Great-circle_navigation#Course

# Some basic settings
flag show_tui_datetime off
flag cardinal_points off
flag show_tui_short_obj_info off
flag atmosphere off

# Set date to a time when there's a full moon.
date local 2019-09-13T23:00:00

# Select the moon and fly to where we can view the full moon
select object moon
flyto object moon duration 20
wait duration 20
moveto alt 3500km lat %f lon %f heading 0 pitch -90 duration 20
wait duration 20
''' % (from_lat, from_lon),
          file=outfp)

    lastplace = None
    for place in coordinates:
        if lastplace:
            from_lat, from_lon = coordinates[lastplace]
        nightshadefromto(from_lat, from_lon,
                         coordinates[place][0], coordinates[place][1],
                         place)
        lastplace = place

    #
    # End script
    #
    print('''
text action drop name caption

# At the end of the script, retreat back to view the whole full moon again.
moveto alt 3500km lat 0.0 lon 0.0 heading 0 pitch -90 duration 20
wait duration 20

# end of script''',
          file=outfp)

