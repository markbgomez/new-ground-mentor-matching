# Manual Google Cloud Console Checklist

Before running production deployment (`infra/deploy.sh`), complete these manual steps in the Google Cloud Console for project `new-ground-mentor-matching` (number: `672069369633`).

### 1. Google Auth Platform / OAuth Consent Screen
1. Navigate to **APIs & Services** -> **OAuth consent screen** (or **Google Auth Platform** -> **Branding / Audience**).
2. User Type: Select **External**.
3. Status: Set to **Testing**.
4. App Information:
   - App Name: `New Ground Match Agent`
   - User support email: `mgomez@project127.org`
   - Developer contact email: `mgomez@project127.org` (or `markbgomez@gmail.com`)
5. Scopes:
   - Click **Add or Remove Scopes**.
   - Add:
     - `openid`
     - `https://www.googleapis.com/auth/userinfo.email`
     - `https://www.googleapis.com/auth/gmail.send`
6. Test Users:
   - Add:
     - `mgomez@project127.org`
     - `adudrey@project127.org`
     - `akuykendall@project127.org`
     - `markbgomez@gmail.com`

### 2. OAuth Clients
Navigate to **APIs & Services** -> **Credentials**:
1. Create **Web application** client:
   - Name: `IAP Coordinator App Client`
   - Used for Cloud Run IAP authentication.
2. Create **Desktop app** client:
   - Name: `Gmail Sender CLI Client`
   - Download the JSON credentials file as `infra/client_secret.json`.

### 3. Gmail API Authorization
Run the authorization script:
```bash
python infra/authorize_gmail.py
```
This logs in with `mgomez@project127.org`, requests the `gmail.send` scope, and writes the OAuth refresh token directly to Secret Manager secret `gmail-sender-oauth`.

> [!WARNING]
> Because the OAuth consent screen is in **Testing** mode without Google verification, OAuth refresh tokens expire after **7 days**. Re-run `python infra/authorize_gmail.py` before live demos!

### 4. IAP on Cloud Run
1. Go to **Security** -> **Identity-Aware Proxy**.
2. Select `coordinator-app` service.
3. Turn on IAP using the Web Application OAuth credentials created above.
4. Grant the role **IAP-secured Web App User** (`roles/iap.httpsResourceAccessor`) to:
   - `mgomez@project127.org`
   - `adudrey@project127.org`
   - `akuykendall@project127.org`
