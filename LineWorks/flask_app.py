from calendar import month
from distutils import extension
from this import s
from time import time
from urllib import response
from flask import Flask, jsonify, request
import datetime
import json
from pathlib import Path
import requests
import re
from flask import Response
import google_sheet,jira
from extentions import scheduler,Config
import Jira_get
import jwt
import base64
from flask_cors import CORS
import general_function

from lxml import etree
import pytz
import string, random
from io import BytesIO
from LineWorks_token import get_token
import configparser
from Logger import create_logger
log  = create_logger()

app = Flask(__name__)
CORS(app)
def getSettleFailure():

    return ""
def callapi(type, accountId, roomId, message, picture  ):
    '''
    1.0: https://apis.worksmobile.com/r/{API_ID}/message/v1/bot/{botNo}/message/push
    2.0: https://www.worksapis.com/v1.0/bots/{botId}/channels/{channelId}/messages (群組)    ,  /bots/{botId}/users/{userId}/messages (個人)


    channelId = 1.0 roomId
    botId = 1.0 botNo
    '''
    retry_count = 0 # retry token 過期 重產的 變數
    while True:
        bot_Id = 17385 # fake
        try:

            payload = {}
            content = {}   
            if roomId != None and roomId != '' :
                payload["roomId"] = roomId
            elif accountId != None and accountId != "":
                payload["accountId"] = accountId

            content["type"] = type
            if type == "text":
                content["text"] = message
            elif type == "image" :
                content["previewUrl"] = picture
                content["resourceUrl"] = picture


            payload["content"] = content
            #log.info('callapi payload: %s '%payload)

            log.info('linework 2.0 ')
            if roomId != None and roomId != '' :
                #payload["roomId"] = roomId
                url = f'https://www.worksapis.com/v1.0/bots/{bot_Id}/channels/{roomId}/messages' #2.0 群組
                log.info('roomId 不為空 使用 群組 發送 , url: %s'%url )
            elif accountId != None and accountId != "":
                #payload["accountId"] = accountId
                url = f'https://www.worksapis.com/v1.0/bots/{bot_Id}/users/{accountId}/messages' # 2.0個人
                log.info('roomId 為空 使用 user 發送, url: %s'%url )
            
            #2.0 帶access_token


            config = configparser.ConfigParser(comment_prefixes='/', allow_no_value=True)
            config.read('config.ini', encoding="utf-8")
            token_refresh = config['line_work']['token_refresh']

            try:

                if token_refresh == 'true': # 初始
                    access_token = get_token(token_type = 'new' ) # 新的access_token
                    config.set("line_work","access_token",  access_token )
                    config.set("line_work","token_refresh",  'false' )
                    file = open("config.ini", 'w')
                    config.write(file) 
                    file.close()
                    log.info('初始 access_token 已更新')


                else: # 其他時段
                    access_token = config['line_work']['access_token']
                    log.info(' 延用access_token')

            except Exception as e:
                log.error('callapi error: %s '%e)
                return False
            headers = {
                'Authorization': 'Bearer %s'%access_token
                ,'Content-Type':'application/json'}

            r = requests.post(url, data=json.dumps(payload), headers=headers)
            status_code = r.status_code
            log.info( 'status_code: %s , text: %s '%(status_code , r.text)  )
            
            if str(status_code) == '401':
                
                log.info('token 過期,重新產新的 access token')
                config.set("line_work","token_refresh",  'true' )
                file = open("config.ini", 'w')
                config.write(file) 
                file.close()

                retry_count += 1
                if retry_count >=3:
                    return r.status_code, r.text;         
            
            else:
                return r.status_code, r.text;

        except Exception as e:
            log.error('callapi error: %s'%e)
            return False

def callAppDownload(accountId, roomId, msg):
    url = 'http://testdomain:5400/runAndroidDownloadApp'
    headers = {'Content-Type':'application/json'}
    payload={}
    try:
        payload = {
            "all_msg": msg,
            "roomID": "",
            "accountID": ""
        }
        
        if roomId != "" :
            payload["roomID"]= roomId
        elif accountId !="":
            payload["accountID"] = accountId
        
        # r = requests.get(url, data=json.dumps(payload), headers=headers)
        r = requests.post(url, data=json.dumps(payload), headers=headers)
        return r.status_code, r.text;
    except TimeoutError:
        return 200, "TimeoutError"
    except ConnectionError:
        return 200, "ConnectionError-AppDownload未回應"
    except Exception as e:
        return 200, str(e)

