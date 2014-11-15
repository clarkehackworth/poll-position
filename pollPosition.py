from sys import argv
import requests
import json
from random import randrange
import eventlet
eventlet.monkey_patch()
import time
import re
import os.path

####################### global program options 

# initial bootstrap proxy 
tunnelProxy = '91.225.102.8:8080'

httptimeout = 30 # seconds

maxSleepBetweenVotes = 3 # minutes (randomized between 1 and this number of minutes)

# this should be customized fit the id of the item you want to boost the poll results
ourIDValue = ''

randomizeProxyUsage = True 

sleepAfterGoalReached = 16 # minutes

minimumTimeBetweenCheckingPollResults = 15 # minutes 

####################### /global program options

####################### poll specific functions for voting and getting vote results
################## These functions will need to be customized for your online poll

# sends HTTP vote over a given proxy
# you will need to modify the url, data, headers, failure message and get/post below before code will work for your poll

def sendVote(proxy):
        if type(proxy) == type(str()):
                proxy = {'ip': proxy.split(':')[0], 'port':proxy.split(':')[1] }
        success = False
        proxyDict = {
              "http"  : proxy['ip']+':'+proxy['port']
        }

	#### update url for your poll
        url = ''

	#### update data to be sent
        data = ''
	
	#### add any http headers that should go along with the request
        headers = {    }


	#### update failure message
	failureMessage = "alreadyvoted"

        try:

                print "trying "+proxy['ip']+":"+proxy['port']
                with eventlet.Timeout(httptimeout):
                        response = requests.post(url,data=data,headers=headers, proxies=proxyDict)
                #print response.status_code
                #print response.content

                #newer versions of requests lib may use response.text instead of response.content
                if failureMessage not in response.content.lower():
                        success = True
                        print "voted"
                else:
                        success = False
                        print "already voted"
                markProxyVoted(proxy)
        except requests.exceptions.RequestException as e:
                #print e
                success = False
        except eventlet.timeout.Timeout as e:
                success = False
        return success


# get votes from site, returns an array of { 'id': '<some item id value>', 'votes': '<number of votes for id> }
# you will need to update the url below before this will work for your poll
def getVotes():
        success = False
        proxy = tunnelProxy
        while not success:
                votes = []
                proxyDict = {
                      "http"  : proxy
                }

		###### update url that has the poll results
                url = ''

                try:
                        print 'getting votes'
                        with eventlet.Timeout(httptimeout):
                                response = requests.get(url, proxies=proxyDict)
                        regex = r"(votes_)([0-9A-Za-z]+)" \
                                r"('>)([0-9A-za-z\.]+)<"
                        found = re.findall(regex, response.content);
                        #print found
                        for item in found:
                                votesnumber = item[3]

				# for some reason when someone breaks 1000, they switch to shortened representation
				# such as "1K" or "1.1K", so this turns it back into an number
                                if 'K' in votesnumber:
                                        votesnumber = re.sub('[K]', '', votesnumber)
                                        votesarray = votesnumber.split('.')
                                        if len(votesarray) == 1:
                                                votesnumber = int(votesarray[0])*1000
                                        if len(votesarray) == 2:
                                                votesnumber = int(votesarray[0])*1000+int(votesarray[1])*100

                                votes.append({'id':item[1], 'votes': votesnumber})
                        success = True
                except requests.exceptions.RequestException as e:
                        print 'timeout getting votes'
                        proxy = getUsedProxy()
                except eventlet.timeout.Timeout as e:
                        print 'time out getting votes'
                        proxy = getUsedProxy()
        return votes
####################### /poll specific functions for voting and getting vote results



lastRankUpdated = 0;
currentRank = 0;

# uses getVotes to get the votes and calculate poll placement of our item in the poll
# positive numbers mean we are ahead, negative numbers mean we are behind 
def getRankingDifference():
	global lastRankUpdated
	global currentRank
	if (time.time() - lastRankUpdated) < (60*minimumTimeBetweenCheckingPollResults) :
		return currentRank
	voteList = getVotes()
	currentVotes = -1000
	difference = 1000
	for item in voteList:
		if item['id'] == ourIDValue:
			currentVotes = int(item['votes'])
			#print 'current votes'+str(currentVotes)
	if currentVotes > 0:
		for item in voteList:
			if item['id'] != ourIDValue:
				tmpdifference = currentVotes - int(item['votes'])
				#print currentVotes
				#print int(item['votes'])
				#print "tmp difference"+str(tmpdifference)
				if tmpdifference < difference:
					difference = tmpdifference
	else:
		print 'error cant get vote total'
		return -100
	currentRank = difference
	lastRankUpdated = time.time()
	print "rank is "+str(currentRank)
	return difference


