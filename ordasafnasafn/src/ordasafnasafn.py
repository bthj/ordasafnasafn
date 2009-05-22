import logging
import os
import urllib
import re

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import urlfetch

from BeautifulSoup import BeautifulSoup, Tag

class Search(webapp.RequestHandler):
    def getSearchString(self):
        return self.request.get('q')
    @classmethod
    def getSearch(cls, search_url, search_params):
        logging.error("fetching: " + search_url + "?" + search_params)
        result = urlfetch.fetch(search_url + "?" + search_params)
        if result.status_code == 200:
            return result.content
        else:
            return "<h1>Ekki t&oacute;st a&eth; framkv&aelig;ma leitina</h1>" #TODO: throw error
    @classmethod
    def postSearch(cls, search_url, search_params):
        result = urlfetch.fetch(url=search_url, 
                                payload=search_params, 
                                method=urlfetch.POST, 
                                headers={'Content-Type': 'application/x-www-form-urlencoded'})
        if result.status_code == 200:
            return result.content
        else:
            return "<h1>Ekki t&oacute;st a&eth; framkv&aelig;ma leitina</h1>" #TODO: throw error        
    @classmethod
    def filterSearch(cls, filter_pattern, result):
        matcher = re.compile(filter_pattern, re.I | re.S | re.M)
        return matcher.findall(result)
    @classmethod
    def addTargetToLinks(cls, string):
        return re.sub("(<a.*?)>", "\\1 target=\"_blank\">", string)
    @classmethod
    def addBaseUrlToLinks(cls, base_url, string):
        return re.sub("(href=[\'|\"])(.*?)([\'|\"])", "\\1"+base_url+"\\2\\3", string)
    
class SearchInput(Search):
    def get(self):
        self.response.out.write("""
          <html>
            <body>
              <form action="/ritmalaskra" method="get">
                <div><input type="text" value="" name="q"/></div>
                <div><input type="submit" value="Leita"></div>
              </form>
            </body>
          </html>""")    

class SearchHugtakasafn(Search):
    base_url = "http://hugtakasafn.utn.stjr.is/"
    search_params = {"tungumal" : "oll"}
    filter_pattern = "<dl>(.*)</dl>"
    def get(self):
        ### Search.get(self)
        self.search_params["leitarord"] = self.getSearchString()
        search_url = self.base_url + "leit-nidurstodur.adp"
        search_results = self.getSearch(search_url, urllib.urlencode(self.search_params)).decode('iso-8859-1')
        html = self.filterSearch(self.filter_pattern, search_results)[0]
        if len(html) > 1:
            html = self.addTargetToLinks(html)
            html = "<dl>" + self.addBaseUrlToLinks(self.base_url, html) + "</dl>"
        else:
            html = "<h1>Ekkert fannst</h1>"
        self.response.out.write(html)
        
