# Future Roadmap: Household AI Assistant

## Phase 1: AWS Migration & Production Infrastructure

### Development phase

- FastAPI/uvicorn Python server running in Docker locally
- SQLite database for persistence
- Development-friendly but not production-ready

### Moving to AWS

#### Server Deployment

- **Container Registry:** Use Amazon ECR (Elastic Container Registry) to store the Docker image
- **Compute:** Options include:
  - **ECS (Elastic Container Service)** - Simpler, AWS-managed containers
  - **EKS (Elastic Kubernetes Service)** - If we want orchestration later
  - **Lambda** - If we refactor to serverless (less ideal for our use case)
- **Load Balancing:** ALB (Application Load Balancer) for reliability & auto-scaling
- **Auto-scaling:** ECS Service can scale based on demand

#### Database Migration

SQLite won't work in AWS production because:
- No persistent file system across container instances
- Database file would be lost when container restarts
- Can't be shared between multiple server instances

**Options:**

1. **Amazon RDS (Relational Database Service)** - Most Straightforward

   - PostgreSQL (recommended) or MySQL
   - Managed backups, failover, monitoring
   - Easy to migrate from SQLite using tools like `pgloader`
   - Cost: ~$15-50/month for hobby usage
   - Minimal code changes needed in app.ts (just update Prisma connection string)

2. **Amazon DynamoDB** - NoSQL, Serverless

   - No server to manage
   - Pay-per-request pricing (good for low traffic)
   - Would require significant refactoring of Prisma queries
   - Less ideal for our relational schema (users → appointments, tasks, etc.)

3. **Aurora Serverless** - Hybrid approach

   - PostgreSQL-compatible
   - Auto-scales to zero when not in use
   - Good for unpredictable traffic patterns
   - Cost: ~$1-10/month for low usage

**Recommendation:** Start with **Amazon RDS PostgreSQL**

- Minimal app changes (Prisma handles most of it)
- Familiar SQL syntax
- Great free tier eligibility (12 months)
- Easy to understand and manage

#### Migration Steps

1. Set up RDS PostgreSQL instance
2. Update `DATABASE_URL` in docker-compose.yml to RDS endpoint
3. Run `npx prisma migrate deploy` to create schema
4. Test locally first, then deploy to ECS
5. Set up automated backups & monitoring

#### Hosting the Web App

- Serve the React/vanilla JS frontend from:
  - **CloudFront** (CDN) + **S3** for static files (cheapest: ~$0.50-5/month)
  - Or serve from the same ECS container (simpler, slightly more expensive)

---

## Phase 2: Raspberry Pi Hardware Portals

### Vision

Physical "smart home stations" throughout the house (and portable) with:

- 7-10" touchscreen
- Microphone & speaker for voice interaction
- Status display (weather, tasks, appointments)
- Quick action buttons

### Hardware Stack

#### Base Components

- **Raspberry Pi 5** (or Pi 4 if budget-constrained)
  - 4GB RAM minimum, 8GB recommended
  - ~$60-80

- **7" Official Touchscreen** or USB touchscreen

  - $50-80

- **Audio Module**

  - USB microphone + speaker combo (~$30-50)
  - OR Raspberry Pi official mic + good USB speaker

- **Case**

  - 3D-printed or commercial enclosure
  - Mount on wall or stand on counter
  - ~$20-50

- **Power Supply**

  - USB-C 30W power adapter
  - ~$15

**Estimated Cost per Portal:** $150-250

### Software Architecture

#### Option A: Lightweight Browser-Based (Simpler)

1. Raspbian OS running on Pi
2. Chromium browser in kiosk mode pointing to `http://[server-ip]:3000`
3. Local microphone input handled by Web Audio API
4. Speech recognition via Web Speech API or Vosk
5. Text-to-speech for responses via browser's Web Speech API or espeak
6. **Pros:** Minimal code changes, works with current codebase
7. **Cons:** Latency, internet dependency, less native feel

