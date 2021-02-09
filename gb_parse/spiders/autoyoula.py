import scrapy
import pymongo


class AutoyoulaSpider(scrapy.Spider):
    name = 'autoyoula'
    allowed_domains = ['auto.youla.ru']
    start_urls = ['http://auto.youla.ru/']
    css_query =  {
        'brands': 'div.TransportMainFilters_brandsList__2tIkv div.ColumnItemList_container__5gTrc a.blackLink',
        'pagination': 'div.Paginator_block__2XAPy a.Paginator_button__u1e7D',
        'ads': 'div.SerpSnippet_titleWrapper__38bZM a.SerpSnippet_name__3F7Yu',
    }

    data_query = {
        'title': '.AdvertCard_advertTitle__1S1Ak::text',
        'price': '.AdvertCard_price__3dDCr::text',
        'description': '.AdvertCard_descriptionInner__KnuRi::text',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_client = pymongo.MongoClient()

    @staticmethod
    def gen_tasks(response, link_list, callback):
        for link in link_list:
            yield response.follow(link.attrib.get('href'), callback=callback)

    def parse(self, response):
        yield from self.gen_tasks(response, response.css(self.css_query['brands']), self.brand_parse)

    def brand_parse(self, response):
        yield from self.gen_tasks(response, response.css(self.css_query['pagination']), self.brand_parse)
        yield from self.gen_tasks(response, response.css(self.css_query['ads']), self.ads_parse)

    def ads_parse(self, response):
        data = {}
        for key, query in self.data_query.items():
            data[key] = response.css(query).get()
        data['user_id'] = response.xpath('//script').re_first('youlaId%22%2C%22([a-zA-Z|\d]+)%22%2C%22avatar')

        specs = {}
        for i in response.css('div.AdvertCard_specs__2FEHc div.AdvertSpecs_row__ljPcX'):
            if i.css('div.AdvertSpecs_label__2JHnS::text').get() not in ['Год выпуска', 'Кузов']:
                specs[i.css('div.AdvertSpecs_label__2JHnS::text').get()] = i.css(
                    'div.AdvertSpecs_data__xK2Qx::text').get()
            else:
                specs[i.css('div.AdvertSpecs_label__2JHnS::text').get()] = i.css('a::text').get()
        data['features'] = specs

        pics = []
        for i in response.css('div.PhotoGallery_photoWrapper__3m7yM source'):
            pics.append(i.xpath('@srcset').get())
        data['images'] = pics
        self.db_client['gb_parse'][self.name].insert_one(data)
