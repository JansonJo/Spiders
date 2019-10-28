# -*- coding:utf-8 -*-
import pymongo


def save_data(data):
    conn = pymongo.MongoClient(host="127.0.0.1", port=27017)
    db = conn["Spider"]
    print('save to mongodb: ', data)
    db.WeiBoUsers.insert(data)


if __name__ == '__main__':
    conn = pymongo.MongoClient(host="127.0.0.1", port=27017)
    spiderdb = conn['Spider']
    ito_fans_list = spiderdb['ito_fans_list']
    # user = WeiBoUsers.find_one(filter={'用户名': '何猷君MarioHo'})
    # pageinfo = ito_weibo_fans.find_one(filter={'meta': 'pageinfo'})
    # print(pageinfo)
    # ito_weibo_fans.update_one(filter={'meta': 'pageinfo'}, update={'$set': {'startpage': 201, 'endpage': 300}})
    # pageinfo = ito_weibo_fans.find_one(filter={'meta': 'pageinfo'})
    # print(pageinfo)
    fans_list = ito_fans_list.distinct('url')
    print(len(fans_list))
    distinct_fans_list = []
    for url in fans_list:
        data = ito_fans_list.find_one(filter={'url': url})
        distinct_fans_list.append(data)
    print(len(distinct_fans_list))
    import pandas as pd
    pd.DataFrame(distinct_fans_list, columns=[''])
