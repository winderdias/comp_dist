from bottle import route, run, request, redirect, view, get, template
import sys
import requests
import json
from threading import Thread
import hashlib
import time
import binascii
import copy
import glob
#constantes definem os limites da faixa de portas
#os peers normais, que nao oferecem nem baixam, tem portas na faixa START_PORT - END_PORT
#o peer de oferta tem contato inicial com o ultimo peer, ou seja, com o peer cuja porta eh END_PORT
#o peer de download tem porta configurada em: DOWN_PORT
START_PORT = 8080
END_PORT = 8090
DOWN_PORT = 8092
OFFER_PORT = 8091
logDownload = []
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
		
			p.myDht.inserePeerArquivoDht(remetente,p.myHash,0)
	 
	 def verificaSeArquivoExiste(self,hashArquivo,p):
		 
		 for linha in p.myDht.tableFiles:
			if linha['peer'] != None:
				if (linha['peer']['hashArquivo'] == hashArquivo):
					return True
			
		 return False
	 
	 def removePeerLista(self,listaPeers,myHash):
		for i in listaPeers:
			if i.myHash == myHash:
				listaPeers.remove(i)
				#print "objeto removido ",i.myPorta
				
	 def removePeerDht(self,myHash):
		#remove peer i da dht		
		for linhaDht in self.tablePeers:
			if linhaDht['peer'] != None:
				#print "tentando remover: ",linhaDht ['peer']['hash'],myHash
				if linhaDht ['peer']['hash'] == myHash:
					#print "removido: ",linhaDht ['peer']['hash']
					linhaDht ['peer'] = None
		
	 #insere Peer ou Arquivo na DHT
	 #escolha = 0 -> Peer
	 #escolha = 1 -> Arquivo	
	 def inserePeerArquivoDht(self,remetente,pHash,escolha):
		if escolha == 0: 
			rModdedHash = self.hashMod(remetente['hash'])
			myModdedHash = self.hashMod(pHash)
			lista = self.tablePeers
			
		if escolha == 1:	
			#faz o hash mod 4 do arquivo remetente
			rModdedHash = self.hashMod(remetente['hashArquivo'])
			##print rModdedHash 
			myModdedHash =self.hashMod(pHash)
			lista = self.tableFiles
			
		pos = 0
		
		#retorna falso se ja possui peer na tabela dht
		for linha in lista:
			# procura por linhas ocupadas
				if (linha['peer'] != None):
					if escolha == 0:
						#se for um peer a ser inserido na dht de peers, compara se ja existe a porta na dht
						if int(linha['peer']['port']) == int(remetente['port']):
							return False
					#se for um arquivo a ser inserido, compara o hash do arquivo pra ver se existe
					if escolha == 1:
						if linha['peer']['hashArquivo'] == remetente['hashArquivo']:
							return False
								
		#procura pela posicao onde os hash se diferem
		for i in range(len(myModdedHash)):
			if (myModdedHash[i] == rModdedHash[i]):
				pos+=1
			else: 
				break
		
		#print "estou na inserePeerArquivoDht remetente[porta]: ",remetente['port'],pos		
		#se os primeiros numeros nao batem, tenta inserir na primeira linha
		if(pos == 0):
			for linha in lista:
				#se o primeiro char do hash do remetente for 0,1,2,3
				if (linha['hash'] == rModdedHash[0]):  
					# espaco livre, insere
					if (linha['peer'] == None): 
						#insere na lista
						remetente['moddedHash'] = rModdedHash
						linha['peer'] = copy.deepcopy(remetente)
						#print "inserido na Dht",linha['peer']['port']
						return True
					else:
						#print "bloqueado"
						return False
			return False
		
		parecidos = []	
		temp = ''
		for i in range(pos+1):
			temp = temp + rModdedHash[i]
			for linha in lista: # percorre toda lista atras da mesma parte do hash
				if(linha['hash'] == temp):
					parecidos.append(linha)
						
		for linha in parecidos[::-1]:
			if(linha['peer'] == None):
				#vai inserir na peer na posicao da dht
				remetente['moddedHash'] = rModdedHash
				linha['peer'] = copy.deepcopy(remetente)
				#print "inserido na Dht ",linha['peer']['port']
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
		
		#for i in listaPeers:
			#print "o que eu quero inserir eh ",remetente['port'], "minha lista eh ",i.myPorta
			
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
	arquivosOferecidos = None
	
	def __init__(self,ip,porta):
		self.myPorta = int(porta)
		self.myIp = ip
		self.myHash = hashlib.sha256(str(self.myPorta)).hexdigest()
		self.myPeers = []
		self.arquivosOferecidos = []
		
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
def dhtPeers():
	return template('indexPeers',titulo='Dht Peers',dht=p.myDht.tablePeers)

