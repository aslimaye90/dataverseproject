import grpc
import logging
import os
import commands
import random
import sys

sys.path.append('../')
import file_server_pb2
import file_server_pb2_grpc

CHUNK_SIZE = int(1024 * 1024 * 3.9) # 3.99MB

class Client:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        logging.info("initializing GRPC client")

    def _byteStream(self, fileHandle, readUntil):
        while True:
            readFrom = fileHandle.tell()
            read_chunk_size = min(abs(readUntil - readFrom), CHUNK_SIZE)
            chunk = fileHandle.read(read_chunk_size)
            if not chunk:
                break
            yield file_server_pb2.Chunk(chunk=chunk)
    
    def upload(self, uploadedFile, grpcServerIP, readUntil, chunkName):
        logging.info("within GRPC client upload")  
        try:
            stub=self._connect(grpcServerIP)
            chunks_generator = self._byteStream(uploadedFile, readUntil)
            metadata = (('filename', chunkName),)
            response = stub.Upload(chunks_generator, metadata=metadata)
            return response.success
        except Exception as e:
            logging.warning("%s",str(e))

    def download(self, filename, grpcServerIP, fileHandle):
        logging.info("within GRPC client download")
        try:
            stub=self._connect(grpcServerIP)
            response = stub.Download(file_server_pb2.Name(name=filename))
            if fileHandle is not None:
                for chunk in response:
                    fileHandle.write(chunk.chunk)
                logging.info("Successfully downloaded chunk %s Exiting GRPC client download", filename)
                return True
            logging.warning("GRPC client fail download")    
            return False
        except Exception as e:
            logging.warning("%s",str(e))
            return False
    
    # Gets the list of GRPC Servers ports running as
    def _getAllNodes(self):
        list_of_ps = os.popen("ps -eaf|grep grpc_server").read().split('\n')
        output = [i for i in list_of_ps if "python" in i]
        i=0
        portList =[]
        while i<len(output):
            temp = output[i].split(' ')
            portList.append(temp[len(temp)-1])
            logging.info("GRPC servers on port %s",str(temp[len(temp)-1]))
            i=i+1
        return portList
    
    # connect to given GRPC server
    def _connect(self, grpcServerIP):
        # Move the host selection logic next 2 lines to Consistent Hash algorithm
        # ports = self._getAllNodes()
        # portNumber=random.choice(ports)
        logging.info("connecting to grpc server at %s", grpcServerIP)
        channel = grpc.insecure_channel(grpcServerIP)
        stub = file_server_pb2_grpc.FileServiceStub(channel)
        return stub