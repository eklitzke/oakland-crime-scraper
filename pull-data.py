#!/usr/bin/env python

from xml.dom import minidom
import urllib
import time
import datetime
from sqlite3 import dbapi2 as sqlite

def check_dom_format(crime_dom):
	'''Ensure that the dom has the format that we expect'''
	assert len(crime_dom.childNodes) == 1
	feed = crime_dom.firstChild
	assert feed.localName == 'feed'

def get_dom():
	feed_location = 'http://oakland.crimespotting.org/crime-data'
	feed_str = urllib.urlopen(feed_location).read()
	return minidom.parseString(feed_str)

def get_single_node_value(node):
	return node.firstChild.nodeValue

def handle_link_node(node):
	return node.attributes['href'].nodeValue

def handle_category_node(node):
	return node.attributes['term'].nodeValue

def handle_georss_point_node(node):
	return get_single_node_value(node).split(' ')

def convert_uni_dict_to_str_dict(d):
	for k in d.iterkeys():
		if isinstance(k, unicode):
			d[str(k)] = d.pop(k)
	for k, v in d.iteritems():
		if isinstance(v, unicode):
			d[k] = str(v)

def convert_weird_time_to_unix_time(weird_time):
	'''Convert their weird time format to unix time'''
	try:
		time.strptime(weird_time, '%Y-%m-%dT%H:%M:%S')
	except ValueError, v:
		last_part = v.message.split(' ')[-1]
		t = datetime.datetime.strptime(weird_time[:-len(last_part)], '%Y-%m-%dT%H:%M:%S')
		delta_hours, delta_minutes = map(int, last_part.split(':'))
		if delta_hours < 0:
			delta_minutes *= -1
		t = t + datetime.timedelta(hours=delta_hours, minutes=delta_minutes)
		return int(t.strftime('%s'))
	assert False

#if __name__ == '__main__':
crime_dom = get_dom()
fetch_time = int(time.time())
check_dom_format(crime_dom)

# Get the entries, which are the only things we're really interested in
entries = [c for c in crime_dom.firstChild.childNodes if c.localName == u'entry']
assert entries

entry_list = []

for entry in entries:
	nodes = [n for n in entry.childNodes if n.nodeType == minidom.Node.ELEMENT_NODE]
	d = {'time_fetched': fetch_time}
	for node in nodes:
		if node.nodeName in ('title', 'id', 'updated'):
			d[node.nodeName] = get_single_node_value(node)
		elif node.nodeName == 'link':
			d['cs_url'] = handle_link_node(node)
		elif node.nodeName == 'category':
			d['cs_category'] = handle_category_node(node)
		elif node.nodeName == 'georss:point':
			lat, long = handle_georss_point_node(node)
			d['latitude'], d['longitude'] = float(lat), float(long)
		else:
			pass # print node
	convert_uni_dict_to_str_dict(d)
	d['cs_guid'] = d.pop('id')
	d['cs_title'] = d.pop('title')
	d['time_updated'] = convert_weird_time_to_unix_time(d.pop('updated'))
	entry_list.append(d)

db_conn = sqlite.connect('/home/evan/oakland-crime/oakland_crime.db')
cursor = db_conn.cursor()

for entry in entry_list:
	cursor.execute('SELECT time_updated FROM atom_feed WHERE cs_guid = ?', (entry['cs_guid'],))
	result = cursor.fetchone()
	if not result:
		print 'insert %s' % entry['cs_guid']
		cursor.execute('INSERT INTO atom_feed (cs_guid, cs_category, cs_title, cs_url, time_fetched, time_updated, latitude, longitude) VALUES (:cs_guid, :cs_category, :cs_title, :cs_url, :time_fetched, :time_updated, :latitude, :longitude)', entry)
	else:
		time_updated, = result
		if entry['time_updated'] > time_updated:
			print 'new data, updating %s' % entry['cs_guid']
			cursor.execute('UPDATE atom_feed SET cs_category = :cs_category, cs_title = :cs_title, cs_url = :cs_url, time_fetched = :time_fetched, time_updated = :time_updated, latitude = :latitude, longitude = :longitude WHERE cs_guid = :cs_guid', entry)
		else:
			print 'updating time fetched for %s' % entry['cs_guid']
			cursor.execute('UPDATE atom_feed SET time_fetched = :time_fetched WHERE cs_guid = :cs_guid', entry)
db_conn.commit()