#### Option B: Native Python/Rust Backend (Better UX)

1. Raspbian OS with Python/Rust daemon running on Pi
2. Custom touchscreen UI (Qt/Kivy for Python, or native Rust)
3. Local speech recognition (Vosk or Whisper)
4. Local speech synthesis (pyttsx3 or festival)
5. WebSocket connection to main server for smart home operations
6. Can work offline with cached data
7. **Pros:** Responsive, low latency, beautiful native UI
8. **Cons:** More code to maintain, different language stack

**Recommendation:** Start with **Option A** (browser-based)

- Reuse existing frontend
- Learn hardware integration
- Upgrade to Option B later if needed

### Key Features for Portal

#### Display Layer
```
┌─────────────────────────┐
│    🏠 Household HQ      │  ← Title
├─────────────────────────┤
│ 🌡️  72°F ☁️  Partly...   │  ← Weather widget
├─────────────────────────┤
│ 📋 Tasks (3 due today)  │  ← Quick tasks summary
│   □ Grocery shopping    │
│   □ Pay electric bill   │
├─────────────────────────┤
│ 🗓️  Appointments        │  ← Next appointment
│   Dentist - 2:00 PM     │
├─────────────────────────┤
│ 🎙️ Listening...         │  ← Voice interaction
└─────────────────────────┘
```

#### Voice Interaction

```
User: "Hey, what's on my task list?"
Portal:
  - Listens using microphone
  - Sends audio to Vosk (local) or cloud speech-to-text
  - Parses intent ("list tasks")
  - Calls API endpoint
  - Reads response aloud using text-to-speech
  - Displays on screen
```

#### Smart Home Integration (Future)

- Philips Hue light control via voice
- Check door lock status
- View security camera feeds
- Thermostat adjustments

---

## Phase 3: Portable Portal & Remote Access

### Portable Use Case

"Take a portal while traveling to check on the house"

#### How It Would Work

1. **Portal Connectivity**

   - Portable Pi battery pack (5000mAh = ~6-8 hours runtime)
   - Connects to WiFi at destination (hotel, rental, cabin)
   - All data synced from main server

2. **Remote Server Access**

   - Use ngrok (current setup) or proper VPN
   - Portal authenticates with username/password
   - Shows real-time status from home server

3. **Use Cases**

   ```
   Scenario 1: Vacation Home Check-In
   - Browse upcoming appointments & tasks
   - Check weather at home
   - View security camera feeds (if integrated)
   - Send voice reminders to household members via speaker at home

   Scenario 2: Grocery Shopping Trip
   - Carry portal to store
   - Voice: "Add milk to grocery list"
   - Check off items as you shop
   - Sync back to home server

   Scenario 3: Work Trip
   - Check household status from hotel room
   - See if tasks are getting done
   - Monitor calendar for upcoming events
   - Emergency: Call household members via two-way audio
   ```

#### Implementation

**Portal Authentication**

```typescript
// New endpoint: /api/auth/login
POST /api/auth/login
{
  "username": "user@household.local",
  "password": "secure_password"
  // Returns JWT token for this session
}

// Validate JWT on all API calls
middleware: verifyToken()
```

**Remote Sync**
- Portal pulls data from server every 30 seconds
- Two-way communication for voice messages
- Offline cache using localStorage for critical data
- Auto-sync when connection restored

**Security Considerations**
- TLS/HTTPS for all remote connections
- Rate limiting on auth attempts
- Token expiration (2 hour session)
- Optional: End-to-end encryption for sensitive data
- Option to disable remote access for privacy

---

## Phase 4: Voice Assistant Enhancement (Longer Term)

### Natural Language Processing

- **Vosk** (open-source, runs locally) for initial MVP
- **Rhasspy** (complete voice assistant framework)
- **Home Assistant** integration (if moving toward that ecosystem)

### Example Voice Commands

