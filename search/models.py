from django.db import models

from elasticsearch_dsl import Document, Date, Nested, Boolean, \
    analyzer, Completion, Keyword, Text, Integer,Object,Long
from elasticsearch_dsl.analysis import CustomAnalyzer as _CustomAnalyzer
from elasticsearch_dsl.connections import connections

connections.create_connection(hosts=["47.110.225.193:9200"],http_auth=('elastic', 'Pinjianyuan666'))


class CustomAnalyzer(_CustomAnalyzer):
    def get_analysis_definition(self):
        return {}


ik_analyzer = CustomAnalyzer("ik_max_word", filter=["lowercase"])


class PaperType(Document):
    suggest = Completion(analyzer=ik_analyzer)  # 用于自动补全

    paper_title = Text(analyzer="ik_max_word")
    paper_writer = Text()
    paper_time = Text()
    paper_cite_count = Integer()
    paper_source = Keyword()
    paper_abstract = Text(analyzer="ik_max_word")
    paper_keywords = Text(analyzer="ik_max_word")
    paper_DOI = Text()
    paper_download_link = Text()

    applicantAddress = Text(analyzer="ik_max_word")
    applicantName = Text(analyzer="ik_max_word")
    bjspName = Text(analyzer="ik_max_word")
    bufaDate = Date()
    changeDate = Date()
    dateValid = Keyword()
    expirationDate = Date()
    naturalProgression = Text(analyzer="ik_max_word")
    notargetPopulation = Keyword()
    pizhunDate = Date()
    productID = Keyword()
    productIngredients = Object()
    qianProductID = Keyword()
    qianProductId = Text()
    shourangAddress = Text(analyzer="ik_max_word")
    shourangName = Text(analyzer="ik_max_word")
    storageMethod = Text(analyzer="ik_max_word")
    targetPopulation = Keyword()
    useMethods = Text(analyzer="ik_max_word")
    warning = Text(analyzer="ik_max_word")
    zhuanrangAddress = Text(analyzer="ik_max_word")
    zhuanrangChName = Text(analyzer="ik_max_word")
    zhuanrangDate = Date()
    zhuanrangEnName = Text(analyzer="ik_max_word")

    class Meta:
        index = "gcc"


if __name__ == "__main__":
    PaperType.init()