@app.route('/lineworks', methods=['post'])
def entry():
    sheet_msg=""
    sheet_accountId=""
    sheet_roomId=""
    response_msg=""

    data = request.data
    j_data =  json.loads(data)
    search_jira = 0
    log.info('lineworks req data: %s'%j_data )
    
    try:
        if j_data["content"]["text"] != None :
            sheet_msg = j_data["content"]["text"]        
            if 'userId' in j_data["source"] : # 2.0
                sheet_accountId  = j_data["source"]["userId"]        
            if "channelId" in j_data["source"]:     
                sheet_roomId = j_data["source"]["channelId"] 
            if "fromJira" in j_data["source"]:
                search_jira = j_data["source"]["fromJira"]
    except Exception as e:
        log.error('lineworks error: %s '%e)
        return False
           
    

    gs = google_sheet.gsheet_controller()
    gs.save_msg(sheet_roomId,sheet_msg,sheet_accountId,json.dumps(j_data))
    # search jira by issue num, won't search in chatroom
    if sheet_roomId == "" or search_jira==1:
        ja = jira.jira_controller()
        m = re.findall(ja.pattern,sheet_msg)
        for mr in m :
            summary,assignee,status = ja.get_issue(mr)
            response_msg += f"{mr} : {summary}\nassignee : {assignee}\nstatus : {status}\nhttps://domainname.atlassian.net/browse/{mr}\n" 

    
    if ('VD0' in sheet_msg.upper() and ('测试' in sheet_msg or '測試' in sheet_msg)) and 'http' in sheet_msg:
        returncode, returnmessage = callAppDownload(sheet_accountId, sheet_roomId, sheet_msg)
        if returnmessage !="測試結束":
            response_msg = returnmessage
    elif '查詢UAT版號' in sheet_msg:
        response_msg = general_function.get_service_version("UAT")     
    elif '查詢STG版號' in sheet_msg:
        response_msg = general_function.get_service_version("STG")
    elif '查詢PP1版號' in sheet_msg:
        response_msg = general_function.get_service_version("PP1")
    elif '查詢PP2版號' in sheet_msg:
        response_msg = general_function.get_service_version("PP2")
    elif '查詢QA1版號' in sheet_msg:
        response_msg = general_function.get_service_version("QA1")     
    elif '查詢QA2版號' in sheet_msg:
        response_msg = general_function.get_service_version("QA2")
    elif '查詢QA3版號' in sheet_msg:
        response_msg = general_function.get_service_version("QA3")
    elif sheet_msg.find("統編")>=0 or sheet_msg.find("統一編號")>=0 or sheet_msg.find("公司資訊")>=0 :
        response_msg="你要的是公司資訊嗎? \n公司地址: --------- \n"+"統編: -------- \n"
    elif sheet_msg.find("奴才你在嗎")>=0 or sheet_msg.find("奴才在嗎")>=0 or sheet_msg.find("奴才呢")>=0 :
        response_msg="我在這，你找我嗎?"
    try:
        if response_msg != "" :
            log.info( '/lineworks: sheet_accountId: %s , sheet_roomId: %s , response_msg: %s '%(  sheet_accountId, sheet_roomId , response_msg  )     )
            returncode, returnmessage = callapi("text",sheet_accountId, sheet_roomId, response_msg, ""  )   

        else :
            returncode, returnmessage = 200,""
    except Exception as e:
        log.error('lineworks entry error: %s'%e)
    return Response(returnmessage, status=returncode, mimetype='application/json');


