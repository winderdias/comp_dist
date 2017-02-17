from bottle import route, run, request, redirect, view, get, template
import sys
import requests
import json
from threading import Thread
import hashlib
import time
import binascii
import copy
#constantes definem os limites da faixa de portas
START_PORT = 8080
END_PORT = 8099
DOWN_PORT = 8101
class Dht:
	 #linhas da tabela
	 tablePeers = None
	 tableFiles = None
	 myPeers = None
	 
	 def __init__(self):
		 self.tablePeers = []
		 self.tableFiles = []
		 self.myPeers = []
		 
	 def constroiDhtPeers(self,p):
		myPeers = p.myDht.myPeers
		myHash = p.myHash
		buffHash = ''
		moddedHash = self.hashMod(myHash)
		cont = 0
		
		for i in range(len(moddedHash)+1):
			for j in range(4):
				self.tablePeers.append({"hash": buffHash + str(j), "peer": None})
				self.tableFiles.append({"hash": buffHash + str(j), "peer": None})
				
			buffHash = buffHash + moddedHash[int(cont)]
			if(i < len(moddedHash)-1): cont+=1	
			
		#insere os vizinhos iniciais na Dht
		for vizinho in myPeers:
			remetente = {}
			remetente['ip'] = vizinho.myIp
			remetente['port'] = vizinho.myPorta
			remetente['hash'] = vizinho.myHash
		
			p.myDht.inserePeerDht(remetente,p.myHash)
	 
	 def removePeerLista(self,listaPeers,myHash):
		for i in listaPeers:
			if i.myHash == myHash:
				listaPeers.remove(i)
				print "objeto removido ",i.myPorta
	 def removePeerDht(self,myHash):
		#remove peer i da dht		
		for linhaDht in self.tablePeers:
			if linhaDht['peer'] != None:
				print "tentando remover: ",linhaDht ['peer']['hash'],myHash
				if linhaDht ['peer']['hash'] == myHash:
					print "removido: ",linhaDht ['peer']['hash']
					linhaDht ['peer'] = None  
		
	 def inserePeerDht(self,remetente,pHash):
		rModdedHash = self.hashMod(remetente['hash'])
		myModdedHash = self.hashMod(pHash)
		pos = 0
		
		#procura pela posicao onde os hash se diferem
		for i in range(len(myModdedHash)):
			if (myModdedHash[i] == rModdedHash[i]):
				pos+=1
			else: 
				break
		
		print "estou na inserePeerDht remetente[porta]: ",remetente['port'],pos		
		#se os primeiros numeros nao batem, tenta inserir na primeira linha
		if(pos == 0):
			for linha in self.tablePeers:
				#se o primeiro char do hash do remetente for 0,1,2,3
				if (linha['hash'] == rModdedHash[0]):  
					# espaco livre, insere
					if (linha['peer'] == None): 
						#insere na lista
						remetente['moddedHash'] = rModdedHash
						linha['peer'] = copy.deepcopy(remetente)
						print "inserido na Dht",linha['peer']['port']
						return True
					else:
						print "bloqueado"
						return False
			return False
		
		#senao vai continuar e faz a verificacao ate o numero cont de caracteres do hash iguais		
		temp = ''
		for i in range(pos+1):
			temp = temp + rModdedHash[i]
			for linha in self.tablePeers: # percorre toda lista atras da mesma parte do hash
				if(linha['hash'] == temp):
					if(linha['peer'] == None):
						#vai inserir na peer na posicao da dht
						remetente['moddedHash'] = rModdedHash
						linha['peer'] = copy.deepcopy(remetente)
						print "inserido na Dht ",linha['peer']['port']
						return True
		return False
	 def hashMod(self,hashStr):
		buff = binascii.unhexlify(hashStr)
		strF = ''
		
		for i in buff:
			k = ord(i) % 4
			strF = strF + str(k)
		
		return strF
	
	 def adicionaListaPeer(self,remetente,p):
		listaPeers = p.myDht.myPeers
		
		if int(remetente['port']) == p.myPorta:
			return False
			
		for i in listaPeers:
			if (i.myPorta == int(remetente['port'])):
				return False
		
		for i in listaPeers:
			print "o que eu quero inserir eh ",remetente['port'], "minha lista eh ",i.myPorta
		
		try:
			r = requests.get('http://'+remetente['ip']+':'+str(remetente['port'])+'/');			
		#host nao ta online nao adiciona	
		except requests.exceptions.RequestException as e:			
			return False
			
		copia = copy.deepcopy(remetente)
		#adiciona peers#
		#se ainda nao possui o peer em sua lista
		#seta parametros do objeto para o novo peer
		pn = Peer(copia['ip'],copia['port'])
		pn.myHash = copia ['hash']
		
		#adiciona remetente a lista de peers
		p.myDht.myPeers.append(pn)
		return True
		
