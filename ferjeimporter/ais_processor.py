# ferjeimporter/ais_processor.py
from dataclasses import dataclass
import datetime as dt
import pytz
import hashlib
# ...
# 

@dataclass
class CoordinatesArea:
    min_lat: float = 0
    min_lon: float = 0
    max_lat: float = 0
    max_lon: float = 0


# Defines a range of lat and lon that each signal should be in.
# We start with a fairly small area, to avoid storing too much data.
VALID_OPERATING_AREA = CoordinatesArea(
    min_lat=63.428929,
    max_lat=63.430550,
    min_lon=10.345295,
    max_lon=10.444677
    # min_lat=61,
    # max_lat=63,
    # min_lon=9,
    # max_lon=12
)

def hash_mmsi(mmsi):
    return hashlib.sha256(mmsi.encode()).hexdigest()

def filter_and_clean_ais_items(signals, shipinformation):
    """
    Responsible for removing any irrelevant AIS signals.
    This function may need to handle quite large lists, so it might be useful
    to exploit dataprocessing libraries, such as Pandas
    :param ais_items:
    :return:
    """
    rows_signals = [x.split(';') for x in signals.split('\n')]
    rows_shipinformation = [x.split(';') for x in shipinformation.split('\n')]

    header_signals = rows_signals[0]
    header_signals_lookup = {}
    for index, value in enumerate(header_signals):
        header_signals_lookup[value.strip()] = index
    header_shipinformation = rows_shipinformation[0]
    header_shipinformation_lookup = {}
    for index, value in enumerate(header_shipinformation):
        header_shipinformation_lookup[value.strip()] = index

    signalpoints=[]
    timezone_Norway = pytz.timezone('Europe/Oslo')
    timezone_UTC = pytz.timezone('UTC')

    for row in rows_signals[1:]:
        if len(row) < len(header_shipinformation_lookup):
            print(f'Row {row} not the same length as lookup')
            continue       
        lon=float(row[header_signals_lookup['lon']])
        lat=float(row[header_signals_lookup['lat']])
        if (lat <= VALID_OPERATING_AREA.max_lat and lat >=VALID_OPERATING_AREA.min_lat and lon <= VALID_OPERATING_AREA.max_lon and lon >=VALID_OPERATING_AREA.min_lon):
            ship_signal = {}
            timestamp=dt.datetime.strptime(row[header_signals_lookup['date_time_utc']], '%Y-%m-%d %H:%M:%S')
            localized_timestamp = timezone_Norway.localize(timestamp)      
            new_timezone_timestamp = localized_timestamp.astimezone(timezone_UTC)
            ship_signal['timestamp'] =str(new_timezone_timestamp)
            ship_signal['ferryId'] = hash_mmsi(row[header_signals_lookup['mmsi']])
            ship_signal['lat'] = lat
            ship_signal['lon'] = lon
            ship_signal['source'] = "ais"
            metadata = {}
            if row[header_shipinformation_lookup['mmsi']].strip() in rows_shipinformation[1:]:
                for r in rows_shipinformation[1:]:
                    if row[header_signals_lookup['mmsi']] == r[header_shipinformation_lookup['mmsi']].strip():
                        metadata["width"] = round(float(r[header_shipinformation_lookup['width']]),0)
                        metadata["length"] = round(float(r[header_shipinformation_lookup["length"]]),0)
                        metadata["type"] = r[header_shipinformation_lookup["type"]]
                metadata["heading"] = float(row[header_signals_lookup['true_heading']])
                ship_signal['metadata']=metadata
                signalpoints.append(ship_signal)
            else:
                print('Boat in OPERATING_AREA, but not in shipInfo')
    print(signalpoints)
    return signalpoints