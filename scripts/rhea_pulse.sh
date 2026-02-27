#!/bin/bash
# rhea_pulse.sh — rhythm keeper. Water, food, music, rest.
# Usage: bash scripts/rhea_pulse.sh &
# Kill:  kill $(cat /tmp/rhea_pulse.pid)

echo $$ > /tmp/rhea_pulse.pid
echo "[pulse] Started at $(date +%H:%M). PID $$"

WATER_INTERVAL=2400    # 40 min
FOOD_INTERVAL=10800    # 3 hours
REST_INTERVAL=5400     # 90 min (ultradian cycle)

last_water=$(date +%s)
last_food=$(date +%s)
last_rest=$(date +%s)

notify() {
    osascript -e "display notification \"$1\" with title \"Rhea\" sound name \"Tink\"" 2>/dev/null
}

now_hour() {
    date +%H | sed 's/^0//'
}

# TODO(human): music_for_phase — pick playlist/genre per work phase
# This function receives one argument: "focus", "rest", or "wind-down"
# Use it to control Apple Music, Spotify, or whatever you use.
# Examples:
#   osascript -e 'tell application "Music" to play playlist "Deep Focus"'
#   open "spotify:playlist:37i9dQZF1DWZeKCadgRdKQ"
music_for_phase() {
    local phase="$1"
    echo "[pulse] Phase: $phase (music not configured yet)"
}

while true; do
    now=$(date +%s)
    hour=$(now_hour)

    # Water
    if (( now - last_water >= WATER_INTERVAL )); then
        notify "💧 Выпей воды"
        last_water=$now
    fi

    # Food (only 8:00-22:00)
    if (( now - last_food >= FOOD_INTERVAL )) && (( hour >= 8 )) && (( hour <= 22 )); then
        notify "🍽 Поешь что-нибудь"
        last_food=$now
    fi

    # Rest (ultradian 90min)
    if (( now - last_rest >= REST_INTERVAL )); then
        notify "⏸ 90 минут прошло. Встань, потянись."
        music_for_phase "rest"
        last_rest=$now
    fi

    # Time-based music phases
    if (( hour >= 6 )) && (( hour < 10 )); then
        : # morning — could auto-start gentle playlist
    elif (( hour >= 10 )) && (( hour < 18 )); then
        : # work — focus music
    elif (( hour >= 22 )); then
        : # wind-down
    fi

    sleep 60
done
