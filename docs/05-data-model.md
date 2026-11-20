# 05 — Data model

SQLite only. All tables `snake_case`, plural, explicit `id` PK, `created_at`/`updated_at` UTC.

## Global invariants

- **Emissions are stored as integer grams of CO2e** (`*_grams`). The API/UI display kg with two
  decimals. This avoids float drift.
- **Factor snapshots:** every consumption record stores the factor value, source, and year used
  at calculation time. Historical totals never change when an admin edits a factor.
- **Timestamps are UTC.** Period boundaries use the user's IANA timezone from `user_profiles`.
- **Foreign keys are enforced** (`PRAGMA foreign_keys=ON`) and WAL mode is enabled.
- **User-facing content is bilingual:** `*_en`, `*_ar` for categories, factors, alternatives,
  challenges, badges, articles, notifications, and plan text where applicable.
- **Ownership:** users own their records/goals/plans/documents. Organization accounts scope those
  rows with `organization_id`; individual/household rows leave it null.
- **Soft delete:** records use `status`; users/orgs use `is_active`; documents may be hard-deleted
  only when no record references them.
- **No raw prompt logging:** `ai_usage` stores metadata, not prompt text. Reported responses may
  be stored after PII redaction.
- **Admin actions** on sensitive entities are written to `admin_audit_logs`.
- **Pagination:** list endpoints use `page`, `per_page` (≤ 50), `q`, `sort`.

## Tables

### `organizations`

Purpose: business/organization profile and ownership scope. Owner feature: F01/F13.

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER | no | auto | PK |
| `name_en` | TEXT | no | — | display name |
| `name_ar` | TEXT | yes | null | Arabic display name |
| `slug` | TEXT | no | — | unique, URL-safe |
| `org_type` | TEXT | no | `business` | business/ngo/government/other |
| `industry` | TEXT | yes | null | free text |
| `country` | TEXT | yes | null | ISO-ish text |
| `city` | TEXT | yes | null | free text |
| `size` | TEXT | yes | null | 1-10, 11-50, 51-200, 200+ |
| `contact_email` | TEXT | yes | null | public contact |
| `is_active` | BOOLEAN | no | true | admin can suspend |
| `created_at` | DATETIME | no | UTC now | |
| `updated_at` | DATETIME | no | UTC now | |

Keys/indexes: unique `slug`; index `name_en`, `is_active`.
Relations: one-to-many with `users`, `consumption_records`, `documents`, `goals`, `reduction_plans`.

### `users`

Purpose: account identity and account type. Owner feature: F01.

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER | no | auto | PK |
| `email` | TEXT | no | — | unique, lower-case |
| `password_hash` | TEXT | no | — | werkzeug hash |
| `full_name` | TEXT | no | — | |
| `account_type` | TEXT | no | `individual` | individual/household/organization |
| `organization_id` | INTEGER | yes | null | FK → organizations; required for organization |
| `locale` | TEXT | no | `ar` | en/ar |
| `timezone` | TEXT | no | `UTC` | IANA timezone |
| `is_active` | BOOLEAN | no | true | admin can suspend |
| `is_verified` | BOOLEAN | no | false | no email flow in v1; kept for future |
| `last_login_at` | DATETIME | yes | null | |
| `created_at` | DATETIME | no | UTC now | |
| `updated_at` | DATETIME | no | UTC now | |

Keys/indexes: unique `email`; index `organization_id`, `is_active`, `account_type`.
Relations: organization, profile, refresh tokens, records, documents, goals, plans, conversations,
notifications, challenge participation, badges, points.

### `user_profiles`

Purpose: personal/household details, preferences, leaderboard opt-in. Owner feature: F01.

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER | no | auto | PK |
| `user_id` | INTEGER | no | — | FK → users, unique |
| `phone` | TEXT | yes | null | |
| `country` | TEXT | yes | null | |
| `city` | TEXT | yes | null | |
| `household_size` | INTEGER | yes | null | 1–50 |
| `home_type` | TEXT | yes | null | apartment/house/other |
| `bio` | TEXT | yes | null | |
| `avatar_path` | TEXT | yes | null | private upload path |
| `leaderboard_opt_in` | BOOLEAN | no | false | privacy default |
| `leaderboard_alias` | TEXT | yes | null | display name in leaderboard |
| `onboarding_completed` | BOOLEAN | no | false | |
| `default_period` | TEXT | no | `month` | week/month/year |
| `created_at` | DATETIME | no | UTC now | |
| `updated_at` | DATETIME | no | UTC now | |

