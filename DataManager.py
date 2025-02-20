import pandas as pd
import os
from cryptography.fernet import Fernet
import sys
from datetime import datetime
import pickle
import numpy as np
from threading import Lock
import json
from openpyxl import load_workbook

import gspread
from google.oauth2.service_account import Credentials
'''auth is connected to upload rex , get_date_1 is important for frame'''

class DataManager():
    def __init__(self,shift = None):
        self.lock = Lock()
        if getattr(sys, 'frozen', False):  # If running as .exe
            self.__base_path = os.path.dirname(sys.executable) 
        else:
            self.__base_path = os.path.dirname(os.path.abspath(__file__))

        self.__usagePath = os.path.join(self.__base_path,'resources','usage.xlsx')
        self.__RexUsagePath = os.path.join(self.__base_path,'resources','RexUsage.xlsx')
        self.__liveDataPath = os.path.join(self.__base_path,'resources','data.pkl')
        self.__authPath = os.path.join(self.__base_path,'resources','auth.pkl')

        # for shift data memory
        self.x = 0 # shift A
        self.y = 0 # shift B
        self.z = 0 # shift C
        self.Ptotal  = 0 # previous total of the same day so that restarting app doesn't clear value
        

    def getCalib(self):
        with open(self.__liveDataPath,'rb') as file:
                data = pickle.load(file)
                calib = data['calib']
                return calib

    def setCalib(self,val):
        with open(self.__liveDataPath,'rb') as file:
            data = pickle.load(file)
            data['calib']= val

        with open(self.__liveDataPath,'wb') as file:
            pickle.dump(data,file)
  
   # functions for auth.pkl date:d/m/y
    def get_date_1(self):  
        with open(self.__authPath,'rb') as f:
            data = pickle.load(f)
            date_1 = data['date_1']
            return date_1
        
    def acc_info(self):
        with open(self.__authPath,'rb') as f:
            data = pickle.load(f)
            cred = data['cred']
            return cred
        
    def get_id(self):
        with open(self.__authPath,'rb') as f:
            data = pickle.load(f)
            id = data['sheet_id']
            return id
        
    def get_frame(self):
        with open(self.__authPath,'rb') as f:
            data = pickle.load(f)
            frame = data['frame']
            return frame

    def get_scopes(self):
        with open(self.__authPath,'rb') as f:
            data = pickle.load(f)
            scopes = data['scopes']
            return scopes
        
   # functions for uploading data to cloud  
    def auth_access(self):
        creds = Credentials.from_service_account_info(self.acc_info(), scopes=self.get_scopes())
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(self.get_id())
        return spreadsheet
    
    def framer(self,val,date_first:str,date_dest:str) -> list:
        frame  = self.get_frame()
        diff = abs((datetime.strptime(date_dest,'%d/%m/%Y')-datetime.strptime(date_first,'%d/%m/%Y')).days)
        for idx in range(10): ## framegeneration from data received from worker thread
            frame[idx]['range'] = f"Sheet{idx+1}!A{2+diff}:G{2+diff}"
            frame[idx]['values'] = [ [ date_dest, float(val['Ctotal'][idx]),
                                int(val['shift'][idx][0]),int(val['shift'][idx][1]), 
                                int(val['shift'][idx][2]), int(val['demand'][idx]), int(val['setV'][idx])] ]
        return frame

    def upload_rex(self,sheet,val):
        today_date = datetime.now().strftime('%d/%m/%Y')
        try:
            body = {
            "valueInputOption": "RAW",  # Use "RAW" or "USER_ENTERED" depending on your needs
            "data": self.framer(val=val, date_first= self.get_date_1(), date_dest=today_date)
            }
            sheet.values_batch_update(body)
            return 1
        except Exception as e:
            print(f"Error : {e}")
            return 0

        

   # functions for data.pkl
    def getPass(self):
        with open(self.__liveDataPath,'rb') as file:
            data = pickle.load(file)
            pasw = str(data['password'])
            return pasw
        
    def pushPass(self,value):
        with open(self.__liveDataPath,'rb') as file:
            data = pickle.load(file)
            data['password']= str(value)

        with open(self.__liveDataPath,'wb') as file:
            pickle.dump(data,file)

    def getTotal(self):
        with open(self.__liveDataPath,'rb') as file:
            data = pickle.load(file)
            total = data['total']
            return total
        
    def pushTotal(self,value):
        with open(self.__liveDataPath,'rb') as file:
            data = pickle.load(file)
            arr = np.array(value)
            if not np.any(arr == 0):
                data['total']= value
        with open(self.__liveDataPath,'wb') as file:
            pickle.dump(data,file)

    def resetHour(self):
        with open(self.__liveDataPath,'rb') as file:
            data = pickle.load(file)
            hour_value = data['hour']
            hour_value = np.zeros((24,10),dtype=np.int32)
            data['hour'] = hour_value
        with open(self.__liveDataPath,'wb') as file:
            pickle.dump(data,file)


    def pushHour(self,h,val):
        with open(self.__liveDataPath,'rb') as file:
            data = pickle.load(file)
            hour_value = data['hour']
            hour_value[h] = val
            data['hour'] = hour_value
        with open(self.__liveDataPath,'wb') as file:
            pickle.dump(data,file)

    def getHour(self):
        with open(self.__liveDataPath,'rb') as file:
            data = pickle.load(file)
            hour = data['hour']
            return hour
        
    def getSlaveHours(self,id):
        with open(self.__liveDataPath,'rb') as file:
            data = pickle.load(file)
            hour = data['hour'][:,id-1]
            return hour

        
    def pushreset(self,val):
        with open(self.__liveDataPath,'rb') as file:
            data = pickle.load(file)
            data['reset']= val

        with open(self.__liveDataPath,'wb') as file:
            pickle.dump(data,file)

    def getReset(self):
        with open(self.__liveDataPath,'rb') as file:
            data = pickle.load(file)
            reset = data['reset']
            return reset

    def getLive(self):
        with open(self.__liveDataPath,'rb') as file:
            data = pickle.load(file)
            live = data['curV']
            return live
        
    def pushLive(self,val):
        with open(self.__liveDataPath,'rb') as file:
            data = pickle.load(file)
            data['curV']= val

        with open(self.__liveDataPath,'wb') as file:
            pickle.dump(data,file)

    def pushValue(self, MeterId, total, a, b, c, demand, sw: bool = 1):
        try:
            # Determine path
            path = self.__usagePath if sw else self.__RexUsagePath

            with self.lock:
                # Ensure file exists or create it
                if not os.path.exists(path):
                    print(f"File not found. Creating a new file at: {path}")
                    pd.DataFrame(columns=['Date', 'Total(L litre)', 'A(litre)', 'B(litre)', 'C(litre)', 'Demand(litre)']).to_excel(
                        path, sheet_name=f"Sheet{MeterId}", index=False
                    )

                # Read existing Excel file
                excel_data = pd.ExcelFile(path)
                sheet_name = f"Sheet{MeterId}"

                # Check for the sheet and load its data
                if sheet_name in excel_data.sheet_names:
                    dfu = pd.read_excel(path, sheet_name=sheet_name)
                else:
                    print(f"Sheet {sheet_name} does not exist. Creating it.")
                    dfu = pd.DataFrame(columns=['Date', 'Total(L litre)', 'A(litre)', 'B(litre)', 'C(litre)', 'Demand(litre)'])

                # Update or append data
                today_date = datetime.now().strftime('%d/%m/%Y')
                if today_date in dfu['Date'].values:
                    if not (a>1 or b>1 or c>1) and (self.x==0 and self.y==0 and self.z==0 ): # if any data is zero
                        self.x  = dfu.loc[dfu['Date'] == today_date,'A(litre)'].values[0]
                        self.y  = dfu.loc[dfu['Date'] == today_date,'B(litre)'].values[0]
                        self.z  = dfu.loc[dfu['Date'] == today_date,'C(litre)'].values[0]
                        self.Ptotal  = dfu.loc[dfu['Date'] == today_date,'Total(L litre)'].values[0]
                    # Update existing row
                    dfu.loc[dfu['Date'] == today_date, ['Total(L litre)', 'A(litre)', 'B(litre)', 'C(litre)', 'Demand(litre)']] = [
                        total + self.Ptotal,
                        a + self.x,
                        b + self.y,
                        c + self.z,
                        demand
                    ]
                else:
                    if not (a>1 or b>1 or c>1) and (self.x==0 and self.y==0 and self.z==0 ): # if any data is zero
                        self.x  = dfu.loc[dfu['Date'] == today_date,'A(litre)'].values[0]
                        self.y  = dfu.loc[dfu['Date'] == today_date,'B(litre)'].values[0]
                        self.z  = dfu.loc[dfu['Date'] == today_date,'C(litre)'].values[0]
                        self.Ptotal  = dfu.loc[dfu['Date'] == today_date,'Total(L litre)'].values[0]
                    # Append new row
                    new_row = {
                        'Date': today_date,
                        'Total(L litre)': total + self.Ptotal,
                        'A(litre)': a + self.x,
                        'B(litre)': b + self.y,
                        'C(litre)': c + self.z,
                        'Demand(litre)': demand
                    }
                    dfu = pd.concat([dfu, pd.DataFrame([new_row])], ignore_index=True)

                # Write back to Excel
                with pd.ExcelWriter(path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                    dfu.to_excel(writer, sheet_name=sheet_name, index=False)

        except FileNotFoundError:
            print("Error: Excel file not found. Check the file path.")
        except KeyError as e:
            print(f"Error: Missing column or sheet - {e}")
        except Exception as e:
            print(f"Error updating the Excel file: {e}")
   # functions for xl files  
    # def pushValue(self,MeterId,total,a,b,c,demand,sw : bool=1):  ##sw 0 for real value push
    #     try:
    #         if sw:
    #             path = self.__usagePath
    #         else:
    #             path = self.__RexUsagePath

    #         with self.lock:
    #             excel_data = pd.ExcelFile(path)

    #             sheet_name = f"Sheet{MeterId}"
    #             if sheet_name in excel_data.sheet_names:
    #                 dfu = pd.read_excel(path, sheet_name=sheet_name)
    #             else:
    #                 print("file does not exists")
                    
    #             today_date = datetime.now().strftime('%d/%m/%Y')
                
    #             if today_date in dfu['Date'].values:
    #                 if not (a>1 or b>1 or c>1) and (self.x==0 and self.y==0 and self.z==0 ): # if any data is zero
    #                     self.x  = dfu.loc[dfu['Date'] == today_date,'A(litre)'].values[0]
    #                     self.y  = dfu.loc[dfu['Date'] == today_date,'B(litre)'].values[0]
    #                     self.z  = dfu.loc[dfu['Date'] == today_date,'C(litre)'].values[0]
    #                     self.Ptotal  = dfu.loc[dfu['Date'] == today_date,'Total(L litre)'].values[0]

    #                 dfu.loc[dfu['Date'] == today_date, ['Total(L litre)', 'A(litre)', 'B(litre)', 'C(litre)', 'Demand(litre)']] = [total+self.Ptotal, a+self.x, b+self.y, c+self.z, demand]
    #             else:
    #                 if not (a>1 or b>1 or c>1) and (self.x==0 and self.y==0 and self.z==0 ):
    #                     self.x  = dfu.loc[dfu['Date'] == today_date,'A(litre)'].values[0]
    #                     self.y  = dfu.loc[dfu['Date'] == today_date,'B(litre)'].values[0]
    #                     self.z  = dfu.loc[dfu['Date'] == today_date,'C(litre)'].values[0]
    #                     self.Ptotal  = dfu.loc[dfu['Date'] == today_date,'Total(L litre)'].values[0]

    #                 new_row = pd.DataFrame({'Date': [today_date], 'Total(L litre)': [total+self.Ptotal], 'A(litre)': [a+self.x], 'B(litre)': [b+self.y], 'C(litre)': [c+self.z], 'Demand(litre)': [demand]})
    #                 dfu = pd.concat([dfu, new_row],ignore_index=True)
                    
                
    #             with pd.ExcelWriter(path, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
    #                 dfu.to_excel(writer, sheet_name=sheet_name, index=False)


    #     except Exception as e:
    #         print(f"Error updating the Excel file: {e}")

        
    