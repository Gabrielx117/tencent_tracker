#!/usr/bin/env python3
# coding=utf-8
import time
import urllib.request
import sys
import json
import re
import pickle
import smtplib
from collections import Iterable
from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr

DEBUG = 0
tencent_tracker = '%s/tencent.last.json' % sys.path[0]
history = '%s/history.json' % sys.path[0]
email = '%s/email.json' % sys.path[0]

with open(email, 'r', encoding='utf-8') as f:
    email_info = json.load(f)
to_addr = email_info.get('to_addr')
from_addr = email_info['from_addr']
password = email_info['passwd']
smtp_server = email_info['smtp_server']

date = time.strftime("%Y%m%d", time.localtime())
url = 'http://play.domain.qq.com/getdomain.php?dtime=%s' % date

urllib.request.urlretrieve(url, tencent_tracker)


def is_ipv4(data):  # "IPv4过滤函数"
    ipv4 = re.compile('^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')  # ipv4正则表达式
    return ipv4.match(data)


def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name).encode(), addr))


with open(tencent_tracker, 'r') as f:  # 读取新文件
    tracker = json.load(f)

# 获取上一次列表
try:
    with open(history, 'rb') as i:
        old = set(pickle.load(i))
except:
    IndexError
    old = set()


# 生成新列表
flattened = [val for sublist in tracker['data'].values()
             for val in sublist]  # "压平列表"
ip = list(filter(is_ipv4, flattened))  # 过滤ipv4
new = set(ip)


with open(history, 'wb') as i:  # 将本次列表写入历史文件
    pickle.dump(ip, i)


add = '\n'.join(sorted(new - old)) or '暂无'  # 新增差量
remove = '\n'.join(sorted(old - new)) or '暂无'  # 删除差量


email_list = []  # 生成收件人列表
for k,v in to_addr.items():
    email_list.append(_format_addr('%s <%s>' % (k,v)))
email_list = ','.join(email_list)


# 填写邮件内容
msg = MIMEText('新增\n%s\n删除\n%s' % (add, remove), 'plain', 'utf-8')
msg['From'] = _format_addr('天津网管监控 <%s>' % str(from_addr))
msg['To'] = email_list
msg['Subject'] = Header('腾讯Tracker更新(%s)' %
                        str(tracker['atime'])).encode()


# 发送邮件
server = smtplib.SMTP(smtp_server, 25)
server.login(from_addr, password)
server.sendmail(from_addr, to_addr.values(), msg.as_string())
server.quit()

if DEBUG == 1:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    server.set_debuglevel(1)
    # print(date)
    # print(url)
    # print(new)
    # print(old)
    print('add')
    print(add)
    print('remove')
    print(remove)
