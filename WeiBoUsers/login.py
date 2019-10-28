"""
Version: Python3.7
Author: OniOn
Site: http://www.cnblogs.com/TM0831/
Time: 2019/3/27 16:40
"""
import requests
import time
import json
import base64
import rsa
import binascii
from bs4 import BeautifulSoup
import random
import re
import pymongo


# 返回随机的User-Agent
def get_random_ua():
    user_agent_list = [
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1"
        "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/"
        "536.11",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",
        "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5",
        "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 "
        "Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
        "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"
    ]
    return {
        "User-Agent": random.choice(user_agent_list)
    }


# 把数据保存到MongoDB数据库中
conn = pymongo.MongoClient(host="127.0.0.1", port=27017)
db = conn['Spider']
ito_weibo_fans = db['ito_weibo_fans']
# proxies = {'http': 'http://proxy.spider.ppc.com:40531', 'https': 'http://proxy.spider.ppc.com:40531'}
proxies = {}


def save_ito_fans_list(data):
    print('>>>>>save to mongodb size: ', len(data))
    if len(data) > 0:
        db.ito_fans_list.insert(data)


def update_page(start, end):
    ito_weibo_fans.update_one(filter={'meta': 'pageinfo'}, update={'$set': {'startpage': start, 'endpage': end}})
    pageinfo = ito_weibo_fans.find_one(filter={'meta': 'pageinfo'})
    print(pageinfo)


