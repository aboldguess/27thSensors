main-9.py
100%
# ==========================================
# STAGE 9: MISSION CONTROL HUB
# ==========================================
#
# What it does: Full automated command dashboard. Retains the calibrated 
# 10C-50C labeled grid. Positions interactive control readouts cleanly 
# beneath the graph module to protect the line design structure of Stage 8.

import machine                                              # Brings in hardware control tools for pins and chips
import time                                                 # Brings in timing tools so we can create delays and pauses
import network                                              # Brings in the Wi-Fi control engine to run the radio antenna
import socket                                               # Brings in internet communication tools for web servers
import os                                                   # Brings in file system tools to delete files

# --- HARDWARE PIN SETUPS ---
led = machine.Pin("LED", machine.Pin.OUT)                   # Configures the green onboard LED as an output signal
sensor_temp = machine.ADC(4)                                # Connects to internal temperature sensor on Analog Channel 4
conversion_factor = 3.3 / 65535                             # Converts raw sensor values into volts

# --- GLOBAL SYSTEM MEMORY ---
graph_history = []                                          # Stores historical temperature values for our graph
refresh_rate = 2                                            # Number of seconds between page refreshes (Set by slider!)

# --- WI-FI ROUTER BROADCASTER ---
ap = network.WLAN(network.AP_IF)                            # Configures the Pico as a Wi-Fi hotspot
ap.active(True)                                             # Turns on the Wi-Fi radio

# ⚠️ SCOUT CRITICAL: Change this to your own name
my_network_name = "ALEX_Sensor_Network"                     # Creates the text name for your private Wi-Fi network signal
my_password = "This_Password123"                            # Creates your Wi-Fi password
ap.config(essid=my_network_name, password=my_password)      # Applies the Wi-Fi settings
ip_address = "192.168.4.1"                                  # Standard Pico hotspot address

# --- WEB SERVER PORT PLUMBING ---
address = (ip_address, 80)                                  # Creates the web server address
s = socket.socket()                                         # Creates a network communication socket
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)     # Allows quick reconnects
s.bind(address)                                             # Connects the socket to port 80
s.listen(1)                                                 # Waits for one browser connection at a time

print("Wi-Fi Online!")
print("=========================================")
print(f"Wi-Fi Network Name : {my_network_name}")
print(f"Wi-Fi Password     : {my_password}")
print(f"Web Server Address : http://{ip_address}")
print("=========================================")