############################## get proxy functions
#################### Each function gets a proxy list from a specific site
#################### Each funciton returns an array of { 'ip': '<ip address>','port':'<port>'}

def getFreeProxyListNet():
        proxies = []
	success = False
	proxy = tunnelProxy
	while not success:
	        proxyDict = {
        	      "http"  : proxy 
	        }
        	url = 'http://free-proxy-list.net/'

	        try:
        	        #print 'getting free proxy list dot net proxies'
                	with eventlet.Timeout(httptimeout):
                        	response = requests.get(url, proxies=proxyDict)
        	        regex = r"(<tr><td>)([0-9]+.[0-9]+.[0-9]+.[0-9]+)</td>" \
                	        r"(<td>)([0-9]+)</td>"
	                found = re.findall(regex, response.content);
        	        #print found
                	for item in found:
                        	proxies.append({'ip':item[1], 'port': item[3]})
			success=True
	        except requests.exceptions.RequestException as e:
        	        print 'timeout getting free proxy list dot net proxies'
			proxy = getUsedProxy()
	        except eventlet.timeout.Timeout as e:
        	        print 'time out getting free proxy list dot net proxies'
			proxy = getUsedProxy()
        return proxies


def getGatherProxyChina(): 
        proxies = []
        success = False
        proxy = tunnelProxy
        while not success:
                proxyDict = {
                      "http"  : proxy
                }
                url = 'http://www.gatherproxy.com/proxylist/country/?c=China'

                try:
                        #print 'getting gather proxy proxies'
                        with eventlet.Timeout(httptimeout):
                                response = requests.get(url, proxies=proxyDict)
                        regex = r"gp\.insertPrx\(\{[\"0-9a-zA-Z:\s,_]+,\"PROXY_IP\":\"([0-9]+.[0-9]+.[0-9]+.[0-9]+)\"[\"0-9a-zA-Z:\s,_]+\"PROXY_PORT\":\"([0-9]+)" 
                        found = re.findall(regex, response.content);
                        #print found
                        for item in found:
                                proxies.append({'ip':item[0], 'port': item[1]})
                        success=True
                except requests.exceptions.RequestException as e:
                        print 'timeout getting gather proxies'
                        proxy = getUsedProxy()
                except eventlet.timeout.Timeout as e:
                        print 'time out getting gather proxies'
                        proxy = getUsedProxy()
        return proxies

def getGatherProxyVen():
        proxies = []
        success = False
        proxy = tunnelProxy
        while not success:
                proxyDict = {
                      "http"  : proxy
                }
                url = 'http://www.gatherproxy.com/proxylist/country/?c=Venezuela'

                try:
                        #print 'getting gather proxy proxies'
                        with eventlet.Timeout(httptimeout):
                                response = requests.get(url, proxies=proxyDict)
                        regex = r"gp\.insertPrx\(\{[\"0-9a-zA-Z:\s,_]+,\"PROXY_IP\":\"([0-9]+.[0-9]+.[0-9]+.[0-9]+)\"[\"0-9a-zA-Z:\s,_]+\"PROXY_PORT\":\"([0-9]+)"
                        found = re.findall(regex, response.content);
                        #print found
                        for item in found:
                                proxies.append({'ip':item[0], 'port': item[1]})
                        success=True
                except requests.exceptions.RequestException as e:
                        print 'timeout getting gather proxies'
                        proxy = getUsedProxy()
                except eventlet.timeout.Timeout as e:
                        print 'time out getting gather proxies'
                        proxy = getUsedProxy()

        return proxies

def getLetUsHide():
        proxies = []
        success = False
        proxy = tunnelProxy
        while not success:
                proxyDict = {
                      "http"  : proxy
                }
                url = 'http://letushide.com/filter/all,all,all/list_of_free_proxy_servers'

                try:
                        #print 'getting let us hide proxies'
                        with eventlet.Timeout(httptimeout):
                                response = requests.get(url, proxies=proxyDict)
                        regex = r"<td id=\"link\"><a href=\"[0-9a-zA-Z\/:\.\s_-]+\">([0-9]+.[0-9]+.[0-9]+.[0-9]+)<\/a><\/td><td>([0-9]+)<\/td>" 
                        found = re.findall(regex, response.content);
                        #print found
                        for item in found:
                                proxies.append({'ip':item[0], 'port': item[1]})
                        success=True
                except requests.exceptions.RequestException as e:
                        print 'timeout getting let us hide proxies'
                        proxy = getUsedProxy()
                except eventlet.timeout.Timeout as e:
                        print 'time out getting let us hide proxies'
                        proxy = getUsedProxy()
        return proxies


