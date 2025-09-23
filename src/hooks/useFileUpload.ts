import { useState } from "react"
import type { FileType } from "@/types"

export function useFileUpload() {
  const [dragOver, setDragOver] = useState<string | null>(null)

  const handleFileUpload = (
    file: File,
    type: FileType,
    updateInput: (updates: any) => void
  ) => {
    if (type === "audio") {
      updateInput({ audioFile: file })
    } else {
      updateInput({ documentFile: file })
    }
  }

  const handleDragOver = (e: React.DragEvent, type: string) => {
    e.preventDefault()
    setDragOver(type)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(null)
  }

  const handleDrop = (
    e: React.DragEvent,
    type: FileType,
    updateInput: (updates: any) => void
  ) => {
    e.preventDefault()
    setDragOver(null)
    const files = e.dataTransfer.files
    if (files.length > 0) {
      handleFileUpload(files[0], type, updateInput)
    }
  }

  const handleRemoveFile = (
    type: FileType,
    updateInput: (updates: any) => void
  ) => {
    if (type === "audio") {
      updateInput({ audioFile: null })
      const audioInput = document.getElementById("audio-upload") as HTMLInputElement
      if (audioInput) audioInput.value = ""
    } else {
      updateInput({ documentFile: null })
      const documentInput = document.getElementById("document-upload") as HTMLInputElement
      if (documentInput) documentInput.value = ""
    }
  }

  return {
    dragOver,
    handleFileUpload,
    handleDragOver,
    handleDragLeave,
    handleDrop,
    handleRemoveFile,
  }
}