Keys/indexes: unique `user_id`; index `leaderboard_opt_in`.
Relations: user.

### `admins`

Purpose: back-office accounts. Owner feature: F13.

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER | no | auto | PK |
| `email` | TEXT | no | — | unique |
| `password_hash` | TEXT | no | — | |
| `name` | TEXT | no | — | |
| `role` | TEXT | no | `content_editor` | super_admin/content_editor |
| `is_active` | BOOLEAN | no | true | |
| `last_login_at` | DATETIME | yes | null | |
| `created_at` | DATETIME | no | UTC now | |
| `updated_at` | DATETIME | no | UTC now | |

Keys/indexes: unique `email`; index `role`, `is_active`.
Relations: audit logs.

### `refresh_tokens`

Purpose: revocable refresh token rotation. Owner feature: F01.

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER | no | auto | PK |
| `user_id` | INTEGER | no | — | FK → users |
| `token_hash` | TEXT | no | — | unique; never store raw token |
| `expires_at` | DATETIME | no | — | UTC |
| `revoked_at` | DATETIME | yes | null | logout/rotation |
| `created_at` | DATETIME | no | UTC now | |

Keys/indexes: unique `token_hash`; index `user_id`, `expires_at`.
Relations: user.

### `emission_categories`

Purpose: top-level activity categories. Owner feature: F02.

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER | no | auto | PK |
| `key` | TEXT | no | — | unique slug |
| `name_en` | TEXT | no | — | |
| `name_ar` | TEXT | no | — | |
| `description_en` | TEXT | yes | null | |
| `description_ar` | TEXT | yes | null | |
| `icon` | TEXT | yes | null | icon key |
| `color_hex` | TEXT | yes | null | UI accent |
| `unit_hint` | TEXT | yes | null | kWh/m³/km/kg/L |
| `sort_order` | INTEGER | no | 0 | |
| `is_active` | BOOLEAN | no | true | |
| `created_at` | DATETIME | no | UTC now | |
| `updated_at` | DATETIME | no | UTC now | |

Keys/indexes: unique `key`; index `is_active`, `sort_order`.
Relations: factors, records, alternatives, challenges.

### `emission_factors`

Purpose: documented calculation factors. Owner feature: F02.

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER | no | auto | PK |
| `category_id` | INTEGER | no | — | FK → emission_categories |
| `key` | TEXT | no | — | unique slug |
| `name_en` | TEXT | no | — | |
| `name_ar` | TEXT | no | — | |
| `activity_type` | TEXT | no | — | grid_electricity/petrol_car/... |
| `unit` | TEXT | no | — | kWh, m³, L, km, passenger_km, kg |
| `factor_grams_co2e` | INTEGER | no | — | grams CO2e per unit |
| `source_name` | TEXT | no | — | EPA/DEFRA/IPCC/etc. |
| `source_url` | TEXT | yes | null | |
| `source_year` | INTEGER | yes | null | |
| `region` | TEXT | no | `GLOBAL` | editable region |
| `valid_from` | DATE | no | — | |
| `valid_to` | DATE | yes | null | null = open |
| `is_active` | BOOLEAN | no | true | |
| `notes` | TEXT | yes | null | assumptions |
| `created_at` | DATETIME | no | UTC now | |
| `updated_at` | DATETIME | no | UTC now | |

Keys/indexes: unique `key`; index `category_id`, `activity_type`, `is_active`, `region`.
Relations: category, records.

### `consumption_records`

Purpose: one recorded activity and its calculated emissions. Owner feature: F03.

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER | no | auto | PK |
| `user_id` | INTEGER | no | — | FK → users |
| `organization_id` | INTEGER | yes | null | FK → organizations; org-scoped |
| `category_id` | INTEGER | no | — | FK → emission_categories |
| `factor_id` | INTEGER | no | — | FK → emission_factors |
| `activity_date` | DATE | no | — | user's local date |
| `quantity` | NUMERIC(14,4) | no | — | > 0 |
| `unit` | TEXT | no | — | must match factor unit |
| `factor_grams_co2e_snapshot` | INTEGER | no | — | snapshot |
| `factor_source_snapshot` | TEXT | no | — | source + year text |
| `emissions_grams` | INTEGER | no | — | round(quantity × factor) |
| `notes` | TEXT | yes | null | |
| `status` | TEXT | no | `active` | active/flagged/deleted |
| `source` | TEXT | no | `manual` | manual/document/seed |
| `document_id` | INTEGER | yes | null | FK → documents; unique when set |
| `created_at` | DATETIME | no | UTC now | |
| `updated_at` | DATETIME | no | UTC now | |

