from utils import BusStop
from haversine import haversine, Unit
import pickle
from pprint import pprint
import json
from math import inf

class BusNetwork:
    def __init__(self) -> None:
        f = open('route_modified222.json')
        self.route = json.load(f)
        f.close()

        f = open('gps.json')
        self.gps = json.load(f)
        f.close()

        # previous version
        with open('bus_network_w_distances.pickle', 'rb') as file:
            bus_network = pickle.load(file)
            self.bus_stops = bus_network['stops']
            self.bus_services = bus_network['routes']
            self.distances = bus_network['distances']

            for name in self.distances:
                self.distances[name][name] = 0

    def get_route_json(self, start_coords, end_coords):
        closest_start_stop_name = self.closest_stop_to_coord_json(start_coords)
        closest_end_stop_name = self.closest_stop_to_coord_json(end_coords)
        
        path = [[closest_start_stop_name,"WALK",0]]

        if closest_start_stop_name != closest_end_stop_name:
            path = self.a_star_json(closest_start_stop_name, closest_end_stop_name)

        return path
    
    def closest_stop_to_coord_json(self, coords):
        closest_stop_dist = inf
        for stop_name in self.gps:
            current_stop_dist = haversine(coords, tuple(self.gps[stop_name]), Unit.METERS)
            if current_stop_dist < closest_stop_dist:
                closest_stop_name = str(stop_name)
                closest_stop_dist = current_stop_dist
        return closest_stop_name

    def a_star_json(self, closest_start_stop_name, closest_end_stop_name):
        end_coords = tuple(self.gps[closest_end_stop_name])
        hueristics_dist = haversine(tuple(self.gps[closest_start_stop_name]), end_coords, Unit.METERS)
        open = {closest_start_stop_name:{"from":closest_start_stop_name, "cost":0, "hueristics":hueristics_dist, "transport":"WALK"}}
        close = {}
        current_stop_name = closest_start_stop_name

        #range 0 to INFINITY
        walking_penalty = 3
        #range 0 to 1
        bus_incentive = 0.6
        #range 0 to 1
        same_bus_incentive = 0.9

        while current_stop_name != closest_end_stop_name:
            # Check routes for current stop
            next_stop_info = self.route[current_stop_name]
            for next_stop_name in next_stop_info:
                # Continues if next stop not in closed route
                if close.get(next_stop_name.get("name")) == None:
                    # Check if next stop exists in open route
                    # if it does not exist, add it to open route
                    # otherwise update if the cost is lower
                    if open.get(next_stop_name.get("name")) == None:
                        next_stop_cost = open[current_stop_name]["cost"] + next_stop_name.get("distance")
                        next_stop_hueristics = haversine(tuple(self.gps[next_stop_name.get("name")]), end_coords, Unit.METERS)
                        next_stop_transport = next_stop_name.get("transport")

                        current_transport = open[current_stop_name]["transport"]

                        # Penalize walking and incintivize travelling by bus 
                        if next_stop_transport == "walk":
                            next_stop_cost += next_stop_name.get("distance") * walking_penalty
                        elif next_stop_transport == current_transport:
                            next_stop_cost -= next_stop_name.get("distance") * same_bus_incentive
                        else:
                            next_stop_cost -= next_stop_name.get("distance") * bus_incentive

                        open[next_stop_name.get("name")] = {
                            "from":current_stop_name, 
                            "cost":next_stop_cost, 
                            "hueristics":next_stop_hueristics, 
                            "transport":next_stop_transport}
                    else:
                        next_stop_cost_new = open[current_stop_name]["cost"] + next_stop_name.get("distance")
                        next_stop_transport_new = next_stop_name.get("transport")

                        next_stop_cost_current = open[next_stop_name.get("name")]["cost"]
                        current_transport = open[current_stop_name]["transport"]

                        # Penalize walking and incintivize travelling by bus
                        if next_stop_transport_new == "walk":
                            next_stop_cost_new += next_stop_name.get("distance") * walking_penalty
                        elif next_stop_transport_new == current_transport:
                            next_stop_cost_new -= next_stop_name.get("distance") * same_bus_incentive
                        else:
                            next_stop_cost_new -= next_stop_name.get("distance") * bus_incentive

                        if next_stop_cost_new < next_stop_cost_current:
                            open[next_stop_name.get("name")]["from"] = current_stop_name
                            open[next_stop_name.get("name")]["cost"] = next_stop_cost_new
                            open[next_stop_name.get("name")]["transport"] = next_stop_transport_new

            # Shift current stop from open list into close list
            close[current_stop_name] = open[current_stop_name]
            open.pop(current_stop_name)

            # Get the closest stop from the open queue
            closest_stop_dist = inf
            for bus_stop in open:
                bus_stop_cost = open[bus_stop]["cost"]
                bus_stop_hueristics = open[bus_stop]["hueristics"]
                bus_stop_total = bus_stop_cost + bus_stop_hueristics
                if bus_stop_total < closest_stop_dist:
                    current_stop_name = bus_stop
                    closest_stop_dist = bus_stop_total

        # Shift end stop from open list into close list
        close[current_stop_name] = open[current_stop_name]
        open.pop(current_stop_name)

        route = []
        while current_stop_name != closest_start_stop_name:
            route.append([current_stop_name, close[current_stop_name]["transport"], close[current_stop_name]["cost"]])
            current_stop_name = close[current_stop_name]["from"]
        route.append([current_stop_name, close[current_stop_name]["transport"], close[current_stop_name]["cost"]])
        route.reverse()

        return route


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
    
    def get_closest_nodes(self, origin_node, no_of_nodes, node_list, open_list, closed_list):
        closest_nodes = []

        for i in range(no_of_nodes):
            closest_node = None

            for j, surrounding_node in enumerate(node_list):
                if surrounding_node == origin_node or surrounding_node in closest_nodes:
                    continue

                if surrounding_node in open_list or surrounding_node in closed_list:
                    continue

                if not self.on_same_line(origin_node, surrounding_node):
                    if self.distances[origin_node.name][surrounding_node.name] > 400:
                        continue

                if closest_node is None or self.distances[origin_node.name][surrounding_node.name] < self.distances[origin_node.name][closest_node.name]:
                    closest_node = surrounding_node

            closest_nodes.append(closest_node)

        origin_node_index = node_list.index(origin_node)
        for node in closest_nodes:
            # skip if the stop after the next stop is the current stop
            try:
                if node is node_list[origin_node_index+2]:
                    closest_nodes.remove(node)
            except IndexError:
                continue

        return closest_nodes

    def a_star_walk(self, start_node : BusStop, end_node : BusStop):
        neighbor_nodes = []

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

            neighbor_nodes = self.get_closest_nodes(current_node, 1)

            for neighbor_node in neighbor_nodes:
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

    def optimize_route(self, path):
        start_node = path[0]
        end_node = path[-1]

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

            print(current_node.name)

            if current_node == None:
                print('No path')
                return None
            
            if current_node is end_node:
                new_path = []

                while parents[current_node] != current_node:
                    new_path.append(current_node)
                    current_node = parents[current_node]

                new_path.append(start_node)

                new_path.reverse()

                print('Path found')
                return new_path

            neighbor_nodes = self.get_closest_nodes(current_node, 2, path, open_list, closed_list)

            for neighbor_node in neighbor_nodes:
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

    def on_same_line(self, node, other_node):
        for bus_service in node.next_stops:
            for other_bus_service in other_node.next_stops:
                if bus_service == other_bus_service:
                    return True
                
        return False

    def get_closest_node_to_coord(self, coordinates):
        closest_node = None

        for bus_stop_node in self.bus_stops.values():
            if closest_node is None or haversine(coordinates, bus_stop_node.coordinates, Unit.METERS) < haversine(coordinates, closest_node.coordinates, Unit.METERS):
                closest_node = bus_stop_node

        return closest_node
            
if __name__ == '__main__':
    bn = BusNetwork()

    # start coords are near kulai terminal, end coords are near senai airport
    optimal_route = bn.get_route_json((1.663662, 103.598004), (1.635619, 103.665918))

    # print route to show data structure
    for x in optimal_route:
        print(x)
    
