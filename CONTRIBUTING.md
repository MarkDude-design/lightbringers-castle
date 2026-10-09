# Contributing to Lightbringer's Castle

Welcome to the Castle! Here's how to add your own bots, rooms, and jokes.

## Adding a New Bot

1. Add to `registry/bots.csv`
2. Create `castle/bots/{bot_id}.json`
3. Add asset reference to `registry/assets.json`

## Adding a New Room

1. Add to `registry/rooms.csv`
2. Create `castle/rooms/{room_id}.json`

## Adding a Joke

Add new entries to a room's `jokes` array:

```json
{
  "setup": "Your setup",
  "punchline": "Your punchline"
}
```

## Scaling Notes

- Keep the CSV files as a master index.
- Use JSON for richer details.
- Keep assets mapped via `asset_key`.
- Organize content by room or bot type as the project grows.