Keys/indexes: index `user_id`, `organization_id`, `category_id`, `activity_date`, `status`;
unique `document_id` when non-null.
Relations: user, organization, category, factor, document.

### `documents`

Purpose: private uploaded bill/receipt, extraction state, link to a record. Owner feature: F04.

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER | no | auto | PK |
| `user_id` | INTEGER | no | — | FK → users |
| `organization_id` | INTEGER | yes | null | |
| `record_id` | INTEGER | yes | null | FK → consumption_records; one-to-one |
| `original_filename` | TEXT | no | — | sanitized display |
| `stored_filename` | TEXT | no | — | generated |
| `mime_type` | TEXT | no | — | validated |
| `size_bytes` | INTEGER | no | — | |
| `storage_path` | TEXT | no | — | relative to upload root |
| `status` | TEXT | no | `uploaded` | uploaded/extracting/extracted/confirmed/rejected/failed |
| `extraction_json` | TEXT | yes | null | candidate fields + confidence |
| `extraction_model` | TEXT | yes | null | actual model returned |
| `confirmed_at` | DATETIME | yes | null | |
| `created_at` | DATETIME | no | UTC now | |
| `updated_at` | DATETIME | no | UTC now | |

Keys/indexes: index `user_id`, `status`; unique `record_id` when non-null.
Relations: user, record.

### `goals`

Purpose: percentage reduction goal with stored baseline. Owner feature: F06.

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER | no | auto | PK |
| `user_id` | INTEGER | no | — | FK → users |
| `organization_id` | INTEGER | yes | null | |
| `title` | TEXT | no | — | |
| `target_percent` | NUMERIC(5,2) | no | — | 1–100 |
| `period_type` | TEXT | no | — | weekly/monthly/yearly |
| `start_date` | DATE | no | — | |
| `end_date` | DATE | no | — | |
| `baseline_start` | DATE | no | — | |
| `baseline_end` | DATE | no | — | |
| `baseline_emissions_grams` | INTEGER | no | — | snapshot |
| `target_emissions_grams` | INTEGER | no | — | baseline × (1 − target%) |
| `status` | TEXT | no | `active` | active/completed/missed/cancelled |
| `created_at` | DATETIME | no | UTC now | |
| `updated_at` | DATETIME | no | UTC now | |

Keys/indexes: index `user_id`, `organization_id`, `status`, `end_date`.
Relations: user, plans.

### `reduction_plans`

Purpose: structured plan, optionally linked to a goal. Owner feature: F09.

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER | no | auto | PK |
| `user_id` | INTEGER | no | — | FK → users |
| `organization_id` | INTEGER | yes | null | |
| `goal_id` | INTEGER | yes | null | FK → goals |
| `title` | TEXT | no | — | |
| `summary` | TEXT | no | — | |
| `locale` | TEXT | no | `en` | language of generated text |
| `source` | TEXT | no | `ai` | ai/template/manual/seed |
| `model` | TEXT | yes | null | actual model returned |
| `status` | TEXT | no | `draft` | draft/active/completed/archived |
| `generated_at` | DATETIME | yes | null | |
| `created_at` | DATETIME | no | UTC now | |
| `updated_at` | DATETIME | no | UTC now | |

Keys/indexes: index `user_id`, `organization_id`, `goal_id`, `status`.
Relations: user, goal, actions.

### `plan_actions`

Purpose: actionable steps inside a plan. Owner feature: F09.

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER | no | auto | PK |
| `plan_id` | INTEGER | no | — | FK → reduction_plans |
| `title` | TEXT | no | — | |
| `description` | TEXT | yes | null | |
| `category_id` | INTEGER | yes | null | FK → emission_categories |
| `priority` | TEXT | no | `medium` | high/medium/low |
| `timeframe` | TEXT | no | `this_month` | this_week/this_month/this_quarter/ongoing |
| `estimated_saving_grams` | INTEGER | yes | null | backend-calculated |
| `saving_assumption` | TEXT | yes | null | documented assumption |
| `status` | TEXT | no | `pending` | pending/in_progress/completed/skipped |
| `due_date` | DATE | yes | null | |
| `completed_at` | DATETIME | yes | null | |
| `sort_order` | INTEGER | no | 0 | |
| `created_at` | DATETIME | no | UTC now | |
| `updated_at` | DATETIME | no | UTC now | |

