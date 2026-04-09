import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"

import { type Body_login_access_token as AccessToken, LoginService } from "@/client"
import { handleError } from "@/utils"
import useCustomToast from "./useCustomToast"

const useAuth = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { showErrorToast } = useCustomToast()

  const loginMutation = useMutation({
    mutationFn: (data: AccessToken) =>
      LoginService.loginAccessToken({ formData: data }),
    onSuccess: () => {
      navigate({ to: "/" })
    },
    onError: handleError.bind(showErrorToast),
  })

  const logoutMutation = useMutation({
    mutationFn: () => LoginService.logout(),
    onSettled: () => {
      queryClient.clear()
      navigate({ to: "/login" })
    },
  })

  const logout = () => logoutMutation.mutate()

  return {
    loginMutation,
    logout,
  }
}

export default useAuth
