# laptop-brick

Stop wasting time on the internet! Brick your computer with a Kasa plug (when the plug is ON, websites are blocked).

[Blog post explainer](https://www.neilchen.co/blog/kasa)

<img src="https://cdn.thewirecutter.com/wp-content/media/2024/08/smart-plug-2048px-2206.jpg" width="200"/>

## Setup

1. (optional) add/remove websites by editing `blocklist`
1. `$ pip install -r requirements.txt`
1. Get the IP address of the plug you'll use: `kasa discover`
1. `$ python main.py "Kasa_plug_ip_address"` # For example. `python main.py "192.168.1.111"`
