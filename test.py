from arcgis.gis import GIS
import csv
import time
from collections import Counter
time_now = time.time()
gis = GIS("https://uplan.maps.arcgis.com", client_id='6mLS33NCUtLYkcyd')
content = gis.content.search(query="", sort_field="title", sort_order="asc", max_items = 100000)
content_types = []
with open('uplancontent.csv', 'w', newline='') as file:
    for item in content:
        #print(item['type'])
        content_types.append(item['type'])
#         created_time = item['created']/1000
#         age = round((time_now - created_time) / (60*60*24))
#         if age > 185:
#             url = "https://uplan.maps.arcgis.com/home/item.html?id="+item['id']
#             try:
#                 usage= item.usage(date_range='1Y')
#                 writer.writerow([item, '1Y',age, url])
#                 print('1Y')
#             except:
#                 try:
#                     usage= item.usage(date_range='6M')
#                     writer.writerow([item, '6M',age,url])
#                     print('6M')
#                 except:
#                     writer.writerow([item, 'Less than 6M',age,url])
#                     print('<6M')



uniques = Counter(content_types)
frequency = [(item,content_types.count(item)) for item in uniques]

print(uniques)
