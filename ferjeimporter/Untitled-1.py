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
    min_lat=63.0,
    max_lat=64.0,
    min_lon=7,
    max_lon=10.5999
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
        lon=float(row[header_signals_lookup['lon']])
        lat=float(row[header_signals_lookup['lat']])
        if (lat <= VALID_OPERATING_AREA.max_lat and lat >=VALID_OPERATING_AREA.min_lat and lon <= VALID_OPERATING_AREA.max_lon and lon >=VALID_OPERATING_AREA.min_lon):
            print('True')
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
            for r in rows_shipinformation[1:]:
                if ship_signal['ferryId'] == r[header_shipinformation_lookup['mmsi']].strip():
                    metadata["width"] = round(float(r[header_shipinformation_lookup['width']]),0)
                    metadata["length"] = round(float(r[header_shipinformation_lookup["length"]]),0)
                    metadata["type"] = r[header_shipinformation_lookup["type"]]
            metadata["heading"] = float(row[header_signals_lookup['true_heading']])
            ship_signal['metadata']=metadata
            signalpoints.append(ship_signal)
            print(signalpoints)  
    return signalpoints

if __name__ == '__main__':
    # Enkel måte å mate inn eksempelinput
    ais_signals = """mmsi;lon;lat;date_time_utc;sog;cog;true_heading;nav_status;message_nr;source
111111111;7.93557;63.1633;2018-01-01 16:58:42;0.0;59.5;511;-99;18;g
111111111;7.93555;63.1633;2018-01-01 16:59:12;0.7;63.0;511;-99;18;g
111111111;7.93547;63.1632;2018-01-01 17:00:14;0.1;208.4;511;-99;18;g
111111111;7.9355;63.1633;2018-01-01 17:00:41;0.0;240.6;511;-99;18;g
111111111;7.93552;63.1632;2018-01-01 17:06:32;0.1;221.3;511;-99;18;g
111111111;7.93554;63.1632;2018-01-01 17:12:31;0.0;217.7;511;-99;18;g
111111111;7.93549;63.1632;2018-01-01 17:15:32;0.0;216.9;511;-99;18;g
111111111;7.93553;63.1632;2018-01-01 17:21:31;0.0;227.1;511;-99;18;g
111111111;7.93557;63.1632;2018-01-01 17:27:31;0.0;207.4;511;-99;18;g
111111111;7.93555;63.1633;2018-01-01 17:30:31;0.0;246.5;511;-99;18;g
111111111;7.93554;63.1632;2018-01-01 17:33:32;0.0;246.9;511;-99;18;g
111111111;7.93556;63.1632;2018-01-01 17:36:34;0.0;237.4;511;-99;18;g
111111111;7.93555;63.1632;2018-01-01 17:39:31;0.0;241.0;511;-99;18;g
215211000;7.66103;63.0553;2018-01-01 00:01:42;0.0;93.0;307;5;3;g
215211000;7.66102;63.0553;2018-01-01 00:07:44;0.1;150.0;307;5;3;g
215211000;7.66101;63.0553;2018-01-01 00:10:45;0.1;178.0;307;5;3;g
215211000;7.66101;63.0553;2018-01-01 00:13:44;0.0;209.0;307;5;3;g
215211000;7.661;63.0553;2018-01-01 00:16:45;0.0;114.0;307;5;3;g"""
    shipinformation = """ mmsi;imo;name;callsign;length;width;type
    111111111;7110024;TANUNDA;VJHN;25;8;90.0
    215211000;8712166;KEY FIGHTER;9HA2671;104;17;80.0"""
    filter_and_clean_ais_items(ais_signals, shipinformation)