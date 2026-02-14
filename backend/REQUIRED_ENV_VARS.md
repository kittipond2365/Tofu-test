# Required Production Environment Variables

Set these variables in Render/Supabase/your deployment environment.

## Required
- `DATABASE_URL` - PostgreSQL connection URL (e.g. Supabase/Render Postgres)
- `SECRET_KEY` - Strong random secret (minimum 32 characters)

## Optional / Feature-dependent
- `REDIS_URL` - Required if Redis caching/session features are enabled
- `FIREBASE_PROJECT_ID` - Required if FCM push notifications are enabled
- `FCM_SERVICE_ACCOUNT_JSON` - Required if FCM push notifications are enabled
- `LINE_CHANNEL_ID` - Required if LINE Login is enabled
- `LINE_CHANNEL_SECRET` - Required if LINE Login is enabled
