const { contextBridge,ipcRenderer } = require('electron')

// window.addEventListener('DOMContentLoaded', () => {
//     ipcRenderer.on('update-coords', (_event, value) => {
//         console.log('test')
//         console.log(value)
//         window.alert('test');
//     })
// })
window.api = {}
window.api.UdpCallback = (callback) => ipcRenderer.on('update-coords', callback)


// contextBridge.exposeInMainWorld('funcs', {
//   ping: () => ipcRenderer.invoke('ping'),
// })