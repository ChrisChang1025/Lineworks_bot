import requests
import json
import os
from google.oauth2 import service_account
import gspread
import pandas as pd

dict1 = {"開放":"准备处理",
                 "需求設計": "需求设计",
                 "Monitor": "观察中",
                 "驗收失敗": "验收失败",
                 "PRD業主驗收": "PRD业主验收",
                 "開發中": "开发中",
                 "待測試": "待测试",
                 "STG測試":"STG测试",
                 "UAT待上版": "UAT待上版",
                 "UAT業主驗收": "UAT业主验收",
                 "PRD待上版": "PRD待上版",
                 "上版完成": "上版完成",
                 "暫停": "暂停",
                 "Closed": "已关单"
                 }

class get_jira:

    def __init__(self, url):
        self.init_page = 0
        self.domain = "https://domainname.atlassian.net/rest/api/2/search"
        self.header = {
            "Authorization": "Basic ==",
            "Cookie": "atlassian.xsrf.token=",
            "Content-Type": "application/json",
        }
        path, filename = os.path.split(__file__)
        credentials = service_account.Credentials.from_service_account_file(path+'/lineworks.json')
        scoped_credentials = credentials.with_scopes(['https://spreadsheets.google.com/feeds'])
        gc = gspread.authorize(scoped_credentials)
        self.__workbook = gc.open_by_url(url)


    def get_fromJira(self, vend):
        #get results form Jira and convert to list
        jira_data = []
        while True:
                body = {"jql":"project=TSD AND issuetype in (Bug, Request, 客製化需求) AND status in (Monitor, PRD待上版, "
                               "PRD業主驗收, STG測試, \"TO DO\", UAT待上版, UAT業主驗收, 待測試, 開發中, 需求設計, 驗收失敗) "
                               f"AND labels = {vend} ORDER BY created DESC, updated DESC, status DESC, due DESC","fields":
                [
                    "key",
                    "summary",
                    "status",
                    "Created",
                    "assignee",
                    "updated",
                    "customfield_10100",
                    "duedate",
                    "created"
                ],
                         "maxResults":100,
                         "startAt": self.init_page
                         }
                r = requests.post(self.domain, headers=self.header, data=json.dumps(body))
                r.encoding = 'utf8'
                responses = r.json()
                if responses['total'] >= self.init_page:
                    for response in responses['issues']:
                        key_dictionary = {"Key": response['key'],
                                          "Summary": response['fields']['summary'],
                                          "Status": response['fields']['status']['name'],
                                          "Created": response['fields']['created'],
                                          "Updated": response['fields']['updated'],
                                          "Due Date": response['fields']['duedate'],
                                          "Sprint": response['fields']['customfield_10100']
                        }
                        if response['fields']['customfield_10100']:
                            customSprint = []
                            for sprint in response['fields']['customfield_10100']:
                                customSprint.append(sprint['name'])
                            key_dictionary.update({"Sprint": "".join(customSprint)})
                        jira_data.append(key_dictionary)
                    self.init_page += responses['maxResults']

                else:
                    return jira_data

    def googlSheet(self, data):
        #update returned result to google sheet
        df = pd.DataFrame(data)
        df = df[['Key', 'Summary', 'Status', 'Created', 'Updated', 'Sprint', "Due Date"]]
        df['Status'] = df['Status'].replace(dict1)
        df['Created'] = pd.to_datetime(df["Created"]).dt.strftime('%Y/%m/%d')
        df['Updated'] = pd.to_datetime(df["Updated"]).dt.strftime('%Y/%m/%d')
        df.rename(columns={"Key":"工单号", "Summary": "需求内容", "Status": "状态", "Created": '工单创建日',
                            "Updated": '工单更新日', "Sprint": '工单执行内容及日期', "Due Date": "工单预计完成日"}, inplace=True)
        worksheet = self.__workbook.get_worksheet(0)
        worksheet.clear()
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        worksheet.freeze(rows=1)
        worksheet.format('A1:G1', {'textFormat': {'bold': True}})


if __name__ == '__main__':
    longWall_info = get_jira('https://docs.google.com/spreadsheets/d/1BipNXapvLbtUPWoHgxs0x7CDkrHxcQ4y013-w_YbBf0/edit#gid=0')
    longWall_info_response = longWall_info.get_fromJira('长城')
    longWall_info.googlSheet(longWall_info_response)
    guge_info = get_jira('https://docs.google.com/spreadsheets/d/1OO0LOdb9CJPLExz0In1FnZzG3uejn9Z1saBKjqmIGdk/edit#gid=0')
    guge_info_response = guge_info.get_fromJira('谷歌')
    guge_info.googlSheet(guge_info_response)


