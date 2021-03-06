# encoding=utf8
__author__ = 'wcong'
import ants


class DeadLoopTest(ants.Spider):
    name = "dead_loop_test"

    start_urls = [
        'http://www.baidu.com/s?wd=1'
    ]
    domain = 'http://www.baidu.com'

    def parse(self, response):
        nextpage = response.xpath('//div[@id="page"]/a[contains(text(),"' + '下一页'.decode("utf-8") + '")]/@href').extract()[0]
        yield ants.Request(self.domain + nextpage, callback=self.parse)

