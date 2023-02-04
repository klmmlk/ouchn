# -*- coding:utf-8 -*-
import sys
import time
import requests
import re
import js2py
import base64
import pickle
import os
from prettytable import PrettyTable
import threading


class NoProblem(BaseException):
    def __init__(self, message=None):
        self.message = message


class Ouchn(object):
    def __init__(self, userCode, userPwd, tmplist):

        try:
            if userCode in tmplist:
                now_time = int(time.time())
                with open(f'./tmp/{userCode}', 'rb') as f:
                    last_time, name, last_session = pickle.load(f)
                if now_time - last_time < 7200:
                    self.session = last_session
                    self.name = name
                    self.loignStatus = True
                else:
                    raise NoProblem('111')
            else:
                raise NoProblem('111')
        except NoProblem:
            self.session = requests.Session()
            self.session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1518.70 "
            })
            self.name = None
            self.userCode = userCode
            self.verify_code = None
            self.random_key = None
            self.get_login_page()
            self.userdata = self.encode_data([str(userCode), str(userPwd)])
            self.verifyCode()
            self.login()

    def get_login_page(self):
        url = 'https://iam.pt.ouchn.cn/am/UI/Login?realm=%2F&service=initService&goto=https%3A%2F%2Fiam.pt.ouchn.cn' \
              '%2Fam%2Foauth2%2Fauthorize%3Fservice%3DinitService%26response_type%3Dcode%26client_id' \
              '%3D345fcbaf076a4f8a%26scope%3Dall%26redirect_uri%3Dhttps%253A%252F%252Fmenhu.pt.ouchn.cn%252Fouchnapp' \
              '%252Fwap%252Flogin%252Findex%26decision%3DAllow '

        req = self.session.get(url)
        if req.status_code == 200:
            regex1 = r"(?<=name=\"random\".value=\").+(?=\")"
            matches1 = re.search(regex1, req.text).group()
            self.random_key = matches1

            regex2 = r"(?<=name=\"SunQueryParamsString\".value=\").+(?=\")"
            self.sunQueryParamsString = re.search(regex2, req.text).group()

            regex3 = r"(?<=name=\"goto\".value=\").+(?=\")"
            self.goto = re.search(regex3, req.text).group()

    def encode_data(self, codes: list):
        def read_json(file_name):
            with open(file_name, 'r', encoding='UTF-8') as file:
                result = file.read()
            return result

        js = read_json("./des.js")
        test = js2py.EvalJs()
        test.execute(js)
        result = []
        for i in codes:
            result.append(test.strEnc(i, self.random_key))
        return result

    def verifyCode(self):
        url = 'https://iam.pt.ouchn.cn/am/validate.code'
        verify_url = 'https://iam.pt.ouchn.cn/am/validatecode/verify.do'
        req = self.session.get(url)
        if req.status_code == 200:
            code_ocr = requests.post('http://152.67.249.191:9898/ocr/b64/text',
                                     data=base64.b64encode(req.content).decode())
            if code_ocr.status_code == 200:
                # print(code_ocr.text)
                code_verify = self.session.post(verify_url, data={'validateCode': code_ocr.text}).json()
                if code_verify['state'] == 'success':
                    self.verify_code = code_ocr.text
                else:
                    for i in range(5):
                        self.verifyCode()
        else:
            return False

    def login(self):
        login_url = 'https://iam.pt.ouchn.cn/am/UI/Login'
        data = {
            'IDToken1': self.userdata[0],
            'IDToken2': self.userdata[1],
            # 'IDToken1': 'CCCE346E53115CC3B426804C6667F4FE0F65C21D6AF7FEFD2885E0A94909A9AD',
            # 'IDToken2': 'A48351D40F533D4A917A84E2D216C4F7D1A467D82C34A970',
            'IDToken3': self.verify_code,
            'goto': self.goto,
            'gotoOnFail': '',
            'SunQueryParamsString': self.sunQueryParamsString,
            'encoded': 'true',
            'gx_charset': 'UTF-8'
        }
        login_req = self.session.post(login_url, data=data)
        try:
            name_req = self.session.post('https://menhu.pt.ouchn.cn/ouchnapp/wap/user/get-info').json()
            self.name = name_req["d"]["base"]["realname"]
        except requests.exceptions.JSONDecodeError:
            self.loignStatus = False
            return False
        if login_req.status_code == 200:
            self.tpl_write()
            self.loignStatus = True
        else:
            self.loignStatus = False

    def get_data(self):
        test_url = 'https://menhu.pt.ouchn.cn/ouchnapp/wap/course/xskc-pc'
        exam_url2 = 'https://menhu.pt.ouchn.cn/ouchnapp/wap/cj/cj'
        req: dict = self.session.post(test_url, data={'page': 1, 'page_size': 20}).json()
        if 'm' in req.keys() and req['m'] == "操作成功":
            data = req['d']['list']
        else:
            return False
        stu_data = {'name': self.name, 'test': [], 'exam': []}
        for i in data:
            sub_data = {
                'sub_name': i['name'],
                "completeness": i["completeness"],
                "test": None
            }
            test_data = []
            for each in i["activitys"]:
                test_data.append(
                    f'{each["name"]}:完成{each["completed"]}/{each["num"]}'
                )
            sub_data.update({"test": test_data})
            stu_data['test'].append(sub_data)
        return stu_data

    def tpl_write(self):
        now = int(time.time())
        with open(f'./tmp/{self.userCode}', 'wb') as f:
            pickle.dump([now, self.name, self.session], f)
        pass


