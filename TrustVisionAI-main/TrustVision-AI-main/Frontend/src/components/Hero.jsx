import { CheckCircle2, Cpu, Image, Shield, Sparkles, Video, Zap } from 'lucide-react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';

const featureToneClasses = {
    sky: 'bg-sky-50 text-sky-600',
    emerald: 'bg-emerald-50 text-emerald-600',
    blue: 'bg-blue-50 text-blue-600',
};

const features = [
    {
        icon: Cpu,
        title: 'Fast Face Checks',
        desc: 'Upload a still image and get a prediction, confidence score, and authenticity estimate in one pass.',
        tone: 'sky',
    },
    {
        icon: Shield,
        title: 'Attention Heatmaps',
        desc: 'Review the model attention overlay to explain which facial regions influenced the decision.',
        tone: 'emerald',
    },
    {
        icon: Zap,
        title: 'Hybrid Visual Features',
        desc: 'The detector combines spatial backbones, frequency cues, and optional landmark signals.',
        tone: 'blue',
    },
];

export default function Hero() {
    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: {
                staggerChildren: 0.1,
                delayChildren: 0.2,
            },
        },
    };

    const itemVariants = {
        hidden: { opacity: 0, y: 30 },
        visible: {
            opacity: 1,
            y: 0,
            transition: { type: 'spring', stiffness: 100, damping: 20 },
        },
    };

    return (
        <div className="relative pt-32 pb-20 sm:pt-48 sm:pb-32 overflow-hidden bg-transparent">
            <div className="absolute top-20 left-[10%] w-96 h-96 bg-sky-200/50 rounded-full blur-[100px] animate-float-slow -z-10" />
            <div
                className="absolute bottom-20 right-[10%] w-[500px] h-[500px] bg-emerald-100/60 rounded-full blur-[120px] animate-float -z-10"
                style={{ animationDelay: '2s' }}
            />

            <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
                    <motion.div
                        variants={containerVariants}
                        initial="hidden"
                        animate="visible"
                        className="text-left"
                    >
                        <motion.div
                            variants={itemVariants}
                            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white shadow-sm border border-slate-200 text-slate-600 text-sm font-semibold mb-8"
                        >
                            <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
                            Presentation Build
                        </motion.div>

                        <motion.h1
                            variants={itemVariants}
                            className="text-5xl md:text-6xl lg:text-7xl font-black tracking-tight text-slate-900 mb-6 leading-[1.1]"
                        >
                            Inspect Face Images
                            <br />
                            <span className="gradient-text">For Synthetic Cues.</span>
                        </motion.h1>

                        <motion.p
                            variants={itemVariants}
                            className="max-w-xl text-lg md:text-xl text-slate-600 font-medium leading-relaxed mb-10"
                        >
                            Research prototype for face-image authenticity analysis. Scan uploaded images or sampled
                            webcam frames and review the model heatmap alongside the final verdict.
                        </motion.p>

                        <motion.div variants={itemVariants} className="flex flex-col sm:flex-row gap-4">
                            <Link to="/analyze">
                                <motion.button
                                    whileHover={{ scale: 1.03, y: -2 }}
                                    whileTap={{ scale: 0.97 }}
                                    className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-4 text-base font-bold text-white bg-slate-900 hover:bg-slate-800 rounded-2xl shadow-[0_10px_30px_-10px_rgba(15,23,42,0.4)] transition-all"
                                >
                                    <Sparkles className="w-5 h-5 text-emerald-400" />
                                    Analyze Upload
                                </motion.button>
                            </Link>

                            <Link to="/analyze?mode=live">
                                <motion.button
                                    whileHover={{ scale: 1.03, y: -2 }}
                                    whileTap={{ scale: 0.97 }}
                                    className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-4 text-base font-bold text-slate-700 bg-white hover:bg-slate-50 border border-slate-200 shadow-sm rounded-2xl transition-all"
                                >
                                    <Zap className="w-5 h-5 gradient-icon" />
                                    Scan Webcam Frames
                                </motion.button>
                            </Link>
                        </motion.div>
                    </motion.div>

                    <motion.div
                        initial={{ opacity: 0, scale: 0.9, rotateY: 15 }}
                        animate={{ opacity: 1, scale: 1, rotateY: 0 }}
                        transition={{ duration: 1, delay: 0.4, type: 'spring' }}
                        className="relative hidden lg:block"
                    >
                        <motion.div
                            className="relative z-10 w-full aspect-square rounded-[2.5rem] bg-white/60 backdrop-blur-2xl border border-white/60 shadow-[0_30px_60px_-15px_rgba(0,0,0,0.15)] overflow-hidden flex flex-col group cursor-pointer transition-colors hover:bg-white/80"
                            whileHover={{ scale: 1.02 }}
                            transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                        >
                            <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-400/10 rounded-full blur-3xl -z-10 transition-transform duration-700 group-hover:scale-150" />
                            <div className="absolute bottom-0 left-0 w-64 h-64 bg-indigo-400/10 rounded-full blur-3xl -z-10 transition-transform duration-700 group-hover:scale-150" />

                            <div className="p-8 pb-4 flex justify-between items-start z-10">
                                <motion.div
                                    className="w-14 h-14 rounded-2xl bg-slate-900 flex items-center justify-center text-white shadow-lg shadow-slate-900/20"
                                    whileHover={{ rotate: 180, scale: 1.1 }}
                                    transition={{ duration: 0.6 }}
                                >
                                    <Shield className="w-7 h-7 text-emerald-400" />
                                </motion.div>
                                <motion.div
                                    className="px-4 py-2 bg-emerald-50 text-emerald-700 font-bold text-xs rounded-full border border-emerald-200 uppercase tracking-widest flex items-center gap-2 shadow-sm"
                                    whileHover={{ scale: 1.05 }}
                                >
                                    <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_10px_rgba(16,185,129,0.6)]" />
                                    Model Ready
                                </motion.div>
                            </div>

                            <div className="px-8 space-y-4 mt-2 z-10">
                                <div className="h-6 w-1/2 bg-slate-800 rounded-lg shadow-inner" />
                                <div className="flex gap-3 mt-4">
                                    <div className="h-3 w-1/3 bg-slate-200 rounded-full overflow-hidden relative shadow-inner">
                                        <motion.div
                                            className="absolute inset-y-0 left-0 bg-gradient-to-r from-sky-400 to-indigo-500"
                                            initial={{ width: '0%' }}
                                            animate={{ width: ['0%', '100%', '100%', '0%'] }}
                                            transition={{ duration: 4, times: [0, 0.4, 0.5, 1], repeat: Infinity, ease: 'easeInOut' }}
                                        />
                                    </div>
                                    <div className="h-3 w-1/4 bg-slate-200 rounded-full overflow-hidden relative shadow-inner">
                                        <motion.div
                                            className="absolute inset-y-0 left-0 bg-gradient-to-r from-emerald-400 to-teal-500"
                                            initial={{ width: '0%' }}
                                            animate={{ width: ['0%', '100%', '100%', '0%'] }}
                                            transition={{
                                                duration: 4,
                                                times: [0, 0.4, 0.5, 1],
                                                repeat: Infinity,
                                                ease: 'easeInOut',
                                                delay: 0.5,
                                            }}
                                        />
                                    </div>
                                </div>
                            </div>

                            <div className="absolute bottom-0 inset-x-0 h-3/5 bg-gradient-to-t from-slate-50/80 to-transparent border-t border-white/60 flex items-center justify-center z-10 overflow-hidden">
                                <div className="relative flex items-center justify-center group-hover:scale-105 transition-transform duration-500">
                                    <motion.div
                                        className="absolute w-72 h-72 rounded-full border border-slate-300 border-dashed"
                                        animate={{ rotate: 360 }}
                                        transition={{ duration: 30, repeat: Infinity, ease: 'linear' }}
                                    >
                                        <div className="absolute top-0 left-1/2 w-4 h-4 -ml-2 rounded-full bg-indigo-500 shadow-[0_0_20px_rgba(99,102,241,0.8)]" />
                                        <div className="absolute bottom-0 right-1/2 w-3 h-3 ml-1.5 rounded-full bg-emerald-400 shadow-[0_0_15px_rgba(52,211,153,0.8)]" />
                                    </motion.div>

                                    <motion.div
                                        className="absolute w-44 h-44 rounded-full border-2 border-emerald-300"
                                        animate={{ rotate: -360 }}
                                        transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
                                    >
                                        <div className="absolute bottom-4 left-4 w-5 h-5 rounded-full bg-sky-400 shadow-[0_0_20px_rgba(56,189,248,0.8)]" />
                                    </motion.div>

                                    <motion.div
                                        className="relative w-24 h-24 rounded-full bg-gradient-to-br from-indigo-500 via-sky-500 to-emerald-400 shadow-[0_0_50px_rgba(56,189,248,0.6)] flex items-center justify-center z-20 cursor-pointer"
                                        whileHover={{ scale: 1.15 }}
                                        whileTap={{ scale: 0.95 }}
                                    >
                                        <CheckCircle2 className="w-10 h-10 text-white drop-shadow-md" />
                                        <motion.div
                                            className="absolute inset-0 rounded-full bg-sky-400 -z-10"
                                            animate={{ scale: [1, 2.2], opacity: [0.6, 0] }}
                                            transition={{ duration: 2.5, repeat: Infinity, ease: 'easeOut' }}
                                        />
                                    </motion.div>
                                </div>
                            </div>
                        </motion.div>

                        <motion.div
                            drag
                            dragConstraints={{ left: -50, right: 50, top: -50, bottom: 50 }}
                            className="absolute -top-10 -right-10 w-28 h-28 bg-white/90 backdrop-blur-md rounded-2xl border border-white shadow-2xl flex items-center justify-center cursor-grab active:cursor-grabbing z-20 hover:shadow-indigo-500/20 transition-all hover:scale-110"
                        >
                            <Image className="w-10 h-10 text-indigo-500 drop-shadow-sm" />
                        </motion.div>
                        <motion.div
                            drag
                            dragConstraints={{ left: -50, right: 50, top: -50, bottom: 50 }}
                            className="absolute -bottom-10 -left-10 w-32 h-32 bg-slate-900 rounded-[2.5rem] shadow-2xl flex items-center justify-center cursor-grab active:cursor-grabbing z-30 hover:shadow-emerald-500/30 transition-all hover:scale-110 border-2 border-slate-700"
                        >
                            <Video className="w-12 h-12 text-emerald-400 drop-shadow-sm" />
                        </motion.div>
                    </motion.div>
                </div>

                <motion.div
                    variants={containerVariants}
                    initial="hidden"
                    animate="visible"
                    className="mt-32 grid grid-cols-1 md:grid-cols-3 gap-8"
                >
                    {features.map((feature) => {
                        const Icon = feature.icon;
                        return (
                            <motion.div
                                key={feature.title}
                                variants={itemVariants}
                                whileHover={{ y: -8, scale: 1.02 }}
                                className="p-8 rounded-[2rem] bg-white border border-slate-100 shadow-[0_8px_30px_rgb(0,0,0,0.04)] transition-all cursor-pointer group hover:shadow-[0_20px_40px_-15px_rgba(15,23,42,0.1)]"
                            >
                                <div
                                    className={`w-14 h-14 rounded-2xl ${featureToneClasses[feature.tone]} flex items-center justify-center mb-6 group-hover:scale-110 transition-transform shadow-sm`}
                                >
                                    <Icon className="w-7 h-7" />
                                </div>
                                <h3 className="text-xl font-bold text-slate-900 mb-3">{feature.title}</h3>
                                <p className="text-slate-500 leading-relaxed font-medium">{feature.desc}</p>
                            </motion.div>
                        );
                    })}
                </motion.div>
            </div>
        </div>
    );
}
