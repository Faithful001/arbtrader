import { apiClient } from '@/api/client'

export const authApi = {
  requestOtp: async (email: string) => {
    const { data } = await apiClient.post('/users/auth/request-otp', { email })
    return data
  },

  verifyOtp: async (email: string, otp: string) => {
    const { data } = await apiClient.post('/users/auth/verify-otp', { email, otp })
    return data
  },
}
