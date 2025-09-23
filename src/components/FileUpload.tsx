import type React from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Upload, Check, X } from "lucide-react"
import type { FileUploadProps } from "@/types"

export function FileUpload({
  file,
  fileType,
  accept,
  title,
  description,
  icon: Icon,
  onFileUpload,
  onRemoveFile,
  dragOver,
  onDragOver,
  onDragLeave,
  onDrop,
}: FileUploadProps) {
  const inputId = `${fileType}-upload`

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(2)} KB`
    }
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Icon className="h-5 w-5" />
          {title}
        </CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <Input
          type="file"
          accept={accept}
          onChange={(e) => {
            const selectedFile = e.target.files?.[0]
            if (selectedFile) onFileUpload(selectedFile, fileType)
          }}
          className="hidden"
          id={inputId}
        />
        <Label htmlFor={inputId} className="cursor-pointer block">
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragOver === fileType ? "border-accent bg-accent/5" : "border-border hover:border-accent/50"
            }`}
            onDragOver={(e) => onDragOver(e, fileType)}
            onDragLeave={onDragLeave}
            onDrop={(e) => onDrop(e, fileType)}
          >
            {file ? (
              <div className="space-y-4">
                <div className="flex items-center justify-center gap-2 text-accent">
                  <Check className="h-5 w-5" />
                  <span className="font-medium">{file.name}</span>
                </div>
                <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                  <span>{formatFileSize(file.size)}</span>
                </div>
                <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      onRemoveFile(fileType)
                    }}
                    className="flex items-center justify-center gap-2"
                  >
                    <X className="h-4 w-4" />
                    Remove File
                  </Button>
                </div>
              </div>
            ) : (
              <>
                <Upload className="h-8 w-8 mx-auto mb-4 text-muted-foreground" />
                <p className="text-muted-foreground">Click to browse or drag and drop your file here</p>
              </>
            )}
          </div>
        </Label>
      </CardContent>
    </Card>
  )
}