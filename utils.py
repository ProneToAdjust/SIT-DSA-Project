from haversine import haversine, Unit
import osmnx
import taxicab

class BusStop():
    def __init__(self, name, coordinates) -> None:
        self.name = name
        self.coordinates = coordinates
        self.next_stops = {}

class BusRoute():
    def __init__(self, name) -> None:
        self.name = name
        # Tail of linked list
        self.starting_stop = None
        # Head of linked list
        self.end_stop = None

    def append(self, bus_stop):
        if self.starting_stop is None and self.end_stop is None:
            self.starting_stop = bus_stop
            self.end_stop = bus_stop
        else:
            # distance = get_shortest_distance(self.end_stop.coordinates, bus_stop.coordinates)
            # self.end_stop.next_stops[self.name] = {'node':bus_stop,
            #                                        'distance':distance}
            self.end_stop.next_stops[self.name] = bus_stop
            self.end_stop = bus_stop

def get_shortest_distance(start, end):
    return haversine(start, end)

# def get_shortest_distance(start, end):
#     # direct_dist = haversine(start,end, Unit.METERS)

#     # if direct_dist == 0:
#     #     return 0
    
#     # Use OSMnx to get the street network within the bounding box of the origin and destination points
#     try:
#         G = osmnx.graph_from_bbox(start[0], end[0], start[1], end[1], network_type='all', simplify=True, clean_periphery=True, truncate_by_edge=True)
#         route = taxicab.distance.shortest_path(G, start, end)
#         print('taxicab all')
#         # taxicab.plot_graph_route(G, route)
#     except:
#         try:
#             G = osmnx.graph_from_bbox(start[0], end[0], start[1], end[1], network_type='walk', simplify=True, clean_periphery=True, truncate_by_edge=True)
#             route = taxicab.distance.shortest_path(G, start, end)
#             print('taxicab walk')
#             # taxicab.plot_graph_route(G, route)
#         except:
#             print('haversine')
#             return haversine(start, end, Unit.METERS)
#         # print('haversine')
#         # return haversine(start, end, Unit.METERS)

#     return route[0]

def get_heuristic_distance(start, end, G):
    try:
        route = taxicab.distance.shortest_path(G, start, end)
        # taxicab.plot_graph_route(G, route)
    except:
        return haversine(start, end, Unit.METERS)

    return route[0]