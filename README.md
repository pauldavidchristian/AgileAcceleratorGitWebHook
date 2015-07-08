AgileAcceleratorGitWebHook
=================

### Synopsis

This script is meant to run as a service in SFM as receiver for git commit POSTs.  On each commit, a call is made to the GUS partner API. This call will generate a "change_list" object used to associate a code check with a GUS story or bug.

### Dependences


The service needs to run on a host where it can access your git server. This was developed in SFM against the git.soma server.


Add dependent python modules need to be installed on the host. I recommend using python's "virtualenv" for this.

### General Setup

*Setup and start the service*
  1. git clone https://git.soma.salesforce.com/pchristian/AgileAcceleratorGitWebHook.git
  2. cd AgileAcceleratorGitWebHook
  3. Modify the properties.json file as necessary
  4. python changelist_service.py 
  5. Ping it to make sure it's up; From a separate terminal > wget http://localhost:8080
  
*Configure the Git repository*
  1. From the Git HTTP UI, navigate to your repo.
  2. Click 'Settings' -> 'Webhooks & Services' and click 'Add webhook'
  3. Fill in the Payload URL with the location of the service from previous steps
  4. Set the content type to 'application/json'
  5. Leave secret empty for now
  6. Select 'Just the push event'
  7. Make sure the Activate check box is selected

### Usage

  *Assuming everything is configured appropriately you should be ready to test is out*
  1. Check out a git repo and make a simple edit to a file. I.e. a README.md
  2. Add it. I.e. git add README.md
  3. Commit it, but when you do add a work item ID to it. I.e. "Checking in a fix for whatever W-2572989 ".
  4. Push the commit.
  5. Wait a little bit then navigate to the GUS work item. You should see an entry in the Change List section at the bottom of the page.
  6. W00t! You're done!
  

### Current SSL approach

  Apache's native to SSL support ( mod_ssl ) was used to support SSL and a rewrite rule was to foward the port. 

I.e.
```
 RewriteEngine on 
 RewriteRule ^(.*) http://127.0.0.1:8080$1 [proxy]
````

### ToDo


Add in secrete key bits
