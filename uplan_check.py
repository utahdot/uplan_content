#---- imports, constants ----#
from arcgis.gis import GIS
import time
import sys

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from os.path import basename

import getpass
from difflib import SequenceMatcher
from collections import defaultdict

time_now = time.time()
uplan_popularity_threshold = 0.025
uplan_age_threshold = 180
uplan_default_licenseInfo = ("""\
<p style="font-weight:bold;">This data is for informational purposes and \
must be field verified prior to being used on a project.</p><p>UDOT \
makes no warranty with respect to the accuracy, completeness or usefulness \
of this content or consequential damages resulting from the use or misuse \
of the content or any of the information contained herein. Please contact the \
UDOT GIS Department at <a href="mailto:udotgis@utah.gov">udotgis@utah.gov</a> \
for more information.</p>""")

email_service = {
    'from_address': 'agilvarry@utah.gov',
    'subject': 'UPlan Content - Action Required',
    'bodyTemplateFile': 'bodytemplate.txt',
    'bodyTemplate': None,
    'signatureFile': 'signature.txt',
    'signature': None,
    'signatureLogoFile': 'signature-logo.png',
    'uplanContentManagementFile': 'UPlanContentManagement.pdf',
    'smtp_server': 'smtp.gmail.com',
    'smtp_username': None,
    'smtp_password': None
  }

whitelist_users = ['cbraceras@utah.gov_uplan','tnewell@utah.gov_uplan', 'jasondavis@utah.gov_uplan', 'eweight@utah.gov_uplan',
                   'lhull@utah.gov_uplan', 'bbradshaw@utah.gov_uplan', 'nlee@utah.gov_uplan', 'bbmaughan@utah.gov_uplan',
                   'krispeterson@utah.gov_uplan', 'rwight@utah.gov_uplan', 'bryanadams@utah.gov_uplan', 'robertclayton@utah.gov_uplan',
                   'rtorgerson@utah.gov_uplan'] 
smtp = smtplib.SMTP(email_service['smtp_server'])

##----- Authorization and Checks -----##
uplan = GIS("https://uplan.maps.arcgis.com", client_id='6mLS33NCUtLYkcyd')
uplan_users = uplan.users.search(sort_field='username', sort_order='asc', max_users=100000, outside_org=True)
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

##-------- User Functions --------##
def compile_list_of_unused_enabled_users(uplan_users):
    threshold_age = 396
    filtered_users = []
    
    for user in uplan_users:
        if user.username not in whitelist_users:
            if not user.disabled:
                if user.lastLogin:
                # This user has logged in in the past.
                    time_accessed = user.lastLogin/1000
                    time_diff = time_now - time_accessed
                    if time_diff > threshold_age * (60*60*24):
                        filtered_users.append(user)
                else:
                    # This user has never logged in.
                    time_created = user.created/1000
                    time_diff = time_now - time_created
                    if time_diff > threshold_age * (60*60*24):
                        filtered_users.append(user)
    return filtered_users  
    
def compile_list_of_unused_disabled_users(uplan_users):
    threshold_age = 468
    filtered_users = []
    
    for user in uplan_users:
        if user.username not in whitelist_users:
            if user.disabled:
                if user.lastLogin:
                    # This user has logged in in the past.
                    time_accessed = user.lastLogin/1000
                    time_diff = time_now - time_accessed
                    if time_diff > threshold_age * (60*60*24):
                        filtered_users.append(user)
                else:
                    # This user has never logged in.
                    time_created = user.created/1000
                    time_diff = time_now - time_created
                    if time_diff > threshold_age * (60*60*24):
                        filtered_users.append(user)                
    return filtered_users

##-------- Email Function -------##
def get_email_login():
    email_service['smtp_username'] = input('SMTP username for gmail (incl. the @utah.gov part): ')
    if not email_service['smtp_username']:
        print('You have to provide an SMTP user')
        sys.exit()
    email_service['smtp_password'] = getpass.getpass('SMTP password for ' + email_service['smtp_username'] + ': ')
    if not email_service['smtp_password']:
        print('You have to provide an SMTP password')
        sys.exit()

def set_email_template():
    with open(email_service['bodyTemplateFile']) as f:
        email_service['bodyTemplate'] = f.read()     
    with open(email_service['signatureFile']) as fp:
        email_service['signature'] = fp.read()    

def connect_to_smtp_server():
    smtp.starttls()
    smtp.ehlo()
    smtp.esmtp_features['auth'] = 'LOGIN'
    smtp.login(email_service['smtp_username'], email_service['smtp_password'])

def create_content_list(content):
    content_list = ""
    for item in content:
        try:
            content = uplan.content.get(item)
            title = content['title']
            content_list += f'<br><a href="https://uplan.maps.arcgis.com/home/item.html?id={item}">{title}</a>' 
        except:
            print("issue with getting content info for email")
            print(item)

    return content_list       

