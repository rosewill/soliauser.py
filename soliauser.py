import requests
import time
import random

def stringBetween(begin, end, search):
	beginPos = search.find(begin) + len(begin)
	return search[beginPos:search.find(end, beginPos)]

class soliaUser():
	def __init__(self, usern, passw):
		self.u = usern # Username
		self.p = passw # Password
		self.r = requests.session() # Requests Session
		self.lpt = None # Last Post Time 
		self.sid = None # Session ID
		self.bbs  = None # BBCode beginning formatting
		self.bbf = None # BBCode ending formatting 
		self.ua = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11' # User-Agent String

	def getLPT(self):
		# get the last post time
		return self.lpt

	def setUA(self, ua):
		# set the user agent string sent on every request to mimic a real user
		self.ua = ua

	def setBB(self, sep='@', bb=None):
		# set the user's bb code, seperator is the string from the users preset bb code that will be replaced with a message
		# bb argument not implemented and can be ignored
		if bb == None:
			d = self.r.get('http://soliaonline.com/community/ucp.php?i=prefs&mode=post')
			bb = stringBetween('width: 647px;">', '</textarea>', d.content)
		self.bbs = bb[:bb.find(sep)]
		self.bbf = bb[bb.find(sep) + len(sep):]
		print(self.bbs)
		print(self.bbf)
	
	def login(self):
		# call to login as the user calling the method
		payload = {'mode':'login','redirect':'..%2Findex.php','username':self.u,'password':self.p, 'autologin':'on', 'login':'Login'}
		headers = {'User-Agent':self.ua, 'Referer':'http://soliaonline.com/', 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'Connection':'keep-alive', 'Host':'soliaonline.com'}
		
		d = self.r.post('http://soliaonline.com/community/ucp.php', data=payload, headers=headers)
		
		if d.content.find('user_gold_value') != -1:
			self.r.cookies['solia_orq1k_sid'] = stringBetween('index.php?sid=', '" />', d.content) # this line is 90% not necessary
			self.sid = self.r.cookies['solia_orq1k_sid']
			return 'Login Successful'
		else:
			return 'Login Failed'

	def checkPrizeWheel(self):
		# check the daily prize wheel and get the prize if possible
		# can only get the prize wheel twice a day from one IP address
		d = self.r.get('http://soliaonline.com')
		
		if d.content.find('Spin the daily prize wheel!') != -1:
			akey = stringBetween('id="daily_prize" key="', '" href="', d.content)
			payload = {'mode':'start', 'akey':akey}
			headers = {'User-Agent':self.ua, 'Referer':'http://soliaonline.com/', 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'Connection':'keep-alive', 'Host':'soliaonline.com'}
			d = self.r.post('http://soliaonline.com/community/ajax/daily.php', data=payload, headers=headers,)

			if d.content.find('claimed their prize from this IP address') != -1:
				return 'Daily Prize available, but two Daily Prizes already claimed from this IP.'
			
			dkey = stringBetween('{"complete":"', '"}', d.content)
			payload = {'mode':'stop', 'dkey':dkey}
			
			d = self.r.post('http://soliaonline.com/community/ajax/daily.php', data=payload, headers=headers)
			
			if stringBetween('{"complete":"', '","icon', d.content) == 'Spin Complete, Prize Awarded.':
				return 'Got Daily Prize: ' + stringBetween('"name":"', '","simg', d.content)
			else:
				return 'Failed to get Daily Prize'
		else:
			return 'No Daily Prize Available'

	def clickPet(self, petid):
		# click on a petID
		d = self.r.get('http://soliaonline.com/community/pets/viewer.php?id=' + petid)
		
		if d.content.find('</strong><br />Ready</div>') != -1:
			slot = stringBetween('pet_inv_button pet_inv_ready" slot="', '" id="use_inv', d.content)
			akey = stringBetween('var ajaxKey = "', '";', d.content)
			payload = {'mode':'use_item', 'slot':slot, 'key':petid, 'akey':akey}
			headers = {'User-Agent':self.ua, 'Referer':'http://soliaonline.com/community/pets/viewer.php?clvl=1&id=' + petid, 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'Connection':'keep-alive', 'Host':'soliaonline.com'}
			
			d = self.r.post('http://soliaonline.com/community/pets/ajax.php', data=payload, headers=headers)

			if d.content.find('Earned') != -1:
				return 'Pet ID ' + petid + ' clicked for ' + stringBetween('Earned +', '","ani', d.content) + '.'
			elif d.content.find('Please wait one minute before') != -1:
				return 'Must wait ' + stringBetween('another item. (', 's left)"}', d.content) + ' seconds before clicking.'
			else:
				return 'Clicking pet ID: ' + petid + ' failed.'
		else:
			return 'No items ready for pet ID: ' + petid

	def artComment(self, artid, comment_title, comment):
		# comment on a piece of art
		payload = {'mode':'post', 'art_id':artid, 'comment_title':comment_title, 'comment':comment, 'art_id':artid}
		headers = {'User-Agent':self.ua, 'Referer':'http://soliaonline.com/community/art_view.php?art_id=' + str(artid), 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'Connection':'keep-alive', 'Host':'soliaonline.com'}
		
		if time.time() - self.lpt < 31:
			time.sleep(time.time() - self.lpt)
		
		d = self.r.post('http://soliaonline.com/community/art_view.php', data=payload, headers=headers)
		
		if d.content.find('Your comment was submitted') != -1:
			self.lpt = time.time()
			return 'Comment posted on ID ' + str(artid) + ' for ' + stringBetween('submitted and you gained ', ' gold. <br', d.content) + ' gold.'
		elif d.content.find('Please allow 30 seconds between each post.') != -1:
			return 'Must wait 30s before commenting again on art.'
		else:
			return 'Commenting on ID ' + str(artid) + ' failed.'

	def avatarComment(self, avid, comment_title, comment):
		# comment on an avatar design
		payload = {'mode':'comment', 'id':avid, 'comment_title':comment_title, 'comment':comment, 'id':avid}
		headers = {'User-Agent':self.ua, 'Referer':'http://soliaonline.com/community/avatar_arena.php?mode=view&id=' + str(avid), 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'Connection':'keep-alive', 'Host':'soliaonline.com'}

		if time.time() - self.lpt < 31:
			time.sleep(time.time() - self.lpt)
		
		d = self.r.post('http://soliaonline.com/community/avatar_arena.php', data=payload, headers=headers)
		
		if d.content.find('Your comment was submitted and you gained <strong>') != -1:
			self.lpt = time.time()
			return 'Comment posted on ID ' + str(avid) + ' for ' + stringBetween('submitted and you gained <strong>', ' gold</strong>.', d.content)
		else:
			return 'Commenting on ID ' + str(avid) + ' failed.'

	def postReply(self, forumid, topicid, message):
		# post a reply to a thread in the forums
		headers = {'User-Agent':self.ua, 'Referer':'http://soliaonline.com/community/viewtopic.php?' + forumid + '&t=' + topicid}
		
		d = self.r.get('http://soliaonline.com/community/posting.php?mode=reply&f=' + forumid + '&t=' + topicid, headers=headers)

		lastclick = stringBetween('lastclick" value="', '" />', d.content)
		creation_time = stringBetween('creation_time" value="', '" />', d.content)
		form_token = stringBetween('form_token" value="', '" />', d.content)
		topic_cur_post_id = stringBetween('topic_cur_post_id" value="', '" />', d.content)
		payload = {'addbbcode20':'100', 'message':self.bbs + message + self.bbf, 'topic_cur_post_id':topic_cur_post_id, 'lastclick':lastclick, 'post':'Submit', 'attach_sig':'on', 'creation_time':creation_time, 'form_token':form_token}
		headers = {'User-Agent':self.ua, 'Referer':'http://soliaonline.com/community/posting.php?mode=reply&f=' + forumid + '&t=' + topicid, 'Content-Type':'application/x-www-form-urlencoded', 'Connection':'Keep-alive', 'Host':'soliaonline.com', 'Accept-Language':'en-us,en;q=0.5', 'Accept-Encoding':'gzip, deflate', 'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}

		time.sleep(random.randint(2,5)) # without this delay breaks completely

		if time.time() - self.lpt < 31:
			time.sleep(time.time() - self.lpt)

		d = self.r.post('http://soliaonline.com/community/posting.php?mode=reply&f=' + forumid + '&sid=' + self.sid + '&t=' + topicid, data=payload, headers=headers, allow_redirects=True)

		if d.content.find('This message has been posted successfully.') != -1:
			self.lpt = time.time()
			return 'Comment posted in topic ' + str(topicid) + ' for ' + stringBetween('successfully.<br />You earned ', ' gold for this post.', d.content) + ' gold.'
		elif d.content.find('You cannot make another post so soon after your last.') != -1:
			return 'Could not post in topic: ' + str(topicid) + ' need to wait longer.'
		else:
			return 'Posting in topic: ' + str(topicid) + ' failed.'

	def postTopic(self, forumid, subject, message):
		# post a topic in the forums
		headers = {'User-Agent':self.ua, 'Referer':'http://soliaonline.com/community/viewforum.php?f=' + forumid}

		d = self.r.get('http://soliaonline.com/community/posting.php?mode=post&f=' + forumid, headers=headers)

		lastclick = stringBetween('lastclick" value="', '" />', d.content)
		creation_time = stringBetween('creation_time" value="', '" />', d.content)
		form_token = stringBetween('form_token" value="', '" />', d.content)
		payload = {'mode':'post', 'f':forumid, 'sid':self.sid, 'subject':subject, 'addbbcode20':'100', 'message':self.bbs + message + self.bbf, 'lastclick':lastclick, 'post':'Submit', 'attach_sig':'on', 'creation_time':creation_time, 'form_token':form_token, 'poll_title':'', 'poll_option_text':'', 'poll_max_options':'1', 'poll_length':'0'}
		headers = {'Host':'soliaonline.com', 'Referer':'http://soliaonline.com/community/posting.php?mode=post&f=' + forumid, 'User-Agent':self.ua, 'Content-Type':'application/x-www-form-urlencoded', 'Connection':'Keep-alive', 'Host':'soliaonline.com', 'Accept-Language':'en-us,en;q=0.5', 'Accept-Encoding':'gzip, deflate,sdch', 'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}

		time.sleep(random.randint(2,7)) # will probably break without this delay

		if time.time() - self.lpt < 31:
			time.sleep(time.time() - self.lpt)

		d = self.r.post('http://soliaonline.com/community/posting.php', data=payload, headers=headers)

		if 'This message has been posted successfully.' in d.content:
			self.lpt = time.time()
			return 'Topic posted in forum ' + str(forumid) + ' for ' + stringBetween('successfully.<br />You earned ', 'gold for this post.', d.content) + ' gold.'
		else:
			return 'Posting topic in forum ' + str(forumid) + ' failed.'

	def profileComment(self, profileID, comment):
		# post a comment on a user's profile
		headers = {'User-Agent':self.ua, 'Referer':'http://soliaonline.com/profile/' + profileID + '/'}

		d = self.r.get('http://soliaonline.com/profile/' + profileID + '/post/')
		
		akey = stringBetween('ajaxKey 	= "', '";', d.content)
		payload = {'mode':'ajax_comment_post', 'akey':akey, 'pid':profileID, 'text_entery':comment} # no typo on 'text_entery', their dev spelled it wrong in the request
		headers = {'Referer':'http://soliaonline.com/profile/98678/post/', 'X-Requested-With':'XMLHttpRequest','Origin':'http://soliaonline.com','Host':'soliaonline.com', 'Accept':'application/json, text/javascript, */*', 'Content-Type':'application/x-www-form-urlencoded'}

		d = self.r.post('http://soliaonline.com/community/ajax/profile_ajax.php', data=payload, headers=headers)

		headers = {'User-Agent':self.ua, 'Referer':'http://soliaonline.com/profile/' + profileID + '/'}

		d = self.r.get('http://soliaonline.com/profile/' + profileID + '/comments/', headers=headers)

		if comment in d.content:
			return 'Comment posted on profile ID ' + profileID + '.'
		else:
			return 'Posting comment on profile ID ' + profileID + ' failed.'

''' Sample Code Below

testUser = soliaUser('megusta', 'mememes') # these accounts are banned
testUser2 = soliaUser('jackojacko12', '123456')


print(testUser2.login())
print(testUser2.checkPrizeWheel())
print(testUser2.clickPet('b5a'))
print(testUser2.artComment('15211', 'Great effect', 'I really like your style'))
print(testUser2.avatarComment('737', 'Cool fairy', 'This is a nice fairy'))
print(testUser.login())
testUser.setBB('TEXT HERE')
print(testUser.postReply('41', '296457', 'Welcome to solia, you seem like a cool person, I hope you like it here.'))
print(testUser.profileComment('88949', 'Sweet profile!'))
print('Finished.')

'''