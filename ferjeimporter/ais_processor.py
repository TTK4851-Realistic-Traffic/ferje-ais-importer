from dataclasses import dataclass
import pandas as pd



@dataclass
class CoordinatesArea:
    min_lat: float = 0
    min_lon: float = 0
    max_lat: float = 0
    max_lon: float = 0


# Defines a range of lat and lon that each signal should be in.
# We start with a fairly small area, to avoid storing too much data.
VALID_OPERATING_AREA = CoordinatesArea(
    min_lat=63.3762,
    max_lat=63.58,
    min_lon=10.26,
    max_lon=10.5999
)


def is_signal_inside_area(signal, area: CoordinatesArea):
    return True


def filter_and_clean_ais_items(signals, shipinformation):
    """
    Responsible for removing any irrelevant AIS signals.
    This function may need to handle quite large lists, so it might be useful
    to exploit dataprocessing libraries, such as Pandas
    :param ais_items:
    :return:
    """
    df_signals = pd.DataFrame([x.split(';') for x in signals.split('\n')])
    new_header = df_signals.iloc[1] #grab the first row for the header
    df_signals = df_signals[2:] #take the data less the header row
    df_signals.columns = new_header #set the header row as the df header

    df_shipinformation= pd.DataFrame([x.split(';') for x in shipinformation.split('\n')])
    new_header1 = df_shipinformation.iloc[1] #grab the first row for the header
    df_shipinformation = df_shipinformation[2:] #take the data less the header row
    df_shipinformation.columns = new_header1 #set the header row as the df header
    
    
    shipinfo_dict=df_shipinformation.set_index('    mmsi').T.to_dict('list')
    signals_dict=df_signals.set_index('date_time_utc').T.to_dict('list')
  
    signalpoints=[]
    for ts, shippos in signals_dict.items():
        for ship, meterdata in shipinfo_dict.items():
            data= {
            "timestamp":ts,
            "lat":shippos[2],
            "lon":shippos[1],
            "ferryId":ship,
            "metadata": {"width":meterdata[4],
                        "height":meterdata[3],
                        "heading":shippos[5],
                        "type":meterdata[5]},
            }
        
            
        signalpoints.append(data)
    print(signalpoints)
    return shipinformation
