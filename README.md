# Rocket

Code repository for RMIT HIVE's GSE and Rocket dashboard.

## Functional Requirements

- Whole server needs to be hosted and viewed on a slower linux computer - [PCM3365](https://www.advantech.com/en-au/products/1bd3bc7c-a45b-48ca-b94d-3fca3190bcc0/pcm-3365/mod_b3576b63-5d3f-4ff9-936a-a7daa3d8f362)
- Has to visualise rocket and GSE metrics
	- Pre-launch checks (go/no-go)
	- Post-launch monitoring
	- Show status of all important systems
- Send commands to rocket and GSE (note hardware input) 
- Alert of possible issues
- Safe and accurate enough to be dependable as a ground control system
- System will recieve data from ISA or I2C

## Non-Functional Requirements

- Server can be accessable through a router and viewed from other people's devices
- Modern, clean and cool looking control station interface
- Graphs, cards, gauges, plots, etc

## Wants

In order of priority

- 2D flight path graph
- 6 degrees of freedom 3D visualisation
- Web server accessable by control room for livestream accesability
- Anything that helps with [competition](https://www.soundingrocket.org/live-rocket-video-challenge.html)
- Mobile support
- Music synced up to fill sequence


## Program Design Ideas

Have the telemetry data ingested and trimmed at the lowest level possible. If you can as much of that on the  driver level that would be ideal. Then the telemetry data should be stored in the local database with the timestamp and a collumn for each metric/feature. Little to no relations at all. It's got to be a performant time series database. Also, data should be exported to .csv and cleared from the db on boot. The table only needs to store data for one flight at a time. Then have FastAPI send all metrics from a simple timestamp query to the front end. The web interface should update at like 30-60tps and each re-render should query the server for a list of changes since last update. The front end should be lightweight and offer basic user interaction and a few different views.


Alternatively, it's worth looking into having the front end run with PHP, laraval and inertiajs while querying straight to db and removing the API level entirely. 


Note, broadcast HUD can be transparent web page overlayed on broadcast software with video source for live output visualisation.


Now I'm thinking we use unix sockets to just talk from the ingestion system to the web server. This is designed for inter-proccess communication and runs on memory instead of disk. Then cache data on the web server runtime so you can distribute to clients closer to the data source

## Prospective Tech Stack

### Backend

- Local InfluxDB database
	- More performant and safe for concurrent read and writes than csv updates
	- Suitable for non-relational low latency telemetry. (advertised for aerospace and telemetry on their site)
- FastAPI 
	- Websocket connection 
	- Lightweight and fast API to handle database interactions
	- Safer and conventional option for handling data compared to csv.
	- Allows for scalability and external clients
- Apache server
	- Suitable for our dynamic content
- Vite for web build
	- For quicker development

### Frontend

- Vue TS
	- Lighter and possibly more performant than react. 
	- Use TS over JS because typed is just better 
	- Probably wont use many features, but this is a good foundation. 
- Tailwind CSS
	- To look cool
- Three.js
	- Just a 3D library to keep in mind
- D3.js
	- Standard for data visualisation

## Design Ideas

I like the design and type of the [vite](https://vite.dev/) website
