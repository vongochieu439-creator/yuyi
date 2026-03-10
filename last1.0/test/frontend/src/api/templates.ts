import request from './request'

export const listTemplates = (params?: { category?: string; search?: string }) =>
  request.get('/templates/list', { params })

export const getTemplate = (templateId: string) => request.get(`/templates/${templateId}`)

export const matchTemplates = (productName: string, industry?: string) =>
  request.post('/templates/match', { product_name: productName, industry })
