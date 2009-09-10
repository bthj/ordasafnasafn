import logging
import os
import urllib
import re
from google.appengine.ext.webapp import template

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import urlfetch

from BeautifulSoup import BeautifulSoup, Tag

class Search(webapp.RequestHandler):
    def getSearchString(self):
        return self.request.get('q')
    @classmethod
    def getSearch(cls, search_url, search_params):
        logging.info("fetching: " + search_url + "?" + search_params)
        result = urlfetch.fetch(url=search_url + "?" + search_params,
                                method=urlfetch.GET, 
                                deadline=20)
        if result.status_code == 200:
            return result.content
        else:
            return "<h1>Ekki t&oacute;st a&eth; framkv&aelig;ma leitina</h1>" #TODO: throw error
    @classmethod
    def postSearch(cls, search_url, search_params):
        result = urlfetch.fetch(url=search_url, 
                                payload=search_params, 
                                method=urlfetch.POST, 
                                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                                deadline=20)
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
    @classmethod
    def strengthenSearchstring(cls, searchstring, word):
        searchstring_matcher = re.compile("("+searchstring+")", re.I)
        return searchstring_matcher.sub("<strong>\\1</strong>", word)
    
class SearchInput(Search):
    def get(self):
        query = self.getSearchString()
        if query != '':
            valinOrdasofn = self.request.get("ordasofn", allow_multiple=True)
            html = '<hr />'
            for ordasafn in valinOrdasofn:
                classMethodExecution = ''.join([ordasafn, '.doSearch(\'', query, '\')'])
                try:
                    oneSearchResult = eval(classMethodExecution)
                except urlfetch.Error():
                    oneSearchResult = "<h2>Leitarni&eth;urst&ouml;&eth;ur skilu&eth;u s&eacute;r ekki</h2>"
                    continue
                html = ''.join([html, oneSearchResult, "<hr />" ])
        else:
            valinOrdasofn = []
            html = ''
        template_values = {
                           'query': query,
                           'valinOrdasofn': valinOrdasofn,
                           'searchResults': html}
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

class SearchHugtakasafn(Search):
    base_url = "http://hugtakasafn.utn.stjr.is/"
    search_params = {"tungumal" : "oll"}
    filter_pattern = "<dl>(.*)</dl>"
    html_heading = """<p><a href="http://hugtakasafn.utn.stjr.is/" target="_blank">Hugtakasafn &THORN;&yacute;&eth;ingami&eth;st&ouml;&eth;var utanr&iacute;kisr&aacute;&eth;uneytis</a></p>"""
    def get(self):
        html = self.doSearch( self.getSearchString() )
        self.response.out.write( html )
    @classmethod
    def doSearch(cls, searchString):
        search_params = {"leitarord" : searchString}
        search_params.update( cls.search_params )
        search_url = cls.base_url + "leit-nidurstodur.adp"
        search_results = cls.getSearch(search_url, urllib.urlencode(search_params)).decode('iso-8859-1')
        return cls.renderHTML(search_results)
    @classmethod
    def renderHTML(cls, search_results):
        html = cls.filterSearch(cls.filter_pattern, search_results)[0]
        if len(html) > 1:
            html = cls.addTargetToLinks(html)
            html = "<dl>" + cls.addBaseUrlToLinks(cls.base_url, html) + "</dl>"
        else:
            html = "<p>Ekkert fannst</p>"
        return ''.join([cls.html_heading, html])
            
class SearchIsmal(Search):
    base_url = "http://ordabanki.ismal.hi.is/"
    html_heading = """<p><a href="http://ordabanki.ismal.hi.is/" target="_blank">Or&eth;abanki &Iacute;slenskrar m&aacute;lst&ouml;&eth;var</a></p>"""
    #filter_pattern = "Listi yfir niðurstöður byrjar.*?<td.*?>(.*?</table>).*Listi yfir niðurstöður endar"
    def get(self):
        html = self.doSearch( self.getSearchString() )
        self.response.out.write(html)
    @classmethod
    def doSearch(cls, searchString):
        html = ""
        search_url = cls.base_url + "searchxml"
        search_params = {"searchphrase" : "*" + searchString.decode('utf-8') + "*"}
        for lang in ["IS", "EN"]:
            search_params["searchlanguage"] = lang
            search_results = cls.getSearch(search_url, urllib.urlencode(search_params)).decode('iso-8859-1')
            html += cls.renderHTML(search_results, searchString)
            #html += search_results
        if len(html) > 0:
            html = cls.addTargetToLinks(html)
        else:
            html = "<p>Ekkert fannst</p>"
        return ''.join([cls.html_heading, html])        
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
            "DK" : "danska", "EN" : "enska", "SF" : "finnska", "FR" : "franska", "FO" : "f&aelig;reyska", "GL" : "gr&aelig;nlenska", "NL" : "hollenska", "EI" : "&iacute;rska", "IS" : "&iacute;slenska", "IT" : "&iacute;talska", "JP" : "japanska", "LA" : "lat&iacute;na", "NOB" : "norskt b&oacute;km&aacute;l", "NN" : "n&yacute;norska", "PT" : "port&uacute;galska", "RU" : "r&uacute;ssneska", "SM" : "sam&iacute;ska", "ES" : "sp&aelig;nska", "SV" : "s&aelig;nska", "DE" : "&thorn;&yacute;ska"
        }
        
        searchlanguage = searchlanguage_matcher.search(xml).group(1)
        dl = "<h2>leitarm&aacute;l: " + lang_map[searchlanguage] + "</h2><dl>"
        term_count = 0
        for term in term_matcher.findall(xml):
            term_url = cls.base_url + term_url_matcher.search(term).group(1)
            dictionary = dictionary_matcher.search(term).group(1)
            dictionary_name = name_matcher.search(dictionary).group(1)
            if url_matcher.search(dictionary):
                dictionary_url = url_matcher.search(dictionary).group(1)
            else:
                dictionary_url = None
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
    html_heading = """<p><a href="http://tos.sky.is/" target="_blank">T&ouml;lvuor&eth;asafn</a></p>"""
    def get(self):
        html = self.doSearch( self.getSearchString() )
        self.response.out.write(html)
    @classmethod
    def doSearch(cls, searchString):
        search_url = cls.base_url + "/tos/to/search/"
        search_params = "srch_string=*" + urllib.quote(searchString) + "*"
        search_results = cls.getSearch(search_url, search_params)
        return cls.renderHTML(search_results).decode('utf-8')
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
        return ''.join([ cls.html_heading, str(ul) ])

