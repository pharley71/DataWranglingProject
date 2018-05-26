from geopy.geocoders import Nominatim

locations = [{'coords' : "34.0047224,-81.0591962"}, {'coords' : '33.9338191,-81.0499368'},
				 {'coords' : '33.9803091,-81.1091304'}, {'coords' : '34.044205,-81.11962'},
				 {'coords' : '33.9813462,-81.1048867'}, {'coords' : '33.9773984,-81.0458274'},
				 {'coords' : '33.9991199,-81.0538139'}, {'coords' : '33.991304,-81.048109'},
				 {'coords' : '34.0792974,-80.9568832'}, {'coords' : '34.0779897, -80.9566052'}]

richland = [{'coords' : '34.0792974, -80.9568832'}, {'coords' : '34.0779897, -80.9566052'}, 
            {'coords' : '34.0789751, -80.9567636'}]				 

def fetch_locations(locations):
	from geopy.geocoders import Nominatim
	
	geolocator = Nominatim()
	for l in locations: 
		location = geolocator.reverse(l['coords'])
		print(location.address)
		
	richland = [{'coords' : '34.0792974, -80.9568832'}, {'coords' : '34.0779897, -80.9566052'}, 
				{'coords' : '34.0789751, -80.9567636'}]
	for r in richland: 
		location = geolocator.reverse(r['coords'])
		print(location.address)	