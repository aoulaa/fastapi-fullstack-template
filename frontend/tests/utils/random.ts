export const randomEmail = () =>
  `test_${Math.random().toString(36).substring(7)}@example.com`

export const randomTeamName = () =>
  `Team ${Math.random().toString(36).substring(7)}`

// Generates a password that satisfies backend requirements:
// 8+ chars, uppercase, lowercase, digit, special character
export const randomPassword = () => {
  const lower = Math.random().toString(36).substring(2, 8)
  return `${lower}A1!`
}

export const slugify = (text: string) =>
  text
    .toLowerCase()
    .replace(/\s+/g, "-")
    .replace(/[^\w-]+/g, "")