class Peer:
	myPorta = None
	myIp = None
	myHash = None
	myDht = None
	
	def __init__(self,ip,porta):
		self.myPorta = int(porta)
		self.myIp = ip
		self.myHash = hashlib.sha256(str(self.myPorta)).hexdigest()
		self.myPeers = []
			
	def setFirstContacts(self,listaPeers,ip,porta):
		#se a porta nao for a de inicio
		if porta != START_PORT:
			pe = Peer(ip,porta)
			pe.myIp = ip
			pe.myPorta = porta-1
			pe.myHash = hashlib.sha256(str(porta-1)).hexdigest()
			listaPeers.append(pe)
	
		#se a porta nao for a do final
		if porta != END_PORT:
			pd = Peer(ip,porta)
			pd.myIp = ip
			pd.myPorta = porta+1
			pd.myHash = hashlib.sha256(str(porta+1)).hexdigest()
			listaPeers.append(pd)

@route('/dht/')
def dht():
	return template('index',titulo='Dht',dht=p.myDht.tablePeers)
	
@route('/returnPeers/')
def returnPeers():
	remetente = request.query.decode();
	#se nao tem peer na lista, tenta adicionar
	if p.myDht.adicionaListaPeer({'ip':remetente['ip'],'port':remetente['port'],'hash':remetente['hash']},p):
		#se conseguir adicionar na lista, tenta adicionar na dht
		if not p.myDht.inserePeerDht({'ip':remetente['ip'],'port':remetente['port'],'hash':remetente['hash']},p.myHash):
			#se nao conseguir adicionar na dht, remove da lista
			p.myDht.removePeerLista(p.myDht.myPeers,remetente['hash'])
			
	return json.dumps([ob.__dict__ for ob in p.myDht.myPeers]);


def requestPeers(p):
	
	payload = {}
	
	for i in p.myDht.myPeers:
		if i.myPorta != p.myPorta and i.myPorta != DOWN_PORT:	
			payload['ip'] = p.myIp
			payload['port'] = p.myPorta
			payload['hash'] = p.myHash
			
			try:
				r = requests.get('http://'+i.myIp+':'+str(i.myPorta)+'/returnPeers/',params=payload);			
				v = json.loads(r.text);
				for dictLine in v:
					for i in p.myDht.myPeers:
						print "recebi os vizinhos ",dictLine['myPorta'],"tenho na minha lista ",i.myPorta
				for dictLine in v:
					#se nao tem peer na lista, tenta adicionar
					if p.myDht.adicionaListaPeer({'ip':dictLine['myIp'],'port':dictLine['myPorta'],'hash':dictLine['myHash']},p): # se ip nao esta na listapeers adiciona peers
						#se conseguir adicionar na lista, tenta adicionar na dht
						if not p.myDht.inserePeerDht({'ip':dictLine['myIp'],'port':int(dictLine['myPorta']),'hash':dictLine['myHash']},p.myHash):
							#se nao conseguir adicionar na dht, remove da lista
							p.myDht.removePeerLista(p.myDht.myPeers,dictLine['myHash'])
					for i in p.myDht.myPeers:
						print "minhaLista: ",i.myPorta
			except requests.exceptions.RequestException as e:
				print e
				#remove da lista de peers, exceto vizinhos
				#if i.myPorta != p.myPorta - 1 and i.myPorta != p.myPorta+1:
				p.myDht.removePeerDht(i.myHash)
				p.myDht.myPeers.remove(i)
					
	time.sleep(2)	
					
@route('/addPeers/')
def addPeers():
	
	while(True):
		requestPeers(p)
	
	print "saiu fora wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww"	
'''def forneceArquivo(listaPeers,meusDados):
	while(True):
		requestPeers(p)
		#modificar depois
		arq = "teste1.rar" # inserir um hash para como sendo do arquivo aqui
		hashArquivo = func.hashDoArquivo(arq) #opcional
		address = ("localhost", 5001) # Oferece pro o servidor/cliente com porta 5001
		client_socket = socket(AF_INET, SOCK_DGRAM)
		data = { "tag": "OfferFile",
				"offerOwner": {"ip": meusDados['ip'], "port": meusDados['port'], "hash": meusDados["hash"]},
				"offerHash": hashArquivo # hash de algum arquivo
				}
		client_socket.sendto(json.dumps(data), address)'''

def checkPeers():
	while(1):
		portasExistes = [ob.myPorta for ob in p.myDht.myPeers] 
		print "as portas sao essas : ",portasExistes
		if len(portasExistes) != len(set(portasExistes)):
			print "ACHEEEEEEEEEEEEEEEEEEEEEEEEEEEEI",p.myPorta
			exit(1)
#Seta os atributos do Peer
p = Peer(sys.argv[1],sys.argv[2])
#adiciona dois contatos iniciais a lista de Peers (Porta +- 1)
#inicia tabela dht
d = Dht()

p.setFirstContacts(d.myPeers,p.myIp,p.myPorta)
p.myDht = d
#seta tabela dht do peer
d.constroiDhtPeers(p)

t2 = Thread(target=addPeers)
t2.start()
t = Thread(target=checkPeers)
t.start()

run(host=p.myIp, port=p.myPorta)
