import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ProfileSummary, Profile, Topic, ChatMessage, GeneratedScript } from '../types'
import * as api from '../api/ipStudio'

export const useIPStudioStore = defineStore('ipStudio', () => {
  // State
  const profiles = ref<ProfileSummary[]>([])
  const currentProfile = ref<Profile | null>(null)
  const topics = ref<Topic[]>([])
  const interviewPhase = ref('background')
  const chatHistory = ref<ChatMessage[]>([])
  const generatedScript = ref<GeneratedScript | null>(null)
  const loading = ref(false)
  const currentView = ref<'list' | 'interview' | 'voice' | 'detail' | 'topics' | 'script' | 'feedback'>('list')

  // Interviewee info (shared between InterviewChat and VoiceInterview)
  const intervieweeName = ref('')
  const intervieweeIndustry = ref('')
  const intervieweeRole = ref('创始人')

  // Actions
  const loadProfiles = async () => {
    loading.value = true
    try {
      const res: any = await api.listProfiles()
      profiles.value = res.profiles || []
    } finally {
      loading.value = false
    }
  }

  const loadProfile = async (profileId: string) => {
    loading.value = true
    try {
      const res: any = await api.getProfile(profileId)
      currentProfile.value = res
    } finally {
      loading.value = false
    }
  }

  const removeProfile = async (profileId: string) => {
    await api.deleteProfile(profileId)
    profiles.value = profiles.value.filter(p => p.profile_id !== profileId)
    if (currentProfile.value?.profile_id === profileId) {
      currentProfile.value = null
    }
  }

  const askNextQuestion = async (name: string, industry: string, hotTopics: string = '') => {
    loading.value = true
    try {
      const res: any = await api.nextQuestion({
        name,
        industry,
        chat_history: chatHistory.value.map(m => ({ role: m.role === 'ai' ? 'ai' : 'user', content: m.content })),
        phase: interviewPhase.value,
        hot_topics: hotTopics,
      })
      chatHistory.value.push({ role: 'ai', content: res.question || '' })
      if (res.is_done) {
        // Move to next phase
        const phases = ['background', 'hot_topics', 'cognitive', 'voice']
        const idx = phases.indexOf(interviewPhase.value)
        if (idx < phases.length - 1) {
          interviewPhase.value = phases[idx + 1]!
        }
      }
      return res
    } finally {
      loading.value = false
    }
  }

  const addUserMessage = (content: string) => {
    chatHistory.value.push({ role: 'user', content })
  }

  const finalizeProfile = async (name: string, industry: string, role: string) => {
    loading.value = true
    try {
      const res: any = await api.finalizeInterview({
        name,
        industry,
        role,
        chat_history: chatHistory.value.map(m => ({ role: m.role === 'ai' ? 'ai' : 'user', content: m.content })),
      })
      currentProfile.value = res.profile
      currentView.value = 'detail'
      return res.profile
    } finally {
      loading.value = false
    }
  }

  const loadTopics = async (profileId: string) => {
    loading.value = true
    try {
      const res: any = await api.getTopics(profileId)
      topics.value = res.topics || []
    } finally {
      loading.value = false
    }
  }

  const generateNewTopics = async (profileId: string, count: number = 15) => {
    loading.value = true
    try {
      const res: any = await api.generateTopics(profileId, count)
      topics.value = res.topics || []
      return topics.value
    } finally {
      loading.value = false
    }
  }

  const generateScriptFromTopic = async (profileId: string, topic: Topic, duration: number = 90) => {
    loading.value = true
    try {
      const res: any = await api.generateScript(profileId, topic as unknown as Record<string, unknown>, duration)
      generatedScript.value = res.script
      currentView.value = 'script'
      return res.script
    } finally {
      loading.value = false
    }
  }

  const submitScriptFeedback = async (
    profileId: string,
    rejectedParagraphs: string[],
    edits: Array<{original_text: string; edited_text: string; paragraph_index: number; topic_title: string}>,
    notes: string
  ) => {
    loading.value = true
    try {
      const res: any = await api.submitFeedback({
        profile_id: profileId,
        rejected_paragraphs: rejectedParagraphs,
        edits,
        notes,
      })
      return res
    } finally {
      loading.value = false
    }
  }

  const resetInterview = () => {
    interviewPhase.value = 'background'
    chatHistory.value = []
  }

  const goToView = (view: typeof currentView.value) => {
    currentView.value = view
  }

  return {
    profiles, currentProfile, topics, interviewPhase,
    chatHistory, generatedScript, loading, currentView,
    intervieweeName, intervieweeIndustry, intervieweeRole,
    loadProfiles, loadProfile, removeProfile,
    askNextQuestion, addUserMessage, finalizeProfile,
    loadTopics, generateNewTopics, generateScriptFromTopic,
    submitScriptFeedback, resetInterview, goToView,
  }
})
