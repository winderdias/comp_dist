#!/bin/bash
for i in `seq 8080 8092`;  do ( python Peer.py localhost  $i & ) ;  done
