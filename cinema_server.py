#!/usr/bin/env python

import os
import socket, select
import traceback
import pickle
import argparse


def generate_csv(path, steps, phi, theta):
    """
    path: path to new cinema db
    steps: number of timesteps in sim
    phi: cinema phi resolution
    theta: cinema theta resolution
    
    overwrites existing data.csv
    for now, assumes file names follow the convention below
    """
    fname_template = 'RenderView1_{}p={:06.2f}t={:06.2f}.png'
    phi_step = 360 / phi
    theta_step = 360 / theta
    
    file = open(path + '/data.csv', 'wt')
    file.write('time,phi,theta,FILE\n')
    for s in range(steps):
        for p in range(phi):
            for t in range(theta):
                file.write('{:.1f}'.format(s) + 
                           ',' + 
                           '{:.2f}'.format(p * phi_step) + 
                           ',' + 
                           '{:.2f}'.format(t * theta_step) + 
                           ',' + 
                           fname_template.format(str(s).zfill(6), 
                                p * phi_step, t * theta_step) + '\n'
                           )
    file.close()
    return True
    

def recv_object(sock, initial, size):
    """
    sock: socket to read from
    initial: bytes in object already recieved 
    size: total length of flattened object to recieve
    returns: unserialized object
    (for now, assuming data from a single timestep fits into memory)
    """
    objPkl = []
    objPkl.append(initial)
    received = len(initial)
    while received < size:
        msg  = sock.recv(4096)
        received += len(msg)
        objPkl.append(msg)
    return pickle.loads(b"".join(objPkl))
    

def main(config):
    """
    initialize socket, wait for connection from client
    """
    connected_clients_sockets = []
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((config.host, config.port))
    server_socket.listen(10)
    connected_clients_sockets.append(server_socket)
    
    ## generate data.csv file for cinema database
    if os.path.isfile(config.output + '/data.csv'):
        print('found existing database file: ' + config.output + '/data.csv')
    else:
        print('generating cinema description: ' + config.output + '/data.csv')
        generate_csv(config.output, config.timesteps, config.phi, config.theta)
    
    ## main loop
    while True:
        read_sockets, write_sockets, error_sockets = select.select(connected_clients_sockets, [], [])
        for sock in read_sockets:
            ## check if server
            if sock == server_socket:
                sockfd, client_address = server_socket.accept()
                connected_clients_sockets.append(sockfd)
            else:
                try:
                    ## read from socket
                    data = sock.recv(4096)

                    if data:
                        ## check if getting name size
                        if data.startswith(b'NSIZE'):
                            nameSize = int(data.decode().split()[1])

                            ## confirm name size recieved
                            sock.sendall(("GOT_NSIZE").encode())

                        ## check if getting data size
                        elif data.startswith(b'DSIZE'):
                            dataSize = int(data.decode().split()[1])

                            ## confirm data size recieved
                            sock.sendall(("GOT_DSIZE").encode())

                        ## retrieve file names
                        elif 'NAMES' in str(data[:22]):                         
                            ## get list of filenames from client
                            nameList = recv_object(sock, data, nameSize)
                            nameList.remove('NAMES')
                            sock.sendall(("GOT_NAMES").encode())

                        ## retrieve image data
                        elif 'DATA' in str(data[:22]):
                            ## get list of files from client
                            dataList = recv_object(sock, data, dataSize)
                            dataList.remove('DATA')
                            sock.sendall(("GOT_DATA").encode())

                            ## write image data
                            for i in range(len(dataList)):
                                file = open(config.output + '/' + nameList[i], 'wb')
                                file.write(dataList[i])
                                file.close()

                            print('wrote ' + str(dataSize / 1000000) + ' MB to: ' + config.output + '.')
                            
                            
                        ## close socket if done
                        elif data.startswith(b'DONE'):
                            sock.shutdown(socket.SHUT_RDWR)
                            
                        else:
                            print('ERROR: unexpected message from client')
                            break
                            
                except Exception as e:
                    print(traceback.format_exc())
                    sock.close()
                    connected_clients_sockets.remove(sock)
                    continue
                    
    server_socket.close()
    ## end main ##

    
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    
    ## socket and path settings
    parser.add_argument('--host', type=str, default='127.0.0.1')
    parser.add_argument('--port', type=int, default=10001)
    parser.add_argument('--output', type=str, default='output',
                       help='path to write cinema database')
    
    ## extractor settings
    parser.add_argument('--timesteps', type=int, default=10,
                       help='total number of timesteps in simulation')
    parser.add_argument('--phi', type=int, default=6,
                       help='phi resolution of extractor')
    parser.add_argument('--theta', type=int, default=6,
                       help='theta resolution of extractor')
    
    ## parse cmd line args and start server
    config = parser.parse_args()
    main(config)
    
# reference: https://codereview.stackexchange.com/questions/156704/network-protocol-using-tcp-sending-images-through-sockets
