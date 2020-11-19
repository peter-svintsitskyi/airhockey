const WebSocket = require('ws');
const dgram = require('dgram');

const WS_PORT = 8080
const UDP_PORT = 8081

const wss = new WebSocket.Server({ port: WS_PORT });
let m = 0;

wss.on('connection', function connection(ws) {
  const udp = dgram.createSocket('udp4');

  udp.on('error', (err) => {
    console.log(`server error:\n${err.stack}`);
    udp.close();
  });

  udp.on('message', (buffer, rinfo) => {
    let view = new Int32Array(buffer.buffer);
    const width = 12.0, height = 6.00;
    const x = -width/2 + view[0] / 100;
    const y = height/2 - view[1] / 100;
    console.log(`[${m++}] server got: x:${x} y:${y} from ${rinfo.address}:${rinfo.port}`);
    ws.send(JSON.stringify({x, y}));
  });

  udp.on('listening', () => {
    const address = udp.address();
    console.log(`server listening ${address.address}:${address.port}`);
  });

  udp.bind(UDP_PORT);
});
