'use strict'

import { app, BrowserWindow } from 'electron'
import * as path from 'path'
import { format as formatUrl } from 'url'
import dgram from 'dgram'

const isDevelopment = process.env.NODE_ENV !== 'production'

// global reference to mainWindow (necessary to prevent window from being garbage collected)
let mainWindow

let m = 0
const UDP_PORT = 1133

function createServer(sendCallback) {
    console.log('Starting UDP server on port ' + UDP_PORT);
    const udp = dgram.createSocket('udp4');

    udp.on('error', (err) => {
        console.log(`UDP server error:\n${err.stack}`);
        udp.close();
    });

    udp.on('message', (buffer, rinfo) => {
        if (buffer.toString() == 'ping') {
            console.log('Received ping message')
            console.log(rinfo);

            udp.send("pong airhockey", rinfo.port, rinfo.address, (error) => {
                if (error) {
                    console.log(error);
                } else {
                    console.log('response sent to brains')
                }
            })
            return;
        }
        console.log('Received message: ' + buffer.toString());

        let view = new Int32Array(buffer.buffer);
        const width = 12.0, height = 6.00;
        const x = -width / 2 + view[0] / 100;
        const y = height / 2 - view[1] / 100;
        console.log(`[${m++}] UDP server got: x:${x} y:${y} from ${rinfo.address}:${rinfo.port}`);
        sendCallback('update-coords', JSON.stringify({ x, y }));
    });

    udp.bind(UDP_PORT);

}

function createMainWindow() {
    const window = new BrowserWindow({
        webPreferences: {
            preload: path.resolve(__dirname, '../../dist/main', 'preload.js'),
            nodeIntegration: true,
            contextIsolation: false
        }
    })
    window.setPosition(18, 131);

    if (isDevelopment) {
        window.webContents.openDevTools()
    }

    if (isDevelopment) {
        window.loadURL(`http://localhost:${process.env.ELECTRON_WEBPACK_WDS_PORT}`)
    }
    else {
        window.loadURL(formatUrl({
            pathname: path.resolve(__dirname, '../../dist/renderer', 'index.html'),
            protocol: 'file',
            slashes: true
        }))
    }

    window.on('closed', () => {
        mainWindow = null
    })

    window.webContents.on('devtools-opened', () => {
        window.focus()
        setImmediate(() => {
            window.focus()
        })
    })

    createServer(window.webContents.send.bind(window.webContents));
    // createServer(window.webContents);

    return window
}

// quit application when all windows are closed
app.on('window-all-closed', () => {
    // on macOS it is common for applications to stay open until the user explicitly quits
    if (process.platform !== 'darwin') {
        app.quit()
    }
})

app.on('activate', () => {
    // on macOS it is common to re-create a window even after all windows have been closed
    if (mainWindow === null) {
        mainWindow = createMainWindow()
    }
})

// create main BrowserWindow when electron is ready
app.on('ready', () => {
    mainWindow = createMainWindow()
})