import logging
import os
import urllib
import re
from google.appengine.ext.webapp import template

import webapp2
from webapp2_extras import i18n
#from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import urlfetch

from BeautifulSoup import BeautifulSoup, Tag
import json

#os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
#from google.appengine.dist import use_library
#use_library('django', '1.2')

class Index(webapp2.RequestHandler):
    def get(self):
        locale = self.request.GET.get('locale', 'en_US')
        i18n.get_i18n().set_locale(locale)

        #would be nicer to get a dict with translation keys from i18n if possible...
        template_values = {
            'locale' : locale,
            'title' : i18n.gettext('Wordbank search aggregator'),
            'Search' : i18n.gettext('Search'),
            'exact' : i18n.gettext('exact'),
            'searchLink' : i18n.gettext('searchLink'),
            'On' : i18n.gettext('On'),
            'Off' : i18n.gettext('Off'),
            'About' : i18n.gettext('About'),
            'titleAbout' : i18n.gettext('About the wordbank search aggregator'),
            'aboutContents1' : i18n.gettext('aboutContents1'),
            'aboutContents2' : i18n.gettext('aboutContents2'),
            'aboutContents3' : i18n.gettext('aboutContents3'),
            'aboutContents4' : i18n.gettext('aboutContents4'),
            
            'titleSettings' : i18n.gettext('titleSettings'),
            'legendInterfaceLanguage' : i18n.gettext('legendInterfaceLanguage'),
            'English' : i18n.gettext('English'),
            'Icelandic' : i18n.gettext('Icelandic'),
            'Continue' : i18n.gettext('Continue'),
            'titleCharges' : i18n.gettext('titleCharges'),
            'chargesHeading' : i18n.gettext('chargesHeading'),
            'chargesContents' : i18n.gettext('chargesContents')
        }
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

class Search(webapp2.RequestHandler):
    def getSearchString(self):
        return self.request.get('q')
    def getExact(self):
        return self.request.get('exact')
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
        exact = self.getExact()
        if query != '':
            valinOrdasofn = self.request.get("ordasofn", allow_multiple=True)
            html = '<hr />'
            for ordasafn in valinOrdasofn:
                classMethodExecution = ''.join([ordasafn, '.doSearch(\'', query, '\', \'' + exact + '\')'])
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
        path = os.path.join(os.path.dirname(__file__), 'search-input.html')
        self.response.out.write(template.render(path, template_values))
        
class SearchQuery(Search):
    def get(self):
        query = self.getSearchString()
        exact = self.getExact()
        ordasafn = self.request.get('ordasafn')
        if query != '' and ordasafn != '':
            html = eval( ''.join([ordasafn, '.doSearch(\'', query, '\', \'' + exact + '\')']) )
        else:
            html = ''
        self.response.headers['Content-Type'] = 'text/html'
        self.response.out.write( html )


class SearchHugtakasafn(Search):
    base_url = "http://hugtakasafn.utn.stjr.is/"
    search_params = {"tungumal" : "oll"}
    filter_pattern = "<dl>(.*)</dl>"
    def get(self):
        html = self.doSearch( self.getSearchString(), self.isExact() )
        self.response.out.write( html )
    @classmethod
    def doSearch(cls, searchString, exact):
        search_params = {"leitarord" : searchString.decode('utf-8').encode('iso-8859-1') }
        if exact == 'true':
            search_params["ordrett"] = "t"
        search_params.update( cls.search_params )
        search_url = cls.base_url + "leit-nidurstodur.adp"
        search_results = cls.getSearch(search_url, urllib.urlencode(search_params))
        jsonResults = [ cls.renderHTML(search_results) ]
        return json.dumps( jsonResults )
    @classmethod
    def renderHTML(cls, search_results):
        html = cls.filterSearch(cls.filter_pattern, search_results)[0]
        html = cls.addBaseUrlToLinks(cls.base_url, html)
        html = cls.addTargetToLinks(html)
        soup = BeautifulSoup(html)
        jsonResult = []
        for div in soup.findAll("div", {"class": "term"}):
            oneResult = {}
            oneResult["link"] = div.dt.a['href']
            oneResult["text"] = ''.join( unicode(oneElem) for oneElem in div.dt.a.contents )
            div.dt.a.extract()
            div.dt.insert( 0, oneResult["text"] )
            htmlResult = [ unicode( div.dt ) ]
            for dd in div.dt.findNextSiblings("dd"):
                htmlResult.append( unicode(dd) )
            oneResult["html"] = ''.join( htmlResult )
            jsonResult.append( oneResult )
        return jsonResult
            
