from bottle import route, run, template, request
import sys
import requests
import json
import threading
import time

class Peer:
	msgs = None
	vizinhos = None
	porta = None
	myUrl = None
	
	def __init__(self):
		self.msgs = []
		self.vizinhos = sys.argv[2:]
		self.porta = sys.argv[1]
		self.myUrl = 'http://localhost:'+self.porta;  
		
p = Peer()

#vizinhos = ["http://localhost:"+str(int(porta)+1)]

@route('/chat/')
def chat():
	return template('index',titulo='T1 CHAT',msg=p.msgs)

@route('/chat/', method = 'POST')
def chat():
	usuario = request.forms.get('usuario');
	p.msgs.append([usuario,request.forms.get('mensagem')]);
	
	return template('index',msg=p.msgs,titulo='T1 CHAT')
	
@route('/getMsgs/')
def getMsgs():
	time.sleep(3)
	print p.msgs
	return json.dumps(p.msgs)

@route('/updateMsgs/')
def updateMsgs():
	time.sleep(3)
	
	print "true"
	for n in p.vizinhos:
		print n
		if n != p.myUrl:
			#se a url esta ativa
			try:
				r = requests.get(n+'/getMsgs/');			
				v = json.loads(r.text);
				for mensagem in v:
					print mensagem
					if mensagem not in p.msgs:
						p.msgs.append(mensagem)
				
			except requests.exceptions.RequestException:
				pass
		
@route('/getVizinhos/')
def getVizinhos():
	
	"""recebe url parametro do get """
	urls = request.query.decode();
	for key,value in urls.items():
		print key,value
	#Adiciona os vizinhos recebidos a sua propria lista
	for key, value in urls.items():
		if value not in p.vizinhos:
			p.vizinhos.append(value);
				
	print p.vizinhos;	
	#retorna os vizinhos
	return json.dumps(p.vizinhos);
	
@route('/updateVizinhos/')
def updateVizinhos():
	time.sleep(3)
	### dicionario usado para enviar os vizinhos por GET
	payload = {};
	
	if p.myUrl not in p.vizinhos:
		p.vizinhos.append(p.myUrl);

	for n in p.vizinhos:
		port = n.rpartition(':');
		### payload [porta] = endereco/porta
		payload [port[2]] = n;
	
	while True:
		time.sleep(3)
		for n in p.vizinhos:
			if n != p.myUrl:
				#se a url esta ativa
				try:
					r = requests.get(n+'/getVizinhos/',params=payload);			
					v = json.loads(r.text);
					#adiciono ao fim da lista os novos vizinhos
					for endereco in v:
						if endereco not in p.vizinhos:
							p.vizinhos.append(endereco)
				
				except requests.exceptions.RequestException:
					pass
		updateMsgs()
#run(host='localhost', port=sys.argv[1])

t = threading.Thread(target=updateVizinhos)
t.start()
#t2 = threading.Thread(target=sync_msgs)
#t2.start()

run(host='localhost', port=p.porta)
