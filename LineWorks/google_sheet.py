import gspread
from google.oauth2 import service_account
import os
from datetime import datetime as dt
import pytz

tz = pytz.timezone('Asia/Taipei')
class gsheet_controller:
    _instance = None 
    def __new__(cls, *args, **kwargs): 
        if cls._instance is None: 
            cls._instance = super().__new__(cls) 
        return cls._instance

    def __init__(self) -> None:
        # sync google doc api services and get google sheet object as __workbook
        path, filename = os.path.split(__file__)
        credentials = service_account.Credentials.from_service_account_file(path+'/lineworks.json')
        scoped_credentials = credentials.with_scopes(['https://spreadsheets.google.com/feeds'])
        gc = gspread.authorize(scoped_credentials)
        self.__workbook = gc.open_by_url('https://docs.google.com/spreadsheets/d/13KOZcbLdiP8dHPFR3RDcDVvYAyF8uFs5hTOxwZsHgk0')
        
    def save_msg(self,sheet_roomId,sheet_msg,sheet_accountId,j_data) -> None:
        # Save chat message to google sheet 
        
        current_time = dt.now().astimezone(tz).strftime("%Y/%m/%d %H:%M:%S")

        try:
            worksheet = self.__workbook.worksheet(sheet_roomId)
        except:
            worksheet = self.__workbook.sheet1
        worksheet.insert_row([current_time, ""], 2)
        worksheet.update_cell(2,4, sheet_msg)
        worksheet.update_cell(2,2, sheet_roomId)
        worksheet.update_cell(2,3, sheet_accountId)
        worksheet.update_cell(2,5, j_data)
