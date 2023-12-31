import re
import chardet
import requests
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup


class CxExtractor:
    """cx-extractor implemented in Python"""

    __text = []
    # __threshold = 186
    __indexDistribution = []
    # __blocksWidth = 3

    def __init__(self, threshold=86, blocksWidth=4):
        self.__blocksWidth = blocksWidth
        self.__threshold = threshold

    def dynamics_getText(self, content):
        result = self.getText(content)
        while result == '':
            self.__threshold -= 20
            result = self.getText(content)

            if self.__threshold <= 80:
                break
        return result

    def getText(self, content):
        if self.__text:
            self.__text = []
        lines = content.split('\n')
        for i in range(len(lines)):
            # lines[i] = lines[i].replace("\\n", "")
            # if lines[i] == ' ' or lines[i] == '\n':
            #     lines[i] = ''
            lines[i] = lines[i].strip()

        self.__indexDistribution.clear()
        for i in range(0, len(lines) - self.__blocksWidth):
            wordsNum = 0
            for j in range(i, i + self.__blocksWidth):
                lines[j] = lines[j].replace("\\s", "")
                wordsNum += len(lines[j])
            self.__indexDistribution.append(wordsNum)

        start = -1
        end = -1
        boolstart = False
        boolend = False
        for i in range(len(self.__indexDistribution) - 1):
            if self.__indexDistribution[i] > self.__threshold and (not boolstart):
                if self.__indexDistribution[i + 1] != 0 or self.__indexDistribution[i + 2] != 0 or self.__indexDistribution[i + 3] != 0:
                    boolstart = True
                    start = i
                    continue
            if boolstart:
                if self.__indexDistribution[i] == 0 or self.__indexDistribution[i + 1] == 0:
                    end = i
                    boolend = True
            tmp = []
            if boolend:
                for ii in range(start, end + 1):
                    if len(lines[ii]) < 5:
                        continue
                    tmp.append(lines[ii] + "\n")
                str = "".join(list(tmp))
                if "Copyright" in str or "版权所有" in str:
                    continue
                self.__text.append(str)
                boolstart = boolend = False
        result = "".join(list(self.__text))
        return result

    def replaceCharEntity(self, htmlstr):
        CHAR_ENTITIES = {'nbsp': ' ', '160': ' ',
                         'lt': '<', '60': '<',
                         'gt': '>', '62': '>',
                         'amp': '&', '38': '&',
                         'quot': '"', '34': '"', }
        re_charEntity = re.compile(r'&#?(?P<name>\w+);')
        sz = re_charEntity.search(htmlstr)
        while sz:
            entity = sz.group()
            key = sz.group('name')
            try:
                htmlstr = re_charEntity.sub(CHAR_ENTITIES[key], htmlstr, 1)
                sz = re_charEntity.search(htmlstr)
            except KeyError:
                # 以空串代替
                htmlstr = re_charEntity.sub('', htmlstr, 1)
                sz = re_charEntity.search(htmlstr)
        return htmlstr

    def getHtml(self, url):

        response = requests.get(url)
        encode_info = chardet.detect(response.content)
        response.encoding = encode_info['encoding']
        return response.text

    def readHtml(self, path, coding):
        page = open(path, encoding=coding)
        lines = page.readlines()
        s = ''
        for line in lines:
            s += line
        page.close()
        return s

    def filter_tags(self, htmlstr):
        re_nav = re.compile('<nav.+</nav>')
        re_cdata = re.compile('//<!\[CDATA\[.*//\]\]>', re.DOTALL)
        re_script = re.compile(
            '<\s*script[^>]*>.*?<\s*/\s*script\s*>', re.DOTALL | re.I)
        re_style = re.compile(
            '<\s*style[^>]*>.*?<\s*/\s*style\s*>', re.DOTALL | re.I)
        re_textarea = re.compile(
            '<\s*textarea[^>]*>.*?<\s*/\s*textarea\s*>', re.DOTALL | re.I)
        re_br = re.compile('<br\s*?/?>')
        re_h = re.compile('</?\w+.*?>', re.DOTALL)
        re_comment = re.compile('<!--.*?-->', re.DOTALL)
        re_space = re.compile(' +')
        s = re_cdata.sub('', htmlstr)
        s = re_nav.sub('', s)
        s = re_script.sub('', s)
        s = re_style.sub('', s)
        s = re_textarea.sub('', s)
        s = re_br.sub('', s)
        s = re_h.sub('', s)
        s = re_comment.sub('', s)
        s = re.sub('\\t', '', s)
        # s = re.sub(' ', '', s)
        s = re_space.sub(' ', s)
        s = self.replaceCharEntity(s)
        return s


class Crawler:
    def __init__(self):
        self.headers = {
            'Accept': 'text/javascript, application/javascript, application/ecmascript, application/x-ecmascript, */*; q=0.01Accept-Encoding: gzip, deflate,Accept-Language: zh-CN,zh;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36'
        }

    def __remove_extra_spaces(self, text):
        regex = re.compile(r'\s+')
        return regex.sub(' ', text.strip())

    def SearchResultCrawl(self, query):
        results = []
        url = 'http://www.sogou.com/web?query=' + urllib.parse.quote(query.encode('utf8')) + '&num=10&page=1&ie=utf8'

        try:
            request = urllib.request.Request(url=url, headers=self.headers)
            webpage = urllib.request.urlopen(request, timeout=20).read()
            soup = BeautifulSoup(webpage, 'html.parser')

            result_items = soup.find_all('div', class_='vrwrap')

            rank = 0
            for item in result_items:
                title_element = item.find('h3')
                if title_element:
                    # title
                    title = title_element.text.replace('\n', ' ').strip()

                    # url
                    if item.find('a', class_='special-title'):
                        url = item.find('a', class_='special-title')['href']
                    else:
                        url = title_element.find('a')['href']

                    # abstract
                    old_abstract = ''
                    if item.find('p', class_='star-wiki'):
                        old_abstract = item.find('p', class_='star-wiki').text.replace('\n', ' ').strip()
                    elif item.find('div', class_='fz-mid space-txt'):
                        old_abstract = item.find('div', class_='fz-mid space-txt').text.replace('\n', ' ').strip()
                    abstract = self.__remove_extra_spaces(old_abstract)

                    results.append({
                        'title': title,
                        'url': url,
                        'abstract': abstract,
                        'rank': rank,
                    })
                    rank += 1

                else:
                    pass
            return results

        except Exception as e:
            print(e)
            return

    def UrlCrawl(self, url):
        cx = CxExtractor(threshold=200)
        try:
            request = urllib.request.Request(url=url, headers=self.headers)
            html = urllib.request.urlopen(request, timeout=20).read()
            soup = BeautifulSoup(html, 'html.parser')

            result = chardet.detect(html)

            encoding = result['encoding']
            encoding = 'utf-8' if 'Windows' in encoding else encoding
            html_decoded = html.decode(encoding, 'ignore')
            content = cx.filter_tags(html_decoded)

            # 行块分布函数的通用网页正文抽取算法
            s = cx.dynamics_getText(content)

            if s.strip() == '':
                meta_tag = soup.find('meta', attrs={'name': 'description'})
                if meta_tag:
                    s = meta_tag.get('content')

            return s

        except Exception as e:
            print(e)
            return


if __name__ == "__main__":
    cx = Crawler()

    print(cx.UrlCrawl('https://wenku.baidu.com/aggs/f5837c1252d380eb62946dec.html?fr=sogou'))
