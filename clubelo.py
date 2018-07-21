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
from yattag import indent
PATH = ''
# Rank
# Teamname
# Country
# ELOpoints

# The output file should be named:
# YYYY-MM-DD Clubelo ranking list

# YYYY-MM-DD=(date of scraping)
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
        'country_image_away':215,
        'vs':200,
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
        self.sel = None

    def extract_vs(self, value_y, root):
        
        xpath = '//*[@class="blatt"]/svg//text[@x=200 and @y='+str(value_y)+']/parent::a/@*'
        url = self.sel.xpath(xpath)[0]
        url = 'http://clubelo.com'+url
        res = requests.get(url)
        if res.status_code!=200:
            return root

        html_sel = html.fromstring(res.content)
        gd = html_sel.xpath('//svg[@height=34]/text/text()')
        exact_score = html_sel.xpath('//svg[@height=180]/text/text()')
        extra = html_sel.xpath('//svg[@height=240 and @width=540]/g/text/text()')[:9]
        odds_drift = html_sel.xpath('//svg[@height=240 and @width=540]//text[@fill="#72BBEF"]/text()')
        prob = html_sel.xpath('//svg[@height=22 and @width=640]//text/text()')
        season = html_sel.xpath('//*[@class="astblatt"]/div/p/text()')

        #season
        try:
            league = SubElement(root,'League')
            t = season[1].split(',')[0]
            league.text = t
            # seas = SubElement(root,'Season')
            # seas.text = season[0]
        except:
            pass
        #pred
        Pred1 = root.find('Pred1')
        if Pred1 !=None:
            Pred1.text = prob[2]
            PredX = root.find('PredX')
            PredX.text = prob[1]
            Pred2 = root.find('Pred2')
            Pred2.text = prob[0]
        else:
            Pred1 = SubElement(root, 'Pred1')
            Pred1.text = prob[2]
            PredX = SubElement(root, 'PredX')
            PredX.text = prob[1]
            Pred2 = SubElement(root, 'Pred2')
            Pred2.text = prob[0]
        # goal difference
        # g_d = SubElement(root, 'GoalDifference')
        gd_key = gd[0::2]
        gd_values = gd[1::2]
        try:
            for i in range(len(gd_key)):
                temp = gd_key[i].replace('>+5','6')
                temp = temp.replace('<-5','-6')
                temp = temp.replace('+','')
                temp = 'PredGA'+temp
                val = SubElement(root, temp)
                t = gd_values[i].replace('>','')
                t = t.replace('<','')
                val.text = t
        except:
            pass        

        # exact scores
        # e_s = SubElement(root, 'ExactScore')
        es_key = exact_score[0::2]
        es_values = exact_score[1::2]
        try:
            for i in range(len(es_key)):
                temp = 'PredCSFT'+es_key[i]
                val = SubElement(root, temp)
                t = es_values[i].replace('>','')
                t = t.replace('<','')
                val.text = t
        except:
            pass        
        # odds drift
        if odds_drift!=[]:
            Odds1 = SubElement(root,'Odds1')
            Odds1.text = odds_drift[0]
            OddsX = SubElement(root,'OddsX')
            OddsX.text = odds_drift[1]
            Odds2 = SubElement(root,'Odds2')
            Odds2.text = odds_drift[2]
        # extras tilt,elo percentage, HFA, excepted goals
        if extra!=[]:

            
            try:
                if re.search(r'[\d]+',extra[0]).group() != None:
                    hfa = SubElement(root, 'HomefieldleagueadvELO')
                    hfa.text = re.search(r'[\d]+',extra[0]).group()
            except:
                pass
            elo_per_home = SubElement(root, "PredAHOhome-Homefieldadv")
            elo_per_home.text = extra[1]

            elo_per_away = SubElement(root, "PredAHOaway-Homefieldadv")
            elo_per_away.text = extra[2]

            tilt_home = SubElement(root,"HometeamTilt")
            tilt_home.text = extra[3]

            tilt_away = SubElement(root, 'AwayteamTilt')
            tilt_away.text = extra[4]

            expected_goals_home = SubElement(root, 'Hometeamexpgoals')
            expected_goals_home.text = extra[6]

            expected_goals_away = SubElement(root, 'Awayteamexpgoals')
            expected_goals_away.text = extra[7]
        return root

    def extract_add(self,value_y,root):

        keys_col=['Played','Won','Drawn','Lost','Goals']
        keys_rows =['Total','Home','Away','Neutral','International','Domestic']
        for x in 20,235:
            xpath = '//*[@class="blatt"]/svg//text[@x='+str(x)+' and @y='+str(value_y)+']/parent::a/@*'
            url = self.sel.xpath(xpath)[0]
            url = 'http://clubelo.com'+url
            res = requests.get(url)
            html_sel = html.fromstring(res.content)

            
            data = [i for i in html_sel.xpath('/html/body/div/div[9]/table/td/text()')]
            le = int(len(data)/10)
            if x==20:
                    val = SubElement(root, 'HomeTeamStats') 
            else:
                val = SubElement(root, 'AwayTeamStats')
            for i in range(0,le,1):    
                  
                row = SubElement(val, keys_rows[i])                             
                for j in range(i*10,(i*10+5),1):
                         
                                               
                    el = SubElement(row, keys_col[j-10*i])
                    el.text = data[j]
        return root
        
    def jsontoxml(self, obj,value_y, date=None):
    # create root of xml

          
        root = Element('Matches')


        # copy of mapp remove country mappings
        mapp_dict=mapp.copy()
        del mapp_dict['country_image_away']
        del mapp_dict['country_image_home']
        del mapp_dict['vs']
        # root.set('version', '1.0')
        # Matches = SubElement(root, 'Matches')
        Match = SubElement(root, 'Match')
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

        ground = [ob[i] for ob in obj for i in ob.keys() if i=='vs'][0]   
        NeutralGround = SubElement(Match, 'NeutralGround') 
        if ground=='N':
            NeutralGround.text='Yes'
        else:
            NeutralGround.text  = 'No'    
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
        # for stats of team         
        # Matches = self.extract_add(value_y,Match)           
        Matches = self.extract_vs(value_y,Match) 

        soup = tostring(root)
        return soup    

    def parse_rank(self, response, date):
        try:      
            PATH = os.path.join(os.getcwd(),self.scrape_type,date)
            os.makedirs(PATH)
        except OSError as exc: 
            if exc.errno == errno.EEXIST and os.path.isdir(PATH):
                pass
            else:
                raise  
        res = response.content.decode('utf-8') 
        cr = csv.reader(res.splitlines(), delimiter=',')
        result_list = list(cr)
        filename = date+ ' Clubelo ranking list'+'.xml'
        root = Element('Rankings')
        Source = SubElement(root, 'Source')
        Source.text = 'Clubelo ELO ranking'
        Sport = SubElement(root, 'Sport')
        Sport.text = 'Soccer'

        for i,result in enumerate(result_list[1:]): 
            if result !=[]:
                Team = SubElement(root, 'Team')
                Rank = SubElement(Team, 'Rank')
                Rank.text = str(int(i+1))
                Teamname = SubElement(Team, 'Teamname')
                Teamname.text = result[1]
                Country = SubElement(Team, 'Country')
                Country.text = self.country_list[result[2]]
                ELOpoints = SubElement(Team, 'ELOpoints')
                ELOpoints.text = result[4]
        # soup = BeautifulSoup(tostring(root), 'xml')    
        soup = tostring(root)  
        with open(os.path.join(PATH,filename), 'w', encoding="utf-8") as fl:
            print(filename)
            fl.write(indent(soup.decode('utf-8')))



    def parse(self, response, date=None):
       
        result = []
        res = {}
        html_sel = html.fromstring(response.content)
        self.sel = html_sel
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
                    xx = datetime.datetime.strptime(xx,'%H:%M').strftime('%H:%M')  

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
        if self.scrape_type == "Results":
            if date==None:
                date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d') 
            else:
                date = (datetime.datetime.strptime(date, "%Y-%m-%d").date() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")        
        else:
            if date == None:
                date = datetime.datetime.now().strftime('%Y-%m-%d')
            else:
                pass  
        for result in res:
            try:      
                PATH = os.path.join(os.getcwd(),scrape_type,date)
                os.makedirs(PATH)
            except OSError as exc: 
                if exc.errno == errno.EEXIST and os.path.isdir(PATH):
                    pass
                else:
                    raise   
                     
            xml = self.jsontoxml(res[result],result,date)
            # xml_str = json2xml(res[result])
            home_club = list(filter(lambda x:(x.get('HomeTeam')),res[result]))
            away_club = list(filter(lambda x:(x.get('AwayTeam')),res[result])) 
            filename = home_club[0]['HomeTeam'] + ' '+'-'+' ' + away_club[0]['AwayTeam']+'.xml'
            filename = filename.replace('/',' ')
            with open(os.path.join(PATH,filename), 'w', encoding='utf-8') as fl:
                try: 
                    print(filename+'\n')
                    fl.write(indent(xml.decode('utf-8')))

                except:
                    pass
            fl.close()

    def start_requests(self):  
        if self.scrape_type == 'Results' or self.scrape_type == 'Fixtures':
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

        else:
            if self.date!=None:
                if self.end_date!=None:
                    for dt in rrule(DAILY, dtstart=datetime.datetime.strptime(self.date, "%Y-%m-%d").date(), until=datetime.datetime.strptime(self.end_date, "%Y-%m-%d").date()):
                        response = requests.get('http://api.clubelo.com/'+dt.strftime("%Y-%m-%d"))
                        self.parse_rank(response,dt.strftime("%Y-%m-%d"))
                else:
                    response = requests.get('http://api.clubelo.com/'+self.date)
                    self.parse_rank(response,self.date)
                        
            else:    
                urls = [
                    'http://api.clubelo.com/'+datetime.datetime.now().strftime('%Y-%m-%d')
                ]

                for url in urls:
                    response = requests.get(url)
                    self.parse_rank(response,datetime.datetime.now().strftime('%Y-%m-%d'))



if __name__ == "__main__":
    scraping_type=['Results','Fixtures','Rank']
    scrape_type = input("Enter scrape type: ")
    date = input("Enter start date: ")
    end_date = input("Enter end date: ")

    if scrape_type == '':
        scrape_type = 'Results'
    scrape_type = scrape_type.capitalize()   
    if scrape_type not in scraping_type:
        print("Type Results or Fixtures or Rank")
        sys.exit(0) 
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