class SearchIsmal(Search):
    base_url = "http://ordabanki.hi.is/wordbank/"
    lang_map = {
        "DK" : "danska", "EN" : "enska", "SF" : "finnska", "FR" : "franska", "FO" : "f&aelig;reyska", 
        "GL" : "gr&aelig;nlenska", "NL" : "hollenska", "EI" : "&iacute;rska", "IS" : "&iacute;slenska", 
        "IT" : "&iacute;talska", "JP" : "japanska", "LA" : "lat&iacute;na", "NOB" : "norskt b&oacute;km&aacute;l", 
        "NN" : "n&yacute;norska", "PT" : "port&uacute;galska", "RU" : "r&uacute;ssneska", "SM" : "sam&iacute;ska", 
        "ES" : "sp&aelig;nska", "SV" : "s&aelig;nska", "DE" : "&thorn;&yacute;ska", "GRISKA" : "Gr&iacute;ska"
    }
    def get(self):
        html = self.doSearch( self.getSearchString(), self.getExact() )
        self.response.out.write(html)
    @classmethod
    def doSearch(cls, searchString, exact):
        search_url = cls.base_url + "searchxml"
        search_params = {}
        if exact == 'true':
            search_params = {"searchphrase" : searchString.decode('utf-8').encode('iso-8859-1')}
        else:
            search_params = {"searchphrase" : "*" + searchString.decode('utf-8').encode('iso-8859-1') + "*"}
        jsonResults = []
        for lang in ["IS", "EN"]:
            search_params["searchlanguage"] = lang
            search_results = cls.getSearch(search_url, urllib.urlencode(search_params)).decode('iso-8859-1')
            jsonResults.append( cls.renderHTML(search_results, searchString) )
        jsonDump = json.dumps( jsonResults )
        return cls.addTargetToLinks( jsonDump )        
    @classmethod
    def renderHTML(cls, xml, searchstring):
        # a proper xml parser might have been a good idea here but now i won't bother mucking with one
        # TODO: might be better to use the Beautiful Soup library http://www.crummy.com/software/BeautifulSoup/
        term_matcher = re.compile("<term>(.*?)</term>", re.I | re.S | re.M)
        searchlanguage_matcher = re.compile("<searchlanguage>(.*?)</searchlanguage>", re.I | re.S | re.M)
        dictionary_matcher = re.compile("<dictionary.*?>(.*?)</dictionary>", re.I | re.S | re.M)
        name_matcher = re.compile("<name>(.*?)</name>", re.I | re.S | re.M)
        language_matcher = re.compile("<language>(.*?)</language>", re.I | re.S | re.M)
        synonym_matcher = re.compile("<synonym>(.*?)</synonym>", re.I | re.S | re.M)
        word_entry_matcher = re.compile("<word>(.*?</word>.*?)</word>", re.I | re.S | re.M)
        word_matcher = re.compile("<word>(.*?)</word>", re.I | re.S | re.M)
        term_url_matcher = re.compile("dictionary.*?>.*?</dictionary>.*<url>.*http://ordabanki.hi.is/wordbank/(.*?)</url>", re.I | re.S | re.M)
        searchstring_matcher = re.compile("("+searchstring+")", re.I)

        searchlanguage = searchlanguage_matcher.search(xml).group(1)
        jsonResult = []
        jsonResult.append( {"textlegend": cls.lang_map[searchlanguage]} )
        for term in term_matcher.findall(xml):
            term_url = cls.base_url + term_url_matcher.search(term).group(1)
            dictionary = dictionary_matcher.search(term).group(1)
            dictionary_name = name_matcher.search(dictionary).group(1)
            oneResult = {}
            oneResult["link"] = term_url
            dt = ""
            dd = ""
            for word in word_entry_matcher.findall(term):
                language = language_matcher.search(word).group(1)
                lang_word = word_matcher.search(word).group(1)
                if language == searchlanguage:
                    oneResult["text"] = lang_word
                    dt = ''.join(["<dt>", searchstring_matcher.sub("<strong>\\1</strong>", lang_word), " [",dictionary_name,"]</dt>"])
                else:
                    dd += "<dd>" + lang_word
                    for i, synonym in enumerate(synonym_matcher.findall(word)):
                        if i == 0:
                            dd += " <em>samheiti:</em> "
                        if i > 0:
                            dd += ", "
                        dd += synonym
                    dd += " [" + cls.lang_map[language] + "]</dd>"
            oneResult["html"] = ''.join([ dt, dd, ])
            jsonResult.append( oneResult )
        return jsonResult
    
