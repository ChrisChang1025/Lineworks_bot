from authlib.jose import jwt
import time , requests , json
from Logger import create_logger
log  = create_logger()



def generate_jwt(): # 產新的 jwt 
    header = {"alg":"RS256","typ":"JWT"}
    time_ =  int(time.time() ) + 1000 # 需 將 time 故意往後加 分鐘 ,否則用當下 時間 會jwt token expired

    payload = {
        "iss":"", # clinet_id
        "sub":"", # Service Account
        "iat": time_,
        "exp": time_ 
        }


    PRIVATE_KEY = '''-----BEGIN RSA PRIVATE KEY-----
-----END RSA PRIVATE KEY-----'''

    token = jwt.encode(header, payload, PRIVATE_KEY)
    token = token.decode()
    
    return token


def get_token(token_type= 'refresh' , refresh_token = ''): 
    '''
    token_type 預設 refresh , 會拿已經有的 refresh_token 來產新的 access_token , 過期時間 為24小時
    token_type 帶其他 是產出新的 access_token 和 refresh_token , 過期時間 為24小時 (只需要產一次 )
    '''

    url = 'https://auth.worksmobile.com/oauth2/v2.0/token' # 2.0 url 

    Session = requests.session()

    header  = {
    'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    try:
        if token_type == 'refresh': # 將已經產好的  access_token refresh


            log.info('refresh token 產新的 access_token')

            data = {
                'grant_type': 'refresh_token' , 
                'client_id': '' , 
                'client_secret' : '', 
                'refresh_token':  refresh_token ,
            }

        else:
            log.info('產全新的 access_token 和 refresh_token ')

            data = {
                'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer' , 
                'client_id': '' , 
                'client_secret' : '', 
                'assertion':  generate_jwt() ,
                'scope' : 'bot'

            }



        r = Session.post( url = url , data = data ,   headers=header)
        log.info('response: %s '%r.text)
        token = json.loads(r.text)
        

        return token['access_token']
    
    except Exception as e:
        log.error('get_token error: %s '% e)
        
        return False




