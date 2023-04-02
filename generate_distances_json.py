import pickle
import json
import concurrent.futures
import osmnx
import taxicab
from haversine import haversine, Unit

"""
This script generates a JSON file containing the distances between every bus stop in the network.
"""


def get_shortest_distance(start, end):
    # Use OSMnx to get the street network within the bounding box of the origin and destination points
    # Then use taxicab to find the shortest path between the origin and destination points
    try:
        G = osmnx.graph_from_bbox(start[0], end[0], start[1], end[1],
                                  network_type='walk', clean_periphery=True, truncate_by_edge=True)
        route = taxicab.distance.shortest_path(G, start, end)
    except:
        # If OSMnx fails, use haversine to calculate the distance between the origin and destination points
        return haversine(start, end, Unit.METERS)

    return route[0]


def main():
    # load bus network from pickle file
    with open('bus_network.pickle', 'rb') as file:
        bus_network = pickle.load(file)
        file.close()

    # get bus stops from bus network
    bus_stops = bus_network['stops']

    distances = {}

    # calculate distances between every stop
    for origin_stop_name in bus_stops:
        distances[origin_stop_name] = {}

        futures = {}
        with concurrent.futures.ProcessPoolExecutor() as executor:
            for destination_stop_name in bus_stops:

                if origin_stop_name == destination_stop_name:
                    distances[origin_stop_name][destination_stop_name] = 0

                origin_stop_node = bus_stops[origin_stop_name]
                destination_stop_node = bus_stops[destination_stop_name]

                # submit distance calculation to executor
                futures[executor.submit(get_shortest_distance, origin_stop_node.coordinates,
                                        destination_stop_node.coordinates)] = destination_stop_name

            # add results to distances dict as their futures complete
            for future in concurrent.futures.as_completed(futures):
                dest_name = futures[future]
                distance = future.result()

                print(f'{origin_stop_name} to {dest_name} : {distance}', flush=True)
                distances[origin_stop_name][dest_name] = distance

    # save distances dict to json file
    with open('distances.json', 'w') as file:
        json.dump(distances, file)


if __name__ == '__main__':
    main()