def getLetUsHideChina():
        proxies = []
        success = False
        proxy = tunnelProxy
        while not success:
                proxyDict = {
                      "http"  : proxy
                }
                url = 'http://letushide.com/filter/all,all,cn/list_of_free_CN_China_proxy_servers'

                try:
                        #print 'getting let us hide china proxies'
                        with eventlet.Timeout(httptimeout):
                                response = requests.get(url, proxies=proxyDict)
                        regex = r"<td id=\"link\"><a href=\"[0-9a-zA-Z\/:\.\s_-]+\">([0-9]+.[0-9]+.[0-9]+.[0-9]+)<\/a><\/td><td>([0-9]+)<\/td>"
                        found = re.findall(regex, response.content);
                        #print found
                        for item in found:
                                proxies.append({'ip':item[0], 'port': item[1]})
                        success=True
                except requests.exceptions.RequestException as e:
                        print 'timeout getting let us hide china proxies'
                        proxy = getUsedProxy()
                except eventlet.timeout.Timeout as e:
                        print 'time out getting let us hide china proxies'
                        proxy = getUsedProxy()
        return proxies



def getHideMyAss():
	proxies = []
	success = False
	proxy = tunnelProxy
	while not success:
	        proxyDict = {
        	      "http"  : proxy 
	        }
        	url = 'http://proxylist.hidemyass.com/search-1292985'

		try:
        	        #print 'getting hide my ass proxies'
                	with eventlet.Timeout(httptimeout):
                        	response = requests.get(url, proxies=proxyDict)
        	        #print response.content 
			regex = r"(<td><span><style>(\n*[a-zA-Z0-9\.\{\}\:\s_\-]*\n)+<\/style>)|(([0-9a-zA-z\.\s]*)<(span|div) (class|style)=\"([0-9a-zA-z|:|\s_\-]+)\">([0-9a-zA-z\.]+)<\/(span|div)>(<(span|div)><\/(span|div)>)*([0-9a-zA-z\.\s]*))|(<\/span><\/td>\s*\n\s*<td>\s*\n\s*([0-9]+)\s*<\/td>)" 
	                found = re.findall(regex, response.content);
        	        #print found

			cssLookup = []
			proxyline=''
			proxynums=0
                	for item in found:
				display = False
	                #        proxies.append({'ip':item[1], 'port': item[3]})
				if item[1] != '':
					cssLookup.extend(item[1].split('\n'))
					#print "css lookup"
				if item[6] != '':
					#print item[6]
					if "display" not in item[6]:
						inlist = False
						for cssToken in cssLookup:
							#print "searching "+cssToken
							if "display" not in item[6] and item[6] in cssToken:
								if "inline" in cssToken:
									display = True
								inlist = True
						if inlist == False:
							display = True
					else:
						if "inline" in item[6]:
							#print "found display"
							display = True
					itemsev = re.sub('[\.\s]', '', item[7])
        				if display == True and itemsev != '':
						#print "Found "+itemsev
						proxyline=proxyline+itemsev
						if proxynums != 3:
							proxyline=proxyline+"."
						proxynums=proxynums+1
					itemthree = re.sub('[\.\s]', '', item[3])
					if itemthree != '':
						#print "Found "+itemthree
						proxyline=proxyline+itemthree
                        	                if proxynums != 3:
                                	                proxyline=proxyline+"."
	                                        proxynums=proxynums+1
					itemtwelve = re.sub('[\.\s]', '', item[12])
					if itemtwelve != '':
						#print "Found "+itemtwelve
						proxyline=proxyline+itemtwelve
                                        	if proxynums != 3:
	                                                proxyline=proxyline+"."
        	                                proxynums=proxynums+1
	
				if item[14] != '':
					#print "Port "+item[14]
					#proxyline=proxyline+":"+item[14]
					proxies.append({'ip':proxyline, 'port': item[14]})
					#print proxyline+":"+item[14]
					proxyline=""
					proxynums=0
				success = True
		except requests.exceptions.RequestException as e:
        	        print 'timeout getting hide my ass proxies'
			proxy = getUsedProxy()
	        except eventlet.timeout.Timeout as e:
        	        print 'time out getting hide my ass proxies'
			proxy = getUsedProxy()
        return proxies

############################## /get proxy functions


############################## Proxy store functionality