def send_emails(deficient_content):
    for user in deficient_content:
        try:
            email_body = email_service['bodyTemplate']        
            content_list = create_content_list(deficient_content[user])
            email_body = email_body.replace('{contentList}', ''.join(content_list))
        
            msgRoot = MIMEMultipart('related')
            msgRoot['Subject'] = email_service['subject']
            msgRoot['From'] = email_service['from_address']
            msgRoot['To'] = user
            msgRoot.preamble = 'This is a multi-part message in MIME format.'

            msgAlternative = MIMEMultipart('alternative')
            msgRoot.attach(msgAlternative)
            msgText = MIMEText('Please refer to the HTML portion of this email for a message about your UPlan content')
            msgAlternative.attach(msgText)
            msgText = MIMEText(email_body + email_service['signature'], 'html')
            msgAlternative.attach(msgText)

            with open(email_service['uplanContentManagementFile'], 'rb') as fp:
                pdf = MIMEApplication(fp.read(), _subtype = 'pdf')
                pdf.add_header('content-disposition', 'attachment', filename=basename(email_service['uplanContentManagementFile']))
                msgRoot.attach(pdf)

            with open(email_service['signatureLogoFile'], 'rb') as fp:
                logo = MIMEImage(fp.read())
                logo.add_header('Content-ID', '<logo>')
                msgRoot.attach(logo)    

            smtp.sendmail(msgRoot['From'], msgRoot['To'], msgRoot.as_string())
        except:
            print("failed to send email to:")
            print(user)        

##-------- Content Functions --------##
def remove_unpopular(item, tags):
    newtags = []
    try:
        for tag in tags:
            if tag != 'unpopular':
                newtags.append(tag)
        item.update({'tags' : newtags}) 
    except:
        print("Issue removing unpopular tag")
        print(item)

def remove_deficient(item, tags):
    newtags = []
    try:
        for tag in tags:
            if tag != 'deficient_metadata':
                newtags.append(tag)
        item.update({'tags' : newtags}) 
    except:
        print("Issue removing deficient tag") 
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

def add_uplan_licenseInfo(item):
    try:
        item.update({'licenseInfo': uplan_default_licenseInfo})
    except:
        print("License info update failed")
        print(item)

def tile_pagckage(item, tags):
    tile_description = "This Tile Package has been created for offline use with Collector.  Do not delete this item.  For any questions please contact UDOT GIS (udotgis@utah.gov)."
    tile_snippet = "Tile Package for Collector"
    tile_thumbnail = 'https://maps.udot.utah.gov/uplan_data/documents/hub/TilePackage.png'
    newtags =[]
    for tag in tags:
        if tag != 'deficient_metadata':
            newtags.append(tag)
    try:
        item.update(item_properties={'description':tile_description, 'snippet': tile_snippet,'tags': newtags}, thumbnail=tile_thumbnail)     
    except:
        print("Tile Info Update failed")
        print(item)


def sqlite_data(item, tags):
    sql_description = "This SQLite Geodatabase has been created for offline use with Collector.  Do not delete this item.  For any questions please contact UDOT GIS (udotgis@utah.gov)."
    sql_snippet = "SQLite Geodatabase for Collector"
    sql_thumbnail = 'https://maps.udot.utah.gov/uplan_data/documents/hub/sqlite_geodatabase.png'
    newtags =[]
    for tag in tags:
        if tag != 'deficient_metadata':
            newtags.append(tag)
    try:
        item.update(item_properties={'description':sql_description, 'snippet': sql_snippet,'tags': newtags}, thumbnail=sql_thumbnail)     
    except:
        print("SQLite Geodatabase Info Update failed")
        print(item)            
    
    
def hub_data(item, tags):
    hub_description ="This item is part of a UDOT ArcGIS Hub site. If you have questions about this item or it's associated Hub Site please contact Alex Gilvarry at agilvarry@utah.gov"
    hub_snippet = "This item is part of a UDOT ArcGIS Hub site."
    hub_thumbnail = 'https://maps.udot.utah.gov/uplan_data/documents/hub/HubSites.png'
    newtags =[]
    for tag in tags:
        if tag != 'deficient_metadata':
            newtags.append(tag)
    if 'Hub Site' not in newtags:        
        newtags.append('Hub Site')
    try:
        item.update(item_properties={'description':hub_description, 'snippet': hub_snippet,'tags': newtags}, thumbnail=hub_thumbnail)     
    except:
        print("Hub Info Update failed")
        print(item)

def add_to_deficient_list(item):
    item_owner = item['owner'][:-6] # substring to remove '_uplan' from owner name
    item_id = item['id']        
    try:
        deficient_content[item_owner].append(item_id) 
    except: 
        print("adding item to list failed")   
        print(item)    

def add_deficient_metadata(item,tags):
    item_owner = item['owner'][:-6] # substring to remove '_uplan' from owner name
    item_id = item['id']
    try:
        deficient_content[item_owner].append(item_id) 
        tags.append('deficient_metadata')
        item.update({'tags' : tags}) 
    except: 
        print("adding deficient tags failed")   
        print(item) 

