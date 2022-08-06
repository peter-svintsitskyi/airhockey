const WebSocket = require('ws');
const dgram = require('dgram');

const WS_PORT = 1122
const UDP_PORT = 1133

const wss = new WebSocket.Server({ port: WS_PORT });
let m = 0;

console.log("Starting udp(brain) -> websocket(simulated hardware) proxy");
console.log(`Waiting for websocket connection on port ${WS_PORT}`);

wss.on('connection', function connection(ws) {
  console.log(`Created websocket server`)

  const udp = dgram.createSocket('udp4');

  udp.on('error', (err) => {
    console.log(`UDP server error:\n${err.stack}`);
    udp.close();
  });

  udp.on('message', (buffer, rinfo) => {
    if (buffer.toString() == 'ping') {
      console.log('Received ping message')
      console.log(rinfo);
      

      ws.onmessage = (e) => {
        console.log('received response', e.data)
        console.log('writing to udp')
        udp.send(e.data, rinfo.port, rinfo.address, (error) => {
          if (error) {
            console.log(error);
          } else {
            console.log('response sent to brains')
          }
        })
      }

      ws.send("ping")

      return;
    }

    let view = new Int32Array(buffer.buffer);
    const width = 12.0, height = 6.00;
    const x = -width/2 + view[0] / 100;
    const y = height/2 - view[1] / 100;
    console.log(`[${m++}] UDP server got: x:${x} y:${y} from ${rinfo.address}:${rinfo.port}`);
    ws.send(JSON.stringify({x, y}));
  });

  udp.on('listening', () => {
    const address = udp.address();
    console.log(`UDP server listening ${address.address}:${address.port}`);
  });



  udp.bind(UDP_PORT);
});
