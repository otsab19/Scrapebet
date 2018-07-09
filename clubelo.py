#!/usr/bin/python
import os
import re
import sys
parent_dir = os.path.abspath(os.path.dirname('clubelo.py'))
vendor_dir = os.path.join(parent_dir, 'vendor')
sys.path.append(vendor_dir)  
from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from lxml import html
import multiprocessing
import json
import csv
import xml
import datetime
import requests
from bs4 import BeautifulSoup
from dateutil.rrule import rrule, DAILY
import errno
PATH = ''

mapp={  'Time':625,
        'HomeTeam':20,
        'AwayTeam':235,
        'Rank_Home_Team':145,
        'Rank_Away_Team':360,
        'HomeTeamELOpoints':180,
        'AwayTeamELOpoints':395,
        'Leg-1':472,
        'ELOpointsforgame':675,
        'ELOdiff':450,
        'PredAH0Home':[520,534],
        'PredAH0Draw':550,
        'PredAH0Away':[580,578],
        'MatchScore':615,
        'country_image_home':0,
        'country_image_away':215
        }
mapp_pred = {
            'Pred1':'PredAH0Home',
            'PredX':'PredAH0Draw',
            'Pred2':'PredAH0Away'
            }        

class FootballRatings():
    name = "football"

    def __init__(self, scrape_type, date, end_date):
        self.scrape_type = scrape_type
        self.date = date
        self.end_date = end_date 
        self.country_list = json.load(open('country_list.config'))

    def jsontoxml(self, obj, date=None):
    # create root of xml
        root = Element('xml')


        # copy of mapp remove country mappings
        mapp_dict=mapp.copy()
        del mapp_dict['country_image_away']
        del mapp_dict['country_image_home']
        root.set('version', '1.0')
        Matches = SubElement(root, 'Matches')
        Match = SubElement(Matches, 'Match')
        Source = SubElement(Match, 'Source')
        Source.text = 'Clubelo'
        Sport = SubElement(Match, 'Sport')
        Sport.text = 'Soccer'
        Date = SubElement(Match, 'Date')
        if date!=None:
            Date.text = date
        else:    
            Date.text = datetime.datetime.now().strftime('%Y-%m-%d')

        pred = [ob[i] for ob in obj for i in ob.keys() if i=='PredAH0Home' or i=='PredAH0Draw' or i=='PredAH0Away']
        if len(pred) == 3:
            for item in mapp_pred:
                mapp_dict[item] = mapp_dict.pop(mapp_pred[item])
                for i,ob in enumerate(obj):
                    try:
                        obj[i][item] = obj[i].pop(mapp_pred[item])
                    except:
                        pass    
        
        country_home = [ob[i] for ob in obj for i in ob.keys() if i=='country_image_home'][0]
        country_away = [ob[i] for ob in obj for i in ob.keys() if i=='country_image_away'][0]
        if country_away == country_home:
            Country = SubElement(Match, 'Country')
            country_full = self.country_list[country_home]
            Country.text = country_full    
        keys = [list(obj.keys()) for obj in obj]
        keys = [k[0] for k in keys]
        for outline in list(mapp_dict.keys()):
            if outline in keys:
                current_group = SubElement(Match, outline)
            for element in obj:
                try:
                    current_group.text = element[outline]
                except:
                    pass    
        soup = BeautifulSoup(tostring(root), 'xml')    
        return soup    

    def parse(self, response, date=None):
       
        result = []
        res = {}
        html_sel = html.fromstring(response.content)
        x = html_sel.xpath('//*[@class="blatt"]/svg//text//@x[not(ancestor::g)]')
        y = html_sel.xpath('//*[@class="blatt"]/svg//text//@y[not(ancestor::g)]')
        country_image_home = html_sel.xpath('//*[@class="blatt"]/svg/image/@x')
        country_image_away = html_sel.xpath('//*[@class="blatt"]/svg/image/@y')
        x=x+country_image_home
        y=y+country_image_away
        for i,j in zip(x,y):
            country=''
            try:
                list_item = [item for item in mapp if (mapp[item].__class__==list and (mapp[item][0]==int(i) or mapp[item][1]==int(i))) or mapp[item]==int(i)]
                xpath = '//*[@class="blatt"]/svg//text[@x='+i+'and @y='+j+']/text()'
                if i=='20' or i=='235':
                    #test for latin words
                    test_latin = html_sel.xpath(xpath)[0]
                    try:
                        test_latin.encode('latin1')
                        xx=test_latin
                    except:
                        xpath = '//*[@class="blatt"]/svg//text[@x='+i+'and @y='+j+']/parent::a/@*'
                        xx = html_sel.xpath(xpath)[0]
                        xx=xx.strip('/')
                        try:
                            t = xx.index('/')
                            xx = xx[t+1:]
                        except:
                            pass   
                        xx = re.sub('(?!^)([A-Z][a-z]+)', r' \1', xx)   
                elif i == '615':
                    xx = ''
                    for index in ['615','620','625']:
                        xpath = '//*[@class="blatt"]/svg//text[@x='+index+'and @y='+j+']/text()'
                        temp=html_sel.xpath(xpath)[0]
                        xx = xx+temp
                    xx = xx.replace('-', ':')    

                elif i == '625':
                    xpath = '//*[@class="blatt"]/svg//text[@x='+i+'and @y='+j+']/text()'
                    temp=html_sel.xpath(xpath)[0]
                    xx = temp.replace('h', ':')
                    xx = datetime.datetime.strptime(xx,'%H:%M').strftime('%I:%M %p')  

                elif i == '472':
                    xx=''
                    for index in ['472','476','480']:
                        xpath = '//*[@class="blatt"]/svg//text[@x='+index+'and @y='+j+']/text()'
                        temp=html_sel.xpath(xpath)[0]
                        xx = xx+temp
                #if image
                elif i=='215' or i=='0':
                    xpath = '//*[@class="blatt"]/svg/image[@x='+i+'and @y='+j+']/@*'
                    temp = html_sel.xpath(xpath)[0]
                    xx=temp[7:]
                    xx=xx[:-4]
                    if country == xx:
                        xx=country
                    else:    
                        country=xx

                else:
                    xx = html_sel.xpath(xpath)[0]

                if (int(j)-78) % 20 == 0:
                    j = str((int(j)+9))    

                if j in res:
                    res[str(j)].append({list_item[0]:xx})

                else:    
                    res[str(j)]= [{list_item[0]:xx}]
            except:
                pass

        # set date for folder
        if date==None:
            date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d') 
        else:
            date = (datetime.datetime.strptime(date, "%Y-%m-%d").date() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")        
        for result in res:
            try:      
                PATH = os.path.join(os.getcwd(),scrape_type,date)
                os.makedirs(PATH)
            except OSError as exc: 
                if exc.errno == errno.EEXIST and os.path.isdir(PATH):
                    pass
                else:
                    raise    
            xml = self.jsontoxml(res[result],date)
            # xml_str = json2xml(res[result])
            home_club = list(filter(lambda x:(x.get('HomeTeam')),res[result]))
            away_club = list(filter(lambda x:(x.get('AwayTeam')),res[result])) 
            filename = home_club[0]['HomeTeam'] + ' '+'vs'+' ' + away_club[0]['AwayTeam']+'.xml'
            filename = filename.replace('/',':')
            with open(os.path.join(PATH,filename), 'w', encoding='utf-8') as fl:
                try: 
                    print(filename+'\n')
                    fl.write(xml.decode('utf-16le'))

                except:
                    pass
            fl.close()

    def start_requests(self):  
        if self.date!=None:
            if self.end_date!=None:
                for dt in rrule(DAILY, dtstart=datetime.datetime.strptime(self.date, "%Y-%m-%d").date(), until=datetime.datetime.strptime(self.end_date, "%Y-%m-%d").date()):
                    response = requests.get('http://clubelo.com/'+dt.strftime("%Y-%m-%d")+'/'+self.scrape_type)
                    self.parse(response,dt.strftime("%Y-%m-%d"))
            else:
                response = requests.get('http://clubelo.com/'+self.date+'/'+self.scrape_type)
                self.parse(response,self.date)
                    
        else:    
            urls = [
                'http://clubelo.com/'+self.scrape_type
            ]

            for url in urls:
                response = requests.get(url)
                self.parse(response,None)

    


if __name__ == "__main__":
    
    scrape_type = input("Enter scrape type: ")
    date = input("Enter start date: ")
    end_date = input("Enter end date: ")
    if scrape_type == '':
        scrape_type = 'Results'
    scrape_type = scrape_type.capitalize()    
    if date=='':
        date = None

    if end_date=='': 
        end_date = None    
    try:
        PATH = os.path.join(os.getcwd(),scrape_type)
        os.makedirs(PATH)
    except OSError as exc: 
        if exc.errno == errno.EEXIST and os.path.isdir(PATH):
            pass
        else:
            raise    

    ratings = FootballRatings(scrape_type,date,end_date)
    ratings.start_requests()


