import pickle

threshold = 222

with open('bus_network_w_distances.pickle', 'rb') as file:
    bus_network = pickle.load(file)
    bus_stops = bus_network['stops']
    bus_services = bus_network['routes']
    distances = bus_network['distances']

for stop in distances:
    web = distances[stop]
    for close in web:
        if web[close] < threshold:
            
            busStop_Obj1 = bus_stops[stop]
            nextStop = busStop_Obj1.next_stops
            busStop_Obj2 = bus_stops[close]

            nextStop["walk"] = busStop_Obj2
            busStop_Obj1.next_stops = nextStop

with open('bus_network_w_distances_{}.pickle'.format(threshold), 'wb') as file:
    pickle.dump(bus_network, file, protocol=pickle.HIGHEST_PROTOCOL)

