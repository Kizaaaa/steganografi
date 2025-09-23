"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { FileAudio, File } from "lucide-react"
import { FileUpload } from "@/components/FileUpload"
import { RadioSection } from "@/components/RadioSection"
import { useStegoForm } from "@/hooks/useStegoForm"
import { useFileUpload } from "@/hooks/useFileUpload"

export function StegoForm() {
  const { input, updateInput, handleSubmit } = useStegoForm()
  const {
    dragOver,
    handleFileUpload,
    handleDragOver,
    handleDragLeave,
    handleDrop,
    handleRemoveFile,
  } = useFileUpload()

  const encryptionOptions = [
    { value: "yes", label: "Yes", id: "yesForEncrypt" },
    { value: "no", label: "No", id: "noForEncrypt" },
  ]

  const randomOptions = [
    { value: "yes", label: "Yes", id: "yesForRandom" },
    { value: "no", label: "No", id: "noForRandom" },
  ]

  const lsbOptions = [
    { value: "1 bit lsb", label: "1 bit LSB", id: "1 bit lsb" },
    { value: "2 bit lsb", label: "2 bit LSB", id: "2 bit lsb" },
    { value: "3 bit lsb", label: "3 bit LSB", id: "3 bit lsb" },
    { value: "4 bit lsb", label: "4 bit LSB", id: "4 bit lsb" },
  ]

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Audio File Upload */}
        <FileUpload
          file={input.audioFile}
          fileType="audio"
          accept="audio/mpeg"
          title="Audio File (cover message)"
          description="Upload audio file (MP3)"
          icon={FileAudio}
          onFileUpload={(file, type) => handleFileUpload(file, type, updateInput)}
          onRemoveFile={(type) => handleRemoveFile(type, updateInput)}
          dragOver={dragOver}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={(e, type) => handleDrop(e, type, updateInput)}
        />

        {/* Document File Upload */}
        <FileUpload
          file={input.documentFile}
          fileType="document"
          accept="*/*"
          title="Secret Message File (to hide)"
          description="Upload any file (PDF, DOC, TXT, image, etc.)"
          icon={File}
          onFileUpload={(file, type) => handleFileUpload(file, type, updateInput)}
          onRemoveFile={(type) => handleRemoveFile(type, updateInput)}
          dragOver={dragOver}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={(e, type) => handleDrop(e, type, updateInput)}
        />

        {/* Message Encryption */}
        <RadioSection
          title="Message Encryption"
          description="Do you want to encrypt this message?"
          value={input.encrypt}
          onValueChange={(value) => updateInput({ encrypt: value })}
          options={encryptionOptions}
          layout="horizontal"
        />

        {/* Insert Message Start Point */}
        <RadioSection
          title="Insert Message Start Point"
          description="Do you want to randomize the start point of the message insertion?"
          value={input.random}
          onValueChange={(value) => updateInput({ random: value })}
          options={randomOptions}
          layout="horizontal"
        />

        {/* n-LSB */}
        <RadioSection
          title="n-LSB"
          description="Choose n-LSB for message insertion"
          value={input.lsb}
          onValueChange={(value) => updateInput({ lsb: value })}
          options={lsbOptions}
          layout="vertical"
        />

        {/* Stego Key */}
        <Card>
          <CardHeader>
            <CardTitle>Stego Key</CardTitle>
            <CardDescription>
              Stego key will be used for encryption and seed for random point generator
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Input
              placeholder="Enter stego key"
              value={input.stegoKey}
              onChange={(e) => updateInput({ stegoKey: e.target.value })}
            />
          </CardContent>
        </Card>

        <div className="flex justify-end pt-6">
          <Button type="submit" size="lg" className="bg-accent hover:bg-accent/90 text-accent-foreground px-8">
            Encrypt file
          </Button>
        </div>
      </form>
    </div>
  )
}