#!/usr/bin/env python3

# Given a list of coordinates on the moon, generate an STS script
# to fly between them.
#
# Thanks to Galen Gisler for figuring out how to do this in STS
# and adapting the heading equations from the Wikipedia article
# on great circle navigation,
# https://en.wikipedia.org/wiki/Great-circle_navigation#Course
#
# Output is an STS script, written to the filename specified,
# or standard output.
#

from math import radians, degrees, sin, cos, atan2, sqrt
import sys

# The sites to fly to, in order:
# ( name,  lat, lon, alt, duration )
# lat, lon are in decimal degrees; alt is in km.
# alt and duration are optional; you can omit them or set them to 0 or None.
# alt defaults to 10; 5 - 50 km is a good altitude for most features.
# Duration is how long the flight should take in seconds;
# Setting to 0 or None will choose a default based on the distance.

coordinates = [
    #  Name                  Lat      Lon    Alt  Dur
    # -----                  ---      ---    ---  ---
    ( "Apollo 15",             .5,    23.5           ),    # Rukl 22
    ( "Moltke",              -0.4,    23.9,    0,  6 ),    # Rukl 46
    ( "Tycho",              -42.2,    -8.5,   20     ),    # Rukl 64

    # Mare Oriental *should* be super cool, but Nightshade
    # doesn't seem to have the data for it so you can't see
    # the structure at all.
    # ( "Mare Orientale",     -13,     -72,    100,  0 ),    # Rukl 39-50

    # I couldn't find a good angle that showed the dome field
    # around either Hortensius or the Marius Hills.
    # Marius is very dark in Nightshade at full moon;
    # Hortensius has reasonable light but the domes don't show.
    ( "Hortensius",           7,     -28             ),    # Rukl 30
    # ( "Marius Hills",        11,     -58,      0     ),    # Rukl 29

    # Rumker isn't very good in Nightshade either,
    # partly because it's too dark over there.
    ( "Rumker",              40,     -56,      5     ),    # Rukl 8

    # Fly to Schroter's Valley and then fly along it.
    # I recommend editing the script to remove the various pauses
    # during this sequence -- pause only after the turn toward
    # the third coordinate -- but this script isn't flexible enough
    # to allow specifying that here.
    ( "Schroter's Valley",   26.5,   -54,     60     ),    # Rukl 18
    ( "Schroter's Valley",   25,     -52.5,   10,  5 ),
    ( "Schroter's Valley",   26.1,   -51.75,  10,  8 ),
    ( "Schroter's Valley",   25.4,   -49.8,   10,  8 ),

    # At a duration of 25, Hadley Rille doesn't show up until you
    # stop above it, but longer than that is just too long to take.
    # It might work to tweak the STS script afterward to fly fast
    # to an intermediate point, then slowly the last few degrees,
    # but I haven't tested that yet.
    ( "Hadley Rille",        25.9,     2.25          ),    # Rukl 22

    # Fly to and then along Ariadaeus.
    ( "Ariadaeus Rille",      7.75,   10             ),    # Rukl 34
    ( "Ariadaeus Rille",      6,      15,     10, 18 ),

    # Catena Davy shows up really well in Nightshade, but it's
    # off to the right. Might look a little better if you add a
    # turn to look in the right direction.
    ( "Catena Davy",        -10.9,   -5.75           ),    # Rukl 43

    ( "Straight Wall",      -20,     -8.25           ),    # Rukl 54
    ( "Straight Wall",      -22.2,    -7.5,   10,  9 ),

    ( "Reiner Gamma",         6.5,   -57,     50,  0 )     # Rukl 28
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


def unpack_vals(feature):
    '''Return name, lat, lon, alt, duration,
       calculating appropriate defaults for alt and duration if needed.
    '''
    name = feature[0]
    lat = feature[1]
    lon = feature[2]

    # Default altitude is 10 km
    if len(feature) > 3 and feature[3]:
        alt = feature[3]
    else:
        alt = 10

    # Set duration to None if not specified;, so the default
    # can be calculated relative to the previous point.
    if len(feature) > 4 and feature[4]:
        duration = feature[4]
    else:
        duration = None

    return name, lat, lon, alt, duration


def nightshadefromto(oldfeature, newfeature):
    '''Generate nightshade commands to fly from one point to the other.'''

    name1, lat1, lon1, alt1, duration1 = unpack_vals(oldfeature)
    name2, lat2, lon2, alt2, duration2 = unpack_vals(newfeature)

    init_heading, final_heading = flyfromto(lat1, lon1, lat2, lon2)

    turn_duration = 2

    # Default duration depends on distance.
    # A reasonable speed is 300 miles in 20 seconds.
    if not duration2:
        dist = haversine_distance(lat1, lon1, lat2, lon2)
        duration2 = int(2 * dist / 70)

    # Drop the previous caption before starting to fly, unless
    # the new caption is the same, in which case, keep it.
    if name1 and name2 != name1:
        print('text action drop name caption\n', file=outfp)

    print(f'''# Turn to point to {name2}: ({lat2} {lon2})
moveto alt {alt1}km lat {lat1} lon {lon1} heading {init_heading} pitch -10 duration {turn_duration}
wait duration {turn_duration}

# Fly to {name2}: {lat2}N {lon2}E
moveto alt {alt2}km lat {lat2} lon {lon2} heading {init_heading} pitch -10 duration {duration2}
wait duration {duration2}''',
          file=outfp)

    if name2 and name2 != name1:
          print(f'''text action load alpha 1 coordinate_system dome altitude 9 azimuth 180 font_size 2 r 1 g 1 b 0 name caption string "{name2}"\n
image action drop name MoonPlaces
image action load name MoonPlaces filename moonplaces/all.png alpha 1 coordinate_system dome altitude 20 azimuth 75 scale 40''',
                file=outfp)

    print('script action pause', file=outfp)

#
# Main entry point
#
if __name__ == '__main__':
    if len(sys.argv) > 1:
        outfp = open(sys.argv[1], 'w')
    else:
        outfp = sys.stdout

    # Initial point to fly to before starting the trip
    init_lat = 0
    init_lon = 0
    init_alt = 3500
    init_duration = 10

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
flyto object moon duration {init_duration}
wait duration {init_duration}
moveto alt {init_alt}km lat {init_lat} lon {init_lon} heading 0 pitch -90 duration {init_duration}
wait duration {init_duration}
''',
          file=outfp)

    lastplace = (None, init_lat, init_lon, init_alt, init_duration)
    for place in coordinates:
        nightshadefromto(lastplace, place)
        lastplace = place

    #
    # End script by retreating to show the whole moon
    #
    print('''
text action drop name caption

# At the end of the script, retreat back to view the whole full moon again.
moveto alt 3500km lat 0.0 lon 0.0 heading 0 pitch -90 duration 20
wait duration 20

# end of script''',
          file=outfp)

