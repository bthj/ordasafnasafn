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
        filtered_results = self.filterSearch(self.filter_pattern, search_results)[0]
        if len(filtered_results) > 1:
            target_results = self.addTargetToLinks(filtered_results)
            returned_results = "<dl>" + self.addBaseUrlToLinks(self.base_url, target_results) + "</dl>"
        else:
            returned_results = "<h1>Ekkert fannst</h1>"
        self.response.out.write(returned_results)
        
class SearchIsmal(Search):
    base_url = "http://www.ordabanki.ismal.hi.is/"
    search_params = {
        "searchlanguage" : "EN", 
        "targetlanguage" : "", 
        "Submit" : "Leita"
    }
    filter_pattern = "Listi yfir niðurstöður byrjar.*?<td.*?>(.*?</table>).*Listi yfir niðurstöður endar"
    def get(self):
        Search.get(self)
        self.search_params["searchphrase"] = self.searchstring
        search_url = self.base_url + "search"
        search_results = self.postSearch(search_url, self.search_params).decode('iso-8859-1')
        filtered_results = self.filterSearch(self.filter_pattern, search_results)[0]
        self.response.out.write(filtered_results)

application = webapp.WSGIApplication([
                                      ('/hugtakasafn', SearchHugtakasafn), 
                                      ('/ismal', SearchIsmal)
                                      ], debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()