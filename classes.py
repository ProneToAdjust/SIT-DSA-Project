"""
    This file contains the classes used in the project.
"""


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
            self.end_stop.next_stops[self.name] = bus_stop
            self.end_stop = bus_stop
