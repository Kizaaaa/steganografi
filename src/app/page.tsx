"use client"

import type React from "react"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Upload, FileAudio, File, Check, X } from "lucide-react"

interface input {
  audioFile: File | null
  documentFile: File | null
  encrypt: string
  random: string
  lsb: string
  stegoKey: string
}

export default function App() {
  const [input, setInput] = useState<input>({
    audioFile: null,
    documentFile: null,
    encrypt: "",
    random: "",
    lsb: "",
    stegoKey: "",
  })

  const [dragOver, setDragOver] = useState<string | null>(null)

  const handleFileUpload = (file: File, type: "audio" | "document") => {
    if (type === "audio") {
      setInput((prev) => ({ ...prev, audioFile: file }))
    } else {
      setInput((prev) => ({ ...prev, documentFile: file }))
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

  const handleDrop = (e: React.DragEvent, type: "audio" | "document") => {
    e.preventDefault()
    setDragOver(null)
    const files = e.dataTransfer.files
    if (files.length > 0) {
      handleFileUpload(files[0], type)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    console.log("Form submitted:", input)
    // Handle form submission here
  }

  const handleRemoveFile = (type: "audio" | "document") => {
    if (type === "audio") {
      setInput((prev) => ({ ...prev, audioFile: null }))
      const audioInput = document.getElementById("audio-upload") as HTMLInputElement
      if (audioInput) audioInput.value = ""
    } else {
      setInput((prev) => ({ ...prev, documentFile: null }))
      const documentInput = document.getElementById("document-upload") as HTMLInputElement
      if (documentInput) documentInput.value = ""
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="bg-card border-b border-border">
        <div className="max-w-4xl mx-auto px-6 py-8">
          <h1 className="text-3xl font-bold text-card-foreground text-balance">Steganography in Audio Files</h1>
          <p className="text-muted-foreground mt-2 text-pretty">
            Steganography in Audio Files Using the Multiple-LSB Method
          </p>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8">
        <form onSubmit={handleSubmit} className="space-y-8">

          {/* Audio File */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileAudio className="h-5 w-5" />
                Audio File (cover message)
              </CardTitle>
              <CardDescription>Upload audio file (MP3)</CardDescription>
            </CardHeader>
            <CardContent>
              <Input
                type="file"
                accept="audio/*"
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  if (file) handleFileUpload(file, "audio")
                }}
                className="hidden"
                id="audio-upload"
              />
              <Label htmlFor="audio-upload" className="cursor-pointer block">
                <div
                  className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                    dragOver === "audio" ? "border-accent bg-accent/5" : "border-border hover:border-accent/50"
                  }`}
                  onDragOver={(e) => handleDragOver(e, "audio")}
                  onDragLeave={handleDragLeave}
                  onDrop={(e) => handleDrop(e, "audio")}
                >
                  {input.audioFile ? (
                    <div className="space-y-4">
                      <div className="flex items-center justify-center gap-2 text-accent">
                        <Check className="h-5 w-5" />
                        <span className="font-medium">{input.audioFile.name}</span>
                      </div>
                      <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                        <span>
                          {input.audioFile.size < 1024 * 1024
                            ? `${(input.audioFile.size / 1024).toFixed(2)} KB`
                            : `${(input.audioFile.size / 1024 / 1024).toFixed(2)} MB`}
                        </span>
                      </div>
                      <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={(e) => {
                            e.preventDefault()
                            e.stopPropagation()
                            handleRemoveFile("audio")
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
                      <p className="text-muted-foreground">Click to browse or drag and drop your audio file here</p>
                    </>
                  )}
                </div>
              </Label>
            </CardContent>
          </Card>

          {/* Secret Message File */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <File className="h-5 w-5" />
                Secret Message File (to hide)
              </CardTitle>
              <CardDescription>Upload any file (PDF, DOC, TXT, image, etc.)</CardDescription>
            </CardHeader>
            <CardContent>
              <Input
                type="file"
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  if (file) handleFileUpload(file, "document")
                }}
                className="hidden"
                id="document-upload"
              />
              <Label htmlFor="document-upload" className="cursor-pointer block">
                <div
                  className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                    dragOver === "document" ? "border-accent bg-accent/5" : "border-border hover:border-accent/50"
                  }`}
                  onDragOver={(e) => handleDragOver(e, "document")}
                  onDragLeave={handleDragLeave}
                  onDrop={(e) => handleDrop(e, "document")}
                >
                  {input.documentFile ? (
                    <div className="space-y-4">
                      <div className="flex items-center justify-center gap-2 text-accent">
                        <Check className="h-5 w-5" />
                        <span className="font-medium">{input.documentFile.name}</span>
                      </div>
                      <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                        <span>
                          {input.documentFile.size < 1024 * 1024
                            ? `${(input.documentFile.size / 1024).toFixed(2)} KB`
                            : `${(input.documentFile.size / 1024 / 1024).toFixed(2)} MB`}
                        </span>
                      </div>
                      <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={(e) => {
                            e.preventDefault()
                            e.stopPropagation()
                            handleRemoveFile("document")
                          }}
                          className="flex items-center gap-2"
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

          {/* Message Encryption */}
          <Card>
            <CardHeader>
              <CardTitle>Message Encryption</CardTitle>
              <CardDescription>Do you want to encrypt this message?</CardDescription>
            </CardHeader>
            <CardContent>
              <RadioGroup
                value={input.encrypt}
                onValueChange={(value) => setInput((prev) => ({ ...prev, encrypt: value }))}
                className="flex gap-6"
              >
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="yesForEncrypt" id="yesForEncrypt" />
                  <Label htmlFor="yesForEncrypt" className="flex items-center gap-2 cursor-pointer">
                    Yes
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="noForEncrypt" id="noForEncrypt" />
                  <Label htmlFor="noForEncrypt" className="flex items-center gap-2 cursor-pointer">
                    No
                  </Label>
                </div>
              </RadioGroup>
            </CardContent>
          </Card>

          {/* Insert Message Start Point */}
          <Card>
            <CardHeader>
              <CardTitle>Insert Message Start Point</CardTitle>
              <CardDescription>Do you want to randomize the start point of the message insertion?</CardDescription>
            </CardHeader>
            <CardContent>
              <RadioGroup
                value={input.random}
                onValueChange={(value) => setInput((prev) => ({ ...prev, random: value }))}
                className="flex gap-6"
              >
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="yesForRandom" id="yesForRandom" />
                  <Label htmlFor="yesForRandom" className="flex items-center gap-2 cursor-pointer">
                    Yes
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="noForRandom" id="noForRandom" />
                  <Label htmlFor="noForRandom" className="flex items-center gap-2 cursor-pointer">
                    No
                  </Label>
                </div>
              </RadioGroup>
            </CardContent>
          </Card>

          {/* n-LSB */}
          <Card>
            <CardHeader>
              <CardTitle>n-LSB</CardTitle>
              <CardDescription>Choose n-LSB for message insertion</CardDescription>
            </CardHeader>
            <CardContent>
              <RadioGroup
                value={input.lsb}
                onValueChange={(value) => setInput((prev) => ({ ...prev, lsb: value }))}
                className="space-y-3"
              >
                {["1 bit LSB", "2 bit LSB", "3 bit LSB", "4 bit LSB"].map((option) => (
                  <div key={option} className="flex items-center space-x-2">
                    <RadioGroupItem value={option.toLowerCase()} id={option.toLowerCase()} />
                    <Label htmlFor={option.toLowerCase()} className="cursor-pointer">
                      {option}
                    </Label>
                  </div>
                ))}
              </RadioGroup>
            </CardContent>
          </Card>

          {/* Stego Key */}
          <Card>
            <CardHeader>
              <CardTitle>Stego Key</CardTitle>
              <CardDescription>Stego key will be used for encryption and seed for random point generator</CardDescription>
            </CardHeader>
            <CardContent>
              <Input
                placeholder="Enter stego key"
                value={input.stegoKey}
                onChange={(e) => setInput((prev) => ({ ...prev, stegoKey: e.target.value }))}
              />
            </CardContent>
          </Card>

          <div className="flex justify-end pt-6">
            <Button type="submit" size="lg" className="bg-accent hover:bg-accent/90 text-accent-foreground px-8">
              Encrypt file
            </Button>
          </div>
        </form>
      </main>
    </div>
  )
}
