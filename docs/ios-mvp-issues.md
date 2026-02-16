# iOS Offline Loop MVP — Implementable Issues
> RHEA-IOS-002 | 12 issues | Each has acceptance criteria | No research-only tasks

## Issue 1: Xcode project scaffold
**Create the Xcode project with the frozen folder structure from ARCHITECTURE_FREEZE.md.**

Acceptance criteria:
- [ ] Xcode project compiles with zero warnings on Xcode 16+
- [ ] All folders from ARCHITECTURE_FREEZE.md exist (App, Domain, UI, Infrastructure, Resources, Tests)
- [ ] Minimum deployment target: iOS 17.0
- [ ] SwiftData imported and ModelContainer configured in RheaApp.swift
- [ ] App launches to a blank BlueprintView

## Issue 2: Domain entities
**Implement the four core domain entities as plain Swift structs.**

Files: `Domain/Entities/DailyBlueprint.swift`, `UserProfile.swift`, `Ritual.swift`, `BiometricReading.swift`

Acceptance criteria:
- [ ] `Ritual` has: id (UUID), title, description, timeWindow (start/end), category (enum: morning/midday/evening/night), source (civilization string), biologicalMechanism (string)
- [ ] `DailyBlueprint` has: id, date, rituals ([Ritual] sorted by timeWindow), generatedAt (Date), profileSnapshot (UserProfile)
- [ ] `UserProfile` has: id, chronotype (enum), circadianPhase (Double 0-24h), avgHRV (Double?), sleepDebtHours (Double), lastUpdated (Date)
- [ ] `BiometricReading` has: id, timestamp, type (enum: hrv/sleep/steps/light), value (Double), source (String)
- [ ] Zero framework imports in Domain/Entities (no UIKit, no SwiftUI, no SwiftData)
- [ ] All entities are Codable and Equatable

## Issue 3: Domain protocols
**Define repository and source protocols for the domain layer.**

Files: `Domain/Protocols/BlueprintRepository.swift`, `ProfileRepository.swift`, `BiometricSource.swift`

Acceptance criteria:
- [ ] `BlueprintRepository`: save, fetch by date, fetch latest, delete
- [ ] `ProfileRepository`: save, fetch current, update field
- [ ] `BiometricSource`: fetchReadings(type, dateRange) → async [BiometricReading]
- [ ] All methods are async throws
- [ ] Zero framework imports

## Issue 4: SwiftData persistence layer
**Implement SwiftData models and repository adapters.**

Files: `Infrastructure/Persistence/SwiftDataStore.swift`, `Models/*.swift`

Acceptance criteria:
- [ ] SwiftData @Model classes mirror domain entities
- [ ] `SwiftDataBlueprintRepository` implements `BlueprintRepository` protocol
- [ ] `SwiftDataProfileRepository` implements `ProfileRepository` protocol
- [ ] Mapping functions between domain entities and SwiftData models
- [ ] Unit tests: save → fetch round-trip for each entity
- [ ] ModelContainer configured with automatic migration

## Issue 5: Bundled ritual database
**Create the seed ritual JSON and loader.**

Files: `Resources/Rituals/default_rituals.json`, `Infrastructure/Persistence/RitualLoader.swift`

Acceptance criteria:
- [ ] JSON contains 20+ rituals covering all 4 time categories (morning/midday/evening/night)
- [ ] Each ritual has: title, description, timeWindow, category, source civilization, biological mechanism, scientific reference
- [ ] At least 5 distinct civilizations represented
- [ ] `RitualLoader` decodes JSON into [Ritual] domain entities
- [ ] Unit test: loader returns all rituals, no decode failures

## Issue 6: HealthKit adapter
**Implement the HealthKit biometric source.**

Files: `Infrastructure/HealthKit/HealthKitAdapter.swift`

Acceptance criteria:
- [ ] Implements `BiometricSource` protocol
- [ ] Reads: HRV (heart rate variability), sleep analysis, step count
- [ ] Handles authorization request and denial gracefully
- [ ] Returns empty array (not error) when HealthKit unavailable (Simulator)
- [ ] Unit test with mock HealthKit store

## Issue 7: GenerateBlueprint use case
**Core logic: given a profile and biometrics, produce today's blueprint.**

Files: `Domain/UseCases/GenerateBlueprint.swift`

Acceptance criteria:
- [ ] Input: UserProfile + [BiometricReading] + [Ritual] (available pool)
- [ ] Output: DailyBlueprint
- [ ] Selection logic: filter rituals by chronotype compatibility, sort by timeWindow, limit to 6-8 per day (minimum effective dose)
- [ ] Morning rituals prioritize sensory/body (ADR-003: body before mind)
- [ ] Unit tests: given a fixed profile + readings, output is deterministic
- [ ] No network calls, no side effects

## Issue 8: BlueprintView + ViewModel
**The main screen: today's blueprint as a timeline.**

Files: `UI/Blueprint/BlueprintView.swift`, `BlueprintViewModel.swift`

Acceptance criteria:
- [ ] Shows today's rituals in chronological order
- [ ] Each ritual card shows: title, time window, source civilization, 1-line mechanism
- [ ] Maximum 2 taps from app launch to this screen (ADR-003)
- [ ] Pull-to-refresh regenerates blueprint
- [ ] Empty state when no blueprint exists ("Generating your first blueprint...")
- [ ] Dark mode support
- [ ] VoiceOver accessible (all cards have accessibility labels)

## Issue 9: RitualCard component
**Reusable ritual card with ADHD-optimized design.**

Files: `UI/Components/RitualCard.swift`

Acceptance criteria:
- [ ] Shows title prominently (large, high contrast)
- [ ] Time window as secondary text
- [ ] Source civilization as subtle badge
- [ ] Tap expands to show description + biological mechanism
- [ ] No small text, no low-contrast elements (ADHD-optimized)
- [ ] SwiftUI Preview with sample data

## Issue 10: Onboarding flow
**First-launch flow: HealthKit permissions + chronotype detection.**

Files: `UI/Onboarding/OnboardingFlow.swift`, `PermissionsView.swift`

Acceptance criteria:
- [ ] Maximum 3 screens total
- [ ] Screen 1: "Rhea observes, doesn't interrogate" + HealthKit permission request
- [ ] Screen 2: Initial chronotype inference from current time + device usage patterns (no questionnaire)
- [ ] Screen 3: First blueprint generated and shown
- [ ] Skip button on every screen (generates default blueprint)
- [ ] Onboarding state persisted in UserDefaults (shows only once)

## Issue 11: UpdateProfile use case
**Update user profile from incoming biometric readings.**

Files: `Domain/UseCases/UpdateProfile.swift`

Acceptance criteria:
- [ ] Input: current UserProfile + new [BiometricReading]
- [ ] Updates: avgHRV (rolling 7-day average), sleepDebtHours (based on sleep analysis), circadianPhase (estimated from last sleep/wake)
- [ ] Output: updated UserProfile
- [ ] Handles missing data gracefully (keeps previous values)
- [ ] Unit tests: profile update with various reading combinations

## Issue 12: Background refresh
**Daily blueprint regeneration via background app refresh.**

Files: `App/AppDelegate.swift` (background task registration)

Acceptance criteria:
- [ ] Registers BGAppRefreshTask for daily blueprint generation
- [ ] Triggers at ~05:00 local time (before typical wake)
- [ ] Reads latest HealthKit data, updates profile, generates new blueprint
- [ ] Stores result via BlueprintRepository
- [ ] Falls back gracefully if background refresh denied by system
- [ ] Local notification: "Your blueprint for today is ready" (optional, respects notification permissions)
