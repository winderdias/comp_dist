#!/bin/bash 
 STR="http://localhost:";  for i in `seq 8080 8090`; do  j=$(( i + 1 )) ;  ( python chat1.py $i $STR$j & ) ; done