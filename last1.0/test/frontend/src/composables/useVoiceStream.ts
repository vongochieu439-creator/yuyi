import { ref, onBeforeUnmount } from 'vue'

const SAMPLE_RATE = 24000
const BUFFER_SIZE = 2400 // 100ms at 24kHz

export function useVoiceStream() {
  const audioContext = ref<AudioContext | null>(null)
  const mediaStream = ref<MediaStream | null>(null)
  const isRecording = ref(false)
  const analyser = ref<AnalyserNode | null>(null)
  let workletNode: AudioWorkletNode | null = null
  let scriptNode: ScriptProcessorNode | null = null

  const start = async (onAudioChunk: (base64: string) => void) => {
    try {
      mediaStream.value = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: SAMPLE_RATE,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      })

      audioContext.value = new AudioContext({ sampleRate: SAMPLE_RATE })
      const source = audioContext.value.createMediaStreamSource(mediaStream.value)

      // Analyser for waveform visualization
      analyser.value = audioContext.value.createAnalyser()
      analyser.value.fftSize = 256
      source.connect(analyser.value)

      // Try AudioWorklet first, fallback to ScriptProcessor
      let useWorklet = false
      try {
        const processorCode = `
class AudioCaptureProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this._buf = new Float32Array(${BUFFER_SIZE});
    this._off = 0;
  }
  process(inputs) {
    const input = inputs[0];
    if (!input || !input[0]) return true;
    const samples = input[0];
    for (let i = 0; i < samples.length; i++) {
      this._buf[this._off++] = samples[i];
      if (this._off >= ${BUFFER_SIZE}) {
        const pcm16 = new Int16Array(${BUFFER_SIZE});
        for (let j = 0; j < ${BUFFER_SIZE}; j++) {
          const s = Math.max(-1, Math.min(1, this._buf[j]));
          pcm16[j] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        this.port.postMessage(pcm16.buffer, [pcm16.buffer]);
        this._buf = new Float32Array(${BUFFER_SIZE});
        this._off = 0;
      }
    }
    return true;
  }
}
registerProcessor('audio-capture', AudioCaptureProcessor);`
        const blob = new Blob([processorCode], { type: 'application/javascript' })
        const url = URL.createObjectURL(blob)
        await audioContext.value.audioWorklet.addModule(url)
        URL.revokeObjectURL(url)

        workletNode = new AudioWorkletNode(audioContext.value, 'audio-capture')
        workletNode.port.onmessage = (e: MessageEvent) => {
          if (!isRecording.value) return
          const pcm16 = new Uint8Array(e.data as ArrayBuffer)
          let binary = ''
          for (let i = 0; i < pcm16.length; i++) {
            binary += String.fromCharCode(pcm16[i]!)
          }
          onAudioChunk(btoa(binary))
        }
        source.connect(workletNode)
        // Connect to silent output to keep processing alive
        const silentGain = audioContext.value.createGain()
        silentGain.gain.value = 0
        workletNode.connect(silentGain)
        silentGain.connect(audioContext.value.destination)
        useWorklet = true
        console.log('Audio capture: AudioWorklet (24kHz)')
      } catch {
        console.warn('AudioWorklet unavailable, falling back to ScriptProcessor')
      }

      if (!useWorklet) {
        // Fallback: ScriptProcessor (works on HTTP)
        scriptNode = audioContext.value.createScriptProcessor(4096, 1, 1)
        scriptNode.onaudioprocess = (e) => {
          if (!isRecording.value) return
          const float32 = e.inputBuffer.getChannelData(0)
          const pcm16 = new Int16Array(float32.length)
          for (let i = 0; i < float32.length; i++) {
            const s = Math.max(-1, Math.min(1, float32[i] as number))
            pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
          }
          const bytes = new Uint8Array(pcm16.buffer)
          let binary = ''
          for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i] as number)
          }
          onAudioChunk(btoa(binary))
        }
        source.connect(scriptNode)
        const silentGain = audioContext.value.createGain()
        silentGain.gain.value = 0
        scriptNode.connect(silentGain)
        silentGain.connect(audioContext.value.destination)
        console.log('Audio capture: ScriptProcessor fallback (24kHz)')
      }

      isRecording.value = true
    } catch (err) {
      console.error('Voice stream start failed:', err)
      throw err
    }
  }

  const stop = () => {
    isRecording.value = false
    workletNode?.disconnect()
    workletNode = null
    scriptNode?.disconnect()
    scriptNode = null
    mediaStream.value?.getTracks().forEach(t => t.stop())
    mediaStream.value = null
    audioContext.value?.close()
    audioContext.value = null
    analyser.value = null
  }

  const getWaveformData = (): Uint8Array => {
    if (!analyser.value) return new Uint8Array(0)
    const data = new Uint8Array(analyser.value.frequencyBinCount)
    analyser.value.getByteTimeDomainData(data)
    return data
  }

  onBeforeUnmount(() => {
    stop()
  })

  return { isRecording, start, stop, getWaveformData, analyser }
}