@app.route('/sendmsg', methods=['POST'])
def sendmsg():

    try :
        pic = ""
        msg = ""
        roomID=""
        accountID=""
        msgType = "text"
        if request.json is not None:
            if 'accountID' in request.json : 
                accountID = request.json['accountID']
            if 'roomID' in request.json:
                roomID = request.json['roomID']
            msgType = request.json['content']['type']

            if msgType == "text":
                msg = request.json['content']['message']
            elif msgType == "image":
                pic = request.json['content']['pic']
        else: 
            msg = request.values.get('message')
            roomID = request.values.get('roomID')
            accountID = request.values.get('accountID')
            msgType = "text"           
        
        log.info(f'/sendmsg:  msgType: {msgType} ,accountID: {accountID} ,  roomID:{roomID}  ,  msg: {msg}  ')
        returncode, returnmessage = callapi(msgType, accountID, roomID, msg, pic) # 預設沒帶 是 version 2
    except Exception as e :
        log.error('sendmsg error: %s'%e )
        returncode = 200
        returnmessage = "exception"
    return Response(returnmessage, status=returncode, mimetype='application/json')


    

@app.route('/', methods=['GET'])
def entry_Get():   

    now = datetime.datetime.now()
    current_time = now.strftime("%Y/%m/%d %H:%M:%S")
    return 'hello' + current_time




#新增定時任務
@app.route('/addjob', methods=['post'])
def add_cron():
    
    jobargs = request.get_json()
    trigger_type = jobargs['triggerType']
    type = jobargs['type']
    accountId = jobargs['accountId']
    roomId = jobargs['roomId']
    message = jobargs['message']
    picture = jobargs['picture']
    args = (type, accountId, roomId, message, picture)
    try:
        if trigger_type == "date":
                scheduler.add_job(
                                    func=callapi,
                                    args=args,
                                    trigger=trigger_type,
                                    run_date=jobargs['runTime'],
                                    replace_existing=True,
                                    coalesce=True,
                                    id=jobargs['taskId'],
                                    timezone='Asia/Taipei'
                                )
                print("添加一次性任務成功")
                
        elif trigger_type == "interval":
                scheduler.add_job(
                                    func=callapi,
                                    args=args,
                                    trigger=trigger_type,
                                    seconds=int(jobargs['intervalSeconds']),
                                    minutes=int(jobargs['intervalMinutes']),
                                    hours=int(jobargs['intervalHours']),
                                    start_date=jobargs['startTime'],
                                    end_date=jobargs['endTime'],
                                    replace_existing=True,
                                    coalesce=True,
                                    id=jobargs['taskId'],
                                    timezone='Asia/Taipei'
                                     
                                )
                print("添加間隔任務成功")

        elif trigger_type == "cron":
                scheduler.add_job(
                                    func=callapi,
                                    args=args,
                                    trigger=trigger_type,
                                    day_of_week=jobargs["dayOfWeek"],
                                    hour=jobargs["hour"],
                                    minute=jobargs["minute"],
                                    second=jobargs["second"],
                                    replace_existing=True,
                                    id=jobargs['taskId'],
                                    timezone='Asia/Shanghai'
                                )
                print("添加週期任務成功")
    except:
        return jsonify(msg="新增任務失敗，請確認參數是否輸入正確")

    return jsonify(msg="新增任務成功")


   
#重啟任務
@app.route('/<task_id>/resume',methods=['GET'])

def resume_job(task_id):
    response = {'status': False}
    try:
        scheduler.resume_job(task_id)
        response["status"] = True
        response['msg'] = "job[%s] resume success" % task_id
    except Exception as e:
        response['msg'] = str(e)
    return jsonify(response)        
#刪除任務
@app.route('/<task_id>/remove',methods=['GET'])
def remove_job(task_id):
    response = {'status': False}
    try:
        scheduler.remove_job(task_id)
        response["status"] = True
        response['msg'] = "job[%s] remove success" % task_id
    except Exception as e:
        response['msg'] = str(e)
    return jsonify(response)

@app.route('/update_jira', methods=['GET'])
def update_jira():
    if request.method == 'GET':
        try:
            update = Jira_get.get_jira('https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid=0')
            longWall_info_response = update.get_fromJira('client1')
            update.googlSheet(longWall_info_response)
            update = Jira_get.get_jira('https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid=0')
            guge_info_response = update.get_fromJira('client2')
            update.googlSheet(guge_info_response)
            return "upated completed"
        except Exception as e:
            return "Trigger update TSD JIRA FAiled"
    else:
        return "Method Failed"

