import request from './request'

export const listProductProfiles = () => request.get('/product-profiles')

export const getProductProfile = (id: string) => request.get(`/product-profiles/${id}`)

export const saveProductProfile = (data: Record<string, unknown>) => request.post('/product-profiles', data)

export const deleteProductProfile = (id: string) => request.delete(`/product-profiles/${id}`)
