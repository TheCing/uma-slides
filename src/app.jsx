import { useState } from 'preact/hooks'
import { SlideViewer } from './components/SlideViewer'
import { EventPicker } from './components/EventPicker'
import index from './data/index.json'
import './styles/slides.css'

const dataModules = import.meta.glob('./data/slides-*.json', { eager: true })

function getEventData(file) {
  const match = Object.entries(dataModules).find(([path]) => path.endsWith(file))
  return match ? match[1].default : null
}

export function App() {
  const [selectedFile, setSelectedFile] = useState(null)

  if (!selectedFile) {
    return <EventPicker events={index.events} onSelect={setSelectedFile} />
  }

  const data = getEventData(selectedFile)
  if (!data) return null

  return (
    <SlideViewer
      slides={data.slides}
      event={data.event}
      onBack={() => setSelectedFile(null)}
    />
  )
}
