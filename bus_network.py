from classes import BusStop
from haversine import haversine, Unit
import pickle
import json
from pprint import pprint
from math import inf

"""
    This class represents the bus network and contains 
    methods to find the shortest route between two points.
    This class is used in the main_gui.py file.
    You can run this file to see an example of how to use this class.

"""


class BusNetwork:
    def __init__(self) -> None:
        with open('bus_network.pickle', 'rb') as file:
            bus_network = pickle.load(file)
            self.bus_stops = bus_network['stops']
            self.bus_services = bus_network['routes']
            file.close()

        with open('distances.json', 'r') as file:
            self.distances = json.load(file)
            file.close()

        # iterate through all bus stops
        # if distance between stops is less than 100m, add a walk route between them
        for stop_1 in self.distances:
            for stop_2 in self.distances[stop_1]:
                if self.distances[stop_1][stop_2] < 100 and self.distances[stop_1][stop_2] != 0:
                    stop_node_1 = self.bus_stops[stop_1]
                    stop_node_2 = self.bus_stops[stop_2]
                    stop_node_1.next_stops["walk"] = stop_node_2

    def get_route(self, start_coords, end_coords):
        closest_bus_stop_to_start = self.get_closest_node_to_coord(
            start_coords)
        closest_bus_stop_to_end = self.get_closest_node_to_coord(end_coords)

        # get shortest path between start and end bus stop nodes
        node_list = self.a_star(
            closest_bus_stop_to_start, closest_bus_stop_to_end)

        route = []

        start_index = 0

        # while there are still nodes to process
        while node_list:
            # setup route count

            route_count = {}

            # add all routes from first node to route count
            # and initialise their counts to 1
            for route_name in node_list[0].next_stops:
                route_count[route_name] = 1

            for index, node in enumerate(node_list):
                valid_routes = []

                if node is not closest_bus_stop_to_end:
                    # get all routes that are valid from this node
                    for route_name in node_list[index+1].next_stops:
                        if route_name in route_count:
                            valid_routes.append(route_name)

                # increment route count for all valid routes
                for route_name in valid_routes:
                    route_count[route_name] += 1

                if node is closest_bus_stop_to_end:
                    route.append({'bus_service': max(route_count, key=route_count.get),
                                  'nodes': node_list[start_index:index+1]})

                    start_node = BusStop(start_coords, start_coords)
                    end_node = BusStop(end_coords, end_coords)

                    route.insert(0, {'bus_service': 'walk',
                                     'nodes': [start_node, node_list[0]]})

                    route.append({'bus_service': 'walk',
                                  'nodes': [node_list[-1], end_node]})
                    return route

                # if no more valid routes
                if len(valid_routes) == 0:
                    if index == start_index + 1:
                        # walk to the next stop
                        route.append({'bus_service': 'walk',
                                      'nodes': node_list[start_index:index+1]})
                    else:
                        # add route to route list
                        route.append({'bus_service': max(route_count, key=route_count.get),
                                      'nodes': node_list[start_index:index+1]})

                    start_index = index

                    # temporarily remove walk routes from next stops
                    next_stops_wo_walk = self.without_keys(
                        node.next_stops, ['walk'])

                    # if next node in list is not in the next stops of the current node
                    if node_list[index+1] not in next_stops_wo_walk.values():
                        # walk to the next stop
                        route.append({'bus_service': 'walk',
                                      'nodes': node_list[start_index:index+2]})
                        start_index = index + 1

                    # reset route count dict
                    route_count = {}
                    # include current stop routes to the count
                    for route_name in node.next_stops:
                        route_count[route_name] = 1

                    continue

        return route

    # remove keys from dict
    def without_keys(self, d, keys):
        return {x: d[x] for x in d if x not in keys}

    def a_star(self, start_node, end_node):
        open_list = [start_node]
        closed_list = []

        cost = {}
        cost[start_node] = 0

        parents = {}
        parents[start_node] = start_node

        while open_list:
            current_node = None

            # get node with lowest cost in open list
            for node in open_list:

                if current_node == None or cost[node] + self.distances[node.name][end_node.name] < cost[current_node] + self.distances[current_node.name][end_node.name]:
                    current_node = node

            if current_node == None:
                print('No path')
                return None

            if current_node is end_node:
                path = []

                while parents[current_node] != current_node:
                    path.append(current_node)
                    current_node = parents[current_node]

                path.append(start_node)

                path.reverse()

                print('Path found')
                return path

            neighbor_nodes = current_node.next_stops

            for neighbor_node in neighbor_nodes.values():
                # calculate costs and add neighbor node to lists if node is new
                if neighbor_node not in open_list and neighbor_node not in closed_list:
                    open_list.append(neighbor_node)
                    parents[neighbor_node] = current_node
                    cost[neighbor_node] = cost[current_node] + \
                        self.distances[current_node.name][neighbor_node.name]

                else:
                    # if neighbor node is already in open list, check if new cost is lower
                    # if it is, update cost and parent
                    new_cost = cost[current_node] + \
                        self.distances[current_node.name][neighbor_node.name]
                    if new_cost < cost[neighbor_node]:
                        cost[neighbor_node] = new_cost
                        parents[neighbor_node] = current_node

                        # if neighbor node is in closed list, move it to open list
                        if neighbor_node in closed_list:
                            closed_list.remove(neighbor_node)
                            open_list.append(neighbor_node)

            # remove current node from the open_list, and add it to closed_list
            # because all of its neighbors were inspected
            open_list.remove(current_node)
            closed_list.append(current_node)

        print('No path')
        return None

    def get_closest_node_to_coord(self, coordinates):
        closest_dist = inf

        for bus_stop_node in self.bus_stops.values():
            current_dist = haversine(
                coordinates, bus_stop_node.coordinates, Unit.METERS)
            if current_dist < closest_dist:
                closest_node = bus_stop_node
                closest_dist = current_dist

        return closest_node


if __name__ == '__main__':
    bn = BusNetwork()

    # start coords are near kulai terminal, end coords are near senai airport
    optimal_route = bn.get_route(
        (1.663662, 103.598004), (1.635619, 103.665918))

    pprint(optimal_route)

    for route in optimal_route:
        print(f"From {route['nodes'][0].name}")
        if route['bus_service'] == 'walk':
            print(f"Walk to {route['nodes'][-1].name}")
        else:
            print(f"Take {route['bus_service']} to {route['nodes'][-1].name}")
