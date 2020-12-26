import json
import redis
from django.shortcuts import render
from django.views.generic.base import View
from .models import GCC
from django.http import HttpResponse
from elasticsearch import Elasticsearch
from datetime import datetime
from django.db import connection
from django.http import HttpResponseRedirect


client = Elasticsearch(hosts=["47.110.225.193:9200"],http_auth=('elastic', 'Pinjianyuan666'))
# redis_cli = redis.StrictRedis(password='root')
redis_cli = redis.StrictRedis()


# Create your views here.

class IndexView(View):
    # 首页
    def get(self, request):
        return render(request, "index.html")


# Create your views here.
class SearchSuggest(View):
    def get(self, request):
        key_words = request.GET.get('s', '')
        re_datas = []

        if key_words:
            response = client.search(
                index='movie',
                body={
                    "suggest": {
                        "my_suggest": {
                            "prefix": key_words,
                            "completion": {
                                "field": "suggest",
                                "size": 10,
                                "fuzzy": {
                                    # 模糊查询，编辑距离
                                    "fuzziness": 2
                                }
                            }
                        }
                    }
                }
            )
            for match in response.my_suggest[0].options:
                source = match._source
                re_datas.append(source["bjspName"])
        return HttpResponse(json.dumps(re_datas), content_type="application/json")


class SearchView(View):
    def get(self, request):
        key_words = request.GET.get("q", "")
        topn_search = redis_cli.zrevrangebyscore("search_keywords_set","+inf","-inf",start=0,num=5)
        # 搜索记录、热门搜索功能实现
        page = request.GET.get("p", "1")
        try:
            page = int(page)
            if page <= 1:
                page = 1
        except:
            page = 1

        start_time = datetime.now()
        response = client.search(
                index="gcc",
                body={
                    "query": {
                        "multi_match": {
                            "query": key_words,
                            "fields": ["bjspName", "applicantName"]
                        }
                    },
                    "from": (page - 1) * 10,
                    "size": 10,
                    "highlight": {
                        "pre_tags": ["<span class='keyWord'>"],
                        "post_tags": ["</span>"],
                        "fields": {
                            "bjspName": {},
                            "applicantName": {},
                        }
                    }
                }
        )
        end_time = datetime.now()
        last_seconds = (end_time - start_time).total_seconds()
        total_nums = response["hits"]["total"]["value"]

        if (page % 10) > 0:
            page_nums = int(total_nums / 10) + 1
        else:
            page_nums = int(total_nums / 10)

        hit_list = []
        print(response)
        for hit in response["hits"]["hits"]:
            hit_dict = {}
            """
            这里需要设置返回的数据"""
            # if "title_detail" in hit["highlight"]:
            #     hit_dict["title_detail"] = "".join(hit["highlight"]["title_detail"])
            # else:
            #     hit_dict["title_detail"] = hit["_source"]["title_detail"]
            #
            # if "title" in hit["highlight"]:
            #     hit_dict["title"] = "".join(hit["highlight"]["title"])
            # else:
            #     hit_dict["title"] = hit["_source"]["title"]
            #
            # hit_dict["crawl_time"] = hit["_source"]["crawl_time"]
            # hit_dict["url"] = hit["_source"]["url"]
            # hit_dict["sourcename"] = hit["_source"]["sourcename"]
            # hit_dict["download_url"] = hit["_source"]["download_url"]
            # hit_dict["score"] = hit["_score"]

            hit_list.append(hit_dict)
        """
        返回给前端数，并且在前端需要设置显示效果"""
        return render(request, "result.html", {
            "page": page,
            "all_hits": hit_list,
            "key_words": key_words,
            "total_nums": total_nums,
            "page_nums": page_nums,
            "last_seconds": last_seconds,
            "topn_search": topn_search,
        })
