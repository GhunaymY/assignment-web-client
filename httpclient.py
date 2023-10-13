#!/usr/bin/env python3
# coding: utf-8
# Copyright 2016 Abram Hindle, https://github.com/tywtyw2002, and https://github.com/treedust
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

import sys, socket, re, urllib.parse

def help():
    # Display a help message for using the HTTP client
    print("httpclient.py [GET/POST] [URL]")

class HTTPResponse(object):
    '''
    This class is to represent an HTTP Response Object
    '''
    def __init__(self, code=200, body="",headers={}):
        self.code = code
        self.body = body
        self.headers = headers #Added Headers to be used later on. 

class HTTPClient(object):
    '''
    This class is designed to create an HTTP Client that can connect to web servers to send recieve and process HTTP requests
    '''
    def connect(self, host, port):
        # This function will create a socket and connect to the specified host and port.
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        return None

    def get_code(self, data):
        # Extract and return the response code from the HTTP response. We assume Data is an HTTP Response code.
        response_code = int(data.split()[1])
        return response_code

    def parse_url(self, data):
        # Parse the URL to get object, port, and path
        obj = urllib.parse.urlparse(data) #Using the urlparse function.
        port = obj.port or (80 if obj.scheme == "http" else 443) #Checking for Port.
        path = obj.path or "/" #Checking for Path.
        if obj.query: #Checking for a query.
            path += "?" + obj.query #In the Instance that it does have a query we add it to the path. 
        return obj, port, path #Here we return all the objects we just parsed. 

    def get_headers(self,data):
        # Here we extract and return the response headers from the HTTP response
        end_of_headers = "\r\n\r\n"
        headers = data.split(end_of_headers)[0]
        header_lines = headers.split("\r\n")[1:]  # Skip the HTTP Status line.
        headers_dictionary = {} #Initialize Dictionary
        for line in header_lines:
            parts = line.split(": ")
            if len(parts) == 2:
                key, value = parts
                headers_dictionary[key] = value
        return headers_dictionary

    def get_body(self, data):
        # Extract and return the response body from the HTTP response
        end_of_headers = "\r\n\r\n" #This sequence is to show when the headers will end and the body will start. 
        body = data.split(end_of_headers)[1]
        return body

    def sendall(self, data):
        # Sending the provided data over the socket
        self.socket.sendall(data.encode('utf-8'))

    def close(self):
        # Closing the socket connection
        self.socket.close()

    def recvall(self, sock):
        # Receive and return all data from the socket
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        return buffer.decode('utf-8')

    #The Next Three Functions work together. 

    def get_post_request_sender(self, obj, port, request):
        #Use a try and except block for potential socket errors.
        try:
            # Create a socket and connect to the server
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((obj.hostname, port))
                s.sendall(request.encode()) #Send the request
                response = self.recvall(s) #Receive the response
                if not response:
                    return HTTPResponse(404, "")
                code = self.get_code(response)
                body = self.get_body(response)
                headers = self.get_headers(response)
                return HTTPResponse(code, body,headers) #

        except (socket.error, Exception) as e:
            print(f"Error: {e}")
            return HTTPResponse(500, "Internal Server Error") #Internal Server Error response

    def GET(self, url, args=None):
        # Here we complete the GET request using the parse URL function and the request sender function.
        obj, port, path = self.parse_url(url)
        request = request = "GET " + path + " HTTP/1.1\r\nHost: " + obj.hostname + "\r\nAccept: */*\r\nConnection: Closed\r\n\r\n"
        return self.get_post_request_sender(obj, port, request)

    def POST(self, url, args=None):
        server, port, path = self.parse_url(url) #Parse the URL using the function we created.
        # Initialize variables for the request body, content length, and content type
        request_body = ""
        content_type = ""
        content_length = "0"

        # Check if there is any data to send in the request
        if args:
            request_body = urllib.parse.urlencode(args, doseq=True) #Encode the data
            content_length = str(len(request_body)) #Length of the request body.
            content_type = "\r\nContent-Type: application/x-www-form-urlencoded" #Content type for the request.

        # Build the HTTP request
        request = f"POST {path} HTTP/1.1\r\nHost: {server.hostname}\r\nAccept: */*\r\n \
                    Connection: Closed\r\nContent-Length: {content_length}{content_type}\r\n\r\n{request_body}"
        return self.get_post_request_sender(server, port, request) #Send the POST request


    def command(self, url, command="GET", args=None):
        # Here we process the command with GET being the default
        if command == "POST":
            return self.POST(url, args)
        else:
            return self.GET(url, args)


if __name__ == "__main__":
    client = HTTPClient()
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        print(client.command( sys.argv[2], sys.argv[1] ))
    else:
        print(client.command( sys.argv[1] ))