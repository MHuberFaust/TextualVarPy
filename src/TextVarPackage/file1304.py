import glob
#import os
import re
import simplejson as json
from lxml import etree
import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings
settings.configure()

from django import template

#ToDo:

#correct style attributes or write a css-file
#get rid of global variables
#change parseEtree to only access the selected lines
#refine xpath-expression and verse selection
#refine function structure
#put Sigle in html output (//altIdentifier[@type="edition"]/idno/text())
#filter out redundant/the same verses. Probably RE after xpath query -> needs testing with bigger corpus




###################################################################
#Variables
###################################################################
fileList=[]
fileList1=[]
objectToParse = {}
pythonTempList=[]
contextObjectList = []
#t = 'insert filePath to template'

##
#"dialog"-function
#let the user choose between two use-cases typical for scholarly editions:
##1. shows all text lines of a document // not sure if it is worth implementing
##2. shows textual variance of a text line

def inputConsole(inputVerseFilePath):
    consoleInput = input('Please write one or several verse numbers separated by a comma to see their variance in Goethes Faust')
    if (re.fullmatch('\d{1,6}', consoleInput)):
        #do stuff with consoleInput
        verseFilePathDict ={}
        with open (inputVerseFilePath,'r', encoding='utf-8') as f:
            verseFilePathDict = json.load(f, encoding='utf-8')
            fileList = verseFilePathDict[consoleInput]
        parseXML(fileList)
        
            
    else:
        inputTempList = re.split('\d{1,6}', consoleInput)
        for inputTemp in inputTempList:
            if (re.fullmatch('\d{1,6}', inputTemp)):
                fileList.append(inputTemp)
        parseXML(fileList)
        
    

##
#reads all files of the given directory and calls parseXML() with fileList
def readLocalXML(filePath):
    for item in glob.glob(filePath):
        fileList.append(item)
        print(item)
    parseXML(fileList)
    print('readLocal() done')
    







#fetches data from https://faustedition.uni-wuerzburg.de/xml/
#and saves it at filePathToSample
def readOnlineXML(filePathToSample):

    url = "https://faustedition.uni-wuerzburg.de/xml/transcript/gsa"
    r = requests.get(url, auth=HTTPBasicAuth('MHuber', 'mushroom87') )
    temp =r.text


    refList=re.findall(r'(?<=\>)\d{6}', temp)
    for urlExtension in refList:

        newURL = url+"/"+urlExtension +"/" + urlExtension + ".xml"
        print(newURL)
        s =requests.get(newURL, auth=HTTPBasicAuth('MHuber', 'mushroom87'))
        with open(filePathToSample + urlExtension,'w', encoding="utf-8") as f:
            f.write(s.text)
    print('readOnlineXML done')


# Be careful: deletes whitespace!
# parses an XML and calls parseEtree()
def parseXML(fileList):
    
        #recover=True for potentially broken XML (several crashes indicated that there is broken XML in the collection)
    parser = etree.XMLParser(recover=True, encoding = 'utf-8')
    for item in fileList:
        with open (item,'r', encoding='utf-8') as f:
            doc = etree.parse(f, parser)
            parseEtree(doc)

    #else:
        #for item in fileList:
            #doc = etree.fromstring(item)
            #parseEtree(doc)
    print('parseXML done')


def parseEtree(etreeObject):
    
    lList = etreeObject.xpath("//tei:l[@n]", namespaces = { "tei":"http://www.tei-c.org/ns/1.0"})
        #print (len(lList))
    for line in lList:
        lineNumber = line.get("n")

        #there are attributes "n = 1234-5678" with a range of verses,
        #indicating that the original verse/line is related to several verses in a later state.
        #a combination of split() and a more complex RE is needed to handle this
        #change verseFileDict according to it
        if re.match("^\d+$", lineNumber):

            #ignores inline-Elements! more complex XPath-Expression required
            lineText = etree.tostring(line, encoding="utf-8", method="text")
                #print (lineNumber)
                #print (lineText)
            #if lineAlready exists-> ignore
            #not tested yet! should work though
            if (objectToParse.get(lineNumber)):
                for equalLine in objectToParse[lineNumber]:
                    if not (lineText==equalLine):
                        objectToParse[lineNumber].append(lineText)
            else:
                objectToParse.setdefault(str(lineNumber),[]).append(lineText)
    #print (objectToParse)
    print ('parseEtree() done')



