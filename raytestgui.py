import pandas as pd
from classes import BusStop, BusRoute
from haversine import haversine, Unit
import pickle
from pprint import pprint
import sys
import io
import folium
from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import QWebEngineView
from folium.plugins import LocateControl
import openrouteservice
import json
from bus_network import BusNetwork
from folium.plugins import MousePosition
from folium.vector_layers import PolyLine, Marker
import ipywidgets as widgets
from IPython.display import display

# retrieve rows based on Lat/Long columns
#place_lat = data.Latitude
#place_lng = data.Longtitude
# create empty lists to store the latitude and longitude coordinates of the markers
start_coords = []
dest_coords = []

print(folium.__version__)


# creating the Map GUI
class MyApp(QWidget):
    def __init__(self, lat, long):
        super().__init__()
        self.setWindowTitle('Malaysia Bus Route Map')
        self.window_width, self.window_height = 1050, 900
        self.setMinimumSize(self.window_width, self.window_height)

        layout = QHBoxLayout()
        self.setLayout(layout)

        # Define the width and height of the QWebEngineView widget
        map_width, map_height = 1200, 1600
        
        # Create textboxes instances
        self.textBox_start = QLineEdit()
        self.textBox_end = QLineEdit()
        # Create textboxes placeholders
        self.textBox_start.setPlaceholderText("Enter source...")
        self.textBox_end.setPlaceholderText("Enter destination...")
        # Create textboxes sizes
        self.textBox_start.setFixedSize(350, 50)
        self.textBox_end.setFixedSize(350, 50)
        # Create searchButton instance and onclick function
        self.search_button = QPushButton((self.tr("Find path")))
        # Connect the search button to the on_button_click function
        self.search_button.clicked.connect(self.on_button_click)
        # Create clear button instance and onclick function
        self.clear_button = QPushButton((self.tr("Clear the map")))
        # Connect the clear button to the empty_map function
        self.clear_button.clicked.connect(self.empty_map)

        
        # Add the buttons and textfields to a QHBoxLayout
        self.button_layout_top = QHBoxLayout()
        self.button_layout_mid = QHBoxLayout()
        self.main_layout = QVBoxLayout()
        self.button_layout_top.addWidget(self.textBox_start)
        self.button_layout_top.addWidget(self.textBox_end)
        self.button_layout_mid.addWidget(self.search_button)
        self.button_layout_mid.addWidget(self.clear_button)
        self.main_layout.addLayout(self.button_layout_top)
        self.main_layout.addLayout(self.button_layout_mid)
        # Set the alignments of the button layouts
        self.button_layout_top.setAlignment(QtCore.Qt.AlignTop)
        self.button_layout_mid.setAlignment(QtCore.Qt.AlignTop)
        self.main_layout.setAlignment(QtCore.Qt.AlignTop)

        # Add the button layout to the main layout
        layout.addLayout(self.main_layout)

        # Define the initial map coordinates and zoom level
        coordinate = (lat,long)

        # Create the folium map
        self.m = folium.Map(
            tiles='openstreetmap',
            zoom_start=13,
            location=coordinate,
            html='<div style="font-size: 25px"></div>'
        )
        folium.LatLngPopup().add_to(self.m)

        # Customize layer control CSS style
        css = """
        <style>
        .leaflet-control-layers, .leaflet-control-layers-expanded {
            font-size: 23px !important;
        }
        </style>
        """

        self.m.get_root().header.add_child(folium.Element(css))

        # Add layer control to map
        folium.LayerControl().add_to(self.m)

        # Add locate control to map
        LocateControl().add_to(self.m)

        # Save the folium map data to a BytesIO object
        data = io.BytesIO()
        self.m.save(data, close_file=False)

        # Create a QWebEngineView widget and set its size
        self.webView = QWebEngineView()
        self.webView.setHtml(data.getvalue().decode())
        
        # Alter the PYQT5 window size when maximised
        def check_window_state(self, webView):
            if self.isMaximized():
                self.webView.setFixedSize(map_width, map_height)

        layout.addWidget(self.webView)

        # Align the web view to the right
        layout.setAlignment(self.webView, QtCore.Qt.AlignRight)
        
        # set the size of the map widget based on the size of the main window
        self.webView.setMinimumSize(self.sizeHint())

        # connect the resize event of the main window to the function that resizes the map widget
        self.resize
        self.m

    # runs when "get path" button has been clicked
    def on_button_click(self):
        # get data from the textfields and initialise into the coordinates variables
        startcoordinate = self.textBox_start.text()
        endcoordinate = self.textBox_end.text()

        # split the data into comma seperated array
        startcoord = [float(x) for x in startcoordinate.split(",")]
        endcoord = [float(x) for x in endcoordinate.split(",")]

        # specify an icon of your desired shape or chosing in place for the coordinates points
        services = 0
        locations = []
        walking = []
        # read the bus network get_route with the start and end coordinates
        data = BusNetwork().get_route((startcoord), (endcoord))
        # iterate the bus nodes
        for route in data:
            services += 1
            # for actual bus stops
            if route['bus_service'] != 'walk':
                for i in range(0, len(route['nodes'])):
                    # different services = different colours
                    if services % 2 == 0:
                        colour = 'blue'
                    else:
                        colour = 'green'
                    # put node name as popup content
                    popup_content = '<div style="font-size:25px;">{}</div>'.format(route['nodes'][i].name)
                    # place a marker at each bus stop locations
                    folium.Marker(
                        [route['nodes'][i].coordinates[0], route['nodes'][i].coordinates[1]],
                        popup=folium.Popup(popup_content, max_width=200, min_width=150),
                        icon=folium.Icon(color=colour, icon_color='white', prefix='fa', icon='bus', icon_size=(35, 35),
                                        icon_anchor=(15, 15))
                    ).add_to(self.m)
                    # append the location list with coordinates of the bus stops in long, lat format
                    locations.append([route['nodes'][i].coordinates[1], route['nodes'][i].coordinates[0]])
                    # slice the array into long and lat
                locations = [[coord[0], coord[1]] for coord in locations]
                # use openrouteservice to draw the route of the bus
                routing_bus = client.directions(
                    coordinates=locations,
                    profile='driving-car',
                    format='geojson',
                )
                # get the route from the routing_bus function
                spots_bus = [[coord[1], coord[0]] for coord in routing_bus['features'][0]['geometry']['coordinates']]
                # draw the route on the folium map
                folium.PolyLine(locations=spots_bus,weight=7).add_to(self.m)
                    
            # for walking points        
            elif route['bus_service'] == 'walk':
                # iterate through all the walking nodes
                for i in range(0, len(route['nodes'])):
                    # put node name as popup content
                    popup_content = '<div style="font-size:25px;">{}</div>'.format(route['nodes'][i].name)
                    # place a marker at each walking locations
                    folium.Marker(
                        [route['nodes'][i].coordinates[0], route['nodes'][i].coordinates[1]],
                        popup=folium.Popup(popup_content, max_width=200, min_width=150),
                        icon=folium.Icon(color='orange', icon_color='white', prefix='fa', icon='man', icon_size=(35, 35),
                                        icon_anchor=(15, 15))
                    ).add_to(self.m)
                    # append the walking list with coordinates of the bus stops in long, lat format
                    walking.append([route['nodes'][i].coordinates[1], route['nodes'][i].coordinates[0]])
                    # get a pair of the walking coordinates and draw the route using openrouteservice
                for i in range(0, len(route['nodes'])-1, 2):
                    first_walk = walking[i]
                    second_walk = walking[i+1]
                    routing_walking = client.directions(
                        coordinates=[first_walk, second_walk],
                        profile='foot-walking',
                        format='geojson',
                    )
                    # get the route from the routing_walking
                    spots_walking = [[coord[1], coord[0]] for coord in routing_walking['features'][0]['geometry']['coordinates']]
                    # draw the walking route on the folium map
                    folium.PolyLine(locations=spots_walking,weight=5,color='green').add_to(self.m)

        # put a marker at the start of the route
        folium.Marker(
            location=[float(startcoord[0]), float(startcoord[1])],
            popup="Start"
        ).add_to(self.m)

        # put a marker at the end of the route
        folium.Marker(
            location=[float(endcoord[0]), float(endcoord[1])],
            popup="Destination"
        ).add_to(self.m)
        

        # Save the folium map data to a BytesIO object
        data = io.BytesIO()
        self.m.save(data, close_file=False)

        # Update the QWebEngineView widget with the new map data
        self.webView.setHtml(data.getvalue().decode())

    def empty_map(self):
    # Clear all markers and polylines
        for layer in self.m._children:
            if isinstance(layer, Marker) or isinstance(layer, PolyLine) or isinstance(layer, folium.FeatureGroup):
                self.m.remove_layer(layer)
        