class SearchTos(Search):
    base_url = "http://tos.sky.is"
    filter_pattern = """<span class="search_string">.*?<br /><br />(.*)</p>"""
    html_heading = """<p><a href="http://tos.sky.is/" target="_blank">T&ouml;lvuor&eth;asafn</a></p>"""
    def get(self):
        html = self.doSearch( self.getSearchString(), self.getExact() )
        self.response.out.write(html)
    @classmethod
    def doSearch(cls, searchString, exact):
        search_url = cls.base_url + "/tos/to/search/"
        if exact == 'true':
            search_params = "srch_string=" + urllib.quote(searchString)
        else:        
            search_params = "srch_string=*" + urllib.quote(searchString) + "*"
        search_results = cls.getSearch(search_url, search_params)
        jsonResults = [ cls.renderHTML(search_results, search_url, search_params) ]
        return json.dumps( jsonResults )
    
    @classmethod
    def renderHTML(cls, search_results, search_url, search_params):
        html = cls.filterSearch(cls.filter_pattern, search_results)[0]
        html = cls.addBaseUrlToLinks(cls.base_url, html)
        html = cls.addTargetToLinks(html)
        soup = BeautifulSoup(html)
        jsonResult = []
        for div in soup.findAll("div", { "class" : "word_title" }):
            oneResult = {}
            if div.strong is not None:
                if div.strong.a is not None:
                    oneResult["link"] = div.strong.a['href']
                    oneResult["text"] = ' '.join( unicode(oneElem) for oneElem in div.strong.a.contents )
                else:
                    oneResult["link"] = ''.join([search_url,'?',search_params])
                    oneResult["text"] = ' '.join( unicode(oneElem) for oneElem in div.strong.contents )
                jsonResult.append( oneResult )
        return jsonResult

class SearchHafro(Search):
    base_url = "http://www.hafro.is/ordabok/"
    search_params = {"op" : "search"}
    def get(self):
        html = self.doSearch( self.getSearchString(), self.getExact() )
        self.response.out.write(html)
    @classmethod
    def doSearch(cls, searchString, exact):
        if exact == 'true':
            search_params = {"qstr" : searchString.decode('utf-8').encode('iso-8859-1')}
        else:
            search_params = {"qstr" : "%" + searchString.decode('utf-8').encode('iso-8859-1') + "%"}
        search_params.update( cls.search_params )
        search_results = cls.postSearch(cls.base_url, urllib.urlencode(search_params))
        jsonResults = [ cls.renderHTML(search_results) ]
        return json.dumps( jsonResults )        
    @classmethod
    def renderHTML(cls, search_results):
        html = cls.addTargetToLinks(search_results)
        html = cls.addBaseUrlToLinks(cls.base_url, html)
        soup = BeautifulSoup(html)
        soup.form.extract()
        mainDl = soup.find("dl")
        jsonResult = []
        for h2 in mainDl.findAll("h2"):
            oneResult = {}
            oneResult["text"] = unicode(h2.contents[0])
            oneResultHtml = [ oneResult["text"], '<br />' ]
            oneResultHtml.append( h2.findNextSibling(text=True) )
            for dt in h2.findNext("dl").findAll("dt"):
                oneResultHtml.append( unicode(dt) )
                oneResultHtml.append( unicode(dt.findNextSibling("dd")) )
            oneResult["html"] = ''.join( oneResultHtml )
            jsonResult.append(oneResult)
        return jsonResult
        
class SearchMalfar(Search):
    # forsida: http://www.arnastofnun.is/page/arnastofnun_gagnasafn_malfarsbankinn
    base_url = "http://islex.lexis.hi.is/malfar/"
    def get(self):
        html = self.doSearch( self.getSearchString(), self.getExact() )
        self.response.out.write(html)
    @classmethod
    def doSearch(cls, searchString, exact):
        search_url = cls.base_url + "leit.pl"
        if exact == 'true':
            search_params = {"ord" : searchString.decode('utf-8').encode('iso-8859-1'), "leita" : "Leita"}
        else:
            search_params = {"ord" : "*"+searchString.decode('utf-8').encode('iso-8859-1')+"*", "leita" : "Leita"}
        search_results = cls.postSearch(search_url, urllib.urlencode(search_params))
        jsonResults = [ cls.renderHTML(search_results) ]
        return json.dumps( jsonResults )
    @classmethod
    def renderHTML(cls, search_results):
        html = cls.addTargetToLinks( search_results )
        html = cls.addBaseUrlToLinks(cls.base_url, html)
        soup = BeautifulSoup(html)
        jsonResult = []
        listi = soup.find("div", {"class": "listi"})
        if listi is not None:
            for a in listi.findAll("a"):
                oneResult = {}
                oneResult["link"] = a["href"]
                oneResult["text"] = ' '.join( unicode(oneElem) for oneElem in a.contents )
                jsonResult.append( oneResult )
        return jsonResult
         
