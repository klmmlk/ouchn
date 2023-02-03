import requests
import re
import js2py


class Ouchn(object):
    def __init__(self, userCode, userPwd):
        self.cookies = None
        self.random_key = None
        self.get_login_page()
        # self.userdata = self.encode_data([str(userCode), str(userPwd)])

    def get_login_page(self):
        url = 'https://iam.pt.ouchn.cn/am/UI/Login?realm=%2F&service=initService&goto=https%3A%2F%2Fiam.pt.ouchn.cn' \
              '%2Fam%2Foauth2%2Fauthorize%3Fservice%3DinitService%26response_type%3Dcode%26client_id' \
              '%3D345fcbaf076a4f8a%26scope%3Dall%26redirect_uri%3Dhttps%253A%252F%252Fmenhu.pt.ouchn.cn%252Fouchnapp' \
              '%252Fwap%252Flogin%252Findex%26decision%3DAllow '
        regex = r"(?<=name=\"random\".value=\").+(?=\")"
        req = requests.get(url)
        if req.status_code == 200:
            matches = re.search(regex, req.text).group()
            self.cookies = req.cookies.get_dict()
            self.random_key = matches

    def encode_data(self, codes: list):
        def readJson(file_name):
            with open(file_name, 'r', encoding='UTF-8') as file:
                result = file.read()
            return result

        js = readJson("./des.js")
        test = js2py.EvalJs()
        test.execute(js)
        result = []
        for i in codes:
            result.append(test.strEnc(i, self.random_key))
        return result

    def getVerifyCode(self):
        url = 'https://iam.pt.ouchn.cn/am/validate.code'
        req = requests.get(url,cookies=self.cookies)
        f = open('111.png','wb')
        f.write(req.content)
        f.close()
        pass
if __name__ == '__main__':
    ouchn = Ouchn(2251001204366, 'Ouchn@2021')
    ouchn.getVerifyCode()
