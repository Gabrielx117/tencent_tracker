#!/usr/bin/env python
#coding=utf-8
import time,urllib,sys
import json,re,pickle,smtplib
from collections import Iterable
from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr

DEBUG=0
tencent_tracker='%s/tencent.last.json' %sys.path[0]
history='%s/history.json' %sys.path[0]
email='%s/email.json' %sys.path[0]
with open(email, 'r') as f:
    email_info = json.load(f)

to_addr=email_info['to_addr']
from_addr = email_info['from_addr']
password = email_info['passwd']
smtp_server = email_info['smtp_server']
email_list=[]
date=time.strftime("%Y%m%d", time.localtime())
url='http://play.domain.qq.com/getdomain.php?dtime=%s' %date

urllib.urlretrieve(url,tencent_tracker)

def is_ipv4(data): #"IPv4过滤函数"
    ipv4 = re.compile('^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$') #ipv4正则表达式
    return ipv4.match(data)
def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))



with open(tencent_tracker, 'r') as f:
    tracker = json.load(f)

with open(history, 'rb') as i: #获取上一次列表
    old = set(pickle.load(i))

flat=lambda L: sum(map(flat,L),[]) if isinstance(L,list) else [L] #"压平列表"
l=flat(tracker['data'].values())

ip=filter(is_ipv4,l) #过滤ipv4
new=set(ip) #生成新列表

with open(history, 'wb') as i: #将本次列表写入历史文件
    pickle.dump(ip,i)

add=str('\n'.join(sorted(list((new.difference(old)))))) or '暂无' #新增差量
remove=str('\n'.join(sorted(list(old.difference(new))))) or '暂无' #删除差量

for k in to_addr.keys():
    email_list.append(_format_addr('%s <%s>' %(k,to_addr[k])))
email_list=','.join(email_list)
msg = MIMEText('新增\n%s\n删除\n%s' % (add,remove), 'plain', 'utf-8')
msg['From'] = _format_addr('天津网管监控 <%s>' % str(from_addr))
msg['To'] = email_list
msg['Subject'] = Header('腾讯Tracker更新(%s)'%str(tracker['atime']), 'utf-8').encode()

server = smtplib.SMTP(smtp_server, 25)
if DEBUG == 1:
    server.set_debuglevel(1)
    print (date)
    print (url)
    print('add')
    print (add)
    print ('remove')
    print (str(remove))
server.login(from_addr, password)
server.sendmail(from_addr, to_addr.values(), msg.as_string())
server.quit()
