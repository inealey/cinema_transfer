#!/usr/bin/env python

import socket, select
import traceback
import pickle
from glob import glob
import argparse

"""
some working assumptions:


"""

# ## environment
# INPATH = '/mnt/d/cinema_stream_debug/can_5_steps.cdb'

def txt_query(sock, msg):
    """
    sock: socket to read/write from
    msg: message to send
    returns: 16 byte response from server
    """
    sock.sendall(msg.encode())
    response = sock.recv(16).decode()
    return response


def main(config):
    try:
        ## init socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (config.host, config.port)
        sock.connect(server_address)

        ## read all files in path into list
        nameList, dataList = ['NAMES'], ['DATA']
        imgFiles = glob(config.input + '/*')
        for img in imgFiles:
            nameList.append(img.split('/')[-1])
            file = open(img, 'rb')
            dataList.append(file.read())
            file.close()

        ## serialize lists
        namePkl = pickle.dumps(nameList)
        dataPkl = pickle.dumps(dataList)

        ## num bytes for each flattened object
        nameSize = len(namePkl)
        dataSize = len(dataPkl)
        

        ## start conversation w server
        response = txt_query(sock, ('NSIZE %s' % nameSize))
        if response:
            active = True
            print('preparing to transfer ' + 
                  str(dataSize / 1000000) + ' MB to ' +
                  config.host + ':' + str(config.port)  )
        else:
            active = False
            print('no response from server')
        
        ## negotiate w server while connection open
        while active:

            if response == 'GOT_NSIZE':
                sock.sendall(namePkl)
                response = sock.recv(16).decode()
                if response != 'GOT_NAMES':
                    active = False
                else:
                    response = txt_query(sock, 'DSIZE %s' % dataSize)

            elif response == 'GOT_DSIZE':
                sock.sendall(dataPkl)
                response = sock.recv(16).decode()
                if response != 'GOT_DATA':
                    active = False
                else:
                    sock.sendall(("DONE").encode())
                    print('images successfully sent to server')
                    active = False
                    
            else:
                print('ERROR: unexpected response:')
                print(response)
                active = False

    except Exception as e:
        print(traceback.format_exc())
        sock.close()

    finally:
        sock.close()

        
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    
    ## socket and path setup
    parser.add_argument('--host', type=str, default='127.0.0.1')
    parser.add_argument('--port', type=int, default=10001)
    parser.add_argument('--input', type=str, default='images')
    
    ## extractor settings
    parser.add_argument('--phi', type=int, default=6)
    parser.add_argument('--theta', type=str, default=6)
    
    ## parse cmd line args and start server
    config = parser.parse_args()
    main(config)