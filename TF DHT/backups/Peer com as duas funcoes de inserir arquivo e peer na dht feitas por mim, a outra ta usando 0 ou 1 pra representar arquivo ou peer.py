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
#os peers normais, que nao oferecem nem baixam, tem portas na faixa START_PORT - END_PORT
#o peer de oferta tem contato inicial com o ultimo peer, ou seja, com o peer cuja porta eh END_PORT
#o peer de download tem porta configurada em: DOWN_PORT
START_PORT = 8080
END_PORT = 8099
DOWN_PORT = 8101
OFFER_PORT = 8100

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
	 
	 def insereArquivoDht(self,remetente,pHash):
		 
		#verifica se hash ja esta na lista
		for i in self.tableFiles:
			if(i['peer'] != None):
				if(i['peer']['hash'] == remetente["hashArquivo"]):
					return False
	
		#faz o hash mod 4 do arquivo remetente
		rModdedHash = hashMod(remetente['hashArquivo'])
		#print rModdedHash 
		myModdedHash = hashMod(pHash)
		
		pos = 0
		for i in range(len(myModdedHash)):
			if (myModdedHash[i] == rModdedHash[i]):
				pos+=1
			else: 
				break
			
		if(pos == 0):
			for linha in self.tableFiles:
				#se o primeiro char do hash do remetente for 0,1,2,3
				if (linha['hash'] == rModdedHash[0]):
					# se espaco livre, insere
					if (linha['peer'] == None):
						#insere na lista
						remetente['moddedHash'] = rModdedHash
						linha['peer'] = copy.deepcopy(remetente)
						print "inserido na Dht de arquivos",linha['peer']['port']
						return True
					else:
						print "bloqueado"
						return False
			return False
		
		parecidos = []	
		temp = ''
		
		for i in range(pos+1):
			temp = temp + rModdedHash[i]
			for linha in self.tableFiles: # percorre toda lista atras da mesma parte do hash
				if(linha['hash'] == temp):
					parecidos.append(linha)
					
		for linha in parecidos[::-1]:
			if(linha['peer'] == None):
				#vai inserir na peer na posicao da dht
				remetente['moddedHash'] = rModdedHash
				linha['peer'] = copy.deepcopy(remetente)
				print "inserido na Dht ",linha['peer']['port']
				return True
		return False
		
	 def inserePeerDht(self,remetente,pHash):
		rModdedHash = self.hashMod(remetente['hash'])
		myModdedHash = self.hashMod(pHash)
		pos = 0
		
		#retorna falso se ja possui peer na tabela dht
		for linha in self.tablePeers:
			# procura por linhas ocupadas
				if (linha['peer'] != None): 
					if int(linha['peer']['port']) == int(remetente['port']):
						return False
						
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
		
		parecidos = []	
		temp = ''
		for i in range(pos+1):
			temp = temp + rModdedHash[i]
			for linha in self.tablePeers: # percorre toda lista atras da mesma parte do hash
				if(linha['hash'] == temp):
					parecidos.append(linha)
						
		for linha in parecidos[::-1]:
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
		if porta != END_PORT and porta != OFFER_PORT:
			pd = Peer(ip,porta)
			pd.myIp = ip
			pd.myPorta = porta+1
			pd.myHash = hashlib.sha256(str(porta+1)).hexdigest()
			listaPeers.append(pd)

@route('/dhtPeers/')
def dht():
	return template('indexPeers',titulo='Dht Peers',dht=p.myDht.tablePeers)

@route('/dhtArquivos/')
def dht():
	return template('indexArquivos',titulo='Dht Arquivos',dht=p.myDht.tableFiles)
	
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
		#se meu contato nao for eu mesmo
		if i.myPorta == DOWN_PORT and p.myPorta == OFFER_PORT: 
			continue
			
		if i.myPorta != p.myPorta:	
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
				
	time.sleep(3)	
					
@route('/addPeers/')
def addPeers():
	
	while(True):
		requestPeers(p)

def hashArquivo(nomeArq):
	BLOCKSIZE = 1024
	hasher = hashlib.sha256()
	with open(nomeArq, 'rb') as afile:
		buf = afile.read(BLOCKSIZE)
		while len(buf) > 0:
			hasher.update(buf)
			buf = afile.read(BLOCKSIZE)
			
	return hasher.hexdigest()

@route('/recebeOferta/')
def recebeOferta():
	remetente = request.query.decode();
	#insere peer que mandou oferta na dht, caso nao existir ainda
	if p.myDht.adicionaListaPeer({'ip':remetente['ip'],'port':remetente['port'],'hash':remetente['hash']},p):
		#se conseguir adicionar na lista, tenta adicionar na dht
		if not p.myDht.inserePeerDht({'ip':remetente['ip'],'port':remetente['port'],'hash':remetente['hash']},p.myHash):
			#se nao conseguir adicionar na dht, remove da lista
			p.myDht.removePeerLista(p.myDht.myPeers,remetente['hash'])
	
	
	
	
def forneceArquivo():
	while(True):
		requestPeers(p)
		
		# nome do arquivo a ser hasheado
		arquivo = "uffs.jpg" 
		hashArq = hashArquivo(arquivo)
		
		payload = {}
		payload['ip'] = p.myIp
		payload['port'] = p.myPorta
		payload['hash'] = p.myHash
		payload['hashArquivo'] = hashArq
		
		#especifica porta do peer que vou oferecer o arquivo
		destinoPort = 8081
		
		try:
			r = requests.get('http://localhost:'+str(destinoPort)+'/recebeOferta/',params=payload);
			print "enviado com sucesso ",payload
		except requests.exceptions.RequestException as e:
			print "erro no envio da oferta",e
			pass
			
#Seta os atributos do Peer
p = Peer(sys.argv[1],sys.argv[2])
#adiciona dois contatos iniciais a lista de Peers (Porta +- 1)
#inicia tabela dht
d = Dht()

p.setFirstContacts(d.myPeers,p.myIp,p.myPorta)
p.myDht = d
#seta tabela dht do peer
d.constroiDhtPeers(p)

if p.myPorta >= START_PORT and p.myPorta <= END_PORT:
	t1 = Thread(target=addPeers)
	t1.start()

if p.myPorta == OFFER_PORT:
	t2 = Thread(target=forneceArquivo)
	t2.start()
	
#t = Thread(target=checkPeers)
#t.start()

run(host=p.myIp, port=p.myPorta)