if __name__ == '__main__':
    bn = BusNetwork()

    # start coords are near kulai terminal, end coords are near senai airport
    #startingcoords = (1.663662, 103.598004)
    #optimal_route = bn.get_route(startingcoords, (1.635619, 103.665918))
    
    # start coords are econsave, end coords are near kulai terminal
    startingcoords = (1.611519115179376, 103.65587602883747)
    optimal_route = bn.get_route(startingcoords, (1.6618215659380255, 103.59852337572669))

    # print route to show data structure
    #pprint(optimal_route)
    print("Bus stops")
    
    for route in optimal_route:
        if route['bus_service'] != 'walk':
            for i in range (0, len(route['nodes'])):
                print(route['nodes'][i].coordinates)
    
       # if route['bus_service'] != 'walk':
        #    print(f"location {route['bus_service']} and {route['nodes'][-1].name}")
    
        
    print("----------------")
    print("Route here")
    print("----------------")
    
    for route in optimal_route:
        print(f"From {route['nodes'][0].name}")
        if route['bus_service'] == 'walk':
            print(f"Walk to {route['nodes'][-1].name}")
        else:
            print(f"Take {route['bus_service']} to {route['nodes'][-1].name}")
    
    # initialise openrouteservice client with the API key
    client = openrouteservice.Client(key='5b3ce3597851110001cf6248c8894c015c094545be85cfc3aaf5b86f')
    app = QApplication(sys.argv)
    app.setStyleSheet('''
        QWidget {
            font-size: 35px;
        }
    ''')
    
    myApp = MyApp(1.611519115179376, 103.65587602883747)
    myApp.show()
    try:
        sys.exit(app.exec_())
    except SystemExit:
        print('Closing Window...')