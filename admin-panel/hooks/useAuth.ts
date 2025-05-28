import { useState, useEffect, useContext, createContext } from "react";
import { signInWithEmailAndPassword, signOut, onAuthStateChanged, User as FirebaseUser } from "firebase/auth";
import { auth } from "@/lib/firebaseConfig";
import { getFirestore, doc, getDoc } from "firebase/firestore";

interface AuthContextType {
  user: FirebaseUser | null;
  isAdmin: boolean;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  token: string | null;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<FirebaseUser | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      setUser(firebaseUser);
      setLoading(false);
      setError(null);
      if (firebaseUser) {
        const idToken = await firebaseUser.getIdToken();
        setToken(idToken);
        // Verificar rol admin en Firestore
        const db = getFirestore();
        const userDoc = await getDoc(doc(db, "users", firebaseUser.uid));
        const data = userDoc.data();
        setIsAdmin(data?.role === "admin" || data?.role === "Admin");
      } else {
        setIsAdmin(false);
        setToken(null);
      }
    });
    return () => unsubscribe();
  }, []);

  useEffect(() => {
    if (token) {
      if (typeof window !== "undefined") {
        window.localStorage.setItem("firebaseToken", token);
      }
    } else {
      if (typeof window !== "undefined") {
        window.localStorage.removeItem("firebaseToken");
      }
    }
  }, [token]);

  const login = async (email: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      const cred = await signInWithEmailAndPassword(auth, email, password);
      const idToken = await cred.user.getIdToken();
      setToken(idToken);
      // Verificar rol admin en Firestore
      const db = getFirestore();
      const userDoc = await getDoc(doc(db, "users", cred.user.uid));
      const data = userDoc.data();
      setIsAdmin(data?.role === "admin" || data?.role === "Admin");
      setUser(cred.user);
      setLoading(false);
      if (!(data?.role === "admin" || data?.role === "Admin")) {
        setError("Acceso solo para administradores");
        await signOut(auth);
        setUser(null);
        setToken(null);
        setIsAdmin(false);
      }
    } catch (e: any) {
      setError(e.message || "Error de autenticación");
      setLoading(false);
    }
  };

  const logout = async () => {
    await signOut(auth);
    setUser(null);
    setToken(null);
    setIsAdmin(false);
  };

  return (
    <AuthContext.Provider value={{ user, isAdmin, loading, login, logout, token, error }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return ctx;
} 