def delete_archive(item):
    try:
        item.delete()
    except:
        print("Item Delete Failed: ")
        print(item)

## ---------- Perform Item Checks ----------##
get_email_login()
set_email_template()
print("Getting uplan Items...")
uplan_items = uplan.content.search(query="", sort_field="title", sort_order="asc", max_items = 100000)
deficient_content = defaultdict(list)
print("testing....")

for item in uplan_items:
    #---- Check Usage ----#
    tags = item['tags']
    modified_time = item['modified']/1000
    timeSinceUpdate = round((time_now - modified_time) / (60*60*24))
    created_time = item['created']/1000
    age = round((time_now - created_time) / (60*60*24))
    if age == 0: #was created today, set to 1 to avoid division by 0
        age = 1
    numViews = item['numViews']
    popularity = numViews / age
    hub_types = ['Hub Initiative', 'Hub Page', 'Hub Site Application']
    owner = item['owner']
    item_type = item['type']
    hub_owners =['agilvarry@utah.gov_uplan', 'pdamron@utah.gov_uplan', 'mshah@utah.gov_uplan']
    # if 'archive' in tags and timeSinceUpdate > 420:
    #     delete_archive(item)   
    #     continue

    #if item_type in hub_types and owner not in hub_owners:
    #    try:
    #        item.reassign_to(target_owner='agilvarry@utah.gov_uplan', target_folder='Hub')
    #    except:
    #        print("couldn't reassign hub item")
    #        print(item)
        

    #TODO: Check orphan geodatabase, check whitelist content to email alex

    if 'whitelist' in tags or item['owner'] in whitelist_users or 'archive' in tags or item['type'] == 'File Geodatabase' or item['type'] == 'Code Attachment': 
        #the item is on whitelist or private or archived or is a supporting geodatabase, skip this item
        continue     
    
    

    # if popularity < uplan_popularity_threshold and age > uplan_age_threshold:
    #     #popularity is low and item older than age threshold
    #     if 'unpopular' in tags:
    #         #previously tagged unpopular - unshare and move to archive folder if previously tagged as unpopular 
    #         print("archive item")
    #        # archive_item(item, tags)
    #     else: #tag as upopular
    #         print("add unpopular")
    #         #add_unpopular(item, tags)
    #     continue       

    # elif 'unpopular' in tags: 
    #     #popularity is above threshold, but it was previously tagged as unpopular
    #     #print("remove unpopular")
    #     remove_unpopular(item, tags)
    #     continue    

    #---- Check Metadata ----#

    if item['access'] == 'private':
        #if item is private we don't care about metadata
        continue

    length_description = 0
    length_summary = 0
    description_summary_similarity = 0
    thumbnail = False
    length_tags = len(tags)
 
    if item['description']:
        length_description = len(item['description'])
    if item['snippet']:
        length_summary = len(item['snippet'])
    if item['description'] and item['snippet']:
        description_summary_similarity = round((SequenceMatcher(None, item['description'], item['snippet']).ratio())*100, 2)
    if item['thumbnail']: #TODO: if not, append default thumbnail
        thumbnail = True  
    if not item['licenseInfo']: #TODO: check if license info is exact
        #print("missing License Info")
        add_uplan_licenseInfo(item)

    if length_description < 10 or length_tags == 0 or length_summary < 10 or int(description_summary_similarity) == 100 or not thumbnail:
        if item_type in hub_types:
            add_uplan_licenseInfo(item)  
            hub_data(item, tags)
        elif item_type == 'SQLite Geodatabase':
            add_uplan_licenseInfo(item)  
            sqlite_data(item, tags)
        elif item_type == 'Tile Package':
            add_uplan_licenseInfo(item)    
            tile_pagckage(item, tags)
        elif 'deficient_metadata' in tags: 
            #item was already tagged as deficient, make item private
            #print("adding to list")
            #item.update(item_properties={'access':'private'}) 
            add_to_deficient_list(item)
        else:
            #first check, item is deficient, mark as such and add to email list
            #print("add deficient")
            add_deficient_metadata(item,tags) 
    elif 'deficient_metadata' in tags: 
        #item tagged as deficient but that has been fixed
        # print("remove deficient")
        remove_deficient(item, tags)

#----- User Checks -----#
disabled_users = compile_list_of_unused_disabled_users(uplan_users)
inactive_users = compile_list_of_unused_enabled_users(uplan_users)
for user in disabled_users:
    print("deleteing user", user)
    print(user)
    user.delete(reassign_to="agilvarry@utah.gov_uplan") #TODO: create folder for user with user name?



for user in inactive_users:
    print("deleteing user", user)
    print(user)
    user.disable()

def test(deficient_content):
    print("emails...")
    for user in deficient_content:
        length = len(deficient_content[user])
        print(user, ":", length)          

test(deficient_content)     
connect_to_smtp_server()
send_emails(deficient_content)  

print("done")