@app.route('/encodeJWT', methods=['GET'])
def encodeJWT():
    encode_content = {}
    if request.get_json() is not None:
        encode_content = request.get_json()
    secretKey = ''    
    encoded_jwt = jwt.encode(encode_content, base64.b64decode(secretKey), algorithm="HS256", headers={'typ': None})    
    
    return encoded_jwt

def generate_row_data():
    tz = pytz.timezone('America/New_York')
    random_digits = "".join(random.choice(string.digits) for i in range(20))
    # current_date = datetime.now().astimezone(tz).strftime("%Y%m%d%H%M%S")+random_digits
    data_dict = {}
    data_dict['billno'] = datetime.datetime.now().astimezone(tz).strftime("%Y%m%d%H%M%S")+random_digits
    data_dict['playName'] = '1_ST3_realcashQA5'
    data_dict['gameCode']= "GM057"+datetime.datetime.now().astimezone(tz).strftime("%y%m%d%H%M%S")+"MN"
    data_dict['netAmount']= "19"     
    data_dict['betTime']= datetime.datetime.now().astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")
    data_dict['betAmount']= "20" 
    data_dict['validBetAmount']= "19" 
    data_dict['flag']= "1" 
    data_dict['playType']= "1" 
    data_dict['currency']= "CNY" 
    data_dict['tableCode']= "M057" 
    data_dict['recalcuTime']= (datetime.datetime.now()+datetime.timedelta(minutes=2)).astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")
    data_dict['beforeCredit']= "119" 
    data_dict['betIP']= "133.167.103.134" 
    data_dict['platformType']= "AGIN" 
    data_dict['remark']= "" 
    data_dict['round']= "EMA" 
    data_dict['result']= "" 
    data_dict['gameType']= "BAC" 
    data_dict['deviceType']= "1" 
    data_dict['cardindex']= "100" 
    data_dict['odds']= "0" 

   
    
    return data_dict


@app.route('/env-url', methods=['GET'])
def get_env_url():
    with open("LineWorks/env.json") as json_file:
        data = json.load(json_file)

        env = None
        vend = None
        pw = request.args.get('password')
        
        if pw != "key":
            return Response("None", status=200, mimetype='application/json')
        else:
            if len(request.args) > 1:
                env = request.args.get('env')
                vend = request.args.get('vend')
            else:
                return data
            
            if env in data.keys():
                if vend == None:
                    return data[env]
                elif vend in data[env].keys():
                    return data[env][vend]
                else:
                    return Response("Please provide correct Environment and Vender Information", status=200, mimetype='application/json')
            else:
                return Response("Please provide correct Environment and Vender Information", status=200, mimetype='application/json')                       


@app.route('/getorders.xml', methods=['GET'])
@app.route('/getroundsres.xml', methods=['GET'])
def get_AG_orders():
    # getorders.xml
    request_data = request.json
    callapi("text", "test@myworks", "", "get_AG_orders\n" + request.full_path, "")
    root = etree.Element('result')  
    
    child = etree.Element('addition')
    child_child = etree.Element('total')
    child_child.text = '1'
    child.append(child_child)
    root.append(child)
    # === num_per_page
    child_child = etree.Element('num_per_page')
    child_child.text = '500'
    child.append(child_child)
    root.append(child)
    # === currentpage
    child_child = etree.Element('currentpage')
    child_child.text = '1'
    child.append(child_child)
    root.append(child)
    # === currentpage
    child_child = etree.Element('totalpage')
    child_child.text = '1'
    child.append(child_child)
    root.append(child)
    # === currentpage
    child_child = etree.Element('perpage')
    child_child.text = '1'
    child.append(child_child)
    root.append(child)
    # === info ===
    child = etree.Element('info')
    child.text = '0'
    root.append(child)

    # === row ===
    child = etree.Element('row')
    data_dict = generate_row_data()
    
    for index, key in enumerate(data_dict):
        child.set(key, data_dict[key])
    
    root.append(child)

    et = etree.ElementTree(root)

    f = BytesIO()
    et.write(f, encoding='utf-8', xml_declaration=True) 
    # s = etree.tostring(root, pretty_print=True)
    s = f.getvalue()
    # print(f.getvalue()) 
    print(s)
    return s


if __name__ == '__main__':
    app.config.from_object(Config())
    scheduler.init_app(app)
    scheduler.start()
    app.run(host='0.0.0.0', port=9000)