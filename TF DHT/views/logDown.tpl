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
		 <h1> Log de Download </h1>
		 %if defined('log'):
			%for linhas in log:
				<p> <b> {{ linhas }} </b> </p>
			%end
		 %end
    </body>
</html>
