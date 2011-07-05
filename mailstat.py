import os
import time
import re
import logging
import StringIO
import urlparse
from datetime import datetime
import email
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.api import datastore
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler 
from google.appengine.api import mail

class MailLog(db.Model):
    emailaddr = db.EmailProperty(required=True)
    mailtime = db.DateTimeProperty()

class PersonStat(db.Model):
    emailaddr = db.EmailProperty(required=True)
    name = db.StringProperty()
    mailinglist = db.StringProperty()
    mailmonth = db.ListProperty(int)
    mailtime = db.ListProperty(int)
    total = db.IntegerProperty()
    

class MailServiceHandler(InboundMailHandler):
        
    def receive(self, mail_message):
        logging.info("Received a message from: " + mail_message.sender)

        #temporary
        # bodies = []
        # for content_type,text in mail_message.bodies('text/plain'):
        #     bodies.append(text.decode())

        # txtmsg = '\n'.join(bodies)
        # logging.info(txtmsg)
        #end of temporary

        (_name, _emailaddr) = email.utils.parseaddr(mail_message.sender)
        if (_name==''): _name = _emailaddr

        tm = email.utils.parsedate(mail_message.date)
        q = PersonStat.all()
        q.filter("emailaddr =", _emailaddr)
        results = q.fetch(1)
        if (len(results)==0):
            _mailtime =  [0 for x in range(0,24)]
            _mailtime[tm[3]] += 1; #increase time count
            p = PersonStat(emailaddr=_emailaddr, name=_name, mailinglist="itb",
                           mailtime = _mailtime, total=1)
            
            p.put()
        else:
            p = results[0]
            p.mailtime[tm[3]] += 1; #increase time count
            p.total += 1
            p.put()
        m = MailLog(emailaddr=_emailaddr, mailtime=datetime.fromtimestamp(time.mktime(tm)))
        m.put()
    

class StatPage(webapp.RequestHandler):
    def get(self):
        self.response.out.write('Mailing List Stat')
        path = self.request.path[1:]
        q = PersonStat.all()
        q.filter("mailinglist = ", path)
        q.order("-total")
        stats = q.fetch(20)
        template_values = { 'title': path,
                            'statsdata': stats}
        

        path = os.path.join(os.path.dirname(__file__), 'stat.html')
        self.response.out.write(template.render(path, template_values))        

class MainPage(webapp.RequestHandler):
    def get(self):
        self.response.out.write('Mailing List Stat')
        template_values = {}
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

    def post(self):
        self.response.out.write('Nothing to see here, move along')


application = webapp.WSGIApplication(
    [MailServiceHandler.mapping(),    
        ('/', MainPage), 
        ('/itb', StatPage),
        ('/others', StatPage),
        ],
    debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

