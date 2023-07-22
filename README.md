# home_monitoring_display
Display home_monitoring metrics with streamlit app and inky phat

For raspberry pi, run following command before install (with poetry):

Steps to install and run home_monitoring_display: 
1. Install python 3.9
2. Install poetry
3. If on RPI OS, run : 
```
sudo apt install libjpeg-dev zlib1g-dev libatlas-base-dev gfortran libopenblas-dev patchelf cython3
```
4. Then install env with : ```poetry install```
5. Run app with : ```panel serve streaming_dashboard.ipynb analytics_dashboard.ipynb electrical_dashboard.ipynb```


If the app must accessible from external device, on local network: 
1. Setup a fixed IP for your device on your local DHCP (and optionnaly DNS)
2. Add following option to run command : ```--allow-websocket-origin=<device_ip>:5006```


If the app must be accessible from an external network: 
1. Choose and create an account in a DynamicDNS provider (for example No-IP)
2. Open ports and device to external requests (NAT/PAT rule)
3. Setup an oauth service with a provider (for example github)
4. export key and secret in command line : 
```
export PANEL_OAUTH_KEY=<oauth_key>
export PANEL_OAUTH_SECRET=<oauth_secret>
```
5. generate and export cookie secret : 
```
export PANEL_COOKIE_SECRET=$(panel secret)
```
6. Add following options to run command : ```--allow-websocket-origin=<dyn_dns_domain>:5006 --oauth-provider=<oauth_provider>```
