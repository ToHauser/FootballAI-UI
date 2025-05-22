import React, { useEffect, useState } from "react"
import {
  Streamlit,
  withStreamlitConnection,
  ComponentProps,
} from "streamlit-component-lib"

interface Player {
  id: string
  bbox: [number, number, number, number]
}

interface Props extends ComponentProps {
  args: {
    image: string
    players: Player[]
    assignments: Record<string, { team: "1" | "2"; removed: boolean }>
    colors: { "1": string; "2": string; removed: string }
    width: number    
    height: number   
    scale: number
  }
}

const MyComponent = ({ args }: Props) => {
  const [assignments, setAssignments] = useState<Record<
    string,
    { team: "1" | "2"; removed: boolean }
  >>(() => args.assignments || {})

  // 📦 Synchronisiere neue Props von Streamlit in state
  useEffect(() => {
    setAssignments(args.assignments || {})
  }, [args.assignments])
  useEffect(() => {
    Streamlit.setFrameHeight() 
  }, [assignments, args.image, args.players])
  // 🖱️ Klick-Handler für Bounding Boxes
  const onBoxClick = (id: string, shiftKey: boolean) => {
    const current = assignments[id] || { team: "1", removed: false }

    const updated: Record<string, { team: "1" | "2"; removed: boolean }> = {
      ...assignments,
      [id]: shiftKey
        ? { ...current, removed: !current.removed }
        : {
            team: current.team === "1" ? "2" : "1",
            removed: false,
          },
    }

    console.log("🧪 Updated:", updated)

    setAssignments(updated)
    Streamlit.setComponentValue(updated)
  }

  // ❗ Wichtige Prüfung: Daten überhaupt da?
if (!args.image || !args.players || !args.colors) {
  return <div>⛔ Keine Daten empfangen.</div>
}
const scale = args.scale || 1  // fallback = 1
    return (
        <div
          style={{
            position: "relative",
            display: "inline-block",
            width: `${args.width * scale}px`
          }}
        >
        <img
          src={`data:image/png;base64,${args.image}`}
          alt="Frame"
          style={{
            display: "block",
            width: "100%",   // füllt Wrapper
            height: "auto",
            border: "1px solid red"
          }}
        />

    {args.players.map((player) => {
      const a = assignments[player.id] || { team: "1", removed: false }
      const color = a.removed ? args.colors.removed : args.colors[a.team]
      const [x1, y1, x2, y2] = player.bbox
      return (
        <div
          key={player.id}
          onClick={(e) => onBoxClick(player.id, e.shiftKey)}
          style={{
            position: "absolute",
            top: `${y1 * scale}px`,
            left: `${x1 * scale}px`,
            width: `${(x2 - x1) * scale}px`,
            height: `${(y2 - y1) * scale}px`,
            border: `2px solid ${color}`,
            backgroundColor: "rgba(0,0,0,0.0)",
            boxSizing: "border-box",
            cursor: "pointer",
            zIndex: 10
          }}
        />
      )
    })}
  </div>
)
}

export default withStreamlitConnection(MyComponent)
