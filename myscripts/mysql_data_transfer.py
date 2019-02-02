# -*- coding: utf-8 -*-
# @author: NiHao
""" Mysql 数据转移： """
from pymysql import connect

target_field = ['douban_id', 'name', 'score', 'tv_type', 'stars', 'director', 'country',
                'tv_release', 'episodes', 'alias', 'summery', 'img_sm']
source_field = ['id', '片名', '评分', '类型', '主演', '导演', '制片国家地区',
                '首播', '集数', '又名', '简介', 'img_url']

s = ','.join(source_field)
sql1 = 'SELECT %s FROM %s' % (s, 'oo.tv')

t = ','.join(target_field)
v = ','.join(['%s']*len(target_field))

con = connect(host='localhost', user='root', password='0000')
cur1 = con.cursor()
cur1.execute(sql1)

try:
    with con.cursor() as cur2:
        for r in cur1.fetchall():
            r = list(r)
            if r[0]:
                r[0] = int(r[0])
            if r[2]:
                r[2] = float(r[2])
            if r[8]:
                r[8] = int(r[8])
            for i in r:
                if i is None:
                    i = 'null'
            result = tuple(r)
            sql2 = 'INSERT INTO lacy.tv(%s) VALUES(%s)' % (t, v)
            # print(sql2)
            # break
            cur2.execute(sql2, result)
        con.commit()
finally:
    con.close()
    # pass

