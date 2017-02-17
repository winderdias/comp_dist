<!DOCTYPE html>
<html>
    <head>
		%if defined('titulo'):
			<title> {{ titulo }} </title>
		%else:
			<title> Trabalho Computacao Distribuida</title>
		%end
    </head>
    <body>
		 <h1> Tabela de Peers (Dht) </h1>
		 %if defined('dht'):
			<h2> Hash do Peer: {{ dht[-1]['hash'] }}</h2>
			%i = 0
			%hash = ' '
			%aux = []
			<table border="1">
			<tr>
				<td width="100"> Hash </td> <td width="100"> 0 </td width="100"> <td> 1 </td> <td width="100"> 2</td> <td width="100"> 3 </td>
			</tr>	
			%for linhas in dht:
				%if i < 4:
					%aux.append(linhas)
					%i+=1
					%continue
				%end
				<tr>
				
				<td height="20">{{aux[0]['hash'][:-1]}}</td>
				%for colunas in aux:
					%if colunas['peer'] != None:
						%for j in range(4):
							%if j == int(colunas['hash'][-1]):
								<td height="20" width="100">{{colunas['peer']['port']}}</td>
							%end
						%end
					%else:
						<td height="20" width="100"></td>
						
					%end
					
					%i = 0
				%end
				%del aux[:]
				</tr>
			%end
			</table>
			
			%i = 0
			%for linhas in dht:
				%if i == 4:
					%i = 0
					<br> 
				%end
				%if linhas['peer'] != None:
					<p> <b>{{ id(linhas['peer']) }} {{ linhas['hash'] }} {{ linhas['peer']['moddedHash']}} {{ linhas['peer']['ip']}} {{ linhas['peer']['port']}} {{linhas['peer']['hash']}} </b> </p>
				%else:
					<p> <b>{{ linhas }} </b> </p>
				%end	
				%i+=1
			%end	
		%end
    </body>
</html>
