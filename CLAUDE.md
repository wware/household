# Household AI Assistant

I want to create a shared AI assistant for my household that tracks and
coordinates information across multiple areas: schedules, medical appointments,
pet care, travel plans, household maintenance, grocery needs, and other daily
logistics.

- Shared account between household members with different communication styles
  where each person can develop their own preferred way of interacting with the
  AI while accessing the same underlying household information
- As a web interface, we both have Android phones, I like Chrome, she likes Firefox
- I've got some Philips Hue lights around the house that it would be good to be
  able to control
- Goal is practical household coordination and reducing communication gaps
  between partners
- Privacy is manageable since it's just my partner and me, no children
- Looking to prototype this as a personal solution first, document what works,
  potentially share the approach with others later

Let's code this thing in Python with FastAPI/uvicorn.

## Things to track

- Medical appointments, pet care schedules, maintenance reminders, inventory
  (groceries, supplies), travel coordination, household tasks
- To-do lists on a per-topic basis
- Web search, trivia search, TV schedules, weather
- Games would be cool if we can find something appealing (might only work in
  browser?)
