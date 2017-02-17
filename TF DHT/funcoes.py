import hashlib
import json
import binascii
import time

#constantes definem os limites da faixa de portas
START_PORT = 8080
END_PORT = 8090

def iniciaPrimeirosContatos(listaPeers,ip,porta):
	
	#se a porta nao for a de inicio
	if porta != START_PORT:
		pe = Peer()
		pe.myIp = ip
		pe.myPorta = int(porta)-1
		pe.myHash = hashlib.sha256(str(int(myport)-1)).hexdigest()
		listaPeers.append(pe)

	#se a porta nao for a do final
	if porta != END_PORT:
		pd = Peer()
		pd.myIp = ip
		pd.myPorta = int(porta)+1
		pd.myHash = hashlib.sha256(str(int(myport)+1)).hexdigest()
		listaPeers.append(pd)