# --- THE CONTINUOUS MAIN LOOP ---
while True:                                                 # Runs forever
    try:                                                    # Creates an error protection block
        client, addr = s.accept()                           # Waits for a browser to connect
        request_bytes = client.recv(1024)                   # Receives the browser request data
        
        if not request_bytes:
            client.close()
            continue
            
        request = request_bytes.decode('utf-8')             # Converts bytes into a text string
        
        # --- PATH A: THE SPEED SLIDER COMMAND ---
        if "GET /speed?set=" in request:
            try:
                start_index = request.find("set=") + 4
                end_index = request.find(" ", start_index)
                speed_value = request[start_index:end_index]
                
                refresh_rate = int(speed_value)             # Overwrites our timing variable with the slider choice
                print(f"Update speed changed to {refresh_rate} seconds.")
            except:
                pass

        # --- PATH B: THE RESET DATA COMMAND ---
        elif "GET /reset" in request:
            print("Reset Command Received! Wiping data.csv and clearing graph.")
            try:
                os.remove("data.csv")                       # Deletes the file off the Pico storage completely
            except:
                pass
            graph_history = []                              # Empty our running live chart notebook memory list

        # --- PATH C: THE DOWNLOAD FILE ROUTE ---
        elif "GET /download" in request:
            print("Processing file download request...")
            try:
                with open("data.csv", "r") as f:
                    csv_data = f.read()
                client.send("HTTP/1.1 200 OK\n")
                client.send("Content-Type: text/csv\n")
                client.send("Content-Disposition: attachment; filename=scout_data.csv\n")
                client.send("Connection: close\n\n")
                client.sendall(csv_data)
            except:
                client.send("HTTP/1.1 200 OK\nContent-Type: text/plain\nConnection: close\n\nNo records logged yet.")
            client.close()
            continue

        # --- CORE SENSOR RUN LOGIC ---
        led.value(1)                                        # Turns the LED on
        time.sleep(0.5)                                     # Keeps it on briefly
        led.value(0)                                        # Turns the LED off
        
        raw_reading = sensor_temp.read_u16() * conversion_factor  # Reads the sensor voltage
        temperature = 27 - (raw_reading - 0.706) / 0.001721       # Converts voltage to Celsius
        current_temp = round(temperature, 1)                      # Rounds to one decimal place
        
        with open("data.csv", "a") as f:
            f.write(f"{current_temp}\n")
            
        graph_history.append(current_temp)
        if len(graph_history) > 10:
            graph_history.pop(0)
            
        # --- SVG GRAPH COORDINATE MATH ENGINE ---
        graph_points = ""
        for i, temp in enumerate(graph_history):
            x = 60 + (i * 24)
            y = 250 - ((temp - 10) * 5)                     # Calibrated scale equation matching Stage 7
            graph_points += f"{x},{y} "
            
        svg_graph = f"""
        <svg width="320" height="300">
            <line x1="60" y1="250" x2="300" y2="250" stroke="black" stroke-width="2" />
            <line x1="60" y1="50" x2="60" y2="250" stroke="black" stroke-width="2" />
            <text x="15" y="55" font-family="Arial" font-size="12" fill="black">50&deg;C</text>
            <text x="15" y="155" font-family="Arial" font-size="12" fill="gray">30&deg;C</text>
            <text x="15" y="255" font-family="Arial" font-size="12" fill="black">10&deg;C</text>
            <line x1="55" y1="50" x2="60" y2="50" stroke="black" stroke-width="2" />
            <line x1="55" y1="150" x2="60" y2="150" stroke="gray" stroke-width="1" />
            <line x1="55" y1="250" x2="60" y2="250" stroke="black" stroke-width="2" />
            <polyline points="{graph_points}" fill="none" stroke="blue" stroke-width="3" />
        </svg>
        """
        
        # --- WEBPAGE CODE DESIGN BLOCK (HTML with Inline SVG) ---
        response = f"""
<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="{refresh_rate}">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: Arial; text-align: center; background-color: lightgray; }}
        .card {{ background-color: white; padding: 30px; border-radius: 15px; display: inline-block; margin-top: 30px; width: 320px; }}
        h1 {{ color: green; }}
        .temp {{ font-size: 50px; font-weight: bold; color: orange; }}
        
        .btn {{
            display: inline-block;
            padding: 10px 15px;
            margin: 5px;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: bold;
            font-size: 14px;
            border: none;
            cursor: pointer;
        }}
        .set-btn {{ background-color: blue; }}
        .dl-btn {{ background-color: red; margin-top: 15px; display: block; }}
        .reset-btn {{ background-color: darkorange; margin-top: 10px; display: block; }}
        
        .slider-box {{ margin-top: 15px; background: #f0f0f0; padding: 10px; border-radius: 8px; }}
        input[type=range] {{ width: 80%; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>Live Scout Dashboard</h1>
        <p class="temp">{current_temp}&deg;C</p>
        <h3>Temperature Graph</h3>
        {svg_graph}
        
        <p>Update Speed: <strong>{refresh_rate} seconds</strong></p>
        
        <div class="slider-box">
            <form action="/speed" method="get">
                <label>Adjust Delay (1-100s):</label><br>
                <input type="range" name="set" min="1" max="100" value="{refresh_rate}">
                <input type="submit" value="Set Speed" class="btn set-btn">
            </form>
        </div>
        
        <a href="/download" class="btn dl-btn">Download Spreadsheet Log</a>
        <a href="/reset" class="btn reset-btn">Clear Saved Data</a>
    </div>
</body>
</html>
"""
        
        client.send("HTTP/1.1 200 OK\n")
        client.send("Content-Type: text/html\n")
        client.send("Connection: close\n\n")
        client.sendall(response)
        client.close()
        
    except Exception as e:
        if 'client' in locals():
            client.close()
        led.value(0)
