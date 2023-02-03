import js2py

random_key = "OqxQ1Iea4njSROH/N06Tuw=="
def readJson(file_name):
    with open(file_name, 'r', encoding='UTF-8') as file:
        result = file.read()
    return result


js = readJson("./des.js")
test = js2py.EvalJs()
test.execute(js)
sss = test.strEnc('Ouchn@2021',random_key)
print(sss)
# print(js)
# test.execute(js)
# print(test.strEnc('123','22222','',''))