class SearchIsmal(Search):
    base_url = "http://www.ordabanki.ismal.hi.is/"
    #filter_pattern = "Listi yfir niðurstöður byrjar.*?<td.*?>(.*?</table>).*Listi yfir niðurstöður endar"
    def get(self):
        ### Search.get(self)
        html = ""
        search_url = self.base_url + "searchxml"
        search_params = {"searchphrase" : "*" +self.getSearchString() + "*"}
        for lang in ["IS", "EN"]:
            search_params["searchlanguage"] = lang
            search_results = self.getSearch(search_url, urllib.urlencode(search_params)).decode('iso-8859-1')
            html += self.renderHTML(search_results, self.getSearchString())
            #html += search_results
        if len(html) > 0:
            html = self.addTargetToLinks(html)
        else:
            html = "<h1>Ekkert fannst</h1>"
        self.response.out.write(html)
    @classmethod
    def renderHTML(cls, xml, searchstring):
        # a proper xml parser might have been a good idea here but now i won't bothered mucking with one
        # TODO: might be better to use the Beautiful Soup library http://www.crummy.com/software/BeautifulSoup/
        term_matcher = re.compile("<term>(.*?)</term>", re.I | re.S | re.M)
        searchlanguage_matcher = re.compile("<searchlanguage>(.*?)</searchlanguage>", re.I | re.S | re.M)
        dictionary_matcher = re.compile("<dictionary.*?>(.*?)</dictionary>", re.I | re.S | re.M)
        name_matcher = re.compile("<name>(.*?)</name>", re.I | re.S | re.M)
        language_matcher = re.compile("<language>(.*?)</language>", re.I | re.S | re.M)
        synonym_matcher = re.compile("<synonym>(.*?)</synonym>", re.I | re.S | re.M)
        word_entry_matcher = re.compile("<word>(.*?</word>.*?)</word>", re.I | re.S | re.M)
        word_matcher = re.compile("<word>(.*?)</word>", re.I | re.S | re.M)
        url_matcher = re.compile("<url>(.*?)</url>", re.I | re.S | re.M)
        term_url_matcher = re.compile("dictionary.*?>.*?</dictionary>.*<url>.*http://herdubreid.rhi.hi.is:1026/wordbank/(.*?)</url>", re.I | re.S | re.M)
        searchstring_matcher = re.compile("("+searchstring+")", re.I)
        lang_map = {
            "DK" : "danska", "EN" : "enska", "SF" : "finnska", "FR" : "franska", "FO" : "f�reyska", "GL" : "gr�nlenska", "NL" : "hollenska", "EI" : "�rska", "IS" : "�slenska", "IT" : "�talska", "JP" : "japanska", "LA" : "lat�na", "NOB" : "norskt b�km�l", "NN" : "n�norska", "PT" : "port�galska", "RU" : "r�ssneska", "SM" : "sam�ska", "ES" : "sp�nska", "SV" : "s�nska", "DE" : "��ska"
        }
        
        searchlanguage = searchlanguage_matcher.search(xml).group(1)
        dl = "<h2>leitarm�l: " + lang_map[searchlanguage] + "</h2><dl>"
        term_count = 0
        for term in term_matcher.findall(xml):
            term_url = cls.base_url + term_url_matcher.search(term).group(1)
            dictionary = dictionary_matcher.search(term).group(1)
            dictionary_name = name_matcher.search(dictionary).group(1)
            if url_matcher.search(dictionary):
                dictionary_url = url_matcher.search(dictionary).group(1)
            dt = ""
            dd = ""
            for word in word_entry_matcher.findall(term):
                language = language_matcher.search(word).group(1)
                lang_word = word_matcher.search(word).group(1)
                if language == searchlanguage:
                    dt = "<dt><a href=\"" + term_url + "\">" + searchstring_matcher.sub("<strong>\\1</strong>", lang_word) + "</a>" 
                    if dictionary_url is not None:
                        dt += " [<a href=\"" + dictionary_url + "\">" + dictionary_name + "</a>]</dt>"
                    else:
                        dt += " [" + dictionary_name + "]</dt>"
                else:
                    dd += "<dd>" + lang_word
                    for i, synonym in enumerate(synonym_matcher.findall(word)):
                        if i == 0:
                            dd += " <em>samheiti:</em> "
                        if i > 0:
                            dd += ", "
                        dd += synonym
#                    dd += " [" + lang_map[language] + "]</dd>"
            dl += dt + dd
            term_count += 1
        if term_count > 0:
            dl += "</dl>"
        else:
            dl = ""
        return dl
    

class SearchTos(Search):
    base_url = "http://tos.sky.is"
    filter_pattern = """<span class="search_string">.*?<br /><br />(.*)</p>"""
    def get(self):
        search_url = self.base_url + "/tos/to/search/"
        search_params = "srch_string=*" + urllib.quote(self.getSearchString().encode('utf-8')) + "*"
        #search_params = {"srch_string" : "*" + self.getSearchString() + "*"}
        search_results = self.getSearch(search_url, search_params)
        html = self.renderHTML(search_results)
        self.response.out.write(html)
    @classmethod
    def renderHTML(cls, search_results):
        html = cls.filterSearch(cls.filter_pattern, search_results)[0]
        html = cls.addBaseUrlToLinks(cls.base_url, html)
        html = cls.addTargetToLinks(html)
        soup = BeautifulSoup(html)
        for div in soup.findAll('div'):
            li = Tag(soup, "li")
            li.insert(0, div.strong.a)
            div.replaceWith(li)
        ul = Tag(soup, "ul")
        ul.insert(0, soup)
        return str(ul)

