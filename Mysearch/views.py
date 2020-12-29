import json
import redis
from django.shortcuts import render
from django.views.generic.base import View
from .models import GCC
from django.http import HttpResponse, JsonResponse
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
    "buying_guides":["content","guideauthor","title", "suggest"],
    "ingredients":["CNS","ExcipientsEnglishName","ExcipientsFunction","ExcipientsName","ExcipientsStandard","LiquidDoseSchedule","SolidDoseSchedule","id","definition"]}
#搜索建议需要展示的字段
suggest_field ={"gcc": "bjspName","jkkk": "bjspChName","buying_guides": "title","regulations2": "title", "nutrients": "chemical_name",
                "other_ingredient": "functional_ingredient_name","rawmaterial": "RawMaterialName","ingredients":"ExcipientsName"}
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
        index = request.GET.get('index')
        re_datas = []
        # 判断index 变量
        if index == "gcc":
            field = "bjspName"
        elif index == "buying_guides":
            field = "title"
        elif index == "jkkk":
            field = "bjspChName"
        elif index == "nutrients":
            field = "chemical_name"
        elif index == "other_ingredient":
            filed = "functional_ingredient_name"
        elif index == "rawmaterial":
            filed = "RawMaterialName"
        elif index == "ingredients":
            filed = "ExcipientsName"
        else:
            field = [""]
        if key_words:
            response = client.search(
                index=index,
                body={
                    "suggest": {
                        "my_suggest": {
                            "prefix": key_words,
                            "completion": {
                                "field": field,
                                "skip_duplicates": True,
                                "size": 5
                                # "fuzzy": {
                                #     # 模糊查询，编辑距离
                                #     "fuzziness": 2
                                # }
                            }
                        }
                    }
                }
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
            base_url = 'http://127.0.0.1:8000/search/?q=' + key_words + '&search_type=' + type + '&index=' + key_index
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
            key=[]
            value=[]
            value_must = []
            value_must_not =[]
            value_should = []
            mohu_list = []
            leixing = []
            type=[]
            bool=[]
            #key的取值是字段名
            key1 = request.GET.get("key1")
            print()
            key2 = request.GET.get("key2")
            key3 = request.GET.get("key3")
            key.append(key1)
            key.append(key2)
            key.append(key3)
            #value取值为字段值
            value1 = request.GET.get("value1")
            value2 = request.GET.get("value2")
            value3 = request.GET.get("value3")
            value.append(value1)
            value.append(value2)
            value.append(value3)
            print(value)
            # type取值为mohu或者jingque
            type1 = request.GET.get("type1")
            type2 = request.GET.get("type2")
            type3 = request.GET.get("type3")
            leixing.append(type1)
            leixing.append(type2)
            leixing.append(type3)
            #bool的取值是must,must_not,should
            bool1 = request.GET.get("bool1")
            bool2 = request.GET.get("bool2")
            bool3 = request.GET.get("bool3")
            bool.append(bool1)
            bool.append(bool2)
            bool.append(bool3)
            print(bool)
            must_list=[]
            must_not_list=[]
            should_list=[]
            jingque_list=[]
            base_url = 'http://127.0.0.1:8000/search/?search_type=gaoji&key1='+key1 +'&key2='+key2+'&key3='+key3+'&value1='+value1+'&value2='+value2+'&value3='+value3+'&type1='+type1+'&type2='+type2+'&type3='+type3+'&bool1='+bool1+'&bool2='+bool2+'&bool3='+bool3
            # url_base=""
            for i in range(0,3) :
                if bool[i] == "must":
                    must_list.append(key[i])
                    value_must.append(value[i])
                if bool[i] == "must_not":
                    must_not_list.append(key[i])
                    value_must_not.append(value[i])
                if bool[i] == "should":
                    should_list.append(key[i])
                    value_should.append(value[i])
                if leixing[i] == "jingque":
                    jingque_list.append(key[i])
                else:
                    mohu_list.append(value[i])

            def get_key_list(tiaojian,value_tiaojian):
                key_list=[]
                num =0
                for i in tiaojian:
                    if value_tiaojian[num]:  # 判断字段取值是否为空
                        if i in jingque_list:
                            key_dict = {
                                "match": {
                                    i:{
                                        "query": value_tiaojian[num],
                                        "operator": "AND"
                                    }
                                }
                            }
                        else:
                            key_dict = {"match": {i:value_tiaojian[num]}}
                        key_list.append(key_dict)
                        num += 1
                return key_list
            must_key = get_key_list(must_list, value_must)
            should_key = get_key_list(should_list, value_should)
            must_not_key = get_key_list(must_not_list, value_must_not)
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
            base_url = 'http://127.0.0.1:8000/search/?field='+field+'&search_type=quick'
        else:
            base_url = 'http://127.0.0.1:8000/search/?q=' + key_words + '&search_type=' + type + '&index=' + key_index
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
            "index": key_index,
            "base_url": base_url,
            "q":key_words,
            "search_type":type
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


def facet_menu(request):     # 分面的目录
    facet_dic = {"gcc": ["保健功能", "适宜人群", "原料", "厂商"],
                 "jkkk": ["保健功能", "适宜人群", "原料", "厂商", "营养素名","国家"],
                 "rawmaterial": ["功能", "有效成分", "贮藏方法"],
                 "ingredients": ["功能"],
                 "nutrients": ["营养素名称", "功能", "典型缺乏病", "使用意见", "适用范围", "适宜人群"],
                 "other_ingredient": ["类别", "功能", "理化性质", "存在", "应用"],
                 "buying_guides": ["关键词"],
                 "regulations2": ["发布单位", "发布日期", "生效日期"]}
    if request.GET.get('index'):
        index = request.GET.get('index')
        print(index)
        menu = facet_dic[index]
    else:
        menu = facet_dic["gcc"]
    return JsonResponse(menu, safe=False)


# 用于调试
def base(request):
    return render(request, 'base.html')