@route('/dhtArquivos/')
def dhtArquivos():
	return template('indexArquivos',titulo='Dht Arquivos',dht=p.myDht.tableFiles)
	
@route('/listaPeers/')
def listaPeers():
	return template('listaPeers',titulo='Lista de peers',listaPeers=p.myDht.myPeers)

@route('/logDown/')
def logDown():
	return template('logDown',titulo='Log de Download',log=logDownload)
	
@route('/returnPeers/')
def returnPeers():
	remetente = request.query.decode();
	#se nao tem peer na lista, tenta adicionar
	if p.myDht.adicionaListaPeer({'ip':remetente['ip'],'port':remetente['port'],'hash':remetente['hash']},p):
		#se conseguir adicionar na lista, tenta adicionar na dht
		if not p.myDht.inserePeerArquivoDht({'ip':remetente['ip'],'port':remetente['port'],'hash':remetente['hash']},p.myHash,0):
			#se nao conseguir adicionar na dht, remove da lista
			p.myDht.removePeerLista(p.myDht.myPeers,remetente['hash'])
			
	return json.dumps([ob.__dict__ for ob in p.myDht.myPeers]);


def requestPeers(p):
	
	payload = {}
	
	for i in p.myDht.myPeers:
		if i.myPorta == DOWN_PORT and p.myPorta == OFFER_PORT: 
			continue
			
		if i.myPorta != p.myPorta:
			
			payload['ip'] = p.myIp
			payload['port'] = p.myPorta
			payload['hash'] = p.myHash
			
			try:
				r = requests.get('http://'+i.myIp+':'+str(i.myPorta)+'/returnPeers/',params=payload);			
				v = json.loads(r.text);
				#for dictLine in v:
					#for i in p.myDht.myPeers:
						#print "recebi os vizinhos ",dictLine['myPorta'],"tenho na minha lista ",i.myPorta
				for dictLine in v:
					#se nao tem peer na lista, tenta adicionar
					if p.myDht.adicionaListaPeer({'ip':dictLine['myIp'],'port':dictLine['myPorta'],'hash':dictLine['myHash']},p): # se ip nao esta na listapeers adiciona peers
						#se conseguir adicionar na lista, tenta adicionar na dht
						if not p.myDht.inserePeerArquivoDht({'ip':dictLine['myIp'],'port':int(dictLine['myPorta']),'hash':dictLine['myHash']},p.myHash,0):
							#se nao conseguir adicionar na dht, remove da lista
							p.myDht.removePeerLista(p.myDht.myPeers,dictLine['myHash'])
				
			except requests.exceptions.RequestException as e:
				#print e
				#remove da lista de peers, exceto vizinhos
				#if i.myPorta != p.myPorta - 1 and i.myPorta != p.myPorta+1:
				if not (i.myPorta == OFFER_PORT and p.myPorta == DOWN_PORT):
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
		#print "estou na recebeOferta() prestes a enviar pro proximo"
		#se conseguir adicionar na lista, tenta adicionar na dht
		if not p.myDht.inserePeerArquivoDht({'ip':remetente['ip'],'port':remetente['port'],'hash':remetente['hash']},p.myHash,0):
			#se nao conseguir adicionar na dht, remove da lista
			p.myDht.removePeerLista(p.myDht.myPeers,remetente['hash'])
	
	p.myDht.inserePeerArquivoDht({'ip':remetente['ip'],'port':remetente['port'],'hash':remetente['hash'],'hashArquivo':remetente['hashArquivo'],'donoArquivo':remetente['donoArquivo'],'nomeArquivo':remetente['nomeArquivo']},p.myHash,1)
	
	offerNext(remetente,p)
	
	return
	
