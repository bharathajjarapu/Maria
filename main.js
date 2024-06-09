const { app, BrowserWindow, ipcMain } = require('electron')
const path = require('path')
const { spawn } = require('child_process')

let mainWindow
let pythonProcess

function createWindow() {
   mainWindow = new BrowserWindow({
       width: 1250,
       height: 700,
       minWidth: 1250,
       minHeight: 700,
       webPreferences: {
           nodeIntegration: true,
           contextIsolation: false
       }
   })
   mainWindow.setMenu(null)
   mainWindow.loadFile(path.join(__dirname, 'index.html'))
}

app.on('ready', () => {
   createWindow()
   startPythonProcess()
})

app.on('window-all-closed', () => {
   if (process.platform !== 'darwin') {
       if (pythonProcess && !pythonProcess.killed) {
           pythonProcess.kill()
       }
       app.quit()
   }
})

app.on('activate', () => {
   if (BrowserWindow.getAllWindows().length === 0) {
       createWindow()
   }
})

function startPythonProcess() {
    if (pythonProcess && !pythonProcess.killed) {
        return
    }

    const pythonScriptPath = path.join(__dirname, 'gem.py')
    pythonProcess = spawn('python', [pythonScriptPath])

    pythonProcess.stdout.on('data', (data) => {
        const response = JSON.parse(data.toString().trim())
        mainWindow.webContents.send('receive-message', response.result)
    })

    pythonProcess.stderr.on('data', (data) => {
        console.error(`Python process error: ${data}`)
    })

    pythonProcess.on('exit', (code) => {
        console.log(`Python process exited with code ${code}`)
        startPythonProcess()
    })
}

ipcMain.on('send-message', (event, userInput) => {
   if (pythonProcess && !pythonProcess.killed) {
       pythonProcess.stdin.write(`${userInput}\n`)
   }
})