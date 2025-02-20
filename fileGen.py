import pandas as pd
import numpy as np
import pickle as pkl
import time
from datetime import datetime,timedelta
import os
import sys

class GenFile():
    folder = 'resources'
    if getattr(sys, 'frozen', False):  # If running as .exe
        __base_path = os.path.dirname(sys.executable)  # Directory where the .exe is located
    else:  # If running as a script
        __base_path = os.path.dirname(os.path.abspath(__file__))
    
    def __init__(self):
        if not os.path.exists(os.path.join(self.__base_path,self.folder)):
            os.mkdir(os.path.join(self.__base_path,self.folder))
            
        self.__usagePath = os.path.join(self.__base_path,self.folder,'usage.xlsx')
        self.__RexUsagePath = os.path.join(self.__base_path,self.folder,'RexUsage.xlsx')
        self.__liveDataPath = os.path.join(self.__base_path,self.folder,'data.pkl')
        self.__authPath = os.path.join(self.__base_path,self.folder,'auth.pkl')
        print(self.__usagePath)
        print(self.__RexUsagePath)
        print(self.__liveDataPath)
        print(self.__authPath)
        print('generating files')
        self.genxl(self.__usagePath)
        self.genxl(self.__RexUsagePath)
        self.genpklLive(self.__liveDataPath)
        self.genpklAuth(self.__authPath)
        print('Done')
        

    def genxl(self,path:str):                    
        # headers
        headers = ['Date', 'Total(L litre)', 'A(litre)', 'B(litre)', 'C(litre)', 'Demand(litre)']

        # empty DataFrame with the specified headers
        df = pd.DataFrame(columns=headers)
        dates = []
        for i in range(-1,365):
            dates.append((datetime.now()+timedelta(days=i+1)).strftime('%d/%m/%Y'))

        df['Date'] = dates
        df['Total(L litre)'] = 0
        df['A(litre)'] = 0
        df['B(litre)'] = 0
        df['C(litre)'] = 0
        df['Demand(litre)'] = 0 

        # Specify the filename for the Excel file
        filename = path

        # Create the ExcelWriter object **outside** the loop
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:  # Or use 'xlsxwriter'
            # Write to multiple sheets in the same file
            for i in range(10):
                #df['Date'] = pd.to_datetime(df['Date'])
                sheet_name = f"Sheet{i+1}"  # Naming sheets as Sheet1, Sheet2, ..., Sheet11
                df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    def genpklLive(self,path:str):
        hour  = np.zeros((24,10),dtype=np.int32)
        total = np.array([.1,.1,.1,.1,.1,.1,.1,.1,.1,.1,.1],dtype=np.float32)
        pas = '123'
        reset : bool = 0
        curV = np.zeros(10,dtype=np.int32)
        calib = np.ones(10,dtype=int)
        data = {
            'hour':hour,
            'total': total,
            'password' : pas,
            'reset' : reset,
            'curV' : curV,
            'calib': calib
        }

        with open(path,'wb') as file:
            pkl.dump(data,file)
    
    def genpklAuth(self,path:str):
        sheet_id = '1dAYNnTXsP_TEtDAhl8LKQWk2NsUWigqueIY03IGGnqk'
        frame = [{'range': 'Sheet1!A2:F2', 'values': [['20/12/2024', 0, 0, 0, 0, 0]]},
                    {'range': 'Sheet2!A2:F2', 'values': [['20/12/2024', 0, 0, 0, 0, 0]]},
                    {'range': 'Sheet3!A2:F2', 'values': [['20/12/2024', 0, 0, 0, 0, 0]]},
                    {'range': 'Sheet4!A2:F2', 'values': [['20/12/2024', 0, 0, 0, 0, 0]]},
                    {'range': 'Sheet5!A2:F2', 'values': [['20/12/2024', 0, 0, 0, 0, 0]]},
                    {'range': 'Sheet6!A2:F2', 'values': [['20/12/2024', 0, 0, 0, 0, 0]]},
                    {'range': 'Sheet7!A2:F2', 'values': [['20/12/2024', 0, 0, 0, 0, 0]]},
                    {'range': 'Sheet8!A2:F2', 'values': [['20/12/2024', 0, 0, 0, 0, 0]]},
                    {'range': 'Sheet9!A2:F2', 'values': [['20/12/2024', 0, 0, 0, 0, 0]]},
                    {'range': 'Sheet10!A2:F2', 'values': [['20/12/2024', 0, 0, 0, 0, 0]]}]
        date_1 = datetime.now().strftime('%d/%m/%Y')
        cred = {
                "type": "service_account",
                "project_id": "weighty-yew-445210-c8",
                "private_key_id": "5dd338b16434324f2aba68a25619a78616065210",
                "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDZQBgLdk8fbEIl\nqkKFK8hoHP+T4bVASVvmS1QfA/xgKr/NR4FWbmdThNFpmCPxcPWW4mX7NEwCLyY4\nsvIUpYmH8PNIBl9Jgk+Y9xlgD5VEAzWTZWVccdSFiTR6OuM7/hhY0/UpEgr4GG4V\nWQFK6eLua1dT+VQ8avUJmcCLoLXOD7vxqdKjZMOjlQLHfGhasQeVpGZJKj9W96x3\nnSShoiMg3cA5UVKMSK+cC3gWpQRmifbbQHgHDJOP/3rcmOU7xau5D38yO1pKGaKO\n1K9aat9hK9uQC7gUahqPRzqYO9+fK/Ol+N+lAYozfCpj9Ga9izw5W1kN/NLeldey\nv7/NOx6xAgMBAAECggEAFpgYwBVsdm5IBVqLG0ZBzBkq9/ZvBynx+7YdIDImDNrZ\nUohDomluR9R+AoNDBrTap9fxJwJp/saoTRiIPn82Wdvkc1rNTWv26wfU3OWV/qou\nR99xXp9MjNxHh8hI0ngTUGav3jb9Cs8goMn+TUwckLL7dLVvLi7p/9b8nFDpI45U\nhcxfPtEBPnyikb+PsLMb9VDVuza27vcfmYQPRZRHNr5+sjJzC2CZIb46UIFIL4MN\nKHMHDZgTnBTQt00oq17K+NFVCUIl2yHZhl4X0Ajh2eD/+TyD1twFuQDPa5TcYUcu\n+IA2fe6HXk6W3b2V5qYzgG6R47vD+RP+IA9THqWEmQKBgQD0fPBSp1aO76FI1e54\n3Iw+fXIr6T2YsirJjzcQBkr7m3c2cRr6KrZkB6hlyzfXtsj2HURcy6PZSfD7iIHV\n/a8NiKVC1g1N4vNsbrJ0FXVua0yt0aWeUISSyP1MPpVTaN/Jk/wxIqeztqQ2i7LX\nvE5WqS4vcxiNeYKiLQqjdqQDaQKBgQDjetT7fKA8BJeFSiqKqNUvxBD3qakCqE9c\nSPs8m2UYwAJAkleMTKVB9zhqeuENWdn2z/WZYBcgfrVX/qbihummtMzkFmM81HVF\nz/8RtbbNG3Seb7xgWnfK+gooejagfStvoyusZU6vfj1SzlGZvO14xawf5g0yxqQ5\nDjukQd8ACQKBgA9Hv71qt/42+92RgVYMcrd1H62e5jqk6Aew68AUpJsVHF5Ks2Tv\nRnb6A4xZJyRUSDsZmSwzjgoGlQkjfvng4Q/3elyzBCHaDVy5jm2y6aP9EM3MTI2Y\nerCx3yLkxnBwHYx7s0de4xxYTesa0BKrsjm4WSqeBurQrVl1dzTANYABAoGBAJcM\nT/Ix3cAcmHQkPD1YQD74ZP/ew2AFXLT9rP2gfa/Ch3xS8Bk0J6O2wdpKf7e6yvWN\nPxq56IFmQYoNiMjwJqPQeCCYEQsqVDioFUmwLJLjQTuXHDGqwNKh1y7rf+xvUPFP\nGsfdeTMkkxmx8BMylUjVkSaZPnhR2GgeYFIAf0/pAoGBALxgq2thKv5jbvnLdY4L\n2zlsWaV/NUCC/Zj0OLYeOdYTfSA/e0uELC+1UMWuNdbvDM7b66Akp4GJkW92hP2J\nNarTbmbsnrIeYFHVaSlawS0Hk2HILI7riQQOUsu2t/YNcZY2K/9xh0zhVZm1855t\nOZZAeCapd1ppPTjZgBjWhb5g\n-----END PRIVATE KEY-----\n",
                "client_email": "sheetmanager@weighty-yew-445210-c8.iam.gserviceaccount.com",
                "client_id": "108060892903857127747",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/sheetmanager%40weighty-yew-445210-c8.iam.gserviceaccount.com",
                "universe_domain": "googleapis.com"
                }
        data = {
                'date_1': date_1,
                'cred':cred,
                'sheet_id':sheet_id,
                'scopes':["https://www.googleapis.com/auth/spreadsheets"],
                'frame':frame
            }

        with open(path,'wb') as file:
            pkl.dump(data,file)


if __name__ == '__main__':
     genfile = GenFile()
     
        