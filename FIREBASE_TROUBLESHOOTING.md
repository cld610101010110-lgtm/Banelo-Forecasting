# Firebase Dashboard Timeout - Troubleshooting Guide

## Problem Description

The dashboard view is timing out with the following error:

```
❌ Error loading dashboard: Timeout of 300.0s exceeded
Invalid JWT Signature: ('invalid_grant: Invalid JWT Signature.')
```

This indicates a Google Cloud authentication issue.

## Root Causes

The "Invalid JWT Signature" error typically occurs due to:

1. **Revoked or Expired Credentials** - The service account key has been revoked in Google Cloud Console
2. **Corrupted Credentials File** - The `firebase-credentials.json` file is invalid or corrupted
3. **Wrong Project Credentials** - Credentials are from a different Firebase project
4. **Network Timeout** - Firebase API is unreachable or responding slowly
5. **Clock Skew** - Server time is out of sync with Google's servers

## How This Was Fixed

The dashboard now includes:

1. **Firebase Health Checks** - Validates credentials and connectivity before attempting queries
2. **Fallback Rendering** - Dashboard loads with empty data instead of timing out
3. **Better Error Messages** - Clear error messages indicating the specific issue
4. **Debug Endpoints** - New API endpoints to diagnose Firebase issues
5. **Query Timeouts** - Firestore queries use `limit()` to prevent hanging

## New Endpoints

### Health Check API
```
GET /dashboard/api/health/
```

Returns JSON with:
- Firebase connectivity status
- Credentials validation results
- Environment information

### Debug Status Page
```
GET /dashboard/api/debug/firebase/
```

Returns HTML page with:
- Detailed credentials status
- Connectivity test results
- Troubleshooting steps

## Troubleshooting Steps

### Step 1: Check Credentials File Exists
```bash
ls -la baneloforecasting/firebase-credentials.json
```

If missing, download from Google Cloud Console:
- Go to Firebase Project Settings
- Service Accounts tab
- Generate new private key

### Step 2: Validate Credentials Format
```bash
python -c "import json; json.load(open('baneloforecasting/firebase-credentials.json'))" && echo "✅ Valid JSON"
```

### Step 3: Check Environment Variable
```bash
echo $FIREBASE_CREDENTIALS
# Should output: baneloforecasting/firebase-credentials.json (or your path)
```

### Step 4: Test Firebase Connection
```bash
# View debug page in browser
# http://yourserver/dashboard/api/debug/firebase/
```

### Step 5: Regenerate Credentials (If Revoked)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your Firebase project
3. Navigate to Service Accounts
4. Click on the service account
5. Keys tab → Create new key → JSON
6. Download and replace `firebase-credentials.json`
7. Restart Django

### Step 6: Check Server Time
```bash
# Ensure server time is accurate (within ±5 minutes of UTC)
date
# Install NTP if needed
sudo apt-get install ntp
sudo service ntp restart
```

## Dashboard Fallback Behavior

If Firebase is unavailable:
- Dashboard still loads with empty data
- User sees "Firebase connection issue" message
- Charts show no data
- No timeout errors
- Page loads quickly (~500ms)

## Production Deployment Recommendations

1. **Environment Variables** - Use secure environment variable management
   ```bash
   export FIREBASE_CREDENTIALS=/etc/secrets/firebase-credentials.json
   ```

2. **Monitor Firebase Health** - Set up regular health checks
   ```bash
   # Cron job every 5 minutes
   0 */5 * * * * curl -s https://yourserver/dashboard/api/health/ > /dev/null
   ```

3. **Alerts** - Monitor for authentication failures in logs
   ```bash
   grep "Invalid JWT" /var/log/django.log
   ```

4. **Backup Data** - Ensure local SQLite database is populated as fallback
   - Dashboard uses local DB when Firebase is unavailable
   - ML forecasting uses local Product/Sale models

5. **Service Account Rotation** - Rotate credentials every 90 days
   - Generate new keys in Google Cloud
   - Update FIREBASE_CREDENTIALS
   - Delete old keys

## Advanced: Debugging JWT Issues

If you're seeing JWT signature errors persistently:

1. Check private key format (should start with `-----BEGIN PRIVATE KEY-----`)
2. Verify no characters were corrupted in credentials file
3. Check that the service account has Firestore permissions:
   - Go to IAM & Admin
   - Find the service account
   - Ensure "Editor" or "Cloud Datastore User" role is assigned
4. Try regenerating the credentials completely

## See Also

- [Django Deployment Guide](https://docs.djangoproject.com/en/5.2/howto/deployment/)
- [Firebase Admin SDK](https://firebase.google.com/docs/admin/setup)
- [Google Cloud Service Accounts](https://cloud.google.com/iam/docs/service-accounts)
