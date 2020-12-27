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
                index='gcc',
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
        """
        key_words 关键词
        key_index 检索的索引
        type 搜索类型 mohu：模糊搜索 jingque 精确搜索 gaoji:高级高级搜索 quick:快速搜点，点击首页超链接
        高级搜索的关键词参数形式
        must=字段1,字段2&should=字段3,字段4&must_not=字段1,字段2&字段1=key&字段2=key等等&jingque=字段1,字段2
        must必有,should并含,must_not不含,jingque需要精确搜索的字段
        宽肃搜索的关键词参数形式
        key=关键词&field=字段名
        """
        key_index = request.GET.get("index","gcc").split(",")
        type = request.GET.get("search_type","mohu")
        #模糊与精确的关键词
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
        hit_list = []
        page_nums = 0
        all_total_num = 0
        for i in key_index:
            """遍历索引然后查询"""
            if type == "jingque":
                body = {
                            "query": {
                                "query_string": {
                                    "query": key_words,
                                    "default_operator": "AND"
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
            elif type == "gaoji":
                jingque_list = request.GET.get("jingque").split(',')
                def get_key_list(tiaojian):
                    key_list=[]
                    for i in request.GET.get(tiaojian).split(','):
                        if i in jingque_list:
                            word = request.GET.get(i)
                            key_dict = {
                                "match": {
                                    i:{
                                        "query":word,
                                        "operator": "AND"
                                    }
                                }
                            }
                        else:
                            key_dict = {"match": {i: request.GET.get(i)}}
                        key_list.append(key_dict)
                    return key_list
                must_key = get_key_list("must")
                should_key = get_key_list("should")
                must_not_key = get_key_list("must_not")
                body={
                    "query": {
                        "bool": {
                            "must":must_key,
                            "should": should_key,
                            "must_not": must_not_key
                        }
                    }
                }
            elif type == "quick":
                # 快速的关键词
                key = request.GET.get("key","")
                field = request.GET.get("field","")
                body={
                  "query": {
                    "match": {
                      key: field
                    }
                  }
                }

            else:
                body={
                        "query": {
                            "query_string": {
                                "query": key_words,
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
            response = client.search(
                index=i,
                body=body
            )
            total_nums = response["hits"]["total"]["value"]
            all_total_num += total_nums
            if (page % 10) > 0:
                page_nums += int(total_nums / 10) + 1
            else:
                page_nums += int(total_nums / 10)

            """
            根据当前索引产生返回值，可能会有关于索引的判断逻辑"""
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

                hit_dict["bjspName"]=hit["_source"]["bjspName"]
                hit_dict["productID"] = hit["_source"]["productID"]
                hit_dict["applicantName"] = hit["_source"]["applicantName"]
                hit_dict["applicantAddress"] = hit["_source"]["applicantAddress"]
                hit_dict["naturalProgression"] = hit["_score"]["naturalProgression"]
                hit_dict["productIngredients"]=hit["_source"]["productIngredients"]
                hit_dict["targetPopulation"] = hit["_source"]["targetPopulation"]
                hit_dict["notargetPopulation"] = hit["_source"]["notargetPopulation"]
                hit_dict["useMethods"] = hit["_source"]["useMethods"]
                hit_dict["productSpecifications"] = hit["_score"]["productSpecifications"]
                hit_dict["dateValid"] = hit["_source"]["dateValid"]
                hit_dict["storageMethod"] = hit["_source"]["storageMethod"]
                hit_dict["warning"] = hit["_score"]["warning"]
                hit_dict["pizhunDate"] = hit["_score"]["pizhunDate"]
                hit_list.append(hit_dict)
        end_time = datetime.now()
        last_seconds = (end_time - start_time).total_seconds()


        """
        返回给前端数，并且在前端需要设置显示效果"""
        return render(request, "result.html", {
            "page": page,
            "all_hits": hit_list,
            "key_words": key_words,
            "total_nums": all_total_num,
            "page_nums": page_nums,
            "last_seconds": last_seconds,
            "topn_search": topn_search,
        })
