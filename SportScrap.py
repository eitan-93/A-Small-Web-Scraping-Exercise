import requests
import json
import time
from datetime import datetime
from bs4 import BeautifulSoup

def ScrapGames():
	url = 'https://www.oddschecker.com/football'
	# Connect to the URL
	response = requests.get(url)

	# Parse HTML and save to BeautifulSoup object
	soup = BeautifulSoup(response.text, 'html.parser')
	games = {}
	line_counter = 1 #variable to track what line you are on
	for line in soup.findAll('a'):  #'a' tags are for links
	    if line_counter >= 101: #code for text files starts at line 36
	        link = line['href']
	        if line.has_attr('data-event-name'):
				name = line['data-event-name']
				games[name] = "https://www.oddschecker.com"+link
				
	    line_counter +=1

	#Test:
	#for elem in games:
	#	print(elem + "                   " + games[elem])

	return games

#Helper function to fill BetTypes
def BetTypesArray(tag,attr,ratios,soup,betTypes):
	line_counter = 0
	for line in soup.findAll('tr'):
		if line.has_attr('data-bname'):
			betTypes.append(str(line['data-bname']))
			ratios[betTypes[line_counter]] = {}
			line_counter +=1

#Helper function to Build ratios dictionaries
def BuildRatios(odds,betTypes,ratios):
	line_counter = 0
	mod = len(odds)/len(betTypes)
	a = {str(betTypes[line_counter/mod]) : {}}
	
	for e in odds:
		a[str(betTypes[line_counter/mod ])].update(e)
			
		line_counter += 1
		if line_counter%mod == 0 :
			ratios.update(a)
			if line_counter!= len(odds) :
				a = {str(betTypes[line_counter/mod]) : {}}

def ScrapStats(games,g,stat):
	stats = {}
	name = str(g)
	url = str(games[g].replace("winner",stat))
	response = requests.get(url)
	if response.status_code != 200:# if the link is broken, skip it.
		return
	soup = BeautifulSoup(response.text, 'html.parser')
	betTypes = [];line_counter = 0; ratios = {}

	BetTypesArray('tr','data-bname',ratios,soup,betTypes)
	if len(ratios) == 0 : # if the link is broken, skip it.
		return
	odds = []
	ratios[betTypes[0]] = {}
	for line in soup.findAll('td'):
		if line.has_attr('data-bk') & line.has_attr('data-odig'):
			odds.append({str(line['data-bk']) : str(line['data-odig'])})
	
	BuildRatios(odds,betTypes,ratios)

	stats = {"URL" : games[g], name: {  "winner" : ratios} }
	#print(stats)
	#"URL" : games[g]
	return ratios

### using an old version of python, copied the function from the web.
def to_seconds(date):
    return time.mktime(date.timetuple())

def main():

	games = ScrapGames();

	#Anomaly detection : I chose the following approach: 
	# To look at the avarage of decimal odds in winner_ratios of each game (either one of the teams or draw) at a given time and to alert if the avarage changes in more than 10% in 30 seconds
	old_avg = 0
	alerts = []
	f = open("data.txt", "a")
	while 1 :
		time.sleep(2)
		sum_of_odds = 0
		num_of_odds = 0
		for g in games:
			name = str(g)
			winner_ratios = ScrapStats(games,g,"winner")
			bttc_ratios = ScrapStats(games,g,"both-teams-to-score")
			correct_score = ScrapStats(games,g,"correct-score")
			tgou_score = ScrapStats(games,g,"total-goals-over-under")
			stats = { str(g): {  "winner" : winner_ratios,"both-teams-to-score" : bttc_ratios, "correct-score" : correct_score,"total-goals-over-under" : tgou_score}}
			for key, value in winner_ratios.iteritems():
					for k, v in value:
						print(value[k+v])
						sum_of_odds += float(value[k+v])
						num_of_odds += 1
					avg = float(sum_of_odds)/float(num_of_odds)
					if old_avg == 0:
						old_avg = avg
					else :
						if (abs(old_avg*1.1 - avg) <= 0.005) | (abs(old_avg*0.9 - avg) <= 0.005):
							alerts.append(name)
		
		now = datetime.now()
		timestamp = to_seconds(now)
		json_object = json.dumps({'ts' : int(timestamp) , "data" : stats , "alerts" : alerts}, indent = 4)   
		f.write(json_object)
	f.close()


if __name__ == "__main__":
    main()