Keys/indexes: index `plan_id`, `status`, `priority`.
Relations: plan, category.

### `alternatives`

Purpose: curated sustainable alternatives with documented assumptions. Owner feature: F10.

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER | no | auto | PK |
| `key` | TEXT | no | — | unique |
| `title_en` | TEXT | no | — | |
| `title_ar` | TEXT | no | — | |
| `description_en` | TEXT | no | — | |
| `description_ar` | TEXT | no | — | |
| `category_id` | INTEGER | yes | null | FK → emission_categories |
| `estimated_reduction_percent` | NUMERIC(5,2) | no | — | 0–100 |
| `assumption_en` | TEXT | no | — | documented |
| `assumption_ar` | TEXT | no | — | |
| `source_name` | TEXT | yes | null | |
| `source_url` | TEXT | yes | null | |
| `icon` | TEXT | yes | null | |
| `is_active` | BOOLEAN | no | true | |
| `sort_order` | INTEGER | no | 0 | |
| `created_at` | DATETIME | no | UTC now | |
| `updated_at` | DATETIME | no | UTC now | |

Keys/indexes: unique `key`; index `category_id`, `is_active`.
Relations: category, saved alternatives.

### `saved_alternatives`

Purpose: user saves/accepts/dismisses an alternative. Owner feature: F10.

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER | no | auto | PK |
| `user_id` | INTEGER | no | — | FK → users |
| `alternative_id` | INTEGER | no | — | FK → alternatives |
| `status` | TEXT | no | `saved` | saved/accepted/dismissed |
| `created_at` | DATETIME | no | UTC now | |
| `updated_at` | DATETIME | no | UTC now | |

Keys/indexes: unique (`user_id`, `alternative_id`); index `status`.
Relations: user, alternative.

### `challenges`

Purpose: sustainability challenge definition. Owner feature: F11.

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER | no | auto | PK |
| `key` | TEXT | no | — | unique |
| `title_en` | TEXT | no | — | |
| `title_ar` | TEXT | no | — | |
| `description_en` | TEXT | no | — | |
| `description_ar` | TEXT | no | — | |
| `type` | TEXT | no | `weekly` | weekly/monthly/community |
| `category_id` | INTEGER | yes | null | FK → emission_categories |
| `target_type` | TEXT | no | — | record_count/reduction_percent/action_count/streak |
| `target_value` | NUMERIC(10,2) | no | — | |
| `points` | INTEGER | no | 0 | |
| `badge_id` | INTEGER | yes | null | FK → badges |
| `start_date` | DATE | no | — | |
| `end_date` | DATE | no | — | |
| `is_active` | BOOLEAN | no | true | |
| `created_at` | DATETIME | no | UTC now | |
| `updated_at` | DATETIME | no | UTC now | |

Keys/indexes: unique `key`; index `type`, `is_active`, `start_date`, `end_date`.
Relations: category, badge, participants.

### `challenge_participants`

Purpose: one user's challenge progress. Owner feature: F11.

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER | no | auto | PK |
| `challenge_id` | INTEGER | no | — | FK → challenges |
| `user_id` | INTEGER | no | — | FK → users |
| `progress_value` | NUMERIC(10,2) | no | 0 | |
| `status` | TEXT | no | `joined` | joined/in_progress/completed/failed |
| `joined_at` | DATETIME | no | UTC now | |
| `completed_at` | DATETIME | yes | null | |
| `created_at` | DATETIME | no | UTC now | |
| `updated_at` | DATETIME | no | UTC now | |

Keys/indexes: unique (`challenge_id`, `user_id`); index `user_id`, `status`.
Relations: challenge, user.

### `badges`

Purpose: achievement definition. Owner feature: F11.

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER | no | auto | PK |
| `key` | TEXT | no | — | unique |
| `title_en` | TEXT | no | — | |
| `title_ar` | TEXT | no | — | |
| `description_en` | TEXT | no | — | |
| `description_ar` | TEXT | no | — | |
| `icon` | TEXT | yes | null | |
| `criteria` | TEXT | no | — | human-readable rule |
| `points` | INTEGER | no | 0 | |
| `created_at` | DATETIME | no | UTC now | |
| `updated_at` | DATETIME | no | UTC now | |

