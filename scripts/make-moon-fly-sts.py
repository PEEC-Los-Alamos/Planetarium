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

from math import radians, degrees, sin, cos, atan2, sqrt
import sys

# The sites to fly to, in order:
# ( name,  lat, lon, alt, duration )
# lat, lon are in decimal degrees; alt is in km.
# 5 or 50 km is a good altitude for most features.
# Duration is how long the flight should take in seconds;
# what's reasonable depends on distance. Set to 0 to accept a default.
coordinates = [
    ( 'Apollo 15',             .5,    23.5,   10,  0 ),
    ( 'Moltke',              -0.5,    24.2,   10,  0 ),
    ( 'Tycho',              -43.25,  -11.2,   10,  0 ),
    ( 'Orientale',          -20,     -90,     60,  0 ),
    ( 'Hortensius',           7.75,  -27.8,   10,  0 ),
    ( 'Rumker',              41,     -58.1,   10,  0 ),

    ( 'Schroter\'s Valley',  24.2,   -49.75,  10,  0 ),
    ( 'Schroter\'s Valley',  25.7,   -49.8,   10, 10 ),
    ( 'Schroter\'s Valley',  26,     -51,     10, 10 ),
    ( 'Schroter\'s Valley',  26.15,  -51.7,   10, 10 ),
    ( 'Schroter\'s Valley',  25.8,   -52,     10, 10 ),

    ( 'Hadley Rille',        26,       3,     10,  0 ),
    ( 'Ariadaeus',            7.75,   10,     10,  0 ),
    ( 'Ariadaeus',            5,      17.6,   10, 25 ),

    ( 'Catena Davy',        -11.15,   -6.5,   10,  0 ),

    ( 'Straight Wall',      -20, -     8.25,  10,  0 ),
    ( 'Straight Wall',      -23.7,    -7.3,   10, 25 ),

    ( 'Reiner Gamma',         7.75,  -59,     40,  0 )
]


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


MOON_RADIUS_MI = 1079

def haversine_distance(latitude_1, longitude_1, latitude_2, longitude_2):
    """
    Haversine distance between two points.
    From https://github.com/tkrajina/gpxpy/blob/master/gpxpy/geo.py
    Implemented from http://www.movable-type.co.uk/scripts/latlong.html
    Returns distance in miles.
    """
    d_lat = radians(latitude_1 - latitude_2)
    d_lon = radians(longitude_1 - longitude_2)
    lat1 = radians(latitude_1)
    lat2 = radians(latitude_2)

    a = sin(d_lat / 2) * sin(d_lat / 2) + \
        sin(d_lon / 2) * sin(d_lon / 2) * \
        cos(lat1) * cos(lat2)
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return MOON_RADIUS_MI * c


def nightshadefromto(oldfeature, newfeature):
    '''Generate nightshade commands to fly from one point to the other.'''

    name1, lat1, lon1, alt1, duration1 = oldfeature
    name2, lat2, lon2, alt2, duration2 = newfeature

    init_heading, final_heading = flyfromto(lat1, lon1, lat2, lon2)

    # Drop the previous caption before starting to fly, unless
    # the new caption is the same, in which case, keep it.
    if name1 and name2 != name1:
        print('text action drop name caption\n', file=outfp)

    # Make duration dependent on distance.
    # A reasonable speed is 300 miles in 20 seconds.
    if not duration2:
        dist = haversine_distance(lat1, lon1, lat2, lon2)
        duration2 = int(20 * dist / 300)

    print(f'''# Turn to point to {name2}: ({lat2} {lon2})
moveto alt {alt1}km lat {lat1} lon {lon1} heading {init_heading} pitch -10 duration 5
wait duration 5

# Fly to {name2}: {lat2}N {lon2}E
moveto alt {alt2}km lat {lat2} lon {lon2} heading {init_heading} pitch -10 duration {duration2}
wait duration {duration2}''',
          file=outfp)

    if name2 and name2 != name1:
          print(f'text action load alpha 1 coordinate_system dome altitude 9 azimuth 180 font_size 2 r 1 g 1 b 0 name caption string "{name2}"\n')

    print('script action pause', file=outfp)

if __name__ == '__main__':
    outfp = sys.stdout

    # Initial point to fly to before starting the trip
    init_lat = 0
    init_lon = 0
    init_alt = 3500
    init_duration = 20

    #
    # Begin script
    #
    print(f'''# Nightshade script to fly between a set of points on the moon.
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
moveto alt {init_alt}km lat {init_lat} lon {init_lon} heading 0 pitch -90 duration {init_duration}
wait duration 20
''',
          file=outfp)

    lastplace = (None, init_lat, init_lon, init_alt, init_duration)
    for place in coordinates:
        nightshadefromto(lastplace, place)
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

