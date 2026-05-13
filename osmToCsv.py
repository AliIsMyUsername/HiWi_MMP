#run this script using python in terminal using the folowing instructions to make sure that it works
#python3 -m venv osm_env
#source osm_env/bin/activate
#pip install osmium
# once you're done running the script and having the required output you can deactivate the virtual environment 
#deactivate

import osmium
import csv

class BusinessExtractor(osmium.SimpleHandler):
    def __init__(self, output_file):
        super().__init__()
        self.file = open(output_file, "w", newline='', encoding="utf-8")
        self.writer = csv.writer(self.file)

        self.writer.writerow([
            "name", "amenity",
            "street", "housenumber", "city",
            "lat", "lon"
        ])

    def node(self, n):
        amenity = n.tags.get("amenity")
        if amenity:
            try:
                self.writer.writerow([
                    n.tags.get("name", ""),
                    amenity,
                    n.tags.get("addr:street", ""),
                    n.tags.get("addr:housenumber", ""),
                    n.tags.get("addr:city", ""),
                    n.location.lat,
                    n.location.lon
                ])
            except:
                pass

    def close(self):
        self.file.close()


handler = BusinessExtractor("businesses.csv")
handler.apply_file("koeln-regbez-260507.osm.pbf")
handler.close()

