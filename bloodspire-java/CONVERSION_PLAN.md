# Bloodspire Java Conversion Plan

## Project Overview
Complete 1:1 conversion of the Bloodspire Python game to Java, maintaining all functionality.

## Architecture
- **Backend Server**: Java HTTP server (using Jetty) replacing `league_server.py`
- **Desktop Client**: Java Swing application replacing the HTML/JavaScript client
- **Build System**: Maven
- **Java Version**: Java 17
- **JSON Library**: Gson
- **HTTP Server**: Jetty 11

## Project Structure
```
bloodspire-java/
├── pom.xml
├── src/main/java/com/bloodspire/
│   ├── model/          # Core data models (Warrior, Team, Race, Weapon, etc.)
│   ├── game/           # Game logic (Combat, Matchmaking, Strategy, AI)
│   ├── ai/             # AI team generation and behavior
│   ├── server/         # League server HTTP endpoints
│   ├── gui/            # Desktop client UI (Swing)
│   ├── persistence/    # Save/load functionality
│   └── util/           # Utilities
└── src/main/resources/ # Configuration files
```

## Conversion Phases

### Phase 1: Core Domain Models ✓ (In Progress)
- [x] `RacialModifiers.java` - Complete
- [x] `Race.java` - Complete (all 12 races including NPCs)
- [ ] `Weapon.java` - Weapon definitions and utilities
- [ ] `Armor.java` - Armor definitions
- [ ] `Strategy.java` - Fighting strategies
- [ ] `Warrior.java` - Warrior class with stats, skills, injuries
- [ ] `Team.java` - Team management (5 warriors per team)

### Phase 2: Game Logic
- [ ] `Combat.java` - Fight simulation engine
- [ ] `Matchmaking.java` - Fight card building
- [ ] `Narrative.java` - Fight narrative generation
- [ ] `ScoutReport.java` - Scouting system
- [ ] `Newsletter.java` - Turn newsletters

### Phase 3: Persistence
- [ ] `SaveManager.java` - Save/load teams and game state
- [ ] `AccountManager.java` - Manager accounts
- [ ] `ChampionState.java` - Champion tracking

### Phase 4: AI Systems
- [ ] `AIGenerator.java` - AI warrior creation
- [ ] `AILeagueTeams.java` - 12 AI league teams
- [ ] `AIStrategies.java` - AI strategy assignment

### Phase 5: League Server
- [ ] `LeagueServer.java` - Main HTTP server
- [ ] `LeagueHandler.java` - Request handlers
- [ ] `AdminPanel.java` - Admin interface

### Phase 6: Desktop GUI
- [ ] `MainMenu.java` - Main menu screen
- [ ] `TeamScreen.java` - Team roster view
- [ ] `WarriorSetupScreen.java` - Warrior configuration
- [ ] `FightLogScreen.java` - Fight results viewer
- [ ] `LeagueClient.java` - League connectivity

## Current Status
**Phase 1 Progress: 2/6 classes complete (33%)**

### Completed Files:
1. `pom.xml` - Maven build configuration
2. `RacialModifiers.java` - All racial modifier fields and builder
3. `Race.java` - All 12 races with full modifiers

### Next Steps:
1. Create `Weapon.java` with all 44 weapons
2. Create `Armor.java` with armor types
3. Create `Strategy.java` with fighting styles and triggers
4. Create `Warrior.java` - the core warrior entity
5. Create `Team.java` - team management

## Key Design Decisions

### Builder Pattern
All complex objects use the Builder pattern for clean construction, matching Python's dataclass flexibility.

### Static Initialization
Race and Weapon registries use static initialization blocks, similar to Python module-level constants.

### JSON Serialization
Gson annotations will be added for save/load compatibility with existing Python saves where possible.

### Thread Safety
The league server uses thread-safe collections and synchronization, matching Python's threading.Lock.

## Notes
- All game mechanics must remain identical to Python version
- Combat calculations must produce same results
- Save format should be compatible or migratable
- The desktop GUI should feel native but maintain the same workflow as the HTML client
