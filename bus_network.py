import pandas as pd
from utils import BusStop, BusRoute, get_shortest_distance, get_heuristic_distance
from haversine import haversine, Unit
import pickle
from pprint import pprint

class BusNetwork:
    def __init__(self) -> None:
        
        with open('bus_network_w_distances.pickle', 'rb') as file:
            bus_network = pickle.load(file)
            self.bus_stops = bus_network['stops']
            self.bus_services = bus_network['routes']
            self.distances = bus_network['distances']

            for name in self.distances:
                self.distances[name][name] = 0

    def get_route(self, start_name, end_name):
        start_node = self.bus_stops[start_name]
        end_node = self.bus_stops[end_name]

        # self.graph = osmnx.graph_from_bbox(start_node.coordinates[0], end_node.coordinates[0], start_node.coordinates[1], end_node.coordinates[1], network_type='walk')

        node_list = self.a_star_iterative(start_node, end_node)
        
        route = {}

        start_index = 0
        
        while node_list:
        # setup route count
            route_count = {}
            for route_name in node_list[0].next_stops:
                route_count[route_name] = 1

            for index, node in enumerate(node_list):
                valid_routes = []
                
                if node is not end_node:
                    for route_name in node_list[index+1].next_stops:
                        if route_name in route_count:
                            valid_routes.append(route_name)

                for route_name in valid_routes:
                    route_count[route_name] += 1

                if node is end_node:
                    route[max(route_count, key=route_count.get)] = node_list[start_index:index+1]
                    return route

                # if no more valid routes
                if len(valid_routes) == 0:
                    if index == start_index + 1:
                        # walk to the next stop
                        route['walk'] = node_list[start_index:index+1]
                    else:
                        # add bus route to route dict
                        route[max(route_count, key=route_count.get)] = node_list[start_index:index+1]

                    start_index = index

                    # reset route count dict
                    route_count = {}
                    # include current stop routes to the count
                    for route_name in node.next_stops:
                        route_count[route_name] = 1

                    continue

        return route
    
    def a_star_iterative(self, start_node, end_node):
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

            # print(current_node.name)

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
                    cost[neighbor_node] = cost[current_node] + self.distances[current_node.name][neighbor_node.name]

                else:
                    new_cost = cost[current_node] + self.distances[current_node.name][neighbor_node.name]
                    if new_cost < cost[neighbor_node]:
                        cost[neighbor_node] = new_cost
                        parents[neighbor_node] = current_node

                        if neighbor_node in closed_list:
                            closed_list.remove(neighbor_node)
                            open_list.append(neighbor_node)

            # remove current node from the open_list, and add it to closed_list
            # because all of its neighbors were inspected
            open_list.remove(current_node)
            closed_list.append(current_node)

        print('No path')
        return None

    def a_star_walk(self, start_node : BusStop, end_node : BusStop, distance = 0):
        print(f'{start_node.name} {start_node.coordinates}')
        if end_node is start_node:
            return [end_node]
        
        neighbor_nodes = []

        # find top 3 closest nodes to start node
        for i in range(5):
            closest_distance = 0
            closest_node = None

            for node_name in self.bus_stops:
                current_node = self.bus_stops[node_name]

                if (current_node is start_node) or (current_node in neighbor_nodes):
                    continue

                distance_from_start = haversine(start_node.coordinates, current_node.coordinates, Unit.METERS)

                if closest_node is None:
                    closest_node = current_node
                    closest_distance = distance_from_start
                elif distance_from_start < closest_distance:
                    closest_node = current_node
                    closest_distance = distance_from_start

            neighbor_nodes.append(closest_node)


        shortest_node = None
        shortest_distance = 0

        for current_node in neighbor_nodes:
            distance_from_start = distance + get_shortest_distance(start_node.coordinates, current_node.coordinates)
            distance_from_end = get_shortest_distance(end_node.coordinates, current_node.coordinates)
            prority_distance = distance_from_start + distance_from_end

            if shortest_node is None:
                shortest_node = current_node
                shortest_distance = prority_distance
                dist_from_beginning = distance_from_start

            elif prority_distance < shortest_distance:
                shortest_node = current_node
                shortest_distance = prority_distance
                dist_from_beginning = distance_from_start
        
        return [start_node] + self.a_star_walk(shortest_node, end_node, dist_from_beginning)


if __name__ == '__main__':
    bn = BusNetwork()
    optimal_route = bn.get_route('Majlis Bandaraya Johor Bahru', "AEON Tebrau City")

    pprint(optimal_route)
    
    for bus_service in optimal_route:
        print(f'From {optimal_route[bus_service][0].name}')
        print(f'Take {bus_service} to {optimal_route[bus_service][-1].name}')
