import { useQuery } from "@tanstack/react-query"
import { type UserRead, UsersService } from "@/client"

const useCurrentUser = () => {
  const { data: currentUser } = useQuery<UserRead | null, Error>({
    queryKey: ["currentUser"],
    queryFn: UsersService.readUserMe,
    retry: false,
  })

  return { currentUser }
}

export default useCurrentUser