currentStore = 0
# proxyStore defines each proxy list.  To add more create get function above and add object to array below
proxyStore = [
		{
			'name': 'Free proxy list dot net',
			'updateFunc': getFreeProxyListNet,
			'lastUpdated': 0,
			'timeout': 10,
			'proxyList': []
		},
		{
			'name': 'hide my ass',
                        'updateFunc': getHideMyAss,
                        'lastUpdated': 0,
                        'timeout': 10,
                        'proxyList': []
		},

		{
                        'name': 'Free let us hide ',
                        'updateFunc': getLetUsHide,
                        'lastUpdated': 0,
                        'timeout': 10,
                        'proxyList': []
		},
		{
                        'name': 'Free let us hide china',
                        'updateFunc': getLetUsHideChina,
                        'lastUpdated': 0,
                        'timeout': 10,
                        'proxyList': []
                },
		{
                        'name': 'gather proxy ven',
                        'updateFunc': getGatherProxyVen,
                        'lastUpdated': 0,
                        'timeout': 10,
                        'proxyList': []
                },
		{
                        'name': 'gather proxy china',
                        'updateFunc': getGatherProxyChina,
                        'lastUpdated': 0,
                        'timeout': 10,
                        'proxyList': []
                }
             ]
# get proxy returns a non-used proxy object from a store.  returns { 'ip':'<ip address>','port':'<port>'}
def getProxy():
	global currentStore
	proxy = ''
	while proxy == '':
		proxyItem = proxyStore[currentStore]
		
		#refresh store list when cached list is outdated 
		if (time.time() - proxyItem['lastUpdated']) > proxyItem['timeout']*60:
			proxyItem['proxyList'] = proxyItem['updateFunc']()
			proxyItem['proxyList'].reverse() # reverse list so we can pop and get top proxy
			proxyItem['lastUpdated'] = time.time()
			print "Proxy "+proxyItem['name']+" updated recieved "+str(len(proxyItem['proxyList']))

		try:
			voted = True 
			while voted:

				proxyList = proxyItem['proxyList']

				print "proxy store "+str(currentStore)+" size "+str(len(proxyList))
				if len(proxyList) ==0:
					
					proxyItem['timeout'] = 0
					break

				if randomizeProxyUsage == True:	
					#code to retrieve randomly
					index = (randrange(len(proxyList)))	
					proxy = proxyList[index] 
					proxyList.remove(proxy) 
			 	else:
					#retrieve next proxy in list
					proxy = proxyItem['proxyList'].pop()	
				voted = proxyVoted(proxy)
		except IndexError:
			proxy=''
	
		currentStore = currentStore + 1
		if currentStore >= len(proxyStore):
			currentStore = 0	
	return proxy

############################# / Proxy store functionality


############################# Used proxy functionality
############ Used proxy functionality makes sure that proxies that have already been used are not retried
############ This is needed as refreshed proxy stores will often contain already tried ip addresses
############ This also doubles as an anonymous channel for getting vote count and proxy lists themselves

usedProxies = []
def markProxyVoted(proxy):
	usedProxies.append(proxy['ip']+':'+proxy['port'])
	with open("usedproxylist.txt", "a") as myfile:
    		myfile.write(proxy['ip']+':'+proxy['port']+"\n")

def loadUsedProxies():
	global usedProxies
	if len(usedProxies) == 0:
		if not os.path.isfile("usedproxylist.txt"):
			with open("usedproxylist.txt", "w") as text_file:
			    text_file.write(tunnelProxy)
                with open("usedproxylist.txt") as f:
                        usedProxies = f.read().splitlines()
		print "loaded "+str(len(usedProxies))+" used proxies"

def proxyVoted(proxy):
	global usedProxies
	#print "checking "
	#print proxy
	loadUsedProxies()
	if proxy['ip']+':'+proxy['port'] in usedProxies:
		#print True
		return True
	else:
		#print False
		return False

loadUsedProxies()
currentUsedProxy = len(usedProxies)-1 # start with latest proxy
def getUsedProxy():
	global currentUsedProxy
	global usedProxies
        loadUsedProxies()	
	if len(usedProxies) == 0:
		return tunnelProxy
	else:
		if currentUsedProxy < 0:
			currentUsedProxy = len(usedProxies)-1
		proxy = usedProxies[currentUsedProxy];
		currentUsedProxy = currentUsedProxy -1
		return proxy

##################### /Used proxy functionality

# returns how far ahead we want to stay
# reads from file so you can change on the fly.  defaults to 15
def getGoalRank():
	goalrank = 15
	if not os.path.isfile("goalrank.txt"):
	        with open("goalrank.txt", "w") as text_file:
         	       text_file.write("{0}".format(goalrank))
		print "Goal rank file created.  Check goalrank.txt to verify your goal position"
	with open("goalrank.txt") as f:
        	goalrank = int(f.read())
	return goalrank

def main():

	success = False 
	while 1:
		rank = getRankingDifference()
		while rank >= getGoalRank():
			print "sleeping "+str(sleepAfterGoalReached)
			time.sleep((sleepAfterGoalReached*60))	
        	       	rank = getRankingDifference()
		proxy = getProxy()
		success = sendVote(proxy)
		if success == True:
			sleep = (randrange(maxSleepBetweenVotes)+1)
			print "sleeping "+str(sleep) 
			time.sleep((sleep*60))

main()
