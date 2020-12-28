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
#字段
source = {
       "gcc":["bjspName","productID","naturalProgression","targetPopulation","notargetPopulation","productIngredients","dateValid","expirationDate",
           "useMethods","pizhunDate","productSpecifications","storageMethod", "applicantName","applicantAddress","warning"],
    "jkkk":["bjspChName","bjspEnName","productID","naturalProgression","targetPopulation","notargetPopulation","productIngredients","dateValid","expirationDate",
        "useMethods","pizhunDate","productSpecifications","storageMethod", "applicantName","applicantAddress","warning",
        "country","manufacturerChName","manufacturerEnName","activeIngredient"],

    "rawmaterial":["RawMaterialAlternateName","RawMaterialEnglishName","RawMaterialFunction",
                   "RawMaterialName","activeIngredient","character","description","image","storagePractice",
                   "tropismOfTaste"],
    "other_ingredient":["class_description","functional_ingredients_class","functional_ingresients"],
    "nutrients":["chemical_compound","deficiency","nutrient_name","opinions","physiologic_function",],
    "regulations2":["content","documentNumber","effectiveDate","expirationDate","issueDate",
                    "issuer","title"],
    "buying_guides":["content","guideauthor","title", "suggest"]}
#搜索建议需要展示的字段
suggest_field ={"buying_guides": "suggest","regulations2": "title","jkkk": "bjspChName", "nutrients": "nutrient_name", "other_ingredient": "functional_ingredients_class", "rawmaterial": "RawMaterialName",
                "gcc": "bjspName"}
# Create your views here.

class IndexView(View):
    # 首页
    def get(self, request):
        return render(request, "index.html")


# Create your views here.
class SearchSuggest(View):
    def get(self, request):
        key_words = request.GET.get('s', '')
        #索引参数需要以’,‘逗号分隔
        index = request.GET.get('index','')
        re_datas = []
        # 判断index 变量
        if index == "gcc":
            field = "bjspName"
        elif index == "buying_guides":
            field = "suggest"
        elif index == "jkkk":
            field = "bjspChName"
        else:
            field = [""]
        if key_words:
            response = client.search(
                index=index,
                body={
                    "suggest": {
                        "my_suggest": {
                            "text": key_words,
                            "completion": {
                                "field": field,
                                "skip_duplicates": True,
                                "fuzzy": {
                                    # 模糊查询，编辑距离
                                    "fuzziness": 2
                                }
                            }

                        }}}

            )

            for match in response['suggest']['my_suggest'][0]["options"]:
                text = match["text"]
                re_datas.append(text)
        return HttpResponse(json.dumps(re_datas), content_type="application/json")


class SearchView(View):
    def get(self, request):
        '''
        type 搜索类型 mohu：模糊搜索 jingque 精确搜索 gaoji:高级高级搜索 quick:快速搜点，点击首页超链接
        key_index 检索的索引
        模糊与精确
        key_words 关键词
        高级搜索的关键词参数形式
        must=字段1,字段2&should=字段3,字段4&must_not=字段1,字段2&字段1=key&字段2=key等等&jingque=字段1,字段2
        must必有,should并含,must_not不含,jingque需要精确搜索的字段
        快速搜索的关键词参数形式
        key=关键词&field=字段名
        '''
        key_index = request.GET.get("index", "gcc")
        type = request.GET.get("search_type", "mohu")
        #模糊与精确的关键词
        key_words = request.GET.get("q", "")

        topn_search = redis_cli.zrevrangebyscore("search_keywords_set", "+inf", "-inf", start=0,num=5)
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
        """查询"""
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
                            "pre_tags": ["<b class='keyWord'>"],
                            "post_tags": ["</b>"],
                            "fields": {
                                i: {} for i in source[key_index]
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
                                    "query": word,
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
                },
                "from": (page - 1) * 10,
                "size": 10,
                "highlight": {
                    "pre_tags": ["<b class='keyWord'>"],
                    "post_tags": ["</b>"],
                    "fields": {
                        i: {} for i in source[key_index]
                    }
                }
            }
        elif type == "quick":
            # 快速的关键词
            # key = request.GET.get("key","")
            field = request.GET.get("field", "")
            body = {
                "query": {
                    "match": {
                        "naturalProgression": field
                    }
                },
                "from": (page - 1) * 10,
                "size": 10,
                "highlight": {
                    "pre_tags": ["<b class='keyWord'>"],
                    "post_tags": ["</b>"],
                    "fields": {
                        i: {} for i in source["gcc"]
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
                        "pre_tags": ["<b class='keyWord'>"],
                        "post_tags": ["</b>"],
                        "fields": {
                            i:{} for i in source[key_index]
                        }
                    },
                "aggs": {
                    "function_gc": {
                        "terms": {
                            "field": "naturalProgression.keyword"
                        }
                    }
                }
                }
        response = client.search(
            index=key_index,
            body=body
        )
        total_nums = response["hits"]["total"]["value"]
        all_total_num += total_nums
        if (page % 10) > 0:
            page_nums += int(total_nums / 10) + 1
        else:
            page_nums += int(total_nums / 10)
        """
        根据当前索引产生返回值，可能会有关于索引的判断逻辑
        """
        for hit in response["hits"]["hits"]:
            """
            这里需要设置返回的数据"""
            hit_dict = {}
            for field in source[key_index]:
                if field in hit["_source"]:
                    if "highlight" in hit and field in hit["highlight"]:
                        hit_dict[field] = "".join(hit["highlight"][field])
                    else:
                        hit_dict[field] = hit["_source"][field]
            hit_list.append(hit_dict)

        end_time = datetime.now()
        last_seconds = (end_time - start_time).total_seconds()
        response_final = render(request, "result.html", {
            "page": page,
            "all_hits": hit_list,
            "key_words": key_words,
            "total_nums": all_total_num,
            "page_nums": page_nums,
            "last_seconds": last_seconds,
            "topn_search": topn_search,
            "body": body,
            "index": key_index
        })
        """
        返回给前端数，并且在前端需要设置显示效果"""
        return response_final

def Facet(request):
    index = request.POST.get("index")
    field = request.POST.get("field")
    body = request.POST.get("body").update({"size":0,"aggs": {
            "function_gc": {
                "terms": {
                    "field": field
                }
            }
        }})
    del body["from"]
    del body["highlight"]
    response = client.search(body=body,index=index)
    return HttpResponse({"info":response["aggregations"]["function_gc"]["buckets"]},content_type ="application/json")


def Gaoji(request):
    return render(request,'gaoji.html')


