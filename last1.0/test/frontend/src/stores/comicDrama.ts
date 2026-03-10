import { defineStore } from 'pinia'
import { ref } from 'vue'
import { generateComicDrama } from '../api/comicDrama'

export interface Scene {
  scene_id: number
  visual_prompt: string
  narration: string
  camera: string
  mood: string
  duration: number
  image_url?: string
}

export interface Storyboard {
  title: string
  character: { description: string; name: string }
  scenes: Scene[]
  bgm_style: string
}

export const useComicDramaStore = defineStore('comicDrama', () => {
  // State
  const userInput = ref('')
  const style = ref('cinematic')
  const generating = ref(false)
  const progress = ref('')
  const step = ref<'input' | 'storyboard' | 'images' | 'video_gen' | 'composing' | 'done' | 'error'>('input')
  const videoGenCount = ref(0)
  const storyboard = ref<Storyboard | null>(null)
  const imageUrls = ref<Record<number, string>>({})
  const videoUrl = ref('')
  const taskId = ref('')
  const elapsedSeconds = ref(0)
  const errorMessage = ref('')

  let abortController: AbortController | null = null

  // Actions
  const startGeneration = () => {
    if (!userInput.value.trim()) return
    generating.value = true
    step.value = 'input'
    progress.value = 'AI正在构思剧情...'
    storyboard.value = null
    imageUrls.value = {}
    videoUrl.value = ''
    errorMessage.value = ''

    abortController = generateComicDrama(
      userInput.value,
      style.value,
      (event, data) => {
        switch (event) {
          case 'started':
            taskId.value = data.task_id
            progress.value = data.message
            break

          case 'storyboard_ready':
            storyboard.value = {
              title: data.title,
              character: data.character,
              scenes: data.scenes,
              bgm_style: data.bgm_style,
            }
            step.value = 'storyboard'
            progress.value = '分镜脚本就绪，正在生成画面...'
            break

          case 'image_generated':
            imageUrls.value = { ...imageUrls.value, [data.scene_id]: data.image_url }
            step.value = 'images'
            progress.value = `画面生成中 (${Object.keys(imageUrls.value).length}/${data.total})`
            break

          case 'video_generated':
            videoGenCount.value = (videoGenCount.value || 0) + 1
            step.value = 'video_gen'
            progress.value = `动态视频生成中 (${videoGenCount.value}/${data.total})`
            break

          case 'progress':
            progress.value = data.message
            if (data.step === 'video_gen') step.value = 'video_gen'
            if (data.step === 'composing') step.value = 'composing'
            break

          case 'complete':
            videoUrl.value = data.video_url
            elapsedSeconds.value = data.elapsed_seconds
            step.value = 'done'
            generating.value = false
            progress.value = `生成完成！用时${data.elapsed_seconds}秒`
            break

          case 'error':
            errorMessage.value = data.message
            step.value = 'error'
            generating.value = false
            progress.value = ''
            break
        }
      },
      (err) => {
        errorMessage.value = err.message || '连接失败'
        step.value = 'error'
        generating.value = false
      },
    )
  }

  const stopGeneration = () => {
    abortController?.abort()
    generating.value = false
    progress.value = '已取消'
  }

  const reset = () => {
    stopGeneration()
    userInput.value = ''
    style.value = 'cinematic'
    generating.value = false
    progress.value = ''
    step.value = 'input'
    storyboard.value = null
    imageUrls.value = {}
    videoUrl.value = ''
    taskId.value = ''
    elapsedSeconds.value = 0
    errorMessage.value = ''
    videoGenCount.value = 0
  }

  return {
    userInput, style, generating, progress, step,
    storyboard, imageUrls, videoUrl, taskId, elapsedSeconds, errorMessage, videoGenCount,
    startGeneration, stopGeneration, reset,
  }
})
