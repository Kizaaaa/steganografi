import { useState } from "react"
import type { StegoInput } from "@/types"

export function useStegoForm() {
  const [input, setInput] = useState<StegoInput>({
    audioFile: null,
    documentFile: null,
    encrypt: "",
    random: "",
    lsb: "",
    stegoKey: "",
  })

  const updateInput = (updates: Partial<StegoInput>) => {
    setInput((prev) => ({ ...prev, ...updates }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    console.log("Form submitted:", input)
    // Handle form submission here
  }

  return {
    input,
    updateInput,
    handleSubmit,
  }
}