```
"What's my schedule today?"
"Add 'pick up dry cleaning' to my tasks"
"Is anyone home?" (via security integration)
"Call [family member]" (two-way audio between portals)
"Set reminder: water plants in 30 minutes"
"Show me the grocery list"
"What's the weather?" (with location awareness)
```

### ML/Personalization

- Learn user voice patterns
- Predict task completions
- Suggest optimal scheduling for household tasks
- Seasonal reminders (yard work, HVAC maintenance)

---

## Technical Debt & Infrastructure

### Current State

- ✅ Local Docker container
- ✅ SQLite database
- ✅ Basic REST API
- ✅ Web frontend
- ❌ No authentication
- ❌ No database backups
- ❌ No monitoring/logging

### Pre-AWS Requirements

1. **Add User Authentication**

   - JWT tokens
   - Password hashing (bcrypt)
   - Session management

2. **Add Logging & Monitoring**

   - Winston or Bunyan for logging
   - CloudWatch integration for AWS

3. **Database Backup Strategy**

   - Automated daily backups
   - Point-in-time recovery
   - Tested restore procedures

4. **Environment Configuration**

   - `.env` files for secrets
   - Separate configs for dev/staging/production
   - Never commit secrets to git

---

## Timeline & Priority

### Immediate (Next 1-2 weeks)

- [ ] Set up AWS account & RDS PostgreSQL
- [ ] Migrate database from SQLite to PostgreSQL
- [ ] Deploy server to ECS
- [ ] Set up CloudFront CDN for web frontend

### Short Term (1-2 months)

- [ ] Add user authentication
- [ ] Order Raspberry Pi hardware
- [ ] Set up kiosk-mode browser on Pi
- [ ] Create portal-specific UI layout

### Medium Term (2-4 months)

- [ ] Implement voice interface (Vosk)
- [ ] Add Philips Hue integration
- [ ] Portable portal battery/power management
- [ ] Remote access & security hardening

### Long Term (6+ months)

- [ ] Custom native portal UI (Python/Rust)
- [ ] Security camera integration
- [ ] Advanced ML-based scheduling
- [ ] Multi-household support
- [ ] Mobile app (React Native)

---

## Cost Estimates

| Component | Monthly Cost | Notes |
|-----------|------------|-------|
| AWS ECS | $5-15 | Low traffic, auto-scaling |
| RDS PostgreSQL | $0-15 | Free tier then ~$15 |
| CloudFront | $0-5 | Mostly free tier |
| **Server Total** | **$5-35** | Production AWS |
| | | |
| Raspberry Pi Hardware | $150-250 | One-time per portal |
| Power (yearly) | ~$10 | Electricity cost |
| Internet | Included | Uses home WiFi |
| **Per Portal** | **$150-250** | One-time + minimal ongoing |

---

## Risk Mitigation

1. **Data Loss**

   - RDS automated backups (daily)
   - Manual export to S3 (weekly)

2. **Service Downtime**

   - Auto-scaling & load balancing
   - Health checks & auto-recovery
   - Fallback to local portal if main server down

3. **Security Breach**

   - Strong authentication & authorization
   - End-to-end encryption option
   - Regular security audits
   - Limit portal remote access features

4. **Cost Overruns**

   - Set AWS billing alerts
   - Use free tier aggressively
   - Monitor for unused resources

---

## Success Metrics

- ✅ Server uptime > 99%
- ✅ Portal voice recognition accuracy > 90%
- ✅ Response latency < 500ms
- ✅ Daily active portals (all working)
- ✅ Task/appointment sync within 30 seconds
- ✅ User satisfaction with voice commands

---

## Questions for Future Discussion

1. Should we build native mobile app or just use web?
2. How many portals initially? (1, 2, or more?)
3. Budget limit for hardware?
4. Priority: voice control or touchscreen UI first?
5. Integrate with existing smart home (Hue, thermostats)?
6. Do we want offline-first capabilities?
7. How much remote access is acceptable for privacy?
