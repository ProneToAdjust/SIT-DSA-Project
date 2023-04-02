import pandas as pd
import pickle
from classes import BusStop, BusRoute

"""
    This script generates a data structure that represents the bus network and 
    stores it in a pickle file to be used in bus_network.py.
"""


def main():
    sheets = pd.read_excel("bus_stops.xlsx", sheet_name=None)

    bus_stops = {}
    bus_routes = {}

    for bus_name in sheets:
        bus_route = BusRoute(bus_name)

        # for every bus stop in sheet get name and coordinates
        for stop_name, gps_loc in zip(sheets[bus_name]['Bus stop'], sheets[bus_name]['GPS Location']):

            # split coordinates to longitude and latitude, skip row if no coordinates
            try:
                bus_stop_coords = tuple(map(float, gps_loc.split(', ')))
            except ValueError:
                continue

            node = None

            # get node if it exists else make new node
            if stop_name in bus_stops:
                node = bus_stops[stop_name]
            else:
                bus_stops[stop_name] = BusStop(stop_name, bus_stop_coords)
                node = bus_stops[stop_name]

            # append node to bus route
            bus_route.append(node)

        bus_routes[bus_name] = bus_route

    bus_network = {'stops': bus_stops,
                   'routes': bus_routes}

    # save data structure to file
    with open('bus_network.pickle', 'wb') as file:
        pickle.dump(bus_network, file)


if __name__ == '__main__':
    main()
