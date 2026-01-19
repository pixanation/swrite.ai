import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, Image as ImageIcon } from 'lucide-react';

export function UploadZone({ onFileSelect, disabled }) {
    const onDrop = useCallback(acceptedFiles => {
        if (acceptedFiles?.length > 0) {
            onFileSelect(acceptedFiles[0]);
        }
    }, [onFileSelect]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'application/pdf': ['.pdf'],
            'image/*': ['.png', '.jpg', '.jpeg']
        },
        disabled,
        multiple: false
    });

    return (
        <div
            {...getRootProps()}
            className={`
        border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all duration-300
        ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'}
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
      `}
        >
            <input {...getInputProps()} />
            <div className="flex flex-col items-center gap-4">
                <div className="p-4 bg-white rounded-full shadow-sm">
                    <Upload className="w-8 h-8 text-blue-600" />
                </div>
                <div>
                    <p className="text-lg font-medium text-gray-900">
                        {isDragActive ? "Drop it here!" : "Click to upload or drag and drop"}
                    </p>
                    <p className="text-sm text-gray-500 mt-1">
                        PDFs or Images (Handwritten)
                    </p>
                </div>
            </div>
        </div>
    );
}
