import path from "node:path"
import { fileURLToPath } from "node:url"
import dotenv from "dotenv"

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

dotenv.config({ path: path.join(__dirname, "../../.env") })

function getEnvVar(name: string, defaultValue?: string): string {
  const value = process.env[name]
  if (!value) {
    if (defaultValue !== undefined) {
      return defaultValue
    }
    throw new Error(`Environment variable ${name} is undefined`)
  }
  return value
}

// Use backend admin credentials for testing
export const firstSuperuser = getEnvVar("ADMIN_EMAIL", "admin@example.com")
export const firstSuperuserPassword = getEnvVar("ADMIN_PASSWORD", "Change-me2")