class SearchRitmalaskra(Search):
    base_url = "http://lexis.hi.is"
    filter_pattern_1 = """<td height="100" valign="middle">.*?<font color="#000000" face="Verdana, Arial, Helvetica, sans-serif" size="2">(.*)<tr>.*?<td height="40" valign="top" align="middle">(.*)&nbsp;&nbsp;<br>"""
    filter_pattern_2 = """(<table border="1" cellpadding="5">.*</table>)"""
    search_params = {"adg" : "leit"}
    def get(self):
        html = self.doSearch( self.getSearchString(), self.getExact() )
        self.response.out.write(html)
    @classmethod
    def doSearch(cls, searchString, exact):
        search_url = cls.base_url + "/cgi-bin/ritmal/leitord.cgi"
        search_params = {"l" : searchString.decode('utf-8').encode('iso-8859-1')}
        search_params.update( cls.search_params )
        search_results = cls.getSearch(search_url, urllib.urlencode(search_params)).decode('iso-8859-1')
        jsonResults = [ cls.renderHTML(search_results) ]
        return json.dumps( jsonResults, indent=4 )        
    @classmethod
    def renderHTML(cls, search_results):
        filtered_search = cls.filterSearch(cls.filter_pattern_1, search_results)
        html  = ""
        if len(filtered_search) > 0:
            html = filtered_search[0][0] + "<br /><br />" + filtered_search[0][1] 
        else:
            filtered_search = cls.filterSearch(cls.filter_pattern_2, search_results)
            if len(filtered_search) > 0:
                html = filtered_search[0]
        jsonResult = []
        if html is not None:
            html = cls.addTargetToLinks(html)
            html = cls.addBaseUrlToLinks(cls.base_url, html)
            soup = BeautifulSoup(html)
            word = soup.find("strong")
            if word is not None:
                oneResult = {}
                oneResult["text"] = ' '.join( unicode(oneElem) for oneElem in word.contents )
                oneResult["html"] = html
                jsonResult.append(oneResult)
        return jsonResult
    
class SearchBin(Search):
    base_url = "http://bin.arnastofnun.is/"
    filter_pattern = """<div id="main">(.*)<center>.*?<form>"""
    search_params = {"ordmyndir" : "on"}
    def get(self):
        html = self.doSearch( self.getSearchString(), self.getExact() )
        self.response.out.write(html)
    @classmethod
    def doSearch(cls, searchString, exact):
        search_url = cls.base_url + "leit.php"
        if exact == 'true':
            search_params = {"q" : searchString}
        else:
            search_params = {"q" : searchString + "%"}
        search_params.update( cls.search_params )
        search_results = cls.getSearch(search_url, urllib.urlencode(search_params))
        jsonResults = [ cls.renderHTML(search_results, search_url, search_params) ]
        return json.dumps( jsonResults )
    @classmethod
    def renderHTML(cls, search_results, search_url, search_params):
        filtered_search = cls.filterSearch(cls.filter_pattern, search_results)
        html = filtered_search[0]
        html = re.sub(r'<h2>.*</h2>', '', html)
        html = cls.addTargetToLinks(html)
        html = cls.addBaseUrlToLinks(cls.base_url, html)
        soup = BeautifulSoup(html)
        jsonResult = []
        for li in soup.findAll("li"):
            oneResult = {}
            oneResult["link"] = li.strong.a["href"]
            oneResult["text"] = ' '.join( unicode(oneElem) for oneElem in li.strong.a.contents )
            oneResultHtml = [ oneResult["text"],' <small>' ]
            oneResultHtml.append( ''.join(unicode(oneElem) for oneElem in li.strong.findNextSiblings(text=True)) )
            oneResultHtml.append( '</small>' )
            oneResult["html"] = ''.join( oneResultHtml )
            jsonResult.append( oneResult )
        if len(jsonResult) < 1:
            resultHead = soup.find("span", {"style" : "font-size:1.25em; color:#0000FF;"})
            if resultHead is not None:  # we seem to have exactly one result and are already on the detail page
                oneResult = {}
                oneResult["link"] = ''.join([search_url,'?',urllib.urlencode(search_params)])
                oneResult["text"] = ''.join( unicode(oneElem) for oneElem in resultHead.strong.contents )
                oneResultHtml = [ oneResult["text"], ' <small>' ]
                oneResultHtml.append( ''.join(unicode(oneElem) for oneElem in resultHead.findNextSiblings(text=True)) )
                oneResultHtml.append( '</small>' )
                oneResult['html'] = ''.join( oneResultHtml )
                jsonResult.append( oneResult )                
        return jsonResult

#TODO:
# http://elias.rhi.hi.is/rimord/

logging.getLogger().setLevel(logging.DEBUG)
application = webapp2.WSGIApplication([
                                      ('/', Index),
                                      ('/search-input', SearchInput),
                                      ('/search', SearchQuery),
                                      ('/hugtakasafn', SearchHugtakasafn), 
                                      ('/ismal', SearchIsmal),
                                      ('/tos', SearchTos),
                                      ('/hafro', SearchHafro),
                                      ('/malfar', SearchMalfar),
                                      ('/ritmalaskra', SearchRitmalaskra),
                                      ('/bin', SearchBin)
                                      ], debug=True)