def sortUpload():
    #error prone if there are more then 26 variations
    charArray =["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z"]

    #jsonTemp=''
    #pythonTempDict ={}

    url = 'http://collatex.net/demo/collate'
    headers = {'content-type':'application/json',
                'accept':'application/json'}
    #CollateX only accepts json objects in a specific format: for more information: CollateX documentation
    for key, value in sorted(objectToParse.items()):
        difLines = {}
        for index, singleLine in enumerate(value):
            awitness = {"id":charArray[index],"content":singleLine}
            difLines.setdefault("witnesses",[]).append(awitness)
        ##old code:    
        #i = 0
        #while i < len(value):
            #awitness ={"id": charArray[i], "content":value[i]}
            #difLines.setdefault("witnesses",[]).append(awitness)
            #i = i + 1

        print(difLines)


        #change http header as CollateX provides several possible outputs
        #"if(r.status_code==requests.codes.ok):" produces an error...
        # with pydev extension for eclipse, but it is an known error
        r= requests.post(url, data=json.dumps(difLines),headers=headers)
        if(r.status_code==requests.codes.ok):
            data =json.loads(r.content)
            print((data))
            pythonTempList.append(data)

        else:
            print(('something is wrong with ' + str(key)))
            continue



#Creates Context for the django template
def createContext():
    
    print(('start'))
    #t = Template('insertDirectorythingy')
    for coldata in pythonTempList:
        contextObject ={}
        print (('--------coldata--------'))
        print ((coldata))
        #print ((coldata['table']))
        for variance in coldata['table']:
            print('-------variance--------')
            print ((variance))

            for index, tokenset in enumerate(variance):
                print('-------tokenset-----')
                print ((tokenset))

                contextObject.setdefault(index,[]).append(tokenset)
                #a contextObject should look like {1:['a','b','v','v']['aasd','asd','afds']}
        contextObjectList.append(contextObject)
                    #samplecolddata: {'witnesses': ['A', 'B'], 'table': [[['Ein '], ['Ein ']], [['ewges '], ['ewiges ']], [['Meer\n               '], ['Meer']], [[], [',\n                ']]]}
    print('-----------------------contexObjectList-------------------------')
    print((contextObjectList))
    print('createContext() done')
    #return contextObjectList

def renderContext():
    htmlString ="""
<html>
    <head>
        <title>
        Textual Variance
        </title>
    </head>
    <body>
        <h1>Apparatus</h1>
        <div>Dict-Key (change List to dict)</div>
        {% for contextObject in contextObjectList %}
        <table border="1">
            <thead>
                <tr>
                    <th>Sigle</th>
                    <th>verse//line content</th>
                </tr>
            </thead>
            <tbody>
                {% for key, value in contextObject.items %}
                    <tr>
                        <td>verse Sigle placeholder {{ key }}</td>
                        <td>
                            {% for varianceList in value %}
                                
                                <div type = "border">
                                    {% for item in varianceList %}
                                        {{ item }}
                                    {% endfor %}
                                </div>
                                
                            {% endfor %}
                        </td>
                    </tr>
                {% endfor %}
            </tbody>
         </table>   
        {% endfor %}
    </body>
</html>"""
    t = template.Template(htmlString)
    c = template.Context({'contextObjectList' : contextObjectList})
    renderedTemp = t.render(c)
    print (renderedTemp)
    with open('/Users/MHuber/Documents/python/newHtml.html','w', encoding ='utf-8') as f:
        f.write(renderedTemp)
    #print((t.render(c)))






###################################################
#function call
###################################################
inputConsole('/Users/MHuber/Documents/python/verseFilePath.json')
#readLocalXML('/Users/MHuber/Documents/python/testFolder/*')
#readOnlineXML('/Users/MHuber/Documents/python/testFolder/')
#parseXML()
sortUpload()
createContext()
renderContext()