import http from 'http'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const PORT = 3000
const BACKEND_URL = 'http://127.0.0.1:8000'

const MIME_TYPES = {
  '.html': 'text/html',
  '.js': 'text/javascript',
  '.jsx': 'text/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.png': 'image/png',
  '.svg': 'image/svg+xml'
}

const server = http.createServer((req, res) => {
  // Proxy /api requests to FastAPI backend
  if (req.url.startsWith('/api')) {
    const proxyUrl = new URL(req.url, BACKEND_URL)
    const options = {
      hostname: proxyUrl.hostname,
      port: proxyUrl.port,
      path: proxyUrl.pathname + proxyUrl.search,
      method: req.method,
      headers: req.headers
    }

    const proxyReq = http.request(options, (proxyRes) => {
      res.writeHead(proxyRes.statusCode, proxyRes.headers)
      proxyRes.pipe(res, { end: true })
    })

    proxyReq.on('error', (err) => {
      res.writeHead(502, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify({ error: 'Backend unreachable. Make sure FastAPI is running on port 8000.' }))
    })

    req.pipe(proxyReq, { end: true })
    return
  }

  // Serve static frontend files
  let safePath = req.url.split('?')[0]
  if (safePath === '/' || safePath === '') safePath = '/index.html'

  const filePath = path.join(__dirname, safePath)
  const ext = path.extname(filePath).toLowerCase()
  const contentType = MIME_TYPES[ext] || 'application/octet-stream'

  fs.readFile(filePath, (err, content) => {
    if (err) {
      if (err.code === 'ENOENT') {
        // Fallback to index.html for SPA
        fs.readFile(path.join(__dirname, 'index.html'), (indexErr, indexContent) => {
          if (indexErr) {
            res.writeHead(404)
            res.end('File not found')
          } else {
            res.writeHead(200, { 'Content-Type': 'text/html' })
            res.end(indexContent, 'utf-8')
          }
        })
      } else {
        res.writeHead(500)
        res.end(`Server Error: ${err.code}`)
      }
    } else {
      res.writeHead(200, { 'Content-Type': contentType })
      res.end(content, 'utf-8')
    }
  })
})

server.listen(PORT, () => {
  console.log(`\n🚀 CareerMatch AI Frontend running at: http://localhost:${PORT}/`)
  console.log(`📡 Connected to FastAPI Backend proxy at: ${BACKEND_URL}/api\n`)
})
