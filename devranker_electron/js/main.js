const { app, BrowserWindow, ipcMain } = require('electron')

var pathInfo
// Event handler for asynchronous incoming messages
ipcMain.on('asynchronous-setPathInfo', (event, arg) => {
    console.log('main.js/asynchronous-setPathInfo', arg)
    pathInfo = arg
    // Event emitter for sending asynchronous messages
    event.sender.send('asynchronous-reply-setPathInfo', 'Received')
})

// Synchronous Communication
ipcMain.on('synchronous-getPathInfo', (event, arg) => {
    console.log('main.js/synchronous-getPathInfo', arg)
    // Synchronous event emmision
    event.returnValue = pathInfo
})

function createWindow() {
    // GUI with Html
    window = new BrowserWindow({
        width: 1100, height: 800, webPreferences: {
            nodeIntegration: true,
            enableRemoteModule: true
        }
    })
    window.loadFile('./html/home.html')
}

app.on('ready', createWindow)

app.on('window-all-closed', () => {
    app.quit()
})