Keys/indexes: unique `key`.
Relations: challenge awards, user badges.

### `user_badges`

Purpose: awarded badges. Owner feature: F11.

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER | no | auto | PK |
| `user_id` | INTEGER | no | — | FK → users |
| `badge_id` | INTEGER | no | — | FK → badges |
| `awarded_at` | DATETIME | no | UTC now | |

Keys/indexes: unique (`user_id`, `badge_id`); index `user_id`.
Relations: user, badge.

### `points_ledger`

Purpose: append-only points history. Owner feature: F11.

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER | no | auto | PK |
| `user_id` | INTEGER | no | — | FK → users |
| `points` | INTEGER | no | — | positive/negative |
| `reason` | TEXT | no | — | |
| `reference_type` | TEXT | yes | null | challenge/plan/badge/... |
| `reference_id` | INTEGER | yes | null | |
| `created_at` | DATETIME | no | UTC now | |

Keys/indexes: index `user_id`, `created_at`.
Relations: user.

### `notifications`

Purpose: in-app notification/announcement. Owner feature: F12.

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER | no | auto | PK |
| `user_id` | INTEGER | yes | null | null = broadcast |
| `type` | TEXT | no | — | reminder/goal/alert/plan/challenge/summary/announcement |
| `title_en` | TEXT | no | — | |
| `title_ar` | TEXT | no | — | |
| `body_en` | TEXT | no | — | |
| `body_ar` | TEXT | no | — | |
| `is_read` | BOOLEAN | no | false | |
| `action_url` | TEXT | yes | null | app route |
| `created_at` | DATETIME | no | UTC now | |
| `read_at` | DATETIME | yes | null | |

Keys/indexes: index `user_id`, `is_read`, `created_at`, `type`.
Relations: user.

### `notification_preferences`

Purpose: per-type opt-in. Owner feature: F12.

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER | no | auto | PK |
| `user_id` | INTEGER | no | — | FK → users |
| `type` | TEXT | no | — | same values as notifications |
| `enabled` | BOOLEAN | no | true | |
| `created_at` | DATETIME | no | UTC now | |
| `updated_at` | DATETIME | no | UTC now | |

Keys/indexes: unique (`user_id`, `type`).
Relations: user.

### `articles`

Purpose: bilingual educational content. Owner feature: F15.

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER | no | auto | PK |
| `slug` | TEXT | no | — | unique |
| `title_en` | TEXT | no | — | |
| `title_ar` | TEXT | no | — | |
| `summary_en` | TEXT | yes | null | |
| `summary_ar` | TEXT | yes | null | |
| `body_en` | TEXT | no | — | plain text/markdown-lite |
| `body_ar` | TEXT | no | — | |
| `image_path` | TEXT | yes | null | committed asset path |
| `category` | TEXT | yes | null | energy/transport/waste/... |
| `is_published` | BOOLEAN | no | false | |
| `published_at` | DATETIME | yes | null | |
| `sort_order` | INTEGER | no | 0 | |
| `created_at` | DATETIME | no | UTC now | |
| `updated_at` | DATETIME | no | UTC now | |

Keys/indexes: unique `slug`; index `is_published`, `category`.
Relations: none.

### `ai_conversations`

Purpose: assistant conversation header. Owner feature: F07.

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER | no | auto | PK |
| `user_id` | INTEGER | no | — | FK → users |
| `title` | TEXT | no | — | first question snippet |
| `created_at` | DATETIME | no | UTC now | |
| `updated_at` | DATETIME | no | UTC now | |

Keys/indexes: index `user_id`, `updated_at`.
Relations: user, messages.

### `ai_messages`

Purpose: assistant conversation messages. Owner feature: F07.

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER | no | auto | PK |
| `conversation_id` | INTEGER | no | — | FK → ai_conversations |
| `role` | TEXT | no | — | user/assistant/system |
| `content` | TEXT | no | — | |
| `locale` | TEXT | no | `en` | en/ar |
| `model` | TEXT | yes | null | actual model |
| `tokens` | INTEGER | yes | null | total |
| `created_at` | DATETIME | no | UTC now | |

Keys/indexes: index `conversation_id`, `created_at`.
Relations: conversation.

### `ai_usage`

