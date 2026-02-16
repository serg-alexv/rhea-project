# ARCHITECTURE FREEZE — Rhea iOS App
> Frozen: 2026-02-16 | Author: B2 | Status: DRAFT (pending LEAD review)

## Core / UI Boundary

```
┌─────────────────────────────────────────────────────┐
│                    UI Layer (SwiftUI)                │
│  Views → ViewModels → Domain Events                 │
├─────────────────────────────────────────────────────┤
│                   Domain Layer                       │
│  UseCases → Repositories (protocols) → Entities     │
├─────────────────────────────────────────────────────┤
│                Infrastructure Layer                  │
│  Persistence (SwiftData) │ HealthKit │ Sensors       │
│  Local ML (CoreML)       │ Network (optional)        │
└─────────────────────────────────────────────────────┘
```

**Rule:** UI imports Domain. Domain imports nothing. Infrastructure implements Domain protocols.

## Folder Structure

```
Rhea/
├── App/
│   ├── RheaApp.swift              # Entry point
│   └── AppDelegate.swift          # Background tasks, notifications
├── Domain/
│   ├── Entities/
│   │   ├── DailyBlueprint.swift   # The core output: what to do today
│   │   ├── UserProfile.swift      # Neuroprofile + circadian state
│   │   ├── Ritual.swift           # Single action item with timing
│   │   └── BiometricReading.swift # HRV, sleep, light, activity
│   ├── UseCases/
│   │   ├── GenerateBlueprint.swift
│   │   ├── UpdateProfile.swift
│   │   └── ProcessBiometrics.swift
│   └── Protocols/
│       ├── BlueprintRepository.swift
│       ├── ProfileRepository.swift
│       └── BiometricSource.swift
├── UI/
│   ├── Blueprint/
│   │   ├── BlueprintView.swift
│   │   └── BlueprintViewModel.swift
│   ├── Onboarding/
│   │   ├── OnboardingFlow.swift
│   │   └── PermissionsView.swift
│   ├── Settings/
│   │   └── SettingsView.swift
│   └── Components/
│       ├── RitualCard.swift
│       └── TimelineView.swift
├── Infrastructure/
│   ├── Persistence/
│   │   ├── SwiftDataStore.swift
│   │   └── Models/               # SwiftData @Model classes
│   ├── HealthKit/
│   │   └── HealthKitAdapter.swift
│   ├── Sensors/
│   │   └── LightSensorAdapter.swift
│   └── ML/
│       └── CircadianPredictor.swift
├── Resources/
│   ├── Assets.xcassets
│   └── Rituals/                  # Bundled ritual database (JSON)
└── Tests/
    ├── DomainTests/
    └── IntegrationTests/
```

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Files | PascalCase, matches type name | `DailyBlueprint.swift` |
| Types | PascalCase | `struct DailyBlueprint` |
| Properties | camelCase | `var morningRituals: [Ritual]` |
| Protocols | PascalCase, noun or adjective | `BlueprintRepository` |
| Use cases | Verb phrase | `GenerateBlueprint` |
| View models | TypeNameViewModel | `BlueprintViewModel` |
| Tests | TypeName_Tests | `GenerateBlueprint_Tests` |

## Persistence Strategy

**Primary:** SwiftData (local-first, offline-only for MVP)

| Data | Storage | Sync |
|------|---------|------|
| User profile | SwiftData | None (MVP) |
| Daily blueprints | SwiftData | None (MVP) |
| Biometric readings | HealthKit (read-only) | Apple Health |
| Ritual database | Bundled JSON + SwiftData cache | None |
| Settings | UserDefaults | None |

**No server dependency in MVP.** Everything runs offline. Network layer exists only as a protocol stub for future bridge integration.

## Key Constraints (from ADRs)

1. **ADHD-first** (ADR-003): No questionnaires. No complex navigation. Maximum 2 taps to today's blueprint.
2. **Passive profiling** (ADR-005): Profile built from HealthKit + device sensors, not user input.
3. **Cheap-first** (ADR-008): On-device CoreML for routine predictions. Bridge API only for deep analysis (future).
4. **Hunter-gatherer baseline** (ADR-006): Default rituals derived from circadian biology, not productivity culture.

## What This Freeze Means

- Folder structure above is canonical. New files go in the matching folder.
- Domain layer has zero dependencies on UIKit, SwiftUI, or any framework.
- No "networking layer" in MVP. Stubs only.
- SwiftData is the persistence choice. No Core Data, no Realm, no SQLite directly.
- All biometrics come through HealthKit adapter, never accessed directly from UI.
