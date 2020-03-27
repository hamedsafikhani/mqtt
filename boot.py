# Complete project details at https://RandomNerdTutorials.com
#ap mode and after connect to router for connect to broker
#v1
import time
from umqttsimple import MQTTClient
import ubinascii
import machine
from machine import Pin
import micropython
import network
import esp
esp.osdebug(None)
import gc
gc.collect()
try:
  import usocket as socket
except:
  import socket
import re

f = open("config","r")
a = f.read().split(" ")
user =  a[0]
passw =  a[1]
print(user,passw)
ssid = user
password = passw
mqtt_server = '....'# broker addr1 if(Online)

mqtt_server1 = '....'# broker addr2 if(Offline) Local network

#EXAMPLE IP ADDRESS
#mqtt_server = '192.168.1.144'
client_id = ubinascii.hexlify(machine.unique_id())
topic_sub = 'hello'
topic_pub = 'notification'
_hextobyte_cache = None

_configpin = 23 # input pin (esp)
_ledPin = 2 # LED pin 
configpin = Pin(_configpin,Pin.IN)
led = Pin(_ledPin, Pin.OUT)
def unquote(string):
    """unquote('abc%20def') -> b'abc def'."""
    global _hextobyte_cache
    if not string:
        return b''

    if isinstance(string, str):
        string = string.encode('utf-8')

    bits = string.split(b'%')
    if len(bits) == 1:
        return string

    res = [bits[0]]
    append = res.append
    if _hextobyte_cache is None:
        _hextobyte_cache = {}

    for item in bits[1:]:
        try:
            code = item[:2]
            char = _hextobyte_cache.get(code)
            if char is None:
                char = _hextobyte_cache[code] = bytes([int(code, 16)])
            append(char)
            append(item[2:])
        except KeyError:
            append(b'%')
            append(item)

    return b''.join(res)


def web_page():
  if led.value() == 1:
    gpio_state="ON"
  else:
    gpio_state="OFF"
  html = """<html><head> <title>Company Name</title> <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="data:,"> <style>html{font-family: Helvetica; display:inline-block; margin: 0px auto; text-align: center;}
  h1{color: #0F3376; padding: 2vh;}p{font-size: 1.5rem;}.button{display: inline-block; background-color: #e7bd3b; border: none; 
  border-radius: 4px; color: white; padding: 16px 40px; text-decoration: none; font-size: 30px; margin: 2px; cursor: pointer;}
  .button2{background-color: #4286f4;}</style></head><body> <h1>IoT Company</h1> 
  <p>GPIO state: <strong>""" + gpio_state + """</strong></p><p><a href="/?led=on"><button class="button">ON</button></a></p>
  <p><a href="/?led=off"><button class="button button2">OFF</button></a></p>
  
  <form action="/">
  <label for="fname">Router Name (SSID):</label><br>
  <input type="text" id="fname" name="fname" value=""><br>
  <label for="lname">Password:</label><br>
  <input type="text" id="lname" name="lname" value=""><br><br>
  <input type="submit" value="Submit">
  </form>
  
  </body></html>"""
  return html

def config():
    ssid = 'configMode'
    password = '123456789'

    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=ssid, password=password)

    while ap.active() == False:
        pass

    print('Connection successful')
    print(ap.ifconfig())
    
    print(configpin.value())
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 80))
    s.listen(5)

    while configpin.value() == 1:
      conn, addr = s.accept()
      print('Got a connection from %s' % str(addr))
      request = conn.recv(1024)
      request = str(request)
      print('Content = %s' % request)
      led_on = request.find('/?led=on')
      led_off = request.find('/?led=off')
      name = request.find('/?fname')
      print("named : ",name)
      if name == 6 :
            text = request
            a = text[14:].split("&")[0]
            b = text[14:].split("=")[1].split(" ")[0]
            print(a,b)
            a = str(unquote(a).decode("utf-8") )
            b = str(unquote(b).decode("utf-8") )
            c = a + " " + b
            f = open("config","rw")
            f.write(str(c))
            f.close()
      if led_on == 6:
        print('LED ON')
        led.value(1)
      if led_off == 6:
        print('LED OFF')
        led.value(0)
      response = web_page()
      conn.send('HTTP/1.1 200 OK\n')
      conn.send('Content-Type: text/html\n')
      conn.send('Connection: close\n\n')
      conn.sendall(response)
      conn.close()
  
def run():
    station = network.WLAN(network.STA_IF)
    station.active(True)
    station.connect(ssid, password)
    while station.isconnected() == False:
        pass
    print('Connection successful')
    print(station.ifconfig())
    
    def sub_cb(topic, msg):
      print((topic, msg))
      if (msg == b'h'):
          print("hamed is here")
          client.publish("hamedmessage","ok")
          led.value(not led.value())
          #time.sleep(1)
          

    def connect_and_subscribe():
      global client_id, mqtt_server, topic_sub
      client = MQTTClient(client_id, mqtt_server)
      client.set_callback(sub_cb)
      client.connect()
      client.subscribe(topic_sub)
      print('Connected1 to %s MQTT broker, subscribed to %s topic' % (mqtt_server, topic_sub))
      return client

    def connect_and_subscribe1():
      global client_id, mqtt_server, topic_sub
      client = MQTTClient(client_id, mqtt_server1)
      client.set_callback(sub_cb)
      client.connect()
      client.subscribe(topic_sub)
      print('Connected2 to %s MQTT broker, subscribed to %s topic' % (mqtt_server1, topic_sub))
      #client = connect_and_subscribe()
      return client

    def restart_and_reconnect():
      print('Failed to connect to MQTT broker. Reconnecting...')
      time.sleep(1)
      machine.reset()

    try:
        try:
          client = connect_and_subscribe()
        except:
          client = connect_and_subscribe1()
    except OSError as e:
      restart_and_reconnect()

    while True:
      try:
        new_message = client.check_msg()
        if new_message != 'None':
          client.publish(topic_pub, b'received')
        time.sleep(1)
      except OSError as e:
        restart_and_reconnect()
        
        
        
if configpin.value() == 1:
    print("CONFIG_MODE")
    config()
else:
    print("MQTT STARTING...")
    run()
