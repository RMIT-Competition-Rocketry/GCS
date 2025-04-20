/**
 * GCS API
 * 
 * Receives data from the API and loads it into memory to be accessed by other javascript modules.
 *
 * Functions and constants should be prefixed with "api_"  
 */

let api_socket;
let api_latest = {};

function connectSocket() {
	api_socket = new WebSocket("ws://localhost:1887");

	api_socket.onopen = () => {
		console.log("connection gaming");
	};

	api_socket.onmessage = (event) => {
		try {
			const api_data = JSON.parse(event.data);
			api_latest = api_data;

			//console.log(Object.keys(api_latest.data));
			//console.log(api_latest.data)

			if (api_latest.id == 3) {
				// Update interface modules
				interfaceUpdateAvionics(api_latest.data);
				interfaceUpdatePosition(api_latest.data);
			}
		}
		catch (error) {
			console.error("data is dogshit");
		}
	};

	api_socket.onerror = (error) => {
		console.error("websocket is dogshit");
	};

	api_socket.onclose = (event) => {
		console.log("socket closed");
	};
}

connectSocket();