#Essa funcao propaga o peer que tem o arquivo para aquele peer da sua lista
#que mais se parece com o hash do arquivo
def offerNext(remetente,p):
	
	numPrefixos = 0
	cont = 0
	vizinho = None
	
	arqModdedHash = p.myDht.hashMod(remetente['hashArquivo'])
	for i in p.myDht.myPeers:
		#para cada peer valido em minha lista
		if (i != None and i.myPorta != OFFER_PORT): 
			vizinhoModdedHash = p.myDht.hashMod(i.myHash)
			#compara char por char do hash do vizinho com o do arquivo
			for j in range(0,len(vizinhoModdedHash)):
				if (vizinhoModdedHash[j] == arqModdedHash[j]): 
					#se os caracteres batem, atualiza o contador
					cont+=1
				else: 
					break
			#armazeno o peer vizinho com prefixos mais parecidos com o do arquivo		
			if (cont>numPrefixos): 
				numPrefixos = cont
				vizinho = i
				
		cont = 0
	
	#Apos achar o vizinho, verifica se voce eh mais parecido com o arquivo do que ele
	cont = 0
	myHash = p.myDht.hashMod(p.myHash)
	for j in range(0,len(myHash)):
		if (arqModdedHash[j] == myHash[j]): 
			cont+=1
		else: 
			break
			
	#se o vizinho nao for mais parecido com o arquivo, retorna sem enviar pro vizinho
	if (cont>numPrefixos):
		return False
		
	#se nao, envia pro vizinho mais parecido com o arquivo
	else:
		if vizinho != None:
			payload = {}
			payload['ip'] = p.myIp
			payload['port'] = p.myPorta
			payload['hash'] = p.myHash
			payload['hashArquivo'] = remetente['hashArquivo']
			payload['nomeArquivo'] = remetente['nomeArquivo']
			payload['donoArquivo'] = remetente['donoArquivo']
			
			try:
				requests.get('http://localhost:'+str(vizinho.myPorta)+'/recebeOferta/',params=payload);
				#print "enviado com sucesso para proximo vizinho",payload
			except requests.exceptions.RequestException as e:
				#print "erro no envio da oferta",e
				return False
		else: 
			return False
	
	return True
	
def forneceArquivo():
	
	while(True):
		requestPeers(p)
		#para todos os arquivos .jpg presentes no diretorio faca:
		for arquivo in glob.glob('*.jpg'):
			# nome do arquivo a ser hasheado
			#arquivo = "uffs.jpg" 
				
			hashArq = hashArquivo(arquivo)
			if hashArq not in p.arquivosOferecidos:
				p.arquivosOferecidos.append(hashArq)
				
			#print arquivo
			payload = {}
			payload['ip'] = p.myIp
			payload['port'] = p.myPorta
			payload['hash'] = p.myHash
			payload['donoArquivo'] = p.myPorta
			payload['hashArquivo'] = hashArq
			payload['nomeArquivo'] = arquivo
			
			#especifica porta do peer que vou oferecer o arquivo
			#o peer com essa porta ainda vai repassar o arquivo pra dois peers mais parecidos, o 8083 e o 8087
			destinoPort = 8080
			try:
				requests.get('http://localhost:'+str(destinoPort)+'/recebeOferta/',params=payload);
				#print "enviado com sucesso ",payload
			except requests.exceptions.RequestException as e:
				#print "erro no envio da oferta",e
				pass
			time.sleep(3)
			
def procuraMaisParecido(hashArquivo,p):
	vizinho = None
	#hash mod 4
	aModdedHash = p.myDht.hashMod(hashArquivo)
	maisParecido = 0
	cont = 0
	for peer in p.myDht.myPeers:
		if peer != None and peer.myPorta != DOWN_PORT:
			vModdedHash = p.myDht.hashMod(peer.myHash)
			for j in range(0,len(aModdedHash)):
				if vModdedHash[j] == aModdedHash[j]: 
					cont = cont + 1
				else: 
					break
		#se o vizinho for mais parecido, seta o como mais parecido
		if (cont > maisParecido or maisParecido == 0):
			maisParecido = cont
			vizinho = peer # mais proximo
		cont = 0
	
	return vizinho

@route('/getDownloadRequest/')
def getDownloadRequest():
	remetente = request.query.decode();
	resposta = {}
	
	for hashArq in p.arquivosOferecidos:
		if remetente['hashArquivo'] == hashArq:
			#arquivo encontrado
			resposta['resposta'] = "ArquivoEncontrado"
			resposta['peer'] = {'ip':p.myIp,'port':p.myPorta,'hash':p.myHash}
			return json.dumps(resposta)
	
	resposta['resposta'] = 'EncaminhaRequisicao'
	resposta['proximoPeer'] = None
	resposta['fonte'] = None
	
	#procura na propria tabela de arquivos para ver se tem o hash do arquivo
	for linha in p.myDht.tableFiles:
		if (linha['peer'] != None):
			if (linha['peer']['hashArquivo'] == remetente['hashArquivo']): 
				resposta['fonte'] = {'ip':linha['peer']['ip'],'port':linha['peer']['donoArquivo'],'hash':linha['peer']['hash']} 
				return json.dumps(resposta)
	
	
	#se nao possuir na propria lista, retorna o peer da sua lista mais parecido com o hash do arquivo
	pParecido = procuraMaisParecido(remetente['hashArquivo'],p)			
	if pParecido != None:
		resposta['proximoPeer'] = {'ip':pParecido.myIp,'port':pParecido.myPorta,'hash':pParecido.myHash}

	return json.dumps(resposta)