class WeiBoLogin:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.session()
        self.cookie_file = "Cookie.json"
        self.fans_url = ''    # 粉丝列表链接
        self.follow_url = ''  # 关注列表链接
        self.fans = []        # 粉丝列表
        self.nonce, self.pubkey, self.rsakv = "", "", ""
        self.headers = get_random_ua()
        # self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'}

    def save_cookie(self, cookie):
        """
        保存Cookie
        :param cookie: Cookie值
        :return:
        """
        with open(self.cookie_file, 'w') as f:
            json.dump(requests.utils.dict_from_cookiejar(cookie), f)

    def load_cookie(self):
        """
        导出Cookie
        :return: Cookie
        """
        with open(self.cookie_file, 'r') as f:
            cookie = requests.utils.cookiejar_from_dict(json.load(f))
            return cookie

    def pre_login(self):
        """
        预登录，获取nonce, pubkey, rsakv字段的值
        :return:
        """
        url = 'https://login.sina.com.cn/sso/prelogin.php?entry=weibo&su=&rsakt=mod&client=ssologin.js(v1.4.19)&_={}'.format(int(time.time() * 1000))
        res = requests.get(url)
        js = json.loads(res.text.replace("sinaSSOController.preloginCallBack(", "").rstrip(")"))
        self.nonce, self.pubkey, self.rsakv = js["nonce"], js['pubkey'], js["rsakv"]

    def sso_login(self, sp, su):
        """
        发送加密后的用户名和密码
        :param sp: 加密后的用户名
        :param su: 加密后的密码
        :return:
        """
        data = {
            'encoding': 'UTF-8',
            'entry': 'weibo',
            'from': '',
            'gateway': '1',
            'nonce': self.nonce,
            'pagerefer': 'https://login.sina.com.cn/crossdomain2.php?action=logout&r=https%3A%2F%2Fweibo.com%2Flogout.php%3Fbackurl%3D%252F',
            'prelt': '22',
            'pwencode': 'rsa2',
            'qrcode_flag': 'false',
            'returntype': 'META',
            'rsakv': self.rsakv,
            'savestate': '7',
            'servertime': int(time.time()),
            'service': 'miniblog',
            'sp': sp,
            'sr': '1920*1080',
            'su': su,
            'url': 'https://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack',
            'useticket': '1',
            'vsnf': '1'}
        url = 'https://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.19)&_={}'.format(int(time.time() * 1000))
        r = self.session.post(url, headers=self.headers, data=data, proxies=proxies)
        location = self.get_location_from_script(r.content.decode('gbk'))
        if location != "":
            r = self.session.get(location, headers=self.headers, proxies=proxies)
            # print(r.content.decode("gbk"))
            bs = BeautifulSoup(r.content.decode("gbk"), "lxml")
            scripts = bs.find_all("script")
            scriptstr = scripts[1].text
            searchObj = re.search(r'(location.replace\(.*\'\);)', scriptstr, re.M | re.I)
            if searchObj:
                location = searchObj.group()
                location = location.replace("location.replace('", "").replace("');", "")
                r = self.session.get(location, headers=self.headers, proxies=proxies)
                print(r.content)

    def get_location_from_script(self, content):
        bs = BeautifulSoup(content, "lxml")
        scripts = bs.find_all("script")
        scriptstr = scripts[0].text
        searchObj = re.search(r'(\(.*\);)', scriptstr, re.M | re.I)
        if searchObj:
            location = searchObj.group()
            location = location.replace("(\"", "").replace("\");", "")
            return location
        return None

    def login(self):
        """
        模拟登录主函数
        :return:
        """

        # Base64加密用户名
        def encode_username(usr):
            return base64.b64encode(usr.encode('utf-8'))[:-1]

        # RSA加密密码
        def encode_password(code_str):
            pub_key = rsa.PublicKey(int(self.pubkey, 16), 65537)
            crypto = rsa.encrypt(code_str.encode('utf8'), pub_key)
            return binascii.b2a_hex(crypto)  # 转换成16进制

        # 获取nonce, pubkey, rsakv
        self.pre_login()

        # 加密用户名
        su = encode_username(self.username)
        # 加密密码
        text = str(int(time.time())) + '\t' + str(self.nonce) + '\n' + str(self.password)
        sp = encode_password(text)

        # 发送参数，保存cookie
        self.sso_login(sp, su)
        # for test
        # self.get_main_page('https://weibo.com/p/1006063610794337/home?from=page_100606&mod=TAB&is_all=1#place')
        self.save_cookie(self.session.cookies)
        self.session.close()

    def get_main_page(self, main_page_url):
        """
        进入个人主页, 拿到粉丝列表链接和关注列表链接
        :param main_page_url: 个人主页地址
        :return:
        """
        self.session = requests.session()
        self.session.cookies = self.load_cookie()
        res = self.session.get(main_page_url, headers=self.headers, proxies=proxies)
        # print('个人主页信息：', res.content.decode())
        html = self.get_html_from_script_contains(res.content.decode(), 'fans?')
        if html:
            bs = BeautifulSoup(html, 'lxml')
            links = bs.find_all("a")
            self.follow_url = 'https:' + links[0]['href']
            self.fans_url = 'https:' + links[1]['href']
            print('follow_url:', self.follow_url)
            print('fans_url:', self.fans_url)
            self.get_fans_list(1, 251)
            save_ito_fans_list(wb.fans)
            # for i in range(2, 15):
            #     self.fans = []
            #     start_page = i * 100
            #     end_page = (i + 1) * 100
            #     wb.get_fans_list(start_page, end_page)
            #     print('data crawled >>> start_page: %s, end_page: %s' % (start_page, end_page))
            #     print('crawled fans size: ', len(wb.fans))
            #     if len(wb.fans) == 0:
            #         print('fans size is 0. stop......')
            #         break
            #     save_info(wb.fans)
            #     update_page(start_page, end_page)

    def get_fans_list(self, start_page, end_page):
        """
        爬取当前登录用户的粉丝列表
        :param fans_url: 跳转到粉丝列表的url
        :return:
        """
        if self.fans_url:
            r = self.session.get(self.fans_url, headers=self.headers, proxies=proxies)
            # print(r.content.decode('gbk'))
            fanspage = self.get_html_from_script_contains(r.content.decode(), 'follow_list')
            # fanspage = self.get_html_from_script_contains(r.content.decode(), 'W_pages')
            bs = BeautifulSoup(fanspage, 'lxml')
            a_tags = bs.select('.W_pages')[0].find_all('a')
            a_size = len(a_tags)
            total_page = int(a_tags[a_size - 2].text)
            follow_items = bs.select('.follow_list')[0].select('.follow_item')
            if start_page == 1:
                self.parse_follow_items(follow_items)
                print('parse first page fans, self.fans size: %s' % str(len(self.fans)))
            next_page_url = a_tags[2]['href']
            page_prefix = 'https://weibo.com'
            if end_page > total_page + 1:
                end_page = total_page + 1
            _ref = self.fans_url
            end_index = next_page_url.index('page=')
            next_page_url = next_page_url[:end_index]
            for i in range(start_page, end_page):
                _t = str(int(time.time()*10**6))
                page_url = next_page_url + 'page=%s&ajaxpagelet=1&ajaxpagelet_v6&_ref=%s&_t=%s' % (str(i), _ref, 'FM_' + _t)
                r = self.session.get(page_prefix + page_url, headers=self.headers, timeout=5, proxies=proxies)
                html = self.get_html_from_script_contains(r.content.decode(), 'follow_list')
                # html = self.get_html_from_script_contains(r.content.decode(), 'W_pages')
                item_size = 0
                if html:
                    bs = BeautifulSoup(html, 'lxml')
                    follow_items = bs.select('.follow_list')[0].select('.follow_item')
                    self.parse_follow_items(follow_items)
                    item_size = len(follow_items)
                    if item_size == 0:
                        break
                # else:
                #     time.sleep(random.randint(1, 3))
                # print('current page: %s, item_size: %s, next_page_url: %s' % (i, item_size, next_page_url))
                print('current page: %s, item_size: %s, self_fans: %s, page_url: %s' % (i, item_size, len(self.fans), page_url))
                # print(time.sleep(random.randint(1, 3)))
        else:
            print('self.fans_url is empty!!!')

    def parse_follow_items(self, follow_items):
        # print('================ready to parse follow_items size: ', len(follow_items))
        # print('fans size before parse follow_items: ', len(self.fans))
        page_prefix = 'https://weibo.com'
        for item in follow_items:
            a = item.find_all('a')[0]
            fan = {}
            fan['url'] = page_prefix + a['href']
            fan['nick'] = a['title']
            info_name_ele = item.select_one('.info_name')
            verify = info_name_ele.select_one('.icon_approve')  # 微博个人认证
            if verify:
                fan['verify'] = True
            vip = info_name_ele.find(attrs={'title': '微博会员'})
            if vip:
                fan['vip'] = True
            icon_male = info_name_ele.select_one('.icon_male')
            if icon_male:
                fan['gender'] = 'male'
            icon_female = info_name_ele.select_one('.icon_female')
            if icon_female:
                fan['gender'] = 'female'
            a_links = item.select_one('.info_connect').find_all('a')
            info_intro = item.select_one('.info_intro')  # 简介
            if info_intro:
                fan['intro'] = info_intro.text.strip()
            if a_links and len(a_links) > 2:
                fan['follow'] = a_links[0].text
                fan['fans'] = a_links[1].text
                fan['weiboNum'] = a_links[2].text
            info_add = item.select_one('.info_add')
            if info_add:
                fan['address'] = info_add.text.replace("地址", "").replace(" ", "").replace("\"", "")

            info_from = item.select_one('.info_from')
            if info_from:
                fan['from'] = info_from.text.replace(" ", "").replace("\"", "")
            # print(fan)
            self.fans.append(fan)
        # print('fans size after parse follow_items: ', len(self.fans))


    def get_json_from_script(self, script):
        searchObj = re.search(r'({.*})', script, re.M | re.I)
        if searchObj:
            data = searchObj.group()
            jsonobj = json.loads(data)
            return jsonobj
        return None

    def get_script_from_content(self, content):
        bs = BeautifulSoup(content, "lxml")
        scripts = bs.find_all("script")
        return scripts

    def get_html_from_script_contains(self, content, target):
        scripts = self.get_script_from_content(content)
        for script in scripts:
            if target in str(script):
                jsonObj = self.get_json_from_script(str(script))
                return jsonObj['html']
        return None


if __name__ == '__main__':
    # user_name = '18750103605'
    # pass_word = 'jayson.0201'
    user_name = 'info@itocases.com'
    pass_word = 'yditocases881'
    wb = WeiBoLogin(user_name, pass_word)
    wb.login()
    wb.get_main_page('https://weibo.com/p/1006063610794337/home?from=page_100606&mod=TAB&is_all=1#place')
    # wb.get_main_page('https://weibo.com/jansonzhuo/profile?rightmod=1&wvr=6&mod=personinfo&ajaxpagelet=1&ajaxpagelet_v6=1&__ref=%2Fjansonzhuo%2Fhome%3Fwvr%3D5%26lf%3Dreg&_t=FM_157197991830521')
    # wb.get_main_page('https://weibo.com/p/1006063610794337/home?from=page_100606&mod=TAB&is_all=1#place')