class SearchHafro(Search):
    base_url = "http://www.hafro.is/ordabok/"
    search_params = {"op" : "search"}
    def get(self):
        html = self.doSearch( self.getSearchString() )
        self.response.out.write(html)
    @classmethod
    def doSearch(cls, searchString):
        search_params = {"qstr" : "%" + searchString + "%"}
        search_params.update( cls.search_params )
        search_results = cls.postSearch(cls.base_url, urllib.urlencode(search_params)).decode('iso-8859-1')
        return cls.renderHTML(search_results)        
    @classmethod
    def renderHTML(cls, search_results):
        html = cls.addTargetToLinks(search_results)
        html = cls.addBaseUrlToLinks(cls.base_url, html)
        soup = BeautifulSoup(html)
        soup.form.extract()
        return re.sub('<h1>(Or.*?k) (.*)</h1>', 
                      '''<p><a href="http://www.hafro.is/ordabok/" target="_blank">Sj&aacute;vard&yacute;raor&eth;ab&oacute;k</a>:  \\2</p>''', 
                      soup.body.renderContents() )
    
class SearchMalfar(Search):
    # fors��a: http://www.arnastofnun.is/page/arnastofnun_gagnasafn_malfarsbankinn
    base_url = "http://www.ismal.hi.is/cgi-bin/malfar/leita"
    filter_pattern = """<br>.*?<hr>.*?<br>(.*)<br>.*?<br>.*?<hr>"""
    def get(self):
        html = self.doSearch( self.getSearchString() )
        self.response.out.write(html)
    @classmethod
    def doSearch(cls, searchString):
        search_params = {"ord" : searchString}
        search_results = cls.postSearch(cls.base_url, urllib.urlencode(search_params)).decode('iso-8859-1')
        return cls.renderHTML(search_results)        
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
        html = self.doSearch( self.getSearchString() )
        self.response.out.write(html)
    @classmethod
    def doSearch(cls, searchString):
        search_url = cls.base_url + "/cgi-bin/ritmal/leitord.cgi"
        search_params = {"l" : searchString}
        search_params.update( cls.search_params )
        search_results = cls.getSearch(search_url, urllib.urlencode(search_params)).decode('iso-8859-1')
        return cls.renderHTML(search_results)        
    @classmethod
    def renderHTML(cls, search_results):
        html_heading = """<p><a href="http://www.arnastofnun.is/page/arnastofnun_gagnasafn_ritmal" target="_blank">Ritm&aacute;lssafn Or&eth;ab&oacute;kar H&aacute;sk&oacute;lans</a></p>"""
        filtered_search = cls.filterSearch(cls.filter_pattern_1, search_results)
        html  = ""
        if len(filtered_search) > 0:
            html = filtered_search[0][0] + "<br /><br />" + filtered_search[0][1] 
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
    
class SearchBin(Search):
    base_url = "http://bin.arnastofnun.is/"
    filter_pattern = """<div id="main">(.*)<center>.*?<form>"""
    search_params = {"ordmyndir" : "on"}
    def get(self):
        html = self.doSearch( self.getSearchString() )
        self.response.out.write(html)
    @classmethod
    def doSearch(cls, searchString):
        search_url = cls.base_url + "leit.php"
        search_params = {"q" : searchString + "%"}
        search_params.update( cls.search_params )
        search_results = cls.getSearch(search_url, urllib.urlencode(search_params)).decode('utf-8')
        return cls.renderHTML(search_results)
    @classmethod
    def renderHTML(cls, search_results):
        html_heading = """<p><a href="http://bin.arnastofnun.is/" target="_blank">Beygingarl&yacute;sing &iacute;slensks n&uacute;t&iacute;mam&aacute;ls</a></p>"""
        filtered_search = cls.filterSearch(cls.filter_pattern, search_results)
        html = filtered_search[0]
        html = re.sub(r'<h2>.*</h2>', '', html)
        html = cls.addTargetToLinks(html)
        html = cls.addBaseUrlToLinks(cls.base_url, html)
        return html_heading + html

#TODO:
# http://elias.rhi.hi.is/rimord/
# http://elias.rhi.hi.is/rimord/

logging.getLogger().setLevel(logging.DEBUG)
application = webapp.WSGIApplication([
                                      ('/', SearchInput),
                                      ('/hugtakasafn', SearchHugtakasafn), 
                                      ('/ismal', SearchIsmal),
                                      ('/tos', SearchTos),
                                      ('/hafro', SearchHafro),
                                      ('/malfar', SearchMalfar),
                                      ('/ritmalaskra', SearchRitmalaskra),
                                      ('/bin', SearchBin)
                                      ], debug=True)


def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()