Purpose: AI usage metadata, budget, monitoring. Owner feature: F07–F10.

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER | no | auto | PK |
| `user_id` | INTEGER | yes | null | |
| `feature` | TEXT | no | — | assistant/insights/summary/plan/alternatives/extraction |
| `model` | TEXT | no | — | actual model returned |
| `prompt_tokens` | INTEGER | no | 0 | |
| `completion_tokens` | INTEGER | no | 0 | |
| `total_tokens` | INTEGER | no | 0 | |
| `latency_ms` | INTEGER | no | 0 | |
| `status` | TEXT | no | `success` | success/error/rate_limited/vision_unavailable |
| `error_code` | TEXT | yes | null | |
| `request_hash` | TEXT | no | — | no prompt text |
| `created_at` | DATETIME | no | UTC now | |

Keys/indexes: index `user_id`, `feature`, `created_at`, `status`.
Relations: user.

### `ai_flagged_responses`

Purpose: user-reported AI response for admin review. Owner feature: F15.

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER | no | auto | PK |
| `user_id` | INTEGER | no | — | FK → users |
| `message_id` | INTEGER | yes | null | FK → ai_messages |
| `reason` | TEXT | no | — | inaccurate/unsafe/offensive/other |
| `status` | TEXT | no | `open` | open/reviewed/dismissed |
| `admin_notes` | TEXT | yes | null | |
| `created_at` | DATETIME | no | UTC now | |
| `resolved_at` | DATETIME | yes | null | |

Keys/indexes: index `status`, `created_at`.
Relations: user, message.

### `admin_audit_logs`

Purpose: sensitive admin action history. Owner feature: F13.

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER | no | auto | PK |
| `admin_id` | INTEGER | no | — | FK → admins |
| `action` | TEXT | no | — | create/update/deactivate/delete/reset |
| `entity_type` | TEXT | no | — | user/factor/content/... |
| `entity_id` | INTEGER | yes | null | |
| `details_json` | TEXT | yes | null | redacted details |
| `created_at` | DATETIME | no | UTC now | |

Keys/indexes: index `admin_id`, `created_at`, `entity_type`.
Relations: admin.

### `app_settings`

Purpose: platform settings editable by super admin. Owner feature: F15.

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER | no | auto | PK |
| `key` | TEXT | no | — | unique |
| `value` | TEXT | no | — | string/JSON |
| `updated_at` | DATETIME | no | UTC now | |

Keys/indexes: unique `key`.

### `ai_cache`

Purpose: prompt-hash cache scoped by user/context. Owner feature: F07–F10.

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER | no | auto | PK |
| `user_id` | INTEGER | yes | null | |
| `cache_key` | TEXT | no | — | unique sha256 |
| `feature` | TEXT | no | — | |
| `locale` | TEXT | no | `en` | |
| `response_json` | TEXT | no | — | validated response |
| `created_at` | DATETIME | no | UTC now | |
| `expires_at` | DATETIME | no | — | |

Keys/indexes: unique `cache_key`; index `expires_at`.
Relations: user.

## State machines

| Entity | States | Allowed transitions |
|---|---|---|
| Document | uploaded → extracting → extracted → confirmed / rejected / failed | user confirms/rejects; AI failure → failed; retry allowed |
| Goal | active → completed / missed / cancelled | system updates status by end date; user can cancel |
| Reduction plan | draft → active → completed → archived | user activates/completes; new AI generation creates a draft |
| Plan action | pending → in_progress → completed / skipped | user updates; completed sets timestamp |
| Challenge participant | joined → in_progress → completed / failed | progress endpoint updates; end date marks failed |
| AI flagged response | open → reviewed / dismissed | admin resolves |
| Consumption record | active → flagged → deleted | admin flags; soft delete only |
| Notification | unread → read | user marks read/all read |

## Seed data

Deterministic, idempotent, `flask seed [--reset]`, fixed window ending `DEMO_SEED_DATE`
(default 2026-06-30):

- 1 super admin + 1 content editor.
- 3 demo users + 1 demo organization.
- 7 categories, 20 factors, 12 alternatives.
- 60 consumption records, 3 documents with confirmed extractions.
- 4 goals, 3 plans with actions, 5 challenges, 12 badges, 20 points entries.
- 8 notifications, 8 articles, 10 AI usage metadata rows, 10 audit entries.

Every table above traces to a feature page in `docs/features/`.

Related: #4
