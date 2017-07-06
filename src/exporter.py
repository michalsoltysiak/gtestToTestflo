'''
Created on Jul 4, 2017

@author: slsm
'''
from jira import JIRA
import sys, getopt
import jiraDump
from jiraDump import dumpIssue
from sre_compile import isstring
import datetime
import re
from jira.exceptions import JIRAError
import json
from orca.scripts.apps import planner






def parseCommandLine(argv):
    dictArgs=dict({'user':'','password':'','key':'','inputFile':''})
    try:
        opts, args = getopt.getopt(argv,"hu:p:k:i:s:",["user=","pass=","key=","ifile=","server="])
    except getopt.GetoptError:
        print( 'main.py -u <jira_user> -p <jira_password> -k <project_key> -i <input_file> -s <server_url>' )
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print( 'main.py -i -u <user> -p <password> -k <project_key> -i <input_file> -s <server_url>' )
            sys.exit()
        elif opt in ("-u", "--user"):
            dictArgs['user'] = arg
        elif opt in ("-p", "--password"):
            dictArgs['password'] = arg
        elif opt in ("-k", "--key"):
            dictArgs['key'] = arg
        elif opt in ("-i", "--ifile"):
            dictArgs['inputFile'] = arg
        elif opt in ("-s", "--server"):
            dictArgs['server'] = arg
    return dictArgs

    

class JiraHelper:
    priorities=['Low', 'Normal', 'High', 'Critical']
    testResults=['Pass', 'Fail','Test','Skipped']
    testTypes={'Other':'None', 'Acceptance':'Acceptance', 'Smoke':'Smoke', 'Regression':'Regression', 'Performance':'Performance', 'Development':'Development', 'Security':'Security', 'Installation':'Installation', 'Destructive':'Destructive'}
    testLevels=['None', 'Unit', 'Integration', 'Component Interface', 'System', 'Operational Acceptance']
        
    
    def __init__(self, jiraObj, projectKey):
        '''
        :param jiraObj - initiated (created) JIRA object
        :param projectKey - string which identify project key you want to work with
        :param   
        '''
        self.errLog=''
        self.projectKey = ''
        if isinstance(jiraObj, JIRA):
            self.jira = jiraObj
        else:
            raise JIRAError('jiraObj is not instance of JIRA class')
        
        
        self.cfDict = self.__customFiledsMapping()
                     
        if isstring(projectKey):
            for p in self.jira.projects():
                if p.key == projectKey:
                    self.projectKey = projectKey
                    break
            if not self.projectKey:
                raise JIRAError(projectKey+ ' is not found or user has no access') 
        self.components = list()
                    
    def __customFiledsMapping(self):
        cfMap = dict()
        for f in self.jira.fields():        
            if f['id'].find('customfield_') == 0: #id fields starts with 'customfield_'
                cfMap[f['name']]=f['id']
        return cfMap

    def createTestPlan(self, summary, priority='Normal'):
        if priority not in JiraHelper.priorities:
            raise JIRAError('incorrect priority ') 
    
        issueDict = dict()
        issueDict['project'] = {'key':self.projectKey}
        issueDict['issuetype'] = {'name':'Test Plan'}
        issueDict['summary'] = summary
        issueDict['priority'] = {'name':priority}
        self.testPlanIssue = jira.create_issue(fields=issueDict)
        return self.testPlanIssue.key
    
    def createTestCase(self, uniqueTemplateID, testResult=''):
        query = 'project = ' + self.projectKey + ' and issuetype= \'Test Case Template\' and summary ~ ' + uniqueTemplateID
        issues = self.jira.search_issues(query)
        if len(issues) > 1:
            print( 'Warning: More than one issue found: %s, using first one' % uniqueTemplateID )            
            
        elif len(issues) == 0:
            print( 'Warning: No issue found: %s' % uniqueTemplateID )
        else:
            pass
        tctIssue = issues[0]
        
        issueDict=dict()        
        issueDict['project'] = {'key':self.projectKey}
        issueDict['issuetype'] = {'name': 'Test Case'}
        issueDict['summary'] = tctIssue.fields.summary
        issueDict['priority'] = {'name':tctIssue.fields.priority.name }
        issueDict['parent'] = { 'key' : self.testPlanIssue.key }
        issueDict['description'] = getattr(tctIssue.fields, 'description')
        issueDict[self.cfDict['Pre-conditions']] = tctIssue.raw['fields'][self.cfDict['Pre-conditions']]     
        
        issueDict[self.cfDict['Test Type']] = tctIssue.raw['fields'][self.cfDict['Test Type']]
        issueDict[self.cfDict['Test Level']] = tctIssue.raw['fields'][self.cfDict['Test Level']] 
        
        issueDict[self.cfDict['Steps']] = tctIssue.raw['fields'][self.cfDict['Steps']]
        #issueDict[self.cfDict['Steps']]['rows'][0]['columns'][3]['value']=''
        #issueDict[self.cfDict['Steps']]['rows'][1]['columns'][3]['value']=''
        issueDict[self.cfDict['TC Template']] = tctIssue.key
        issueDict['components'] = tctIssue.raw['fields']['components']
        issueDict['labels'] = tctIssue.raw['fields']['labels']
        #issueDict[self.cfDict['Epic Link']] = tctIssue.raw['fields'][self.cfDict['Epic Link']]
        '''
        labels
        components
        
        '''
        
        self.tcIssue = self.jira.create_issue(fields = issueDict)
        
        
        print('')
    def dumpIssue( self, issueId ):
        """ 
            this functin returns raw value of issue fields (all of them) in JSON format
            :param jiraObj -JIRA object - you need to create it first  - connecting to jira server)
            :param issueId - string containign issue id  
        """  
        
        fields = self.jira.issue(issueId).raw
        return fields
 
    
    
if __name__ == "__main__":

    parsedArgs = dict()
    parsedArgs = parseCommandLine(sys.argv[1:])

    jira = JIRA(parsedArgs['server'],basic_auth=(parsedArgs['user'], parsedArgs['password']))
    #if True:
    if False:
        issueDict = dict( {'project':{'key':parsedArgs['key']}, 'issuetype': {'name': 'Test Plan'}, 'summary':'Test Test Plan' })
        
        issue = jira.create_issue(fields=issueDict)
        issueDict = dict( {'project':{'key':parsedArgs['key']}, 'issuetype': {'name': 'Test Case'}, 'parent' : { 'id' : issue.key}, 'customfield_11493': 'SBREST-358', 'summary':'test it', 
                            })
        issue = jira.create_issue(fields=issueDict)
        jira.transition_issue(issue, 'Test')
        jira.transition_issue(issue, 'Pass')
        

    else:
        print( dumpIssue(jira, 'SBREST-439') )
        print( dumpIssue(jira, 'SBREST-440') )
        print( dumpIssue(jira, 'SBREST-451') )
      
        jh = JiraHelper(jira, 'SBREST')
        key = jh.createTestPlan('Test plan ', 'Normal')
        jh.createTestCase('C2020')


'''
        copy test plann
'''