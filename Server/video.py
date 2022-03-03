import socket
import cv2
import numpy as np
import detect2
import torch
import pandas as pd
from sqlalchemy import create_engine
from PIL import Image
import base64
from io import BytesIO
import time



def recvall(sock, count):
    # 바이트 문자열
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf: return None
        buf += newbuf
        count -= len(newbuf)
    return buf

def send(client_socket, sendtext):
    try:
        #print("client to server:",sendtext)
        client_socket.sendall(sendtext.encode())
    except:
        pass



def server():
    HOST = ''
    PORT = 9999

    # TCP 사용
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


    # 서버의 아이피와 포트번호 지정
    s.bind((HOST, PORT))
    print('Socket now listening')
    s.listen(10)


    # 연결, conn에는 소켓 객체, addr은 소켓에 바인드 된 주소
    conn, addr = s.accept()
    print('접속 완료')

    #DataBase pandas
    engine = create_engine('mysql+pymysql://root:111111@113.198.234.39/project', echo=False)
    while True:
        # client에서 받은 stringData의 크기 (==(str(len(stringData))).encode().ljust(16))
        img_read1 = pd.read_sql(sql='select pic from illegal_carnumber', con=engine)


        if True:
            length = recvall(conn, 16)
            stringData = recvall(conn, int(length))
            data = np.fromstring(stringData, dtype='uint8')

            # data를 디코딩한다.
            frame = cv2.imdecode(data, cv2.IMREAD_COLOR)
            with torch.no_grad():
                illegal = str(True)

                detect_class, detect_carnumber = detect2.detect(frame)#################DB에서 차량번호가 존재하는지 불러오는 code###################
                if (len(str(detect_carnumber)) == 7 or len(str(detect_carnumber)) == 8):
                    img_read = pd.read_sql(sql="select EXISTS (select * FROM legal_carnumber WHERE carnumber='"+detect_carnumber+"') as success;", con=engine)

                    img_str1 = img_read['success'].values[0]
                    if (img_str1 == 1):
                        print("합법 차량입니다.")
                        illegal = str(False)
                    else:
                        ## 이미지 DB에 저장하는 code
                        print(time.strftime('%c', time.localtime(time.time())), detect_carnumber)

                        buffer = BytesIO()
                        im = Image.fromarray(frame)
                        im.save(buffer, format='jpeg')
                        img_str = base64.b64encode(buffer.getvalue())

                        img_df = pd.DataFrame(
                            {'date': time.strftime('%c', time.localtime(time.time())), 'carnumber': detect_carnumber,
                             'location' : 'B5','fine': 100000,'overlap':0, 'pic': [img_str]})

                        img_df.to_sql('illegal_carnumber', con=engine, if_exists='append', index=False)

                        illegal = str(True)
                        ## DB에서 Python 이미지으로 불러오는 code
                    #########################################################################
                    send(conn, illegal)
                else:
                    print(time.strftime('%c', time.localtime(time.time())), detect_class)
                    buffer = BytesIO()
                    im = Image.fromarray(frame)
                    im.save(buffer, format='jpeg')
                    img_str = base64.b64encode(buffer.getvalue())
                    img_df = pd.DataFrame({'date': time.strftime('%c', time.localtime(time.time())), 'class': detect_class, 'pic': [img_str]})
                    img_df.to_sql('illegal_action', con=engine, if_exists='append', index=False)



if __name__ == "__main__":
    server()