class SearchHafro(Search):
    base_url = "http://www.hafro.is/ordabok/"
    search_params = {"op" : "search"}
    def get(self):
        self.search_params["qstr"] = "%" + self.getSearchString() + "%"
        search_results = self.postSearch(self.base_url, urllib.urlencode(self.search_params)).decode('iso-8859-1')
        html = self.renderHTML(search_results)
        self.response.out.write(html)
    @classmethod
    def renderHTML(cls, search_results):
        html = cls.addTargetToLinks(search_results)
        html = cls.addBaseUrlToLinks(cls.base_url, html)
        soup = BeautifulSoup(html)
        soup.dl.form.extract()
        return soup.body.renderContents()
    
class SearchMalfar(Search):
    # fors��a: http://www.arnastofnun.is/page/arnastofnun_gagnasafn_malfarsbankinn
    base_url = "http://www.ismal.hi.is/cgi-bin/malfar/leita"
    filter_pattern = """<br>.*?<hr>.*?<br>(.*)<br>.*?<br>.*?<hr>"""
    def get(self):
        search_params = {"ord" : self.getSearchString()}
        search_results = self.postSearch(self.base_url, urllib.urlencode(search_params)).decode('iso-8859-1')
        html = self.renderHTML(search_results)
        self.response.out.write(html)
    @classmethod
    def renderHTML(cls, search_results):
        html = """<p><a href="http://www.arnastofnun.is/page/arnastofnun_gagnasafn_malfarsbankinn" target="_blank">M&aacute;lfarsbanki &Iacute;slenskrar m&aacute;lst&ouml;&eth;var</a></p>"""
        filtered_search = cls.filterSearch(cls.filter_pattern, search_results)
        if len(filtered_search) < 1:
            html += "<p>Ekkert fannst</p>"
        else:
            html += filtered_search[0]
        return html
         
class SearchRitmalaskra(Search):
    base_url = "http://lexis.hi.is"
    filter_pattern_1 = """<td height="100" valign="middle">.*?<font color="#000000" face="Verdana, Arial, Helvetica, sans-serif" size="2">(.*)<tr>.*?<td height="40" valign="top" align="middle">(.*)&nbsp;&nbsp;<br>"""
    filter_pattern_2 = """(<table border="1" cellpadding="5">.*</table>)"""
    search_params = {"adg" : "leit"}
    def get(self):
        search_url = self.base_url + "/cgi-bin/ritmal/leitord.cgi"
        self.search_params["l"] = self.getSearchString()
        search_results = self.getSearch(search_url, urllib.urlencode(self.search_params)).decode('iso-8859-1')
        html = self.renderHTML(search_results)
        self.response.out.write(html)
    @classmethod
    def renderHTML(cls, search_results):
        html_heading = """<p><a href="http://www.arnastofnun.is/page/arnastofnun_gagnasafn_ritmal" target="_blank">Ritm&aacute;lssafn Or&eth;ab&oacute;kar H&aacute;sk&oacute;lans</a></p>"""
        filtered_search = cls.filterSearch(cls.filter_pattern_1, search_results)
        html  = ""
        if len(filtered_search) > 0:
            html = filtered_search[0][1] + "<br /><br />" + filtered_search[0][0] 
        else:
            filtered_search = cls.filterSearch(cls.filter_pattern_2, search_results)
            if len(filtered_search) > 0:
                html = filtered_search[0]
            else:
                html = "<p>Ekkert fannst</p>"
        html = cls.addTargetToLinks(html)
        html = cls.addBaseUrlToLinks(cls.base_url, html)
        html = html_heading + html
        return html

logging.getLogger().setLevel(logging.DEBUG)
application = webapp.WSGIApplication([
                                      ('/', SearchInput),
                                      ('/hugtakasafn', SearchHugtakasafn), 
                                      ('/ismal', SearchIsmal),
                                      ('/tos', SearchTos),
                                      ('/hafro', SearchHafro),
                                      ('/malfar', SearchMalfar),
                                      ('/ritmalaskra', SearchRitmalaskra)
                                      ], debug=True)


# http://tos.sky.is/tos/
# http://www.hafro.is/ordabok/
# http://www.arnastofnun.is/page/arnastofnun_gagnasafn_malfarsbankinn
# http://www.biblian.is/
# http://www.arnastofnun.is/page/arnastofnun_gagnasafn_ritmal


def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()