// Script para obtener un ID token de Firebase Auth desde Node.js
// Requiere instalar: npm install firebase

const { initializeApp } = require('firebase/app');
const { getAuth, signInWithEmailAndPassword } = require('firebase/auth');

// Configuración de Firebase (rellena con los datos de tu proyecto)
const firebaseConfig = {
  apiKey: "AIzaSyAFSKgCPMCrg7D_z5HGYJinGWv1aIp5-o8",
  authDomain: "pdzr-458820.firebaseapp.com",
  projectId: "pdzr-458820",
  storageBucket: "pdzr-458820.firebasestorage.app",
  messagingSenderId: "217182607497",
  appId: "1:217182607497:web:b40c0b73f425df07ddce58",
  measurementId: "G-VS8TKB9Q9F"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

const email = 'testuser1@padelyzer.com';
const password = 'TestPassword123!';

signInWithEmailAndPassword(auth, email, password)
  .then((userCredential) => userCredential.user.getIdToken())
  .then((token) => {
    console.log('ID Token de Firebase:', token);
  })
  .catch((error) => {
    console.error('Error al obtener el token:', error);
    process.exit(1);
  }); 