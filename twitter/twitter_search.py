#!/usr/bin/env python

# Twitter Api Exercise
# Author: Nancy Yang
# Email : maxbearwiz@gmail.com
# Date  : July 3, 2014

from urllib import urlencode
import urllib2 
from time import time
import datetime
from random import getrandbits
import base64
import hmac
import hashlib
import sys
import socket
import select
import time
import json
import codecs
import os
import getopt
import logging
import threading

# 
CONSUMER_KEY = ""
CONSUMER_SECRET = ""
OAUTH_TOKEN = ""
OAUTH_TOKEN_SECRET = ""

CRLF = b'\r\n'

def encode_params(base_url, method, params):
   print base_url
   params = params.copy()
   params['oauth_token'] = OAUTH_TOKEN
   params['oauth_consumer_key'] = CONSUMER_KEY
   params['oauth_signature_method'] = 'HMAC-SHA1'
   params['oauth_version'] = '1.0'
   params['oauth_timestamp'] = str(int(time.time()))
   params['oauth_nonce'] = str(getrandbits(64))

   enc_params = urlencode(sorted(params.items())).replace("+", "%20")

   key = CONSUMER_SECRET + "&" + urllib2.quote(OAUTH_TOKEN_SECRET, safe='~')

   x = []
   for s in [method.upper(), base_url, enc_params]:
      x.append(urllib2.quote(s, safe='~'))
   text = '&'.join(x)

   signature = (base64.b64encode(hmac.new(
      key.encode('ascii'),
      text.encode('ascii'),
      hashlib.sha1).digest()))

   return enc_params + "&" + "oauth_signature=" + urllib2.quote(signature,
	 safe='~')

def test_search_tweets(keyword, since=None, max_id=None, geocode=None):
   uriBase = "https://api.twitter.com/1.1/search/tweets.json"
   kword = keyword if keyword!=None else ""
   params = {"q": kword}
   if geocode!=None:
      params["geocode"] = geocode
   if since !=None:
      params = {"q": "%s since:%s" % (keyword, "2013-1-1")}
   if max_id !=None: 
      params["max_id"] = max_id

   enc = encode_params(uriBase, 'GET', params)
   url = uriBase + "?" + enc 

   req = urllib2.Request(url)
   try: 
      handle = urllib2.urlopen(req)
      for s in ['x-rate-limit-limit',
 	  'x-rate-limit-remaining', 'x-rate-limit-reset']:
        if s=='x-rate-limit-reset':
 	  print "%-25s: %s" % (s, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(handle.headers[s]))))
        else:
 	  print "%-25s: %s" % (s, handle.headers[s])

   except urllib2.HTTPError as e:
     print "# http exception"
     print e
     print "#"
     raise

   if handle.getcode() != 200:
      return 

   data = handle.read()
   json_data = json.loads(data)
   if not ('statuses' in json_data):
      print "no status returend for keyword: %s" % keyword
      return 
   if keyword != None:
     fname = '%s.txt' % keyword
   elif geocode != None:
     fname = '%s.txt' % 'geocode'
   f = open(fname, 'a')
   f.write("Query generated at : %s\n" % datetime.datetime.now().strftime("%Y%m%d %H:%M:%S"))
   for stat in json_data['statuses']:
      f.write("%s %s %-15s %s\n" % (stat['id'], 
	       stat['created_at'],
	       stat['user']['name'].encode('ascii', 'ignore')[:10],
	       stat['text'].encode('ascii','ignore')[:50]))
   f.close()

   f = open("stats.txt", 'a')
   f.write("Query generated at : %s\n" % datetime.datetime.now().strftime("%Y%m%d %H:%M:%S"))
   f.write("%-15s: %s\n" % ("keyword", keyword))
   meta =  json_data['search_metadata']
   for s in ['max_id', 'since_id', 'count', 'completed_in']:
	 if s=='completed_in':
	    f.write("%-15s: %0.3f\n" % (s, float(meta[s])))
         else:
	    f.write("%-15s: %d\n" % (s, int(meta[s])))
   f.close()
   search_time = float(meta['completed_in'])

   try:
     max_id = int(json_data['statuses'][int(meta['count'])-1]['id'])
   except Exception as e:
      print "#"
      print e
      print "#"
      max_id = None
   return (max_id, search_time)

class Twitter(threading.Thread):
   def __init__(self, filename, keyword):
      threading.Thread.__init__(self)
      self.filename = filename
      self.keyword = keyword
   def run(self):
      test_search_tweets(self.keyword)

if __name__== "__main__":
   logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
   logging.basicConfig(format='%(asctime)s %(message)s')
   
   f = open("stats.txt", 'w')
   f.write("twitter search stats log, test start at: %s\n" % datetime.datetime.now().strftime("%Y%m%d %H:%M:%S"))
   f.close()

   keyword = None
   geocode = None
   fname  = None
   try:
      opts, args = getopt.getopt(sys.argv[1:], 'k:m:g:')
   except getopt.GetoptError:
      print 'usage: twitter_search.py -t <search keyword> | -g <geocode> | -m'
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print 'usage: stream.py -t <search keyword> | -m'
	 sys.exit(2)
      if opt in ('-g'):
	 geocode = arg
	 fname = "%s.txt" % 'geocode'
      if opt in ('-k'):
	 keyword = arg
         fname = "%s.txt" % keyword
      if opt in ('-m'):
        thread1 = Twitter("worldcup.txt", "worldcup")
        thread2 = Twitter("france.txt", "france")
	thread1.start()
	thread2.start()

   if fname==None:
      print 'usage: twitter_search.py -t <search keyword> | -g <geocode> | -m'
      sys.exit(2)

   f = open(fname, 'w')
   f.write("twitter search result log, test start at: %s\n" % 
         datetime.datetime.now().strftime("%Y%m%d %H:%M:%S"))
   f.close()
   (max_id, search_time) = test_search_tweets(keyword, None, None, geocode)
   if max_id != None:
     max_id = max_id -1
   avg_search_time = search_time
   while True:
      try:
         (max_id, search_time) = test_search_tweets(keyword, None, max_id, geocode)
         if max_id!=None:
           max_id -= 1
         avg_search_time = (avg_search_time + search_time) / 2
      except Exception as e:
         print e
         raise
      except KeyboardInterrupt:
         print "Test finished, please check search result file: %s, search statistics : %s" % (fname, "stats.txt")
         break

   f = open(fname, 'a')
   f.write("twitter search result log, test finish at: %s\n" %
         datetime.datetime.now().strftime("%Y%m%d %H:%M:%S"))
   f.close()

   f = open("stats.txt", 'a')
   f.write("search keyword : %s, average search time: %0.3f\n" % (keyword, avg_search_time))
   f.write("twitter search stats log, test finish at: %s\n" % datetime.datetime.now().strftime("%Y%m%d %H:%M:%S"))
   f.close()
