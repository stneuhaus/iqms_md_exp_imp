import requests
import json
import pandas
import time
import os


http_proxy="http://BYMCA_VIP.de.bayer.cnb:8080"
proxylist = { http_proxy }
proxydict={"http" : http_proxy, "https" : http_proxy}

vaultbaseurl="https://bayer-iqms.veevavault.com"
vaulturl=vaultbaseurl+"/api/v24.2"

sessionID = input("Session ID : ")
#include Vault IDs
#payload="q=select id, domain_active__v, user_name__v,user_first_name__v,user_last_name__v,user_email__v, last_login__v, federated_id__v, user_timezone__v,user_locale__v,security_policy_id__v,user_language__v,created_date__v, created_by__v, modified_date__v, modified_by__v, vault_id__v from users order by id"

payload="q=select id, domain_active__v, user_name__v,user_first_name__v,user_last_name__v,user_email__v, last_login__v, federated_id__v, user_timezone__v,user_locale__v,security_policy_id__v,user_language__v,created_date__v, created_by__v, modified_date__v, modified_by__v from users where user_first_name__v ='Stefan' order by id"
headers = {
  'Authorization': sessionID,
  'Accept': 'application/json',
  'X-VaultAPI-DescribeQuery': 'true',
  'Content-Type': 'application/x-www-form-urlencoded'
}

response = requests.request("POST", vaulturl+"/query", headers=headers, data=payload, proxies=proxydict)

jrespx = json.loads(response.text)
dfall = pandas.json_normalize(jrespx, record_path=['data'] )

numrecs = jrespx["responseDetails"]["total"]

print ("Number of Users: "+str(numrecs))

pageoffset = 1000

print ("Retrieving Domain Users...")
while pageoffset < numrecs:
  payloadnext = payload+" pageoffset "+str(pageoffset)
  print ("\r%d" % pageoffset,)
  response= requests.post(vaulturl+"/query", headers=headers, proxies=proxydict, data=payloadnext)
  jrespx = json.loads(response.text)
  df = pandas.json_normalize(jrespx, record_path=['data'] )
  dfall=pandas.concat([dfall,df])
  pageoffset = pageoffset+1000
  
#print ("Writing data to CSV")
#dfall.to_csv('domain_users_prod.csv', index=False)
print ("Writing data to CSV")
timestr = time.strftime("%Y%m%d-%H%M%S")
# Get the project root directory (go up from current script location)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
filename = os.path.join(project_root, "exports", "domain_users", f"02_domain_users_prod.{timestr}.csv")
print (filename)

# Create directory if it doesn't exist
os.makedirs(os.path.dirname(filename), exist_ok=True)

#dfall.to_csv('domain_users_prod.csv', index=False)
dfall.to_csv(filename, index=False)
