import request from './request'

export const listProfiles = () => request.get('/ip-studio/profiles')

export const getProfile = (profileId: string) => request.get(`/ip-studio/profiles/${profileId}`)

export const deleteProfile = (profileId: string) => request.delete(`/ip-studio/profiles/${profileId}`)

export const nextQuestion = (data: {
  name: string
  industry: string
  chat_history: Array<{role: string; content: string}>
  phase: string
  hot_topics?: string
}) => request.post('/ip-studio/interview/next-question', data)

export const finalizeInterview = (data: {
  name: string
  industry: string
  role: string
  chat_history: Array<{role: string; content: string}>
}) => request.post('/ip-studio/interview/finalize', data)

export const supplementInterview = (profileId: string, chatHistory: Array<{role: string; content: string}>) =>
  request.post('/ip-studio/interview/supplement', { profile_id: profileId, chat_history: chatHistory })

export const getHotTopics = (industry: string) => request.get(`/ip-studio/hot-topics/${industry}`)

export const generateTopics = (profileId: string, count: number = 15) =>
  request.post('/ip-studio/topics/generate', { profile_id: profileId, count })

export const getTopics = (profileId: string) => request.get(`/ip-studio/topics/${profileId}`)

export const generateScript = (profileId: string, topic: Record<string, unknown>, duration: number = 90) =>
  request.post('/ip-studio/script/generate', { profile_id: profileId, topic, duration })

export const submitFeedback = (data: {
  profile_id: string
  rejected_paragraphs: string[]
  edits: Array<{original_text: string; edited_text: string; paragraph_index: number; topic_title: string}>
  notes: string
}) => request.post('/ip-studio/script/feedback', data)
