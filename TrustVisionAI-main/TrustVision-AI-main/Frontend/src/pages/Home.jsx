import { motion } from 'framer-motion';

import Hero from '../components/Hero';
import Navbar from '../components/Navbar';

export default function Home() {
    return (
        <div className="min-h-screen relative overflow-hidden font-sans text-slate-800">
            <Navbar />
            <main>
                <Hero />
            </main>

            <motion.div
                initial={{ scaleX: 0 }}
                animate={{ scaleX: 1 }}
                transition={{ delay: 0.5, duration: 1.2, ease: 'circOut' }}
                className="h-px w-full bg-gradient-to-r from-transparent via-slate-200 to-transparent"
            />

            <motion.footer
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.8, duration: 0.6 }}
                className="py-12 pb-20 text-center text-sm text-slate-500 relative z-10"
            >
                <p className="mb-2 font-medium">Copyright {new Date().getFullYear()} TrustVision AI</p>
                <p className="text-xs text-slate-400">Face-image authenticity research prototype</p>
            </motion.footer>
        </div>
    );
}
