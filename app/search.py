# -*- coding: utf-8 -*-
# @author: NiHao

import zlib
from thulac import thulac


class BloomFilter(object):
    # 布鲁过滤器，判断字段是否一定不再分词字典中
    def __init__(self, size):
        self.size = size
        self.value = [False]*size

    def add_value(self, value):
        index = hash(value) % self.size
        self.value[index] = True

    def might_contain(self, value):
        index = hash(value) % self.size
        return self.value[index]


class Segment(object):
    # 分词
    def __init__(self):
        # 载入并初始化 thulac
        self.thu = thulac()

    def thulac(self, text):
        # 调用 thulac 模块进行分词（自然语言分词）
        # type text: string
        # rtype: set
        if not isinstance(text, str):
            raise ValueError
        results = set()
        results_list = self.thu.cut(text)
        for item in results_list:
            if item[1] == 'w':
                break
            results.add(item[0])
        return results

    @staticmethod
    def sub_segment(text):
        # 单字 分词
        # type text: string
        # rtype: set
        if not isinstance(text, str):
            raise ValueError
        results = set(text)
        return results

    def cut(self, text):
        # 使用上面2种方法分词
        return self.thulac(text).union(self.sub_segment(text))

    def init_app(self, app):
        pass


class Search(object):
    # 信息源量较大时再考虑临时储存，或建立索引文件 -----------------------------------------
    """建立索引、搜索"""
    def __init__(self, bf_size=100):
        self.bf = BloomFilter(bf_size)
        self.terms = {}
        self.events = {}
        self.segment = Segment()

    def add_event(self, event, event_id=None):
        # 添加信息源，并分词，形成分词字典
        event_id = event_id or zlib.crc32(event.encode('utf-8'))    # 通过crc32 函数生成event 的唯一id
        self.events[event_id] = event

        for term in self.segment.cut(event):
            self.bf.add_value(term)
            if term not in self.terms:
                self.terms[term] = set()
            self.terms[term].add(event_id)

    def auto_add_events(self, **kwargs):
        # 添加所有的tv 名称，当前功能只索引tv 名称
        db = kwargs.get('db')
        TV = kwargs.get('TV')
        if not db or not TV:
            raise ValueError
        try:
            id_and_name = db.session.query(TV.id, TV.name).all()
            for event_id, event in id_and_name:
                self.add_event(event, event_id)
        except Exception as e:
            print(e)
            raise Exception

    def search(self, key, return_id=True):
        # 在已有的分词字典中搜索，返回信息源。使用前需通过 self.add_event 添加事件，建立索引。
        # rtype: list of tv_id
        results = {}
        result_of_events = []
        # type terms: list
        key_terms = self.segment.cut(key)
        for term in key_terms:
            if not self.bf.might_contain(term):
                break
            if term not in self.terms:
                break
            for event_id in self.terms[term]:
                if event_id in results:
                    results[event_id] += 1
                else:
                    results[event_id] = 1

        sorted_results = sorted(results, key=lambda x: results[x], reverse=True)

        # return_id 为True 时，返回信息源的 id，否则返回信息源的名称
        if return_id:
                result_of_events = sorted_results
        else:
            for event_id in sorted_results:
                result_of_events.append(self.events[event_id])
        return result_of_events


