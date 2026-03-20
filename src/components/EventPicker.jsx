const base = import.meta.env.BASE_URL

export function EventPicker({ events, onSelect }) {
  return (
    <div class="event-picker">
      <h1 class="picker-title">Oshi Award Slides</h1>
      <p class="picker-subtitle">Select a Champion's Meeting event</p>
      <div class="event-grid">
        {events.map((evt) => (
          <button
            key={evt.id}
            class="event-card"
            onClick={() => onSelect(evt.file)}
          >
            <img
              class="event-card-icon"
              src={`${base}${evt.icon}`}
              alt={evt.name}
              draggable={false}
            />
            <div class="event-card-info">
              <span class="event-card-id">{evt.id}</span>
              <span class="event-card-name">{evt.name}</span>
            </div>
            <span class="event-card-count">{evt.slideCount} slides</span>
          </button>
        ))}
      </div>
    </div>
  )
}
