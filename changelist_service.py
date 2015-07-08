import cherrypy
import simplejson
import re
import smtplib
from email.mime.text import MIMEText
from simple_salesforce import Salesforce

class changelist_service(object):

    exposed = True
    global username
    global password
    global token_key
    global proxy
    global sender_email
    global smtp

    @cherrypy.tools.accept(media='text/plain')
    # Use this method for the initial setup
    def GET(self):
        return 'OK'

    def POST(self, length=8):
        cl = cherrypy.request.headers['Content-Length']
        rawbody = cherrypy.request.body.read(int(cl))
        body = simplejson.loads(rawbody)

        # Grab the Git variables from the json.
        try:
            commit_message_string = str(body['commits'][0]['message'])
            git_url = str(body['compare'])
            email = str(body['head_commit']['author']['email'])
        except KeyError:
            cherrypy.response.status = 206
            return "Invalid JSON"

        # Regex for W-123155 format
        match = re.search( r'([Ww]-\d+)', commit_message_string )

        # If there's no work item ID message the user
        if not match:
            raw_message = 'Your recent commit of ' + git_url + ' did not have an associated '
            raw_message = raw_message + ' work ID to bind this commit to. I.e. '
            raw_message = raw_message + ' W-123123 . Please add work Items to future check ins.'
            msg = MIMEText(raw_message)
            msg['Subject'] = 'Your recent Git commit didn\'t have an associated work ID'
            msg['From'] = sender_email
            msg['To'] = email
            s = smtplib.SMTP(smtp)
            s.sendmail(sender_email, [email], msg.as_string())
            s.quit()
            cherrypy.response.status = 202
            return "OK"
        else:
        	work_item_name = match.group(1)

        proxies = { "https": proxy}
        try:
            # Connect to the GUS SFDC API
            sfdcConnector = Salesforce( password=password, username=username, security_token=token_key, proxies=proxies )
        except simple_salesforce.login.SalesforceAuthenticationFailed:        
            cherrypy.response.status = 202
            return 'Login failure to SFDC api. Please confirm your credentials'

        work_item_id = str(changelist_service.getWorkItemIDFromSalesforceAPI( sfdcConnector, work_item_name ))
        # Split the url in half, since the GUS will prepend the Git server hostname
        git_url_relative = git_url.split('//')[1].split('/',1)[1]
        # Create the change list entry
        changelist_service.publishChangeListEntryIntoSalesforceAPI( sfdcConnector, work_item_id, git_url_relative  )

        cherrypy.response.status = 200
        return "OK"

    @staticmethod
    def getWorkItemIDFromSalesforceAPI( sfConnector, workItemName ):
        workItemResult = dict(sfConnector.query("SELECT Id, Name FROM ADM_Work__c where Name = '" +workItemName+ "'"))
        try:
            workItemResult_id = workItemResult['records'][0]['Id']
        except IndexError:
            # If no result, end the email!
            cherrypy.response.status = 202
            return 'Unable to find the work item'
        return workItemResult_id

    @staticmethod
    def publishChangeListEntryIntoSalesforceAPI( sfConnector, work_id, git_url ):
        sfConnector.agf__ADM_Change_List__c.create({
            'Work__c' : work_id,
            'Perforce_Changelist__c': git_url ,
            'Source__c':'Internal Git',
            'External_ID__c': git_url
     })

if __name__ == '__main__':
   
    # Load the properties file
    property_data = simplejson.loads(open('properties.json').read())
    username = property_data['username']
    password = property_data['password']
    token_key = property_data['token_key']
    proxy = property_data['proxy']
    sender_email = property_data['sender-email']
    smtp = property_data['smtp']
   
    conf = {
    '/': {
         'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
         'tools.sessions.on': True,
         'tools.response_headers.on': True,
         'tools.response_headers.headers': [('Content-Type', 'text/plain')],
        }
    }
    cherrypy.quickstart(changelist_service(), '/', conf)
