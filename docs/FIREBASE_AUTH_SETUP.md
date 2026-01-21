# Firebase Authentication Setup

## Enable Google Sign-In (Manual Step)

Google Sign-In must be enabled manually via the Firebase Console. This is a one-time setup.

### Steps

1. **Open Firebase Console**
   ```
   https://console.firebase.google.com/project/ocr-perfect/authentication/providers
   ```

2. **Get Started with Authentication**
   - Click "Get started" if this is your first time

3. **Enable Google Provider**
   - Click on "Google" in the providers list
   - Toggle "Enable" to ON
   - Set a project support email (e.g., your email)
   - Click "Save"

4. **Verify Configuration**
   - Google should now appear as "Enabled" in the providers list

### Why Manual?

Firebase Authentication providers cannot be configured via:
- `gcloud` CLI (no identity-platform commands)
- `firebase` CLI (no auth provider commands)
- Pulumi with ADC (quota project issues with Identity Toolkit API)

The only supported methods are:
- Firebase Console (recommended for one-time setup)
- Identity Toolkit REST API (complex, requires OAuth)
- Terraform with service account key (security concerns)

### Verification

After enabling, test with:
```javascript
import { signInWithPopup, GoogleAuthProvider } from 'firebase/auth';
import { auth } from './lib/firebase';

const provider = new GoogleAuthProvider();
signInWithPopup(auth, provider)
  .then((result) => console.log('Signed in:', result.user.email))
  .catch((error) => console.error('Error:', error));
```

### Authorized Domains

Firebase automatically authorizes these domains:
- `ocr-perfect.firebaseapp.com`
- `ocr-perfect.web.app`
- `localhost`

To add custom domains, go to:
```
Firebase Console > Authentication > Settings > Authorized domains
```

## Related Documentation

- [Firebase Auth Documentation](https://firebase.google.com/docs/auth/web/google-signin)
- [Google Sign-In Web](https://developers.google.com/identity/sign-in/web)
