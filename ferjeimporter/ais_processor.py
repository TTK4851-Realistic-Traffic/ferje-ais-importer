from dataclasses import dataclass
from typing import Dict, List
import datetime as dt
import pytz
import hashlib


@dataclass
class CoordinatesArea:
    min_lat: float = 0
    min_lon: float = 0
    max_lat: float = 0
    max_lon: float = 0

    def is_in_area(self, lat: float, lon: float) -> bool:
        return self.min_lat <= lat <= self.max_lat and \
               self.min_lon <= lon <= self.max_lon


# Defines a range of lat and lon that each signal should be in.
# We start with a fairly small area, to avoid storing too much data.
VALID_OPERATING_AREA = CoordinatesArea(
    min_lat=63.428929,
    max_lat=63.555,
    min_lon=10.345295,
    max_lon=10.444677
    # min_lat=61,
    # max_lat=63,
    # min_lon=9,
    # max_lon=12
)

TIMEZONE_NORWAY = pytz.timezone('Europe/Oslo')
TIMEZONE_UTC = pytz.timezone('UTC')


def _from_csv(csv, delimiter=';') -> List[List[str]]:
    rows = [x.split(delimiter) for x in csv.split('\n')]
    for index, row in enumerate(rows):
        for col_index, column in enumerate(row):
            rows[index][col_index] = column.strip()
    return rows


def _hash_mmsi(mmsi):
    return hashlib.sha256(mmsi.encode()).hexdigest()


def _attach_timezone_identifier(datetime_utc):
    """
    Ensures the datetime in UTC is attached the timezone identifier +00:00 or Z
    :param datetime_utc: Should have the format '%Y-%m-%d %H:%M:%S' and be in UTC
    :return:
    """
    timestamp = dt.datetime.strptime(datetime_utc, '%Y-%m-%d %H:%M:%S')
    localized_timestamp = TIMEZONE_NORWAY.localize(timestamp)
    return str(localized_timestamp.astimezone(TIMEZONE_UTC))


def _build_shipinfo_lookup(shipinformation) -> dict:
    """
    Builds a dictionary of shipmetadata, where key is MMSI.
    The metadata is also cleaned to make further use easier
    :param shipinformation:
    :return:
    """
    column_index = {}
    for index, value in enumerate(shipinformation[0]):
        column_index[value.strip()] = index

    lookup = {}

    for ship in shipinformation[1:]:
        # Skip empty lines
        if len(ship) < 1 or len(ship[0]) < 1:
            continue
        mmsi = ship[column_index['mmsi']].strip()

        if mmsi in lookup:
            continue

        lookup[mmsi] = {
            'imo': ship[column_index['imo']].strip(),
            'name': ship[column_index['name']].strip(),
            'callsign': ship[column_index['callsign']],
            'length': round(float(ship[column_index['length']]), 0),
            'width': round(float(ship[column_index['width']]), 0),
            'type': ship[column_index['type']].strip(),
        }

    return lookup


def _build_column_index(rows: List[List[str]]) -> Dict[str, int]:
    header = rows[0]

    header_index = {}
    for index, value in enumerate(header):
        header_index[value.strip()] = index

    return header_index


def filter_and_clean_ais_items(signals, shipinformation):
    """
    Responsible for removing any irrelevant AIS signals.
    This function may need to handle quite large lists, so it might be useful
    to exploit dataprocessing libraries, such as Pandas
    :param ais_items:
    :return:
    """
    rows_signals = _from_csv(signals, delimiter=';')
    rows_shipinformation = _from_csv(shipinformation, delimiter=';')

    header = _build_column_index(rows_signals)
    metadata = _build_shipinfo_lookup(rows_shipinformation)

    signalpoints = []

    for row in rows_signals[1:]:
        if len(row) < len(header):
            print(f'Row {row} not the same length as header: {len(row)} != {len(header)}')
            continue
        lon = float(row[header['lon']])
        lat = float(row[header['lat']])

        if not VALID_OPERATING_AREA.is_in_area(lat, lon):
            continue

        mmsi = row[header['mmsi']].strip()
        timestamp = _attach_timezone_identifier(row[header['date_time_utc']])

        ship_signal = {
            'timestamp': timestamp,
            'ferryId': _hash_mmsi(mmsi),
            'lat': lat,
            'lon': lon,
            'source': 'ais',
        }

        # Does this signal have any metadata attached to it?
        if mmsi not in metadata:
            # print(f'Boat in OPERATING_AREA, but not in shipInfo. MMSI: {mmsi}. Keys: {metadata.keys()}')
            continue

        ship_heading = float(row[header['true_heading']])

        ship_signal['metadata'] = {
            'width': metadata[mmsi]['width'],
            'length': metadata[mmsi]['length'],
            'type': metadata[mmsi]['type'],
            'heading': ship_heading,
        }

        signalpoints.append(ship_signal)

    return signalpoints
