import { ref, onBeforeUnmount } from 'vue'

export function useAudioPlayer(sampleRate = 24000) {
  const audioCtx = ref<AudioContext | null>(null)
  const nextPlayTime = ref(0)

  const playPcm16Base64 = (base64Chunk: string) => {
    if (!audioCtx.value) {
      audioCtx.value = new AudioContext({ sampleRate })
      nextPlayTime.value = 0
    }
    try {
      const binary = atob(base64Chunk)
      const bytes = new Uint8Array(binary.length)
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
      const pcm16 = new Int16Array(bytes.buffer)
      const float32 = new Float32Array(pcm16.length)
      for (let i = 0; i < pcm16.length; i++) float32[i] = pcm16[i]! / 32768.0
      const buffer = audioCtx.value.createBuffer(1, float32.length, sampleRate)
      buffer.getChannelData(0).set(float32)
      const now = audioCtx.value.currentTime
      const startTime = Math.max(now, nextPlayTime.value)
      nextPlayTime.value = startTime + buffer.duration
      const src = audioCtx.value.createBufferSource()
      src.buffer = buffer
      src.connect(audioCtx.value.destination)
      src.start(startTime)
    } catch (e) {
      console.error('Audio playback error:', e)
    }
  }

  const cleanup = () => {
    audioCtx.value?.close()
    audioCtx.value = null
  }

  onBeforeUnmount(cleanup)

  return { playPcm16Base64, cleanup }
}
