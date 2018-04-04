import requests
import json
import sys
import re
from googletrans import Translator


header={'Accept':'application/json','Content-type':'application/json'}

#payload={'userName':'ssukumaran7','password':'test123','auth':'secEnterprise'}
payload={'userName':'administrator','password':'Admin1234','auth':'secEnterprise'}                
#get token
#response=requests.post('http://20.198.58.32:6405/biprws/logon/long',json=payload,headers=header)	
response=requests.post('http://20.198.60.132:6405/biprws/logon/long',json=payload,headers=header)	
token=response.json()['logonToken']

docId=278407
elementList=[]
processList=[]
toLanguage='id'
#'ar'
encoding='utf8'
documentsToProcess=[]

try :
	translator=Translator()
	
	if (translator.translate('Hello World',dest='en').text =='Hello World'):
		print 'Translation service working' 
 	else:
 		'Translation service down...exiting'
 		sys.exit()

except:
 	print 'Error in library'
 	print sys.exc_info()[0]
 	sys.exit()


def getDocDtls(docId):	
	documenturl='http://20.198.60.132:6405/biprws/raylight/v1/documents/'+str(docId)+'/reports'
	header = {
	            'X-SAP-LogonToken': '"' + token + '"',
	            'Accept': 'application/json'}

	response=requests.get(documenturl,headers=header)

	responseDict=response.json()
	responseDict['documentId']=docId
	return [responseDict]

def translateText(Translator,inputText):
	toTranslateText=inputText
	try:
		return translator.translate(toTranslateText,dest=toLanguage).text.encode(encoding)
	
	except error as e:
		print sys.exc_info()[0]
		return None


def addReport(docId):
	documenturl='http://20.198.60.132:6405/biprws/raylight/v1/documents/'+str(docId)+'/reports'

	payload={'report':{'name':'Chart Report'}}

	header = {
	            'X-SAP-LogonToken': '"' + token + '"',
	            'Content-Type': 'application/json',
	            'Accept': 'application/json'}

	response=requests.post(documenturl,headers=header,json=payload)

	return response.text

def saveChanges(docId):
	print('Saving Changes')
	documenturl='http://20.198.60.132:6405/biprws/raylight/v1/documents/'+str(docId)
	header = {
	            'X-SAP-LogonToken': '"' + token + '"',
	            'Accept': 'application/json'}

	response=requests.put(documenturl,headers=header)
	print(response.text)

def getReportElements(docId,reportId):

	reportElementList=[]
	
	reportUrl='http://20.198.60.132:6405/biprws/raylight/v1/documents/'+str(docId)+'/reports/'+str(reportId)+'/elements'
	header = {
	            'X-SAP-LogonToken': '"' + token + '"',
	            'Accept': 'application/json'}

	response=requests.get(reportUrl,headers=header)

	for elements in response.json()['elements']['element']:
			#if elements['@type'] in ('Cell','HTable','VTable'):
				try:
					reportElementList.append((reportId,elements['@type'],elements['parentId'],elements['id']))
				except KeyError as e:
					#This is required for handling PageZone elements like Header & Footer
					# check this
					reportElementList.append((reportId,elements['name'],elements['@type'],elements['id']))

	with open('output.txt','a') as file:
			file.write(response.text)
			file.write('-----------------------------------------')
	#reportElementList=filter(lambda x:x[3]==18,reportElementList)
	return reportElementList

def getAllElementParams(docId,reportelementList):

	elementParamList=[]

	for elementReportId,elementType,elementParentId,elementId in reportelementList:

		reporturl='http://20.198.60.132:6405/biprws/raylight/v1/documents/'+str(docId)+'/reports/'+str(elementReportId)+'/elements/'+str(elementId)

		header = {
		            'X-SAP-LogonToken': '"' + token + '"',
		            'Accept': 'application/json'}
		response=requests.get(reporturl,headers=header)
		
		elementParamList.append((elementReportId,elementType,elementParentId,elementId,response.json()))

	return elementParamList

