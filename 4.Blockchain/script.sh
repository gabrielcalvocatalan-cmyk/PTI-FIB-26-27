#!/bin/bash
pkill -f blockchain.py
python3 blockchain.py -p 5000 &
python3 blockchain.py -p 5001 &
sleep 3

# Dos transacciones en el nodo 1
curl -X POST -H "Content-Type: application/json" -d '{"sender":"A","recipient":"B","amount":8,"order":1}' http://localhost:5000/transactions/new
curl -X POST -H "Content-Type: application/json" -d '{"sender":"B","recipient":"C","amount":5,"order":2}' http://localhost:5000/transactions/new

# Nodo 1: 3 bloques
curl http://localhost:5000/mine
curl http://localhost:5000/chain
curl http://localhost:5000/mine
curl http://localhost:5000/chain
curl http://localhost:5000/mine
curl http://localhost:5000/chain

# Nodo 2: 2 bloques
curl http://localhost:5001/mine
curl http://localhost:5001/mine
curl http://localhost:5001/chain

# Registro mutuo
curl -X POST -H "Content-Type: application/json" -d '{"nodes":"http://localhost:5001"}' http://localhost:5000/nodes/register
curl -X POST -H "Content-Type: application/json" -d '{"nodes":"http://localhost:5000"}' http://localhost:5001/nodes/register

# Consenso
curl http://localhost:5000/nodes/resolve
curl http://localhost:5001/nodes/resolve
curl http://localhost:5001/chain