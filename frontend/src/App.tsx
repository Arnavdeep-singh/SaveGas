import { useEffect, useState } from 'react'
import './App.css'

type Station = {
  id: number
  name: string
  brand: string
  latitude: number
  longitude: number
}

const apiBase = (import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '')

function App() {
  const [stations, setStations] = useState<Station[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    const timeout = window.setTimeout(() => controller.abort(), 10000)
    let active = true

    async function loadStations() {
      try {
        const response = await fetch(`${apiBase}/api/stations`, { signal: controller.signal })
        if (!response.ok) {
          throw new Error(response.status === 503
            ? 'The station database is unavailable. Please try again.'
            : `Could not load stations (HTTP ${response.status}).`)
        }
        const data: Station[] = await response.json()
        if (active) setStations(data)
      } catch (cause) {
        if (active) {
          setError(controller.signal.aborted
            ? 'Loading stations timed out. Please try again.'
            : cause instanceof TypeError
              ? 'Cannot reach SaveGas. Check that the backend is running.'
              : cause instanceof Error ? cause.message : 'Could not load stations.')
        }
      } finally {
        window.clearTimeout(timeout)
        if (active) setLoading(false)
      }
    }

    void loadStations()
    return () => {
      active = false
      window.clearTimeout(timeout)
      controller.abort()
    }
  }, [attempt])

  return (
    <main className="stations-page">
      <h1>SaveGas</h1>
      <h2>Stations</h2>
      {loading ? <p role="status">Loading stations...</p> : error ? (
        <div role="alert">
          <p>{error}</p>
          <button onClick={() => {
            setLoading(true)
            setError(null)
            setAttempt(value => value + 1)
          }}>Try again</button>
        </div>
      ) : stations.length === 0 ? (
        <p>No stations yet. Add one using the station API to get started.</p>
      ) : (
        <ul className="station-list">
          {stations.map(station => (
            <li key={station.id}>
              <h3>{station.name}</h3>
              <p>{station.brand}</p>
              <small>Coordinates: {station.latitude}, {station.longitude}</small>
            </li>
          ))}
        </ul>
      )}
    </main>
  )
}

export default App
