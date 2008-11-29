import os
import urllib
import re

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import urlfetch

class Search(webapp.RequestHandler):
    def get(self):
        self.searchstring = self.request.get('q')
    @classmethod
    def getSearch(cls, search_url, search_params):
        result = urlfetch.fetch(search_url + "?" + urllib.urlencode(search_params))
        if result.status_code == 200:
            return result.content
        else:
            return "<h1>Ekki tókst að framkvæma leitina</h1>" #TODO: throw error
    @classmethod
    def postSearch(cls, search_url, search_params):
        form_data = urllib.urlencode(search_params)
        result = urlfetch.fetch(url=search_url, 
                                payload=form_data, 
                                method=urlfetch.POST, 
                                headers={'Content-Type': 'application/x-www-form-urlencoded'})
        if result.status_code == 200:
            return result.content
        else:
            return "<h1>Ekki tókst að framkvæma leitina</h1>" #TODO: throw error        
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

class SearchHugtakasafn(Search):
    base_url = "http://hugtakasafn.utn.stjr.is/"
    search_params = {"tungumal" : "oll"}
    filter_pattern = "<dl>(.*)</dl>"
    def get(self):
        Search.get(self)
        self.search_params["leitarord"] = self.searchstring
        search_url = self.base_url + "leit-nidurstodur.adp"
        search_results = self.getSearch(search_url, self.search_params).decode('iso-8859-1')
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
        Search.get(self)
        html = ""
        search_url = self.base_url + "searchxml"
        search_params = {"searchphrase" : "*" +self.searchstring + "*"}
        for lang in ["IS", "EN"]:
            search_params["searchlanguage"] = lang
            search_results = self.getSearch(search_url, search_params).decode('iso-8859-1')
            html += self.renderHTML(search_results, self.searchstring)
        if len(html) > 0:
            html = self.addTargetToLinks(html)
        else:
            html = "<h1>Ekkert fannst</h1>"
        self.response.out.write(html)
    @classmethod
    def renderHTML(cls, xml, searchstring):
        # a proper xml parser might have been a good idea here but now i won't bothered mucking with one
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
            "DK" : "danska", "EN" : "enska", "SF" : "finnska", "FR" : "franska", "FO" : "færeyska", "GL" : "grænlenska", "NL" : "hollenska", "EI" : "írska", "IS" : "íslenska", "IT" : "ítalska", "JP" : "japanska", "LA" : "latína", "NOB" : "norskt bókmál", "NN" : "nýnorska", "PT" : "portúgalska", "RU" : "rússneska", "SM" : "samíska", "ES" : "spænska", "SV" : "sænska", "DE" : "þýska"
        }
        
        searchlanguage = searchlanguage_matcher.search(xml).group(1)
        dl = "<h2>leitarmál: " + lang_map[searchlanguage] + "</h2><dl>"
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
                    dd += " [" + lang_map[language] + "]</dd>"
            dl += dt + dd
            term_count += 1
        if term_count > 0:
            dl += "</dl>"
        else:
            dl = ""
        return dl

application = webapp.WSGIApplication([
                                      ('/hugtakasafn', SearchHugtakasafn), 
                                      ('/ismal', SearchIsmal)
                                      ], debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()