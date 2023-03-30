from utils import BusStop
from haversine import haversine, Unit
import pickle
from pprint import pprint
from math import inf

class BusNetwork:
    def __init__(self) -> None:
        with open('bus_network_w_distances_222.pickle', 'rb') as file:
            bus_network = pickle.load(file)
            self.bus_stops = bus_network['stops']
            self.bus_services = bus_network['routes']
            self.distances = bus_network['distances']

            for name in self.distances:
                self.distances[name][name] = 0

    def get_route(self, start_coords, end_coords):
        closest_bus_stop_to_start = self.get_closest_node_to_coord(start_coords)
        closest_bus_stop_to_end = self.get_closest_node_to_coord(end_coords)

        node_list = self.a_star_iterative(closest_bus_stop_to_start, closest_bus_stop_to_end)

        # optimal_route = self.optimize_route(node_list)

        # if optimal_route is not None:
        #     node_list = optimal_route
        
        route = []

        start_index = 0
        
        while node_list:
        # setup route count
            route_count = {}
            for route_name in node_list[0].next_stops:
                route_count[route_name] = 1

            for index, node in enumerate(node_list):
                valid_routes = []
                
                if node is not closest_bus_stop_to_end:
                    for route_name in node_list[index+1].next_stops:
                        if route_name in route_count:
                            valid_routes.append(route_name)

                for route_name in valid_routes:
                    route_count[route_name] += 1

                if node is closest_bus_stop_to_end:
                    route.append({'bus_service' : max(route_count, key=route_count.get),
                                  'nodes' : node_list[start_index:index+1]})
                    
                    start_node = BusStop(start_coords, start_coords)
                    end_node = BusStop(end_coords, end_coords)

                    route.insert(0, {'bus_service' : 'walk',
                                    'nodes': [start_node , node_list[0]]})
                    
                    route.append({'bus_service' : 'walk',
                                'nodes': [node_list[-1] , end_node]})
                    return route

                # if no more valid routes
                if len(valid_routes) == 0:
                    if index == start_index + 1:
                        # walk to the next stop
                        route.append({'bus_service' : 'walk',
                                      'nodes' : node_list[start_index:index+1]})
                    else:
                        # add bus route to route dict
                        route.append({'bus_service' : max(route_count, key=route_count.get),
                                      'nodes' : node_list[start_index:index+1]})

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

    def get_closest_node_to_coord(self, coordinates):
        closest_dist = inf

        for bus_stop_node in self.bus_stops.values():
            current_dist = haversine(coordinates, bus_stop_node.coordinates, Unit.METERS)
            if current_dist < closest_dist:
                closest_node = bus_stop_node
                closest_dist = current_dist

        return closest_node
            
if __name__ == '__main__':
    bn = BusNetwork()

    # start coords are near kulai terminal, end coords are near senai airport
    optimal_route = bn.get_route((1.663662, 103.598004), (1.635619, 103.665918))

    pprint(optimal_route)

    for route in optimal_route:
        print(f"From {route['nodes'][0].name}")
        if route['bus_service'] == 'walk':
            print(f"Walk to {route['nodes'][-1].name}")
        else:
            print(f"Take {route['bus_service']} to {route['nodes'][-1].name}")
    
