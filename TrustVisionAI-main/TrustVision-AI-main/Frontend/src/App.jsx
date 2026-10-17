import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import Home from "./pages/Home";
import Analyze from "./pages/Analyze";

function App() {
  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: 'linear-gradient(135deg, #0f172a, #1e293b)',
            color: '#f8fafc',
            border: '1px solid #0f766e',
            borderRadius: '10px',
            boxShadow: '0 0 30px rgba(15, 118, 110, 0.18)',
            backdropFilter: 'blur(10px)',
          },
          success: {
            style: {
              borderColor: '#059669',
              boxShadow: '0 0 30px rgba(5, 150, 105, 0.28)',
            },
            iconTheme: {
              primary: '#059669',
              secondary: '#0f172a',
            },
          },
          error: {
            style: {
              borderColor: '#ef4444',
              boxShadow: '0 0 30px rgba(239, 68, 68, 0.3)',
            },
            iconTheme: {
              primary: '#ef4444',
              secondary: '#0f172a',
            },
          },
        }}
      />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/analyze" element={<Analyze />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