def updateElementText(docId,Translator,elementParamList):

	header = {'X-SAP-LogonToken': '"' + token + '"',
		          'Content-Type':'application/json',
		          'Accept': 'application/json'}

	#cellList=filter(lambda x:x[1]=='Cell',elementParamList)   

	for elementReportId,elementType,elementParentId,elementId,params in elementParamList:
		elementFinalList=[]
		translatedParam=''
		#Map required with text key and translated value. This will be used to replace the original text
		translateTextMap={}
		translatedText=''
		finalProcessedText=''
		tmpList=[]
		updateurl='http://20.198.60.132:6405/biprws/raylight/v1/documents/'+str(docId)+'/reports/'+str(elementReportId)+'/elements/'+str(elementId)

		with open('trans.txt','a') as file:			
			try:
				payload=params
				#Code section to handle Formula inside Cell or other elements
				#print params['element']['content']['expression']['formula']['@dataType']
				#regular expression to match all words within double quotes				
				tmpParams=params['element']['content']['expression']['formula']['$']
				translationTextList=re.findall(r'"([^"]*)"',tmpParams)
				
				#need separate handling for Nameof since it need to change to static translated text
				if 'NameOf' in tmpParams:
					for requiredField in tmpParams.split('.'):
							tmpList.append(requiredField)
						
					tmpTranslateText=tmpList.pop()

					nameofText=re.search(r'\[(.*?)\]',tmpTranslateText).group(1)
					print 'nameofText' ,nameofText
					translatedText=translateText(translator,nameofText)
					print 
					translateTextMap.update({nameofText:translatedText})
					print 'translateTextMap',translateTextMap

				else:
					for translationTextKey in translationTextList:
						translatedText=translateText(translator,translationTextKey)
							
						translateTextMap.update({translationTextKey:'\"'+translatedText+'\"'})				    	


				print 'Map',translateTextMap
				tmpList=[]
				
				for tokens in tmpParams.split("\""):					 
					print ('process list',tokens)
					
					if 'NameOf' in tokens:						
						print 'inside token'
						for requiredField in tokens.split('.'):
							tmpList.append(requiredField)
						
						tokens=tmpList.pop()

						print 'required txt',tokens
						elementFinalList.append(translateTextMap[re.search(r'\[(.*?)\]',tokens).group(1)])
						print 'elementFinalList' ,elementFinalList
					else:
						try:
							elementFinalList.append(translateTextMap[tokens])

						except KeyError as e:
							elementFinalList.append(str(tokens))

						except:
							print sys.exc_info()[0]

			 	
				print 'finallist',elementFinalList
				
				try:
					finalProcessedText=finalProcessedText.join(elementFinalList)
					payload['element']['content']['expression']['formula']['$']=finalProcessedText
				
				except:
					print sys.exc_info()[0]
				
			 
			except KeyError as e:

				print 'Inside cell handling code'

				try:
					#Code section to handle Cell without concatenated formula strings
					payload=params
					print ('cell translate text',params)
					textToTranslate=params['element']['content']['expression']['formula']['$']
					
					translatedText=translateText(translator,textToTranslate)				
					print 'final cell translated text' ,translatedText
					payload['element']['content']['expression']['formula']['$']=translatedText
				except :
					print sys.exc_info()[0]	
			

			response=requests.put(updateurl,headers=header,json=payload)

			print(response.text)
			print(saveChanges(docId))	

			
	return 'done' #saveChanges(docId)

documentsToProcess=getDocDtls(docId)

if documentsToProcess:
	for documents in documentsToProcess:
		try:
			reportsList=documents['reports']['report']
			if type(reportsList)!=type([]):
				reportsList=[reportsList]
				
		except KeyError as e:
			print sys.exc_info[0]
 
		for reports in reportsList:

			elementParamList = getAllElementParams(documents['documentId'],getReportElements(documents['documentId'],reports['id']))			
			
			if 	elementParamList:

				updateElementText(docId,translator,elementParamList)

