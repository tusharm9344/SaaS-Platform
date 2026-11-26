import api from './api'

export const getIncidents = async (params = {}) => {
  const response = await api.get('/incidents/', {
    params,
  })

  return response.data
}

export const getIncidentDetails = async (incidentId) => {
  const response = await api.get(`/incidents/${incidentId}/`)

  return response.data
}

export const getInvestigation = async (incidentId) => {
  const response = await api.get(
    `/incidents/${incidentId}/investigation/`
  )

  return response.data
}

export const resolveIncident = async (incidentId) => {
  const response = await api.post(
    `/incidents/${incidentId}/resolve/`
  )

  return response.data
}

export const reopenIncident = async (incidentId) => {
  const response = await api.post(
    `/incidents/${incidentId}/reopen/`
  )

  return response.data
}