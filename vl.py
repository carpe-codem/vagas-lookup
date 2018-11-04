#!/usr/bin/env python2

import os
import osmnx as ox
import networkx as nx
import matplotlib.cm as cm
import matplotlib.colors as colors
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import googlemaps

GOOGLEAPI = os.environ['GOOGLEAPI']

ox.config(log_file=True, log_console=True, use_cache=True)
gmaps = googlemaps.Client(key=GOOGLEAPI)

def remove_adjacent(nums):
    a = nums[:1]
    for item in nums[1:]:
        if item != a[-1]:
            a.append(item)
        return a

def get_waypoints_by_address(address, network_type='walk', maxtime=15, gmaps=None, vagas_df=None, plot=False):
    if gmaps is None:
        gmaps = googlemaps.Client(key='AIzaSyCKLToq3Xfzj-IfIO-y931NlVQJiKOLd2M')
    geocode = gmaps.geocode(address)
    loc = geocode[0]['geometry']['location']
    return get_waypoints_by_lat_long(loc['lat'], loc['lng'], maxtime=maxtime, vagas_df=vagas_df, plot=plot)

def get_waypoints_by_lat_long(lat, long, network_type='walk', maxtime=15, vagas_df=None, plot=False):
    G = ox.graph_from_point((lat, long), network_type=network_type)
    dest_node = ox.get_nearest_node(G, (lat, long))
    
    ##################################################
    # Compute `time` and `vagastime` edge attributes
    #     time = length / speed
    #     vagastime = time / vagas
    ##################################################
    travel_speed = 3.5 #walking speed in km/hour
    meters_per_minute = travel_speed * 1000 / 60 #km per hour to m per minute
    for u, v, k, data in G.edges(data=True, keys=True):
        data['time'] = data['length'] / meters_per_minute
        data['vagastime'] = data['length'] / meters_per_minute

        edge_in_list = vagas_df[vagas_df.ID == "%d-%d" % (u, v)]
        if len(edge_in_list.index): # nonempty
            vaga = edge_in_list.iloc[0].TemVaga
            if vaga == 0:
                G.remove_edge(u, v)
            else:
                data['vagastime'] /= vaga

        edge_in_list = vagas_df[vagas_df.ID == "%d-%d" % (v, u)]
        if len(edge_in_list.index): # nonempty
            vaga = edge_in_list.iloc[0].TemVaga
            if vaga == 0:
                G.remove_edge(u, v)
            else:
                data['vagastime'] /= vaga
                
    ##################################################
    # Compute `isochrones`. Ensures we are within
    # walking distance
    ##################################################
    trip_times = np.linspace(5, maxtime, num=10) #in minutes
    iso_colors = ox.get_colors(n=len(trip_times), cmap='Reds', start=0.3, return_hex=True)
    node_colors = {}
    for trip_time, color in zip(sorted(trip_times, reverse=True), iso_colors):
        subgraph = nx.ego_graph(G, dest_node, radius=trip_time, distance='vagastime')
        for node in subgraph.nodes():
            node_colors[node] = color
    nc = [node_colors[node] if node in node_colors else 'none' for node in G.nodes()]
    
    if plot:
        nc = ['k' if node  == dest_node else nc[i] for (i, node) in enumerate(G.nodes())] # Make dest node black
        ns = [30 if node in node_colors else 0 for node in G.nodes()]
        ns = [500 if node  == dest_node else ns[i] for (i, node) in enumerate(G.nodes())] # Make dest node large
        ox.plot_graph(G, fig_height=8, node_color=nc, node_size=ns, node_alpha=0.8, node_zorder=2)       
    
    ##################################################
    # Compute all routes to every place, get line segments
    ##################################################
    routes = []
    for color, node in zip(nc, G.nodes()):
        if color != 'none':
            routes.append(nx.shortest_path(G, dest_node, node, weight='length'))
            
    lines = []
    for i, route in enumerate(routes):
        lines_route = []
        edge_nodes = list(zip(route[:-1], route[1:]))
        for u, v in edge_nodes:
            # if there are parallel edges, select the shortest in length
            data = min(G.get_edge_data(u, v).values(), key=lambda x: x['length'])
            # if it has a geometry attribute (ie, a list of line segments)
            if 'geometry' in data:
                # add them to the list of lines to plot
                xs, ys = data['geometry'].xy
                #print(i)
                #print("geom")
                #print(list(zip(xs, ys)))
                lines_route += list(zip(xs, ys))
            else:
                # if it doesn't have a geometry attribute, the edge is a straight
                # line from node to node
                x1 = G.nodes[u]['x']
                y1 = G.nodes[u]['y']
                x2 = G.nodes[v]['x']
                y2 = G.nodes[v]['y']
                line = [(x1, y1), (x2, y2)]
                #print(i)
                #print("line")
                #print(line)
                lines_route += line

        lines.append(remove_adjacent(lines_route))
    return lines
