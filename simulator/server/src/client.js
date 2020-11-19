const dgram = require('dgram');

const UDP_PORT = 8081

const client = dgram.createSocket('udp4');


let buffer = new ArrayBuffer(8);

let view = new Int32Array(buffer);
view[0] = process.argv[2];
view[1] = process.argv[3];

client.connect(UDP_PORT, 'localhost', (err) => {
  if (err) {
    console.log(err);
  }

  client.send(view, (err) => {
    if (err) {
      console.log(err);
    }
    client.close();
  });
});