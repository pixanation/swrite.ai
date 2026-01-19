import React from 'react';
import { CheckCircle, Circle, ArrowRight, Loader2 } from 'lucide-react';

const STEPS = [
    { id: 'processing', label: 'Segregating' },
    { id: 'extracted', label: 'Extracting' },
    { id: 'planned', label: 'Planning' },
    { id: 'completed', label: 'Rendered' }
];

export function JobStatus({ status }) {
    // Map backend status to step index
    const getCurrentStep = () => {
        if (!status) return -1;
        if (status === 'created') return 0;
        if (status === 'processing') return 0; // Segregating
        if (status === 'extracted') return 1; // Extracting Done
        if (status === 'planned') return 2;   // Planning Done
        if (status === 'competed') return 3;  // Rendered
        return 0;
    };

    const activeIndex = getCurrentStep();

    return (
        <div className="w-full max-w-2xl mx-auto py-8">
            <div className="flex items-center justify-between relative">
                {/* Connector Line */}
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-1 bg-gray-200 -z-10" />
                <div
                    className="absolute left-0 top-1/2 -translate-y-1/2 h-1 bg-green-500 -z-10 transition-all duration-500"
                    style={{ width: `${(activeIndex / (STEPS.length - 1)) * 100}%` }}
                />

                {STEPS.map((step, index) => {
                    const isCompleted = index <= activeIndex;
                    const isCurrent = index === activeIndex;

                    return (
                        <div key={step.id} className="flex flex-col items-center gap-2 bg-white px-2">
                            <div className={`
                w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all
                ${isCompleted ? 'bg-green-500 border-green-500 text-white' : 'bg-white border-gray-300 text-gray-400'}
                ${isCurrent ? 'ring-4 ring-green-100' : ''}
              `}>
                                {isCompleted ? <CheckCircle className="w-6 h-6" /> : <Circle className="w-6 h-6" />}
                            </div>
                            <span className={`text-sm font-medium ${isCompleted ? 'text-gray-900' : 'text-gray-500'}`}>
                                {step.label}
                            </span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
