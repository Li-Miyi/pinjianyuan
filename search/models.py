from django.db import models

from elasticsearch_dsl import Document, Date, Nested, Boolean, \
    analyzer, Completion, Keyword, Text, Integer
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

    class Meta:
        index = "baidu"
        doc_type = "paper"


if __name__ == "__main__":
    PaperType.init()
