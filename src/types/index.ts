export interface StegoInput {
  audioFile: File | null
  documentFile: File | null
  encrypt: string
  random: string
  lsb: string
  stegoKey: string
}

export type FileType = "audio" | "document"

export interface FileUploadProps {
  file: File | null
  fileType: FileType
  accept: string
  title: string
  description: string
  icon: React.ComponentType<{ className?: string }>
  onFileUpload: (file: File, type: FileType) => void
  onRemoveFile: (type: FileType) => void
  dragOver: string | null
  onDragOver: (e: React.DragEvent, type: string) => void
  onDragLeave: (e: React.DragEvent) => void
  onDrop: (e: React.DragEvent, type: FileType) => void
}

export interface RadioSectionProps {
  title: string
  description: string
  value: string
  onValueChange: (value: string) => void
  options: Array<{
    value: string
    label: string
    id: string
  }>
  layout?: "horizontal" | "vertical"
}