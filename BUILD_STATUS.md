# V18 Update

- Enlarged the floating launcher from 66px to 82px on desktop.
- Enlarged the mobile launcher to 72px.
- Rebuilt the bubble logo from the tighter header asset, removed unused transparent margins, and produced a high-resolution browser asset.
- Increased contrast and clarity while retaining the official company artwork.
- Enlarged the logo shown in the 15-second welcome teaser.
- Incremented frontend cache version to 18.

# Resumed Build Status

This version continues the previous James Wholesale Homes chatbot project.

## Completed-conversation behaviour

- A submitted conversation is marked `completed` in the database.
- Reloading the page does not restart or reuse that completed enquiry.
- The message composer remains disabled after submission.
- Only **Start New Chat** calls `/api/chat/new` and creates a new session ID.
- The previous submitted lead remains stored in the admin dashboard.

## Professional features included

- Official company logo in the chat header
- Branded navy and orange launcher bubble and interface
- Speaker and browser voice-input controls
- File upload and property-link controls
- FAQ menu and question batches
- Buyer, seller, buy-and-sell, investor and funding flows
- Real-estate property types and type-specific requirement fields
- Name, email, US phone, state, ZIP and currency validation
- Contact verification-code workflow with SMTP and SMS-webhook support
- Recent real-estate projects public endpoint and cards
- Public statistics and featured Minnesota location models
- Lead classification, conversation history and admin dashboard storage
- SMTP owner notification and customer confirmation support
- Argon2id password hashing, login lockout protection and audit logs

## Production configuration still required

- SMTP credentials and owner email
- SMS verification webhook, when phone verification is required
- Real malware scanner such as ClamAV
- Production PostgreSQL database
- Redis-backed rate limiting
- Final privacy, consent and legal wording
- Verified project photographs and public statistics

## Professional interface update

- Removed the demo landing page. The root route now displays only the floating chat launcher and chat window, suitable for transparent iframe embedding.
- Removed the automatic teaser card so the closed state remains a single professional chat icon.
- Enlarged the official James Wholesale Homes logo inside the navy header.
- Moved microphone and attachment controls beside the message field.
- Renamed “Browse Real Estate FAQs” to “Real Estate FAQs”.
- Added professional SVG icons, arrows, shadows and hover states to main menu cards.
- Added a subtle navy/orange surface treatment to the conversation background.
- Improved chat flex sizing, internal scrolling and quick-response overflow so lower buttons remain accessible.
- Added a 0.10-second typing indicator before new assistant messages.
- Preserved speaker, new-chat, close-chat, file upload, link upload and completed-conversation behaviour.

## 27 July 2026 UI refinement

- Replaced the large welcome chat bubble with a compact welcome heading.
- Added a five-image auto-sliding welcome carousel using the supplied property photographs.
- Added clickable image detail overlays with service descriptions and direct actions.
- Added orange hover and selected states across menu, FAQ, property and condition buttons.
- Added a fixed action dock so the active controls remain available while conversation content scrolls.
- Removed the verbose office-status and footer messages to reclaim chat space.
- Kept microphone and file/link controls beside the typing field.
- Kept the 100 millisecond typing indicator delay.
- Added client-side ZIP formatting plus server-side city/state/ZIP validation.
- Added explicit invalid-ZIP handling when the remote ZIP service returns 404.


## V3 review improvements
- Professional grouped enquiry summary with validation badges.
- Strict city-name checks reject generic entries such as USA or United States.
- City/state/ZIP validation is repeated before final lead creation.
- Submit is disabled when final validation issues remain.
- Uploaded files and submitted links appear in the review summary.

## V5 seller FAQ update

- Added 11 approved selling-property questions and answers.
- The Sell a Property button opens the complete seller-question list before lead capture.
- Viewed questions are removed from the remaining list.
- Yes shows unanswered questions; No starts the seller enquiry at full-name collection.
- `seed_faq.py` now safely updates existing FAQ data.

## V11 final submission fix
- Callback time ranges are now validated case-insensitively.
- Existing sessions containing `9:00 AM TO 11:00 AM` are accepted and normalised.
- Final review button changes to **Submit Enquiry** when all checks pass.
- Blocked review action now reads **Complete Required Details** with **Edit Enquiry**.


## V12 interface update
- Floating launcher now displays the James Wholesale Homes company logo.
- Duplicate “Buy and Sell a Property” welcome card removed; dedicated Buy and Sell buttons remain.


## V14 updates
- Added a 15-second floating welcome prompt beside the launcher after each reload.
- Removed the extra welcome subtitle line.
- Changed phone prompt to remove “US”.
- Added secure Account Settings for changing admin email and password with current-password confirmation.


## V15 updates
- Improved speaker control with reliable voice loading, long-answer chunking, pause, resume and stop states.
- Added four buyer questions under the Buy a Property entry flow.
- Buyer FAQ answers now lead to remaining questions or the buyer enquiry form.


## V16 changes
- Removed the Ask a Real Estate Question card from the welcome screen.
- Rebuilt the chat-header logo with safe padding to prevent the James lettering from being clipped.
- Adjusted desktop and mobile logo sizing and alignment.


## V17 hotfix
- Fixed `Cannot access bubbleTeaserTimer before initialization`.
- Added defensive teaser element checks.
- Added static asset cache-busting for widget.js and widget.css.
