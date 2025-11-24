import { useState, useRef, useEffect } from 'react'
import { Camera, Shield, AlertTriangle, CheckCircle, HardHat, User } from 'lucide-react'
import './index.css'

function App() {
  const [isStreaming, setIsStreaming] = useState(false)
  const [status, setStatus] = useState('idle')
  const [message, setMessage] = useState('Click "Start Safety Check" to begin')
  const [userName, setUserName] = useState(null)
  const [missingPPE, setMissingPPE] = useState([])
  const [annotatedFrame, setAnnotatedFrame] = useState(null)

  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const wsRef = useRef(null)
  const streamRef = useRef(null)
  const intervalRef = useRef(null)

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'user'
        }
      })

      if (videoRef.current) {
        videoRef.current.srcObject = stream
        streamRef.current = stream
      }

      // Connect to WebSocket
      const ws = new WebSocket('ws://localhost:8000/ws')

      ws.onopen = () => {
        console.log('Connected to backend')
        setIsStreaming(true)
        setStatus('idle')
        setMessage('System ready. Please look at the camera.')

        // Start sending frames - TRIGGER FIRST FRAME
        if (ws.readyState === WebSocket.OPEN) {
          captureAndSendFrame()
        }
      }

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        handleBackendResponse(data)
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setMessage('Connection error. Please refresh and try again.')
      }

      ws.onclose = () => {
        console.log('Disconnected from backend')
        stopCamera()
      }

      wsRef.current = ws

    } catch (error) {
      console.error('Camera access error:', error)
      setMessage('Unable to access camera. Please check permissions.')
    }
  }

  const captureAndSendFrame = () => {
    if (!videoRef.current || !canvasRef.current) return

    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) return

    const video = videoRef.current
    const canvas = canvasRef.current
    const context = canvas.getContext('2d')

    if (video.videoWidth === 0 || video.videoHeight === 0) {
      requestAnimationFrame(captureAndSendFrame)
      return
    }

    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    context.drawImage(video, 0, 0, canvas.width, canvas.height)

    // Convert to base64 and send
    canvas.toBlob((blob) => {
      if (!blob) return
      const reader = new FileReader()
      reader.onloadend = () => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(reader.result.split(',')[1]) // Send base64 data only
        }
      }
      reader.readAsDataURL(blob)
    }, 'image/jpeg', 0.7) // Slightly lower quality for speed
  }

  const handleBackendResponse = (data) => {
    setStatus(data.status)
    setMessage(data.message)
    setUserName(data.user)
    setMissingPPE(data.missing_ppe || [])

    if (data.annotated_frame) {
      setAnnotatedFrame(`data:image/jpeg;base64,${data.annotated_frame}`)
    }

    // Trigger next frame
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      requestAnimationFrame(captureAndSendFrame)
    }
  }

  const stopCamera = () => {
    if (wsRef.current) {
      wsRef.current.close()
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
    }

    setIsStreaming(false)
    setStatus('idle')
    setMessage('Camera stopped')
    setAnnotatedFrame(null)
    setUserName(null)
    setMissingPPE([])
  }

  useEffect(() => {
    return () => {
      stopCamera()
    }
  }, [])

  const getStatusColor = () => {
    if (status === 'Access Granted') return 'status-success'
    if (status === 'Access Denied') return 'status-error'
    if (status === 'Unknown User') return 'status-warning'
    return ''
  }

  const getStatusIcon = () => {
    if (status === 'Access Granted') return <CheckCircle className="w-8 h-8" />
    if (status === 'Access Denied') return <AlertTriangle className="w-8 h-8" />
    return <Shield className="w-8 h-8" />
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 p-8">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex items-center gap-4 mb-2">
          <HardHat className="w-12 h-12 text-amber-400" />
          <h1 className="text-5xl font-bold bg-gradient-to-r from-cyan-500 to-amber-400 bg-clip-text text-transparent">
            Construction Safety System
          </h1>
        </div>
        <p className="text-gray-400 text-lg ml-16">
          AI-Powered Worker Identification & PPE Compliance Check
        </p>
      </div>

      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Video Feed */}
        <div className="lg:col-span-2">
          <div className="card">
            <div className="relative aspect-video bg-black rounded-lg overflow-hidden border-2 border-gray-700">
              {annotatedFrame ? (
                <img
                  src={annotatedFrame}
                  alt="Annotated feed"
                  className="w-full h-full object-contain"
                />
              ) : (
                <div className="absolute inset-0 flex items-center justify-center">
                  {!isStreaming ? (
                    <div className="text-center">
                      <Camera className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                      <p className="text-gray-500 text-lg">Camera feed will appear here</p>
                    </div>
                  ) : (
                    <div className="text-center">
                      <div className="animate-pulse">
                        <Shield className="w-16 h-16 text-cyan-400 mx-auto mb-4" />
                        <p className="text-gray-400">Processing...</p>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Hidden elements */}
              <video
                ref={videoRef}
                autoPlay
                playsInline
                className="hidden"
              />
              <canvas ref={canvasRef} className="hidden" />
            </div>

            {/* Controls */}
            <div className="flex gap-4 mt-6">
              {!isStreaming ? (
                <button
                  onClick={startCamera}
                  className="btn-primary flex items-center gap-2 flex-1"
                >
                  <Camera className="w-5 h-5" />
                  Start Safety Check
                </button>
              ) : (
                <button
                  onClick={stopCamera}
                  className="bg-red-600 hover:bg-red-700 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 shadow-lg hover:shadow-red-600/50 hover:scale-105 flex items-center gap-2 flex-1"
                >
                  <AlertTriangle className="w-5 h-5" />
                  Stop Camera
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Status Panel */}
        <div className="space-y-6">
          {/* Status Card */}
          <div className={`card ${getStatusColor()} transition-all duration-300`}>
            <div className="flex items-center gap-3 mb-4">
              {getStatusIcon()}
              <h2 className="text-2xl font-bold">Status</h2>
            </div>
            <div className="space-y-3">
              <div className="text-lg font-semibold">
                {status === 'idle' ? 'Standby' : status}
              </div>
              <div className="text-sm opacity-90">
                {message}
              </div>
            </div>
          </div>

          {/* Worker Info */}
          {userName && (
            <div className="card animate-fadeIn">
              <div className="flex items-center gap-3 mb-4">
                <User className="w-6 h-6 text-cyan-400" />
                <h3 className="text-xl font-bold">Worker Info</h3>
              </div>
              <div className="bg-gray-900 rounded-lg p-4">
                <p className="text-sm text-gray-400 mb-1">Name</p>
                <p className="text-xl font-semibold text-amber-400">{userName}</p>
              </div>
            </div>
          )}

          {/* PPE Status */}
          {missingPPE.length > 0 && (
            <div className="card status-error animate-fadeIn">
              <div className="flex items-center gap-3 mb-4">
                <AlertTriangle className="w-6 h-6" />
                <h3 className="text-xl font-bold">Missing PPE</h3>
              </div>
              <ul className="space-y-2">
                {missingPPE.map((item, index) => (
                  <li key={index} className="flex items-center gap-2 bg-gray-900 rounded-lg p-3">
                    <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                    <span className="capitalize font-medium">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Instructions */}
          <div className="card bg-gradient-to-br from-primary/10 to-secondary/10 border border-cyan-500/30">
            <h3 className="text-lg font-bold mb-3 text-amber-400">Instructions</h3>
            <ol className="space-y-2 text-sm text-gray-300">
              <li className="flex gap-2">
                <span className="text-cyan-400 font-bold">1.</span>
                <span>Click "Start Safety Check" to activate camera</span>
              </li>
              <li className="flex gap-2">
                <span className="text-cyan-400 font-bold">2.</span>
                <span>Look directly at the camera for identification</span>
              </li>
              <li className="flex gap-2">
                <span className="text-cyan-400 font-bold">3.</span>
                <span>System will verify PPE compliance</span>
              </li>
              <li className="flex gap-2">
                <span className="text-cyan-400 font-bold">4.</span>
                <span>Ensure helmet and safety vest are visible</span>
              </li>
            </ol>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="max-w-7xl mx-auto mt-8 text-center text-gray-500 text-sm">
        <p>© 2025 Construction Safety System • Powered by AI • Real-time Worker Safety Compliance</p>
      </div>
    </div>
  )
}

export default App
