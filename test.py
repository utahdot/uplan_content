from arcgis.gis import GIS
import time
import pandas as pd
time_now = time.time()
uplan = GIS("pro")
print("Successfully logged in as: " + uplan.properties.user.username)
whitelist_users = ['cbraceras@utah.gov_uplan','tnewell@utah.gov_uplan', 'jasondavis@utah.gov_uplan', 'eweight@utah.gov_uplan',
                   'lhull@utah.gov_uplan', 'bbradshaw@utah.gov_uplan', 'nlee@utah.gov_uplan', 'bbmaughan@utah.gov_uplan',
                   'krispeterson@utah.gov_uplan', 'rwight@utah.gov_uplan', 'bryanadams@utah.gov_uplan', 'robertclayton@utah.gov_uplan',
                   'rtorgerson@utah.gov_uplan','rwallis@utah.gov_uplan', 'rbaltazar@utah.gov_uplan','mbradshaw@utah.gov_uplan',
                   'smulahalilovic@utah.gov_uplan'] 

skip_types = ['Code Attachment', 'File Geodatabase', 'Service Definition']

uplan_items = uplan.content.search(query="", sort_field="title", sort_order="asc", max_items = 10000)
uplan_users = uplan.users.search(sort_field='username', sort_order='asc', max_users=1000, outside_org=True)
me = uplan.users.me

if me.role != 'org_admin':
    print("You don't have the org_admin role.")
    sys.exit()

alex = uplan.users.get("agilvarry@utah.gov_uplan")
for folder in alex.folders:
    if folder['title'] == 'Archive':
        archive_folder = folder
        
if not archive_folder:
    print("Alex doesn't have an archive folder.") 
    sys.exit() 

def remove_unpopular(item, tags):
    newtags = []
    try:
        for tag in tags:
            if tag != 'unpopular' and tag !='archive':
                newtags.append(tag)
        item.update({'tags' : newtags}) 
    except:
        print("Issue removing unpopular tag")
        print(item)

def add_unpopular(item, tags):
    try:
        tags.append('unpopular')
        item.update({'tags' : tags}) 
    except:
        print("Issue tagging unpopular")
        print(item)

def archive_item(item, tags):
    try:
        tags.append('archive')
        item.update(item_properties={'access':'private', 'tags' : tags}) 
        item.reassign_to(target_owner='agilvarry@utah.gov_uplan', target_folder='Archive')
        item.share(everyone=False, org=False, groups=None, allow_members_to_edit=False)
    except:
        print("Issue archiving")
        print(item)  
       
def getUsage(item):
    return item.usage(date_range='1Y', as_df='True')

for item in uplan_items:
    tags = item['tags']

    created_time = item['created']/1000
    age = round((time_now - created_time) / (60*60*24))
    if age == 0: #was created today, set to 1 to avoid division by 0
        age = 1
    
    if item['type'] in skip_types or age <365:
        continue

    use_data = getUsage(item)
    useage = 0
    for index, row in use_data.iterrows():
        useage += row['Usage']
        
    print(item)
    print('useage', useage)   
