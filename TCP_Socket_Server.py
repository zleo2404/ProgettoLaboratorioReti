import sys
import os
import logging
import mimetypes
from socket import *

#Configurazione del file di logging
logging.basicConfig(
    filename='log.txt',
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

#Inizializzo il sever sulla porta 8080 e con connessione TCP
HOST, PORT = 'localhost', 8080
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind((HOST, PORT))
serverSocket.listen(1)
logging.info("Server avviato su %s:%d", HOST, PORT)
print(f"[START] Server avviato su {HOST}:{PORT}")

WWW_ROOT = os.path.abspath("www")

while True:
    connectionSocket, addr = serverSocket.accept()
    logging.info("Connessione da %s", addr)
    print(f"[CONNECT] {addr}")

    try:
        request = connectionSocket.recv(1024).decode()
        logging.info("Richiesta:\n%s", request.strip())
        lines = request.splitlines()
        if not lines:
            raise IOError("Richiesta vuota")

        method, path, _ = lines[0].split()
        if method != 'GET':
            raise IOError("Metodo non supportato")

        #Inizializzo il default index e lo slash iniziale
        if path == '/':
            path = '/index.html'
        rel_path = path.lstrip('/')
        full_path = os.path.abspath(os.path.join(WWW_ROOT, rel_path))

        #Controllo per evitare il path traversal
        if not full_path.startswith(WWW_ROOT):
            raise IOError("Accesso non consentito")

        if not os.path.isfile(full_path):
            raise IOError("File non trovato")

        #Lettura file in binario (per esempio utilizzato per le immagini)
        with open(full_path, 'rb') as f:
            body = f.read()

        #Determino il mimetype tramite guess type
        mime_type, _ = mimetypes.guess_type(full_path)
        if not mime_type:
            mime_type = 'application/octet-stream'

        #Rispondo con 200 se non ho riscontrato nessun problema
        header = (
            "HTTP/1.1 200 OK\r\n"
            f"Content-Type: {mime_type}; charset=UTF-8\r\n"
            f"Content-Length: {len(body)}\r\n"
            "Connection: close\r\n"
            "\r\n"
        ).encode('utf-8')

        connectionSocket.sendall(header + body)
        logging.info("200 OK: %s (%s)", rel_path, mime_type)

    except IOError as e:
        #in caso di problemi restituisco 404 Not Found
        logging.warning("404 Not Found: %s", e)
        response_body = b"<html><body><h1>404 Not Found</h1></body></html>"
        header = (
            "HTTP/1.1 404 Not Found\r\n"
            "Content-Type: text/html; charset=UTF-8\r\n"
            f"Content-Length: {len(response_body)}\r\n"
            "Connection: close\r\n"
            "\r\n"
        ).encode('utf-8')
        connectionSocket.sendall(header + response_body)

    except Exception as ex:
        logging.exception("Errore interno: %s", ex)

    finally:
        connectionSocket.close()
        logging.info("Connessione chiusa")
        print(f"[DISCONNECT] {addr}")
