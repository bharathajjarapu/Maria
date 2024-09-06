const { app, BrowserWindow, ipcMain, Menu } = require('electron')
const path = require('path')
const { spawn } = require('child_process')
const fs = require('fs')

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

function findPython() {
    const possibilities = [
        path.join(process.resourcesPath, 'venv', 'scripts', 'python.exe'),
        path.join(__dirname, 'venv', 'scripts', 'python.exe'),
    ]
    for (const path_to_python of possibilities) {
        if (fs.existsSync(path_to_python)) {
            return path_to_python
        }
    }
    console.log('Could not find python, checked', possibilities)
    app.quit()
}

const pythonPath = findPython()
console.log('Python Path:', pythonPath)

function startPythonProcess() {
    if (pythonProcess && !pythonProcess.killed) {
        return
    }

    const pythonScriptPath = path.join(__dirname, 'llm.py')
    pythonProcess = spawn(pythonPath, [pythonScriptPath])

    pythonProcess.stdout.on('data', (data) => {
        try {
            const response = JSON.parse(data.toString().trim())
            switch (response.type) {
                case 'message':
                    mainWindow.webContents.send('receive-message', response.result)
                    break
                case 'pdf_processed':
                    mainWindow.webContents.send('pdf-processed', response.filename)
                    break
                case 'pdf_list':
                    mainWindow.webContents.send('update-pdf-list', response.pdfs)
                    break
                case 'pdf_deleted':
                    mainWindow.webContents.send('pdf-deleted', response.filename)
                    break
            }
        } catch (error) {
            console.error('Error parsing Python output:', error)
        }
    })

    pythonProcess.stderr.on('data', (data) => {
        console.error(`Python process error: ${data}`)
    })

    pythonProcess.on('exit', (code) => {
        console.log(`Python process exited with code ${code}`)
        startPythonProcess()
    })

    // Request initial PDF list
    pythonProcess.stdin.write(JSON.stringify({ type: 'get_pdf_list' }) + '\n')
}

ipcMain.on('send-message', (_event, userInput) => {
    if (pythonProcess && !pythonProcess.killed) {
        pythonProcess.stdin.write(JSON.stringify({ type: 'message', content: userInput }) + '\n')
    }
})

ipcMain.on('upload-pdf', (_event, fileContent, filename) => {
    if (pythonProcess && !pythonProcess.killed) {
        pythonProcess.stdin.write(JSON.stringify({ type: 'pdf_upload', content: Array.from(fileContent), filename: filename }) + '\n')
    }
})

ipcMain.on('delete-pdf', (_event, filename) => {
    if (pythonProcess && !pythonProcess.killed) {
        pythonProcess.stdin.write(JSON.stringify({ type: 'delete_pdf', filename: filename }) + '\n')
    }
})