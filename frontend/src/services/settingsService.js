import api from './api'

export const getAIProviderConfig = async (organizationId) => {
  const response = await api.get(
    `/organizations/${organizationId}/ai-provider/`
  )
  return response.data
}

export const saveAIProviderConfig = async (organizationId, data) => {
  const response = await api.put(
    `/organizations/${organizationId}/ai-provider/`,
    data
  )
  return response.data
}

export const testAIProvider = async (organizationId) => {
  const response = await api.post(
    `/organizations/${organizationId}/ai-provider/test/`
  )
  return response.data
}