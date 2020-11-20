from gevent import monkey
monkey.patch_all()
import requests
import json
import time
import os
import datetime
from flask import Flask, request, render_template, send_from_directory, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length
import threading
import hashlib
import time


from gevent import pywsgi
from flask_bootstrap import Bootstrap

app = Flask(__name__)
bootstrap = Bootstrap(app)
app.config['UPLOAD_FOLDER'] = 'upload/'
app.config["SECRET_KEY"]='795sdw35fds465e892986f09a100aa1edf'

class fakeit(FlaskForm):
                username = StringField(label='用户名(手机号!)',
                                    validators=[DataRequired()])
                passwd = PasswordField(label='密码',
                                        validators=[DataRequired()])
                SCKEY = StringField(label='授权密匙',
                                    validators=[DataRequired()])
                name = StringField(label='需要展示的名字(最好不填)')
                address = StringField(label='地址(定位签到才要填)')
                latitude = StringField(label='纬度(定位签到才要填)')
                longitude = StringField(label='经度(定位签到才要填)')
                picname = StringField(label='照片码(拍照签到才要填)')
                submit = SubmitField('提交')

@app.route('/upload',methods=['get','post'])
def upload():
    if request.method == 'GET':
        return render_template('upload.html')
    if request.method == 'POST':
      f = request.files['file']
      temp = str(hashlib.md5(str(time.time()).encode("utf8")).hexdigest())
      dirpath=r''+os.getcwd()+'/'+temp+'.jpg'
      f.save(dirpath)
      return '图片码:(后面的全部)'+temp+'.jpg'

