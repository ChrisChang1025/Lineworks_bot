import requests
from Logger import create_logger
log  = create_logger()

sport_microservice = {
    
}
tiger_microservice = {
      
}

env_url = {

}

env_entrance_url = {

}

def get_service_version(env):
    version_list = get_sport_version(env)
    msg = "【Sport Version】"+"\n"
    for service, version in version_list.items():
        msg += service + " : "+version+"\n"

    version_list = get_tiger_version(env)
    msg += "\n【Tiger Version】"+"\n"
    for service, version in version_list.items():
        msg += service + " : "+version+"\n"

    msg += "\n【Entrance Version】"+"\n"
    msg += get_entrance_version(env)
    return msg

def get_tiger_version(env):    
    version_list = {}
    for service in tiger_microservice:
        try :
            url= "http://" + env_url[env] + tiger_microservice[service]

            r = requests.request("GET", url)
            response = r.json()
            if response['git.tags'] == "":
                version_list[service] = response['git.build.version']
            else:
                version_list[service] = response['git.tags']
        except Exception as e:
            version_list[service] = 'get_version error: %s'%e

    return version_list

def get_sport_version(env):    
    version_list = {}   
    
    for service in sport_microservice:
        try:
            url= "http://" + env_url[env] + sport_microservice[service]

            r = requests.request("GET", url)
            response = r.json()
            if response['git.tags'] == "":
                version_list[service] = response['git.build.version']
            else:
                version_list[service] = response['git.tags']
        except Exception as e:
            version_list[service] = 'get_version error: %s'%e

    return version_list

def get_entrance_version(env):
    ver = ""
    url= "http://" + env_entrance_url[env] + "/lastUpdateTime"
    r = requests.request("GET", url)
    try:
        response = r.json()
        ver = response['data']['version']
    except:
        ver = ''
    
    return ver

# result = get_tiger_version()
# result = get_sport_version()
