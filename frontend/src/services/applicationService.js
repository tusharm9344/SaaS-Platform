import api from './api'

export const getOrganizations = async () => {
  const response = await api.get('/organizations/')
  return response.data.results || []
}

export const getApplications = async () => {
  const response = await api.get('/applications/')
  return response.data.results || []
}

export const createApplication = async (data) => {
  const response = await api.post('/applications/', data)
  return response.data
}

export const updateApplication = async (id, data) => {
  const response = await api.patch(`/applications/${id}/`, data)
  return response.data
}

export const getApplicationKeys = async (applicationId) => {
  const response = await api.get(
    `/applications/${applicationId}/api-keys/`
  )
  return response.data.results || []
}

export const createApplicationKey = async (applicationId, name) => {
  const response = await api.post(
    `/applications/${applicationId}/api-keys/`,
    { name }
  )
  return response.data
}

export const revokeApplicationKey = async (applicationId, keyId) => {
  const response = await api.post(
    `/applications/${applicationId}/api-keys/${keyId}/revoke/`
  )
  return response.data
}