@app.route('/',methods=['get','post'])
def index():
    form = fakeit()
    if request.method == 'GET':
        return render_template('index.html', form=form)
    if request.method == 'POST':
        # 验证表单
        if form.validate_on_submit():
            messages=[]
            session = requests.session()
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.108 Safari/537.36',"Connection": "close"}
            allsubject = []
            allname = []
            allclassid = []
            allcourseid = []
            activates = []
            allaid = []
            cook = []
            allobjectid = []
            conf={}

            class CxSign():
                def __init__(self, num):
                    CxSign.username = conf['username']
                    CxSign.passwd = conf['passwd']
                    CxSign.SCKEY = conf['SCKEY']
                    CxSign.name = conf['name'] 
                    CxSign.address = conf['address']
                    CxSign.longitude = conf['longitude']
                    CxSign.latitude = conf['latitude']
                    CxSign.picname = conf['picname'] 
                    # self.name = conf['name'] 
                    # self.address = conf['address'] 
                    # self.longitude = conf['longitude'] 
                    # self.latitude = conf['latitude'] 
                    # self.picname = conf['picname'] 
                    # self.speed = conf['speed']

                def login(num):  # 获取cookie
                    url = 'https://passport2-api.chaoxing.com/v11/loginregister'
                    data = {'uname': CxSign(num).username, 'code': CxSign(num).passwd, }
                    session = requests.session()
                    cookie_jar = session.post(url=url, data=data, headers=headers).cookies
                    cookie_t = requests.utils.dict_from_cookiejar(cookie_jar)
                    cook.append(cookie_t)
                    print('用户:',data['uname'],'获取cookie成功')
                    # return cookie_t

                def subject(i):  # 获取课程
                    url = "http://mooc1-api.chaoxing.com/mycourse/backclazzdata"
                    res = requests.get(url, headers=headers, cookies=cook[i])
                    cdata = json.loads(res.text)
                    # coursedata=[]
                    # dict_n = {}
                    name = []
                    classid = []
                    courseid = []
                    if (cdata['result'] != 1):
                        print("课程列表获取失败")
                    for item in cdata['channelList']:
                        if ("course" not in item['content']):
                            continue
                        pushdata = {}
                        # pushdata['user'] = str(i)  # 插入用户标记
                        courseid.append(item['content']['course']['data'][0]['id'])
                        name.append(item['content']['course']['data'][0]['name'])
                        classid.append(item['content']['id'])
                    allname.append(name)
                    allclassid.append(classid)
                    allcourseid.append(courseid)
                    # coursedata.append(pushdata)
                    # allsubject.append(coursedata)
                    # return coursedata

                def taskactivelist(i):  # 查找签到任务
                    global a
                    aid = []
                    url = "https://mobilelearn.chaoxing.com/ppt/activeAPI/taskactivelist"
                    for index in range(len(allname[i])):
                        payload = {'courseId': str(allcourseid[i][index]), 'classId': str(allclassid[i][index]),
                                'uid': cook[i]['UID']}
                        time.sleep(1.5)
                        print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '用户:', i, '正在查询课程:', allname[i][index])
                        res = requests.get(url, params=payload, headers=headers, cookies=cook[i])
                        respon = res.status_code
                        # print(index)
                        if respon == 200:  # 网页状态码正常
                            # print(res.text)
                            data = json.loads(res.text)
                            # print(data)
                            activeList = data['activeList']  # 把所有任务提出来
                            for item in activeList:  # 轮询所有的任务
                                if ("nameTwo" not in item):
                                    continue
                                if (item['activeType'] == 2 and item['status'] == 1):  # 查找进行中的签到任务
                                    # signurl = item['url']  # 提取activePrimaryId
                                    aid = item['id']  # 提取activePrimaryId
                                    if (aid not in activates):  # 查看是否签到过
                                        print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                            '[签到]', allname[i][index], '查询到待签到活动 活动名称:%s 活动状态:%s 活动时间:%s aid:%s' % (
                                                item['nameOne'], item['nameTwo'], item['nameFour'], aid))
                                        CxSign.sign(aid, i, index)  # 调用签到函数
                        else:
                            print('error', respon)  # 不知道为啥...

                def token(self):  # 获取上传图片用的token
                    url = 'https://pan-yz.chaoxing.com/api/token/uservalid'
                    res = requests.get(url, headers=headers, cookies=cook[0])
                    tokendict = json.loads(res.text)
                    return (tokendict['_token'])

                def upload(i):  # 上传图片
                    try:
                        picname = CxSign(i).picname
                    except:
                        picname = ''

                    if picname.isspace() or len(picname) == 0:
                        return
                    else:
                        url = 'https://pan-yz.chaoxing.com/upload'
                        files = {'file': (picname, open(picname, 'rb'),
                                        'image/webp,image/*',), }
                        res = requests.post(url, data={'puid': cook[0]['UID'], '_token': CxSign.token(i)}, files=files,
                                            headers=headers, cookies=cook[0])
                        resdict = json.loads(res.text)
                        allobjectid.append(resdict['objectId'])
                        # return (resdict['objectId'])

                def sign(aid, i, index):  # 签到,偷了个懒,所有的签到类型都用这个,我测试下来貌似都没问题
                    url = "https://mobilelearn.chaoxing.com/pptSign/stuSignajax"
                    if len(CxSign(i).picname) == 0:
                        allobjectid.append('')
                        objectId = ''

                    else:
                        CxSign.upload(i)
                        objectId = allobjectid[i]
                    try:
                        name = CxSign(i).name
                    except:
                        try:
                            name = CxSign.name
                        except:
                            name = ''

                    try:
                        address = CxSign(i).address
                    except:
                        try:
                            address = CxSign.address
                        except:
                            address = ''

                    try:
                        longitude = CxSign(i).longitude
                    except:
                        try:
                            longitude = CxSign.longitude
                        except:
                            longitude = ''
                    try:
                        latitude = CxSign(i).latitude
                    except:
                        try:
                            latitude = CxSign.latitude
                        except:
                            latitude = ''

                    data = {'name': name, 'address': address, 'activeId': aid, 'uid': cook[i]['UID'],
                            'longitude': longitude, 'latitude': latitude, 'objectId': objectId}
                    # data = { 'activeId': aid, 'uid': cook[i]['UID'],}
                    
                    res = requests.post(url, data=data, headers=headers, cookies=cook[i])
                    print("签到状态:", res.text)
                    messages.append(res.text)
                    if res.text == 'success':
                        CxSign.push(i, index, res.text)
                    activates.append(aid)

                def push(i, index, msg):
                    try:
                        E_SCKEY = CxSign(i).SCKEY
                    except:
                        try:
                            E_SCKEY = CxSign.SCKEY
                        except:
                            E_SCKEY = ''
                    if E_SCKEY.isspace() or len(E_SCKEY) == 0:

                        return
                    else:
                        api = 'https://sc.ftqq.com/' + E_SCKEY + '.send'
                        title = u"签到辣!"
                        content = '用户:' + str(i) + '\n\n课程: ' + allname[i][index] + '\n\n签到状态:' + msg
                        data = {
                            "text": title,
                            "desp": content
                        }
                        requests.post(api, data=data)
                        print('已推送')


            conf=request.form.to_dict()
            for (k,v) in conf.items():
                if v == None:
                    v=''
            if conf['SCKEY']=='nmslxxt':
                conf['SCKEY']==''
                print(conf)
                number = len(conf['username'])

                CxSign.login(1)
                time.sleep(0.8)
                CxSign.subject(0)
                time.sleep(0.8)
                CxSign.taskactivelist(0)
                return json.dumps(messages,ensure_ascii=False)
            else:
                return render_template('index.html', form=form)
app.run(host='0.0.0.0',port=80,debug=True,threaded=True)