def init():
    tips = "*******请按照下面的格式写入账号密码********\n" \
           "*************每行一个账号***************\n" \
           "*******账号,密码（中间使用英文逗号隔开）****\n" \
           "*                                    *\n" \
           "*        123456789,password          *\n" \
           "*        987654321,password          *\n" \
           "*                                    *\n" \
           "*==========在我下面填写账号=============*\n"
    if 'count.txt' not in os.listdir('./'):
        with open('./count.txt', 'w', encoding='utf-8') as f:
            f.write(tips)
            f.close()
    if 'tmp' in os.listdir('./'):
        return os.listdir('./tmp')
    else:
        os.mkdir('./tmp')
        init()


def out_data(each_data):
    tb = PrettyTable(title=each_data['name'], field_names=['科目', '学习进度', '作业完成情况'])
    for each in each_data['test']:
        tb.add_row([each['sub_name'], f"{each['completeness']}%", ','.join(each['test'])])
    print(tb)


def read_user():
    with open('./count.txt', 'r', encoding='utf-8') as f:
        user_list = []
        for each in f.readlines():
            if '*' != each[0]:
                each = each.replace('\n', '').split(',')

                user_list.append(each)
    if not user_list:
        return None
    return user_list


if __name__ == '__main__':
    print('*' * 30 + '请耐心等待' + '*' * 30)
    tmp_list = init()
    list1 = read_user()
    if not list1:
        print('填写账号密码')
        time.sleep(3)
        sys.exit()

    def threading_test(**kwargs):
        ouchn = Ouchn(kwargs['username'], kwargs['password'], tmp_list)
        if ouchn.loignStatus:
            data = ouchn.get_data()
            out_data(data)
        else:
            print(f'{kwargs["username"]}账号或密码错误')


    obj = {}
    for i in range(len(list1)):
        obj[i]: threading.Thread = threading.Thread(target=threading_test,
                                                    kwargs={'tmplist': tmp_list, 'username': list1[i][0],
                                                            'password': list1[i][1]})
        obj[i].start()
        obj[i].join()
        while True:
            if len(threading.enumerate()) < 3:
                break

    print('*' * 22 + '查询完毕，如需保存，请自行复制' + '*' * 22)
    while True:
        pass
