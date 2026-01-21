import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';
import { getStorage } from 'firebase/storage';

const firebaseConfig = {
  projectId: "ocr-perfect",
  appId: "1:276562330509:web:1ea1e68e28ba8cb02973c4",
  storageBucket: "ocr-perfect.firebasestorage.app",
  apiKey: "AIzaSyBQ_tNlu9w6Gr0oIq_f6kzKf0BBF_fZSvM",
  authDomain: "ocr-perfect.firebaseapp.com",
  messagingSenderId: "276562330509",
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize services
export const auth = getAuth(app);
export const db = getFirestore(app);
export const storage = getStorage(app);

// Auth providers
export const googleProvider = new GoogleAuthProvider();

export default app;
