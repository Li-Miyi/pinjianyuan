# -*- coding:utf-8 -*-
__author__ = "東飛"
__date__ = "2018-1-28"
from django.db import models
from elasticsearch_dsl import Document, Date,  Keyword, Text, Completion

from elasticsearch_dsl.connections import connections
connections.create_connection(hosts=["47.110.225.193:9200"],http_auth=('elastic', 'Pinjianyuan666'))
# Create your models here.




from elasticsearch_dsl.analysis import CustomAnalyzer as _CustomAnalyzer
# 设置搜索建议字段
class CustomAnalyzer(_CustomAnalyzer):
    def get_analysis_definition(self):
        return {}

# ik_analyzer = CustomAnalyzer("ik_max_word",filter=["lowercase"])
ik_analyzer = CustomAnalyzer("ik_max_word")

class GCC(Document):

    suggest = Completion(analyzer=ik_analyzer) #自动补全

    class Meta:
        index = "gcc"

