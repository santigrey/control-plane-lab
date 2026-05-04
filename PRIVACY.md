# Privacy Policy — Alexandra

**Last updated:** 2026-05-04

## What Alexandra is

Alexandra is a personal AI assistant operated by a single individual (the application owner) for that individual's own use. It is not a product, service, or platform offered to other people.

## Who uses Alexandra

Only the application owner. There are no other users. There are no plans to add other users. If at any point this changes, this policy will be updated and re-published.

## What data Alexandra accesses

Alexandra requests OAuth access to the application owner's own Google account, specifically:

- **Gmail (read-only)** — to read incoming emails and present summaries to the application owner
- **Gmail (send)** — to send emails composed by the application owner via the assistant interface
- **Google Calendar (events)** — to read upcoming calendar events and create new events on the application owner's primary calendar

All data accessed is the application owner's own data. No data is accessed on behalf of any other person.

## What Alexandra does with that data

- **Reads it locally** on infrastructure controlled by the application owner (a private homelab). Email summaries and calendar context are presented to the application owner via a personal AI assistant interface.
- **Stores derived summaries** in a local PostgreSQL database on the application owner's hardware. These summaries are used to give the assistant continuity across conversations.
- **Does not transmit Google data to third parties.** Email content and calendar event details never leave the application owner's local infrastructure except as necessary to call Google's own APIs (which is by definition required to read the data).
- **Does not sell, share, or aggregate any data.** Alexandra is not a commercial product and has no monetization model.

## Third-party services used

Alexandra uses the following third-party services as infrastructure dependencies. None of them receive Google account data:

- Anthropic Claude API — for natural-language reasoning. Prompts may include summaries of email subjects or calendar event titles when the application owner asks the assistant to reason about their schedule or correspondence; full email bodies are not transmitted.
- Tailscale — for secure network connectivity within the application owner's infrastructure. Tailscale does not see application data.
- Twilio — for SMS notifications about calendar events or alerts. Twilio receives only the message body the application owner authorizes (e.g. "reminder: 3pm meeting").

## Data retention

- **Live OAuth tokens:** stored locally; rotated when the application owner re-authenticates.
- **Email summaries / calendar derivatives:** stored in the local PostgreSQL database indefinitely for assistant continuity, deletable by the application owner at any time via direct database access.
- **Raw email bodies:** never persisted. Read transiently from Gmail API and discarded after summary generation.

## How to revoke Alexandra's access

The application owner can revoke Alexandra's access at any time by visiting https://myaccount.google.com/permissions and removing the Alexandra application. This invalidates all tokens immediately.

## Contact

Questions about this policy can be directed to the application owner at the email address registered in the OAuth consent screen.
