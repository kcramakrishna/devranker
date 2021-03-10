const { app, BrowserWindow, ipcMain } = require('electron')

// // To select Directory Absolute path
// const {dialog} = require('electron').remote;
// const {dialog} = require('electron').remote;
// const electron = require('electron');
var dialog = app.dialog


function createWindow() {
    // GUI with Html
    window = new BrowserWindow({
        width: 1000, height: 800, webPreferences: {
            nodeIntegration: true,
            enableRemoteModule: true
        }
    })
    window.loadFile('./html/home.html')
    // window.loadFile('./html/index.html')
}

app.on('ready', createWindow)

app.on('window-all-closed', () => {
    // On macOS it is common for applications and their menu bar
    // to stay active until the user quits explicitly with Cmd + Q
    //   if (process.platform !== 'darwin') {
    app.quit()
    //   }
})








// ***********************************************
// **************** COMMUNICATION ****************
// ***********************************************
// Event handler for asynchronous incoming messages
ipcMain.on('asynchronous-testing', (event, arg) => {
    console.log(arg)
    // Event emitter for sending asynchronous messages

    const { dialog } = require('electron')
    const pathArray = dialog.showOpenDialog({ properties: ['openDirectory'] })
    // alert(pathArray)
    event.sender.send('asynchronous-testing-reply', JSON.stringify(pathArray))
    console.log(pathArray) // to this method callback value will go
})

// Event handler for synchronous incoming messages
ipcMain.on('synchronous-testing', (event, arg) => {
    console.log(arg)
    // Synchronous event emmision
    event.returnValue = 'callback for synchronous testing ' // this is callback to caller directly
})