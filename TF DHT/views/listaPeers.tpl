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
		 <h1> Lista Peers </h1>
		 %if defined('listaPeers'):
			%for linhas in listaPeers:
				<p> <b>{{ linhas.myPorta }} </b> </p>
			%end
		 %end
    </body>
</html>
