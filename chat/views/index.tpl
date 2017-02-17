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
		 %if defined('msg'):
			%for mensagens in msg:
			<p> <b>{{ mensagens[0] }} </b>enviou: {{ mensagens[1] }} </p>
			%end	
		%end	
		<h1> Envie uma mensagem </h1>
       
        <form action="/chat/" method="post">
			Usuario: <input name="usuario" type="text" />
            Mensagem: <input name="mensagem" type="text" />
            <input value="Enviar" type="submit" />
        </form>
    </body>
</html>
