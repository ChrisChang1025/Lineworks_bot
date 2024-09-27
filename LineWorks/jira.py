import requests



class jira_controller:
    _instance = None 
    def __new__(cls, *args, **kwargs): 
        if cls._instance is None: 
            cls._instance = super().__new__(cls) 
        return cls._instance

    def __init__(self) -> None:
        self.jiraurl = 'https://innotech.atlassian.net/rest/api/2/'
        self.headers = {'Authorization':'Basic Y2hyaXNjQGlubm90ZWNoLm1lOjdaYUZCcDBqYUxFV3c3WDMydVNwMEYwNQ==',
        'Content-Type':'application/json'}
        self.pattern = r'(IN-[0-9]+)' 
        
    def get_issue(self,issue_num):
        issue_content = requests.request("GET", f'{self.jiraurl}issue/{issue_num}', headers=self.headers).json()
        try:
            return issue_content['fields']['summary'],issue_content['fields']['assignee']['displayName'],issue_content['fields']['status']['name']
        except KeyError:
            return f"can not find this issue","None","None"


if __name__ == "__main__":
    my_jira = jira_controller()
    summary,assignee,status = my_jira.get_issue('QIP-15781')
    print(f'QIP-15781 : {summary}\nassignee : {assignee}\nstatus : {status}')
    