#essa funcao faz a comparacao dos hashs dos peers que possuem o arquivo (anterior e o recebido)
def cmpHash(hashAnterior, hashRecebido, hashArquivo):
	#verifica o anterior
	anterior = 0
	recebido = 0
	j = 0
	
	for i in range(len(hashArquivo)):
		if (hashArquivo[i] == hashAnterior[i]): 
			j+=1
		else: 
			break
	
	anterior = j
	
	j = 0
	
	#verifica o recebido hash
	for i in range(len(hashArquivo)):
		if (hashArquivo[i] == hashRecebido[i]): 
			j+=1
		else: 
			break
	
	recebido = j
	
	if (recebido>anterior): 
		return True
	
	else: 
		return False
			
def requisitaDownload():
	
	while True:
		requestPeers(p)
		print "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
		i = 0
	
		time.sleep(4)
		arquivo = 'uffs.jpg'
		hashArq = hashArquivo(arquivo)
		
		if ( p.myDht.verificaSeArquivoExiste(hashArq,p) ):
			continue
		
		pParecido = procuraMaisParecido(hashArq,p)
		
		if pParecido == None:
			continue
		
		#aqui ele encontra o mais proximo da lista dele, que eh o 8087
		vModdedHash = p.myDht.hashMod(pParecido.myHash)
		
		payload = {}
		payload['hashArquivo'] = hashArq
		porta = pParecido.myPorta
		
		#del logDownload[:]
		
		logDownload.append("Envia requisicao de Download para Peer "+porta)
		
		while(True):
			try:
				r = requests.get('http://localhost:'+str(porta)+'/getDownloadRequest/',params=payload);
				print "enviado com sucesso ",payload
				v = json.loads(r.text);
				
				logDownload.append("Envio realizado com sucesso para "+porta)
				
				if v['resposta'] == "ArquivoEncontrado":
					print "********************* Arquivo baixado ************************** ", v['peer']['port']
					logDownload.append("O Peer "+str(porta)+" tinha o arquivo fisico, faz Download e termina")
					break
				
				if v['resposta'] == 'EncaminhaRequisicao':
					if v['fonte'] != None:
						porta = v['fonte']['port']
						vModdedHash = p.myDht.hashMod(hashlib.sha256(str(v['fonte']['port'])).hexdigest())
						logDownload.append("O Peer "+str(porta)+"possuia o hash do arquivo em sua tabela e me devolveu a porta do peer que tem o arquivo fisico")
						continue
							
					if v['proximoPeer'] != None:
						if v['proximoPeer']['port'] == p.myPorta:
							print 'peer mais proximo sou eu'
							logDownload.append("O Peer "+str(porta)+" O arquivo nao pode ser baixado, o peer que mais se parece com o arquivo sou eu, e eu nao tenho o arquivo, ENCERRO!")
							break
				
				
						if cmpHash(vModdedHash,p.myDht.hashMod(v['proximoPeer']['hash']),p.myDht.hashMod(hashArq)):
							print v['proximoPeer']['port'],"CMP HASHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH"
							porta = v['proximoPeer']['port']
							vModdedHash = p.myDht.hashMod(v['proximoPeer']['hash'])
							logDownload.append("O Peer "+str(porta)+" me devolveu a porta"+v['proximoPeer']['port']+" que tem hash MAIS parecido com o hash do arquivo do que eu, ENVIO uma requisicao de download pra essa porta")
						else:
							print pParecido.myPorta, "meu hash ainda eh mais parecido kk CMP HASHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH"
							print pParecido.myPorta,  v['proximoPeer']['port']
							logDownload.append("O Peer "+str(porta)+" me devolveu a porta"+v['proximoPeer']['port']+" que tem hash MENOS parecido com o hash do arquivo do que eu, ENCERRO!")
							break
							
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

if p.myPorta == DOWN_PORT:
	t2 = Thread(target=requisitaDownload)
	t2.start()
	
	
#t = Thread(target=checkPeers)
#t.start()

run(host=p.myIp, port=p.myPorta)
