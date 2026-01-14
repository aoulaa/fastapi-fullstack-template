// Helper to create users for testing using admin credentials
import { OpenAPI, UsersService } from "../../src/client"
import { firstSuperuser, firstSuperuserPassword } from "../config"
import { LoginService } from "../../src/client"

OpenAPI.BASE = `${process.env.VITE_API_URL}`

export const createUser = async ({
  email,
  password,
}: {
  email: string
  password: string
}) => {
  // Authenticate as admin to create users
  const loginResponse = await LoginService.loginAccessToken({
    formData: {
      username: firstSuperuser,
      password: firstSuperuserPassword,
    },
  })
  
  // Set the token for the next request
  const previousToken = OpenAPI.TOKEN
  OpenAPI.TOKEN = loginResponse.access_token
  
  try {
    const user = await UsersService.createUser({
      requestBody: {
        email,
        password,
        name: "Test User",
      },
    })
    return user
  } finally {
    // Restore previous token
    OpenAPI.TOKEN = previousToken
  }
}
