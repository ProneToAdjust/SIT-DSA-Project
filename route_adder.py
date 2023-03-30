import pickle
import json

with open('bus_network_w_distances.pickle', 'rb') as file:
    bus_network = pickle.load(file)
    bus_stops = bus_network['stops']
    distances = bus_network['distances']

# 'route_base.json', 'route_base_modified', 222
def juice_route_modify(filename_in, filename_out, threshold):
    f = open(filename_in)
    data = json.load(f)
    f.close()

    for stop in distances:
        web = distances[stop]
        for close in web:
            if web[close] < threshold:
                dump = data.get(stop)
                info = {"name":close,"transport":"walk","distance":web[close]}
                dump.append(info)
                data[stop] = dump

    file = open('{}{}.json'.format(filename_out,threshold), 'w')
    file.write(json.dumps(data))
    file.close()

# 'route_base.json'
def juice_route(filename):
    data = {}
    for stop in bus_stops:
        data1 = []
        links = bus_stops.get(stop).next_stops
        for link in links: 
            data2 = {}

            next_stop = links.get(link).name
            distance = distances[stop][next_stop]

            data2["name"] = next_stop
            data2["transport"] = link
            data2["distance"] = distance
            data1.append(data2)
        data[stop] = data1

    file = open(filename, 'w')
    file.write(json.dumps(data))
    file.close()

juice_route_modify('route_base.json', 'route_base_modified', 222)
