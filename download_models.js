import fs from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"
import { Readable } from "node:stream"
import { finished } from "node:stream/promises"

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const download = async (url, destPath, description) => {
  if (fs.existsSync(destPath)) {
    const stats = fs.statSync(destPath)
    if (stats.size > 10000) {
      const sizeMb = (stats.size / (1024 * 1024)).toFixed(2)
      console.log(`[OK] ${description} already exists (${sizeMb} MB).`)
      return true
    }
  }

  console.log(`\n[DOWNLOADING] ${description}...`)
  console.log(`URL: ${url}`)
  console.log(`Destination: ${destPath}`)

  try {
    const response = await fetch(url, {
      headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
      },
      redirect: "follow"
    })

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status} ${response.statusText}`)
    }

    const totalBytes = Number(response.headers.get("content-length")) || 0
    let downloadedBytes = 0

    const fileStream = fs.createWriteStream(destPath)
    const reader = response.body.getReader()

    const customReadable = new Readable({
      async read() {
        try {
          const { done, value } = await reader.read()
          if (done) {
            this.push(null)
            return
          }
          downloadedBytes += value.length
          if (totalBytes > 0) {
            const percent = ((downloadedBytes / totalBytes) * 100).toFixed(1)
            const downMb = (downloadedBytes / (1024 * 1024)).toFixed(2)
            const totalMb = (totalBytes / (1024 * 1024)).toFixed(2)
            process.stdout.write(`\rProgress: ${percent}% (${downMb} MB / ${totalMb} MB)`)
          }
          this.push(value)
        } catch (error) {
          this.destroy(error)
        }
      }
    })

    await finished(customReadable.pipe(fileStream))
    console.log(`\n[SUCCESS] ${description} saved!`)
    return true
  } catch (error) {
    console.error(`\n[ERROR] Failed to download ${description}:`, error.message)
    if (fs.existsSync(destPath)) {
      try {
        fs.unlinkSync(destPath)
      } catch {
        // ignore cleanup error
      }
    }
    return false
  }
}

const main = async () => {
  const modelsDir = path.join(__dirname, "models")
  if (!fs.existsSync(modelsDir)) {
    fs.mkdirSync(modelsDir, { recursive: true })
  }

  // 1. YOLO Plate Detection (YOLOv8 ONNX)
  const yoloUrl = "https://huggingface.co/ml-debi/yolov8-license-plate-detection/resolve/main/best.onnx?download=true"
  const yoloDest = path.join(modelsDir, "yolov8n-plate.onnx")
  await download(yoloUrl, yoloDest, "YOLOv8 Plate Detection")

  // 2. CRNN OCR Model (OpenCV CRNN ONNX)
  const crnnUrl = "https://huggingface.co/opencv/text_recognition_crnn/resolve/main/text_recognition_CRNN_EN_2021sep.onnx?download=true"
  const crnnDest = path.join(modelsDir, "crnn-plate-ocr.onnx")
  await download(crnnUrl, crnnDest, "CRNN OCR Model")
}

main()
